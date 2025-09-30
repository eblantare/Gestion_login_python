from flask import Blueprint, request, render_template, jsonify, send_file
from ..models import Enseignant, Matiere, Ecole
from sqlalchemy import cast, String, extract
from gestion_login.gestion_login.models import Utilisateur
from flask_login import current_user
from extensions import db
from sqlalchemy.orm import joinedload
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from datetime import datetime
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

enseignants_bp = Blueprint('enseignants', __name__)

def is_admin():
    return getattr(current_user, "role", "").lower() in ["admin", "administrateur"]

# ---------------- Filtrage ----------------
FILTER_DIC = {
    "sexe": {
        "M": ["M", "Masculin"],
        "F": ["F", "Féminin"]
    },
    "etat": {
        "Inactif": ["Inactif"],
        "Actif": ["Actif"],
        "Muté": ["Muté"],
        "Retraité": ["Retraité"]
    },
    "titre": {
        "Enseignant": ["Enseignant", "Enseignante"],
        "Directeur": ["Directeur", "Directrice"],
        "Directeur adjoint": ["Directeur adjoint", "Directrice adjointe"],
        "Surveillant": ["Surveillant", "Surveillante"],
        "Bibliothécaire": ["Bibliothécaire"],
        "Économe": ["Économe"]
    }
}

@enseignants_bp.route("/")
def liste_enseignants():
    data = request.args
    search = data.get("search", "", type=str)
    per_page = data.get("per_page", 5, type=int)
    page = data.get("page", 1, type=int)

    query = Enseignant.query
    matieres = Matiere.query.with_entities(Matiere.id, Matiere.libelle).all()
    
    # Récupérer toutes les années distinctes de date_fonction
    annees = (
        db.session.query(extract("year", Enseignant.date_fonction).label("annee"))
        .distinct()
        .order_by("annee")
        .all()
    )
    annees = [int(a.annee) for a in annees if a.annee is not None]

    # Recherche dans le texte
    if search:
        query = (
            query.join(Utilisateur, Enseignant.utilisateur)
            .filter(
                (Utilisateur.nom.ilike(f"%{search}%")) |
                (Utilisateur.prenoms.ilike(f"%{search}%")) |
                (cast(Enseignant.date_fonction, String).ilike(f"%{search}%")) |
                (Utilisateur.sexe.ilike(f"%{search}%")) |
                (Utilisateur.email.ilike(f"%{search}%")) |
                (Utilisateur.telephone.ilike(f"%{search}%")) |
                (Enseignant.titre.ilike(f"%{search}%")) |
                (Enseignant.matieres.any(Matiere.libelle.ilike(f"%{search}%")))
            )
        )

    # Filtrage spécifique
    filter_value = data.get("filter", "", type=str)
    query = query.options(joinedload(Enseignant.matieres))

    if filter_value:
        key, val = filter_value.split(":", 1)
        if key == "sexe":
            query = query.join(Utilisateur).filter(Utilisateur.sexe == val)
        elif key == "date_fonction":
            query = query.filter(extract("year", Enseignant.date_fonction) == int(val))
        elif key == "matiere" and val:
            query = query.join(Enseignant.matieres).filter(Matiere.id == int(val))
        elif key in FILTER_DIC and val in FILTER_DIC[key]:
            query = query.filter(getattr(Enseignant, key).in_(FILTER_DIC[key][val]))
        else:
            query = query.filter(getattr(Enseignant, key) == val)

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    enseignants = pagination.items

    # Récupérer l'utilisateur courant
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()
    return render_template("enseignants/ens_liste.html",
                          enseignants=enseignants,
                          pagination=pagination,
                          search=search,
                          per_page=per_page,
                          user_role=user_role,
                          filter_value=filter_value,
                          matieres=matieres,
                          annees=annees)

# --------------CRUD-------------
@enseignants_bp.route("/add", methods=["POST"])
def add_ens():
    data = request.form
    utilisateur_id = data.get("utilisateur_id")

    # Vérification si cet utilisateur est déjà enregistré comme enseignant
    existing_ens = Enseignant.query.filter_by(utilisateur_id=utilisateur_id).first()
    if existing_ens:
        return jsonify({"error": "Cet utilisateur est déjà enregistré comme enseignant"}), 400

    enseignant = Enseignant(
        utilisateur_id=utilisateur_id,
        titre=data.get("titre"),
        date_fonction=data.get("date_fonction"),
        etat="Inactif"
    )
    db.session.add(enseignant)
    db.session.commit()

    # Ajouter les matières sélectionnées
    matieres_ids = request.form.getlist("matiere_id")
    if matieres_ids:
        enseignant.matieres = Matiere.query.filter(Matiere.id.in_(matieres_ids)).all()
        db.session.commit()

    return jsonify({"message": "Ajout réussi"}), 200

@enseignants_bp.route("/update/<string:id>", methods=["POST"])
def update_ens(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    enseignant = Enseignant.query.get_or_404(id)
    # Contrôle sur l'état
    if enseignant.etat.lower() != 'inactif':
        return jsonify({"error": "État non inactif"}), 403
    
    for field in ["titre", "date_fonction"]:
        setattr(enseignant, field, request.form.get(field))
    
    db.session.commit()
    return jsonify({
        "titre": enseignant.titre,
        "date_fonction": enseignant.date_fonction.strftime("%Y-%m-%d")
    })

@enseignants_bp.route("/delete/<string:id>", methods=["POST"])
def delete_ens(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    enseignant = Enseignant.query.get_or_404(id)
    # Contrôle sur l'état
    if enseignant.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de supprimer"}), 403
    
    db.session.delete(enseignant)
    db.session.commit()
    return jsonify({"success": True})

@enseignants_bp.route("/get/<string:enseignant_id>", methods=["GET"])
def get_enseignant(enseignant_id):
    enseignant = Enseignant.query.get_or_404(enseignant_id)
    utilisateur = enseignant.utilisateur if hasattr(enseignant, "utilisateur") else None
    matieres_str = ", ".join([m.libelle for m in enseignant.matieres]) if hasattr(enseignant, "matieres") else ""

    return jsonify({
        "id": str(enseignant.id),
        "nom": utilisateur.nom if utilisateur else "",
        "prenoms": utilisateur.prenoms if utilisateur else "",
        "email": utilisateur.email if utilisateur else "",
        "telephone": utilisateur.telephone if utilisateur else "",
        "sexe": utilisateur.sexe if utilisateur else "",
        "photo_filename": utilisateur.photo_filename if utilisateur else None,
        "matiere": matieres_str,
        "titre": enseignant.titre,
        "etat": enseignant.etat,
        "date_fonction": enseignant.date_fonction.strftime("%d/%m/%Y") if enseignant.date_fonction else ""
    })

@enseignants_bp.route("/detail/<string:id>", methods=["GET"])
def get_ens(id):
    enseignant = Enseignant.query.get_or_404(id)
    utilisateur = enseignant.utilisateur
    matieres_str = ", ".join([m.libelle for m in enseignant.matieres]) if hasattr(enseignant, "matieres") else ""

    return jsonify({
        "id": str(enseignant.id),
        "utilisateur_id": str(enseignant.utilisateur_id),
        "nom": utilisateur.nom,
        "prenoms": utilisateur.prenoms,
        "sexe": utilisateur.sexe,
        "email": utilisateur.email,
        "telephone": utilisateur.telephone,
        "matiere_id": ",".join([str(m.id) for m in enseignant.matieres]) if hasattr(enseignant, "matieres") else "",
        "matiere": matieres_str,
        "titre": enseignant.titre,
        "date_fonction": enseignant.date_fonction.strftime("%Y-%m-%d") if enseignant.date_fonction else None,
        "photo_filename": utilisateur.photo_filename,
        "etat": enseignant.etat
    })

@enseignants_bp.route("/<string:ens_id>/changer_etat", methods=["POST"])
def changer_etat(ens_id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    enseignant = db.session.get(Enseignant, ens_id)
    if not enseignant:
        return jsonify({"error": "Enseignant introuvable"}), 404

    data = request.get_json()
    action = (data.get("action") or "").lower()

    # Définition du workflow
    transitions = {
        "inactif": {"activer": "Actif"},
        "actif": {"muter": "Muté"},
        "muté": {"retraiter": "Retraité"}
    }

    current_etat = (enseignant.etat or "Inactif").lower()
    next_etat = transitions.get(current_etat, {}).get(action)

    if not next_etat:
        return jsonify({"error": f"Action '{action}' invalide pour l'état {enseignant.etat}"}), 400

    enseignant.etat = next_etat
    db.session.commit()

    return jsonify({"message": "État mis à jour", "etat": enseignant.etat})

# ---------------- Routes AJAX pour auto-remplissage ----------------
@enseignants_bp.route("/options", methods=["GET"])
def enseignants_options():
    """
    Renvoie en une seule requête :
      - liste des utilisateurs (id, nom, prenoms, sexe, email, telephone, photo_filename)
      - liste des matieres (id, libelle)
    """
    try:
        users = Utilisateur.query.with_entities(
            Utilisateur.id,
            Utilisateur.nom,
            Utilisateur.prenoms,
            Utilisateur.sexe,
            Utilisateur.email,
            Utilisateur.telephone,
            Utilisateur.photo_filename
        ).all()

        matieres = Matiere.query.with_entities(Matiere.id, Matiere.libelle).all()

        users_list = [
            {
                "id": str(u.id),
                "nom": u.nom,
                "prenoms": u.prenoms,
                "sexe": u.sexe,
                "email": u.email,
                "telephone": u.telephone,
                "photo_filename": u.photo_filename
            } for u in users
        ]

        matieres_list = [
            {"id": str(m.id), "libelle": m.libelle} for m in matieres
        ]

        return jsonify({"utilisateurs": users_list, "matieres": matieres_list}), 200

    except Exception as exc:
        print(f"Erreur lors de l'envoi des options enseignants: {exc}")
        return jsonify({"error": "Impossible de charger les options"}), 500

# ---------------- EXPORTATIONS CORRIGÉES ----------------
@enseignants_bp.route("/export/pdf")
def export_enseignants_pdf():
    """Export PDF de la liste des enseignants - Version corrigée"""
    try:
        # Récupérer tous les enseignants avec leurs relations
        enseignants = Enseignant.query.options(
            joinedload(Enseignant.utilisateur),
            joinedload(Enseignant.matieres)
        ).all()

        # Récupérer les informations de l'école depuis la base de données
        ecole = Ecole.query.first()  # Prend la première école de la base
        nom_ecole = ecole.nom if ecole else "COLLÈGE D'ENSEIGNEMENT GÉNÉRAL 'SAINT BLANT'"
        dre = ecole.dre if ecole and ecole.dre else "MARITIME"
        inspection = ecole.inspection if ecole and ecole.inspection else "TSÉVIÉ"

        # Créer le PDF en mémoire
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            topMargin=15*mm, 
            bottomMargin=15*mm,
            leftMargin=10*mm,
            rightMargin=10*mm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # ========== EN-TÊTE ==========
        # Chemin absolu vers le logo
        logo_path = r"C:\projets\python\gestion_scolaire\app\static\images\logo.png"
        
        # Vérifier si le logo existe
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=35*mm, height=35*mm)
                logo.hAlign = 'CENTER'
            except:
                logo = Paragraph("<b>[LOGO]</b>", styles['Normal'])
        else:
            logo = Paragraph("<b>[LOGO ÉCOLE]</b>", styles['Normal'])
        
        # Style pour l'entête
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Normal'],
            fontSize=9,
            alignment=1,  # Centré
            spaceAfter=0,  # SUPPRIMÉ pour éliminer l'espace
            leading=10
        )
        
        small_header_style = ParagraphStyle(
            'SmallHeader',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,
            spaceAfter=0,  # SUPPRIMÉ pour éliminer l'espace
            leading=8
        )
        
        # CORRECTION : Structure compacte sans espaces entre les lignes
        # Colonne gauche - Ministère (éléments bien groupés)
        left_col_content = [
            Paragraph("<b>MINISTÈRE DES ENSEIGNEMENTS PRIMAIRES ET SECONDAIRE</b>", header_style),
            Paragraph("-----------", small_header_style),
            Paragraph(f"DIRECTION RÉGIONALE DE L'ÉDUCATION - {dre}", header_style),
            Paragraph("-----------", small_header_style),
            Paragraph(f"INSPECTION DE L'ENSEIGNEMENT SECONDAIRE GÉNÉRAL - {inspection}", header_style)
        ]
        
        # Colonne droite - République (éléments bien groupés)
        right_col_content = [
            Paragraph("<b>RÉPUBLIQUE TOGOLAISE</b>", header_style),
            Paragraph("-----------", small_header_style),
            Paragraph("Travail - Liberté - Patrie", ParagraphStyle(
                'DeviseStyle',
                parent=styles['Normal'],
                fontSize=7,
                alignment=1,
                spaceAfter=0,  # SUPPRIMÉ
                leading=8
            ))
        ]
        
        # Colonne centre
        center_col_content = [
            logo,
            Paragraph(f"<b>{nom_ecole}</b>", header_style)
        ]

        # Tableau en-tête avec 3 colonnes
        header_table = Table([[
            left_col_content, 
            center_col_content, 
            right_col_content
        ]], colWidths=[doc.width/3, doc.width/3, doc.width/3])
        
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # SUPPRIMÉ
            ('TOPPADDING', (0, 0), (-1, -1), 0),     # SUPPRIMÉ
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 6*mm))
        
        # Ligne de séparation
        separation_line = Table([['']], colWidths=[doc.width])
        separation_line.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (0, 0), 1, colors.black),
        ]))
        elements.append(separation_line)
        elements.append(Spacer(1, 6*mm))
        
        # ========== TITRE DU DOCUMENT ==========
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=1,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=6
        )
        
        title = Paragraph("LISTE DES ENSEIGNANTS", title_style)
        elements.append(title)
        
        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,
            textColor=colors.gray,
            spaceAfter=8
        )
        
        date_text = Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style)
        elements.append(date_text)
        
        # ========== TABLEAU DES ENSEIGNANTS ==========
        # En-têtes du tableau avec largeurs optimisées
        headers = [
            'Nom & Prénoms',
            'Sexe', 
            'Date prise\nfonction',
            'Téléphone',
            'Email',
            'Matière(s)'
        ]
        
        data = [headers]
        
        for enseignant in enseignants:
            utilisateur = enseignant.utilisateur
            matieres = ", ".join([m.libelle for m in enseignant.matieres]) if enseignant.matieres else "Non assigné"
            date_fonction = enseignant.date_fonction.strftime("%d/%m/%Y") if enseignant.date_fonction else "Non définie"
            
            # Tronquer les textes longs pour éviter les débordements
            email = (utilisateur.email or "Non renseigné")[:25] + "..." if len(utilisateur.email or "") > 25 else (utilisateur.email or "Non renseigné")
            matieres_trunc = matieres[:30] + "..." if len(matieres) > 30 else matieres
            
            row = [
                f"{utilisateur.nom} {utilisateur.prenoms}",
                utilisateur.sexe,
                date_fonction,
                utilisateur.telephone or "Non renseigné",
                email,
                matieres_trunc
            ]
            data.append(row)
        
        # Création du tableau avec largeurs optimisées
        table = Table(data, colWidths=[
            doc.width * 0.22,  # Nom & Prénoms
            doc.width * 0.08,  # Sexe
            doc.width * 0.12,  # Date fonction
            doc.width * 0.14,  # Téléphone
            doc.width * 0.22,  # Email
            doc.width * 0.22   # Matières
        ], repeatRows=1)
        
        # Style du tableau optimisé
        table_style = TableStyle([
            # En-têtes
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 4),
            
            # Lignes de données
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),  # Sexe et date centrés
            ('ALIGN', (2, 1), (-1, -1), 'LEFT'),   # Reste à gauche
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Bordures
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            
            # Alternance des couleurs des lignes
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Padding réduit pour économiser l'espace
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        # ========== STATISTIQUES ==========
        elements.append(Spacer(1, 8*mm))
        
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=0,
            textColor=colors.gray,
            spaceAfter=1
        )
        
        total_enseignants = len(enseignants)
        hommes = sum(1 for e in enseignants if e.utilisateur.sexe and e.utilisateur.sexe.upper() == 'M')
        femmes = total_enseignants - hommes
        
        stats_text = [
            Paragraph(f"<b>STATISTIQUES :</b>", stats_style),
            Paragraph(f"Total enseignants : {total_enseignants}", stats_style),
            Paragraph(f"Hommes : {hommes} | Femmes : {femmes}", stats_style),
        ]
        
        for element in stats_text:
            elements.append(element)
        
        # ========== GÉNÉRATION DU PDF ==========
        doc.build(elements)
        buffer.seek(0)
        
        # Retourner le PDF avec des headers améliorés
        filename = f"liste_enseignants_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
        # Headers supplémentaires pour forcer le téléchargement
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Erreur génération PDF: {str(e)}")
        return jsonify({"error": f"Erreur lors de la génération du PDF: {str(e)}"}), 500

@enseignants_bp.route("/export/excel")
def export_enseignants_excel():
    """Export Excel de la liste des enseignants avec en-tête"""
    try:
        # Récupérer les données
        enseignants = Enseignant.query.options(
            joinedload(Enseignant.utilisateur),
            joinedload(Enseignant.matieres)
        ).all()

        # Récupérer les informations de l'école
        ecole = Ecole.query.first()
        nom_ecole = ecole.nom if ecole else "COLLÈGE D'ENSEIGNEMENT GÉNÉRAL 'SAINT BLANT'"
        prefecture = ecole.prefecture if ecole and ecole.prefecture else "MARITIME"
        inspection = ecole.inspection if ecole and ecole.inspection else "TSÉVIÉ"
        
        # Créer le fichier Excel
        buffer = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Liste des enseignants"
        
        # ========== EN-TÊTE EXCEL ==========
        center_align = Alignment(horizontal="center", vertical="center")
        
        # CORRECTION : Structure organisée comme dans le PDF
        # Ligne 1: Ministère à gauche
        ws.merge_cells('A1:E1')
        ws['A1'] = "MINISTÈRE DES ENSEIGNEMENTS PRIMAIRES ET SECONDAIRE"
        ws['A1'].font = Font(bold=True, size=10)
        ws['A1'].alignment = center_align
        
        # Ligne 1: République à droite
        ws.merge_cells('F1:I1')
        ws['F1'] = "RÉPUBLIQUE TOGOLAISE"
        ws['F1'].font = Font(bold=True, size=10)
        ws['F1'].alignment = center_align
        
        # Ligne 2: tirets
        ws.merge_cells('A2:E2')
        ws['A2'] = "-----------"
        ws['A2'].alignment = center_align
        
        ws.merge_cells('F2:I2')
        ws['F2'] = "-----------"
        ws['F2'].alignment = center_align
        
        # Ligne 3: Direction Régionale
        ws.merge_cells('A3:E3')
        ws['A3'] = f"DIRECTION RÉGIONALE DE L'ÉDUCATION - {prefecture}"
        ws['A3'].font = Font(size=9)
        ws['A3'].alignment = center_align
        
        # Ligne 3: Devise
        ws.merge_cells('F3:I3')
        ws['F3'] = "Travail - Liberté - Patrie"
        ws['F3'].font = Font(bold=True, size=8)
        ws['F3'].alignment = center_align
        
        # Ligne 4: tirets
        ws.merge_cells('A4:E4')
        ws['A4'] = "-----------"
        ws['A4'].alignment = center_align
        
        # Ligne 5: Inspection
        ws.merge_cells('A5:E5')
        ws['A5'] = f"INSPECTION DE L'ENSEIGNEMENT SECONDAIRE GÉNÉRAL - {inspection}"
        ws['A5'].font = Font(size=9)
        ws['A5'].alignment = center_align
        
        # Ligne 6: Nom de l'école (CENTRÉ sur toutes les colonnes)
        ws.merge_cells('A6:I6')
        ws['A6'] = nom_ecole
        ws['A6'].font = Font(bold=True, size=14, color="2C3E50")
        ws['A6'].alignment = center_align
        
        # Ligne 7: Titre du document
        ws.merge_cells('A7:I7')
        ws['A7'] = "LISTE DES ENSEIGNANTS"
        ws['A7'].font = Font(bold=True, size=16, color="2C3E50")
        ws['A7'].alignment = center_align
        
        # Ligne 8: Date de génération
        ws.merge_cells('A8:I8')
        ws['A8'] = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        ws['A8'].font = Font(size=8, italic=True, color="666666")
        ws['A8'].alignment = center_align
        
        # Ligne vide
        ws['A9'] = ""
        
        # ========== TABLEAU DES DONNÉES ==========
        # En-têtes du tableau
        headers = [
            'Nom', 'Prénoms', 'Sexe', 'Date de prise de fonction', 
            'Téléphone', 'Email', 'Matière(s)', 'Titre', 'État'
        ]
        
        # Commencer à la ligne 10 pour les données
        start_row = 10
        ws.append(headers)
        
        # Style des en-têtes du tableau
        table_header_fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
        table_header_font = Font(color="FFFFFF", bold=True)
        
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=start_row, column=col)
            cell.fill = table_header_fill
            cell.font = table_header_font
            cell.alignment = center_align
        
        # Données
        for enseignant in enseignants:
            utilisateur = enseignant.utilisateur
            matieres = ", ".join([m.libelle for m in enseignant.matieres]) if enseignant.matieres else "Non assigné"
            date_fonction = enseignant.date_fonction.strftime("%d/%m/%Y") if enseignant.date_fonction else "Non définie"
            
            row = [
                utilisateur.nom,
                utilisateur.prenoms,
                utilisateur.sexe,
                date_fonction,
                utilisateur.telephone or "Non renseigné",
                utilisateur.email or "Non renseigné",
                matieres,
                enseignant.titre,
                enseignant.etat
            ]
            ws.append(row)
        
        # ========== MISE EN FORME FINALE ==========
        # Ajuster la largeur des colonnes
        column_widths = {
            'A': 20, 'B': 20, 'C': 8, 'D': 18, 
            'E': 15, 'F': 25, 'G': 30, 'H': 15, 'I': 12
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Centrer le sexe
        for row in range(start_row + 1, ws.max_row + 1):
            ws[f'C{row}'].alignment = center_align
        
        # Ajouter des bordures au tableau
        from openpyxl.styles import Border, Side
        thin_border = Border(
            left=Side(style='thin'), 
            right=Side(style='thin'), 
            top=Side(style='thin'), 
            bottom=Side(style='thin')
        )
        
        for row in range(start_row, ws.max_row + 1):
            for col in range(1, len(headers) + 1):
                ws.cell(row=row, column=col).border = thin_border
        
        # ========== STATISTIQUES ==========
        stats_row = ws.max_row + 2
        total_enseignants = len(enseignants)
        hommes = sum(1 for e in enseignants if e.utilisateur.sexe and e.utilisateur.sexe.upper() == 'M')
        femmes = total_enseignants - hommes
        
        ws.merge_cells(f'A{stats_row}:I{stats_row}')
        ws[f'A{stats_row}'] = "STATISTIQUES"
        ws[f'A{stats_row}'].font = Font(bold=True, size=10)
        
        ws.merge_cells(f'A{stats_row + 1}:I{stats_row + 1}')
        ws[f'A{stats_row + 1}'] = f"Total enseignants : {total_enseignants} | Hommes : {hommes} | Femmes : {femmes}"
        ws[f'A{stats_row + 1}'].font = Font(size=9)
        
        # Sauvegarder
        wb.save(buffer)
        buffer.seek(0)
        
        # Retourner le fichier avec des headers améliorés
        filename = f"liste_enseignants_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Headers supplémentaires pour forcer le téléchargement
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Erreur génération Excel: {str(e)}")
        return jsonify({"error": f"Erreur lors de la génération du Excel: {str(e)}"}), 500
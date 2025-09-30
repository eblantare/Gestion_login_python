from flask import Blueprint, render_template, request, jsonify, send_file
from extensions import db
from ..models import Eleve, Classe, Ecole
from sqlalchemy import cast, String
from flask_login import current_user
import uuid
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from datetime import datetime
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill


eleves_bp = Blueprint(
    "eleves",
    __name__
)


def is_admin():
    return getattr(current_user,"role","").lower() in ["admin", "administrateur"]

@eleves_bp.route("/add",methods=["POST"])
def add_eleve():
    if request.method == 'POST':
        data = request.form
        matricule = data.get('matricule')
        nom = data.get('nom')
        prenoms = data.get('prenoms')
        date_naissance = data.get('date_naissance')
        sexe = data.get('sexe')
        status = data.get('status','Nouveau')
        classe_id = data.get('classe_id')#Récupère l'id choisi

        #Si aucun matricule n'est saisi, générer automatiquement
        if not matricule:
            if nom and prenoms:
                initials = f"{nom[0]}{prenoms[0]}".upper()
            elif nom:
                 initials = nom[0].upper()
            else:
                initials = "X"
            matricule = f"{initials}-{uuid.uuid4().hex[:6].upper()}"

                #vérifier l'unicité
        if Eleve.query.filter_by(matricule=matricule).first():
           return jsonify({"error":"Ce matricule existe déjà"}), 400
        

        eleve = Eleve(matricule=matricule,nom=nom,prenoms=prenoms,date_naissance=date_naissance,
                       sexe=sexe, status=status,classe_id=classe_id, etat="Inactif")        
        db.session.add(eleve)
        db.session.commit()
        
        return jsonify({"message": "Ajout réussi", "matricule":matricule}), 200

# Définis ton dictionnaire en global (avant la route, dans le fichier)
FILTER_ALIASES = {
    "sexe": {
        "M": ["M", "Masculin"],
        "F": ["F", "Féminin"],
    },
    "status": {
        "Nouveau": ["N", "Nouveau"],
        "Ancien": ["A", "Ancien"],
    },
    "classe": {  # <-- mettre "classe" (singulier) car ton filtre utilise "classe:"
        "6e": ["6e", "6è", "6èm", "Sixième"],
        "5e": ["5e", "5è", "5èm", "Cinquième"],
        "4e": ["4e", "4è", "4èm", "Quatrième"],
        "3e": ["3e", "3è", "3èm", "Troisième"],
        "2nd": ["2nd", "2nd S", "2nd A", "Seconde"],
        "1ère": ["1ère", "1ère A", "1ère D", "1ère C", "Première"],
        "Tle": ["Tle", "Tle A", "Tle D", "Tle C", "Terminale"],
    }
}

@eleves_bp.route("/")
def liste_eleves():
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)

    query = Eleve.query.join(Classe)

    # Recherche texte
    if search:
        query = query.filter(
            (Eleve.nom.ilike(f"%{search}%")) |
            (Eleve.prenoms.ilike(f"%{search}%")) |
            (cast(Eleve.date_naissance, String).ilike(f"%{search}%")) |
            (Eleve.sexe.ilike(f"%{search}%")) |
            (Eleve.status.ilike(f"%{search}%")) |
            (Classe.nom.ilike(f"%{search}%")) |
            (Eleve.etat.ilike(f"%{search}%"))
        )

    # Filtrage spécifique
    filter_value = request.args.get("filter", "", type=str)
    if filter_value:
        filter_map = {
            "sexe": Eleve.sexe,
            "status": Eleve.status,
            "etat": Eleve.etat,
            "classe": Classe.nom   # ✅ filtrage sur le nom de la classe
        }
        if ":" in filter_value:
            key, val = filter_value.split(":", 1)

            if key in FILTER_ALIASES and val in FILTER_ALIASES[key]:
               query = query.filter(filter_map[key].in_(FILTER_ALIASES[key][val]))
            elif key in filter_map:
                 query = query.filter(filter_map[key] == val)
        else:
        # Cas simplifié: on suppose que c’est un alias de classe (6e, 6è, Sixième…)
            for alias, values in FILTER_ALIASES.get("classe", {}).items():
               if filter_value in values or filter_value == alias:
                  query = query.filter(Classe.nom.in_(values))
                  break

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    eleves = pagination.items

    user_role = (getattr(current_user, "role", "guest") or "guest").lower()
    classes = Classe.query.all()
    return render_template("eleves/e_liste.html",
                           eleves=eleves,
                           pagination=pagination,
                           search=search,
                           per_page=per_page,
                           user_role=user_role,
                           filter_value=filter_value,
                           classes=classes)

@eleves_bp.route("/update/<string:id>", methods=["POST"])
def update_eleve(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    eleve = Eleve.query.get_or_404(id)
    #contrôle sur l'état
    if eleve.etat.lower() != 'inactif':
        return jsonify({"error", "Impossible de modifier cet élève, état non inactif"}),403
    data = request.form
    eleve.matricule = data.get("matricule")
    eleve.nom = data.get("nom")
    eleve.prenoms = data.get("prenoms")
    eleve.date_naissance = data.get("date_naissance")
    eleve.sexe = data.get("sexe")
    eleve.status = data.get("status")
    eleve.classe_id = data.get("classe_id")
    db.session.commit() #Indispensable pour la sauveagrde

    # ⚠️ récupérer aussi le nom de la classe
    classe = Classe.query.get(eleve.classe_id)
    return jsonify({
        "id":eleve.id,
        "matricule":eleve.matricule,
        "nom":eleve.nom,
        "prenoms":eleve.prenoms,
        "date_naissance":str(eleve.date_naissance),
        "sexe":eleve.sexe,
        "status":eleve.status,
        "classe_id":eleve.classe_id,
        "classe_nom":classe.nom if classe else "",
        "etat": eleve.etat
    })

@eleves_bp.route("/delete/<string:id>", methods=["POST"])
def delete_eleve(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    eleve = Eleve.query.get_or_404(id)
    #Contrôle sur l'état
    if eleve.etat.lower() != 'inactif':
        return jsonify({"error", "Impossible de supprimer cet élève, état non inactif"})
    db.session.delete(eleve)
    db.session.commit()
    return jsonify({"success": True})

@eleves_bp.route("/detail/<string:id>", methods = ["GET"])
def detail_eleve(id):
    eleve =Eleve.query.get_or_404(id)
    return jsonify(
        {
            "matricule": eleve.matricule,
            "nom": eleve.nom,
            "prenoms": eleve.prenoms,
            "date_naissance": eleve.date_naissance.strftime("%Y-%m-%d") if eleve.date_naissance else None,
            "sexe": eleve.sexe,
            "status": eleve.status,
            "classe": eleve.classe.nom if eleve.classe else None,
            "etat": eleve.etat
        }
    )

@eleves_bp.route("/get/<string:id>" , methods=["GET"])
def get_eleve(id):
    eleve = Eleve.query.get_or_404(id)
    return jsonify(
        {
            "id": str(eleve.id),
            "matricule": eleve.matricule,
            "nom": eleve.nom,
            "prenoms": eleve.prenoms,
            "date_naissance":eleve.date_naissance.strftime("%Y-%m-%d") if eleve.date_naissance else None,
            "sexe": eleve.sexe,
            "status": eleve.status,
            "classe": eleve.classe.nom if eleve.classe else None,
            "etat": eleve.etat
        }
    )


WORKFLOW = {
       "Activer" :{"from": "Inactif", "to": "Actif"},
       "Suspendre" :{"from": "Actif", "to": "Suspendu"},
       "Valider" :{"from": "Suspendu", "to": "Validé"},
       "Sortir" :{"from": "Validé", "to": "Sorti"}
}
@eleves_bp.route("/<string:id>/changer_etat", methods=["POST"])
def changer_etat(id):
    if not is_admin():
        return jsonify({"error", "Accès refusé"}), 403
    eleve = Eleve.query.get_or_404(id)
    action = request.json.get("action")

    if action not in WORKFLOW:
        return jsonify({"error": "Action non valide!"}),400
    
    trans = WORKFLOW[action]
    if eleve.etat != trans["from"]:
        return jsonify({"error": f"L'état actuel est {eleve.etat}, impossible d'appliquer {action}"}),400
    
    eleve.etat = trans["to"]
    db.session.commit()
    return jsonify({"etat": eleve.etat})

# ---------------- EXPORTATIONS ÉLÈVES ----------------
@eleves_bp.route("/export/pdf/<string:classe_id>")
def export_eleves_pdf(classe_id):
    """Export PDF de la liste des élèves par classe"""
    try:
        # Récupérer la classe spécifique
        classe = Classe.query.get_or_404(classe_id)
        
        # Récupérer les élèves de cette classe
        eleves = Eleve.query.filter_by(classe_id=classe_id).order_by(Eleve.nom, Eleve.prenoms).all()
        
        # Calculer les statistiques
        effectif_total = len(eleves)
        garcons = sum(1 for e in eleves if e.sexe and e.sexe.upper() == 'M')
        filles = effectif_total - garcons

        # Récupérer les informations de l'école
        ecole = Ecole.query.first()
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
            alignment=1,
            spaceAfter=0,
            leading=10
        )
        
        small_header_style = ParagraphStyle(
            'SmallHeader',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,
            spaceAfter=0,
            leading=8
        )
        
        # Structure de l'en-tête
        left_col_content = [
            Paragraph("<b>MINISTÈRE DES ENSEIGNEMENTS PRIMAIRES ET SECONDAIRE</b>", header_style),
            Paragraph("-----------", small_header_style),
            Paragraph(f"DIRECTION RÉGIONALE DE L'ÉDUCATION - {dre}", header_style),
            Paragraph("-----------", small_header_style),
            Paragraph(f"INSPECTION DE L'ENSEIGNEMENT SECONDAIRE GÉNÉRAL - {inspection}", header_style)
        ]
        
        right_col_content = [
            Paragraph("<b>RÉPUBLIQUE TOGOLAISE</b>", header_style),
            Paragraph("-----------", small_header_style),
            Paragraph("Travail - Liberté - Patrie", ParagraphStyle(
                'DeviseStyle',
                parent=styles['Normal'],
                fontSize=7,
                alignment=1,
                spaceAfter=0,
                leading=8
            ))
        ]
        
        center_col_content = [
            logo,
            Paragraph(f"<b>{nom_ecole}</b>", header_style)
        ]

        header_table = Table([[
            left_col_content, 
            center_col_content, 
            right_col_content
        ]], colWidths=[doc.width/3, doc.width/3, doc.width/3])
        
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
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
        
        # ========== INFORMATIONS DE LA CLASSE ==========
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=4
        )
        
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=9,
            alignment=1,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=2
        )
        
        # Titre principal
        title = Paragraph(f"LISTE DES ÉLÈVES - CLASSE DE {classe.nom.upper()}", ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=1,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=8
        ))
        elements.append(title)
        
        # Statistiques de la classe
        stats_table_data = [
            [Paragraph(f"<b>Effectif total:</b> {effectif_total} élèves", stats_style),
             Paragraph(f"<b>Garçons:</b> {garcons}", stats_style),
             Paragraph(f"<b>Filles:</b> {filles}", stats_style)],
            [Paragraph(f"<b>Année scolaire:</b> {datetime.now().year}-{datetime.now().year + 1}", stats_style),
             Paragraph("", stats_style),
             Paragraph("", stats_style)]
        ]
        
        stats_table = Table(stats_table_data, colWidths=[doc.width/3, doc.width/3, doc.width/3])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(stats_table)
        
        # Date de génération
        date_text = Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,
            textColor=colors.gray,
            spaceAfter=12
        ))
        elements.append(date_text)
        
        # ========== TABLEAU DES ÉLÈVES ==========
        headers = [
            'Matricule',
            'Nom & Prénoms', 
            'Sexe',
            'Date de naissance',
            'Classe',
            'Statut'
        ]
        
        data = [headers]
        
        for eleve in eleves:
            date_naissance = eleve.date_naissance.strftime("%d/%m/%Y") if eleve.date_naissance else "Non définie"
            
            row = [
                eleve.matricule,
                f"{eleve.nom} {eleve.prenoms}",
                eleve.sexe,
                date_naissance,
                classe.nom,
                eleve.status
            ]
            data.append(row)
        
        # Création du tableau
        table = Table(data, colWidths=[
            doc.width * 0.15,  # Matricule
            doc.width * 0.25,  # Nom & Prénoms
            doc.width * 0.08,  # Sexe
            doc.width * 0.15,  # Date naissance
            doc.width * 0.12,  # Classe
            doc.width * 0.15   # Statut
        ], repeatRows=1)
        
        # Style du tableau
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
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),   # Matricule à gauche
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),   # Nom à gauche
            ('ALIGN', (2, 1), (2, -1), 'CENTER'), # Sexe centré
            ('ALIGN', (3, 1), (3, -1), 'CENTER'), # Date centrée
            ('ALIGN', (4, 1), (4, -1), 'CENTER'), # Classe centrée
            ('ALIGN', (5, 1), (5, -1), 'CENTER'), # Statut centré
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Bordures
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            
            # Alternance des couleurs des lignes
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Padding réduit
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        # ========== GÉNÉRATION DU PDF ==========
        doc.build(elements)
        buffer.seek(0)
        
        # Retourner le PDF
        filename = f"liste_eleves_{classe.nom}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Erreur génération PDF: {str(e)}")
        return jsonify({"error": f"Erreur lors de la génération du PDF: {str(e)}"}), 500

@eleves_bp.route("/export/excel/<string:classe_id>")
def export_eleves_excel(classe_id):
    """Export Excel de la liste des élèves par classe"""
    try:
        # Récupérer la classe spécifique
        classe = Classe.query.get_or_404(classe_id)
        
        # Récupérer les élèves de cette classe
        eleves = Eleve.query.filter_by(classe_id=classe_id).order_by(Eleve.nom, Eleve.prenoms).all()
        
        # Calculer les statistiques
        effectif_total = len(eleves)
        garcons = sum(1 for e in eleves if e.sexe and e.sexe.upper() == 'M')
        filles = effectif_total - garcons

        # Récupérer les informations de l'école
        ecole = Ecole.query.first()
        nom_ecole = ecole.nom if ecole else "COLLÈGE D'ENSEIGNEMENT GÉNÉRAL 'SAINT BLANT'"
        dre = ecole.dre if ecole and ecole.dre else "MARITIME"
        inspection = ecole.inspection if ecole and ecole.inspection else "TSÉVIÉ"
        
        # Créer le fichier Excel
        buffer = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = f"Liste élèves {classe.nom}"
        
        # ========== EN-TÊTE EXCEL ==========
        center_align = Alignment(horizontal="center", vertical="center")
        
        # En-tête institutionnel
        ws.merge_cells('A1:E1')
        ws['A1'] = "MINISTÈRE DES ENSEIGNEMENTS PRIMAIRES ET SECONDAIRE"
        ws['A1'].font = Font(bold=True, size=10)
        ws['A1'].alignment = center_align
        
        ws.merge_cells('F1:I1')
        ws['F1'] = "RÉPUBLIQUE TOGOLAISE"
        ws['F1'].font = Font(bold=True, size=10)
        ws['F1'].alignment = center_align
        
        ws.merge_cells('A2:E2')
        ws['A2'] = "-----------"
        ws['A2'].alignment = center_align
        
        ws.merge_cells('F2:I2')
        ws['F2'] = "-----------"
        ws['F2'].alignment = center_align
        
        ws.merge_cells('A3:E3')
        ws['A3'] = f"DIRECTION RÉGIONALE DE L'ÉDUCATION - {dre}"
        ws['A3'].font = Font(size=9)
        ws['A3'].alignment = center_align
        
        ws.merge_cells('F3:I3')
        ws['F3'] = "Travail - Liberté - Patrie"
        ws['F3'].font = Font(bold=True, size=8)
        ws['F3'].alignment = center_align
        
        ws.merge_cells('A4:E4')
        ws['A4'] = "-----------"
        ws['A4'].alignment = center_align
        
        ws.merge_cells('A5:E5')
        ws['A5'] = f"INSPECTION DE L'ENSEIGNEMENT SECONDAIRE GÉNÉRAL - {inspection}"
        ws['A5'].font = Font(size=9)
        ws['A5'].alignment = center_align
        
        # Nom de l'école
        ws.merge_cells('A6:I6')
        ws['A6'] = nom_ecole
        ws['A6'].font = Font(bold=True, size=14, color="2C3E50")
        ws['A6'].alignment = center_align
        
        # Titre du document avec classe
        ws.merge_cells('A7:I7')
        ws['A7'] = f"LISTE DES ÉLÈVES - CLASSE DE {classe.nom.upper()}"
        ws['A7'].font = Font(bold=True, size=16, color="2C3E50")
        ws['A7'].alignment = center_align
        
        # Statistiques de la classe
        ws.merge_cells('A8:I8')
        ws['A8'] = f"Effectif total: {effectif_total} élèves | Garçons: {garcons} | Filles: {filles} | Année scolaire: {datetime.now().year}-{datetime.now().year + 1}"
        ws['A8'].font = Font(size=10, bold=True)
        ws['A8'].alignment = center_align
        
        # Date de génération
        ws.merge_cells('A9:I9')
        ws['A9'] = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        ws['A9'].font = Font(size=8, italic=True, color="666666")
        ws['A9'].alignment = center_align
        
        # Ligne vide
        ws['A10'] = ""
        
        # ========== TABLEAU DES DONNÉES ==========
        headers = [
            'Matricule', 'Nom', 'Prénoms', 'Sexe', 
            'Date de naissance', 'Classe', 'Statut'
        ]
        
        # Commencer à la ligne 11 pour les données
        start_row = 11
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
        for eleve in eleves:
            date_naissance = eleve.date_naissance.strftime("%d/%m/%Y") if eleve.date_naissance else "Non définie"
            
            row = [
                eleve.matricule,
                eleve.nom,
                eleve.prenoms,
                eleve.sexe,
                date_naissance,
                classe.nom,
                eleve.status
            ]
            ws.append(row)
        
        # ========== MISE EN FORME FINALE ==========
        column_widths = {
            'A': 15, 'B': 20, 'C': 20, 'D': 8, 
            'E': 15, 'F': 12, 'G': 12
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Centrer certaines colonnes
        for row in range(start_row + 1, ws.max_row + 1):
            ws[f'D{row}'].alignment = center_align  # Sexe
            ws[f'E{row}'].alignment = center_align  # Date naissance
            ws[f'F{row}'].alignment = center_align  # Classe
            ws[f'G{row}'].alignment = center_align  # Statut
        
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
        
        # Sauvegarder
        wb.save(buffer)
        buffer.seek(0)
        
        # Retourner le fichier
        filename = f"liste_eleves_{classe.nom}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Erreur génération Excel: {str(e)}")
        return jsonify({"error": f"Erreur lors de la génération du Excel: {str(e)}"}), 500

# Route pour récupérer les classes (pour le select)
@eleves_bp.route("/classes", methods=["GET"])
def get_classes():
    """Renvoie la liste des classes pour le select d'export"""
    classes = Classe.query.order_by(Classe.nom).all()
    classes_list = [{"id": str(classe.id), "nom": classe.nom} for classe in classes]
    return jsonify(classes_list)

# @eleves_bp.route("/")
# def index():
#     return render_template("eleves/index.html")
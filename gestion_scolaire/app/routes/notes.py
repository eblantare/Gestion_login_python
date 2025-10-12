from flask import Blueprint, request, render_template, jsonify
from ..models import Note, Eleve, Matiere, Enseignant, Classe, Enseignement,Ecole
from sqlalchemy import cast, String
from flask_login import current_user
import uuid
from uuid import UUID
from datetime import date
from extensions import db
from sqlalchemy.orm import joinedload
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from flask import send_file
import os

notes_bp = Blueprint('notes', __name__)

# Liste des notes
@notes_bp.route('/')
def liste_notes():
    data = request.args
    search = data.get("search", "", type=str)
    per_page = data.get("per_page", 5, type=int)
    page = data.get("page", 1, type=int)
    eleve_id = data.get("eleve_id", type=str)
    matiere_id = data.get("matiere_id", type=str)
    enseignant_id = data.get("enseignant_id", type=str)
    classe_id = data.get("classe_id", type=str)
    trimestre = data.get("trimestre", type=int)
    annee_scolaire = data.get("annee_scolaire", type=str)

    # CORRECTION : Chargement cohérent des relations avec jointure sur Eleve
    query = Note.query.join(Eleve).options(
        joinedload(Note.eleve),
        joinedload(Note.matiere),
        joinedload(Note.enseignement).joinedload(Enseignement.enseignant).joinedload(Enseignant.utilisateur)
    )

    # Recherche texte
    if search:
        query = query.filter(
            (Note.note1.cast(String).ilike(f"%{search}%")) |
            (Note.note2.cast(String).ilike(f"%{search}%")) |
            (Note.note3.cast(String).ilike(f"%{search}%")) |
            (Note.note_comp.cast(String).ilike(f"%{search}%")) |
            (cast(Note.coefficient, String).ilike(f"%{search}%")) |
            (cast(Note.date_saisie, String).ilike(f"%{search}%"))|
            (Eleve.nom.ilike(f"%{search}%")) |  # Recherche dans le nom de l'élève
            (Eleve.prenoms.ilike(f"%{search}%")) |  # Recherche dans le prénom de l'élève
            (Note.etat.ilike(f"%{search}%"))
        )

    # Filtrage par élève
    if eleve_id and eleve_id.lower() != "none":
        try:
            eleve_uuid = UUID(eleve_id)
            query = query.filter(Note.eleve_id == eleve_uuid)
        except ValueError:
            pass

    # Filtrage par matière
    if matiere_id and matiere_id.lower() != "none":
        try:
            matiere_uuid = UUID(matiere_id)
            query = query.filter(Note.matiere_id == matiere_uuid)
        except ValueError:
            pass

    # Filtrage par enseignant
    if enseignant_id and enseignant_id.lower() != "none":
       try:
          enseignant_uuid = UUID(enseignant_id)
          query = query.join(Note.enseignement).filter(Enseignement.enseignant_id == enseignant_uuid)
       except ValueError:
          pass
    
    # CORRECTION : Filtrage par classe via Eleve (déjà joint)
    if classe_id and classe_id.lower() != "none":
        try:
            classe_uuid = UUID(classe_id)
            query = query.filter(Eleve.classe_id == classe_uuid)
        except ValueError:
            pass

    # Filtrage par trimestre et année scolaire
    if trimestre:
        query = query.filter(Note.trimestre == trimestre)
    if annee_scolaire:
        query = query.filter(Note.annee_scolaire == annee_scolaire)
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    notes = pagination.items

    user_role = (getattr(current_user, "role", "guest") or "guest").lower()
    eleves = Eleve.query.all()
    matieres = Matiere.query.all()
    enseignants = Enseignant.query.options(joinedload(Enseignant.utilisateur)).all()
    classes = Classe.query.all()  # AJOUT: Récupérer les classes pour le filtre
    types = Matiere.query.filter(Matiere.parent_id.is_(None)).options(joinedload(Matiere.children)).all()

    annees_scolaires = db.session.query(Note.annee_scolaire).distinct().all()
    annees_scolaires = [a[0] for a in annees_scolaires]
    
    return render_template("notes/list_notes.html",
        notes=notes,
        pagination=pagination,
        search=search,
        per_page=per_page,
        user_role=user_role,
        eleves=eleves,
        matieres=matieres,
        enseignants=enseignants,
        classes=classes,  # AJOUT: Passer les classes au template
        types=types,
        eleve_id=eleve_id,
        matiere_id=matiere_id,
        enseignant_id=enseignant_id,
        classe_id=classe_id,
        trimestre=trimestre,
        annee_scolaire=annee_scolaire,
        annees_scolaires=annees_scolaires
    )

@notes_bp.route("/add", methods=["POST"])
def add_note():
    try:
        data = request.json
        
        # Validation
        required_fields = ['eleve_id', 'matiere_id', 'enseignant_id', 'trimestre', 'annee_scolaire']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Le champ {field} est requis"}), 400

        # Vérifications de base
        eleve = Eleve.query.get(data.get("eleve_id"))
        if not eleve or not eleve.classe_id:
            return jsonify({"error": "Élève ou classe introuvable"}), 400

        # Conversion UUID
        try:
            matiere_uuid = UUID(data.get("matiere_id"))
            enseignant_uuid = UUID(data.get("enseignant_id"))
        except ValueError:
            return jsonify({"error": "IDs invalides"}), 400

        # CORRECTION STRICTE : Vérifier d'abord si une note existe déjà
        note_existante = Note.query.filter_by(
            eleve_id=eleve.id,
            matiere_id=matiere_uuid,
            trimestre=data.get("trimestre", 1),
            annee_scolaire=data.get("annee_scolaire")
        ).first()

        # CORRECTION STRICTE : Si une note existe déjà, refuser la création
        if note_existante:
            return jsonify({
                "error": "Une note existe déjà pour cet élève dans cette matière pour ce trimestre. Veuillez modifier la note existante au lieu d'en créer une nouvelle."
            }), 400

        # Gestion enseignement (seulement si aucune note n'existe)
        enseignement = Enseignement.query.filter_by(
            matiere_id=matiere_uuid,
            enseignant_id=enseignant_uuid,
            classe_id=eleve.classe_id
        ).first()

        if not enseignement:
            if not Enseignant.query.get(enseignant_uuid):
                return jsonify({"error": "Enseignant introuvable"}), 400
                
            enseignement = Enseignement(
                id=uuid.uuid4(),
                matiere_id=matiere_uuid,
                enseignant_id=enseignant_uuid,
                classe_id=eleve.classe_id
            )
            db.session.add(enseignement)
            db.session.flush()

        # Récupérer les nouvelles notes
        note1 = float(data.get("note1")) if data.get("note1") else None
        note2 = float(data.get("note2")) if data.get("note2") else None
        note3 = float(data.get("note3")) if data.get("note3") else None
        note_comp = float(data.get("note_comp")) if data.get("note_comp") else None

        # Création nouvelle note (on est sûr qu'aucune n'existe)
        nouvelle_note = Note(
            id=uuid.uuid4(),
            note1=note1,
            note2=note2,
            note3=note3,
            note_comp=note_comp,
            coefficient=data.get("coefficient", 1),
            date_saisie=date.today(),
            eleve_id=eleve.id,
            matiere_id=matiere_uuid,
            enseignement_id=enseignement.id,
            trimestre=data.get("trimestre", 1),
            annee_scolaire=data.get("annee_scolaire"),
            etat="Actif"
        )
        db.session.add(nouvelle_note)
        db.session.commit()

        # Recharger et retourner réponse
        note_finale = Note.query.options(
            joinedload(Note.eleve),
            joinedload(Note.matiere),
            joinedload(Note.enseignement).joinedload(Enseignement.enseignant).joinedload(Enseignant.utilisateur)
        ).get(nouvelle_note.id)

        row_html = render_template("notes/_note_row.html", note=note_finale)
        return jsonify({
            "message": "Note enregistrée avec succès",
            "note_html": row_html,
            "note_id": str(note_finale.id)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur: {str(e)}"}), 500



# Éditer une note
@notes_bp.route("/<string:note_id>/edit", methods=["PUT"])
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    data = request.json
    if note.cloture:
        return jsonify({"error": "Ce trimestre est clôturé, modification impossible"}), 400

    try:
        note.note1 = float(data.get("note1")) if data.get("note1") else note.note1
        note.note2 = float(data.get("note2")) if data.get("note2") else note.note2
        note.note3 = float(data.get("note3")) if data.get("note3") else note.note3
        note.note_comp = float(data.get("note_comp")) if data.get("note_comp") else note.note_comp
        note.coefficient = int(data.get("coefficient")) if data.get("coefficient") else note.coefficient
        note.trimestre = int(data.get("trimestre")) if data.get("trimestre") else note.trimestre
        note.annee_scolaire = data.get("annee_scolaire", note.annee_scolaire)
        note.etat = data.get("etat", note.etat)
        note.date_saisie = date.today()
  # ← Ajouter ici la mise à jour de l'enseignant
        if "enseignement_id" in data:note.enseignement_id = data["enseignement_id"]
        db.session.commit()

        row_html = render_template("notes/_note_row.html", note=note)
        return jsonify({"message": "Note mise à jour avec succès", "note_html": row_html}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Sérialisation récursive pour arborescence matières
def serialize_matiere(matiere):
    return {
        "id": str(matiere.id),
        "libelle": matiere.libelle,
        "parent_id": str(matiere.parent_id) if matiere.parent_id else None,
        "children": [serialize_matiere(c) for c in matiere.children]
    }

# Endpoint pour récupérer élèves, matières et classes (JSON)
@notes_bp.route("/list_elements", methods=["GET"])
def list_elements():
    eleves = Eleve.query.all()
    matieres = Matiere.query.all()
    enseignants = Enseignant.query.all()
    classes = Classe.query.all()
    

    # 🔹 Construire les catégories à partir du champ "type"
    types_dict = {}
    for m in matieres:
        type_lib = m.type or "Autres"
        if type_lib not in types_dict:
            types_dict[type_lib] = {
                "id": f"type_{type_lib.lower().replace(' ', '_')}",
                "libelle": type_lib,
                "children": []
            }
        types_dict[type_lib]["children"].append({
            "id": str(m.id),
            "code": m.code,
            "libelle": m.libelle,
            "etat": m.etat
        })

    # 🔹 Classes disponibles
    classes_data = [{"id": str(c.id), "nom": c.nom} for c in classes]

    data = {
        "eleves": [
            {"id": str(e.id), "nom": e.nom, "prenoms": e.prenoms, "classe_id": str(e.classe_id)}
            for e in eleves
        ],
        "matieres": list(types_dict.values()),  # ← regroupées dynamiquement
        "classes": classes_data,
       "enseignants" : [
      {
        "id": str(e.id),
        "noms": e.utilisateur.nom,
        "prenoms": e.utilisateur.prenoms
      }
      for e in enseignants if e.utilisateur
   ]
    }
    return jsonify(data)


# Route JSON pour liste filtrée des notes
@notes_bp.route("/list", methods=["GET"])
def list_notes_json():
    classe_id = request.args.get("classe_id", type=str)
    trimestre = request.args.get("trimestre", type=int)
    annee_scolaire = request.args.get("annee_scolaire", type=str)

    query = Note.query.join(Eleve).options(
        joinedload(Note.eleve),
        joinedload(Note.matiere),
        joinedload(Note.enseignement).joinedload(Enseignement.enseignant).joinedload(Enseignant.utilisateur)
    )

    # Filtrage par classe
    if classe_id and classe_id.lower() != "none":
        try:
            query = query.filter(Eleve.classe_id == UUID(classe_id))
        except ValueError:
            pass

    # Filtrage par trimestre
    if trimestre:
        query = query.filter(Note.trimestre == trimestre)
    # Filtrage par année scolaire
    if annee_scolaire:
        query = query.filter(Note.annee_scolaire == annee_scolaire)

    notes = query.all()

    return jsonify([
        {
            "id": str(n.id),
            "eleve_nom": n.eleve.nom if n.eleve else "",
            "eleve_prenoms": n.eleve.prenoms if n.eleve else "",
            "matiere_nom": n.matiere.libelle if n.matiere else "",
            "enseignant_nom": n.enseignement.enseignant.utilisateur.nom if n.enseignement and n.enseignement.enseignant else "",
            "enseignant_prenoms": n.enseignement.enseignant.utilisateur.prenoms if n.enseignement and n.enseignement.enseignant else "",
            "note1": n.note1,
            "note2": n.note2,
            "note3": n.note3,
            "note_comp": n.note_comp,
            "coefficient": n.coefficient,
            "trimestre": n.trimestre,
            "annee_scolaire": n.annee_scolaire
        } for n in notes
    ])



#récupération des détails d'une note.
@notes_bp.route("/<string:note_id>", methods=["GET"])
def get_notes(note_id):
       # CORRECTION : Charger toutes les relations nécessaires
    note = Note.query.options(
        joinedload(Note.eleve),
        joinedload(Note.matiere),
        joinedload(Note.enseignement).joinedload(Enseignement.enseignant).joinedload(Enseignant.utilisateur)
    ).get(note_id)
    if not note:
        return jsonify({"error": "Note non trouvée"}), 404

    # CORRECTION : Récupérer correctement le nom de l'enseignant
    enseignant_nom = ""
    enseignant_prenoms = ""
    
    if note.enseignement and note.enseignement.enseignant:
        if note.enseignement.enseignant.utilisateur:
            enseignant_nom = note.enseignement.enseignant.utilisateur.nom or ""
            enseignant_prenoms = note.enseignement.enseignant.utilisateur.prenoms or ""
        else:
            # Fallback si pas d'utilisateur associé
            enseignant_nom = getattr(note.enseignement.enseignant, 'nom', '') or getattr(note.enseignement.enseignant, 'noms', '')
            enseignant_prenoms = getattr(note.enseignement.enseignant, 'prenoms', '')
    return jsonify({
        "id": str(note.id),
        "note1": note.note1,
        "note2": note.note2,
        "note3": note.note3,
        "note_comp": note.note_comp,
        "coefficient": note.coefficient,
        "eleve_id": str(note.eleve_id),
        "matiere_id": str(note.matiere_id),
        "enseignant_id": str(note.enseignement.enseignant_id) if note.enseignement else None,
        "etat": note.etat,
        "date": note.date_saisie.isoformat() if note.date_saisie else None,
        "eleve_nom": f"{note.eleve.nom} {note.eleve.prenoms}" if note.eleve else "",
        "matiere_nom": note.matiere.libelle if note.matiere else "",
        "enseignant_nom": enseignant_nom,
        "enseignant_prenoms": enseignant_prenoms,
        "trimestre": note.trimestre,
        "annee_scolaire":note.annee_scolaire,
        "valeur": note.note1 or note.note2 or note.note3 or note.note_comp
    })

@notes_bp.route("/<string:note_id>/delete", methods=["DELETE"])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    try:
        db.session.delete(note)
        db.session.commit()
        return jsonify({"message": "Note supprimée avec succès"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Récupérer les années/trimestres actifs (non clôturés)
@notes_bp.route("/clotures/actifs", methods=["GET"])
def clotures_actifs():
    if getattr(current_user, "role", "guest").lower() != "admin":
        return jsonify({"error": "Non autorisé"}), 403

    actifs = db.session.query(Note.annee_scolaire, Note.trimestre).filter(
        Note.cloture == False
    ).distinct().all()

    return jsonify([
        {"annee": a, "trimestre": t} for a, t in actifs
    ])


# Clôturer une année/trimestre
@notes_bp.route("/clotures/close", methods=["POST"])
def cloturer_periode():
    if getattr(current_user, "role", "guest").lower() != "admin":
        return jsonify({"error": "Non autorisé"}), 403

    data = request.json
    annee = data.get("annee")
    trimestre = data.get("trimestre")

    # Vérification période antérieure
    today = date.today()
    current_annee = f"{today.year if today.month >= 8 else today.year-1}-{today.year+1 if today.month >= 8 else today.year}"
    current_trimestre = ((today.month - 8) // 3 + 1) if today.month >= 8 else ((today.month + 4) // 3)

    if annee == current_annee and (trimestre is None or trimestre >= current_trimestre):
        return jsonify({"error": "Impossible de clôturer une période en cours ou future"}), 400

    try:
        # Si le trimestre n'est pas précisé, clôturer tous les trimestres de l'année
        if trimestre is None:
            notes = Note.query.filter_by(annee_scolaire=annee, cloture=False).all()
        else:
            notes = Note.query.filter_by(annee_scolaire=annee, trimestre=trimestre, cloture=False).all()
        for n in notes:
            n.cloture = True
            n.etat = "Clôturé"
        db.session.commit()
        return jsonify({"message": f"Période {annee} - Trimestre {trimestre or 'Tous'} clôturée avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Récupérer uniquement les années scolaires actives (non clôturées)
from datetime import date

@notes_bp.route("/annees/actives", methods=["GET"])
def annees_actives():
    today = date.today()
    current_year = today.year if today.month >= 8 else today.year - 1
    next_year = current_year + 1

    annees_possibles = [f"{current_year}-{current_year+1}", f"{next_year}-{next_year+1}"]

    actifs = db.session.query(Note.annee_scolaire).filter(
        Note.cloture == False
    ).distinct().all()
    actifs = [a[0] for a in actifs]

    # On garde seulement celles qui ne sont pas clôturées
    annees = [a for a in annees_possibles if a in actifs]
    if not annees:
        annees = [annees_possibles[0]]

    return jsonify(annees)


# ---------------- EXPORTATIONS NOTES ----------------
@notes_bp.route("/export/pdf", methods=["GET"])
def export_notes_pdf():
    """Export PDF de la liste des notes avec filtres"""
    try:
        # Récupérer les paramètres de filtrage
        classe_id = request.args.get("classe_id", type=str)
        trimestre = request.args.get("trimestre", type=int)
        annee_scolaire = request.args.get("annee_scolaire", type=str)
        matiere_id = request.args.get("matiere_id", type=str)

        # Construire la requête avec les mêmes filtres que la liste
        query = Note.query.join(Eleve).options(
            joinedload(Note.eleve),
            joinedload(Note.matiere),
            joinedload(Note.enseignement).joinedload(Enseignement.enseignant).joinedload(Enseignant.utilisateur)
        )

        # Appliquer les filtres
        if classe_id and classe_id.lower() != "none":
            try:
                query = query.filter(Eleve.classe_id == UUID(classe_id))
            except ValueError:
                pass

        if trimestre:
            query = query.filter(Note.trimestre == trimestre)
            
        if annee_scolaire:
            query = query.filter(Note.annee_scolaire == annee_scolaire)
            
        if matiere_id and matiere_id.lower() != "none":
            try:
                matiere_uuid = UUID(matiere_id)
                query = query.filter(Note.matiere_id == matiere_uuid)
            except ValueError:
                pass

        notes = query.order_by(Eleve.nom, Eleve.prenoms).all()

        # Récupérer les informations pour l'en-tête
        classe = None
        matiere = None
        enseignant = None
        
        if classe_id and classe_id.lower() != "none":
            classe = Classe.query.get(UUID(classe_id))
            
        if matiere_id and matiere_id.lower() != "none":
            matiere = Matiere.query.get(UUID(matiere_id))
            
        # Calculer l'effectif composant (élèves avec au moins une note)
        effectif_composant = len(set(note.eleve_id for note in notes))

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
        
        # Structure de l'en-tête (similaire à élèves)
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
        
        # ========== INFORMATIONS DES NOTES - ALIGNEMENT HORIZONTAL ==========
        info_style = ParagraphStyle(
          'InfoStyle',
           parent=styles['Normal'],
           fontSize=10,
           alignment=0,
           textColor=colors.HexColor('#2C3E50'),
           spaceAfter=0,
           leading=12
        )

        # Titre principal
        title = Paragraph("LISTE DES NOTES", ParagraphStyle(
           'TitleStyle',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=1,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=12
        ))
        elements.append(title)

        # Informations détaillées en tableau horizontal
        info_data_line1 = [
             f"Année scolaire: {annee_scolaire or 'Non spécifiée'}",
             f"Trimestre: {trimestre or 'Non spécifié'}", 
             f"Matière: {matiere.libelle if matiere else 'Toutes'}"
        ]
        info_table_line1 = Table([info_data_line1], colWidths=[doc.width/3, doc.width/3, doc.width/3])
        info_table_line1.setStyle(TableStyle([
             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
             ('FONTSIZE', (0, 0), (-1, -1), 10),
             ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
             ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
             ('TOPPADDING', (0, 0), (-1, -1), 4),
       ]))

        elements.append(info_table_line1)
        
        info_data_line2 =  [
             f"Classe: {classe.nom if classe else 'Toutes'}",
             f"Effectif composant: {effectif_composant} élèves",
             f"Date de saisie: {datetime.now().strftime('%d/%m/%Y')}"
        ]
        info_table_line2 = Table([info_data_line2], colWidths=[doc.width/3, doc.width/3, doc.width/3])
        info_table_line2.setStyle(TableStyle([
           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
           ('FONTSIZE', (0, 0), (-1, -1), 10),
           ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
           ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
           ('TOPPADDING', (0, 0), (-1, -1), 4),
       ]))

        elements.append(info_table_line2)
        elements.append(Spacer(1, 8*mm))
        
        # ========== TABLEAU DES NOTES AVEC COLONNE MATIÈRE ==========
        headers = [
            'N°',
            'Nom & Prénoms',
            'Matière',  # NOUVELLE COLONNE AJOUTÉE ICI
            'Note 1',
            'Note 2', 
            'Note 3',
            'Note Comp.',
            'Coefficient'
        ]
        
        data = [headers]
        
        # Ajouter les données avec numérotation
        for index, note in enumerate(notes, 1):
            row = [
                str(index),  # Numéro d'ordre
                f"{note.eleve.nom} {note.eleve.prenoms}" if note.eleve else "N/A",
                note.matiere.libelle if note.matiere else "N/A",  # NOUVELLE COLONNE
                str(note.note1) if note.note1 is not None else "-",
                str(note.note2) if note.note2 is not None else "-",
                str(note.note3) if note.note3 is not None else "-",
                str(note.note_comp) if note.note_comp is not None else "-",
                str(note.coefficient) if note.coefficient else "1"
            ]
            data.append(row)
        
        # Ajustement des largeurs de colonnes avec la nouvelle colonne Matière
        table = Table(data, colWidths=[
            doc.width * 0.04,  # N° (4%)
            doc.width * 0.20,  # Nom & Prénoms (20%)
            doc.width * 0.18,  # Matière (18%) - NOUVELLE COLONNE
            doc.width * 0.08,  # Note 1 (8%)
            doc.width * 0.08,  # Note 2 (8%)
            doc.width * 0.08,  # Note 3 (8%)
            doc.width * 0.14,  # Note Comp. (14%)
            doc.width * 0.12   # Coefficient (12%)
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
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),   # N° centré
            ('ALIGN', (1, 1), (2, -1), 'LEFT'),     # Nom et Matière à gauche
            ('ALIGN', (3, 1), (-1, -1), 'CENTER'),  # Notes centrées
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
        def add_page_number(canvas, doc):
            """Ajoute les numéros de page au PDF"""
            page_num = canvas.getPageNumber()
            text = f"Page {page_num}"
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(doc.pagesize[0] - 20, 20, text)
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buffer.seek(0)
        
        # Nom du fichier
        filename = f"releve_notes"
        if classe:
            filename += f"_{classe.nom}"
        if matiere:
            filename += f"_{matiere.libelle}"
        filename += f"_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
        return response
        
    except Exception as e:
        print(f"Erreur génération PDF notes: {str(e)}")
        return jsonify({"error": f"Erreur lors de la génération du PDF: {str(e)}"}), 500
    
@notes_bp.route("/export/excel", methods=["GET"])
def export_notes_excel():
    """Export Excel de la liste des notes avec filtres"""
    try:
        # Récupérer les paramètres de filtrage
        classe_id = request.args.get("classe_id", type=str)
        trimestre = request.args.get("trimestre", type=int)
        annee_scolaire = request.args.get("annee_scolaire", type=str)
        matiere_id = request.args.get("matiere_id", type=str)

        # Construire la requête (identique à PDF)
        query = Note.query.join(Eleve).options(
            joinedload(Note.eleve),
            joinedload(Note.matiere),
            joinedload(Note.enseignement).joinedload(Enseignement.enseignant).joinedload(Enseignant.utilisateur)
        )

        if classe_id and classe_id.lower() != "none":
            try:
                query = query.filter(Eleve.classe_id == UUID(classe_id))
            except ValueError:
                pass

        if trimestre:
            query = query.filter(Note.trimestre == trimestre)
            
        if annee_scolaire:
            query = query.filter(Note.annee_scolaire == annee_scolaire)
            
        if matiere_id and matiere_id.lower() != "none":
            try:
                matiere_uuid = UUID(matiere_id)
                query = query.filter(Note.matiere_id == matiere_uuid)
            except ValueError:
                pass

        notes = query.order_by(Eleve.nom, Eleve.prenoms).all()

        # Récupérer les informations pour l'en-tête
        classe = None
        matiere = None
        
        if classe_id and classe_id.lower() != "none":
            classe = Classe.query.get(UUID(classe_id))
            
        if matiere_id and matiere_id.lower() != "none":
            matiere = Matiere.query.get(UUID(matiere_id))
            
        effectif_composant = len(set(note.eleve_id for note in notes))

        # Récupérer les informations de l'école
        ecole = Ecole.query.first()
        nom_ecole = ecole.nom if ecole else "COLLÈGE D'ENSEIGNEMENT GÉNÉRAL 'SAINT BLANT'"
        dre = ecole.dre if ecole and ecole.dre else "MARITIME"
        inspection = ecole.inspection if ecole and ecole.inspection else "TSÉVIÉ"
        
        # Créer le fichier Excel
        buffer = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        
        # Titre de l'onglet
        ws.title = "Relevé de notes"
        
        # ========== EN-TÊTE EXCEL CORRIGÉ ==========
        center_align = Alignment(horizontal="center", vertical="center")
        left_align = Alignment(horizontal="left", vertical="center")
        right_align = Alignment(horizontal="right", vertical="center")

        # CORRECTION : Structure simplifiée et compacte
        current_row = 1

        # Ligne 1 - MINISTÈRE à gauche et RÉPUBLIQUE à droite (SUR LA MÊME LIGNE)
        ws.merge_cells(f'A{current_row}:E{current_row}')
        ws[f'A{current_row}'] = "MINISTÈRE DES ENSEIGNEMENTS PRIMAIRES ET SECONDAIRE"
        ws[f'A{current_row}'].font = Font(bold=True, size=11)
        ws[f'A{current_row}'].alignment = left_align

        ws.merge_cells(f'F{current_row}:I{current_row}')
        ws[f'F{current_row}'] = "RÉPUBLIQUE TOGOLAISE"
        ws[f'F{current_row}'].font = Font(bold=True, size=11)
        ws[f'F{current_row}'].alignment = right_align
        current_row += 1

        # Ligne 2 - DRE à gauche et devise à droite (SUR LA MÊME LIGNE)
        ws.merge_cells(f'A{current_row}:E{current_row}')
        ws[f'A{current_row}'] = f"DIRECTION RÉGIONALE DE L'ÉDUCATION - {dre}"
        ws[f'A{current_row}'].font = Font(size=9)
        ws[f'A{current_row}'].alignment = left_align

        ws.merge_cells(f'F{current_row}:I{current_row}')
        ws[f'F{current_row}'] = "Travail - Liberté - Patrie"
        ws[f'F{current_row}'].font = Font(bold=True, size=9)
        ws[f'F{current_row}'].alignment = right_align
        current_row += 1

        # Ligne 3 - Inspection à gauche (SUR LA MÊME LIGNE)
        ws.merge_cells(f'A{current_row}:E{current_row}')
        ws[f'A{current_row}'] = f"INSPECTION DE L'ENSEIGNEMENT SECONDAIRE GÉNÉRAL - {inspection}"
        ws[f'A{current_row}'].font = Font(size=9)
        ws[f'A{current_row}'].alignment = left_align
        current_row += 1

        # Ligne vide
        current_row += 1

        # Ligne 4 - Nom de l'école (centré)
        ws.merge_cells(f'A{current_row}:I{current_row}')
        ws[f'A{current_row}'] = nom_ecole
        ws[f'A{current_row}'].font = Font(bold=True, size=14, color="2C3E50")
        ws[f'A{current_row}'].alignment = center_align
        current_row += 1

        # Ligne 5 - Titre du document (centré)
        ws.merge_cells(f'A{current_row}:I{current_row}')
        ws[f'A{current_row}'] = "LISTE DES NOTES"
        ws[f'A{current_row}'].font = Font(bold=True, size=16, color="2C3E50")
        ws[f'A{current_row}'].alignment = center_align
        current_row += 1

        # ========== INFORMATIONS DÉTAILLÉES - COMPACTES ==========
        # Première ligne d'informations
        info_row = current_row

        # Année scolaire
        ws.merge_cells(f'A{info_row}:B{info_row}')
        ws[f'A{info_row}'] = f"Année scolaire: {annee_scolaire or 'Non spécifiée'}"
        ws[f'A{info_row}'].font = Font(size=9, bold=True)
        ws[f'A{info_row}'].alignment = left_align

        # Trimestre
        ws.merge_cells(f'C{info_row}:D{info_row}')
        ws[f'C{info_row}'] = f"Trimestre: {trimestre or 'Non spécifié'}"
        ws[f'C{info_row}'].font = Font(size=9, bold=True)
        ws[f'C{info_row}'].alignment = center_align

        # Matière
        ws.merge_cells(f'E{info_row}:F{info_row}')
        ws[f'E{info_row}'] = f"Matière: {matiere.libelle if matiere else 'Toutes'}"
        ws[f'E{info_row}'].font = Font(size=9, bold=True)
        ws[f'E{info_row}'].alignment = center_align

        # Classe
        ws.merge_cells(f'G{info_row}:I{info_row}')
        ws[f'G{info_row}'] = f"Classe: {classe.nom if classe else 'Toutes'}"
        ws[f'G{info_row}'].font = Font(size=9, bold=True)
        ws[f'G{info_row}'].alignment = right_align

        current_row += 1

        # Deuxième ligne d'informations
        info_row2 = current_row

        # Effectif composant
        ws.merge_cells(f'A{info_row2}:C{info_row2}')
        ws[f'A{info_row2}'] = f"Effectif composant: {effectif_composant} élèves"
        ws[f'A{info_row2}'].font = Font(size=9, bold=True)
        ws[f'A{info_row2}'].alignment = left_align

        # Date de génération
        ws.merge_cells(f'D{info_row2}:I{info_row2}')
        ws[f'D{info_row2}'] = f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws[f'D{info_row2}'].font = Font(size=9, bold=True)
        ws[f'D{info_row2}'].alignment = right_align

        current_row += 1  # Une seule ligne vide avant le tableau

        # ========== TABLEAU DES DONNÉES ==========
        headers = [
            'N°',
            'Nom & Prénoms', 
            'Matière',  # NOUVELLE COLONNE AJOUTÉE ICI
            'Note 1', 
            'Note 2', 
            'Note 3', 
            'Note Composition', 
            'Coefficient'
        ]
        
        # En-têtes du tableau
        table_header_fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
        table_header_font = Font(color="FFFFFF", bold=True)
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col)
            cell.value = header
            cell.fill = table_header_fill
            cell.font = table_header_font
            cell.alignment = center_align
        
        current_row += 1
        
        # CORRECTION : Données avec numérotation - COLONNES CORRECTES
        for index, note in enumerate(notes, 1):
            ws.cell(row=current_row, column=1).value = index  # Numéro d'ordre
            ws.cell(row=current_row, column=2).value = f"{note.eleve.nom} {note.eleve.prenoms}" if note.eleve else "N/A"
            ws.cell(row=current_row, column=3).value = note.matiere.libelle if note.matiere else "N/A"  # CORRECTION : Colonne 3 = Matière
            ws.cell(row=current_row, column=4).value = note.note1 if note.note1 is not None else "-"    # Colonne 4 = Note 1
            ws.cell(row=current_row, column=5).value = note.note2 if note.note2 is not None else "-"    # Colonne 5 = Note 2
            ws.cell(row=current_row, column=6).value = note.note3 if note.note3 is not None else "-"    # Colonne 6 = Note 3
            ws.cell(row=current_row, column=7).value = note.note_comp if note.note_comp is not None else "-"  # Colonne 7 = Note Comp
            ws.cell(row=current_row, column=8).value = note.coefficient if note.coefficient else 1      # Colonne 8 = Coefficient
            
            current_row += 1
        
        # ========== MISE EN FORME FINALE COMPACTE ==========
        column_widths = {
            'A': 5,   # N° (plus étroit)
            'B': 25,  # Nom & Prénoms
            'C': 20,  # Matière (NOUVELLE COLONNE)
            'D': 8,   # Note 1
            'E': 8,   # Note 2
            'F': 8,   # Note 3
            'G': 12,  # Note Composition
            'H': 10,  # Coefficient
            'I': 8    # Colonne supplémentaire
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Centrer les colonnes de notes et le N°
        for row in range(current_row - len(notes), current_row):
            for col in ['A', 'D', 'E', 'F', 'G', 'H']:  # N° et notes centrés
                ws[f'{col}{row}'].alignment = center_align
            
            # Alignement à gauche pour Nom et Matière
            ws[f'B{row}'].alignment = left_align
            ws[f'C{row}'].alignment = left_align
        
        # Ajouter des bordures au tableau
        from openpyxl.styles import Border, Side
        thin_border = Border(
            left=Side(style='thin'), 
            right=Side(style='thin'), 
            top=Side(style='thin'), 
            bottom=Side(style='thin')
        )
        
        # Appliquer les bordures seulement au tableau de données
        table_start_row = current_row - len(notes) - 1  # Ligne des en-têtes du tableau
        for row in range(table_start_row, current_row):
            for col in range(1, len(headers) + 1):  # Ajusté pour 8 colonnes maintenant
                ws.cell(row=row, column=col).border = thin_border
        
        # Sauvegarder
        wb.save(buffer)
        buffer.seek(0)
        
        # Nom du fichier
        filename = f"releve_notes"
        if classe:
            filename += f"_{classe.nom}"
        if matiere:
            filename += f"_{matiere.libelle}"
        filename += f"_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        return response
        
    except Exception as e:
        print(f"Erreur génération Excel notes: {str(e)}")
        return jsonify({"error": f"Erreur lors de la génération du Excel: {str(e)}"}), 500

# Route pour récupérer les filtres d'export (optionnel)
@notes_bp.route("/export/filters", methods=["GET"])
def get_export_filters():
    """Renvoie les filtres disponibles pour l'export"""
    classes = Classe.query.order_by(Classe.nom).all()
    matieres = Matiere.query.order_by(Matiere.libelle).all()
    annees_scolaires = db.session.query(Note.annee_scolaire).distinct().all()
    
    return jsonify({
        "classes": [{"id": str(c.id), "nom": c.nom} for c in classes],
        "matieres": [{"id": str(m.id), "libelle": m.libelle} for m in matieres],
        "annees_scolaires": [a[0] for a in annees_scolaires],
        "trimestres": [1, 2, 3]
    })
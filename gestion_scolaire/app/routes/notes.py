from flask import Blueprint, request, render_template, jsonify
from ..models import Note, Eleve, Matiere
from sqlalchemy import cast, String
from flask_login import current_user
import uuid
from uuid import UUID
from datetime import date
from extensions import db
from sqlalchemy.orm import joinedload

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
    trimestre = data.get("trimestre", type=int)
    annee_scolaire = data.get("annee_scolaire", type=str)

    query = Note.query

    # Recherche texte
    if search:
        query = query.filter(
            (Note.note1.cast(String).ilike(f"%{search}%")) |
            (Note.note2.cast(String).ilike(f"%{search}%")) |
            (Note.note3.cast(String).ilike(f"%{search}%")) |
            (Note.note_comp.cast(String).ilike(f"%{search}%")) |
            (cast(Note.coefficient, String).ilike(f"%{search}%")) |
            (cast(Note.date_saisie, String).ilike(f"%{search}%"))|
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
    types = Matiere.query.filter(Matiere.parent_id.is_(None)).options(joinedload(Matiere.children)).all()

    return render_template("notes/list_notes.html",
        notes=notes,
        pagination=pagination,
        search=search,
        per_page=per_page,
        user_role=user_role,
        eleves=eleves,
        matieres=matieres,
        types=types,
        eleve_id=eleve_id,
        matiere_id=matiere_id,
        trimestre=trimestre,
        annee_scolaire=annee_scolaire
    )

# Ajouter une note
# Ajouter une note
@notes_bp.route("/add", methods=["POST"])
def add_note():
    data = request.json
    eleve_id = data.get("eleve_id")
    matiere_id = data.get("matiere_id")
    trimestre = data.get("trimestre", 1)
    annee_scolaire = data.get("annee_scolaire")
    if not annee_scolaire:
        today = date.today()
        annee_scolaire = f"{today.year if today.month >= 8 else today.year-1}-{today.year+1 if today.month >= 8 else today.year}"

    note1 = float(data.get("note1")) if data.get("note1") else None
    note2 = float(data.get("note2")) if data.get("note2") else None
    note3 = float(data.get("note3")) if data.get("note3") else None
    note_comp = float(data.get("note_comp")) if data.get("note_comp") else None

    try:
        note_record = Note.query.filter_by(
            eleve_id=eleve_id,
            matiere_id=matiere_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire
        ).first()

        # Création si n'existe pas
        if not note_record:
            note_record = Note(
                id=uuid.uuid4(),
                note1=note1,
                note2=note2,
                note3=note3,
                note_comp=note_comp,
                coefficient=data.get("coefficient", 1),
                date_saisie=date.today(),
                eleve_id=eleve_id,
                matiere_id=matiere_id,
                trimestre=trimestre,
                annee_scolaire=annee_scolaire,
                etat="Actif"
            )
            db.session.add(note_record)
        else:
            # Vérifier chaque note individuellement
            if note1 is not None and note_record.note1 is not None:
                return jsonify({"error": "Note 1 déjà saisie pour cet élève et cette matière"}), 400
            if note2 is not None and note_record.note2 is not None:
                return jsonify({"error": "Note 2 déjà saisie pour cet élève et cette matière"}), 400
            if note3 is not None and note_record.note3 is not None:
                return jsonify({"error": "Note 3 déjà saisie pour cet élève et cette matière"}), 400
            if note_comp is not None and note_record.note_comp is not None:
                return jsonify({"error": "Note de composition déjà saisie pour cet élève et cette matière"}), 400

            # Mise à jour uniquement des notes non saisies
            if note1 is not None: note_record.note1 = note1
            if note2 is not None: note_record.note2 = note2
            if note3 is not None: note_record.note3 = note3
            if note_comp is not None: note_record.note_comp = note_comp

            note_record.coefficient = data.get("coefficient", note_record.coefficient)
            note_record.date_saisie = date.today()
            note_record.etat = "Actif"

        db.session.commit()
        row_html = render_template("notes/_note_row.html", note=note_record)
        return jsonify({"message": "Note enregistrée/mise à jour avec succès", "note_html": row_html}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



# Éditer une note
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
    classes = {str(e.classe_id): e.classe.nom for e in eleves if e.classe}

    data = {
        "eleves": [
            {"id": str(e.id), "nom": e.nom, "prenoms": e.prenoms, "classe_id": str(e.classe_id)}
            for e in eleves
        ],
        "matieres": list(types_dict.values()),  # ← regroupées dynamiquement
        "classes": [{"id": cid, "nom": nom} for cid, nom in classes.items()]
    }
    return jsonify(data)



#récupération des détails d'une note.
@notes_bp.route("/<string:note_id>", methods=["GET"])
def get_notes(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Note non trouvée"}), 404

    return jsonify({
        "id": str(note.id),
        "note1": note.note1,
        "note2": note.note2,
        "note3": note.note3,
        "note_comp": note.note_comp,
        "coefficient": note.coefficient,
        "eleve_id": str(note.eleve_id),
        "matiere_id": str(note.matiere_id),
        "etat": note.etat,
        "date": note.date_saisie.isoformat() if note.date_saisie else None,
        "eleve_nom": f"{note.eleve.nom} {note.eleve.prenoms}" if note.eleve else "",
        "matiere_nom": note.matiere.libelle if note.matiere else "",
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
        n# Si le trimestre n'est pas précisé, clôturer tous les trimestres de l'année
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


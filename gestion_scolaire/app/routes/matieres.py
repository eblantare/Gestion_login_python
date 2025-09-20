from flask import Blueprint, render_template, request, jsonify
from extensions import db
from ..models import Matiere
from flask_login import current_user
import uuid

matieres_bp = Blueprint("matieres", __name__, url_prefix="/matieres")

def is_admin():
    return getattr(current_user, "role","").lower() in ["admin", "administrateur"]

@matieres_bp.route("/")
def list_mat():
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)

    query = Matiere.query
    if search:
        query = query.filter(
            (Matiere.code.ilike(f"%{search}%")) |
            (Matiere.libelle.ilike(f"%{search}%")) |
            (Matiere.type.ilike(f"%{search}%")) |
            (Matiere.etat.ilike(f"%{search}%"))
        )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    matieres = pagination.items
    user_role = getattr(current_user, "role", "").lower()

    return render_template("matieres/list_mat.html",
                           matieres=matieres,
                           pagination=pagination,
                           search=search,
                           per_page=per_page,
                           user_role=user_role)

WORKFLOW = {
    "Activer": {"from": "Inactif", "to": "Actif"},
    "Bloquer": {"from": "Actif", "to": "Bloqué"}
}

@matieres_bp.route("/get/<string:id>", methods=["GET"])
def get_matiere(id):
    matiere = Matiere.query.get_or_404(id)
    return jsonify({
        "id": str(matiere.id),
        "code": matiere.code,
        "libelle": matiere.libelle,
        "etat": matiere.etat,
        "type": matiere.type
    })

@matieres_bp.route("/<string:id>/changer_etat", methods=["POST"])
def changer_etat(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    matiere = Matiere.query.get_or_404(id)
    action = request.json.get("action")
    if action not in WORKFLOW:
        return jsonify({"error": "Action non valide!"}), 400
    trans = WORKFLOW[action]
    if matiere.etat != trans["from"]:
        return jsonify({"error": f"L'état actuel est {matiere.etat}, impossible d'appliquer {action}"}), 400
    matiere.etat = trans["to"]
    db.session.commit()
    return jsonify({
        "message": f"Etat changé en {matiere.etat}",
        "id": str(matiere.id),
        "etat": matiere.etat
    }), 200

def generer_code_matiere(libelle):
    if not libelle:
        prefix = "MAT"
    else:
        mots = libelle.strip().split()
        if len(mots) == 1:
            prefix = mots[0][:3].upper()
        elif len(mots) == 2:
            prefix = f"{mots[0][:2].upper()}{mots[1][:2].upper()}"
        else:
            prefix = "".join([mot[0].upper() for mot in mots])
    while True:
        code_gen = f"{prefix}-{uuid.uuid4().hex[:3].upper()}"
        if not Matiere.query.filter_by(code=code_gen).first():
            return code_gen

@matieres_bp.route("/add", methods=["POST"])
def add_matiere():
    data = request.form
    code = data.get("code")
    libelle = data.get("libelle")
    type_ = data.get("type", "Autres")

    if not code:
        code = generer_code_matiere(libelle)

    if Matiere.query.filter_by(code=code).first():
        return jsonify({"error": f"Une matière existe déjà avec le code '{code}'"}), 400

    try:
        matiere = Matiere(code=code, libelle=libelle, type=type_, etat="Inactif")
        db.session.add(matiere)
        db.session.commit()
        return jsonify({"message": "Ajout réussi", "code": code, "id": str(matiere.id)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@matieres_bp.route("/delete/<string:id>", methods=["POST"])
def delete_mat(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    matiere = Matiere.query.get_or_404(id)
    if matiere.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de supprimer cette matière, état non inactif"}), 400
    db.session.delete(matiere)
    db.session.commit()
    return jsonify({"success": True})

@matieres_bp.route("/detail/<string:id>", methods=["GET"])
def detail_mat(id):
    matiere = Matiere.query.get_or_404(id)
    return jsonify({
        "id": str(matiere.id),
        "code": matiere.code,
        "libelle": matiere.libelle,
        "etat": matiere.etat,
        "type": matiere.type
    })

@matieres_bp.route("/update/<string:id>", methods=["POST"])
def update_mat(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    matiere = Matiere.query.get_or_404(id)
    if matiere.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de modifier cette matière, état non inactif!"}), 400
    data = request.form
    matiere.code = data.get("code")
    matiere.libelle = data.get("libelle")
    matiere.type = data.get("type", matiere.type)
    db.session.commit()
    return jsonify({
        "id": str(matiere.id),
        "code": matiere.code,
        "libelle": matiere.libelle,
        "type": matiere.type,
        "etat": matiere.etat
    })

@matieres_bp.route("/liste", methods=["GET"])
def liste_matieres():
    matieres = Matiere.query.all()
    return jsonify([{"id": str(m.id), "libelle": m.libelle} for m in matieres])

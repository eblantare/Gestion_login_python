from extensions import db
from ..models import Appreciations
from flask import Blueprint,render_template, request, jsonify
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

appreciations_bp = Blueprint(
    "appreciations",__name__, url_prefix="/appreciations"
)


def is_admin():
    return getattr(current_user, "role","").lower() in ["admin", "administrateur"]

from flask import current_app

@appreciations_bp.route("/add", methods=["POST"])
def add_appreciations():
    libelle = request.form.get("libelle", "").strip()
    description = request.form.get("description", "").strip()

    if not libelle:
        return jsonify({"error": "Le libellé est obligatoire."}), 400
    if not description:
        return jsonify({"error": "La description est obligatoire."}), 400

    # Vérifier si l'appréciation existe déjà
    existing = Appreciations.query.filter_by(libelle=libelle, description=description).first()
    if existing:
        return jsonify({"error": "Cette appréciation existe déjà."}), 400

    appreciation = Appreciations(libelle=libelle, description=description, etat="Inactif")
    db.session.add(appreciation)

    try:
        db.session.commit()
        # Retourner l'objet créé côté JS
        return jsonify({
            "id": str(appreciation.id),
            "libelle": appreciation.libelle,
            "description": appreciation.description,
            "etat": appreciation.etat
        }), 200
    except IntegrityError as db_err:
        db.session.rollback()
        if "uq_libelle_description" in str(db_err.orig):
            return jsonify({"error": "Cette appréciation existe déjà."}), 400
        current_app.logger.error(f"Erreur SQL lors du commit: {db_err}", exc_info=True)
        return jsonify({"error": "Erreur base de données, vérifiez les logs."}), 500
    
@appreciations_bp.route("/")

def liste_appr():
    # paramètres de recherche et de pagination
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)

    # Requête de base
    query = Appreciations.query

    # Recherche
    if search:
        query = query.filter(
            (Appreciations.libelle.ilike(f"%{search}%")) |
            (Appreciations.description.ilike(f"%{search}%")) |
            (Appreciations.etat.ilike(f"%{search}%"))
        )

    # Pagination (toujours exécutée, que search soit vide ou pas)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    appreciations = pagination.items

    # on récupère le rôle de l'utilisateur connecté pour l'afficher sur la page
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()

    return render_template(
        "appreciations/liste_appr.html",
        appreciations=appreciations,
        pagination=pagination,
        search=search,
        per_page=per_page,
        user_role=user_role
    )
    
@appreciations_bp.route("/get/<string:id>", methods=["GET"])
def get_appreciation(id):
        appreciation=Appreciations.query.get_or_404(id)
        return jsonify({
            "id": str(appreciation.id),
            "libelle":appreciation.libelle,
            "description":appreciation.description,
            "etat":appreciation.etat
        })


WORKFLOW = {
        "Activer" :{"from": "Inactif", "to": "Actif"},
       "Abandonner" :{"from": "Actif", "to": "Abandonné"}
   }
    
@appreciations_bp.route("/<string:id>/changer_etat", methods=["POST"])
def changer_etat(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403

    appreciation = Appreciations.query.get_or_404(id)
    action = request.json.get("action")

    if action not in WORKFLOW:
        return jsonify({"error": "Action non valide!"}), 400

    trans = WORKFLOW[action]
    if appreciation.etat != trans["from"]:
        return jsonify({
            "error": f"L'état actuel est {appreciation.etat}, impossible d'appliquer {action}"
        }), 400

    appreciation.etat = trans["to"]
    db.session.commit()

    return jsonify({
    "message": f"État changé : {appreciation.etat}","etat": appreciation.etat}), 200
    

@appreciations_bp.route("/update/<string:id>", methods=["POST"])
def update_appreciation(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    appreciation = Appreciations.query.get_or_404(id)
    #contrôle sur l'état
    if appreciation.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de modifier cette appréciation, état non inactif"}),403
    data = request.form
    appreciation.libelle = data.get("libelle")
    appreciation.description = data.get("description")
    db.session.commit() #Indispensable pour la sauveagrde
    return jsonify({
        "id":appreciation.id,
        "libelle":appreciation.libelle,
        "description":appreciation.description,
        "etat": appreciation.etat
    })

@appreciations_bp.route("/delete/<string:id>", methods=["POST"])
def delete_appreciation(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    appreciation = Appreciations.query.get_or_404(id)
    #Contrôle sur l'état
    if appreciation.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de supprimer cette appréciation, état non inactif"})
    db.session.delete(appreciation)
    db.session.commit()
    return jsonify({"success": True})

@appreciations_bp.route("/detail/<string:id>", methods = ["GET"])
def detail_appreciation(id):
    appreciation =Appreciations.query.get_or_404(id)
    return jsonify(
        {
            "libelle": appreciation.libelle,
            "description": appreciation.description,
            "etat": appreciation.etat
        }
    )
    
    


            

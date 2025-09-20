from flask import Blueprint, render_template, request, jsonify
from extensions import db
from ..models import Classe, Enseignant
from sqlalchemy import cast,String
from flask_login import current_user
import random
import string
import uuid
from uuid import UUID

classes_bp = Blueprint("classes", __name__, url_prefix="/classes")

#Contrôle , permission et autorisation pour les admin
def is_admin():
    return getattr(current_user, "role","").lower() in ["admin", "administrateur"]

@classes_bp.route("/")
def liste_classes():
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)

    query = Classe.query

#Recherche texte
    if search:
        query = query.filter(
            (Classe.code.ilike(f"%{search}%")) |
            (Classe.nom.ilike(f"%{search}%")) |
            (cast(Classe.effectif, String).ilike(f"%{search}%")) |
            (Classe.etat.ilike(f"%{search}%"))
        )
    
    # Pagination (toujours exécutée, que search soit vide ou pas)
    pagination = query.paginate(page=page,per_page=per_page,error_out=False)
    classes = pagination.items
 # on récupère le rôle de l'utilisateur connecté pour l'afficher sur la page
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()
    enseignants = Enseignant.query.all()

    return render_template("classes/e_listeClasse.html",
                           classes = classes,
                           pagination = pagination,
                           search = search,
                           per_page = per_page,
                           user_role=user_role,
                           enseignants=enseignants)


def generate_classe_code():
    """Génère un code de classe de 6 caractères commençant par CLAS"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
    return f"CLAS{suffix}"


@classes_bp.route("/add", methods=["POST"])
def add_classe():
    # Si un code est fourni manuellement, on l’utilise. Sinon on génère un code unique.
    code = request.form.get("code")
    if not code:
        code = f"CL-{uuid.uuid4().hex[:6].upper()}"
    
    nom = request.form.get("nom")
    effectif = int(request.form.get("effectif", 0))

    # Vérifier unicité du code (avant d’insérer)
    if Classe.query.filter_by(code=code).first():
        return jsonify({"error": "Cette classe existe déjà"}), 400

    # Récupérer les enseignants sélectionnés
    enseignant_ids = request.form.getlist("enseignants[]")
    enseignants = Enseignant.query.filter(Enseignant.id.in_(enseignant_ids)).all()

    # Création de la classe
    classe = Classe(code=code, nom=nom, effectif=effectif, etat="Inactif")
    classe.enseignants = enseignants

    db.session.add(classe)
    db.session.commit()

    return jsonify({"message": "Ajout réussi"})

    
WORKFLOW = {
    "Activer":{"from": "Inactif", "to": "Actif"},
    "Fermer":{"from": "Actif", "to": "Fermé"}
}


@classes_bp.route("/get/<string:id>" , methods=["GET"])
def get_classe(id):
    classe = Classe.query.get_or_404(id)
    return jsonify(
        {
            "id": str(classe.id),
            "code": classe.code,
            "nom": classe.nom,
            "effectif": classe.effectif,
            "enseignants": [str(e.id) for e in classe.enseignants],  # <- retourner id
            "enseignants_nom": [f"{e.utilisateur.prenoms} {e.utilisateur.nom}" for e in classe.enseignants],
            "etat": classe.etat
        }
    )

@classes_bp.route("/<string:id>/changer_etat", methods=["POST"])
def changer_etat(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    classe = Classe.query.get_or_404(id)
    action = request.json.get("action")

    if action not  in WORKFLOW:
        return jsonify({"error": "Action non valide! "}), 400
    trans = WORKFLOW[action]
    if classe.etat != trans["from"]:
         return jsonify({"error": f"L'état actuel est {classe.etat}, impossible d'appliquer {action}"}),400
    classe.etat = trans["to"]
    db.session.commit()
    return jsonify({"etat": classe.etat})

@classes_bp.route("/update/<string:id>", methods=["POST"])
def update_classe(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    classe = Classe.query.get_or_404(id)
    #COntrôle d'état
    if classe.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de modifier cette classe, état non inactif!"}),400
    data = request.form
    classe.code = data.get("code")
    classe.nom = data.get("nom")
    classe.effectif = data.get("effectif")
    # 🔹 Récupérer les enseignants sélectionnés
    enseignant_ids = request.form.getlist("enseignants[]")
    enseignants = Enseignant.query.filter(Enseignant.id.in_(enseignant_ids)).all()
    classe.enseignants = enseignants  # met à jour la relation many-to-many
    db.session.commit()
    return jsonify({
        "id":str(classe.id),
        "code":classe.code,
        "nom":classe.nom,
        "effectif":classe.effectif,
       "enseignants": [str(e.id) for e in classe.enseignants],  # pour select
       "enseignants_nom": [f"{e.utilisateur.prenoms} {e.utilisateur.nom}" for e in classe.enseignants],  # pour affichage
       "etat": classe.etat
    })

@classes_bp.route("/delete/<string:id>", methods=["POST"])
def delete_classe(id):
    # if not is_admin():
    #     return jsonify({"error", "Accès refusé"}), 403
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    classe = Classe.query.get_or_404(id)
    #Contrôle sur l'état
    if classe.etat.lower() != 'inactif':
        return jsonify({"error", "Impossible de supprimer cette classe, état non inactif"})
    db.session.delete(classe)
    db.session.commit()
    return jsonify({"success": True})

@classes_bp.route("/detail/<string:id>", methods=["GET"])
def detail_classe(id):
    classe = Classe.query.get_or_404(id)
    return jsonify(
        {
            "code": classe.code,
            "nom": classe.nom,
            "effectif": classe.effectif,
            "enseignants": [f"{e.utilisateur.prenoms} {e.utilisateur.nom}" for e in classe.enseignants],
            "etat": classe.etat
        }
    )


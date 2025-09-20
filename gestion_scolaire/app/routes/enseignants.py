from flask import Blueprint, request, render_template,jsonify
from ..models import Enseignant,Matiere # si nécessaire
from sqlalchemy import cast, String, extract
from gestion_login.gestion_login.models import Utilisateur
from flask_login import current_user
from extensions import db
from sqlalchemy.orm import joinedload



enseignants_bp = Blueprint('enseignants', __name__)


def is_admin():
     return getattr(current_user,"role","").lower() in ["admin", "administrateur"]


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

# WORKFLOW = {
#     "Activer": {"from": "Inactif", "to": "Actif"},
#     "Muter": {"from": "Actif", "to": "Muté"},
#     "Retraiter": {"from": "Muté", "to": "Retraité"}
# }
# ici tes routes
@enseignants_bp.route("/")

def liste_enseignants():

    data = request.args
    search = data.get("search", "", type=str)
    per_page = data.get("per_page", 5, type=int)
    page = data.get("page",1, type=int)

    query = Enseignant.query
    # --- Récupérer la liste des matières pour le filtre ---
    matieres = Matiere.query.with_entities(Matiere.id, Matiere.libelle).all()
      #Récupérer toutes les années distintes de date_fonction 
# Récupérer toutes les années distinctes de date_fonction
    annees = (
    db.session.query(extract("year", Enseignant.date_fonction).label("annee"))
    .distinct()
    .order_by("annee")
    .all()
   )

# Convertir en liste simple d'années
    annees = [int(a.annee) for a in annees if a.annee is not None]

    #Recherche dans le texte
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
                 (Enseignant.matiere.has(Matiere.libelle.ilike(f"%{search}%")))
             )
    )
#Filtrage spécifique
    filter_value = data.get("filter", "", type=str)
  
    query = query.options(joinedload(Enseignant.matieres))  # charger toutes les matières liées
    if filter_value:
        key,val = filter_value.split(":",1)
        if key == "sexe":
            query = query.join(Utilisateur).filter(Utilisateur.sexe == val)
            
        elif key == "date_fonction":
        # Exemple simple : filtrer par année
           query = query.filter(extract("year",Enseignant.date_fonction) == int(val))
        elif key == "matiere" and val:
           query = query.join(Enseignant.matieres).filter(Matiere.id == int(val))
        elif key in FILTER_DIC and val in FILTER_DIC[key]:
           query = query.filter(getattr(Enseignant, key).in_(FILTER_DIC[key][val]))
        else:
          query = query.filter(getattr(Enseignant, key) == val)

        #Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    enseignants = pagination.items

    # --- Charger les matières pour le select ---
    matieres = Matiere.query.all()
            #Récupérer l'utilisateur courant
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()
    return render_template("enseignants/ens_liste.html",
                               enseignants=enseignants,
                               pagination=pagination,
                               search = search,
                               per_page=per_page,
                               user_role=user_role,
                               filter_value=filter_value,
                               matieres=matieres,
                               annees=annees

                               
                               )
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
        utilisateur_id = utilisateur_id,
        titre = data.get("titre"),
        date_fonction = data.get("date_fonction"),
        etat = "Inactif"
    )
    db.session.add(enseignant)
    db.session.commit()

# Ajouter les matières sélectionnées
    matieres_ids = request.form.getlist("matiere_id")  # <-- note getlist() pour multi
    if matieres_ids:
        enseignant.matieres = Matiere.query.filter(Matiere.id.in_(matieres_ids)).all()
        db.session.commit()
    

    return jsonify({"message": "Ajout réussi"}), 200
    
@enseignants_bp.route("/update/<string:id>", methods=["POST"])
def update_ens(id):
    if not is_admin():
        return jsonify({"error", "Accès refusé"}), 403
    
    enseignant = Enseignant.query.get_or_404(id)
    #contrôle sur l'état
    if enseignant.etat.lower() != 'inactif':
        return jsonify({"error", "Etat non inactif"}),403
    for field in ["titre","date_fonction"]:
        setattr(enseignant,field,request.form.get(field))
    db.session.commit() #Indispensable pour la sauveagrde
    return jsonify({
    "titre": enseignant.titre,
    "date_fonction": enseignant.date_fonction.strftime("%Y-%m-%d")
})

@enseignants_bp.route("/delete/<string:id>", methods=["POST"])
def delete_ens(id):
    if not is_admin():
        return jsonify({"error", "Accès refusé"}), 403
    
    enseignant = Enseignant.query.get_or_404(id)
    #Contrôle sur l'état
    if enseignant.etat.lower() != 'inactif':
        return jsonify({"error", "Impossible de supprimer"}), 403
    db.session.delete(enseignant)
    db.session.commit()
    return jsonify({"success": True})

@enseignants_bp.route("/get/<string:enseignant_id>", methods=["GET"])
def get_enseignant(enseignant_id):
    enseignant = Enseignant.query.get_or_404(enseignant_id)

    # Récupérer aussi les infos utilisateur liées
    utilisateur = enseignant.utilisateur if hasattr(enseignant, "utilisateur") else None
    # Construire une chaîne de matières (séparées par une virgule)
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
        "nom":utilisateur.nom,
        "prenoms":utilisateur.prenoms,
        "sexe":utilisateur.sexe,
        "email":utilisateur.email,
        "telephone":utilisateur.telephone,
        "matiere_id": ",".join([str(m.id) for m in enseignant.matieres]) if hasattr(enseignant, "matieres") else "",
        "matiere": matieres_str,
        "titre": enseignant.titre,
        "date_fonction": enseignant.date_fonction.strftime("%Y-%m-%d") if enseignant.date_fonction else None,
        "photo_filename":utilisateur.photo_filename,
        "etat": enseignant.etat
    })



# @enseignants_bp.route("/<string:id>/changer_etat", methods=["POST"])
# def changer_etat(id):
#     if not is_admin():
#         return jsonify({"error", "Accès refusé"}), 403
#     enseignant = Enseignant.query.get_or_404(id)
#     action = request.json.get("action")

#     if action not in WORKFLOW:
#         return jsonify({"error": "Action non valide!"}),400
    
#     trans = WORKFLOW[action]
#     if enseignant.etat != trans["from"]:
#         return jsonify({"error": f"L'état actuel est {enseignant.etat}, impossible d'appliquer {action}"}),400
    
#     enseignant.etat = trans["to"]
#     db.session.commit()
#     return jsonify({"etat": enseignant.etat})

@enseignants_bp.route("/<string:ens_id>/changer_etat", methods=["POST"])
# @login_required
def changer_etat(ens_id):
    if not is_admin():
        return jsonify({"error", "Accès refusé"}), 403
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

from flask import current_app

# ... tes autres imports et code ...

@enseignants_bp.route("/options", methods=["GET"])
def enseignants_options():
    """
    Renvoie en une seule requête :
      - liste des utilisateurs (id, nom, prenoms, sexe, email, telephone, photo_filename)
      - liste des matieres (id, libelle)
    Utile pour peupler les selects et faire l'auto-fill côté client.
    """
    try:
        # Remplace Utilisateur et Matiere par les noms réels de tes modèles si différent
        from ..models import  Matiere
        from gestion_login.gestion_login.models import Utilisateur

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
        current_app.logger.exception("Erreur lors de l'envoi des options enseignants")
        return jsonify({"error": "Impossible de charger les options"}), 500

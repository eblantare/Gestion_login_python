from flask import Blueprint, render_template, request, jsonify
from extensions import db
from ..models import Eleve,Classe
from sqlalchemy import cast, String
from flask_login import current_user
import uuid


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





# @eleves_bp.route("/")
# def index():
#     return render_template("eleves/index.html")

from flask import Blueprint, render_template, request, jsonify
from extensions import db
from ..models import Eleve
from sqlalchemy import cast, String
from ..utils import login_required
from flask_login import current_user


eleves_bp = Blueprint(
    "eleves",
    __name__
    # template_folder="../templates",       # templates propres au module
    # static_folder="static",                   # les fichiers statiques du module
    # static_url_path="/eleves_static"          # URL publique = http://127.0.0.1:5000/eleves_static/...
)

# eleves_bp = Blueprint('eleves', __name__, template_folder='../templates/modules/eleves')

def is_admin():
    return getattr(current_user,"role","").lower() in ["admin", "administrateur"]

@eleves_bp.route("/add",methods=["POST"])
def add_eleve():
    if request.method == 'POST':
        matricule = request.form['matricule']
        nom = request.form['nom']
        prenoms = request.form['prenoms']
        date_naissance = request.form['date_naissance']
        sexe = request.form['sexe']
        status = request.form.get('status','Nouveau')
        classe = request.form.get('classe','6èm')
        

        eleve = Eleve(matricule=matricule,nom=nom,prenoms=prenoms,date_naissance=date_naissance,
                       sexe=sexe, status=status,classe=classe, etat="Inactif")        
        db.session.add(eleve)
        db.session.commit()
        
        return jsonify({"message": "Ajout réussi"}), 200

@eleves_bp.route("/")
def liste_eleves():

    #paramètres de recherche et de pagination
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)
    # Requête de base
    query = Eleve.query

    # Recherche
    if search:
        query = query.filter(
            (Eleve.nom.ilike(f"%{search}%"))|
            (Eleve.nom.ilike(f"%{search}%"))|
            (Eleve.prenoms.ilike(f"%{search}%"))|
            (cast(Eleve.date_naissance, String).ilike(f"%{search}%"))|
            (Eleve.sexe.ilike(f"%{search}%"))|
            (Eleve.status.ilike(f"%{search}%"))|
            (Eleve.classe.ilike(f"%{search}%"))|
            (Eleve.etat.ilike(f"%{search}%"))
        )

        #----Pagination----
    pagination = query.paginate(page=page,per_page=per_page,error_out=False)
    eleves= pagination.items

    #on récupère le rôle de l'utilisateur connecté
    user_role = getattr(current_user, "role", None).lower()
    return render_template("eleves/e_liste.html",
                           eleves=eleves,
                           pagination = pagination,
                           search = search,
                           per_page = per_page,
                           user_role = user_role
                           )

@eleves_bp.route("/update/<string:id>", methods=["POST"])
def update_eleve(id):
    if not is_admin():
        return jsonify({"error", "Accès refusé"}), 403
    
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
    eleve.classe = data.get("classe")
    db.session.commit() #Indispensable pour la sauveagrde
    return jsonify({
        "id":eleve.id,
        "matricule":eleve.matricule,
        "nom":eleve.nom,
        "prenoms":eleve.prenoms,
        "date_naissance":str(eleve.date_naissance),
        "sexe":eleve.sexe,
        "status":eleve.status,
        "classe":eleve.classe,
        "etat": eleve.etat
    })

@eleves_bp.route("/delete/<string:id>", methods=["POST"])
def delete_eleve(id):
    if not is_admin():
        return jsonify({"error", "Accès refusé"}), 403
    
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
            "classe": eleve.classe,
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
            "classe": eleve.classe,
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
        return jsonify({"error",f"L'état actuel est {eleve.etat}, impossible d'appliquer {action}"}),400
    
    eleve.etat = trans["to"]
    db.session.commit()
    return jsonify({"etat": eleve.etat})





# @eleves_bp.route("/")
# def index():
#     return render_template("eleves/index.html")

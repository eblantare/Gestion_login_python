from flask import Blueprint, render_template, request, jsonify
from ..models import Classe,Eleve,Paiement
from sqlalchemy import cast,String
from flask_login import current_user
from datetime import datetime
import uuid
from extensions import db
from uuid import UUID
from sqlalchemy.orm import joinedload

paiements_bp = Blueprint('paiements', __name__)

def is_admin():
    return getattr(current_user, "role","").lower() in ["admin", "administrateur"]

workflow = {
        "Activer":  {"from":"Inactif", "to":"Actif"},
        "Valider": {"from":"Actif", "to":"Validé"}
    }
# ici tes routes
@paiements_bp.route('/')
def liste_paiements():
    data = request.args
    search = data.get("search", "", type=str)
    per_page = data.get("per_page", 5, type=int)
    page = data.get("page", 1, type=int)
    classe_id = data.get("classe_id", type=str)
    query = Paiement.query.options(
        joinedload(Paiement.eleve),   # charge l'élève
        joinedload(Paiement.classe)   # charge la classe
    )

#Recherche texte
    if search:
        query = query.filter(
            (Paiement.code.ilike(f"%{search}%")) |
            (Paiement.libelle.ilike(f"%{search}%")) |
            (Paiement.eleve.has(Eleve.nom.ilike(f"%{search}%"))) |
            (Paiement.classe.has(Classe.nom.ilike(f"%{search}%")))|
            (cast(Paiement.date_payement, String).ilike(f"%{search}%"))|
            (Paiement.montant_net.cast(String).ilike(f"%{search}%"))|
            (Paiement.montant_pay.cast(String).ilike(f"%{search}%"))|
            (Paiement.montant_rest.cast(String).ilike(f"%{search}%"))|
            (Paiement.etat.ilike(f"%{search}%"))
        )
    
    #Filtrage par classe
    if classe_id and classe_id.lower() != "none":
        try:
          classe_uuid = UUID(classe_id)
          query = query.filter(Paiement.classe_id == classe_uuid)
        except ValueError:
            pass

    # Pagination (toujours exécutée, que search soit vide ou pas)
    pagination = query.paginate(page=page,per_page=per_page,error_out=False)
    paiements = pagination.items
 # on récupère le rôle de l'utilisateur connecté pour l'afficher sur la page
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()

    #Récupérer toutes les classes pour le select
    classes = Classe.query.all()
    #Récupérer tous les élèves
    eleves = Eleve.query.all()
    return render_template("paiements/pay_list.html",
                           paiements = paiements,
                           pagination = pagination,
                           search = search,
                           per_page = per_page,
                           user_role=user_role,
                           classes = classes,
                           eleves = eleves,
                           classe_id = classe_id)

@paiements_bp.route("/add", methods=["GET", "POST"])
def ajouter_paiement():
    if request.method == "POST":
       data = request.form
       print("==== DONNEES RECUES ====")
       print(data)
       eleve_id = data.get("eleve_id")
       classe_id = data.get("classe_id")
       libelle = data.get("libelle")
       date_payement = data.get("date_payement")
       montant_net = data.get("montant_net")
       montant_pay = data.get("montant_pay")
    #    montant_rest = data.get("montant_rest")

       #Vérifier que tous les champs sont remplis
       if not eleve_id or not classe_id or not date_payement or not montant_net or not montant_pay:
        return jsonify({"status":"warning", "message":"Veuillez remplir tous les champs obligatoires"})
       
       # Conversion de la date (on sait qu'elle est présente)
       date_payement_dt = datetime.strptime(date_payement, "%Y-%m-%d")
       #Vérifier si l'élève a déjà un paiement
       existing = Paiement.query.filter_by(eleve_id=eleve_id).first()
       if existing:
        return jsonify({"status":"danger","message":"Cet élève a déjà effectué un paiements"})
       
       #Calcul montant restant
       montant_rest = float(montant_net) - float(montant_pay)

       #création du code paiement unique
       code = f"PAY-{uuid.uuid4().hex[:6].upper()}"

       #Création et enregistrement
       paiement = Paiement(
            id=uuid.uuid4(),
            code=code,
            libelle=libelle,
            eleve_id=eleve_id,
            classe_id=classe_id,
            date_payement=date_payement_dt,
            montant_net=montant_net,
            montant_pay=montant_pay,
            montant_rest=montant_rest,
         )
       db.session.add(paiement)
       db.session.commit()
       paiement = Paiement.query.get(paiement.id) #Récupérer toutes les actions

       return jsonify({"status": "success",
       "message":"Ajout réussi",
       "paiement" :{
        "id":str(paiement.id),
        "code":paiement.code,
        "libelle":paiement.libelle,
        "eleve": f"{paiement.eleve.nom} {paiement.eleve.prenoms}",
        "classe": paiement.classe.nom,
        "date_payement": paiement.date_payement.strftime('%d/%m/%Y') if paiement.date_payement else '',
        "montant_net": paiement.montant_net,
        "montant_pay": paiement.montant_pay,
        "montant_rest": paiement.montant_rest
       }})
    # Pour GET → afficher le formulaire
    eleves = Eleve.query.all()
    classes = Classe.query.all()
    return render_template("paiements/add_pay.html", eleves=eleves, classes=classes)
    # sinon on affiche le formulaire

@paiements_bp.route("/detail/<string:pay_id>", methods=["GET"])
def detail_pay(pay_id):
   paiement = Paiement.query.get_or_404(pay_id)
   if not paiement:
        return jsonify({"error": "Paiement non trouvé"}), 404
   return jsonify({
      "id": str(paiement.id),
        "code": paiement.code,
        "libelle": paiement.libelle,
        "eleve_id": str(paiement.eleve.id),
        "eleve": f"{paiement.eleve.nom} {paiement.eleve.prenoms}",
        "classe_id": str(paiement.classe.id),
        "classe": paiement.classe.nom,
        "date_payement": paiement.date_payement.strftime("%Y-%m-%d") if paiement.date_payement else '',
        "montant_net": paiement.montant_net,
        "montant_pay": paiement.montant_pay,
        "montant_rest": paiement.montant_rest

   })

# gestion_scolaire/routes.py
@paiements_bp.route("/edit/<string:paiement_id>", methods=["POST"])
def edit_paiement(paiement_id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    # récupérer le paiement et mettre à jour
    paiement = Paiement.query.get(paiement_id)
    if not paiement:
        return jsonify({"status":"error","message":"Paiement introuvable"}), 404
    
    # récupérer les données du formulaire
    libelle = request.form.get("libelle")
    date_payement = request.form.get("date_payement")
    montant_net = request.form.get("montant_net")
    montant_pay = request.form.get("montant_pay")
    
    # mise à jour
    paiement.libelle = libelle
    paiement.date_payement = date_payement
    paiement.montant_net = float(montant_net)
    paiement.montant_pay = float(montant_pay)
    paiement.montant_rest = paiement.montant_net - paiement.montant_pay
    db.session.commit()
    
    return jsonify({"status":"success","message":"Paiement modifié avec succès"})


@paiements_bp.route("/delete/<string:id>", methods=["POST"])
def delete_pay(id):
   if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
   paiement = Paiement.query.get_or_404(id)
   db.session.delete(paiement)
   db.session.commit()
   return jsonify({"status":"success", "message":"Paiement supprimé"})
   
@paiements_bp.route("/workflow/<string:pay_id>", methods=["POST"])
def change_workflow(pay_id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    paiement = Paiement.query.get_or_404(pay_id)
    data = request.get_json()
    action = data.get("action") if data else None

    if not action or action not  in workflow:
        return jsonify({"error": "Action non valide! "}), 400
    trans = workflow[action]
    if paiement.etat != trans["from"]:
         return jsonify({"error": f"L'état actuel est {paiement.etat}, impossible d'appliquer {action}"}),400
    paiement.etat = trans["to"]
    db.session.commit()
    return jsonify({
        "etat": paiement.etat,
        "message": f"L'état a été mis à jour vers {paiement.etat}"
    })
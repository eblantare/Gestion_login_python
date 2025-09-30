from flask import Blueprint, render_template, request, jsonify
from extensions import db
from ..models import Ecole
from flask_login import current_user
import uuid
import re

ecoles_bp = Blueprint('ecoles', __name__)

def is_admin():
    return getattr(current_user, "role", "").lower() in ["admin", "administrateur"]

def validate_phone_format(phone):
    """Valide le format international du numéro de téléphone"""
    if not phone:
        return True, None
    
    # Format international: +228 12 34 56 78 ou +22812345678
    pattern = r'^\+[1-9]\d{1,14}$'
    cleaned_phone = phone.replace(' ', '').replace('-', '')
    
    if re.match(pattern, cleaned_phone):
        return True, cleaned_phone
    else:
        return False, "Format invalide. Utilisez le format international: +228 XX XX XX XX"

def validate_email_format(email):
    """Valide le format d'email"""
    if not email:
        return True, None
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, email
    else:
        return False, "Format d'email invalide"

@ecoles_bp.route("/")
def liste_ecoles():
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)

    query = Ecole.query

    if search:
        query = query.filter(
            (Ecole.code.ilike(f"%{search}%")) |
            (Ecole.nom.ilike(f"%{search}%")) |
            (Ecole.localite.ilike(f"%{search}%")) |
            (Ecole.boite_postale.ilike(f"%{search}%")) |
            (Ecole.telephone1.ilike(f"%{search}%")) |
            (Ecole.telephone2.ilike(f"%{search}%")) |
            (Ecole.email.ilike(f"%{search}%")) |
            (Ecole.site.ilike(f"%{search}%")) |
            (Ecole.devise.ilike(f"%{search}%")) |
            (Ecole.dre.ilike(f"%{search}%")) |
            (Ecole.inspection.ilike(f"%{search}%")) |
            (Ecole.prefecture.ilike(f"%{search}%")) 
        )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    ecoles = pagination.items
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()

    return render_template("ecoles/list_eco.html",
                           ecoles=ecoles,
                           pagination=pagination,
                           search=search,
                           per_page=per_page,
                           user_role=user_role)

@ecoles_bp.route("/add", methods=["POST"])
def add_ecole():
    try:
        # Si un code est fourni manuellement, on l'utilise. Sinon on génère un code unique.
        code = request.form.get("code")
        if not code:
            code = f"EC-{uuid.uuid4().hex[:6].upper()}"

        # Vérifier unicité du code
        if Ecole.query.filter_by(code=code).first():
            return jsonify({"error": "Cette école existe déjà"}), 400

        # Validation des formats
        email = request.form.get("email")
        if email:
            is_valid, error = validate_email_format(email)
            if not is_valid:
                return jsonify({"error": error}), 400

        telephone1 = request.form.get("telephone1")
        if telephone1:
            is_valid, formatted_phone = validate_phone_format(telephone1)
            if not is_valid:
                return jsonify({"error": formatted_phone}), 400
            telephone1 = formatted_phone

        telephone2 = request.form.get("telephone2")
        if telephone2:
            is_valid, formatted_phone = validate_phone_format(telephone2)
            if not is_valid:
                return jsonify({"error": formatted_phone}), 400
            telephone2 = formatted_phone

        # Création de l'ecole
        ecole = Ecole(
            code=code,
            nom=request.form.get("nom"),
            localite=request.form.get("localite"),
            boite_postale=request.form.get("boite_postale"),
            dre=request.form.get("dre"),
            inspection=request.form.get("inspection"),
            prefecture=request.form.get("prefecture"),
            site=request.form.get("site"),
            email=email,
            devise=request.form.get("devise"),
            telephone1=telephone1,
            telephone2=telephone2
        )

        db.session.add(ecole)
        db.session.commit()

        return jsonify({"message": "École ajoutée avec succès"})

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur serveur lors de l'ajout"}), 500

@ecoles_bp.route("/get/<string:id>", methods=["GET"])
def get_ecole(id):
    ecole = Ecole.query.get_or_404(id)
    return jsonify({
        "id": str(ecole.id),
        "code": ecole.code,
        "nom": ecole.nom,
        "localite": ecole.localite,
        "boite_postale": ecole.boite_postale,
        "inspection": ecole.inspection,
        "email": ecole.email,
        "site": ecole.site,
        "devise": ecole.devise,
        "dre": ecole.dre,
        "telephone1": ecole.telephone1,
        "telephone2": ecole.telephone2,
        "prefecture": ecole.prefecture
    })

@ecoles_bp.route("/update/<string:id>", methods=["POST"])
def update_ecole(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    try:
        ecole = Ecole.query.get_or_404(id)
        
        # Validation des formats
        email = request.form.get("email")
        if email:
            is_valid, error = validate_email_format(email)
            if not is_valid:
                return jsonify({"error": error}), 400

        telephone1 = request.form.get("telephone1")
        if telephone1:
            is_valid, formatted_phone = validate_phone_format(telephone1)
            if not is_valid:
                return jsonify({"error": formatted_phone}), 400
            telephone1 = formatted_phone

        telephone2 = request.form.get("telephone2")
        if telephone2:
            is_valid, formatted_phone = validate_phone_format(telephone2)
            if not is_valid:
                return jsonify({"error": formatted_phone}), 400
            telephone2 = formatted_phone

        # Mise à jour des champs
        ecole.code = request.form.get("code")
        ecole.nom = request.form.get("nom")
        ecole.localite = request.form.get("localite")
        ecole.boite_postale = request.form.get("boite_postale")
        ecole.dre = request.form.get("dre")
        ecole.site = request.form.get("site")
        ecole.email = email
        ecole.inspection = request.form.get("inspection")
        ecole.prefecture = request.form.get("prefecture")
        ecole.telephone1 = telephone1
        ecole.telephone2 = telephone2
        ecole.devise = request.form.get("devise")

        db.session.commit()

        return jsonify({
            "id": str(ecole.id),
            "code": ecole.code,
            "nom": ecole.nom,
            "localite": ecole.localite,
            "boite_postale": ecole.boite_postale,
            "inspection": ecole.inspection,
            "email": ecole.email,
            "site": ecole.site,
            "devise": ecole.devise,
            "dre": ecole.dre,
            "telephone1": ecole.telephone1,
            "telephone2": ecole.telephone2,
            "prefecture": ecole.prefecture
        })

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur serveur lors de la modification"}), 500

@ecoles_bp.route("/delete/<string:id>", methods=["POST"])
def delete_ecole(id):
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole = Ecole.query.get_or_404(id)
    db.session.delete(ecole)
    db.session.commit()
    return jsonify({"success": True})

@ecoles_bp.route("/detail/<string:id>", methods=["GET"])
def detail_ecole(id):
    ecole = Ecole.query.get_or_404(id)
    return jsonify({
        "code": ecole.code,
        "nom": ecole.nom,
        "localite": ecole.localite,
        "boite_postale": ecole.boite_postale,
        "inspection": ecole.inspection,
        "email": ecole.email,
        "site": ecole.site,
        "devise": ecole.devise,
        "dre": ecole.dre,
        "telephone1": ecole.telephone1,
        "telephone2": ecole.telephone2,
        "prefecture": ecole.prefecture
    })
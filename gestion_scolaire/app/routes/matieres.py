from flask import Blueprint, render_template, request, jsonify, current_app, abort, session
from extensions import db
from ..models import Matiere, Enseignant, Note
from flask_login import current_user, login_required
import uuid
import re
import logging
from uuid import UUID
from datetime import datetime
from ..utils import ecole_required, get_current_ecole_id

matieres_bp = Blueprint("matieres", __name__, url_prefix="/matieres")

# ==================== CONFIGURATION DE SÉCURITÉ ====================

# Configuration du logger de sécurité
security_logger = logging.getLogger('security')
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - [%(ip)s] %(user_id)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)
    security_logger.setLevel(logging.INFO)

def log_security_event(action, resource, status="success", details=None):
    """Journalise les événements de sécurité"""
    user_id = str(current_user.id) if current_user.is_authenticated else "anonymous"
    ip = request.remote_addr if request else "unknown"
    
    log_data = {
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "status": status,
        "ip": ip,
        "user_agent": request.headers.get('User-Agent', 'unknown') if request else "unknown"
    }
    
    if details:
        log_data["details"] = details
    
    security_logger.info(f"{action} - {resource} - {status}", extra={
        'ip': ip, 
        'user_id': user_id
    })

def validate_uuid(uuid_string):
    """Valide le format UUID de manière sécurisée"""
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    
    try:
        uuid_obj = UUID(uuid_string)
        return str(uuid_obj) == uuid_string
    except (ValueError, AttributeError):
        return False

def sanitize_input(param, max_length=100, allowed_pattern=None):
    """Nettoie et valide les paramètres d'entrée"""
    if param is None:
        return None
    
    param_str = str(param).strip()
    
    # Vérification de la longueur
    if len(param_str) > max_length:
        log_security_event(
            "input_validation", 
            "parameter_length", 
            "failed", 
            {"parameter": str(param)[:50], "max_length": max_length}
        )
        return None
    
    # Nettoyage des caractères dangereux pour prévenir les injections
    param_str = re.sub(r'[<>"\';()&+]', '', param_str)
    
    # Validation par pattern si spécifié
    if allowed_pattern and not re.match(allowed_pattern, param_str):
        log_security_event(
            "input_validation", 
            "parameter_pattern", 
            "failed", 
            {"parameter": param_str, "pattern": allowed_pattern}
        )
        return None
    
    return param_str

def rate_limit_check():
    """Vérification basique de rate limiting basée sur la session"""
    if 'request_count' not in session:
        session['request_count'] = 1
        session['first_request'] = datetime.utcnow().timestamp()
    else:
        session['request_count'] += 1
    
    # Limite: 100 requêtes par minute
    current_time = datetime.utcnow().timestamp()
    if current_time - session['first_request'] > 60:  # 1 minute
        session['request_count'] = 1
        session['first_request'] = current_time
    elif session['request_count'] > 100:
        log_security_event(
            "rate_limit", 
            f"ip_{request.remote_addr}", 
            "failed", 
            {"request_count": session['request_count']}
        )
        return False
    
    return True

# ==================== FONCTIONS UTILITAIRES SÉCURISÉES ====================

def is_admin():
    """Vérifie si l'utilisateur est administrateur"""
    if not current_user.is_authenticated:
        return False
    
    admin_roles = ["admin", "administrateur"]
    user_role = getattr(current_user, "role", "").lower()
    
    return user_role in admin_roles

def validate_matiere_data(code, libelle, type_):
    """Valide les données d'une matière de manière sécurisée"""
    # Validation des longueurs
    if code and len(code) > 20:
        return False, "Le code est trop long (max 20 caractères)"
    
    if libelle and len(libelle) > 100:
        return False, "Le libellé est trop long (max 100 caractères)"
    
    if type_ and len(type_) > 50:
        return False, "Le type est trop long (max 50 caractères)"
    
    # Validation des patterns
    code_pattern = r'^[A-Z0-9\-_]{1,20}$'
    if code and not re.match(code_pattern, code):
        return False, "Le code contient des caractères non autorisés"
    
    libelle_pattern = r'^[a-zA-Z0-9\s\-\'àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]{1,100}$'
    if libelle and not re.match(libelle_pattern, libelle):
        return False, "Le libellé contient des caractères non autorisés"
    
    # Validation des types autorisés (suppression de "Matière spécialisée")
    allowed_types = ["Matière scientifique", "Matière littéraire", "Autres"]
    if type_ and type_ not in allowed_types:
        return False, "Type de matière non autorisé"
    
    return True, ""

# ==================== ROUTES SÉCURISÉES ====================

@matieres_bp.route("/")
@login_required
# @ecole_required
def list_mat():
    """Liste des matières - VERSION SÉCURISÉE ET CORRIGÉE"""
    # Rate limiting
    if not rate_limit_check():
        abort(429, "Trop de requêtes")
    
    ecole_id = get_current_ecole_id()
    
    # Validation et sanitisation des paramètres - CORRECTION: meilleure gestion des valeurs par défaut
    search = sanitize_input(request.args.get("search", "", type=str), max_length=50)
    
    # CORRECTION: Gestion robuste de per_page avec valeur par défaut appropriée
    try:
        per_page = request.args.get("per_page", 10, type=int)
        per_page = min(max(per_page, 1), 500)  # Limite à 500
    except (ValueError, TypeError):
        per_page = 10  # Valeur par défaut en cas d'erreur
    
    # CORRECTION: Gestion robuste de la page
    try:
        page = request.args.get("page", 1, type=int)
        page = max(page, 1)
    except (ValueError, TypeError):
        page = 1

    # Filtrer par école
    query = Matiere.query.filter_by(ecole_id=ecole_id)

    # DEBUG: Compter les matières pour cette école
    total_matiere_count = query.count()
    print(f"DEBUG - Total matières pour ecole {ecole_id}: {total_matiere_count}")
    
    if search:
        from sqlalchemy import or_
        # Utilisation de paramètres sanitizés pour prévenir les injections SQL
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Matiere.code.ilike(search_term),
                Matiere.libelle.ilike(search_term),
                Matiere.type.ilike(search_term),
                Matiere.etat.ilike(search_term)
            )
        )
    
    # CORRECTION: Meilleure gestion de la pagination avec error_out=False
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False,
        max_per_page=500  # Limite maximale
    )
    
    matieres = pagination.items
    user_role = getattr(current_user, "role", "").lower()

    log_security_event("page_access", "matieres_list", "success")
    
    return render_template("matieres/list_mat.html",
                           matieres=matieres,
                           pagination=pagination,
                           search=search,
                           per_page=per_page,
                           user_role=user_role,
                           ecole_id=ecole_id)

WORKFLOW = {
    "Activer": {"from": "Inactif", "to": "Actif"},
    "Bloquer": {"from": "Actif", "to": "Bloqué"}
}

@matieres_bp.route("/get/<string:id>", methods=["GET"])
@login_required
@ecole_required
def get_matiere(id):
    """Récupère une matière - VERSION SÉCURISÉE"""
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    # Validation UUID
    if not validate_uuid(id):
        log_security_event("invalid_uuid", f"matiere_{id}", "failed")
        abort(404)
    
    ecole_id = get_current_ecole_id()
    matiere = Matiere.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    log_security_event("matiere_retrieval", f"matiere_{id}", "success")
    
    return jsonify({
        "id": str(matiere.id),
        "code": matiere.code,
        "libelle": matiere.libelle,
        "etat": matiere.etat,
        "type": matiere.type
    })

@matieres_bp.route("/<string:id>/changer_etat", methods=["POST"])
@login_required
@ecole_required
def changer_etat(id):
    """Change l'état d'une matière - VERSION SÉCURISÉE"""
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    # Validation des permissions
    if not is_admin():
        log_security_event(
            "unauthorized_action", 
            f"changer_etat_matiere_{id}", 
            "failed", 
            {"user_id": current_user.id}
        )
        return jsonify({"error": "Accès refusé"}), 403
    
    # Validation UUID
    if not validate_uuid(id):
        log_security_event("invalid_uuid", f"matiere_{id}", "failed")
        return jsonify({"error": "ID matière invalide"}), 400
    
    # Validation content-type
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    ecole_id = get_current_ecole_id()
    matiere = Matiere.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données JSON manquantes"}), 400
    
    action = sanitize_input(data.get("action"), max_length=20)
    if action not in WORKFLOW:
        log_security_event(
            "invalid_action", 
            f"matiere_{id}", 
            "failed", 
            {"action": action}
        )
        return jsonify({"error": "Action non valide!"}), 400
    
    trans = WORKFLOW[action]
    if matiere.etat != trans["from"]:
        return jsonify({"error": f"L'état actuel est {matiere.etat}, impossible d'appliquer {action}"}), 400
    
    try:
        matiere.etat = trans["to"]
        db.session.commit()
        
        log_security_event(
            "matiere_state_change", 
            f"matiere_{id}", 
            "success", 
            {"action": action, "new_state": matiere.etat}
        )
        
        return jsonify({
            "message": f"État changé en {matiere.etat}",
            "id": str(matiere.id),
            "etat": matiere.etat
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur changement état matière {id} - Utilisateur: {current_user.id}, Erreur: {str(e)}"
        )
        log_security_event(
            "database_error", 
            f"matiere_{id}_state_change", 
            "failed", 
            {"error": str(e)}
        )
        return jsonify({"error": "Erreur lors du changement d'état"}), 500

def generer_code_matiere(libelle, ecole_id):
    """Génère un code basé sur les 3-4 premières lettres du libellé"""
    if not libelle:
        base_code = "MAT"
    else:
        # Prendre les 3-4 premières lettres en majuscules
        base_code = libelle.upper()[:4]
        # Nettoyer les caractères non alphabétiques
        base_code = re.sub(r'[^A-Z]', '', base_code)
        # Assurer une longueur minimale
        if len(base_code) < 3:
            base_code = "MAT"
    
    # Vérifier l'unicité et ajouter un numéro si nécessaire
    code_final = base_code
    compteur = 1
    
    while Matiere.query.filter_by(code=code_final, ecole_id=ecole_id).first():
        compteur += 1
        code_final = f"{base_code}{compteur:02d}"
        
        # Limite de sécurité
        if compteur > 99:
            code_final = f"{base_code}_{uuid.uuid4().hex[:4].upper()}"
            break
    
    return code_final

@matieres_bp.route("/add", methods=["POST"])
@login_required
@ecole_required
def add_matiere():
    """Ajoute une matière - VERSION SÉCURISÉE"""
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    ecole_id = get_current_ecole_id()
    
    # GARANTIR qu'on a un ecole_id
    if not ecole_id:
        # Méthode 1: Récupérer depuis l'utilisateur
        if hasattr(current_user, 'ecole_id') and current_user.ecole_id:
            ecole_id = current_user.ecole_id
        # Méthode 2: Première école disponible
        else:
            from ..models.ecoles import Ecole
            default_ecole = Ecole.query.first()
            if not default_ecole:
                return jsonify({"error": "Aucune école configurée. Veuillez d'abord créer une école."}), 400
            ecole_id = default_ecole.id
    
    # Validation que ecole_id n'est plus None
    if not ecole_id:
        return jsonify({"error": "Impossible de déterminer l'école. Contactez l'administrateur."}), 400
    
    # Validation CSRF implicite via Flask-WTF ou vérification du referer
    if request.referrer and not request.referrer.startswith(request.host_url):
        log_security_event(
            "csrf_suspicion", 
            "add_matiere", 
            "failed", 
            {"referrer": request.referrer}
        )
        return jsonify({"error": "Requête suspecte"}), 400
    
    data = request.form
    code = sanitize_input(data.get("code"), max_length=20, allowed_pattern=r'^[A-Z0-9\-_]{1,20}$')
    libelle = sanitize_input(data.get("libelle"), max_length=100)
    type_ = sanitize_input(data.get("type", "Autres"), max_length=50)

    # Validation des données
    if not libelle:
        return jsonify({"error": "Le libellé de la matière est obligatoire"}), 400

    # Validation des données avec la fonction sécurisée
    is_valid, error_msg = validate_matiere_data(code, libelle, type_)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # Générer un code si non fourni
    if not code:
        code = generer_code_matiere(libelle, ecole_id)

    # Vérifier l'unicité du code dans l'école
    if Matiere.query.filter_by(code=code, ecole_id=ecole_id).first():
        return jsonify({"error": f"Une matière existe déjà avec le code '{code}' dans cette école"}), 400

    # Vérifier l'unicité du libellé dans l'école
    if Matiere.query.filter_by(libelle=libelle, ecole_id=ecole_id).first():
        return jsonify({"error": f"Une matière avec le libellé '{libelle}' existe déjà dans cette école"}), 400

    try:
        matiere = Matiere(
            code=code, 
            libelle=libelle, 
            type=type_, 
            etat="Inactif",
            ecole_id=ecole_id
        )
        db.session.add(matiere)
        db.session.commit()
        
        # Journalisation
        current_app.logger.info(
            f"Matière créée - ID: {matiere.id}, Code: {code}, "
            f"Libellé: {libelle}, Par utilisateur: {current_user.id}"
        )
        
        log_security_event(
            "matiere_creation", 
            f"matiere_{matiere.id}", 
            "success", 
            {"code": code, "libelle": libelle}
        )
        
        return jsonify({
            "message": "Matière ajoutée avec succès", 
            "code": code, 
            "id": str(matiere.id)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur création matière - Utilisateur: {current_user.id}, Erreur: {str(e)}"
        )
        log_security_event(
            "matiere_creation", 
            "database", 
            "failed", 
            {"error": str(e)}
        )
        return jsonify({"error": "Erreur lors de l'ajout de la matière"}), 500

def check_matiere_dependencies_detailed(matiere):
    """
    Version détaillée avec vérifications directes en base de données - SÉCURISÉE
    """
    dependencies_info = {
        'has_dependencies': False,
        'message': '',
        'details': {},
        'suggestions': []
    }
    
    from ..models import Enseignant, Note
    
    try:
        # 1. Vérifier les enseignants associés
        enseignants_count = db.session.query(Enseignant).join(
            Enseignant.matieres
        ).filter(
            Matiere.id == matiere.id
        ).count()
        
        if enseignants_count > 0:
            dependencies_info['details']['enseignants'] = {
                'count': enseignants_count,
                'nom_affichage': 'enseignants',
                'suggestion': 'Retirez cette matière des enseignants associés'
            }
    except Exception as e:
        current_app.logger.warning(f"Erreur comptage enseignants: {str(e)}")
    
    try:
        # 2. Vérifier les notes associées
        notes_count = Note.query.filter_by(matiere_id=matiere.id).count()
            
        if notes_count > 0:
            dependencies_info['details']['notes'] = {
                'count': notes_count,
                'nom_affichage': 'notes',
                'suggestion': 'Supprimez ou transférez les notes associées'
            }
    except Exception as e:
        current_app.logger.warning(f"Erreur comptage notes: {str(e)}")
    
    # Compiler les résultats
    if dependencies_info['details']:
        dependencies_info['has_dependencies'] = True
        used_in = [f"{detail['count']} {detail['nom_affichage']}" for detail in dependencies_info['details'].values()]
        dependencies_info['message'] = f"Dépendances détectées : {', '.join(used_in)}"
        dependencies_info['total_dependencies'] = sum(detail['count'] for detail in dependencies_info['details'].values())
        
        # Ajouter les suggestions
        for detail in dependencies_info['details'].values():
            dependencies_info['suggestions'].append(detail['suggestion'])
    
    return dependencies_info

@matieres_bp.route("/delete/<string:id>", methods=["POST"])
@login_required
@ecole_required
def delete_mat(id):
    """Supprime une matière - VERSION SÉCURISÉE"""
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    # Validation des permissions
    if not is_admin():
        log_security_event(
            "unauthorized_action", 
            f"delete_matiere_{id}", 
            "failed", 
            {"user_id": current_user.id}
        )
        return jsonify({"error": "Accès refusé"}), 403
    
    # Validation UUID
    if not validate_uuid(id):
        log_security_event("invalid_uuid", f"matiere_{id}", "failed")
        return jsonify({"error": "ID matière invalide"}), 400
    
    ecole_id = get_current_ecole_id()
    matiere = Matiere.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    if matiere.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de supprimer cette matière, état non inactif"}), 400
    
    # Vérifier les dépendances avec la version détaillée
    dependencies = check_matiere_dependencies_detailed(matiere)
    
    if dependencies['has_dependencies']:
        log_security_event(
            "matiere_deletion_blocked", 
            f"matiere_{id}", 
            "failed", 
            {"dependencies": dependencies['total_dependencies']}
        )
        return jsonify({
            "error": "Impossible de supprimer cette matière, des dépendances existent",
            "details": dependencies['message'],
            "dependencies": dependencies['details'],
            "suggestions": dependencies['suggestions'],
            "total_dependencies": dependencies['total_dependencies']
        }), 400
    
    try:
        db.session.delete(matiere)
        db.session.commit()
        
        current_app.logger.info(
            f"Matière supprimée - ID: {id}, Code: {matiere.code}, "
            f"Par utilisateur: {current_user.id}"
        )
        
        log_security_event("matiere_deletion", f"matiere_{id}", "success")
        
        return jsonify({
            "success": True, 
            "message": "Matière supprimée avec succès"
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur suppression matière ID {id} - Utilisateur: {current_user.id}, Erreur: {str(e)}"
        )
        log_security_event(
            "matiere_deletion", 
            f"matiere_{id}", 
            "failed", 
            {"error": str(e)}
        )
        return jsonify({"error": "Erreur lors de la suppression"}), 500

@matieres_bp.route("/delete/<string:id>/report", methods=["GET"])
@login_required
@ecole_required
def delete_matiere_report(id):
    """
    Génère un rapport détaillé des impacts d'une suppression de matière - SÉCURISÉ
    """
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    # Validation UUID
    if not validate_uuid(id):
        log_security_event("invalid_uuid", f"matiere_{id}", "failed")
        return jsonify({"error": "ID matière invalide"}), 400
    
    ecole_id = get_current_ecole_id()
    matiere = Matiere.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    # Rapport complet des dépendances
    dependencies = check_matiere_dependencies_detailed(matiere)
    
    report = {
        "matiere": {
            "id": str(matiere.id),
            "code": matiere.code,
            "libelle": matiere.libelle,
            "type": matiere.type,
            "etat": matiere.etat
        },
        "can_delete": (matiere.etat.lower() == 'inactif' and not dependencies['has_dependencies']),
        "dependencies_report": dependencies,
        "actions_required": []
    }
    
    # Suggestions d'actions selon les dépendances
    if matiere.etat.lower() != 'inactif':
        report["actions_required"].append("Changer l'état de la matière à 'Inactif'")
    
    if dependencies['has_dependencies']:
        for dep_key, dep_detail in dependencies['details'].items():
            report["actions_required"].append(
                f"{dep_detail['suggestion']} ({dep_detail['count']} {dep_detail['nom_affichage']})"
            )
    
    log_security_event("matiere_deletion_report", f"matiere_{id}", "success")
    
    return jsonify(report)

@matieres_bp.route("/detail/<string:id>", methods=["GET"])
@login_required
@ecole_required
def detail_mat(id):
    """Détail d'une matière - VERSION SÉCURISÉE"""
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    # Validation UUID
    if not validate_uuid(id):
        log_security_event("invalid_uuid", f"matiere_{id}", "failed")
        abort(404)
    
    ecole_id = get_current_ecole_id()
    matiere = Matiere.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    log_security_event("matiere_detail", f"matiere_{id}", "success")
    
    return jsonify({
        "id": str(matiere.id),
        "code": matiere.code,
        "libelle": matiere.libelle,
        "etat": matiere.etat,
        "type": matiere.type
    })

@matieres_bp.route("/update/<string:id>", methods=["POST"])
@login_required
@ecole_required
def update_mat(id):
    """Met à jour une matière - VERSION SÉCURISÉE"""
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    # Validation des permissions
    if not is_admin():
        log_security_event(
            "unauthorized_action", 
            f"update_matiere_{id}", 
            "failed", 
            {"user_id": current_user.id}
        )
        return jsonify({"error": "Accès refusé"}), 403
    
    # Validation UUID
    if not validate_uuid(id):
        log_security_event("invalid_uuid", f"matiere_{id}", "failed")
        return jsonify({"error": "ID matière invalide"}), 400
    
    ecole_id = get_current_ecole_id()
    matiere = Matiere.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    if matiere.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de modifier cette matière, état non inactif!"}), 400
    
    data = request.form
    nouveau_code = sanitize_input(data.get("code"), max_length=20, allowed_pattern=r'^[A-Z0-9\-_]{1,20}$')
    nouveau_libelle = sanitize_input(data.get("libelle"), max_length=100)
    nouveau_type = sanitize_input(data.get("type", matiere.type), max_length=50)

    # Validation des données
    if not nouveau_libelle:
        return jsonify({"error": "Le libellé de la matière est obligatoire"}), 400

    # Validation des données avec la fonction sécurisée
    is_valid, error_msg = validate_matiere_data(nouveau_code, nouveau_libelle, nouveau_type)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # Vérifier l'unicité du code (exclure la matière actuelle)
    existing_code = Matiere.query.filter(
        Matiere.code == nouveau_code,
        Matiere.ecole_id == ecole_id,
        Matiere.id != id
    ).first()
    if existing_code:
        return jsonify({"error": f"Le code '{nouveau_code}' est déjà utilisé par une autre matière"}), 400

    # Vérifier l'unicité du libellé (exclure la matière actuelle)
    existing_libelle = Matiere.query.filter(
        Matiere.libelle == nouveau_libelle,
        Matiere.ecole_id == ecole_id,
        Matiere.id != id
    ).first()
    if existing_libelle:
        return jsonify({"error": f"Le libellé '{nouveau_libelle}' est déjà utilisé par une autre matière"}), 400

    try:
        matiere.code = nouveau_code
        matiere.libelle = nouveau_libelle
        matiere.type = nouveau_type
        db.session.commit()
        
        current_app.logger.info(
            f"Matière modifiée - ID: {id}, Code: {nouveau_code}, "
            f"Par utilisateur: {current_user.id}"
        )
        
        log_security_event(
            "matiere_update", 
            f"matiere_{id}", 
            "success", 
            {"new_code": nouveau_code, "new_libelle": nouveau_libelle}
        )
        
        return jsonify({
            "id": str(matiere.id),
            "code": matiere.code,
            "libelle": matiere.libelle,
            "type": matiere.type,
            "etat": matiere.etat,
            "message": "Matière modifiée avec succès"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur modification matière ID {id} - Utilisateur: {current_user.id}, Erreur: {str(e)}"
        )
        log_security_event(
            "matiere_update", 
            f"matiere_{id}", 
            "failed", 
            {"error": str(e)}
        )
        return jsonify({"error": "Erreur lors de la modification"}), 500

@matieres_bp.route("/liste", methods=["GET"])
@login_required
@ecole_required
def liste_matieres():
    """Retourne la liste des matières pour les selects (AJAX) - SÉCURISÉ"""
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    ecole_id = get_current_ecole_id()
    matieres = Matiere.query.filter_by(ecole_id=ecole_id, etat="Actif").order_by(Matiere.libelle).all()
    
    log_security_event("matieres_list_ajax", "matieres", "success")
    
    return jsonify([{
        "id": str(m.id), 
        "libelle": m.libelle,
        "code": m.code,
        "type": m.type
    } for m in matieres])

@matieres_bp.route("/actives", methods=["GET"])
@login_required
@ecole_required
def get_matieres_actives():
    """Retourne les matières actives avec plus de détails - SÉCURISÉ"""
    # Rate limiting
    if not rate_limit_check():
        return jsonify({"error": "Trop de requêtes"}), 429
    
    ecole_id = get_current_ecole_id()
    matieres = Matiere.query.filter_by(ecole_id=ecole_id, etat="Actif").order_by(Matiere.libelle).all()
    
    matieres_list = []
    for matiere in matieres:
        matieres_list.append({
            "id": str(matiere.id),
            "code": matiere.code,
            "libelle": matiere.libelle,
            "type": matiere.type,
            "nb_enseignants": matiere.enseignants.count() if hasattr(matiere, 'enseignants') else 0
        })
    
    log_security_event("matieres_actives_list", "matieres", "success")
    
    return jsonify(matieres_list)

# ==================== MIDDLEWARE DE SÉCURITÉ ====================

@matieres_bp.after_request
def apply_security_headers(response):
    """Applique les headers de sécurité après chaque requête - VERSION CORRIGÉE"""
    # Ne pas appliquer aux fichiers statics
    if request.endpoint and 'static' not in request.endpoint:
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY', 
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            # CSP CORRIGÉE - Autorise les styles inline et scripts inline
            'Content-Security-Policy': "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; script-src 'self' 'unsafe-inline'",
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        for header, value in headers.items():
            response.headers[header] = value
    
    return response

# ==================== GESTIONNAIRES D'ERREURS ====================

@matieres_bp.errorhandler(404)
def not_found_error(error):
    """Gestionnaire d'erreur 404 sécurisé"""
    log_security_event(
        "page_not_found", 
        request.path, 
        "failed", 
        {"user_agent": request.headers.get('User-Agent')}
    )
    return jsonify({"error": "Ressource non trouvée"}), 404

@matieres_bp.errorhandler(429)
def rate_limit_error(error):
    """Gestionnaire d'erreur rate limiting"""
    log_security_event(
        "rate_limit_exceeded", 
        request.path, 
        "failed", 
        {"ip": request.remote_addr}
    )
    return jsonify({
        'success': False,
        'error': 'Trop de requêtes. Veuillez réessayer plus tard.'
    }), 429

@matieres_bp.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500 sécurisé"""
    log_security_event(
        "internal_server_error", 
        request.path, 
        "failed", 
        {"error": str(error)}
    )
    return jsonify({"error": "Erreur interne du serveur"}), 500

    
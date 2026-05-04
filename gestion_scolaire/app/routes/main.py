from flask import Blueprint, render_template, request, session, jsonify, abort, current_app
from flask_login import current_user, login_required
from ..models import Ecole
# CORRECTION : Importer depuis le bon chemin
from ..utils import is_system_admin, system_admin_required, get_current_ecole_id
import uuid
import os
import re
from uuid import UUID
import logging
from datetime import datetime
from extensions import db

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

main_bp = Blueprint(
    "main",
    __name__,
    template_folder="../templates/scolaire",
    static_folder="../static/scolaire", 
    static_url_path="/scolaire_static"
)

# ==================== FONCTIONS DE SÉCURITÉ ====================

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
    
    # Nettoyage des caractères dangereux
    param_str = re.sub(r'[<>"\'%;()&+]', '', param_str)
    
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

def validate_ecole_access(ecole_id):
    """Valide l'accès d'un utilisateur à une école spécifique"""
    if not current_user.is_authenticated:
        return False
    
    # Admin système a accès à toutes les écoles
    if is_system_admin():
        return True
    
    # Vérifier que l'utilisateur appartient à cette école
    user_ecole_id = getattr(current_user, 'ecole_id', None)
    return user_ecole_id and str(user_ecole_id) == str(ecole_id)

# ==================== FONCTIONS UTILITAIRES SÉCURISÉES ====================

def get_user_accessible_ecoles():
    """Récupère les écoles accessibles par l'utilisateur - VERSION CORRIGÉE"""
    try:
        if not current_user.is_authenticated:
            return []
        
        if is_system_admin():
            # Pour les admins système, retourner toutes les écoles
            ecoles = Ecole.query.order_by(Ecole.nom).all()
        else:
            # CORRECTION : Pour les utilisateurs normaux, retourner seulement leur école
            user_ecole_id = getattr(current_user, 'ecole_id', None)
            if user_ecole_id:
                ecoles = Ecole.query.filter_by(id=user_ecole_id).all()
            else:
                ecoles = []
        
        return ecoles
        
    except Exception as e:
        current_app.logger.error(f"Erreur récupération écoles: {str(e)}")
        return []


# ==================== ROUTES SÉCURISÉES ====================

@main_bp.route("/")
@login_required
def index():
    """Page d'accueil principale - VERSION SÉCURISÉE"""
    # Vérification basique de rate limiting
    if not rate_limit_check():
        abort(429, "Trop de requêtes")
    
    log_security_event("page_access", "dashboard", "success")
    
    # Informations utilisateur sécurisées
    username = sanitize_input(current_user.username, max_length=50) if current_user.is_authenticated else "Utilisateur"
    user_role = sanitize_input(getattr(current_user, "role", "Utilisateur"), max_length=30)
    
    return render_template("edashboard.html", 
                         username=username,
                         user_role=user_role)

# routes/main.py - CORRECTION COMPLÈTE ET FONCTIONNELLE

@main_bp.route('/select-ecole', methods=['POST'])
@login_required
def select_ecole():
    """Sélectionner une école pour la session"""
    try:
        data = request.json
        ecole_id = data.get('ecole_id')
        
        print(f"DEBUG select_ecole: user={current_user.username}, requested ecole_id={ecole_id}")
        
        # Pour l'admin système
        if current_user.is_system_admin and current_user.username == 'admin':
            if ecole_id:
                # Convertir en UUID si nécessaire
                if isinstance(ecole_id, str):
                    try:
                        ecole_id = uuid.UUID(ecole_id)
                    except:
                        return jsonify({'success': False, 'error': 'ID école invalide'}), 400
                
                # Stocker dans la session
                session['selected_ecole_id'] = str(ecole_id)
                print(f"DEBUG: Admin selected ecole_id={ecole_id} (stored in session)")
                
                return jsonify({
                    'success': True, 
                    'message': f'École sélectionnée: {ecole_id}'
                })
            else:
                # Effacer la sélection
                session.pop('selected_ecole_id', None)
                print("DEBUG: Admin cleared ecole selection")
                return jsonify({'success': True, 'message': 'Sélection effacée'})
        
        # Pour les autres utilisateurs, utiliser leur école assignée
        elif current_user.ecole_id:
            # Forcer l'utilisation de l'école de l'utilisateur
            session['selected_ecole_id'] = str(current_user.ecole_id)
            print(f"DEBUG: Non-admin user using assigned ecole_id={current_user.ecole_id}")
            return jsonify({
                'success': True, 
                'message': f'Utilisation de votre école: {current_user.ecole_id}'
            })
        
        else:
            return jsonify({
                'success': False, 
                'error': 'Vous n\'êtes associé à aucune école'
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Erreur select_ecole: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/current-ecole', methods=['GET'])
@login_required
def get_current_ecole():
    """Récupérer les informations de l'école courante - VERSION SÉCURISÉE"""
    try:
        # Rate limiting
        if not rate_limit_check():
            return jsonify({
                'success': False,
                'error': 'Trop de requêtes'
            }), 429
        
        selected_ecole_id = session.get('selected_ecole_id')
        
        if not selected_ecole_id:
            return jsonify({
                'success': False,
                'message': 'Aucune école sélectionnée'
            }), 404
        
        # Validation d'accès
        if not validate_ecole_access(selected_ecole_id):
            session.pop('selected_ecole_id', None)
            log_security_event(
                "unauthorized_ecole_access", 
                f"ecole_{selected_ecole_id}", 
                "failed", 
                {"user_id": current_user.id}
            )
            return jsonify({
                'success': False,
                'message': 'Accès non autorisé à cette école'
            }), 403
        
        ecole = Ecole.query.get(selected_ecole_id)
        if not ecole:
            session.pop('selected_ecole_id', None)
            log_security_event(
                "ecole_not_found", 
                f"ecole_{selected_ecole_id}", 
                "failed", 
                {"user_id": current_user.id}
            )
            return jsonify({
                'success': False,
                'message': 'École non trouvée'
            }), 404
        
        # Données sécurisées (ne pas exposer toutes les informations sensibles)
        ecole_data = {
            'id': str(ecole.id),
            'nom': sanitize_input(ecole.nom, max_length=100),
            'code': sanitize_input(ecole.code, max_length=20),
            'localite': sanitize_input(ecole.localite, max_length=100),
            'dre': sanitize_input(ecole.dre, max_length=100),
            'inspection': sanitize_input(ecole.inspection, max_length=100)
        }
        
        log_security_event("ecole_info_retrieval", f"ecole_{selected_ecole_id}", "success")
        
        return jsonify({
            'success': True,
            'ecole': ecole_data
        })
        
    except Exception as e:
        current_app.logger.error(
            f"Erreur récupération école courante - Utilisateur: {current_user.id}, Erreur: {str(e)}"
        )
        log_security_event(
            "server_error", 
            "get_current_ecole", 
            "failed", 
            {"error": str(e)}
        )
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la récupération de l\'école'
        }), 500

@main_bp.route('/clear-ecole', methods=['POST'])
@login_required
@system_admin_required
def clear_ecole():
    """Effacer la sélection d'école (admin système seulement) - VERSION SÉCURISÉE"""
    try:
        # Rate limiting
        if not rate_limit_check():
            return jsonify({
                'success': False,
                'error': 'Trop de requêtes'
            }), 429
        
        session.pop('selected_ecole_id', None)
        
        log_security_event("ecole_clear", "session", "success")
        
        current_app.logger.info(
            f"Sélection école effacée - Par utilisateur: {current_user.id}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Sélection d\'école effacée'
        })
        
    except Exception as e:
        current_app.logger.error(
            f"Erreur effacement école - Utilisateur: {current_user.id}, Erreur: {str(e)}"
        )
        log_security_event(
            "server_error", 
            "clear_ecole", 
            "failed", 
            {"error": str(e)}
        )
        return jsonify({
            'success': False,
            'error': 'Erreur lors de l\'effacement de la sélection'
        }), 500

# ==================== MIDDLEWARE DE SÉCURITÉ ====================

@main_bp.after_request
def apply_security_headers(response):
    """Applique les headers de sécurité après chaque requête - VERSION CORRIGÉE"""
    # Ne pas appliquer aux fichiers statics
    if request.endpoint and 'static' not in request.endpoint:
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY', 
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            # CSP CORRIGÉE - Autorise les styles inline et images data URI
            'Content-Security-Policy': "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; script-src 'self'",
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        for header, value in headers.items():
            response.headers[header] = value
    
    return response

# Route de santé sécurisée
@main_bp.route('/health')
def health_check():
    """Route de santé pour vérifier que l'application fonctionne - VERSION SÉCURISÉE"""
    # Informations limitées pour la santé
    health_info = {
        'status': 'healthy',
        'service': 'main_bp',
        'authenticated': current_user.is_authenticated
    }
    
    # Ne pas exposer d'informations sensibles même dans health check
    if current_user.is_authenticated:
        health_info['user_id'] = str(current_user.id)
        health_info['is_system_admin'] = is_system_admin()
    
    return jsonify(health_info)

# Gestionnaire d'erreurs sécurisé
@main_bp.errorhandler(404)
def not_found_error(error):
    """Gestionnaire d'erreur 404 sécurisé"""
    log_security_event(
        "page_not_found", 
        request.path, 
        "failed", 
        {"user_agent": request.headers.get('User-Agent')}
    )
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500 sécurisé"""
    log_security_event(
        "internal_server_error", 
        request.path, 
        "failed", 
        {"error": str(error)}
    )
    return render_template('500.html'), 500

@main_bp.errorhandler(429)
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

# Ajoutez cette route temporaire pour debug
@main_bp.route('/debug-ecole')
@login_required
def debug_ecole():
    """Route de debug pour vérifier les écoles"""
    from flask import jsonify
    from app.models import Ecole
    
    user_ecole_id = getattr(current_user, 'ecole_id', None)
    
    debug_info = {
        'user': current_user.username,
        'user_ecole_id': str(user_ecole_id) if user_ecole_id else None,
        'ecole_exists': False,
        'all_ecoles': []
    }
    
    # Vérifier si l'école de l'utilisateur existe
    if user_ecole_id:
        ecole = Ecole.query.get(user_ecole_id)
        debug_info['ecole_exists'] = ecole is not None
        if ecole:
            debug_info['ecole_nom'] = ecole.nom
    
    # Lister toutes les écoles
    all_ecoles = Ecole.query.all()
    debug_info['all_ecoles'] = [{'id': str(e.id), 'nom': e.nom} for e in all_ecoles]
    
    return jsonify(debug_info)
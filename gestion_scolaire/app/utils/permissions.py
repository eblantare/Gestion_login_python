# permissions.py - VERSION CORRIGÉE AVEC LOGIQUE EXACTE

from functools import wraps
from flask import session, current_app, jsonify
from flask_login import current_user

def is_system_admin():
    """Détermine si l'utilisateur est l'admin système UNIQUE"""
    if not current_user.is_authenticated:
        return False
    
    # CORRECTION : L'admin système est UNIQUEMENT celui avec username = 'admin'
    # et/ou is_system_admin = True dans la base
    if hasattr(current_user, 'is_system_admin') and current_user.is_system_admin:
        return True
    
    # CORRECTION CRITIQUE : Seul le username 'admin' est admin système
    # Tous les autres utilisateurs avec rôle 'admin' sont des admins d'école
    if hasattr(current_user, 'username') and current_user.username == 'admin':
        return True
    
    # CORRECTION : Même si le rôle est 'admin', si le username n'est pas 'admin'
    # et is_system_admin est False, c'est un admin d'école
    return False

def is_ecole_admin():
    """Détermine si l'utilisateur est administrateur d'une école spécifique"""
    if not current_user.is_authenticated:
        return False
    
    # CORRECTION : Si c'est un admin système, ce n'est PAS un admin d'école
    if is_system_admin():
        return False
    
    user_role = getattr(current_user, 'role', '').lower().strip()
    
    # CORRECTION : 'admin' OU 'administrateur' = admin d'école (sauf admin système)
    ecole_admin_roles = ['admin', 'administrateur', 'ecole_admin', 'admin_ecole', 'directeur', 'chef_etablissement']
    
    result = user_role in ecole_admin_roles
    
    print(f"🔐 PERMISSIONS CORRIGÉ - User: {current_user.username}, Role: '{user_role}', is_ecole_admin: {result}")
    return result

def get_user_type():
    """Retourne le type d'utilisateur corrigé"""
    if not current_user.is_authenticated:
        return 'anonymous'
    
    if is_system_admin():
        return 'system_admin'
    elif is_ecole_admin():
        return 'ecole_admin'
    else:
        return 'regular_user'

def is_regular_user():
    """Détermine si l'utilisateur est un utilisateur régulier (non-admin)"""
    if not current_user.is_authenticated:
        return False
    
    return not (is_system_admin() or is_ecole_admin())

def can_manage_enseignants():
    """Détermine si l'utilisateur peut gérer les enseignants"""
    if not current_user.is_authenticated:
        return False
    
    return is_system_admin() or is_ecole_admin()

# ========== DÉCORATEURS ==========

def system_admin_required(f):
    """Décorateur pour restreindre l'accès aux admins système seulement"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_system_admin():
            return jsonify({'error': 'Accès réservé aux administrateurs système'}), 403
        return f(*args, **kwargs)
    return decorated_function

def ecole_admin_required(f):
    """Décorateur pour restreindre l'accès aux admins d'école seulement"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_ecole_admin():
            return jsonify({'error': 'Accès réservé aux administrateurs d\'école'}), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour les admins (système et école)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (is_system_admin() or is_ecole_admin()):
            return jsonify({'error': 'Accès administrateur requis'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ========== FONCTIONS UTILITAIRES ==========

def get_current_ecole_id():
    """Récupère l'ID de l'école courante - VERSION CORRIGÉE"""
    from flask import request, session
    
    # Priorité 1: Session (utilisez 'selected_ecole_id' qui existe)
    if 'selected_ecole_id' in session:
        return session['selected_ecole_id']
    
    # Priorité 2: Paramètre URL (pour les admins système)
    ecole_url = request.args.get('ecole')
    if ecole_url:
        session['selected_ecole_id'] = ecole_url
        return ecole_url
    
    # Priorité 3: École de l'utilisateur connecté
    if hasattr(current_user, 'ecole_id') and current_user.ecole_id:
        return current_user.ecole_id
    
    return None

def can_access_ecole(ecole_id):
    """Vérifie si l'utilisateur peut accéder à cette école"""
    if not ecole_id:
        return False
        
    if is_system_admin():
        return True
    
    user_ecole_id = getattr(current_user, 'ecole_id', None)
    return user_ecole_id and str(user_ecole_id) == str(ecole_id)

def ecole_required(f):
    """
    Décorateur pour s'assurer qu'une école est sélectionnée/assignée
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ecole_id = get_current_ecole_id()
        
        # Si admin système, permettre l'accès même sans école spécifique
        if is_system_admin():
            if not ecole_id:
                current_app.logger.info(f"Admin système {current_user.id} travaille sans école spécifique")
            return f(*args, **kwargs)
        
        # Pour les non-admins, l'école est obligatoire
        if not ecole_id:
            return jsonify({'error': 'Aucune école assignée'}), 400
        
        return f(*args, **kwargs)
    return decorated_function
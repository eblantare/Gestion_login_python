# context.py - VERSION AVEC CONTEXT PROCESSOR CORRIGÉ

from flask import session
from ..models import Ecole
from flask_login import current_user
from .permissions import is_system_admin, is_ecole_admin

# context.py - MODIFICATIONS CRITIQUES
def inject_ecole_context_global():
    """Context processor corrigé - TOUJOURS fournir all_ecoles"""
    print("🎯 CONTEXT PROCESSOR EXÉCUTÉ!")
    
    context = {
        'is_system_admin': False,
        'is_ecole_admin': False,
        'all_ecoles': [],  # ← TOUJOURS initialiser
        'selected_ecole_id': None,
        'selected_ecole': None
    }
    
    if not current_user.is_authenticated:
        return context
    
    try:
        # Détermination des droits
        context['is_system_admin'] = is_system_admin()
        context['is_ecole_admin'] = is_ecole_admin()
        
        # CORRECTION CRITIQUE : TOUJOURS peupler all_ecoles selon les droits
        if context['is_system_admin']:
            # Admin système voit toutes les écoles
            context['all_ecoles'] = Ecole.query.order_by(Ecole.nom).all()
            print(f"✅ CONTEXT: Admin système - {len(context['all_ecoles'])} écoles chargées")
        else:
            # Utilisateurs normaux voient leur école
            user_ecole_id = getattr(current_user, 'ecole_id', None)
            if user_ecole_id:
                user_ecole = Ecole.query.get(user_ecole_id)
                if user_ecole:
                    context['all_ecoles'] = [user_ecole]
                    print(f"✅ CONTEXT: Utilisateur normal - école: {user_ecole.nom}")
                else:
                    # Fallback sécurisé
                    fallback_ecole = Ecole.query.first()
                    if fallback_ecole:
                        context['all_ecoles'] = [fallback_ecole]
        
        # Gestion de la sélection d'école
        selected_ecole_id = session.get('selected_ecole_id')
        context['selected_ecole_id'] = selected_ecole_id
        
        if selected_ecole_id:
            context['selected_ecole'] = Ecole.query.get(selected_ecole_id)
        elif context['all_ecoles'] and not context['is_system_admin']:
            # Pour les non-admins, utiliser leur première école comme sélectionnée
            context['selected_ecole'] = context['all_ecoles'][0]
            context['selected_ecole_id'] = str(context['all_ecoles'][0].id)
        
        # Debug
        print(f"📊 CONTEXT FINAL: is_system_admin={context['is_system_admin']}, all_ecoles={len(context['all_ecoles'])}, selected_ecole_id={context['selected_ecole_id']}")
        
    except Exception as e:
        print(f"❌ CONTEXT ERROR: {str(e)}")
    
    return context

# Cette fonction n'est plus nécessaire si vous utilisez directement le context processor
def register_context_processor(app):
    @app.context_processor
    def inject_ecole():
        return inject_ecole_context_global()
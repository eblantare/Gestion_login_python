# context.py - VERSION AVEC CONTEXT PROCESSOR CORRIGÉ

from flask import session
from ..models import Ecole
from flask_login import current_user
from .permissions import is_system_admin, is_ecole_admin

def inject_ecole_context_global():
    """Context processor corrigé"""
    print("🎯 CONTEXT PROCESSOR EXÉCUTÉ!")
    
    context = {
        'is_system_admin': False,
        'is_ecole_admin': False,
        'ecoles': [],
        'selected_ecole_id': None,
        'selected_ecole': None
    }
    
    if not current_user.is_authenticated:
        return context
    
    try:
        # Détermination des droits
        context['is_system_admin'] = is_system_admin()
        context['is_ecole_admin'] = is_ecole_admin()
        
        # Récupération des écoles
        if context['is_system_admin']:
            # Admin système voit toutes les écoles
            context['ecoles'] = Ecole.query.order_by(Ecole.nom).all()
        else:
            # CORRECTION CRITIQUE : Utilisateurs normaux voient leur école
            user_ecole_id = getattr(current_user, 'ecole_id', None)
            if user_ecole_id:
                user_ecole = Ecole.query.get(user_ecole_id)
                if user_ecole:
                    context['ecoles'] = [user_ecole]
                else:
                    # Fallback sécurisé
                    fallback_ecole = Ecole.query.first()
                    if fallback_ecole:
                        context['ecoles'] = [fallback_ecole]
        
        # Gestion de la sélection d'école
        selected_ecole_id = session.get('selected_ecole_id')
        context['selected_ecole_id'] = selected_ecole_id
        
        if selected_ecole_id:
            context['selected_ecole'] = Ecole.query.get(selected_ecole_id)
        elif context['ecoles'] and not context['is_system_admin']:
            # CORRECTION : Pour les non-admins, utiliser leur première école comme sélectionnée
            context['selected_ecole'] = context['ecoles'][0]
            context['selected_ecole_id'] = str(context['ecoles'][0].id)
        
    except Exception as e:
        print(f"❌ CONTEXT ERROR: {str(e)}")
    
    return context

# Cette fonction n'est plus nécessaire si vous utilisez directement le context processor
def register_context_processor(app):
    @app.context_processor
    def inject_ecole():
        return inject_ecole_context_global()
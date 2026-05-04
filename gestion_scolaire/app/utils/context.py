# context.py - VERSION AVEC CONTEXT PROCESSOR CORRIGÉ

from flask import session
from ..models import Ecole
from flask_login import current_user
from .permissions import is_system_admin, is_ecole_admin
import uuid
# context.py - MODIFICATIONS CRITIQUES
def inject_ecole_context_global():
    """Injecte le contexte de l'école dans tous les templates"""
    context = {
        'all_ecoles': [],
        'selected_ecole': None,
        'selected_ecole_id': None,
        'is_system_admin': False
    }
    
    try:
        # 1. Vérifier si l'utilisateur est connecté
        if not current_user.is_authenticated:
            return context
        
        # 2. Déterminer si c'est un admin système
        is_system_admin = (current_user.is_authenticated and 
                          hasattr(current_user, 'username') and 
                          current_user.username == 'admin')
        context['is_system_admin'] = is_system_admin
        
        # 3. Récupérer toutes les écoles (pour l'admin) ou l'école de l'utilisateur
        if is_system_admin:
            # Admin système: toutes les écoles
            context['all_ecoles'] = Ecole.query.order_by(Ecole.nom).all()
        else:
            # Utilisateur normal: seulement son école
            if current_user.ecole_id:
                user_ecole = Ecole.query.get(current_user.ecole_id)
                if user_ecole:
                    context['all_ecoles'] = [user_ecole]
        
        # 4. Déterminer l'école sélectionnée
        selected_ecole_id = None
        
        # Priorité 1: session (pour l'admin système)
        if 'selected_ecole_id' in session:
            selected_ecole_id = session['selected_ecole_id']
            print(f"DEBUG context: Using session ecole_id={selected_ecole_id}")
        
        # Priorité 2: école de l'utilisateur (si pas d'admin)
        elif not is_system_admin and current_user.ecole_id:
            selected_ecole_id = str(current_user.ecole_id)
            print(f"DEBUG context: Using user ecole_id={selected_ecole_id}")
        
        # Priorité 3: première école disponible (pour admin sans sélection)
        elif is_system_admin and context['all_ecoles']:
            selected_ecole_id = str(context['all_ecoles'][0].id)
            print(f"DEBUG context: Using first ecole for admin: {selected_ecole_id}")
        
        # 5. Récupérer l'objet école sélectionnée
        if selected_ecole_id:
            try:
                ecole_uuid = uuid.UUID(selected_ecole_id)
                selected_ecole = Ecole.query.get(ecole_uuid)
                if selected_ecole:
                    context['selected_ecole'] = selected_ecole
                    context['selected_ecole_id'] = str(selected_ecole.id)
                    
                    # Mettre à jour current_user.ecole_id pour cette requête
                    if is_system_admin:
                        current_user._ecole_id = selected_ecole.id
                        current_user._ecole_nom = selected_ecole.nom
                    print(f"DEBUG context: Selected ecole={selected_ecole.nom}")
            except Exception as e:
                print(f"DEBUG context error: {e}")
        
        return context
        
    except Exception as e:
        print(f"ERROR in inject_ecole_context_global: {e}")
        return context

# Cette fonction n'est plus nécessaire si vous utilisez directement le context processor
def register_context_processor(app):
    @app.context_processor
    def inject_ecole():
        return inject_ecole_context_global()
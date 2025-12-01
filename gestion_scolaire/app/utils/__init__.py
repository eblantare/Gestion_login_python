# gestion_scolaire/app/utils/__init__.py - VERSION CORRIGÉE
from .permissions import (
    is_system_admin,
    is_ecole_admin, 
    is_regular_user,
    get_user_type,
    can_manage_enseignants,
    system_admin_required,
    ecole_admin_required,
    admin_required,
    ecole_required,  # AJOUTEZ CETTE LIGNE
    get_current_ecole_id,
    can_access_ecole
)

from .context import inject_ecole_context_global, register_context_processor

__all__ = [
    'is_system_admin',
    'is_ecole_admin',
    'is_regular_user', 
    'get_user_type',
    'can_manage_enseignants',
    'system_admin_required',
    'ecole_admin_required',
    'admin_required',
    'ecole_required',
    'get_current_ecole_id',
    'can_access_ecole',
    'inject_ecole_context_global',
    'register_context_processor'
]
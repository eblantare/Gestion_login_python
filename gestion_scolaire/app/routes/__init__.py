# gestion_scolaire/app/routes/__init__.py
from .main import main_bp
from .eleves import eleves_bp
from .classes import classes_bp
from .enseignants import enseignants_bp
from .matieres import matieres_bp
from .appreciations import appreciations_bp
from .paiements import paiements_bp
from .notes import notes_bp
from .moyennes import moyennes_bp
from .enseignements import enseignements_bp
from .ecoles import ecoles_bp
from .services import services_bp
from .bulletins_export import bulletins_export_bp

__all__ = [
    "main_bp",
    "eleves_bp", "classes_bp", "enseignants_bp", "matieres_bp",
    "appreciations_bp", "paiements_bp", "notes_bp", "moyennes_bp", 
    "enseignements_bp", "ecoles_bp", "services_bp", 
     "bulletins_export_bp"  # ✅ Tous inclus
]
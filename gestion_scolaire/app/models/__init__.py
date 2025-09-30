# Import explicite de tous les modèles
from .eleves import Eleve
from .classes import Classe
from .enseignants import Enseignant
from .matieres import Matiere
from .notes import Note
from .moyennes import Moyenne
from .appreciations import Appreciations
from .paiements import Paiement
from .services import Service
from .enseignements import Enseignement
from .ecoles import Ecole

# Liste des exports pour les imports *
__all__ = [
    "Eleve", "Classe", "Enseignant", "Matiere",
    "Note", "Moyenne", "Appreciations",
    "Paiement", "Service", "Enseignement", "Ecole"
]

from flask import Blueprint
from ..models import Enseignant  # si nécessaire

enseignants_bp = Blueprint('enseignants', __name__)

# ici tes routes
@enseignants_bp.route('/')
def liste_enseignants():
    print("Blueprint enseignants_bp chargé avec succès")
    return "Liste des enseignants"
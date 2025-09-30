from flask import Blueprint
from ..models import Enseignement  # si nécessaire

enseignements_bp = Blueprint('enseignements', __name__)

# ici tes routes
@enseignements_bp.route('/')
def liste_enseignement():
    return "Liste des enseignnments"
from flask import Blueprint
from ..models import Paiement  # si nécessaire

paiements_bp = Blueprint('paiements', __name__)

# ici tes routes
@paiements_bp.route('/')
def liste_paiements():
    return "Liste des paiements"
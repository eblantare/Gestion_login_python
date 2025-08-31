from flask import Blueprint
from ..models import Service  # si nécessaire

services_bp = Blueprint('services', __name__)

# ici tes routes
@services_bp.route('/')
def liste_service():
    return "Liste des services"
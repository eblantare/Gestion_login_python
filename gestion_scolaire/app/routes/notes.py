from flask import Blueprint
from ..models import Note  # si nécessaire

notes_bp = Blueprint('notes', __name__)

# ici tes routes
@notes_bp.route('/')
def liste_notes():
    return "Liste des notes"
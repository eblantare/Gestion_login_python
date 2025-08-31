from app.__init__ import create_app
from extensions import db

# Crée l'application scolaire
app = create_app()

# Tu peux préparer la DB scolaire ici si tu veux
with app.app_context():
    db.create_all()
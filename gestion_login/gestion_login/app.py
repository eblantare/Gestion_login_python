from .__init__ import create_app, db
from .models import Utilisateur

# Crée l'application (mais ne la lance pas ici !)
app = create_app()

# Initialise la base uniquement si besoin
with app.app_context():
    db.create_all()
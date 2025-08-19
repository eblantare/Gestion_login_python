from .__init__ import create_app, db
from .models import Utilisateur

app = create_app()

     # Crée les tables si elles n'existent pas
# with app.app_context():
#      db.create_all()

     # Lancement de l'application
     # =========================
with app.app_context():
          db.create_all()
if __name__ == "__main__":
     # Crée la table utilisateurs si elle n'existe pas
     app.run(debug=True)
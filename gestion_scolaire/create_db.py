from run import create_app
from extensions import db   # <-- on enlève gestion_scolaire ici

app = create_app()

with app.app_context():
    print("👉 Suppression des tables...")
    db.drop_all()
    print("👉 Création des tables...")
    db.create_all()
    print("✅ Base de données réinitialisée avec succès.")
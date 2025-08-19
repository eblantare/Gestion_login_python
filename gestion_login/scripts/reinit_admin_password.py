from app import app
from extensions import db
from .models import Utilisateur
from werkzeug.security import generate_password_hash

ADMIN_USERNAME = "admin"
NEW_PASSWORD = "Admin@123"


with app.app_context():
    admin = Utilisateur.query.filter_by(username=ADMIN_USERNAME).first()
    if admin:
        admin.password_hash = generate_password_hash(NEW_PASSWORD)
        db.session.commit()
        print(f"✅ Mot de passe pour {ADMIN_USERNAME} réinitialisé avec succès !")
        print(f"Mot de passe temporaire : {NEW_PASSWORD}")
    else:
        print(f"❌ Aucun utilisateur trouvé avec le nom {ADMIN_USERNAME}")

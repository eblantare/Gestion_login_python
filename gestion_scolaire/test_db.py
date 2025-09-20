import uuid
from werkzeug.security import generate_password_hash
from run import create_app, db   # on réutilise create_app et db
from gestion_login.gestion_login.models import Utilisateur
from datetime import datetime

app = create_app()

with app.app_context():
    # S'assurer que toutes les tables existent
    db.create_all()

    # Vérifier si l'admin existe déjà
    admin = Utilisateur.query.filter_by(username="admin").first()
    if not admin:
        admin_user = Utilisateur(
            nom="Mon_admin",
            prenoms="Mon_admin123",
            username="admin",
            telephone="0000000000",
            email="admin@example.com",
            password_hash=generate_password_hash("Admin@123"),
            role="admin",
            photo_filename=None,
            failed_attempts=0,
            locked_until=None
        )

        db.session.add(admin_user)
        db.session.commit()
        print(f"✅ Utilisateur admin créé avec id: {admin_user.id}")
    else:
        print("ℹ️ Utilisateur admin existe déjà.")
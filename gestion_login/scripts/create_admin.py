import hashlib
from app import app;
from extensions import db
from models import Utilisateur

def create_admin():
    with app.app_context():
        if Utilisateur.query.filter_by(username = "admin").first():
            print("Utilisateur admin exist déjà, ");
            return
        
        admin = Utilisateur(
            nom="Admin",
            prenoms="Super",
            username="admin",
            telephone="+22890000000",
            email="admin@exemple.com",
            password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
            role="admin",
            photo_filename=None
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Compte admin créé avec succès.")
    
if __name__=="__main__":
    create_admin()
import os
from urllib.parse import quote_plus
from flask import Flask, send_from_directory,jsonify
from dotenv import load_dotenv
import uuid
from flask_sqlalchemy import session
# Ajouter le package courant au sys.path pour éviter ModuleNotFound
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import db, login_manager, mail
from gestion_login.gestion_login.routes import auth_bp
from datetime import timedelta
# Import des blueprints
from gestion_scolaire.app.routes import (
    main_bp, eleves_bp, appreciations_bp, classes_bp, matieres_bp,
    enseignants_bp, paiements_bp, notes_bp, moyennes_bp,enseignements_bp,
    ecoles_bp,services_bp, bulletins_export_bp
)

load_dotenv()

def create_default_admin():
    """Crée l'utilisateur admin par défaut s'il n'existe pas"""
    try:
        # Import différé pour éviter les problèmes circulaires
        from gestion_login.gestion_login.models import Utilisateur
        
        # Vérifier si l'admin existe déjà
        existing_admin = Utilisateur.query.filter_by(username='admin').first()
        if existing_admin:
            print("✅ Utilisateur admin existe déjà")
            return True

        # CORRECTION : Ne pas passer l'ID, laisser la base le générer
        admin_user = Utilisateur(
            # SUPPRIMEZ la ligne id=uuid.uuid4() - la base générera l'UUID automatiquement
            nom="Admin",
            prenoms="System", 
            sexe="Masculin",
            username="admin",
            telephone="+2250102030405",
            email="admin@geslog.com",
            role="admin",
            is_system_admin=True
        )
        admin_user.set_password("Admin@123")
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✅ Utilisateur admin créé avec succès!")
        print("📧 Identifiants: admin / Admin@123")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur création admin: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "gestion_scolaire", "app", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "gestion_scolaire", "app", "static")
    )
    app.secret_key = os.getenv("SECRET_KEY")

    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

    # Configuration DB
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Config Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 465))
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")

    # Initialisations
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    mail.init_app(app)

    # Configuration du user_loader
    @login_manager.user_loader
    def load_user(user_id):
        from gestion_login.gestion_login.models import Utilisateur
        try:
            # CORRECTION : Pas besoin de UUID() car l'ID est déjà un string
            return db.session.get(Utilisateur, user_id)
        except:
            return None

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp, url_prefix="/scolaire")
    app.register_blueprint(eleves_bp, url_prefix="/eleves")
    app.register_blueprint(appreciations_bp, url_prefix="/appreciations")
    app.register_blueprint(classes_bp, url_prefix="/classes")
    app.register_blueprint(matieres_bp, url_prefix="/matieres")
    app.register_blueprint(enseignants_bp, url_prefix="/enseignants")
    app.register_blueprint(paiements_bp, url_prefix="/paiements")
    app.register_blueprint(notes_bp, url_prefix="/notes")
    app.register_blueprint(moyennes_bp, url_prefix="/moyennes")
    app.register_blueprint(enseignements_bp, url_prefix="/enseignements")
    
    # 🔥 CORRECTION CRITIQUE : Supprimer le url_prefix supplémentaire
    app.register_blueprint(ecoles_bp)  # Le préfixe /admin/ecoles est déjà dans le blueprint
    
    app.register_blueprint(services_bp, url_prefix='/services')
    # app.register_blueprint(moyennes_export_bp, url_prefix='/moyennes')
    app.register_blueprint(bulletins_export_bp, url_prefix='/')

    # Middleware login
    from gestion_login.gestion_login.utils import login_required_middleware
    login_required_middleware(app, protected_paths=[
        "/eleves", "/enseignants", "/matieres", "/classes",
        "/appreciations", "/paiements", "/notes", "/moyennes","/enseignements","/ecoles","/services", "/listUsers"
    ])

    # Route spéciale pour uploads
    @app.route('/static/upload/<path:filename>') 
    def uploaded_file(filename):
        upload_folder = os.path.join(
            os.path.dirname(__file__),
            "gestion_login", "gestion_login", "static", "upload"
        )
        return send_from_directory(upload_folder, filename)

    # Route spéciale pour les logos
    @app.route('/static/logos/<path:filename>')
    def serve_logo(filename):
        logos_folder = os.path.join(
            os.path.dirname(__file__),
            "gestion_scolaire", "app", "static", "logos"
        )
        return send_from_directory(logos_folder, filename)

    # ✅ CONTEXT PROCESSOR GLOBAL - AJOUTEZ CETTE PARTIE
    from gestion_scolaire.app.utils.context import inject_ecole_context_global
    
    @app.context_processor
    def inject_ecole_global():
        print("🔧 CONTEXT PROCESSOR GLOBAL APPELÉ!")
        result = inject_ecole_context_global()
        print(f"🔧 CONTEXT RESULT GLOBAL: {len(result.get('ecoles', []))} école(s)")
        return result
    
    print("✅ Context processor global configuré")

    # Commande CLI pour créer l'admin manuellement
    @app.cli.command("create-admin")
    def create_admin_cli():
        """Crée un utilisateur admin par défaut (commande manuelle)"""
        create_default_admin()
    return app
     


from sqlalchemy import text
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        try:
            # Créer le schéma et les tables
            db.session.execute(text("CREATE SCHEMA IF NOT EXISTS geslog_schema;"))
            db.session.commit()
            
            # CORRECTION : Importer les modèles APRÈS la création du contexte
            from gestion_scolaire.app.models.ecoles import Ecole
            from gestion_scolaire.app.models import (
                Eleve, Classe, Enseignant, Matiere,
                Note, Moyenne, Appreciations, Paiement, Service, Enseignement
            )
            
            db.create_all()
            print("✅ Tables créées avec succès")
            
            # Créer l'admin par défaut automatiquement
            create_default_admin()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            import traceback
            traceback.print_exc()
        
    app.run(debug=True, port=5000)
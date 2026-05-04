# run.py - VERSION SIMPLIFIÉE SANS TABLEAU SERVICE
import os
from urllib.parse import quote_plus
from flask import Flask, send_from_directory, redirect, url_for
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import db, login_manager, mail
from gestion_login.gestion_login.routes import auth_bp
from datetime import timedelta

# IMPORT DIRECT DES BLUEPRINTS
from gestion_scolaire.app.routes.main import main_bp
from gestion_scolaire.app.routes.eleves import eleves_bp
from gestion_scolaire.app.routes.appreciations import appreciations_bp
from gestion_scolaire.app.routes.classes import classes_bp
from gestion_scolaire.app.routes.matieres import matieres_bp
from gestion_scolaire.app.routes.enseignants import enseignants_bp
from gestion_scolaire.app.routes.paiements import paiements_bp
from gestion_scolaire.app.routes.notes import notes_bp
from gestion_scolaire.app.routes.moyennes import moyennes_bp
from gestion_scolaire.app.routes.enseignements import enseignements_bp
from gestion_scolaire.app.routes.ecoles import ecoles_bp
from gestion_scolaire.app.routes.services import services_bp
from gestion_scolaire.app.routes.bulletins_export import bulletins_export_bp

load_dotenv()

def create_default_admin():
    """Crée l'utilisateur admin par défaut s'il n'existe pas"""
    try:
        from gestion_login.gestion_login.models import Utilisateur
        
        existing_admin = Utilisateur.query.filter_by(username='admin').first()
        if existing_admin:
            print("✅ Admin existe déjà")
            return True

        admin_user = Utilisateur(
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
        
        print("✅ Admin créé - Identifiants: admin / Admin@123")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur création admin: {e}")
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
    app.register_blueprint(ecoles_bp)
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(bulletins_export_bp, url_prefix='/')
    
    # Middleware login
    from gestion_login.gestion_login.utils import login_required_middleware
    login_required_middleware(app, protected_paths=[
        "/eleves", "/enseignants", "/matieres", "/classes",
        "/appreciations", "/paiements", "/notes", "/moyennes",
        "/enseignements", "/ecoles", "/services", "/listUsers"
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

    # ✅ ROUTE RACINE - REDIRIGE VERS LA PAGE DE LOGIN
    @app.route('/')
    def index():
        """Redirige vers la page de connexion"""
        return redirect(url_for('auth.login'))

    # ✅ CONTEXT PROCESSOR GLOBAL
    from gestion_scolaire.app.utils.context import inject_ecole_context_global
    
    @app.context_processor
    def inject_ecole_global():
        """Injecte le contexte de l'école dans tous les templates"""
        result = inject_ecole_context_global()
        return result
    
    # ========== DÉSACTIVER/DÉFINIR CSP PERMISSIVE ==========
    @app.after_request
    def add_security_headers(response):
        """Définit une CSP permissive pour autoriser les scripts inline"""
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-src 'self';"
        )
        return response

    # Commande CLI pour créer l'admin manuellement
    @app.cli.command("create-admin")
    def create_admin_cli():
        """Crée un utilisateur admin par défaut (commande manuelle)"""
        create_default_admin()
    
    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        try:
            from sqlalchemy import text, inspect
            
            # Créer le schéma si nécessaire
            db.session.execute(text("CREATE SCHEMA IF NOT EXISTS geslog_schema;"))
            db.session.commit()
            
            # Importer les modèles de base d'abord
            from gestion_scolaire.app.models import (
                Ecole, Classe, Matiere, Enseignant,
                Eleve, Note, Moyenne, Appreciations, 
                Paiement, Service, Enseignement,
                SystemeEvaluation
            )
            
            # Liste des modèles à créer (dans l'ordre logique)
            models_to_create = [
                Ecole,  # Table racine
                Matiere,
                Classe,
                Enseignant,
                Eleve,
                Note,
                Moyenne,
                Appreciations,
                Paiement,
                Service,
                Enseignement,
                SystemeEvaluation
            ]
            
            # Créer les tables si elles n'existent pas (messages simplifiés)
            created_count = 0
            for Model in models_to_create:
                try:
                    Model.__table__.create(db.engine, checkfirst=True)
                    created_count += 1
                except Exception:
                    pass  # Table existe déjà, on ignore
            
            if created_count > 0:
                print(f"✅ {created_count} tables créées/validées")
            else:
                print("✅ Toutes les tables existent déjà")
            
            # Vérification rapide des tables essentielles
            inspector = inspect(db.engine)
            tables = inspector.get_table_names(schema="geslog_schema")
            
            essential_tables = ['ecoles', 'classes', 'matieres', 'utilisateurs']
            missing_essential = [t for t in essential_tables if t not in tables]
            
            if missing_essential:
                print(f"⚠️  Tables manquantes: {missing_essential}")
            
            # Créer l'admin par défaut automatiquement
            create_default_admin()
            
        except Exception as e:
            print(f"❌ Erreur d'initialisation: {e}")
            db.session.rollback()
    
    print(f"🚀 Application démarrée sur http://localhost:5000")
    print(f"🔗 Page de connexion: http://localhost:5000/login")
    app.run(debug=True, port=5000, host='0.0.0.0')
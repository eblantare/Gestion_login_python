# app/__init__.py - VERSION CORRIGÉE
import os
import sys
from flask import Flask
from dotenv import load_dotenv
from urllib.parse import quote_plus

# ========== IMPORT CORRIGÉ ==========
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

try:
    from extensions import db
except ImportError:
    sys.path.insert(0, os.path.join(project_root, 'common'))
    from extensions import db
# ========== FIN IMPORT CORRIGÉ ==========

# Register blueprints
from .routes.eleves import eleves_bp
from .routes.services import services_bp
from .routes.appreciations import appreciations_bp
from .routes.classes import classes_bp
from .routes.matieres import matieres_bp
from .routes.enseignants import enseignants_bp
from .routes.paiements import paiements_bp
from .routes.notes import notes_bp
from .routes.moyennes import moyennes_bp
from .routes.enseignements import enseignements_bp
# from .routes.tableau_service import tableau_service_bp
from .routes.bulletins_export import bulletins_export_bp
from .routes.main import main_bp
from .routes.ecoles import ecoles_bp
from .utils.context import inject_ecole_context_global
from .utils.permissions import is_system_admin, is_ecole_admin
from .routes.admin import admin_bp


load_dotenv()

def create_app():
    app = Flask(__name__)

    # 🔐 Clé secrète
    app.secret_key = os.getenv("SECRET_KEY")

    # --- Configuration base de données ---
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ========== CONTEXT PROCESSOR ==========
    @app.context_processor
    def utility_processor():
        """Rend les fonctions de permissions disponibles dans tous les templates"""
        return dict(
            is_system_admin=is_system_admin,
            is_ecole_admin=is_ecole_admin
        )
    
    @app.context_processor
    def inject_ecole_global():
        """Injecte le contexte de l'école dans tous les templates"""
        result = inject_ecole_context_global()
        return result
    # ========== FIN CONTEXT PROCESSOR ==========

    # ========== DÉSACTIVER/DÉFINIR CSP PERMISSIVE ==========
    @app.after_request
    def add_security_headers(response):
        """Définit une CSP permissive pour autoriser les scripts inline"""
        if 'Content-Security-Policy' not in response.headers:
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
    # ========== FIN CSP ==========

    # Enregistrement des blueprints
    app.register_blueprint(eleves_bp, url_prefix='/eleves')
    app.register_blueprint(enseignants_bp, url_prefix='/enseignants')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(appreciations_bp, url_prefix='/appreciations')
    app.register_blueprint(classes_bp, url_prefix='/classes')
    app.register_blueprint(matieres_bp, url_prefix='/matieres')
    app.register_blueprint(paiements_bp, url_prefix='/paiements')
    app.register_blueprint(notes_bp, url_prefix='/notes')
    app.register_blueprint(moyennes_bp, url_prefix='/moyennes')
    app.register_blueprint(enseignements_bp, url_prefix='/enseignements')
    app.register_blueprint(ecoles_bp, url_prefix='/admin/ecoles')
    app.register_blueprint(admin_bp)
    
    
    app.register_blueprint(bulletins_export_bp, url_prefix='/')
    app.register_blueprint(main_bp, url_prefix='/scolaire')

    # Initialisation de SQLAlchemy
    db.init_app(app)

    return app
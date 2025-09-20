import os
from urllib.parse import quote_plus
from flask import Flask, send_from_directory
from dotenv import load_dotenv

# Ajouter le package courant au sys.path pour éviter ModuleNotFound
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import db, login_manager, mail
from gestion_login.gestion_login.routes import auth_bp

# Import des blueprints
from gestion_scolaire.app.routes import (
    main_bp, eleves_bp, appreciations_bp, classes_bp, matieres_bp,
    enseignants_bp, paiements_bp, notes_bp, moyennes_bp
)

# Import models pour db.create_all()
from gestion_scolaire.app.models import (
    Eleve, Classe, Enseignant, Matiere,
    Note, Moyenne, Appreciations, Paiement, Service
)

load_dotenv()

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "gestion_scolaire", "app", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "gestion_scolaire", "app", "static")
    )
    app.secret_key = os.getenv("SECRET_KEY")

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
    login_manager.login_view = "login"
    mail.init_app(app)

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

    # Middleware login
    from gestion_login.gestion_login.utils import login_required_middleware
    login_required_middleware(app, protected_paths=[
        "/eleves", "/enseignants", "/matieres", "/classes",
        "/appreciations", "/paiements", "/notes", "/moyennes", "/listUsers"
    ])

    # Route spéciale pour uploads
    @app.route('/static/upload/<path:filename>') 
    def uploaded_file(filename):
        upload_folder = os.path.join(
            os.path.dirname(__file__),
            "gestion_login", "gestion_login", "static", "upload"
        )
        return send_from_directory(upload_folder, filename)

    return app

from sqlalchemy import text
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Crée toutes les tables si elles n'existent pas
        db.session.execute(text("CREATE SCHEMA IF NOT EXISTS geslog_schema;"))
        db.session.commit()
        db.create_all()
    app.run(debug=True, port=5000)

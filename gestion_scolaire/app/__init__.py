import os
from flask import Flask
from extensions import db
from dotenv import load_dotenv
from urllib.parse import quote_plus

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
from .routes.main import main_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    # 🔐 Clé secrète
    app.secret_key = os.getenv("SECRET_KEY")

    # --- Même base de données que gestion_login ---
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

   

    app.register_blueprint(eleves_bp, url_prefix='/eleves')
    app.register_blueprint(enseignants_bp, url_prefix='/enseignants')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(appreciations_bp, url_prefix='/appreciations')
    app.register_blueprint(classes_bp, url_prefix='/classes')
    app.register_blueprint(matieres_bp, url_prefix='/matieres')
    app.register_blueprint(paiements_bp, url_prefix='/paiements')
    app.register_blueprint(notes_bp, url_prefix='/notes')
    app.register_blueprint(moyennes_bp, url_prefix='/moyennes')
    app.register_blueprint(main_bp, url_prefix='/scolaire')

    # Initialisation de SQLAlchemy
    db.init_app(app)

    return app

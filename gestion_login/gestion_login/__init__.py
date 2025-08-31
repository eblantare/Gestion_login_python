# from .models import db
import os
from flask import Flask
from extensions import db, login_manager, mail
from .routes import auth_bp
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

def create_app():
    app = Flask(__name__)
    # 🔐 Configuration
    app.secret_key = os.getenv("SECRET_KEY")

        # Configuration DB PostgreSQL
    # ----------------------------
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")


    DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # app.config['SQLALCHEMY_SCHEMA'] = 'geslog_schema'
     # ----------------------------
    # Configuration mail
    # ----------------------------
    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 465))
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_DEFAULT_SENDER'] = "romain.blantare@gmail.com"


    
    # @app.context_processor
    # def inject_urls():
    #     return {
    #         "scolaire_url": os.getenv("SCOLAIRE_URL")
    #     }
    
    # ----------------------------
    # Initialisation extensions
    # ----------------------------
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Page de login par défaut
    login_manager.login_view = "auth.login"

    # ----------------------------
    # Register blueprint
    # ----------------------------
    app.register_blueprint(auth_bp)

    # Créer dossier upload si inexistant
    upload_folder = os.path.join(app.root_path, "static", "upload")
    os.makedirs(upload_folder, exist_ok=True)

    return app


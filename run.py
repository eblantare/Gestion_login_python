from flask import Flask
from extensions import db,login_manager, mail
from gestion_login.gestion_login.routes import auth_bp
from gestion_scolaire.app.routes import main_bp
from gestion_scolaire.app.routes.eleves import eleves_bp
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), "gestion_scolaire", "app", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "gestion_scolaire", "app", "static"))
    app.secret_key = os.getenv("SECRET_KEY")  # utiliser la clé depuis .env

    # Configuration PostgreSQL depuis .env
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))  # encode special chars
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialiser db
    db.init_app(app)

        # Initialiser Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "login"  # endpoint de ta route login

    # Initialiser Flask-Mail (si tu l’utilises)
    mail.init_app(app)

    # Enregistrer les blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp, url_prefix="/scolaire")
    app.register_blueprint(eleves_bp, url_prefix="/eleves")

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
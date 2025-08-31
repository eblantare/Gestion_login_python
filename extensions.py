# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

# Classe de base avec le schéma par défaut
class BaseModel(db.Model):
    __abstract__ = True
    __table_args__ = {"schema": "geslog_schema"}
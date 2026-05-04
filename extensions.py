# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

# Classe de base avec le schéma par défaut et timestamps
class BaseModel(db.Model):
    __abstract__ = True
    __table_args__ = {"schema": "geslog_schema"}
    
    # Ajouter les timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
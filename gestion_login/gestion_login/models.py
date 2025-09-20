import hashlib
from extensions import db, BaseModel
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class Utilisateur(BaseModel,UserMixin):
    __tablename__ = "utilisateurs"
    __table_args__ = {"schema": "geslog_schema"}  # <-- c'est ici !
    #Générer un uuid par défaut pour l'id
    id = db.Column(UUID(as_uuid=True), primary_key=True,default = uuid.uuid4, unique = True, nullable=False) 
    # id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenoms = db.Column(db.String(100), nullable=False)
    sexe = db.Column(db.String(40), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    telephone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    photo_filename = db.Column(db.String(255), nullable=True)

    #Sécurité connexion
    failed_attempts = db.Column(db.Integer, nullable = False, default = 0)
    locked_until =  db.Column(db.DateTime, nullable=True)



#setter
    def set_password(self, password):
            self.password_hash = generate_password_hash(password)
    
#verification
    def check_password(self, password):
         return check_password_hash(self.password_hash, password)

    # Méthodes utilitaires
    @staticmethod
    def password_is_strong(password):
        pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$'
        return re.match(pattern, password) is not None

    @staticmethod
    def email_is_valid(email):
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email) is not None

    @staticmethod
    def phone_is_valid(telephone):
        pattern = r'^\+?\d{8,15}$'
        return re.match(pattern, telephone) is not None

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
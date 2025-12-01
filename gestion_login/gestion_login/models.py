import os
import re
import hashlib
from uuid import uuid4, UUID
from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from extensions import db

# Extensions autorisées pour les photos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class Utilisateur(UserMixin, db.Model):
    __tablename__ = 'utilisateurs'
    __table_args__ = {"schema": "geslog_schema"}
    
    # CORRECTION : Utiliser UUID PostgreSQL au lieu de VARCHAR
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenoms = db.Column(db.String(150), nullable=False)
    sexe = db.Column(db.String(10), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    photo_filename = db.Column(db.String(255))
    
    # CORRECTION : Utiliser UUID pour correspondre à la table ecoles
    ecole_id = db.Column(UUID(as_uuid=True), ForeignKey('geslog_schema.ecoles.id'), nullable=True)
    
    is_system_admin = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime(timezone=True))
    
    # Relation avec Ecole
    ecole = relationship("Ecole", backref="utilisateurs", lazy="joined")
    @property
    def ecole_nom(self):
        """Retourne le nom de l'école sans relation circulaire"""
        if not self.ecole_id:
            return "Aucune école"
        
        try:
            from gestion_scolaire.app.models.ecoles import Ecole
            ecole = Ecole.query.get(self.ecole_id)
            return ecole.nom if ecole else "École inconnue"
        except Exception:
            return "École inconnue"
    
    @property 
    def nom_complet(self):
        """Retourne le nom complet"""
        return f"{self.prenoms} {self.nom}"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = uuid4()
    
    def set_password(self, password):
        """Hash et stocke le mot de passe"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def can_manage_users(self):
        """Vérifie si l'utilisateur peut gérer d'autres utilisateurs"""
        return self.role.lower() in ['admin', 'administrateur'] or self.is_system_admin
    
    def can_access_ecole(self, ecole_id):
        """Vérifie si l'utilisateur peut accéder à une école spécifique"""
        if self.is_system_admin:
            return True
        return str(self.ecole_id) == str(ecole_id)
    
    def get_accessible_ecoles(self):
        """Retourne la liste des écoles accessibles"""
        from gestion_scolaire.app.models.ecoles import Ecole
        if self.is_system_admin:
            return Ecole.query.all()
        elif self.ecole_id:
            return [self.ecole]
        return []
    
    def get_id(self):
        return str(self.id)
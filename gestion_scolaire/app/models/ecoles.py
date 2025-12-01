import uuid
import re
from extensions import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event
from sqlalchemy.orm import relationship

class Ecole(BaseModel): 
    __tablename__ = 'ecoles' 
    __table_args__ = {"schema": "geslog_schema", "extend_existing": True} 
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
    code = db.Column(db.String(50), unique=True, nullable=False) 
    nom = db.Column(db.String(200), nullable=False)
    boite_postale = db.Column(db.String(20), nullable=True)
    site = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telephone1 = db.Column(db.String(20), nullable=True)
    telephone2 = db.Column(db.String(20), nullable=True)
    devise = db.Column(db.String(100), nullable=True)
    localite = db.Column(db.String(100), nullable=True)
    inspection = db.Column(db.String(200), nullable=True)
    prefecture = db.Column(db.String(200), nullable=True)
    dre = db.Column(db.String(100), nullable=True)

    # NOUVEAU : Logo de l'école
    logo_filename = db.Column(db.String(255), nullable=True)

    # Chef d'établissement
    chef_etablissement_nom = db.Column(db.String(100))
    chef_etablissement_titre = db.Column(db.String(100), default="LE CHEF D'ÉTABLISSEMENT")
    chef_etablissement_civilite = db.Column(db.String(10), default="M.")

    # Relation avec Utilisateur - chemin complet
    # utilisateurs = relationship("gestion_login.gestion_login.models.Utilisateur", back_populates="ecole")

        # ⚠️ CORRECTION : Méthode pour récupérer les utilisateurs sans relation directe
    def get_utilisateurs(self):
        """Récupère les utilisateurs de l'école sans relation circulaire"""
        from gestion_login.gestion_login.models import Utilisateur
        return Utilisateur.query.filter_by(ecole_id=self.id).all()
    # GARDEZ toutes les relations mais avec des noms UNIQUES pour backref
    classes = relationship("Classe", backref="ecole", cascade="all, delete-orphan")
    eleves = relationship("Eleve", backref="ecole", cascade="all, delete-orphan")
    enseignants = relationship("Enseignant", backref="ecole", cascade="all, delete-orphan")
    matieres = relationship("Matiere", backref="ecole", cascade="all, delete-orphan")
    appreciations = relationship("Appreciations", backref="ecole", cascade="all, delete-orphan")
    notes = relationship("Note", backref="ecole", cascade="all, delete-orphan")
    paiements = relationship("Paiement", backref="ecole", cascade="all, delete-orphan")
    services = relationship("Service", backref="ecole", cascade="all, delete-orphan")

    # SUPPRIMEZ les paramètres 'overlaps' qui causent des problèmes

    @staticmethod
    def validate_phone_number(phone):
        """Valide le format international du numéro de téléphone"""
        if not phone:
            return True, None
        
        pattern = r'^\+[1-9]\d{1,14}$'
        if re.match(pattern, phone.replace(' ', '')):
            return True, None
        else:
            return False, "Format invalide. Utilisez le format international: +228 XX XX XX XX"

    @staticmethod
    def validate_email(email):
        """Valide le format d'email"""
        if not email:
            return True, None
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, None
        else:
            return False, "Format d'email invalide"

    def __repr__(self):
        return f'<Ecole {self.nom}>'

# Validation avant insertion/mise à jour
@event.listens_for(Ecole, 'before_insert')
@event.listens_for(Ecole, 'before_update')
def validate_ecole_data(mapper, connection, target):
    # Validation téléphone 1
    if target.telephone1:
        is_valid, error = Ecole.validate_phone_number(target.telephone1)
        if not is_valid:
            raise ValueError(f"Téléphone 1: {error}")
    
    # Validation téléphone 2
    if target.telephone2:
        is_valid, error = Ecole.validate_phone_number(target.telephone2)
        if not is_valid:
            raise ValueError(f"Téléphone 2: {error}")
    
    # Validation email
    if target.email:
        is_valid, error = Ecole.validate_email(target.email)
        if not is_valid:
            raise ValueError(f"Email: {error}")
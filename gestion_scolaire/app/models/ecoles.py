import uuid
import re
from extensions import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event

class Ecole(BaseModel): 
    __tablename__ = 'ecoles' 
    __table_args__ = {"schema": "geslog_schema", "extend_existing": True} 
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
    code = db.Column(db.String(50), unique=True, nullable=False) 
    nom = db.Column(db.String(200), nullable=False)
    boite_postale = db.Column(db.String(20), nullable=True)
    site = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telephone1 = db.Column(db.String(20), nullable=True)  # Longueur réduite pour format international
    telephone2 = db.Column(db.String(20), nullable=True)  # Longueur réduite pour format international
    devise = db.Column(db.String(100), nullable=True)
    localite = db.Column(db.String(100), nullable=True)
    inspection = db.Column(db.String(200), nullable=True)
    prefecture = db.Column(db.String(200), nullable=True)
    dre = db.Column(db.String(100), nullable=True)

    @staticmethod
    def validate_phone_number(phone):
        """Valide le format international du numéro de téléphone"""
        if not phone:
            return True, None
        
        # Format international: +228 12 34 56 78 ou +22812345678
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
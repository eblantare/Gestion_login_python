from extensions import db,BaseModel  # utilisation de la db bindée
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Appreciations(BaseModel):
     __tablename__ = "appreciations" 
     __table_args__ = ( db.UniqueConstraint('libelle', 'description', 
                        name='uq_libelle_description'), 
                        {"schema": "geslog_schema", "extend_existing": True} ) 
     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
     libelle = db.Column(db.String(200), nullable=False) 
     description = db.Column(db.String(300), nullable=True) 
     etat = db.Column(db.String(40), default="Inactif")




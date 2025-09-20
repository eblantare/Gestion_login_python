import uuid
from extensions import db,BaseModel
from sqlalchemy.dialects.postgresql import UUID

class Paiement(BaseModel): 
    __tablename__ = 'paiements' 
    __table_args__ = {"schema": "geslog_schema", 'extend_existing': True} 
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
    code = db.Column(db.String(50), unique=True, nullable=False) 
    libelle = db.Column(db.String(200), nullable=False) 
    eleve_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.eleves.id"), nullable=False) 
    classe_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.classes.id"), nullable=False) 
    date_payement = db.Column(db.Date, nullable=True) 
    montant_net = db.Column(db.Float,nullable=False) 
    montant_pay= db.Column(db.Float,nullable=False) 
    montant_rest= db.Column(db.Float,nullable=False) 
    # relations 
    eleve = db.relationship("Eleve", backref="paiements") 
    classe = db.relationship("Classe", backref="paiements") 
    etat = db.Column(db.String(20), default="Inactif")

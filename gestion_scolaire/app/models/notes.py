from extensions import db,BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import date

class Note(BaseModel): 
    __tablename__ = "notes" 
    __table_args__ = {"schema": "geslog_schema", 'extend_existing': True} 

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
    note1 = db.Column(db.Float, nullable=True) 
    note2 = db.Column(db.Float, nullable=True) 
    note3 = db.Column(db.Float, nullable=True) 
    note_comp = db.Column(db.Float, nullable=True) 
# 🔹 Nouvelle colonne coefficient (valeur entre 1 et 6) 
    coefficient = db.Column(db.Integer, nullable=False, default=1) # 
    date_saisie = db.Column(db.Date) 
    eleve_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.eleves.id"), nullable=False) 
    matiere_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.matieres.id"), nullable=False) 
# relations 
    trimestre = db.Column(db.Integer, nullable=False, default=1) # 1,2,3 ou 1,2 selon semestre 
    annee_scolaire = db.Column(db.String(9), nullable=False) # ex: "2025-2026" 
    cloture = db.Column(db.Boolean, default=False) 
    eleve = db.relationship("Eleve", backref="notes") 
    matiere = db.relationship("Matiere", backref="notes") 
    etat = db.Column(db.String(20), default="Inactif")
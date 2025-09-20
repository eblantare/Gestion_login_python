# app/models/classes.py
from extensions import db, BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

# Table d'association Many-to-Many avec schema 
classe_enseignant = db.Table( "classe_enseignant", 
                             db.Column("classe_id", UUID(as_uuid=True), 
                             db.ForeignKey("geslog_schema.classes.id"),
                             primary_key=True), db.Column("enseignant_id", UUID(as_uuid=True), 
                             db.ForeignKey("geslog_schema.enseignants.id"), primary_key=True), 
                             schema="geslog_schema",extend_existing=True )

class Classe(BaseModel): 
    __tablename__ = 'classes' 
    __table_args__ = {"schema": "geslog_schema", "extend_existing": True} 
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
    code = db.Column(db.String(50), unique=True, nullable=False) 
    nom = db.Column(db.String(200), nullable=False) 
    effectif = db.Column(db.Integer, nullable=False) 
    etat = db.Column(db.String(20), default="Inactif") 
    # Relation many-to-many vers Enseignant 
    enseignants = db.relationship( "Enseignant", 
                                  secondary=classe_enseignant, 
                                  lazy="subquery", backref=db.backref("classes", lazy="dynamic") )



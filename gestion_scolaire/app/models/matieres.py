# app/models/matieres.py
from extensions import db, BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Matiere(BaseModel):
     __tablename__ = "matieres" 
     __table_args__ = {"schema": "geslog_schema", 'extend_existing': True} 
     # ⚠️ Important pour self-referential FK 
     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
     code = db.Column(db.String(50), unique=True, nullable=False) 
     libelle = db.Column(db.String(200), nullable=False) 
     etat = db.Column(db.String(20), default="Inactif") 
     type = db.Column(db.String(50), nullable=False, default="Autres") 
     parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.matieres.id"), nullable=True) 
     children = db.relationship( "Matiere", backref=db.backref("parent", remote_side=[id]), lazy="select" ) 
     def is_type(self): 
         return self.parent_id is None 
     def __repr__(self): 
        if self.is_type(): 
            return f"<Type Matiere {self.libelle}>" 
        return f"<Matiere {self.libelle} (Type: {self.parent.libelle if self.parent else self.type})>"




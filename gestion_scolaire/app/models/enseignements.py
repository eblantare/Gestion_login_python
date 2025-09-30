# app/models/enseignements.py
from extensions import db, BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Enseignement(BaseModel):
    __tablename__ = "enseignements"
    __table_args__ = {"schema": "geslog_schema", "extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    classe_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.classes.id"), nullable=False)
    matiere_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.matieres.id"), nullable=False)
    enseignant_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.enseignants.id"), nullable=False)

    # Relations
    classe = db.relationship("Classe", backref="enseignements")
    matiere = db.relationship("Matiere", backref="enseignements")
    enseignant = db.relationship("Enseignant", backref="enseignements")

    def __repr__(self):
        return f"<Enseignement {self.enseignant.nom} - {self.matiere.libelle} ({self.classe.nom})>"

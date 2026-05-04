# C:\projets\python\gestion_scolaire\app\models\enseignements.py
# app/models/enseignements.py
from extensions import db, BaseModel
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

class Enseignement(BaseModel):
    __tablename__ = "enseignements"
    __table_args__ = {"schema": "geslog_schema", "extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    classe_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.classes.id"), nullable=False)
    matiere_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.matieres.id"), nullable=False)
    enseignant_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.enseignants.id"), nullable=False)
    
    # 🔑 NOUVEAU: Lien avec l'école
    ecole_id = db.Column(UUID(as_uuid=True), db.ForeignKey('geslog_schema.ecoles.id'), nullable=False)
    
    # AJOUTER CES CHAMPS MANQUANTS :
    volume_horaire_semaine = db.Column(db.Integer, nullable=True, default=0)
    annee_scolaire = db.Column(db.String(50), nullable=True, default="2024-2025")
    statut = db.Column(db.String(20), nullable=True, default="actif")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    classe = db.relationship("Classe", backref="enseignements")
    matiere = db.relationship("Matiere", backref="enseignements")
    enseignant = db.relationship("Enseignant", backref="enseignements")
    ecole = db.relationship("Ecole", backref="enseignements")

    def __repr__(self):
        if self.enseignant and self.matiere and self.classe:
            enseignant_nom = self.enseignant.utilisateur.nom if self.enseignant.utilisateur else "Inconnu"
            return f"<Enseignement {enseignant_nom} - {self.matiere.libelle} ({self.classe.nom})>"
        return f"<Enseignement {self.id}>"
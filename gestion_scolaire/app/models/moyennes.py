from extensions import db, BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Moyenne(BaseModel): 
    __tablename__ = "moyennes" 
    __table_args__ = {"schema": "geslog_schema", 'extend_existing': True} 
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
     # 🔹 Informations générales 
    code = db.Column(db.String(50), nullable=False) # ex: "2025-2026-T1-CLASSE1" 
    annee_scolaire = db.Column(db.String(9), nullable=False) # ex: "2025-2026" 
    trimestre = db.Column(db.Integer, nullable=False) # 1, 2 ou 3 
    # 🔹 Moyennes de l'élève 
    moy_class = db.Column(db.Float, nullable=False) 
    # Moyenne de classe (moyenne de toutes les matières de l'élève) 
    moy_trim = db.Column(db.Float, nullable=False) # Moyenne du trimestre 
    moy_gen = db.Column(db.Float, nullable=True) # Moyenne générale annuelle (calculée au 3e trimestre seulement) 
    # 🔹 Statistiques de la classe 
    moy_faible = db.Column(db.Float, nullable=False) # Moyenne la plus faible de la classe 
    moy_forte = db.Column(db.Float, nullable=False) # Moyenne la plus forte de la classe 
    # 🔹 Classement et appréciations 
    classement = db.Column(db.Integer, nullable=False) # Position de l’élève dans la classe 
    eff_comp = db.Column(db.Integer, nullable=False, default=1) # Effectif ayant composé 
    appreciation_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.appreciations.id"), nullable=True) 
    # 🔹 Relations 
    eleve_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.eleves.id"), nullable=False) 
    enseignant_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.enseignants.id"), nullable=False) 
    eleve = db.relationship("Eleve", backref="moyennes") 
    enseignant = db.relationship("Enseignant", backref="moyennes") 
    appreciation = db.relationship("Appreciations", backref="moyennes") 
    # 🔹 État du calcul (Actif = calculé, Clôturé = archivé, Inactif = en attente) 
    etat = db.Column(db.String(20), default="Inactif")

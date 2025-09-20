from extensions import db
from sqlalchemy.dialects.postgresql import UUID


# Table d'association Classe ↔ Enseignant
classe_enseignant = db.Table(
    "classe_enseignant",
    db.Column("classe_id", UUID(as_uuid=True), db.ForeignKey("geslog_schema.classes.id"), primary_key=True),
    db.Column("enseignant_id", UUID(as_uuid=True), db.ForeignKey("geslog_schema.enseignants.id"), primary_key=True),
    schema="geslog_schema",
    extend_existing=True
)

# Table d'association Enseignant ↔ Matiere
enseignants_matieres = db.Table(
    'enseignants_matieres',
    db.Column('enseignant_id', UUID(as_uuid=True), db.ForeignKey('geslog_schema.enseignants.id'), primary_key=True),
    db.Column('matiere_id', UUID(as_uuid=True), db.ForeignKey('geslog_schema.matieres.id'), primary_key=True),
    schema="geslog_schema",
    extend_existing=True
)

from extensions import db,BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Enseignant(BaseModel):
    __tablename__ = 'enseignants'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    prenoms = db.Column(db.String(255), nullable=False)
    date_naissance = db.Column(db.Date)
    sexe = db.Column(db.String(50), nullable=False)
    matiere = db.Column(db.String(200), nullable=False)
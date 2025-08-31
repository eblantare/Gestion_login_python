from extensions import db,BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Note(BaseModel):
    __tablename__ = 'notes'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    eleve_id = db.Column(db.String(200), nullable=False)  # futur FK vers Eleve
    matiere = db.Column(db.String(200), nullable=False)
    valeur = db.Column(db.Float, nullable=False)
    coefficient = db.Column(db.Integer, default=1)
    date_saisie = db.Column(db.Date)
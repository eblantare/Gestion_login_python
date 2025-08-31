from extensions import db,BaseModel  # utilisation de la db bindée
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Eleve(BaseModel):
    __tablename__ = 'eleves'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    matricule = db.Column(db.String(50), unique=True, nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    prenoms = db.Column(db.String(255), nullable=False)
    date_naissance = db.Column(db.Date)
    sexe = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50),default="nouveau")
    classe = db.Column(db.String(200), default="6èm")

    etat = db.Column(db.String(40), default="Inactif")

    def __repr__(self):
        return f"<Eleve {self.matricule} - {self.nom}>"

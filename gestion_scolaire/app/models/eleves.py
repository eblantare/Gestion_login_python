import uuid
from extensions import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID

class Eleve(BaseModel): 
    __tablename__ = 'eleves'
    __table_args__ = {"schema": "geslog_schema",'extend_existing': True} 
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
    matricule = db.Column(db.String(50), unique=True, nullable=False) 
    nom = db.Column(db.String(200), nullable=False) 
    prenoms = db.Column(db.String(255), nullable=False) 
    date_naissance = db.Column(db.Date) 
    sexe = db.Column(db.String(50), nullable=False) 
    status = db.Column(db.String(50),default="nouveau") 
    # Lien vers Classe 
    classe_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.classes.id")) 
    classe = db.relationship("Classe", backref="eleves") 
    etat = db.Column(db.String(40), default="Inactif") 
    def __repr__(self): 
       return f"<Eleve {self.matricule} - {self.nom}>"

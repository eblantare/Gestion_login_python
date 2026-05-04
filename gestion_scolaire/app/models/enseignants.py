# app/models/enseignants.py
from extensions import db, BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

enseignants_matieres = db.Table( 
    'enseignants_matieres', 
    db.Column('enseignant_id', UUID(as_uuid=True), db.ForeignKey('geslog_schema.enseignants.id'), primary_key=True), 
    db.Column('matiere_id', UUID(as_uuid=True), db.ForeignKey('geslog_schema.matieres.id'), primary_key=True), 
    schema="geslog_schema", 
    extend_existing=True 
)

class Enseignant(BaseModel):
    __tablename__ = 'enseignants' 
    __table_args__ = {
        "schema": "geslog_schema", 
        'extend_existing': True
    }

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
    
    utilisateur_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.utilisateurs.id"), nullable=True)
    
    utilisateur = db.relationship(
        "gestion_login.gestion_login.models.Utilisateur", 
        backref="enseignants", 
        lazy="joined",
        foreign_keys=[utilisateur_id]
    ) 
    
    matieres = db.relationship(
        "Matiere", 
        secondary=enseignants_matieres, 
        backref=db.backref("enseignants", lazy="dynamic"), 
        lazy="select"
    )

    ecole_id = db.Column(UUID(as_uuid=True), db.ForeignKey('geslog_schema.ecoles.id'), nullable=False)

    titre = db.Column(db.String(200), nullable=False) 
    date_fonction = db.Column(db.Date, nullable=True) 
    etat = db.Column(db.String(50), default="Inactif")
    
    def set_actif(self, actif=True):
        """Active ou désactive l'enseignant"""
        self.etat = 'Actif' if actif else 'Inactif'
    
    def get_nom_complet(self):
        """Retourne le nom complet de l'enseignant"""
        if self.utilisateur:
            return self.utilisateur.nom_complet
        return self.titre or f"Enseignant {str(self.id)[:8]}"
    
    def get_matieres_str(self):
        """Retourne la liste des matières sous forme de chaîne"""
        if not self.matieres:
            return ""
        return ", ".join([m.libelle for m in self.matieres if hasattr(m, 'libelle')])
    
    def __repr__(self):
        if self.utilisateur:
            return f"<Enseignant: {self.utilisateur.nom} {self.utilisateur.prenoms}>"
        return f"<Enseignant #{self.id[:8]}>"
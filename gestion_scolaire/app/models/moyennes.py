from extensions import db, BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Moyenne(BaseModel): 
    __tablename__ = "moyennes" 
    __table_args__ = {"schema": "geslog_schema", 'extend_existing': True} 

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    # 🔹 Informations générales 
    code = db.Column(db.String(50), nullable=False)  # ex: "2025-2026-T1-CLASSE1" 
    annee_scolaire = db.Column(db.String(9), nullable=False)  # ex: "2025-2026" 
    trimestre = db.Column(db.Integer, nullable=False)  # 1, 2 ou 3 
    # 🔹 Moyennes de l'élève 

    # 🔹 Stats de la classe par trimestre
    moy_faible_trim1 = db.Column(db.Float, nullable=True)
    moy_forte_trim1  = db.Column(db.Float, nullable=True)
    moy_class_trim1  = db.Column(db.Float, nullable=True)

    moy_faible_trim2 = db.Column(db.Float, nullable=True)
    moy_forte_trim2  = db.Column(db.Float, nullable=True)
    moy_class_trim2  = db.Column(db.Float, nullable=True)

    moy_faible_trim3 = db.Column(db.Float, nullable=True)
    moy_forte_trim3  = db.Column(db.Float, nullable=True)
    moy_class_trim3  = db.Column(db.Float, nullable=True)
    moy_mat = db.Column(db.Float, nullable=False) 
    moy_class = db.Column(db.Float, nullable=False) 

    # Moyenne du trimestre (colonne réelle, renommée)
    moy_trim = db.Column(db.Float, nullable=False)
    
    # Moyenne générale annuelle (calculée au 3e trimestre seulement) 
    moy_gen = db.Column(db.Float, nullable=True) 

    # 🔹 Statistiques de la classe 
    moy_faible = db.Column(db.Float, nullable=False)  # Moyenne la plus faible de la classe 
    moy_forte = db.Column(db.Float, nullable=False)  # Moyenne la plus forte de la classe 

    # 🔹 Classement et appréciations 
    classement = db.Column(db.Integer, nullable=False)  # Position de l’élève dans la classe 
    classement_str = db.Column(db.String(10), nullable=True)  # suffixe : 1er, 2ème...
    classement_gen = db.Column(db.Integer, nullable=True)  # Rang général (au 3e trimestre uniquement)
    eff_comp = db.Column(db.Integer, nullable=False, default=1)  # Effectif ayant composé 
    appreciation_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.appreciations.id"), nullable=True) 

    # 🔹 Relations 
       # 🔹 Relations 
    enseignement_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.enseignements.id"), nullable=True)
    enseignement = db.relationship("Enseignement", backref="moyennes")  # ✅ corrigé
    eleve_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.eleves.id"), nullable=False) 
    eleve = db.relationship("Eleve", backref="moyennes") 
    appreciation = db.relationship("Appreciations", backref="moyennes") 


    # 🔹 État du calcul (Actif = calculé, Clôturé = archivé, Inactif = en attente) 
    etat = db.Column(db.String(20), default="Inactif")

    # 🔹 Propriétés pour la vue
    @property
    def moy_trim1(self):
        return self.moy_trim if self.trimestre == 1 else None

    @moy_trim1.setter
    def moy_trim1(self, value):
        if self.trimestre == 1:
            self.moy_trim = value

    @property
    def moy_trim2(self):
        return self.moy_trim if self.trimestre == 2 else None

    @moy_trim2.setter
    def moy_trim2(self, value):
        if self.trimestre == 2:
            self.moy_trim = value

    @property
    def moy_trim3(self):
        return self.moy_trim if self.trimestre == 3 else None

    @moy_trim3.setter
    def moy_trim3(self, value):
        if self.trimestre == 3:
            self.moy_trim = value

    @property
    def moy_faible_trim(self):
        return getattr(self, f"moy_faible_trim{self.trimestre}")

    @property
    def moy_forte_trim(self):
       return getattr(self, f"moy_forte_trim{self.trimestre}")

    @property
    def moy_class_trim(self):
       return getattr(self, f"moy_class_trim{self.trimestre}")

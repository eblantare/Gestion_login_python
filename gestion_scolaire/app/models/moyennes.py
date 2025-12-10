# app/models/moyennes.py - VERSION COMPLÈTE CORRIGÉE
from extensions import db, BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

class Moyenne(BaseModel): 
    __tablename__ = "moyennes" 
    __table_args__ = {"schema": "geslog_schema", 'extend_existing': True} 

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    # 🔹 Informations générales 
    code = db.Column(db.String(50), nullable=False)  # ex: "2025-2026-T1-CLASSE1" 
    annee_scolaire = db.Column(db.String(9), nullable=False)  # ex: "2025-2026" 
    
    # ✅ CORRECTION : Changer "trimestre" en "periode" pour gérer les deux systèmes
    periode = db.Column(db.Integer, nullable=False)  # 1, 2, 3 pour trimestriel OU 1, 2 pour semestriel
    
    # ✅ AJOUT : Type de période (trimestre ou semestre)
    type_periode = db.Column(db.String(20), default='trimestre')  # 'trimestre' ou 'semestre'
    
    # 🔹 Moyennes de l'élève 
    moy_periode = db.Column(db.Float, nullable=False)  # Moyenne de la période
    
    # ✅ CORRECTION CRITIQUE : Ajouter la colonne moy_trim qui existe dans la base
    moy_trim = db.Column(db.Float, nullable=False)  # Alias pour compatibilité
    
    # Moyenne générale annuelle (calculée au 3e trimestre ou 2e semestre) 
    moy_gen = db.Column(db.Float, nullable=True) 
    
    # ✅ NOUVEAU : Moyenne des notes 1, 2, 3 (calculée par matière)
    moyenne_notes = db.Column(db.Float, nullable=True)
    
    # ✅ AJOUT : Moyenne par matière (gardé pour compatibilité)
    moy_mat = db.Column(db.Float, nullable=False) 
    
    # 🔹 Statistiques de la classe 
    moy_class = db.Column(db.Float, nullable=False)  # Moyenne de la classe
    moy_faible = db.Column(db.Float, nullable=False)  # Moyenne la plus faible de la classe 
    moy_forte = db.Column(db.Float, nullable=False)  # Moyenne la plus forte de la classe 

    # 🔹 Classement et appréciations 
    classement = db.Column(db.Integer, nullable=False)  # Position de l'élève dans la classe 
    classement_str = db.Column(db.String(10), nullable=True)  # suffixe : 1er, 2ème...
    classement_gen = db.Column(db.Integer, nullable=True)  # Rang général
    eff_comp = db.Column(db.Integer, nullable=False, default=1)  # Effectif ayant composé 
    appreciation_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.appreciations.id"), nullable=True) 

    # 🔹 Relations 
    enseignement_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.enseignements.id"), nullable=True)
    eleve_id = db.Column(UUID(as_uuid=True), db.ForeignKey("geslog_schema.eleves.id"), nullable=False) 
    
    # ✅ CORRECTION CRITIQUE : Lien avec l'école
    ecole_id = db.Column(UUID(as_uuid=True), db.ForeignKey('geslog_schema.ecoles.id'), nullable=False)

    # 🔹 État du calcul (Actif = calculé, Clôturé = archivé, Inactif = en attente) 
    etat = db.Column(db.String(20), default="Inactif")

    # Relations
    enseignement = db.relationship("Enseignement", backref="moyennes")
    eleve = db.relationship("Eleve", backref="moyennes")
    appreciation = db.relationship("Appreciations", backref="moyennes")
    ecole = db.relationship("Ecole", backref=db.backref("ecole_moyennes", lazy='dynamic'))

    # 🔹 Méthodes pour synchroniser moy_periode et moy_trim
    def __init__(self, **kwargs):
        # S'assurer que moy_trim est toujours défini
        if 'moy_periode' in kwargs and kwargs['moy_periode'] is not None:
            kwargs['moy_trim'] = kwargs['moy_periode']
        elif 'moy_trim' in kwargs and kwargs['moy_trim'] is not None:
            kwargs['moy_periode'] = kwargs['moy_trim']
        elif 'moy_mat' in kwargs and kwargs['moy_mat'] is not None:
            # Si moy_mat est fourni, l'utiliser pour les deux
            kwargs['moy_periode'] = kwargs['moy_mat']
            kwargs['moy_trim'] = kwargs['moy_mat']
        
        # Valeurs par défaut pour les champs obligatoires
        if 'moy_class' not in kwargs:
            kwargs['moy_class'] = 0.0
        if 'moy_faible' not in kwargs:
            kwargs['moy_faible'] = 0.0
        if 'moy_forte' not in kwargs:
            kwargs['moy_forte'] = 0.0
        if 'classement' not in kwargs:
            kwargs['classement'] = 0
        if 'eff_comp' not in kwargs:
            kwargs['eff_comp'] = 0
            
        super().__init__(**kwargs)
    
    def __setattr__(self, name, value):
        # Synchroniser automatiquement moy_periode et moy_trim
        if name == 'moy_periode' and value is not None:
            super().__setattr__('moy_trim', value)
        elif name == 'moy_trim' and value is not None:
            super().__setattr__('moy_periode', value)
        
        super().__setattr__(name, value)
    
    # 🔹 REMPLACER les propriétés par des hybrid_property pour la compatibilité avec les requêtes
    @hybrid_property
    def trimestre(self):
        """Compatibilité: retourne la période si c'est un trimestre"""
        return self.periode if self.type_periode == 'trimestre' else None
    
    @trimestre.expression
    def trimestre(cls):
        """Expression pour les requêtes"""
        from sqlalchemy import case
        return case(
            (cls.type_periode == 'trimestre', cls.periode),
            else_=None
        )
    
    @hybrid_property
    def semestre(self):
        """Retourne la période si c'est un semestre"""
        return self.periode if self.type_periode == 'semestre' else None
    
    @semestre.expression
    def semestre(cls):
        """Expression pour les requêtes"""
        from sqlalchemy import case
        return case(
            (cls.type_periode == 'semestre', cls.periode),
            else_=None
        )
    
    @hybrid_property
    def moy_sem(self):
        """Retourne moy_periode si c'est un semestre"""
        return self.moy_periode if self.type_periode == 'semestre' else None
    
    @moy_sem.expression
    def moy_sem(cls):
        """Expression pour les requêtes"""
        from sqlalchemy import case
        return case(
            (cls.type_periode == 'semestre', cls.moy_periode),
            else_=None
        )

    def get_periode_display(self):
        """Retourne l'affichage de la période selon le type"""
        if self.type_periode == 'semestre':
            return f"Semestre {self.periode}"
        else:
            return f"Trimestre {self.periode}"

    def __repr__(self):
        return f'<Moyenne {self.eleve_id} - {self.get_periode_display()}: {self.moy_periode}>'
# models/ecoles.py - VERSION CORRIGÉE
import uuid
import re
from extensions import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event
from sqlalchemy.orm import relationship

class Ecole(BaseModel): 
    __tablename__ = 'ecoles' 
    __table_args__ = {"schema": "geslog_schema", "extend_existing": True} 
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False) 
    code = db.Column(db.String(50), unique=True, nullable=False) 
    nom = db.Column(db.String(200), nullable=False)
    boite_postale = db.Column(db.String(20), nullable=True)
    site = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telephone1 = db.Column(db.String(20), nullable=True)
    telephone2 = db.Column(db.String(20), nullable=True)
    devise = db.Column(db.String(100), nullable=True)
    localite = db.Column(db.String(100), nullable=True)
    inspection = db.Column(db.String(200), nullable=True)
    prefecture = db.Column(db.String(200), nullable=True)
    dre = db.Column(db.String(100), nullable=True)

    # Logo de l'école
    logo_filename = db.Column(db.String(255), nullable=True)

    # Chef d'établissement
    chef_etablissement_nom = db.Column(db.String(100))
    chef_etablissement_titre = db.Column(db.String(100), default="LE CHEF D'ÉTABLISSEMENT")
    chef_etablissement_civilite = db.Column(db.String(10), default="M.")

    # ✅ AJOUT : Cycles disponibles (collège/lycée) SEULEMENT
    cycles_disponibles = db.Column(db.JSON, default=lambda: {'college': True, 'lycee': False})

    # ⚠️ SUPPRIMÉ : Pas de systeme_evaluation ici, c'est dans la relation
    
    # ⚠️ CORRECTION : Méthode pour récupérer les utilisateurs sans relation directe
    def get_utilisateurs(self):
        """Récupère les utilisateurs de l'école sans relation circulaire"""
        from gestion_login.gestion_login.models import Utilisateur
        return Utilisateur.query.filter_by(ecole_id=self.id).all()

    def __repr__(self):
        return f'<Ecole {self.nom}>'
    
        # ✅ AJOUT : Méthodes de validation STATIQUES (à ajouter)
    @staticmethod
    def validate_phone_number(phone):
        """Validation simple des numéros de téléphone"""
        if not phone:
            return True, "Numéro vide"
        
        # Nettoyer le numéro
        phone_clean = ''.join(filter(str.isdigit, str(phone)))
        
        # Validation basique : doit avoir entre 8 et 15 chiffres
        if len(phone_clean) < 8 or len(phone_clean) > 15:
            return False, "Le numéro doit contenir entre 8 et 15 chiffres"
        
        # Format international commençant par 00 ou +
        if phone.startswith('00') or phone.startswith('+'):
            if len(phone_clean) < 10:
                return False, "Numéro international trop court"
        
        return True, "Numéro valide"
    
    @staticmethod
    def validate_email(email):
        """Validation simple des emails"""
        if not email:
            return True, "Email vide"
        
        # Expression régulière simple pour valider un email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Format d'email invalide"
        
        return True, "Email valide"
    
    # ✅ AJOUT : Méthodes utilitaires pour les cycles
    def a_college(self):
        """Vérifie si l'école propose le cycle collège"""
        return self.cycles_disponibles.get('college', False)
    
    def a_lycee(self):
        """Vérifie si l'école propose le cycle lycée"""
        return self.cycles_disponibles.get('lycee', False)
    
    def a_les_deux_cycles(self):
        """Vérifie si l'école propose les deux cycles"""
        return self.a_college() and self.a_lycee()
    
    def get_cycles_display(self):
        """Retourne une représentation textuelle des cycles disponibles"""
        cycles = []
        if self.a_college():
            cycles.append('Collège')
        if self.a_lycee():
            cycles.append('Lycée')
        
        if not cycles:
            return 'Aucun cycle défini'
        elif len(cycles) == 1:
            return cycles[0]
        else:
            return ' + '.join(cycles)
    
    # ✅ NOUVELLE : Méthode pour obtenir le système d'évaluation
    def get_systeme_evaluation(self):
        """Retourne le système d'évaluation de l'école via la relation"""
        if hasattr(self, 'config_systeme_evaluation'):
            return self.config_systeme_evaluation
        return None
    
    def est_trimestriel(self):
        """Vérifie si l'école utilise le système trimestriel"""
        systeme = self.get_systeme_evaluation()
        if systeme:
            return systeme.type_systeme == 'trimestriel'
        # Par défaut : trimestriel
        return True
    
    def est_semestriel(self):
        """Vérifie si l'école utilise le système semestriel"""
        systeme = self.get_systeme_evaluation()
        if systeme:
            return systeme.type_systeme == 'semestriel'
        # Par défaut : pas semestriel
        return False

# Validation avant insertion/mise à jour
@event.listens_for(Ecole, 'before_insert')
@event.listens_for(Ecole, 'before_update')
def validate_ecole_data(mapper, connection, target):
    # Validation téléphone 1
    if target.telephone1:
        is_valid, error = Ecole.validate_phone_number(target.telephone1)
        if not is_valid:
            raise ValueError(f"Téléphone 1: {error}")
    
    # Validation téléphone 2
    if target.telephone2:
        is_valid, error = Ecole.validate_phone_number(target.telephone2)
        if not is_valid:
            raise ValueError(f"Téléphone 2: {error}")
    
    # Validation email
    if target.email:
        is_valid, error = Ecole.validate_email(target.email)
        if not is_valid:
            raise ValueError(f"Email: {error}")
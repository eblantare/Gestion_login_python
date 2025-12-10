# models/systeme_evaluation.py - VERSION CORRIGÉE
from extensions import db, BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

class SystemeEvaluation(BaseModel):
    __tablename__ = 'systeme_evaluation'
    __table_args__ = {'schema': 'geslog_schema'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ecole_id = db.Column(UUID(as_uuid=True), db.ForeignKey('geslog_schema.ecoles.id'), nullable=False, unique=True)
    
    # Type de système
    type_systeme = db.Column(db.String(20), default='trimestriel')  # 'trimestriel' ou 'semestriel'
    
    # Labels des périodes (stockés en JSON)
    periode_labels = db.Column(db.JSON, default=lambda: {
        'trimestriel': {
            1: "Premier trimestre",
            2: "Deuxième trimestre", 
            3: "Troisième trimestre"
        },
        'semestriel': {
            1: "Premier semestre",
            2: "Deuxième semestre"
        }
    })
    
    # Barème des appréciations
    baremes_appreciations = db.Column(db.JSON, default=lambda: [
        {"min": 16, "max": 20, "libelle": "Très Bien", "couleur": "success"},
        {"min": 14, "max": 15.99, "libelle": "Bien", "couleur": "primary"},
        {"min": 12, "max": 13.99, "libelle": "Assez Bien", "couleur": "info"},
        {"min": 10, "max": 11.99, "libelle": "Passable", "couleur": "warning"},
        {"min": 5, "max": 9.99, "libelle": "Insuffisant", "couleur": "secondary"},
        {"min": 0, "max": 4.99, "libelle": "Très Insuffisant", "couleur": "danger"}
    ])
    
    # Règles de calcul
    calcul_moyenne_annuelle = db.Column(db.Boolean, default=True)
    ponderation_periodes = db.Column(db.JSON, default=lambda: {
        1: 1.0,
        2: 1.0,
        3: 2.0
    })
    
    # Seuils
    seuil_admission = db.Column(db.Float, default=10.0)
    
    # 🔥 CORRECTION : Relation avec backref unique
    ecole = db.relationship('Ecole', backref=db.backref('config_systeme_evaluation', uselist=False))
    
    def __repr__(self):
        return f'<SystemeEvaluation {self.type_systeme} pour {self.ecole.nom if self.ecole else "école inconnue"}>'
    
    def get_periodes_autorisees(self):
        """Retourne les périodes autorisées selon le système"""
        return [1, 2, 3] if self.type_systeme == 'trimestriel' else [1, 2]
    
    def get_label_periode(self, numero):
        """Retourne le label d'une période"""
        labels = self.periode_labels.get(self.type_systeme, {})
        return labels.get(numero, f"Période {numero}")
    
    def get_appreciation(self, moyenne):
        """Trouve l'appréciation correspondant à une moyenne"""
        if moyenne is None:
            return None
            
        for bareme in self.baremes_appreciations:
            if bareme['min'] <= moyenne <= bareme['max']:
                return bareme
        return None
    
    def get_appreciation_libelle(self, moyenne):
        """Retourne juste le libellé de l'appréciation"""
        appreciation = self.get_appreciation(moyenne)
        return appreciation['libelle'] if appreciation else "Non évalué"
    
def get_appreciation_for_moyenne_safe(self, moyenne):
    """Trouve l'appréciation correspondant à une moyenne - VERSION SÉCURISÉE"""
    if moyenne is None:
        return None
    
    try:
        moyenne_float = float(moyenne)
        
        for bareme in self.baremes_appreciations:
            min_val = float(bareme['min'])
            max_val = float(bareme['max'])
            
            # CRITIQUE: Comparaison avec tolérance pour les nombres flottants
            if min_val <= moyenne_float <= (max_val + 0.001):
                return bareme
        
        # Si pas trouvé, log pour debug
        print(f"[DEBUG] Aucune appréciation trouvée pour {moyenne_float}")
        print(f"[DEBUG] Barèmes: {self.baremes_appreciations}")
        
        # Fallback: déterminer manuellement
        if moyenne_float >= 16:
            return {"min": 16, "max": 20, "libelle": "Très Bien", "couleur": "success"}
        elif moyenne_float >= 14:
            return {"min": 14, "max": 15.99, "libelle": "Bien", "couleur": "primary"}
        elif moyenne_float >= 12:
            return {"min": 12, "max": 13.99, "libelle": "Assez Bien", "couleur": "info"}
        elif moyenne_float >= 10:
            return {"min": 10, "max": 11.99, "libelle": "Passable", "couleur": "warning"}
        elif moyenne_float >= 5:
            return {"min": 5, "max": 9.99, "libelle": "Insuffisant", "couleur": "secondary"}
        else:
            return {"min": 0, "max": 4.99, "libelle": "Très Insuffisant", "couleur": "danger"}
            
    except Exception as e:
        print(f"[ERROR] Erreur get_appreciation_for_moyenne_safe: {e}")
        return None
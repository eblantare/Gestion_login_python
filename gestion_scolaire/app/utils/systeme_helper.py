# app/utils/systeme_helper.py - UN SEUL ENDROIT POUR CETTE FONCTION
from ..models import SystemeEvaluation, Ecole
from extensions import db
import uuid

def get_or_create_systeme_evaluation(ecole_id):
    """
    Récupère ou crée le système d'évaluation pour une école.
    C'est la SEULE fonction de ce type dans toute l'application.
    """
    # 1. Essayer de récupérer un système existant
    systeme = SystemeEvaluation.query.filter_by(ecole_id=ecole_id).first()
    
    if systeme:
        return systeme
    
    # 2. Créer un nouveau système par défaut
    ecole = Ecole.query.get(ecole_id)
    
    # Déterminer le type par défaut
    if ecole and hasattr(ecole, 'cycles_disponibles'):
        # Si c'est un lycée (pas de collège)
        if ecole.cycles_disponibles.get('lycee') and not ecole.cycles_disponibles.get('college'):
            type_par_defaut = 'semestriel'
        else:
            type_par_defaut = 'trimestriel'
    else:
        type_par_defaut = 'trimestriel'
    
    # Créer le système
    systeme = SystemeEvaluation(
        id=str(uuid.uuid4()),
        ecole_id=ecole_id,
        type_systeme=type_par_defaut
        # Note: baremes_appreciations est défini par défaut dans le modèle
        # Note: periode_labels est défini par défaut dans le modèle
    )
    
    db.session.add(systeme)
    db.session.commit()
    
    return systeme
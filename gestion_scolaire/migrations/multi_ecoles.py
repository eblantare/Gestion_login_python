from app import create_app, db
from app.models import Ecole, Eleve, Classe, Enseignant, Matiere, Note, Paiement,Appreciations,Moyenne,Service
import uuid

def migrate_to_multi_ecoles():
    app = create_app()
    
    with app.app_context():
        # 1. Créer une école par défaut pour les données existantes
        ecole_defaut = Ecole(
            id=uuid.uuid4(),
            code="DEF001",
            nom="École par défaut",
            email="contact@ecole-defaut.local"
        )
        db.session.add(ecole_defaut)
        db.session.flush()  # Pour obtenir l'ID
        
        # 2. Assigner tous les enregistrements à cette école
        Eleve.query.update({'ecole_id': ecole_defaut.id})
        Classe.query.update({'ecole_id': ecole_defaut.id})
        Enseignant.query.update({'ecole_id': ecole_defaut.id})
        Matiere.query.update({'ecole_id': ecole_defaut.id})
        Note.query.update({'ecole_id': ecole_defaut.id})
        Paiement.query.update({'ecole_id': ecole_defaut.id})
        Appreciations.query.update({'ecole_id': ecole_defaut.id})
        Moyenne.query.update({'ecole_id': ecole_defaut.id})
        Service.query.update({'ecole_id': ecole_defaut.id})
        
        # 3. Créer un admin système (si nécessaire)
        # admin_systeme = Utilisateur(...)
        # admin_systeme.is_system_admin = True
        # db.session.add(admin_systeme)
        
        db.session.commit()
        print("Migration multi-écoles terminée avec succès!")
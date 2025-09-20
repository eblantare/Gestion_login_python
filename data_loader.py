from extensions import db
from gestion_scolaire.app.models.matieres import Matiere
import uuid


class DataLoader:
    @staticmethod
    def preload_type():
        types = [
            "Matières scientifiques",
            "Matières littéraaires",
            "Autres"
        ]
        
        for t in types:
            #Vérifier si le type existe déjà pour éviter les doublons
            existing = Matiere.query.filter_by(libelle=t,parent_id=None).first()
            if not existing:
                m = Matiere(
                    id=uuid.uuid4(),
                    code=t[:3].upper(),  # ex: MAT, LIT, AUT
                    libelle=t,
                    coefficient=0,        # coefficient nul pour type
                    etat="Actif",
                    type="type",          # ou "categorie"
                    parent_id=None
                )
                db.session.add(m)
            db.session.commit()
            print("Types préchargés dansla base.")

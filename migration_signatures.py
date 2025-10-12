from run import create_app
from extensions import db
from sqlalchemy import text

def migration_finale_signatures():
    """Migration finale pour ajouter les colonnes manquantes"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Début de la migration finale des signatures...")
            
            # Vérifier et ajouter les colonnes si elles n'existent pas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Pour la table ecoles (schéma geslog_schema)
            columns_ecoles = [col['name'] for col in inspector.get_columns('geslog_schema.ecoles')]
            print(f"📋 Colonnes existantes dans ecoles: {columns_ecoles}")
            
            # Ajouter les colonnes manquantes pour l'école
            if 'chef_etablissement_nom' not in columns_ecoles:
                print("➕ Ajout des colonnes chef d'établissement...")
                
                db.session.execute(text('''
                    ALTER TABLE geslog_schema.ecoles 
                    ADD COLUMN chef_etablissement_nom VARCHAR(100)
                '''))
                
                db.session.execute(text('''
                    ALTER TABLE geslog_schema.ecoles 
                    ADD COLUMN chef_etablissement_titre VARCHAR(100) DEFAULT 'LE CHEF D''ÉTABLISSEMENT'
                '''))
                
                db.session.execute(text('''
                    ALTER TABLE geslog_schema.ecoles 
                    ADD COLUMN chef_etablissement_civilite VARCHAR(10) DEFAULT 'M.'
                '''))
                print("✅ Colonnes chef d'établissement ajoutées")
            
            # Pour la table classes (schéma geslog_schema)
            columns_classes = [col['name'] for col in inspector.get_columns('geslog_schema.classes')]
            print(f"📋 Colonnes existantes dans classes: {columns_classes}")
            
            if 'titulaire_id' not in columns_classes:
                print("➕ Ajout de la colonne titulaire_id...")
                db.session.execute(text('''
                    ALTER TABLE geslog_schema.classes 
                    ADD COLUMN titulaire_id UUID
                '''))
                print("✅ Colonne titulaire_id ajoutée")
            
            # Mettre à jour l'école avec des valeurs par défaut
            from gestion_scolaire.app.models.ecoles import Ecole
            ecole = Ecole.query.first()
            if ecole:
                if not ecole.chef_etablissement_nom:
                    ecole.chef_etablissement_nom = "NOM DU CHEF"
                    ecole.chef_etablissement_titre = "LE CHEF D'ÉTABLISSEMENT"
                    ecole.chef_etablissement_civilite = "M."
                    print("👤 Chef d'établissement initialisé")
            
            db.session.commit()
            print("✅ Migration finale terminée avec succès")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la migration: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migration_finale_signatures()
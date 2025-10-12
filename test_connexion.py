from run import create_app
from extensions import db
import psycopg2
from psycopg2 import sql

def migration_sql_direct():
    """Migration SQL directe pour éviter les problèmes SQLAlchemy"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Migration SQL directe...")
            
            # Obtenir l'URL de connexion
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"📡 Connexion à: {db_url}")
            
            # Se connecter directement avec psycopg2
            conn = psycopg2.connect(db_url)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Vérifier si les colonnes existent déjà
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'geslog_schema' 
                AND table_name = 'ecoles' 
                AND column_name = 'chef_etablissement_nom'
            """)
            
            if cursor.fetchone():
                print("✅ Colonnes déjà existantes")
            else:
                print("➕ Ajout des colonnes à la table ecoles...")
                
                # Ajouter les colonnes
                cursor.execute("""
                    ALTER TABLE geslog_schema.ecoles 
                    ADD COLUMN chef_etablissement_nom VARCHAR(100)
                """)
                
                cursor.execute("""
                    ALTER TABLE geslog_schema.ecoles 
                    ADD COLUMN chef_etablissement_titre VARCHAR(100) DEFAULT 'LE CHEF D''ÉTABLISSEMENT'
                """)
                
                cursor.execute("""
                    ALTER TABLE geslog_schema.ecoles 
                    ADD COLUMN chef_etablissement_civilite VARCHAR(10) DEFAULT 'M.'
                """)
                
                print("✅ Colonnes chef d'établissement ajoutées")
            
            # Vérifier la table classes
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'geslog_schema' 
                AND table_name = 'classes' 
                AND column_name = 'titulaire_id'
            """)
            
            if cursor.fetchone():
                print("✅ Colonne titulaire_id déjà existante")
            else:
                print("➕ Ajout de la colonne titulaire_id...")
                
                cursor.execute("""
                    ALTER TABLE geslog_schema.classes 
                    ADD COLUMN titulaire_id UUID
                """)
                
                print("✅ Colonne titulaire_id ajoutée")
            
            # Mettre à jour l'école avec des valeurs par défaut
            cursor.execute("""
                UPDATE geslog_schema.ecoles 
                SET chef_etablissement_nom = 'NOM DU CHEF',
                    chef_etablissement_titre = 'LE CHEF D''ÉTABLISSEMENT',
                    chef_etablissement_civilite = 'M.'
                WHERE chef_etablissement_nom IS NULL
            """)
            
            print("👤 Chef d'établissement initialisé avec valeurs par défaut")
            
            cursor.close()
            conn.close()
            
            print("✅ Migration SQL directe terminée avec succès")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration SQL: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migration_sql_direct()
import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
import psycopg2

# Charger les variables d'environnement
load_dotenv()

def check_database_schema():
    """Vérifie l'état de la base de données"""
    
    # Configuration DB - Utiliser directement les valeurs sans quote_plus pour psycopg2
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Admin@123")  # Sans quote_plus
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "geslog_db")
    
    # Chaîne de connexion pour psycopg2
    conn_str = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
    
    try:
        # Se connecter à la base
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()
        
        print("✅ Connexion à la base de données réussie!")
        print("🔍 Vérification de la base de données...")
        
        # Vérifier les tables et leurs colonnes
        tables = ['eleves', 'classes', 'enseignants', 'matieres', 'notes', 
                 'paiements', 'appreciations', 'moyennes','services', 'utilisateurs']
        
        for table in tables:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'geslog_schema' AND table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            print(f"\n📊 Table: {table}")
            
            if columns:
                ecole_id_found = False
                for col_name, data_type, is_nullable in columns:
                    status = "✅" if col_name == 'ecole_id' else "  "
                    if col_name == 'ecole_id':
                        ecole_id_found = True
                    print(f"   {status} {col_name} ({data_type}) - Nullable: {is_nullable}")
                
                if not ecole_id_found:
                    print("   ❌ ecole_id MANQUANT")
            else:
                print("   ⚠️ Table non trouvée")
        
        cursor.close()
        conn.close()
        print("\n🎉 Vérification terminée!")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

if __name__ == "__main__":
    check_database_schema()
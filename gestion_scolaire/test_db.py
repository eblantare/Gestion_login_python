# C:\projets\python\gestion_scolaire\corrections_direct_fixed.py
import psycopg2
from psycopg2 import sql
import sys

def corriger_direct():
    try:
        # Connexion directe à PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            database="gestion_scolaire",
            user="postgres",
            password="votre_mot_de_passe",  # Remplacez par votre mot de passe
            client_encoding='UTF-8'  # Forcer l'encodage UTF-8
        )
        
        cur = conn.cursor()
        
        print("🔍 Vérification des enseignements...")
        
        # 1. Vérifier les enseignements avec matières inactives
        query = """
        SELECT 
            e.id as enseignement_id,
            m.libelle as matiere,
            m.etat as etat_matiere,
            ens.nom_complet as enseignant,
            c.nom as classe
        FROM geslog_schema.enseignements e
        JOIN geslog_schema.matieres m ON e.matiere_id = m.id
        JOIN geslog_schema.enseignants ens ON e.enseignant_id = ens.id
        JOIN geslog_schema.classes c ON e.classe_id = c.id
        WHERE m.etat != 'actif';
        """
        
        cur.execute(query)
        resultats = cur.fetchall()
        
        if resultats:
            print(f"\n⚠️  Trouvé {len(resultats)} enseignements avec matières inactives:")
            for row in resultats:
                # Décode les chaînes si nécessaire
                matiere = row[1] if isinstance(row[1], str) else row[1].decode('utf-8', errors='ignore')
                etat = row[2] if isinstance(row[2], str) else row[2].decode('utf-8', errors='ignore')
                enseignant = row[3] if isinstance(row[3], str) else row[3].decode('utf-8', errors='ignore')
                classe = row[4] if isinstance(row[4], str) else row[4].decode('utf-8', errors='ignore')
                
                print(f"   • {matiere} ({etat}) - {enseignant} - {classe}")
            
            action = input("\nVoulez-vous les supprimer ? (oui/non): ")
            if action.lower() == 'oui':
                delete_query = """
                DELETE FROM geslog_schema.enseignements 
                WHERE matiere_id IN (
                    SELECT id FROM geslog_schema.matieres WHERE etat != 'actif'
                );
                """
                cur.execute(delete_query)
                conn.commit()
                print(f"✅ {len(resultats)} enseignements supprimés.")
        else:
            print("✅ Aucun enseignement avec matière inactive trouvé.")
        
        # 2. Statistiques
        stats_query = """
        SELECT 
            COUNT(*) as total_enseignements,
            COUNT(CASE WHEN m.etat = 'actif' THEN 1 END) as avec_matieres_actives,
            COUNT(CASE WHEN m.etat != 'actif' THEN 1 END) as avec_matieres_inactives
        FROM geslog_schema.enseignements e
        JOIN geslog_schema.matieres m ON e.matiere_id = m.id;
        """
        
        cur.execute(stats_query)
        stats = cur.fetchone()
        
        print(f"\n📊 STATISTIQUES ENSEIGNEMENTS:")
        print(f"   • Total enseignements: {stats[0]}")
        print(f"   • Avec matières actives: {stats[1]}")
        print(f"   • Avec matières inactives: {stats[2]}")
        
        # 3. Statistiques matières
        matieres_query = """
        SELECT 
            COUNT(*) as total_matieres,
            COUNT(CASE WHEN etat = 'actif' THEN 1 END) as matieres_actives,
            COUNT(CASE WHEN etat != 'actif' THEN 1 END) as matieres_inactives
        FROM geslog_schema.matieres;
        """
        
        cur.execute(matieres_query)
        matieres_stats = cur.fetchone()
        
        print(f"\n📊 STATISTIQUES MATIÈRES:")
        print(f"   • Total matières: {matieres_stats[0]}")
        print(f"   • Matières actives: {matieres_stats[1]}")
        print(f"   • Matières inactives: {matieres_stats[2]}")
        
        # 4. Lister les matières inactives
        matieres_inactives_query = """
        SELECT libelle, code, etat FROM geslog_schema.matieres 
        WHERE etat != 'actif' 
        ORDER BY libelle;
        """
        
        cur.execute(matieres_inactives_query)
        matieres_inactives = cur.fetchall()
        
        if matieres_inactives:
            print(f"\n📝 LISTE DES MATIÈRES INACTIVES:")
            for matiere in matieres_inactives:
                libelle = matiere[0] if isinstance(matiere[0], str) else matiere[0].decode('utf-8', errors='ignore')
                code = matiere[1] if isinstance(matiere[1], str) else matiere[1].decode('utf-8', errors='ignore')
                etat = matiere[2] if isinstance(matiere[2], str) else matiere[2].decode('utf-8', errors='ignore')
                print(f"   • {libelle} ({code}) - état: {etat}")
        
        # 5. Option: Activer toutes les matières
        if matieres_inactives:
            print("\n🔧 Options:")
            print("   1. Activer toutes les matières (mettre etat='actif')")
            print("   2. Quitter")
            
            choix = input("Votre choix (1 ou 2): ")
            
            if choix == '1':
                update_query = "UPDATE geslog_schema.matieres SET etat = 'actif' WHERE etat != 'actif';"
                cur.execute(update_query)
                conn.commit()
                print("✅ Toutes les matières sont maintenant actives.")
        
        cur.close()
        conn.close()
        
        print("\n✅ Opération terminée avec succès!")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        print("Vérifiez:")
        print("  1. PostgreSQL est-il démarré?")
        print("  2. Le mot de passe est-il correct?")
        print("  3. La base 'gestion_scolaire' existe-t-elle?")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Demander le mot de passe de manière sécurisée
    import getpass
    print("Connexion à PostgreSQL")
    
    # Vous pouvez remplacer par votre mot de passe réel
    # password = getpass.getpass("Mot de passe PostgreSQL: ")
    password = "votre_mot_de_passe"  # Remplacez par votre mot de passe
    
    corriger_direct()
import psycopg2
import locale

# Vérifier l'encodage par défaut de Python
print("Encodage système Python :", locale.getpreferredencoding())

try:
    conn = psycopg2.connect(
        dbname="geslog_db",
        user="admin",
        password="admin123",
        host="localhost",
        port="5432"
    )

    # Forcer UTF-8 côté client
    cur = conn.cursor()
    cur.execute("SET client_encoding TO 'UTF8';")

    cur.execute("SHOW client_encoding;")
    print("Encodage client :", cur.fetchone())

    # Tester récupération
    cur.execute("SELECT datname, pg_encoding_to_char(encoding) FROM pg_database;")
    print("\nBases et encodages :")
    for row in cur.fetchall():
        print(row)

    cur.execute("SELECT usename FROM pg_user;")
    print("\nUtilisateurs PostgreSQL :")
    for row in cur.fetchall():
        print(row)

    conn.close()

except UnicodeDecodeError as ue:
    print("❌ Erreur de décodage :", ue)
except Exception as e:
    print("❌ Autre erreur :", e)
@echo off
echo ==========================================
echo   RÉINITIALISATION DE LA BASE DE DONNÉES
echo ==========================================

set DB_NAME=geslog_db
set DB_USER=admin

echo 1. Suppression de la base de données existante...
psql -U postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;"

echo 2. Création de la nouvelle base de données...
psql -U postgres -c "CREATE DATABASE %DB_NAME% OWNER %DB_USER%;"

echo 3. Création du schéma et configuration des privilèges...
psql -U postgres -d %DB_NAME% -c "CREATE SCHEMA IF NOT EXISTS geslog_schema;"
psql -U postgres -d %DB_NAME% -c "GRANT ALL PRIVILEGES ON SCHEMA geslog_schema TO %DB_USER%;"
psql -U postgres -d %DB_NAME% -c "ALTER DEFAULT PRIVILEGES IN SCHEMA geslog_schema GRANT ALL ON TABLES TO %DB_USER%;"

echo 4. Vérification...
psql -U postgres -d %DB_NAME% -c "\dn"

echo ==========================================
echo ✅ Base de données '%DB_NAME%' réinitialisée avec succès!
echo ✅ Schéma 'geslog_schema' créé
echo ✅ Tous les droits accordés à l'utilisateur '%DB_USER%'
echo ==========================================

pause
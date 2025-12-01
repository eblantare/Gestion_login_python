-- Migration incrémentale - Ajout de ecole_id aux tables manquantes
BEGIN;

-- 1. Ajouter ecole_id aux tables enseignements et services (si elles n'existent pas)
DO $$ 
BEGIN
    -- Pour enseignements
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'geslog_schema' 
        AND table_name = 'enseignements' 
        AND column_name = 'ecole_id'
    ) THEN
        ALTER TABLE geslog_schema.enseignements ADD COLUMN ecole_id UUID;
    END IF;

    -- Pour services
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'geslog_schema' 
        AND table_name = 'services' 
        AND column_name = 'ecole_id'
    ) THEN
        ALTER TABLE geslog_schema.services ADD COLUMN ecole_id UUID;
    END IF;
END $$;

-- 2. Assigner les enregistrements existants à l'école par défaut
UPDATE geslog_schema.enseignements 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.services 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

-- 3. Rendre les colonnes NOT NULL
DO $$ 
BEGIN
    -- Pour enseignements
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'geslog_schema' 
        AND table_name = 'enseignements' 
        AND column_name = 'ecole_id'
        AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE geslog_schema.enseignements ALTER COLUMN ecole_id SET NOT NULL;
    END IF;

    -- Pour services
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'geslog_schema' 
        AND table_name = 'services' 
        AND column_name = 'ecole_id'
        AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE geslog_schema.services ALTER COLUMN ecole_id SET NOT NULL;
    END IF;
END $$;

-- 4. Ajouter les contraintes de clé étrangère (si elles n'existent pas)
DO $$ 
BEGIN
    -- Pour enseignements
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema = 'geslog_schema' 
        AND table_name = 'enseignements' 
        AND constraint_name = 'fk_enseignements_ecole'
    ) THEN
        ALTER TABLE geslog_schema.enseignements 
        ADD CONSTRAINT fk_enseignements_ecole 
        FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);
    END IF;

    -- Pour services
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema = 'geslog_schema' 
        AND table_name = 'services' 
        AND constraint_name = 'fk_services_ecole'
    ) THEN
        ALTER TABLE geslog_schema.services 
        ADD CONSTRAINT fk_services_ecole 
        FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);
    END IF;
END $$;

-- 5. Créer les index (s'ils n'existent pas)
DO $$ 
BEGIN
    -- Pour enseignements
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'geslog_schema' 
        AND tablename = 'enseignements' 
        AND indexname = 'idx_enseignements_ecole_id'
    ) THEN
        CREATE INDEX idx_enseignements_ecole_id ON geslog_schema.enseignements(ecole_id);
    END IF;

    -- Pour services
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'geslog_schema' 
        AND tablename = 'services' 
        AND indexname = 'idx_services_ecole_id'
    ) THEN
        CREATE INDEX idx_services_ecole_id ON geslog_schema.services(ecole_id);
    END IF;
END $$;

COMMIT;

-- 6. Vérification finale
SELECT 
    table_name,
    EXISTS(
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'geslog_schema' 
        AND table_name = tables.table_name 
        AND column_name = 'ecole_id'
    ) as has_ecole_id,
    EXISTS(
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema = 'geslog_schema' 
        AND table_name = tables.table_name 
        AND constraint_name = 'fk_' || tables.table_name || '_ecole'
    ) as has_foreign_key,
    (SELECT COUNT(*) FROM geslog_schema.ecoles) as ecoles_count
FROM (VALUES 
    ('eleves'), ('classes'), ('enseignants'), ('matieres'), 
    ('notes'), ('paiements'), ('appreciations'), ('moyennes'),
    ('utilisateurs'), ('enseignements'), ('services')
) AS tables(table_name);
-- Migration multi-écoles - Script complet
BEGIN;

-- 1. Ajouter les colonnes ecole_id et is_system_admin à la table utilisateurs (NULLABLE d'abord)
ALTER TABLE geslog_schema.utilisateurs 
ADD COLUMN IF NOT EXISTS ecole_id UUID,
ADD COLUMN IF NOT EXISTS is_system_admin BOOLEAN DEFAULT FALSE;

-- 2. Ajouter ecole_id à toutes les tables métier (NULLABLE d'abord)
ALTER TABLE geslog_schema.eleves 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

ALTER TABLE geslog_schema.classes 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

ALTER TABLE geslog_schema.enseignants 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

ALTER TABLE geslog_schema.matieres 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

ALTER TABLE geslog_schema.notes 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

ALTER TABLE geslog_schema.paiements 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

ALTER TABLE geslog_schema.appreciations 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

ALTER TABLE geslog_schema.moyennes 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

-- 🔥 NOUVEAU: Ajouter ecole_id aux tables enseignements et services
ALTER TABLE geslog_schema.enseignements 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

ALTER TABLE geslog_schema.services 
ADD COLUMN IF NOT EXISTS ecole_id UUID;

-- 3. Vérifier/Créer une école par défaut
INSERT INTO geslog_schema.ecoles (id, code, nom, email, telephone1)
SELECT 
    '11111111-1111-1111-1111-111111111111'::UUID,
    'DEF001',
    'École par défaut',
    'contact@ecole-defaut.local',
    '+228 00 00 00 00'
WHERE NOT EXISTS (SELECT 1 FROM geslog_schema.ecoles WHERE id = '11111111-1111-1111-1111-111111111111'::UUID);

-- 4. Assigner tous les enregistrements existants à l'école par défaut (avec vérification)
UPDATE geslog_schema.eleves 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.classes 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.enseignants 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.matieres 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.notes 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.paiements 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.appreciations 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.moyennes 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

-- 🔥 NOUVEAU: Assigner enseignements et services à l'école par défaut
UPDATE geslog_schema.enseignements 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

UPDATE geslog_schema.services 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

-- 5. Assigner les utilisateurs existants à l'école par défaut
UPDATE geslog_schema.utilisateurs 
SET ecole_id = '11111111-1111-1111-1111-111111111111'::UUID
WHERE ecole_id IS NULL;

-- 6. Maintenant rendre les colonnes NOT NULL (après avoir assigné des valeurs)
ALTER TABLE geslog_schema.eleves 
ALTER COLUMN ecole_id SET NOT NULL;

ALTER TABLE geslog_schema.classes 
ALTER COLUMN ecole_id SET NOT NULL;

ALTER TABLE geslog_schema.enseignants 
ALTER COLUMN ecole_id SET NOT NULL;

ALTER TABLE geslog_schema.matieres 
ALTER COLUMN ecole_id SET NOT NULL;

ALTER TABLE geslog_schema.notes 
ALTER COLUMN ecole_id SET NOT NULL;

ALTER TABLE geslog_schema.paiements 
ALTER COLUMN ecole_id SET NOT NULL;

ALTER TABLE geslog_schema.appreciations 
ALTER COLUMN ecole_id SET NOT NULL;

ALTER TABLE geslog_schema.moyennes 
ALTER COLUMN ecole_id SET NOT NULL;

-- 🔥 NOUVEAU: Rendre NOT NULL pour enseignements et services
ALTER TABLE geslog_schema.enseignements 
ALTER COLUMN ecole_id SET NOT NULL;

ALTER TABLE geslog_schema.services 
ALTER COLUMN ecole_id SET NOT NULL;

-- 7. Ajouter les contraintes de clé étrangère
ALTER TABLE geslog_schema.utilisateurs 
ADD CONSTRAINT fk_utilisateurs_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.eleves 
ADD CONSTRAINT fk_eleves_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.classes 
ADD CONSTRAINT fk_classes_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.enseignants 
ADD CONSTRAINT fk_enseignants_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.matieres 
ADD CONSTRAINT fk_matieres_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.notes 
ADD CONSTRAINT fk_notes_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.paiements 
ADD CONSTRAINT fk_paiements_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.appreciations 
ADD CONSTRAINT fk_appreciations_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.moyennes 
ADD CONSTRAINT fk_moyennes_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

-- 🔥 NOUVEAU: Contraintes pour enseignements et services
ALTER TABLE geslog_schema.enseignements 
ADD CONSTRAINT fk_enseignements_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

ALTER TABLE geslog_schema.services 
ADD CONSTRAINT fk_services_ecole 
FOREIGN KEY (ecole_id) REFERENCES geslog_schema.ecoles(id);

-- 8. Créer des index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_eleves_ecole_id ON geslog_schema.eleves(ecole_id);
CREATE INDEX IF NOT EXISTS idx_classes_ecole_id ON geslog_schema.classes(ecole_id);
CREATE INDEX IF NOT EXISTS idx_enseignants_ecole_id ON geslog_schema.enseignants(ecole_id);
CREATE INDEX IF NOT EXISTS idx_matieres_ecole_id ON geslog_schema.matieres(ecole_id);
CREATE INDEX IF NOT EXISTS idx_notes_ecole_id ON geslog_schema.notes(ecole_id);
CREATE INDEX IF NOT EXISTS idx_paiements_ecole_id ON geslog_schema.paiements(ecole_id);
CREATE INDEX IF NOT EXISTS idx_appreciations_ecole_id ON geslog_schema.appreciations(ecole_id);
CREATE INDEX IF NOT EXISTS idx_moyennes_ecole_id ON geslog_schema.moyennes(ecole_id);
CREATE INDEX IF NOT EXISTS idx_utilisateurs_ecole_id ON geslog_schema.utilisateurs(ecole_id);

-- 🔥 NOUVEAU: Index pour enseignements et services
CREATE INDEX IF NOT EXISTS idx_enseignements_ecole_id ON geslog_schema.enseignements(ecole_id);
CREATE INDEX IF NOT EXISTS idx_services_ecole_id ON geslog_schema.services(ecole_id);

-- 9. Définir un utilisateur comme admin système (remplacez par votre admin)
UPDATE geslog_schema.utilisateurs 
SET is_system_admin = TRUE 
WHERE username = 'admin'  -- Remplacez par le nom d'utilisateur de votre admin
AND is_system_admin = FALSE;

COMMIT;

-- 10. Vérification complète
SELECT 
    'eleves' as table_name, 
    COUNT(*) as total, 
    COUNT(ecole_id) as avec_ecole,
    COUNT(*) - COUNT(ecole_id) as sans_ecole
FROM geslog_schema.eleves
UNION ALL
SELECT 'classes', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.classes
UNION ALL
SELECT 'enseignants', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.enseignants
UNION ALL
SELECT 'matieres', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.matieres
UNION ALL
SELECT 'notes', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.notes
UNION ALL
SELECT 'paiements', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.paiements
UNION ALL
SELECT 'appreciations', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.appreciations
UNION ALL
SELECT 'moyennes', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.moyennes
UNION ALL
SELECT 'utilisateurs', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.utilisateurs
UNION ALL
SELECT 'enseignements', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.enseignements
UNION ALL
SELECT 'services', COUNT(*), COUNT(ecole_id), COUNT(*) - COUNT(ecole_id) FROM geslog_schema.services;
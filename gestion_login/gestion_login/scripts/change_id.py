from app import db, app
from sqlalchemy import text
import uuid

with app.app_context():  # <- indispensable pour accéder à db
    print(f"URI: '{db.engine.url}'")

    with db.engine.connect() as conn:
        # 1. Ajouter la colonne si elle n’existe pas
        conn.execute(text("ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS new_id UUID;"))

        # 2. Récupérer les IDs existants
        result = conn.execute(text("SELECT id FROM utilisateurs;"))
        rows = result.fetchall()

        # 3. Assigner un UUID à chaque utilisateur
        for row in rows:
            conn.execute(
                text("UPDATE utilisateurs SET new_id = :new_id WHERE id = :id"),
                {"new_id": str(uuid.uuid4()), "id": row.id},
            )

        # 4. Commit
        conn.commit()
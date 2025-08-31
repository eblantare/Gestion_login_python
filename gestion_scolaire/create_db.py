from extensions import db
from app import create_app 
from app.models import *  # charge tous les modèles pour que SQLAlchemy les connaisse

app = create_app()

with app.app_context():
    #créer toutes les tables
    for bind_key, engine in db.engines.items():
         db.metadata.create_all(bind=engine)
print("Tables créées dans la base gestion_scolaire_db")
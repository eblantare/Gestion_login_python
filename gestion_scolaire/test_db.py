from app import create_app
from app.models.eleves import Eleve
from extensions import db

app = create_app()

with app.app_context():
    #création de table
    engine = db.engines["scolaire"]
    Eleve.metadata.create_all(bind=engine)

    # Création d'un nouvel élève
    new_eleve = Eleve(
        matricule="ELE123",
        nom="DJALA",
        prenoms="Théo",
        date_naissance="2020-09-23",
        sexe="Masculin",
        status="Nouveau",
        classe="6èm A"
    )

    db.session.add(new_eleve)
    db.session.commit()

    print(f"Élève créé : {new_eleve.nom} {new_eleve.prenoms}")

    # Vérification
    for e in Eleve.query.all():
        print(e)
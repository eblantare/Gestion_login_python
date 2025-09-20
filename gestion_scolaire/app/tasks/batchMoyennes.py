from sqlalchemy import func
from extensions import db
from gestion_scolaire.app.models import Eleve, Note, Moyenne, Appreciations
import uuid

class BatchMoyennes:
    """Classe regroupant les traitements liés au calcul des moyennes."""

    @staticmethod
    def run(annee_scolaire: str, trimestre: int, classe_id: str, enseignant_id: str):
        """
        Lance le calcul des moyennes pour une classe, un trimestre et une année donnée.
        Version debug avec prints détaillés.
        """
        print(f"[DEBUG] Lancement du batch: classe={classe_id}, trimestre={trimestre}, année={annee_scolaire}")

        # Étape 1 : récupérer les élèves de la classe
        eleves = db.session.query(Eleve).filter_by(classe_id=classe_id).all()
        if not eleves:
            print("[DEBUG] Aucun élève trouvé pour cette classe.")
            return "Aucun élève trouvé pour cette classe."
        print(f"[DEBUG] {len(eleves)} élèves trouvés.")

        resultats = []

        for eleve in eleves:
            # Étape 2 : récupérer les notes de l’élève pour l’année + trimestre
            notes = db.session.query(Note).filter_by(
                eleve_id=eleve.id,
                annee_scolaire=annee_scolaire,
                trimestre=trimestre,
                cloture=False
            ).all()
            print(f"[DEBUG] Élève {eleve.nom} {eleve.prenoms} - {len(notes)} notes trouvées.")

            if not notes:
                continue

            # Étape 3 : calcul de la moyenne pondérée
            total_points = sum([
                ((n.note1 or 0) + (n.note2 or 0) + (n.note3 or 0) + (n.note_comp or 0)) / 4 * (n.coefficient or 0)
                for n in notes
            ])
            total_coef = sum([n.coefficient or 0 for n in notes])
            if total_coef == 0:
                print(f"[WARNING] Élève {eleve.nom} {eleve.prenoms} a un total de coefficient = 0")
                moyenne = 0
            else:
                moyenne = round(total_points / total_coef, 2)

            resultats.append({"eleve": eleve, "moyenne": moyenne})
            print(f"[DEBUG] Moyenne calculée pour {eleve.nom} {eleve.prenoms}: {moyenne}")

        if not resultats:
            print("[DEBUG] Aucun résultat de moyenne calculé.")
            return "Aucun élève avec des notes trouvées."

        # Étape 4 : calcul min/max
        moyennes = [r["moyenne"] for r in resultats]
        moy_forte = max(moyennes)
        moy_faible = min(moyennes)
        eff_comp = len(moyennes)
        print(f"[DEBUG] Moyenne forte: {moy_forte}, Moyenne faible: {moy_faible}, Effectif: {eff_comp}")

        # Étape 5 : classement
        resultats_sorted = sorted(resultats, key=lambda x: x["moyenne"], reverse=True)
        for i, r in enumerate(resultats_sorted, start=1):
            r["classement"] = i

        # Étape 6 : appréciation (exemple simple)
        def appreciation(moy):
            if moy >= 16: return "Très Bien"
            elif moy >= 14: return "Bien"
            elif moy >= 12: return "Assez Bien"
            elif moy >= 10: return "Passable"
            else: return "Insuffisant"

        # Étape 7 : insertion en base
        for r in resultats_sorted:
            m = Moyenne(
                id=uuid.uuid4(),
                code=f"{annee_scolaire}-T{trimestre}-{classe_id}-{r['eleve'].id}",
                annee_scolaire=annee_scolaire,
                trimestre=trimestre,
                moy_class=r["moyenne"],
                moy_trim=r["moyenne"],
                moy_gen=None,
                moy_faible=moy_faible,
                moy_forte=moy_forte,
                classement=r["classement"],
                eff_comp=eff_comp,
                eleve_id=r["eleve"].id,
                enseignant_id=enseignant_id,
                etat="Actif"
            )

            # Ajout de l’appréciation
            app = db.session.query(Appreciations).filter_by(libelle=appreciation(r["moyenne"])).first()
            if app:
                m.appreciation_id = app.id
            else:
                print(f"[DEBUG] Pas d'appréciation trouvée pour {r['moyenne']}")

            db.session.add(m)

            # Étape spéciale : calcul de la moyenne annuelle si trimestre = 3
            if trimestre == 3:
                moys = db.session.query(Moyenne).filter_by(
                    eleve_id=r["eleve"].id,
                    annee_scolaire=annee_scolaire
                ).all()
                notes_trim = [x.moy_trim for x in moys if x.moy_trim is not None]
                print(f"[DEBUG] Notes trims pour T3: {notes_trim}")
                if len(notes_trim) == 3:
                    moy_gen = round(sum(notes_trim) / 3, 2)
                    m.moy_gen = moy_gen
                    app_gen = db.session.query(Appreciations).filter_by(libelle=appreciation(moy_gen)).first()
                    if app_gen:
                        m.appreciation_id = app_gen.id
                    else:
                        print(f"[DEBUG] Pas d'appréciation pour la moyenne générale {moy_gen}")

        # Commit avec try/except
        try:
            db.session.commit()
            print("[DEBUG] Commit effectué avec succès.")
        except Exception as e:
            print("[ERROR] Erreur lors du commit:", e)
            db.session.rollback()
            return f"Erreur lors de l'enregistrement : {e}"

        return f"Moyennes du trimestre {trimestre} pour {annee_scolaire} enregistrées avec succès."

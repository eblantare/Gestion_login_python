from extensions import db
from ..models import Moyenne, Note, Eleve, Appreciations, Classe, Enseignement
import uuid, traceback, logging

logger = logging.getLogger(__name__)

def get_appreciation(moyenne):
    if moyenne >= 16:
        return Appreciations.query.filter_by(libelle='Très Bien').first()
    elif moyenne >= 14:
        return Appreciations.query.filter_by(libelle='Bien').first()
    elif moyenne >= 12:
        return Appreciations.query.filter_by(libelle='Assez Bien').first()
    elif moyenne >= 10:
        return Appreciations.query.filter_by(libelle='Passable').first()
    elif moyenne >= 5:
        return Appreciations.query.filter_by(libelle='Insuffisant').first()
    else:
        return Appreciations.query.filter_by(libelle='Très Insuffisant').first()

def format_classement(rank):
    if rank is None:
        return "—"
    if 10 <= rank % 100 <= 20:
        suffix = "ème"
    else:
        suffix = {1: "er", 2: "ème", 3: "ème"}.get(rank % 10, "ème")
    return f"{rank}{suffix}"

def calcul_classement(sorted_list):
    classement_dict = {}
    current_rank = 1
    for idx, (eleve_id, moy) in enumerate(sorted_list):
        if idx > 0 and moy == sorted_list[idx - 1][1]:
            classement_dict[eleve_id] = classement_dict[sorted_list[idx - 1][0]]
        else:
            classement_dict[eleve_id] = current_rank
        current_rank += 1
    return classement_dict

def calculer_moyennes(classe_id, annee_scolaire, trimestre):
    resume = {"success": [], "errors": [], "created": 0, "updated": 0, "total": 0}
    try:
        eleves = Eleve.query.filter_by(classe_id=classe_id).all()
        if not eleves:
            resume["errors"].append(f"Aucun élève trouvé pour la classe {classe_id}")
            return resume

        enseignements_classe = Enseignement.query.filter_by(classe_id=classe_id).all()
        default_enseignement_id = enseignements_classe[0].id if enseignements_classe else None

        notes_par_eleve = {}
        eleves_ayant_compose = []

        for eleve in eleves:
            notes = Note.query.filter_by(eleve_id=eleve.id,
                                         annee_scolaire=annee_scolaire,
                                         trimestre=trimestre).all()
            total_pondere = total_coef = 0
            for n in notes:
                note_list = [n.note1, n.note2, n.note3]
                note_valeurs = [x for x in note_list if x is not None]
                if note_valeurs or n.note_comp:
                    base_note = sum(note_valeurs)/len(note_valeurs) if note_valeurs else 0
                    val = (base_note + (n.note_comp or 0))/2
                    coef = n.coefficient or 1
                    total_pondere += val * coef
                    total_coef += coef

            moy_trim = round(total_pondere / total_coef, 2) if total_coef > 0 else 0
            notes_par_eleve[eleve.id] = moy_trim
            if total_coef > 0:
                eleves_ayant_compose.append(eleve.id)

        # Classement
        sorted_moy = sorted(notes_par_eleve.items(), key=lambda x: x[1], reverse=True)
        classement_dict = calcul_classement(sorted_moy)

        valeurs_non_nulles = [notes_par_eleve[e_id] for e_id in eleves_ayant_compose]
        moy_forte = max(valeurs_non_nulles, default=0)
        moy_faible = min(valeurs_non_nulles, default=0)
        moy_class = round((moy_forte + moy_faible)/2, 2) if valeurs_non_nulles else 0
        effectif_composants = len(valeurs_non_nulles)

        for eleve in eleves:
            moy_trim = notes_par_eleve.get(eleve.id, 0)
            appreciation = get_appreciation(moy_trim)
            moyenne_obj = Moyenne.query.filter_by(eleve_id=eleve.id,
                                                 annee_scolaire=annee_scolaire,
                                                 trimestre=trimestre).first()
            if not moyenne_obj:
                moyenne_obj = Moyenne(id=uuid.uuid4(),
                                      code=f"M-{uuid.uuid4().hex[:6]}",
                                      annee_scolaire=annee_scolaire,
                                      trimestre=trimestre,
                                      eleve_id=eleve.id,
                                      enseignement_id=default_enseignement_id,
                                      etat="Inactif")
                db.session.add(moyenne_obj)
                resume["created"] += 1
            else:
                resume["updated"] += 1

            moyenne_obj.moy_trim = moy_trim
            moyenne_obj.moy_class = moy_class
            moyenne_obj.moy_forte = moy_forte
            moyenne_obj.moy_faible = moy_faible
            moyenne_obj.eff_comp = effectif_composants
            moyenne_obj.classement = classement_dict.get(eleve.id, None)
            moyenne_obj.classement_str = format_classement(classement_dict.get(eleve.id))
            moyenne_obj.appreciation_id = appreciation.id if appreciation else None
            db.session.add(moyenne_obj)
            resume["success"].append(
                f"{eleve.nom} {eleve.prenoms} - Trim {trimestre}: moy {moy_trim}, rang {classement_dict.get(eleve.id, '—')}"
            )

        resume["total"] = len(eleves)

        # 3ème trimestre: moyenne générale et classement général
        if trimestre == 3:
            trim3_moyennes = []
            for eleve in eleves:
                trim_values = [
                    Moyenne.query.filter_by(eleve_id=eleve.id, annee_scolaire=annee_scolaire, trimestre=t).first().moy_trim
                    for t in [1,2,3]
                    if Moyenne.query.filter_by(eleve_id=eleve.id, annee_scolaire=annee_scolaire, trimestre=t).first() and
                       Moyenne.query.filter_by(eleve_id=eleve.id, annee_scolaire=annee_scolaire, trimestre=t).first().moy_trim > 0
                ]
                if trim_values:
                    m3 = Moyenne.query.filter_by(eleve_id=eleve.id, annee_scolaire=annee_scolaire, trimestre=3).first()
                    if m3:
                        m3.moy_gen = round(sum(trim_values)/len(trim_values), 2)
                        trim3_moyennes.append((eleve.id, m3.moy_gen))
                        db.session.add(m3)

            sorted_gen = sorted(trim3_moyennes, key=lambda x: x[1], reverse=True)
            classement_gen_dict = calcul_classement(sorted_gen)
            for eleve_id, _ in sorted_gen:
                m3 = Moyenne.query.filter_by(eleve_id=eleve_id, annee_scolaire=annee_scolaire, trimestre=3).first()
                if m3:
                    m3.classement_gen = classement_gen_dict[eleve_id]
                    m3.classement_gen_str = format_classement(classement_gen_dict[eleve_id])
                    db.session.add(m3)

        db.session.commit()
        print(f"[DEBUG] Batch terminé: {len(eleves)} élèves traités")
        logger.info(f"Batch terminé pour la classe {classe_id}")

    except Exception as e:
        db.session.rollback()
        resume["errors"].append(f"Erreur globale : {str(e)}")
        print(f"[ERROR] {str(e)}")
        logger.error(traceback.format_exc())

    return resume

from extensions import db
from ..models import Moyenne, Note, Eleve, Appreciations, Classe, Enseignement, SystemeEvaluation
import uuid, traceback, logging
from uuid import UUID

logger = logging.getLogger(__name__)

def format_classement(rank):
    """Formate le classement (1er, 2ème, etc.)"""
    if rank is None:
        return "—"
    if 10 <= rank % 100 <= 20:
        suffix = "ème"
    else:
        suffix = {1: "er", 2: "ème", 3: "ème"}.get(rank % 10, "ème")
    return f"{rank}{suffix}"

def calcul_classement(sorted_list):
    """Calcule le classement avec gestion des ex-aequo"""
    classement_dict = {}
    current_rank = 1
    for idx, (eleve_id, moy) in enumerate(sorted_list):
        if idx > 0 and moy == sorted_list[idx - 1][1]:
            classement_dict[eleve_id] = classement_dict[sorted_list[idx - 1][0]]
        else:
            classement_dict[eleve_id] = current_rank
        current_rank += 1
    return classement_dict

def get_appreciation_for_moyenne(moyenne, ecole_id):
    """
    Retourne l'appréciation pour une moyenne donnée - VERSION CORRIGÉE
    """
    if moyenne is None or moyenne == 0:
        return None
    
    try:
        # 1. Récupérer ou créer le système d'évaluation
        systeme_eval = SystemeEvaluation.query.filter_by(ecole_id=ecole_id).first()
        
        # Barèmes par défaut
        default_baremes = [
            {"min": 16, "max": 20, "libelle": "Très Bien", "couleur": "success"},
            {"min": 14, "max": 15.99, "libelle": "Bien", "couleur": "primary"},
            {"min": 12, "max": 13.99, "libelle": "Assez Bien", "couleur": "info"},
            {"min": 10, "max": 11.99, "libelle": "Passable", "couleur": "warning"},
            {"min": 5, "max": 9.99, "libelle": "Insuffisant", "couleur": "secondary"},
            {"min": 0, "max": 4.99, "libelle": "Très Insuffisant", "couleur": "danger"}
        ]
        
        # Créer le système s'il n'existe pas
        if not systeme_eval:
            systeme_eval = SystemeEvaluation(
                id=str(uuid.uuid4()),
                ecole_id=ecole_id,
                type_systeme='trimestriel',
                baremes_appreciations=default_baremes
            )
            db.session.add(systeme_eval)
            db.session.flush()
            logger.info(f"[INFO] Système d'évaluation créé pour l'école {ecole_id}")
        
        # Utiliser les barèmes du système ou ceux par défaut
        baremes = systeme_eval.baremes_appreciations if systeme_eval.baremes_appreciations else default_baremes
        
        # 2. Trouver le barème correspondant à la moyenne
        bareme_trouve = None
        for bareme in baremes:
            if bareme['min'] <= moyenne <= bareme['max']:
                bareme_trouve = bareme
                break
        
        if not bareme_trouve:
            logger.warning(f"[WARNING] Aucun barème trouvé pour moyenne {moyenne}")
            return None
        
        libelle = bareme_trouve['libelle']
        
        # 3. Chercher dans la table Appreciations
        appreciation = Appreciations.query.filter_by(
            ecole_id=ecole_id,
            libelle=libelle
        ).first()
        
        # 4. Si elle n'existe pas, la créer
        if not appreciation:
            appreciation = Appreciations(
                id=str(uuid.uuid4()),
                ecole_id=ecole_id,
                libelle=libelle,
                seuil_min=bareme_trouve['min'],
                seuil_max=bareme_trouve['max'],
                couleur=bareme_trouve.get('couleur', 'secondary')
            )
            db.session.add(appreciation)
            db.session.flush()
            logger.info(f"[INFO] Appréciation créée: {libelle} pour moyenne {moyenne}")
        
        return appreciation
        
    except Exception as e:
        logger.error(f"[ERROR] Erreur get_appreciation_for_moyenne: {str(e)}")
        return None

def ensure_systeme_evaluation_and_appreciations(ecole_id, type_systeme='trimestriel'):
    """S'assure que le système d'évaluation et les appréciations existent"""
    try:
        # 1. Vérifier/créer le système d'évaluation
        systeme_eval = SystemeEvaluation.query.filter_by(ecole_id=ecole_id).first()
        
        if not systeme_eval:
            systeme_eval = SystemeEvaluation(
                id=str(uuid.uuid4()),
                ecole_id=ecole_id,
                type_systeme=type_systeme,
                baremes_appreciations=[
                    {"min": 16, "max": 20, "libelle": "Très Bien", "couleur": "success"},
                    {"min": 14, "max": 15.99, "libelle": "Bien", "couleur": "primary"},
                    {"min": 12, "max": 13.99, "libelle": "Assez Bien", "couleur": "info"},
                    {"min": 10, "max": 11.99, "libelle": "Passable", "couleur": "warning"},
                    {"min": 5, "max": 9.99, "libelle": "Insuffisant", "couleur": "secondary"},
                    {"min": 0, "max": 4.99, "libelle": "Très Insuffisant", "couleur": "danger"}
                ]
            )
            db.session.add(systeme_eval)
            logger.info(f"[INFO] Système d'évaluation créé pour l'école {ecole_id}")
        else:
            # Vérifier que les barèmes existent
            if not systeme_eval.baremes_appreciations:
                systeme_eval.baremes_appreciations = [
                    {"min": 16, "max": 20, "libelle": "Très Bien", "couleur": "success"},
                    {"min": 14, "max": 15.99, "libelle": "Bien", "couleur": "primary"},
                    {"min": 12, "max": 13.99, "libelle": "Assez Bien", "couleur": "info"},
                    {"min": 10, "max": 11.99, "libelle": "Passable", "couleur": "warning"},
                    {"min": 5, "max": 9.99, "libelle": "Insuffisant", "couleur": "secondary"},
                    {"min": 0, "max": 4.99, "libelle": "Très Insuffisant", "couleur": "danger"}
                ]
        
        # Mettre à jour le type de système si nécessaire
        if systeme_eval.type_systeme != type_systeme:
            systeme_eval.type_systeme = type_systeme
            logger.info(f"[INFO] Type de système mis à jour: {type_systeme}")
        
        db.session.flush()
        
        # 2. S'assurer que les appréciations existent dans la table Appreciations
        for bareme in systeme_eval.baremes_appreciations:
            existing = Appreciations.query.filter_by(
                ecole_id=ecole_id,
                libelle=bareme['libelle']
            ).first()
            
            if not existing:
                new_app = Appreciations(
                    id=str(uuid.uuid4()),
                    ecole_id=ecole_id,
                    libelle=bareme['libelle'],
                    seuil_min=bareme['min'],
                    seuil_max=bareme['max'],
                    couleur=bareme.get('couleur', 'secondary')
                )
                db.session.add(new_app)
                logger.info(f"[INFO] Appréciation créée: {bareme['libelle']}")
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"[ERROR] Erreur dans ensure_systeme_evaluation_and_appreciations: {str(e)}")
        return False

def calculer_moyennes(classe_id, annee_scolaire, periode, ecole_id=None, type_systeme='trimestriel'):
    """
    Calcule les moyennes pour une classe - VERSION FINALE CORRIGÉE
    """
    resume = {"success": [], "errors": [], "created": 0, "updated": 0, "total": 0}
    
    try:
        logger.info(f"[INFO] Début calcul moyennes: classe={classe_id}, periode={periode}, systeme={type_systeme}")
        
        # 1. VÉRIFICATION DE SÉCURITÉ ET RÉCUPÉRATION DE LA CLASSE
        if ecole_id:
            classe = Classe.query.filter_by(id=classe_id, ecole_id=ecole_id).first()
            if not classe:
                resume["errors"].append(f"Classe non trouvée ou accès non autorisé")
                return resume
            ecole_id = classe.ecole_id
        else:
            classe = Classe.query.filter_by(id=classe_id).first()
            if not classe:
                resume["errors"].append(f"Classe non trouvée")
                return resume
            ecole_id = classe.ecole_id
        
        logger.info(f"[INFO] École: {ecole_id}, Classe: {classe.nom}")
        
        # 2. S'ASSURER QUE LE SYSTÈME D'ÉVALUATION ET LES APPRÉCIATIONS EXISTENT
        if not ensure_systeme_evaluation_and_appreciations(ecole_id, type_systeme):
            resume["errors"].append("Impossible de configurer le système d'évaluation")
            return resume
        
        # 3. RÉCUPÉRER LES ÉLÈVES
        eleves = Eleve.query.filter_by(classe_id=classe_id).all()
        if not eleves:
            resume["errors"].append(f"Aucun élève trouvé dans la classe {classe_id}")
            return resume
        
        logger.info(f"[INFO] {len(eleves)} élèves trouvés")
        
        # 4. RÉCUPÉRER LES ENSEIGNEMENTS
        enseignements_classe = Enseignement.query.filter_by(classe_id=classe_id).all()
        default_enseignement_id = enseignements_classe[0].id if enseignements_classe else None
        
        # 5. CALCUL DES MOYENNES PAR ÉLÈVE
        notes_par_eleve = {}
        eleves_ayant_compose = []
        
        for eleve in eleves:
            # Récupérer les notes de l'élève pour la période
            notes = Note.query.filter_by(
                eleve_id=eleve.id,
                annee_scolaire=annee_scolaire,
                trimestre=periode
            ).all()
            
            total_pondere = 0
            total_coef = 0
            
            for note in notes:
                # Récupérer les notes (note1, note2, note3)
                note_list = [note.note1, note.note2, note.note3]
                note_valeurs = [x for x in note_list if x is not None]
                
                if note_valeurs or note.note_comp:
                    base_note = sum(note_valeurs)/len(note_valeurs) if note_valeurs else 0
                    note_finale = (base_note + (note.note_comp or 0)) / 2
                    coef = note.coefficient or 1
                    
                    total_pondere += note_finale * coef
                    total_coef += coef
            
            # Calcul de la moyenne
            moy_periode = round(total_pondere / total_coef, 2) if total_coef > 0 else 0.0
            notes_par_eleve[eleve.id] = moy_periode
            
            if total_coef > 0:
                eleves_ayant_compose.append(eleve.id)
        
        logger.info(f"[INFO] {len(eleves_ayant_compose)}/{len(eleves)} élèves ont composé")
        
        # 6. CALCUL DU CLASSEMENT
        if eleves_ayant_compose:
            moyennes_a_classer = {eid: moy for eid, moy in notes_par_eleve.items() if eid in eleves_ayant_compose}
            sorted_moy = sorted(moyennes_a_classer.items(), key=lambda x: x[1], reverse=True)
            classement_dict = calcul_classement(sorted_moy)
        else:
            classement_dict = {}
        
        # 7. CALCUL DES STATISTIQUES DE LA CLASSE
        valeurs_non_nulles = [notes_par_eleve[e_id] for e_id in eleves_ayant_compose if notes_par_eleve[e_id] > 0]
        
        if valeurs_non_nulles:
            moy_forte = max(valeurs_non_nulles)
            moy_faible = min(valeurs_non_nulles)
            moy_class = round((moy_forte + moy_faible) / 2, 2)
            effectif_composants = len(valeurs_non_nulles)
        else:
            moy_forte = 0.0
            moy_faible = 0.0
            moy_class = 0.0
            effectif_composants = 0
        
        logger.info(f"[INFO] Statistiques: moy_class={moy_class}, moy_forte={moy_forte}, moy_faible={moy_faible}")
        
        # 8. TRAITEMENT DE CHAQUE ÉLÈVE
        for eleve in eleves:
            moy_periode = notes_par_eleve.get(eleve.id, 0.0)
            
            # Récupérer l'appréciation
            appreciation_id = None
            if moy_periode > 0:
                appreciation = get_appreciation_for_moyenne(moy_periode, ecole_id)
                if appreciation:
                    appreciation_id = appreciation.id
                    logger.debug(f"[DEBUG] Appréciation trouvée pour {eleve.nom} (moy={moy_periode}): {appreciation.libelle}")
                else:
                    logger.warning(f"[WARNING] Pas d'appréciation pour {eleve.nom} (moyenne: {moy_periode})")
            
            # Si élève n'a pas composé, on ne crée pas de moyenne
            if eleve.id not in eleves_ayant_compose:
                moyenne_obj = Moyenne.query.filter_by(
                    eleve_id=eleve.id,
                    annee_scolaire=annee_scolaire,
                    periode=periode
                ).first()
                
                if moyenne_obj:
                    db.session.delete(moyenne_obj)
                    logger.info(f"[INFO] Suppression moyenne pour {eleve.nom} (n'a pas composé)")
                continue
            
            # RECHERCHE DE LA MOYENNE EXISTANTE
            moyenne_obj = Moyenne.query.filter_by(
                eleve_id=eleve.id,
                annee_scolaire=annee_scolaire,
                periode=periode
            ).first()
            
            classement_eleve = classement_dict.get(eleve.id, 0)
            classement_str = format_classement(classement_eleve)
            
            # CRÉATION OU MISE À JOUR
            if not moyenne_obj:
                moyenne_obj = Moyenne(
                    id=str(uuid.uuid4()),
                    code=f"M-{uuid.uuid4().hex[:6]}",
                    annee_scolaire=annee_scolaire,
                    periode=periode,
                    type_periode='semestre' if type_systeme == 'semestriel' else 'trimestre',
                    eleve_id=eleve.id,
                    enseignement_id=default_enseignement_id,
                    ecole_id=ecole_id,
                    moy_periode=moy_periode,
                    moy_trim=moy_periode,
                    moy_mat=moy_periode,
                    moy_class=moy_class,
                    moy_faible=moy_faible,
                    moy_forte=moy_forte,
                    classement=classement_eleve,
                    classement_str=classement_str,
                    eff_comp=effectif_composants,
                    appreciation_id=appreciation_id,
                    etat="Actif"
                )
                db.session.add(moyenne_obj)
                resume["created"] += 1
                logger.info(f"[INFO] Créé: {eleve.nom} {eleve.prenoms} - moy: {moy_periode}")
            else:
                moyenne_obj.moy_periode = moy_periode
                moyenne_obj.moy_trim = moy_periode
                moyenne_obj.moy_mat = moy_periode
                moyenne_obj.moy_class = moy_class
                moyenne_obj.moy_faible = moy_faible
                moyenne_obj.moy_forte = moy_forte
                moyenne_obj.classement = classement_eleve
                moyenne_obj.classement_str = classement_str
                moyenne_obj.eff_comp = effectif_composants
                moyenne_obj.appreciation_id = appreciation_id
                moyenne_obj.etat = "Actif"
                resume["updated"] += 1
                logger.info(f"[INFO] Mis à jour: {eleve.nom} {eleve.prenoms} - moy: {moy_periode}")
            
            resume["success"].append(
                f"{eleve.nom} {eleve.prenoms} - {type_systeme.capitalize()} {periode}: moy {moy_periode:.2f}, rang {classement_str}"
            )
        
        resume["total"] = len([e for e in eleves if e.id in eleves_ayant_compose])
        
        # 9. SAUVEGARDE
        try:
            db.session.commit()
            logger.info(f"[SUCCESS] Batch terminé: {resume['created']} créés, {resume['updated']} mis à jour")
        except Exception as commit_error:
            db.session.rollback()
            error_msg = str(commit_error)
            logger.error(f"[ERROR] Erreur commit: {error_msg}")
            resume["errors"].append(f"Erreur sauvegarde: {error_msg}")
    
    except Exception as e:
        db.session.rollback()
        error_message = f"Erreur globale: {str(e)}"
        resume["errors"].append(error_message)
        logger.error(f"[CRITICAL] Erreur globale: {error_message}")
        logger.error(traceback.format_exc())
    
    return resume
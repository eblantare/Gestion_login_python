from flask import Blueprint, request, jsonify, send_file, render_template
from ..models import Moyenne, Eleve, Classe, Matiere, Enseignant, Enseignement, Ecole, Appreciations, Note
from extensions import db
from sqlalchemy.orm import joinedload
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
from uuid import UUID
from collections import namedtuple
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_login import login_required, current_user

bulletins_export_bp = Blueprint('bulletins_export', __name__)

# ==================== FONCTIONS DE CALCUL CORRIGÉES ====================

def calculer_moyenne_notes_eleve_matiere(note_obj):
    """Calcule la moyenne des notes 1, 2, 3 pour un élève dans une matière - REMPLACE M.CL"""
    notes_valides = []
    
    if note_obj.note1 is not None and note_obj.note1 >= 0:
        notes_valides.append(note_obj.note1)
    if note_obj.note2 is not None and note_obj.note2 >= 0:
        notes_valides.append(note_obj.note2)
    if note_obj.note3 is not None and note_obj.note3 >= 0:
        notes_valides.append(note_obj.note3)
    
    if not notes_valides:
        return 0.0
    
    moyenne = sum(notes_valides) / len(notes_valides)
    return arrondir_moyenne_specifique(moyenne)

def calculer_moyenne_matiere(moyenne_notes, note_comp):
    """Moyenne matière (M.MAT) = (moyenne_notes + Note_comp)/2"""
    # Si pas de note de composition, retourner seulement la moyenne_notes
    if note_comp is None or note_comp < 0:
        return arrondir_moyenne_specifique(moyenne_notes)
    
    # Calculer la moyenne matière
    moyenne_matiere = (moyenne_notes + note_comp) / 2
    return arrondir_moyenne_specifique(moyenne_matiere)

def calculer_moyenne_classe_par_matiere(matiere_id, classe_id, trimestre, annee_scolaire):
    """Calcule la moyenne statistique de la classe pour une matière"""
    # Récupérer toutes les notes de la matière dans la classe
    notes_classe = Note.query.filter_by(
        matiere_id=matiere_id,
        trimestre=trimestre,
        annee_scolaire=annee_scolaire
    ).filter(
        Note.eleve.has(classe_id=classe_id)
    ).all()
    
    if not notes_classe:
        return 0.0
    
    # Calculer les moyennes_notes de chaque élève (M.CL individuelles)
    moyennes_eleves = []
    
    for note in notes_classe:
        moyenne_eleve = calculer_moyenne_notes_eleve_matiere(note)
        if moyenne_eleve > 0:  # Ne prendre que les élèves avec des notes valides
            moyennes_eleves.append(moyenne_eleve)
    
    if not moyennes_eleves:
        return 0.0
    
    # La moyenne_classe est la moyenne statistique de toutes les moyennes_notes
    moyenne_classe = sum(moyennes_eleves) / len(moyennes_eleves)
    return arrondir_moyenne_specifique(moyenne_classe)

def calculer_moyenne_ponderee(moyenne_matiere, coefficient):
    """Moy_coef (M.Coef) = Moy_Mat × coef"""
    return moyenne_matiere * coefficient

def arrondir_moyenne_metier(valeur):
    """Arrondi selon la règle métier : 
    - Inférieur à 0.05 → arrondi par défaut
    - Supérieur ou égal à 0.05 → arrondi par excès
    Exemple : 14.04 → 14.0, 14.05 → 14.1
    """
    if valeur is None or valeur == 0:
        return 0.0
    
    # Séparer partie entière et décimale
    partie_entiere = int(valeur)
    partie_decimale = valeur - partie_entiere
    
    # Appliquer la règle métier
    if partie_decimale < 0.05:
        # Arrondi par défaut
        return partie_entiere + round(partie_decimale, 1)
    else:
        # Arrondi par excès
        return partie_entiere + round(partie_decimale + 0.05, 1)

# Remplacer l'ancienne fonction pour uniformiser
def arrondir_moyenne_specifique(valeur):
    """Utilise maintenant l'arrondi métier uniformisé"""
    return arrondir_moyenne_metier(valeur)

# ==================== FONCTION get_eleve_data CORRIGÉE (CALCULS STATISTIQUES CORRIGÉS) ====================

def get_eleve_data(eleve_id, trimestre, annee_scolaire):
    """Récupère toutes les données nécessaires pour un élève donné - VERSION CORRIGÉE"""
    
    eleve = Eleve.query.options(joinedload(Eleve.classe)).filter_by(id=eleve_id).first()
    if not eleve:
        return None
    
    # Récupérer la moyenne depuis la table Moyenne
    moyenne_eleve_db = Moyenne.query.filter_by(
        eleve_id=eleve_id,
        trimestre=trimestre,
        annee_scolaire=annee_scolaire
    ).first()
    
    # Récupérer TOUTES les notes de l'élève (uniquement celles qui existent)
    notes = Note.query.filter_by(
        eleve_id=eleve_id,
        trimestre=trimestre,
        annee_scolaire=annee_scolaire
    ).options(
        joinedload(Note.matiere),
        joinedload(Note.enseignement).joinedload(Enseignement.enseignant).joinedload(Enseignant.utilisateur)
    ).all()

    # On utilise uniquement les notes qui existent réellement
    notes_completes = notes

    # Calculer les moyennes pour chaque note AVEC LA NOUVELLE LOGIQUE
    notes_calculees = []
    for note in notes_completes:
        # 1. Calculer moyenne_notes (remplace M.CL) - moyenne des notes 1,2,3 de l'élève
        moyenne_notes = calculer_moyenne_notes_eleve_matiere(note)
        
        # 2. Calculer moyenne_classe (statistique de la classe)
        moyenne_classe = calculer_moyenne_classe_par_matiere(
            note.matiere_id, eleve.classe_id, trimestre, annee_scolaire
        )
        
        # 3. Calculer moyenne matière (M.MAT)
        moy_matiere = calculer_moyenne_matiere(moyenne_notes, getattr(note, 'note_comp', 0))
        
        # 4. Calculer moyenne pondérée
        coefficient = getattr(note, 'coefficient', 0) or 0
        moy_ponderee = calculer_moyenne_ponderee(moy_matiere, coefficient)
        
        # Déterminer si la matière a des notes valides
        has_notes_valides = (moyenne_notes > 0 or (getattr(note, 'note_comp', 0) and getattr(note, 'note_comp', 0) > 0))
        
        notes_calculees.append({
            'note_obj': note,
            'moyenne_notes': moyenne_notes,  # REMPLACE M.CL
            'moyenne_classe': moyenne_classe,
            'moyenne_matiere': moy_matiere,  # M.MAT
            'moyenne_ponderee': moy_ponderee,  # M.Coef
            'coefficient': coefficient if has_notes_valides else 0,
            'has_notes_valides': has_notes_valides
        })
    
    # Organisation par catégorie
    matieres_litteraires = []
    matieres_scientifiques = []
    matieres_specialisees = []
    
    # Calcul des moyennes par matière pour la classe
    moyennes_par_matiere = {}
    for note_calc in notes_calculees:
        note = note_calc['note_obj']
        matiere_id = note.matiere_id
        
        # Calculer la moyenne de classe pour cette matière
        notes_matiere_classe = Note.query.filter_by(
            matiere_id=matiere_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire
        ).filter(
            Note.eleve.has(classe_id=eleve.classe_id)
        ).all()
        
        if notes_matiere_classe:
            moyennes_calculees_matiere = []
            for note_classe in notes_matiere_classe:
                moy_notes_eleve = calculer_moyenne_notes_eleve_matiere(note_classe)
                moy_matiere_eleve = calculer_moyenne_matiere(moy_notes_eleve, note_classe.note_comp)
                if moy_matiere_eleve > 0:
                    moyennes_calculees_matiere.append(moy_matiere_eleve)
            
            if moyennes_calculees_matiere:
                moyennes_par_matiere[matiere_id] = round(sum(moyennes_calculees_matiere) / len(moyennes_calculees_matiere), 2)
            else:
                moyennes_par_matiere[matiere_id] = 0
        else:
            moyennes_par_matiere[matiere_id] = 0
    
    # Calcul des classements par matière
    classements_par_matiere = {}
    for matiere in set([n['note_obj'].matiere_id for n in notes_calculees]):
        # Récupérer toutes les M.MAT de la matière pour le classement
        moyennes_eleves_matiere = []
        for eleve_classe in Eleve.query.filter_by(classe_id=eleve.classe_id).all():
            note_eleve = Note.query.filter_by(
                eleve_id=eleve_classe.id,
                matiere_id=matiere,
                trimestre=trimestre,
                annee_scolaire=annee_scolaire
            ).first()
            
            if note_eleve:
                moy_notes_eleve = calculer_moyenne_notes_eleve_matiere(note_eleve)
                moy_matiere_eleve = calculer_moyenne_matiere(moy_notes_eleve, note_eleve.note_comp)
                if moy_matiere_eleve > 0:
                    moyennes_eleves_matiere.append({
                        'eleve_id': eleve_classe.id,
                        'moy_matiere': moy_matiere_eleve
                    })
        
        if moyennes_eleves_matiere:
            # Trier par M.MAT décroissante
            moyennes_triees = sorted(moyennes_eleves_matiere, key=lambda x: x['moy_matiere'], reverse=True)
            
            # Calculer les rangs avec gestion des ex-aequo
            current_rank = 1
            previous_moyenne = None
            
            for idx, eleve_data in enumerate(moyennes_triees):
                current_moyenne = eleve_data['moy_matiere']
                
                if previous_moyenne is not None and abs(current_moyenne - previous_moyenne) > 0.001:
                    current_rank = idx + 1
                
                if eleve_data['eleve_id'] == eleve_id:
                    classements_par_matiere[matiere] = current_rank
                    break
                
                previous_moyenne = current_moyenne
    
    # Totaux par catégorie - AVEC LA NOUVELLE LOGIQUE
    total_coeff_litteraire = total_moy_coef_litteraire = 0
    total_coeff_scientifique = total_moy_coef_scientifique = 0
    total_coeff_specialise = total_moy_coef_specialise = 0
    
    for note_calc in notes_calculees:
        note = note_calc['note_obj']
        moyenne_notes = note_calc['moyenne_notes']  # M.CL remplacé par moyenne_notes
        moyenne_classe = note_calc['moyenne_classe']
        moyenne_matiere = note_calc['moyenne_matiere']  # M.MAT
        coefficient = note_calc['coefficient']
        moyenne_ponderee = note_calc['moyenne_ponderee']  # M.Coef
        
        moy_clas = moyennes_par_matiere.get(note.matiere_id, 0)
        rang = classements_par_matiere.get(note.matiere_id, '-')
        
        # Afficher la vraie note_comp
        vraie_note_comp = getattr(note, 'note_comp', 0) or 0
        
        matiere_data = {
            'libelle': note.matiere.libelle,
            'moyenne_notes': round(moyenne_notes, 2),  # REMPLACE moy_clas
            'note_comp': round(vraie_note_comp, 2),
            'moy_mat': round(moyenne_matiere, 2),
            'coefficient': coefficient,
            'moy_coef': round(moyenne_ponderee, 2),
            'rang': rang,
            'observation': getattr(note, 'observation', ''),
            'enseignant': note.enseignement.enseignant.utilisateur.nom if note.enseignement and note.enseignement.enseignant else 'Non assigné',
            'signature': ''
        }

        moy_mat_val = matiere_data['moy_mat']
        coefficient_val = matiere_data['coefficient']
        
        # Classification basée sur les types
        matiere_type = note.matiere.type or 'Autres'
        libelle_lower = note.matiere.libelle.lower()

        # Classification spécifique
        if 'education physique' in libelle_lower or 'eps' in libelle_lower or 'sport' in libelle_lower:
            matieres_specialisees.append(matiere_data)
            if coefficient_val > 0:
                total_coeff_specialise += coefficient_val
                total_moy_coef_specialise += moy_mat_val * coefficient_val
        elif 'education civique' in libelle_lower or 'civique' in libelle_lower or 'morale' in libelle_lower:
            matieres_litteraires.append(matiere_data)
            if coefficient_val > 0:
                total_coeff_litteraire += coefficient_val
                total_moy_coef_litteraire += moy_mat_val * coefficient_val
        elif 'scientifique' in matiere_type.lower():
            matieres_scientifiques.append(matiere_data)
            if coefficient_val > 0:
                total_coeff_scientifique += coefficient_val
                total_moy_coef_scientifique += moy_mat_val * coefficient_val
        elif 'littéraire' in matiere_type.lower():
            matieres_litteraires.append(matiere_data)
            if coefficient_val > 0:
                total_coeff_litteraire += coefficient_val
                total_moy_coef_litteraire += moy_mat_val * coefficient_val
        else:
            matieres_specialisees.append(matiere_data)
            if coefficient_val > 0:
                total_coeff_specialise += coefficient_val
                total_moy_coef_specialise += moy_mat_val * coefficient_val
    
    # Calcul des moyennes par catégorie
    moyenne_litteraire = total_moy_coef_litteraire / total_coeff_litteraire if total_coeff_litteraire > 0 else 0
    moyenne_scientifique = total_moy_coef_scientifique / total_coeff_scientifique if total_coeff_scientifique > 0 else 0
    moyenne_specialise = total_moy_coef_specialise / total_coeff_specialise if total_coeff_specialise > 0 else 0
    
    moyenne_litteraire = max(0, round(moyenne_litteraire, 2))
    moyenne_scientifique = max(0, round(moyenne_scientifique, 2))
    moyenne_specialise = max(0, round(moyenne_specialise, 2))

    # ==================== CALCUL DE LA MOYENNE GÉNÉRALE CORRIGÉ ====================
    # Moy_trim = (somme des moy_coef) / (somme des coef)
    total_coeff = total_coeff_litteraire + total_coeff_scientifique + total_coeff_specialise
    total_moy_coef = total_moy_coef_litteraire + total_moy_coef_scientifique + total_moy_coef_specialise
    moyenne_generale = total_moy_coef / total_coeff if total_coeff > 0 else 0
    
    # ==================== CALCUL DES STATISTIQUES DE CLASSE CORRIGÉ ====================
    tous_eleves_classe = Eleve.query.filter_by(classe_id=eleve.classe_id).all()
    moyennes_eleves_classe = []
    
    for eleve_classe in tous_eleves_classe:
        # Essayer d'abord de récupérer la moyenne depuis la table Moyenne
        moyenne_db = Moyenne.query.filter_by(
            eleve_id=eleve_classe.id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire
        ).first()
        
        if moyenne_db and moyenne_db.moy_trim and moyenne_db.moy_trim > 0:
            moyennes_eleves_classe.append(moyenne_db.moy_trim)
        else:
            # Sinon calculer la moyenne à partir des notes
            notes_eleve = Note.query.filter_by(
                eleve_id=eleve_classe.id,
                trimestre=trimestre,
                annee_scolaire=annee_scolaire
            ).all()
            
            if notes_eleve:
                total_coeff_eleve = 0
                total_moy_coef_eleve = 0
                
                for note_eleve in notes_eleve:
                    moy_notes_eleve = calculer_moyenne_notes_eleve_matiere(note_eleve)
                    moy_matiere_eleve = calculer_moyenne_matiere(moy_notes_eleve, note_eleve.note_comp)
                    coefficient_eleve = note_eleve.coefficient or 1
                    
                    if coefficient_eleve > 0 and (moy_notes_eleve > 0 or (note_eleve.note_comp and note_eleve.note_comp > 0)):
                        total_coeff_eleve += coefficient_eleve
                        total_moy_coef_eleve += moy_matiere_eleve * coefficient_eleve
                
                if total_coeff_eleve > 0:
                    moyenne_eleve_calculee = total_moy_coef_eleve / total_coeff_eleve
                    moyennes_eleves_classe.append(moyenne_eleve_calculee)
    
    # CORRECTION : Calcul des statistiques selon les nouvelles règles
    if moyennes_eleves_classe:
        # 2. Moy_faible = plus petite moyenne supérieure à 0
        moy_faible = min([m for m in moyennes_eleves_classe if m > 0])
        
        # 3. Moy_forte = plus grande moyenne
        moy_forte = max(moyennes_eleves_classe)
        
        # 4. Moy_classe = (moy_faible + moy_forte) / 2
        moy_class = (moy_faible + moy_forte) / 2
        
        # 5. Effectif = nombre d'élèves ayant une moyenne
        effectif_composant = len(moyennes_eleves_classe)
    else:
        moy_forte = 0
        moy_faible = 0
        moy_class = 0
        effectif_composant = 0

    StatsClasse = namedtuple('StatsClasse', ['moy_forte', 'moy_faible', 'moy_class', 'effectif_composant'])
    stats_classe = StatsClasse(
        moy_forte=round(moy_forte, 2),
        moy_faible=round(moy_faible, 2),
        moy_class=round(moy_class, 2),
        effectif_composant=effectif_composant
    )

    # Préparation des données pour les rangs
    eleve_moyennes_data = {
        'moyenne_litteraire': moyenne_litteraire,
        'moyenne_scientifique': moyenne_scientifique,
        'moyenne_specialise': moyenne_specialise,
        'moyenne_generale': moyenne_generale
    }

    # Rangs par catégorie
    rangs_categories = calculer_rangs_categories(
        eleve_moyennes_data, 
        eleve.classe_id, 
        trimestre, 
        annee_scolaire, 
        eleve_id
    )
   
    # Rang général
    rang_general = calculer_rang_simple_ameliore(
        eleve_id,
        eleve.classe_id,
        trimestre,
        annee_scolaire,
        moyenne_generale
    )
    
    # Utiliser la moyenne de la base si elle existe, sinon utiliser la moyenne calculée
    if moyenne_eleve_db and moyenne_eleve_db.moy_trim and moyenne_eleve_db.moy_trim > 0:
        moyenne_generale_finale = moyenne_eleve_db.moy_trim
    else:
        moyenne_generale_finale = moyenne_generale

    return {
        'eleve': eleve,
        'moyenne_eleve': moyenne_eleve_db,
        'matieres_litteraires': matieres_litteraires,
        'matieres_scientifiques': matieres_scientifiques,
        'matieres_specialisees': matieres_specialisees,
        'stats_classe': stats_classe,
        'total_coeff': total_coeff,
        'total_moy_coef': round(total_moy_coef, 2),
        'moyenne_generale': round(moyenne_generale_finale, 2),
        'rang_general': rang_general,
        'moyenne_litteraire': round(moyenne_litteraire, 2),
        'moyenne_scientifique': round(moyenne_scientifique, 2),
        'moyenne_specialise': round(moyenne_specialise, 2),
        'rangs_categories': rangs_categories,
        'notes': notes
    }


def get_observation_for_trimestre(moyenne_generale):
    """Retourne l'observation pour la moyenne trimestrielle générale"""
    if moyenne_generale >= 16:
        return "Excellent travail"
    elif moyenne_generale >= 14:
        return "Très Bon travail"
    elif moyenne_generale >= 12:
        return "Bon travail"
    elif moyenne_generale >= 10:
        return "Travail Passable"
    elif moyenne_generale >= 8:
        return "Avertissement"
    else:
        return "Faible Travail"

# ==================== FONCTION calculer_statistiques_classe CORRIGÉE ====================

def calculer_statistiques_classe(moyennes_eleves):
    """Calcul des statistiques de classe - VERSION CORRIGÉE"""
    if not moyennes_eleves:
        return {
            'moy_faible': 0,
            'moy_forte': 0,
            'moy_classe': 0,
            'effectif_composant': 0
        }
    
    # Filtrer les moyennes supérieures à 0
    moyennes_positives = [moy for moy in moyennes_eleves if moy > 0]
    
    if not moyennes_positives:
        return {
            'moy_faible': 0,
            'moy_forte': 0,
            'moy_classe': 0,
            'effectif_composant': 0
        }
    
    # 2. Moy_faible = plus petite moyenne supérieure à 0
    moy_faible = min(moyennes_positives)
    
    # 3. Moy_forte = plus grande moyenne
    moy_forte = max(moyennes_eleves)
    
    # 4. Moy_classe = (moy_faible + moy_forte) / 2
    moy_classe = (moy_faible + moy_forte) / 2
    
    # 5. Effectif = nombre d'élèves ayant une moyenne
    effectif_composant = len(moyennes_positives)
    
    return {
        'moy_faible': round(moy_faible, 2),
        'moy_forte': round(moy_forte, 2),
        'moy_classe': round(moy_classe, 2),
        'effectif_composant': effectif_composant
    }

# ==================== FONCTION calculer_moyenne_trimestre CORRIGÉE ====================

def calculer_moyenne_trimestre(moyennes_par_type):
    """Moy_trim = (somme des moyenne_coef) / (somme des coef) - VERSION CORRIGÉE"""
    somme_ponderee_totale = 0
    total_coef_totaux = 0
    
    # CORRECTION : On utilise les bonnes clés
    for type_name, type_key in [('littéraire', 'litteraire'), ('scientifique', 'scientifique'), ('spécialisée', 'specialisee')]:
        moyenne_type = moyennes_par_type.get(f'moyenne_{type_key}', 0)
        total_coef_type = moyennes_par_type.get(f'total_coef_{type_key}', 0)
        
        somme_ponderee_totale += moyenne_type * total_coef_type
        total_coef_totaux += total_coef_type
    
    return somme_ponderee_totale / total_coef_totaux if total_coef_totaux > 0 else 0.0

# ==================== FONCTION get_moyennes_par_trimestre CORRIGÉE ====================

# ==================== REMPLACEZ LA FONCTION get_moyennes_par_trimestre DÉFAILLANTE ====================

def get_moyennes_par_trimestre(eleve_id, annee_scolaire):
    """Récupère les moyennes de l'élève pour tous les trimestres - VERSION ROBUSTE"""
    moyennes_trimestres = {}
    
    for trim in [1, 2, 3]:
        # Essayer d'abord de récupérer depuis la table Moyenne
        moyenne_data = Moyenne.query.filter_by(
            eleve_id=eleve_id,
            trimestre=trim,
            annee_scolaire=annee_scolaire
        ).first()
        
        if moyenne_data and moyenne_data.moy_trim is not None:
            eleve = Eleve.query.get(eleve_id)
            if eleve:
                # Calculer l'effectif total de la classe
                effectif_total = Eleve.query.filter_by(classe_id=eleve.classe_id).count()
                
                # Calculer le rang
                rang = calculer_rang_simple_ameliore(
                    eleve_id, 
                    eleve.classe_id, 
                    trim, 
                    annee_scolaire, 
                    moyenne_data.moy_trim
                )
                
                moyennes_trimestres[trim] = {
                    'moyenne': round(moyenne_data.moy_trim, 2),
                    'rang': rang,
                    'effectif_composant': effectif_total
                }
            else:
                moyennes_trimestres[trim] = {
                    'moyenne': round(moyenne_data.moy_trim, 2) if moyenne_data.moy_trim else 0,
                    'rang': 'N/A',
                    'effectif_composant': 0
                }
        else:
            # Si pas de moyenne en base, essayer de calculer à partir des notes
            eleve = Eleve.query.get(eleve_id)
            if eleve:
                notes_eleve = Note.query.filter_by(
                    eleve_id=eleve_id,
                    trimestre=trim,
                    annee_scolaire=annee_scolaire
                ).all()
                
                if notes_eleve:
                    # Calculer la moyenne à partir des notes
                    total_coeff = 0
                    total_moy_coef = 0
                    has_notes_valides = False
                    
                    for note in notes_eleve:
                        moy_notes = calculer_moyenne_notes_eleve_matiere(note)
                        moy_matiere = calculer_moyenne_matiere(moy_notes, note.note_comp)
                        coefficient = note.coefficient or 1
                        
                        if coefficient > 0 and (moy_notes > 0 or (note.note_comp and note.note_comp > 0)):
                            total_coeff += coefficient
                            total_moy_coef += moy_matiere * coefficient
                            has_notes_valides = True
                    
                    if has_notes_valides and total_coeff > 0:
                        moyenne_calculee = total_moy_coef / total_coeff
                        effectif_total = Eleve.query.filter_by(classe_id=eleve.classe_id).count()
                        rang = calculer_rang_simple_ameliore(
                            eleve_id, 
                            eleve.classe_id, 
                            trim, 
                            annee_scolaire, 
                            moyenne_calculee
                        )
                        
                        moyennes_trimestres[trim] = {
                            'moyenne': round(moyenne_calculee, 2),
                            'rang': rang,
                            'effectif_composant': effectif_total
                        }
                    else:
                        moyennes_trimestres[trim] = {
                            'moyenne': 0, 
                            'rang': 'N/A', 
                            'effectif_composant': 0
                        }
                else:
                    moyennes_trimestres[trim] = {
                        'moyenne': 0, 
                        'rang': 'N/A', 
                        'effectif_composant': 0
                    }
            else:
                moyennes_trimestres[trim] = {
                    'moyenne': 0, 
                    'rang': 'N/A', 
                    'effectif_composant': 0
                }
    
    return moyennes_trimestres

# ==================== AJOUTEZ UNE FONCTION DE FALLBACK POUR LES MOYENNES MANQUANTES ====================

def get_moyennes_avec_fallback(eleve_id, trimestre_courant, annee_scolaire):
    """Version robuste avec fallback pour éviter les colonnes MOYENNES vides"""
    moyennes_trimestres = get_moyennes_par_trimestre(eleve_id, annee_scolaire)
    
    # Vérifier si le trimestre courant a des données
    if trimestre_courant in moyennes_trimestres and moyennes_trimestres[trimestre_courant]['moyenne'] > 0:
        return moyennes_trimestres
    
    # Si le trimestre courant n'a pas de données, essayer de calculer à partir des notes actuelles
    eleve = Eleve.query.get(eleve_id)
    if eleve:
        notes_actuelles = Note.query.filter_by(
            eleve_id=eleve_id,
            trimestre=trimestre_courant,
            annee_scolaire=annee_scolaire
        ).all()
        
        if notes_actuelles:
            total_coeff = 0
            total_moy_coef = 0
            has_notes_valides = False
            
            for note in notes_actuelles:
                moy_notes = calculer_moyenne_notes_eleve_matiere(note)
                moy_matiere = calculer_moyenne_matiere(moy_notes, note.note_comp)
                coefficient = note.coefficient or 1
                
                if coefficient > 0 and (moy_notes > 0 or (note.note_comp and note.note_comp > 0)):
                    total_coeff += coefficient
                    total_moy_coef += moy_matiere * coefficient
                    has_notes_valides = True
            
            if has_notes_valides and total_coeff > 0:
                moyenne_calculee = total_moy_coef / total_coeff
                effectif_total = Eleve.query.filter_by(classe_id=eleve.classe_id).count()
                rang = calculer_rang_simple_ameliore(
                    eleve_id, 
                    eleve.classe_id, 
                    trimestre_courant, 
                    annee_scolaire, 
                    moyenne_calculee
                )
                
                moyennes_trimestres[trimestre_courant] = {
                    'moyenne': round(moyenne_calculee, 2),
                    'rang': rang,
                    'effectif_composant': effectif_total
                }
    
    return moyennes_trimestres

# ==================== FONCTION calculer_rang_simple_ameliore (inchangée) ====================

def calculer_rang_simple_ameliore(eleve_id, classe_id, trimestre, annee_scolaire, moyenne_eleve):
    """Calcule le rang avec gestion CORRECTE des ex-aequo - VERSION DÉFINITIVE CORRIGÉE"""
    try:
        print(f"🔍 Calcul rang amélioré - Élève: {eleve_id}, Classe: {classe_id}, Trim: {trimestre}, Moyenne: {moyenne_eleve}")
        
        # Récupérer tous les élèves de la classe avec leurs moyennes
        eleves_classe = Eleve.query.filter_by(classe_id=classe_id).all()
        donnees_moyennes = []
        
        for eleve_classe in eleves_classe:
            # Essayer d'abord la table Moyenne
            moyenne_db = Moyenne.query.filter_by(
                eleve_id=eleve_classe.id,
                trimestre=trimestre,
                annee_scolaire=annee_scolaire
            ).first()
            
            if moyenne_db and moyenne_db.moy_trim and moyenne_db.moy_trim > 0:
                donnees_moyennes.append({
                    'eleve_id': eleve_classe.id,
                    'moyenne': moyenne_db.moy_trim,
                    'nom': f"{eleve_classe.nom} {eleve_classe.prenoms}"
                })
            else:
                # Calculer à partir des notes si pas en base
                notes_eleve = Note.query.filter_by(
                    eleve_id=eleve_classe.id,
                    trimestre=trimestre,
                    annee_scolaire=annee_scolaire
                ).all()
                
                if notes_eleve:
                    total_coeff = 0
                    total_moy_coef = 0
                    has_notes_valides = False
                    
                    for note in notes_eleve:
                        moy_notes = calculer_moyenne_notes_eleve_matiere(note)
                        moy_matiere = calculer_moyenne_matiere(moy_notes, note.note_comp)
                        coefficient = note.coefficient or 1
                        
                        if coefficient > 0 and (moy_notes > 0 or (note.note_comp and note.note_comp > 0)):
                            total_coeff += coefficient
                            total_moy_coef += moy_matiere * coefficient
                            has_notes_valides = True
                    
                    if has_notes_valides and total_coeff > 0:
                        moyenne_calculee = total_moy_coef / total_coeff
                        donnees_moyennes.append({
                            'eleve_id': eleve_classe.id,
                            'moyenne': moyenne_calculee,
                            'nom': f"{eleve_classe.nom} {eleve_classe.prenoms}"
                        })
        
        # S'assurer que l'élève courant est inclus
        eleve_courant_trouve = any(d['eleve_id'] == eleve_id for d in donnees_moyennes)
        if not eleve_courant_trouve and moyenne_eleve > 0:
            eleve_courant = Eleve.query.get(eleve_id)
            donnees_moyennes.append({
                'eleve_id': eleve_id,
                'moyenne': moyenne_eleve,
                'nom': f"{eleve_courant.nom} {eleve_courant.prenoms}" if eleve_courant else "Élève courant"
            })
        
        if not donnees_moyennes:
            print("❌ Aucune moyenne valide dans la classe")
            return 'N/A'
        
        # Trier par moyenne décroissante
        donnees_moyennes.sort(key=lambda x: x['moyenne'], reverse=True)
        
        print("📊 Moyennes de la classe (triées):")
        for i, data in enumerate(donnees_moyennes):
            print(f"   {i+1}. {data['nom']}: {data['moyenne']:.2f}")
        
        # NOUVELLE LOGIQUE DE RANG AVEC EX-AEQUO CORRIGÉE
        rangs_final = []
        current_rank = 1
        previous_moyenne = None
        count_same_rank = 1
        
        for i, data in enumerate(donnees_moyennes):
            current_moyenne = data['moyenne']
            
            if previous_moyenne is not None:
                # Vérifier si même moyenne que le précédent (avec tolérance)
                if abs(current_moyenne - previous_moyenne) <= 0.009:  # Tolérance de 0.01
                    # Même rang que le précédent (ex-aequo)
                    rang_attribue = current_rank
                    count_same_rank += 1
                else:
                    # Moyenne différente, nouveau rang
                    current_rank = i + 1
                    rang_attribue = current_rank
                    count_same_rank = 1
            else:
                # Premier élément
                rang_attribue = 1
                count_same_rank = 1
            
            rangs_final.append({
                'eleve_id': data['eleve_id'],
                'moyenne': current_moyenne,
                'rang': rang_attribue,
                'nom': data['nom']
            })
            
            previous_moyenne = current_moyenne
        
        # Afficher les rangs pour debug
        print("🎯 Rangs calculés (VERSION DÉFINITIVE CORRIGÉE):")
        for rang_data in rangs_final:
            print(f"   {rang_data['nom']}: Moyenne {rang_data['moyenne']:.2f} → Rang {rang_data['rang']}")
        
        # Trouver le rang de l'élève courant
        for rang_data in rangs_final:
            if rang_data['eleve_id'] == eleve_id:
                rang_final = rang_data['rang']
                print(f"✅ Rang final trouvé: {rang_final}")
                return rang_final
        
        print("❌ Élève courant non trouvé dans le classement")
        return 'N/A'
            
    except Exception as e:
        print(f"❌ Erreur calcul rang amélioré: {str(e)}")
        import traceback
        traceback.print_exc()
        return 'N/A'

def calculer_moyennes_par_type(notes_avec_moyennes):
    """4- Calcul des moyennes par type - UTILISE LE TYPE DE LA BASE"""
    types_matiere = {
        'litteraire': [],
        'scientifique': [], 
        'specialisee': []
    }
    
    for note_data in notes_avec_moyennes:
        if not note_data['has_notes_valides']:
            continue
            
        # UTILISER LE TYPE DE LA MATIÈRE DÉFINI DANS LA BASE
        matiere_type = note_data.get('matiere_type', '').lower()
        
        # Classification basée sur le type de la base
        if 'scientifique' in matiere_type:
            types_matiere['scientifique'].append(note_data)
        elif 'littéraire' in matiere_type or 'litteraire' in matiere_type:
            types_matiere['litteraire'].append(note_data)
        else:
            # Par défaut, mettre dans "spécialisée"
            types_matiere['specialisee'].append(note_data)
    
    # Le reste du code reste inchangé
    resultats = {}
    for type_name, notes_type in types_matiere.items():
        if not notes_type:
            resultats[f'moyenne_{type_name}'] = 0.0
            resultats[f'total_coef_{type_name}'] = 0
            continue
            
        somme_ponderee = sum(note['moyenne_ponderee'] for note in notes_type)
        total_coef = sum(note['coefficient'] for note in notes_type)
        
        moyenne_type = somme_ponderee / total_coef if total_coef > 0 else 0.0
        resultats[f'moyenne_{type_name}'] = arrondir_moyenne(moyenne_type)
        resultats[f'total_coef_{type_name}'] = total_coef
    
    return resultats

def calculer_moyenne_trimestre(moyennes_par_type):
    """5- Moy_trim = (somme des moyenne_coef)/sommes des coef"""
    somme_ponderee_totale = 0
    total_coef_totaux = 0
    
    for type_name in ['littéraire', 'scientifique', 'spécialisée']:
        moyenne_type = moyennes_par_type.get(f'moyenne_{type_name}', 0)
        total_coef_type = moyennes_par_type.get(f'total_coef_{type_name}', 0)
        
        somme_ponderee_totale += moyenne_type * total_coef_type
        total_coef_totaux += total_coef_type
    
    return somme_ponderee_totale / total_coef_totaux if total_coef_totaux > 0 else 0.0

def calculer_statistiques_classe(moyennes_eleves):
    """6- Calcul des statistiques de classe"""
    if not moyennes_eleves:
        return {
            'moy_faible': 0,
            'moy_forte': 0,
            'moy_classe': 0
        }
    
    # Filtrer les moyennes supérieures à 0
    moyennes_positives = [moy for moy in moyennes_eleves if moy > 0]
    
    if not moyennes_positives:
        return {
            'moy_faible': 0,
            'moy_forte': 0,
            'moy_classe': 0
        }
    
    moy_faible = min(moyennes_positives)
    moy_forte = max(moyennes_positives)
    moy_classe = (moy_faible + moy_forte) / 2
    
    return {
        'moy_faible': moy_faible,
        'moy_forte': moy_forte,
        'moy_classe': moy_classe
    }


def arrondir_moyenne(valeur):
    """Remplace l'ancienne fonction d'arrondi"""
    return arrondir_moyenne_specifique(valeur)

def get_mention(moyenne):
    """Retourne la mention basée sur la moyenne"""
    if moyenne >= 16:
        return "Très Bien"
    elif moyenne >= 14:
        return "Bien"
    elif moyenne >= 12:
        return "Assez Bien"
    elif moyenne >= 10:
        return "Passable"
    elif moyenne >= 5:
        return "Insuffisant"
    else:
        return "Très Insuffisant"
    
def preparer_donnees_bulletin_nouveau(eleve_id, classe_id, trimestre, annee_scolaire):
    """Prépare toutes les données pour le bulletin d'un élève - VERSION FINALE CORRIGÉE"""
    notes = Note.query.join(Matiere).filter(
        Note.eleve_id == eleve_id,
        Note.trimestre == trimestre,
        Note.annee_scolaire == annee_scolaire
    ).options(joinedload(Note.matiere)).all()
    
    if not notes:
        return {'notes': [], 'has_notes': False}
    
    donnees_notes = []
    for note in notes:
        # 1. Calculer moyenne_notes (notes 1,2,3 de l'élève)
        moyenne_notes = calculer_moyenne_notes_eleve_matiere(note)
        
        # 2. Calculer moyenne_classe (statistique de la classe)
        moyenne_classe = calculer_moyenne_classe_par_matiere(
            note.matiere_id, classe_id, trimestre, annee_scolaire
        )
        
        # 3. Calculer moyenne matière (M.MAT)
        moy_matiere = calculer_moyenne_matiere(moyenne_notes, note.note_comp)
        
        # 4. Calculer moyenne pondérée
        moy_ponderee = calculer_moyenne_ponderee(moy_matiere, note.coefficient)
        
        donnees_notes.append({
            'matiere': note.matiere.libelle,
            'matiere_type': note.matiere.type,
            'coefficient': note.coefficient,
            'note1': arrondir_moyenne(note.note1) if note.note1 else None,
            'note2': arrondir_moyenne(note.note2) if note.note2 else None,
            'note3': arrondir_moyenne(note.note3) if note.note3 else None,
            'note_comp': arrondir_moyenne(note.note_comp) if note.note_comp else None,
            'moyenne_notes': arrondir_moyenne(moyenne_notes),        # Moyenne des notes 1,2,3
            'moyenne_classe': arrondir_moyenne(moyenne_classe),      # Moyenne statistique classe
            'moyenne_matiere': arrondir_moyenne(moy_matiere),        # M.MAT = (moyenne_notes + note_comp)/2
            'moyenne_ponderee': arrondir_moyenne(moy_ponderee),
            'has_notes_valides': moyenne_notes > 0
        })
    
    # ... le reste de la fonction reste inchangé
    moyennes_par_type = calculer_moyennes_par_type(donnees_notes)
    moyenne_trimestre = calculer_moyenne_trimestre(moyennes_par_type)
    
    return {
        'notes': donnees_notes,
        'moyennes_par_type': moyennes_par_type,
        'moyenne_trimestre': arrondir_moyenne(moyenne_trimestre),
        'has_notes': True
    }

def preparer_donnees_bulletin_classe_nouveau(classe_id, trimestre, annee_scolaire):
    """Prépare les données pour tous les bulletins d'une classe - NOUVELLE VERSION"""
    # Récupérer tous les élèves de la classe
    eleves = Eleve.query.filter_by(classe_id=classe_id).all()
    
    bulletins = []
    moyennes_eleves = []
    
    for eleve in eleves:
        donnees_eleve = preparer_donnees_bulletin_nouveau(eleve.id, classe_id, trimestre, annee_scolaire)
        
        bulletin_eleve = {
            'eleve_id': str(eleve.id),
            'eleve_nom': f"{eleve.nom} {eleve.prenoms}",
            'notes': donnees_eleve['notes'],
            'moyennes_par_type': donnees_eleve['moyennes_par_type'],
            'moyenne_trimestre': donnees_eleve['moyenne_trimestre']
        }
        
        bulletins.append(bulletin_eleve)
        moyennes_eleves.append(donnees_eleve['moyenne_trimestre'])
    
    # 6. Calculer les statistiques de classe
    statistiques_classe = calculer_statistiques_classe(moyennes_eleves)
    
    return {
        'bulletins': bulletins,
        'statistiques_classe': statistiques_classe
    }

# CORRIGEZ cette fonction - LIGNE 570
def verifier_coherence_donnees(eleve_id, trimestre, annee_scolaire):
    """Vérifie la cohérence des données pour éviter les incohérences"""
    notes = Note.query.filter_by(
        eleve_id=eleve_id,
        trimestre=trimestre,
        annee_scolaire=annee_scolaire
    ).all()
    
    problemes = []
    
    for note in notes:
        # Vérifier si une moyenne est calculée alors qu'il n'y a pas de notes
        notes_valides = [n for n in [note.note1, note.note2, note.note3] if n is not None and n > 0]
        
        if len(notes_valides) == 0 and note.note_comp is None:
            # L'élève n'a aucune note dans cette matière
            problemes.append(f"Matière {note.matiere.libelle}: Aucune note mais des calculs sont effectués")
    
    return problemes

# ==================== ROUTES POUR LES BULLETINS (NOUVELLES) ====================

@bulletins_export_bp.route("/bulletins/eleve/<string:eleve_id>", methods=["GET"])
def get_bulletin_eleve_nouveau(eleve_id):
    """Retourne le bulletin détaillé d'un élève - VERSION CORRIGÉE"""
    try:
        trimestre = request.args.get("trimestre", type=int, default=1)
        annee_scolaire = request.args.get("annee_scolaire", type=str)
        
        if not annee_scolaire:
            return jsonify({"error": "L'année scolaire est requise"}), 400
        
        eleve = Eleve.query.get(eleve_id)
        if not eleve:
            return jsonify({"error": "Élève non trouvé"}), 404
        
        # Vérifier la cohérence des données
        problemes = verifier_coherence_donnees(eleve_id, trimestre, annee_scolaire)
        
        donnees_bulletin = preparer_donnees_bulletin_nouveau(eleve_id, eleve.classe_id, trimestre, annee_scolaire)
        
        response_data = {
            "eleve": {
                "id": str(eleve.id),
                "nom": eleve.nom,
                "prenoms": eleve.prenoms,
                "classe": eleve.classe.nom if eleve.classe else "N/A"
            },
            "trimestre": trimestre,
            "annee_scolaire": annee_scolaire,
            "avertissements": problemes,
            **donnees_bulletin
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la génération du bulletin: {str(e)}"}), 500

@bulletins_export_bp.route("/bulletins/classe/<string:classe_id>", methods=["GET"])
def get_bulletins_classe_nouveau(classe_id):
    """Retourne tous les bulletins d'une classe - NOUVELLE VERSION"""
    try:
        trimestre = request.args.get("trimestre", type=int, default=1)
        annee_scolaire = request.args.get("annee_scolaire", type=str)
        
        if not annee_scolaire:
            return jsonify({"error": "L'année scolaire est requise"}), 400
        
        classe = Classe.query.get(classe_id)
        if not classe:
            return jsonify({"error": "Classe non trouvée"}), 404
        
        donnees_classe = preparer_donnees_bulletin_classe_nouveau(classe_id, trimestre, annee_scolaire)
        
        return jsonify({
            "classe": {
                "id": str(classe.id),
                "nom": classe.nom
            },
            "trimestre": trimestre,
            "annee_scolaire": annee_scolaire,
            **donnees_classe
        })
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la génération des bulletins: {str(e)}"}), 500


# ========== FONCTIONS UTILITAIRES ==========

def get_observation_for_note(moyenne):
    """Retourne l'observation dynamique basée sur la moyenne"""
    if moyenne >= 16: return "Très Bien"
    elif moyenne >= 14: return "Bien"
    elif moyenne >= 12: return "Assez Bien"
    elif moyenne >= 10: return "Passable"
    elif moyenne >= 5: return "Insuffisant"
    else: return "Très Insuffisant"

def format_classement(rank):
    """Formate le rang avec les suffixes corrects"""
    if rank is None or rank == '-': return "—"
    
    try:
        rank_int = int(rank)
        if 10 <= rank_int % 100 <= 20:
            suffix = "èm"
        else:
            suffix = {1: " er", 2: " èm", 3: " èm"}.get(rank_int % 10, " èm")
        return f"{rank_int}{suffix}"
    except (ValueError, TypeError):
        return str(rank)

def calculer_rangs_categories(eleve_data, classe_id, trimestre, annee_scolaire, eleve_courant_id):
    """Calcule les rangs pour chaque catégorie de matières"""
    rangs_categories = {'litteraire': '-', 'scientifique': '-', 'specialise': '-'}
    
    try:
        eleves_classe = Eleve.query.filter_by(classe_id=classe_id).all()
        moyennes_par_categorie = {'litteraire': [], 'scientifique': [], 'specialise': []}
        
        moyennes_par_categorie['litteraire'].append({
            'eleve_id': eleve_courant_id, 'valeur': eleve_data.get('moyenne_litteraire', 0)
        })
        moyennes_par_categorie['scientifique'].append({
            'eleve_id': eleve_courant_id, 'valeur': eleve_data.get('moyenne_scientifique', 0)
        })
        moyennes_par_categorie['specialise'].append({
            'eleve_id': eleve_courant_id, 'valeur': eleve_data.get('moyenne_specialise', 0)
        })
        
        for eleve in eleves_classe:
            if eleve.id == eleve_courant_id:
                continue
                
            try:
                moyenne_eleve = Moyenne.query.filter_by(
                    eleve_id=eleve.id,
                    trimestre=trimestre,
                    annee_scolaire=annee_scolaire
                ).first()
                
                if moyenne_eleve:
                    moyennes_categories = calculer_moyennes_categories_direct(
                        eleve.id, trimestre, annee_scolaire, classe_id
                    )
                    
                    for categorie in ['litteraire', 'scientifique', 'specialise']:
                        moyennes_par_categorie[categorie].append({
                            'eleve_id': eleve.id,
                            'valeur': moyennes_categories[categorie]
                        })
                    
            except Exception as e:
                print(f"⚠️ Erreur calcul données élève {eleve.id}: {str(e)}")
                continue
        
        for categorie in ['litteraire', 'scientifique', 'specialise']:
            eleves_avec_moyennes = [e for e in moyennes_par_categorie[categorie] if e['valeur'] > 0]
            
            if not eleves_avec_moyennes:
                rangs_categories[categorie] = '-'
                continue
                
            eleves_tries = sorted(eleves_avec_moyennes, key=lambda x: x['valeur'], reverse=True)
            
            current_rank = 1
            for idx, eleve_data in enumerate(eleves_tries):
                if idx > 0 and eleve_data['valeur'] == eleves_tries[idx-1]['valeur']:
                    pass
                else:
                    current_rank = idx + 1
                
                if eleve_data['eleve_id'] == eleve_courant_id:
                    rangs_categories[categorie] = current_rank
                    break
            else:
                rangs_categories[categorie] = '-'
                
    except Exception as e:
        print(f"❌ Erreur calcul rangs catégories: {str(e)}")
        rangs_categories = {'litteraire': 'N/A', 'scientifique': 'N/A', 'specialise': 'N/A'}
    
    return rangs_categories

def calculer_moyennes_categories_direct(eleve_id, trimestre, annee_scolaire, classe_id):
    """Calcule les moyennes par catégorie directement depuis la base"""
    try:
        notes = Note.query.filter_by(
            eleve_id=eleve_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire
        ).options(joinedload(Note.matiere)).all()
        
        total_coeff_litteraire = total_moy_coef_litteraire = 0
        total_coeff_scientifique = total_moy_coef_scientifique = 0
        total_coeff_specialise = total_moy_coef_specialise = 0
        
        for note in notes:
            # CORRECTION : Utiliser la fonction avec les bons paramètres
            moy_classe = calculer_moyenne_classe_par_matiere(
                  note.matiere_id, classe_id, trimestre, annee_scolaire
            )
            moy_matiere = calculer_moyenne_matiere(moy_classe, note.note_comp)
            coefficient = note.coefficient or 1
            
            # Ne compter que si notes valides
            if not (moy_classe > 0 or (note.note_comp and note.note_comp > 0)):
                continue
                
            moy_clas_query = db.session.query(db.func.avg(Note.note_comp)).filter(
                Note.matiere_id == note.matiere_id,
                Note.trimestre == trimestre,
                Note.annee_scolaire == annee_scolaire,
                Note.eleve.has(classe_id=classe_id),
                Note.note_comp.isnot(None)
            ).scalar()
            
            moy_clas = round(moy_clas_query or 0, 2)
            
            matiere_type = note.matiere.type or 'Autres'
            if any(keyword in matiere_type.lower() for keyword in ['littéraire', 'lettre', 'français', 'anglais', 'histoire', 'géographie']):
                total_coeff_litteraire += coefficient
                total_moy_coef_litteraire += moy_matiere * coefficient
            elif any(keyword in matiere_type.lower() for keyword in ['scientifique', 'science', 'math', 'physique', 'chimie', 'svt']):
                total_coeff_scientifique += coefficient
                total_moy_coef_scientifique += moy_matiere * coefficient
            else:
                total_coeff_specialise += coefficient
                total_moy_coef_specialise += moy_matiere * coefficient
        
        return {
            'litteraire': round(total_moy_coef_litteraire / total_coeff_litteraire, 2) if total_coeff_litteraire > 0 else 0,
            'scientifique': round(total_moy_coef_scientifique / total_coeff_scientifique, 2) if total_coeff_scientifique > 0 else 0,
            'specialise': round(total_moy_coef_specialise / total_coeff_specialise, 2) if total_coeff_specialise > 0 else 0
        }
        
    except Exception as e:
        print(f"❌ Erreur calcul moyennes direct: {str(e)}")
        return {'litteraire': 0, 'scientifique': 0, 'specialise': 0}


def calculer_moyenne_annuelle(moyennes_trimestres):
    """Calcule la moyenne annuelle à partir des moyennes des trois trimestres"""
    moyennes_valides = []
    
    for trim in [1, 2, 3]:
        if moyennes_trimestres[trim]['moyenne'] > 0:
            moyennes_valides.append(moyennes_trimestres[trim]['moyenne'])
    
    if len(moyennes_valides) == 0:
        return 0
    
    return round(sum(moyennes_valides) / len(moyennes_valides), 2)


# ========== FONCTIONS DE GÉNÉRATION PDF UNIFORMISÉES ==========

def create_signatures_section(doc_width, eleve_data, include_titulaire=True):
    """Crée la section des signatures avec alignement gauche/droite - VERSION FINALE"""
    
    # Style pour les noms - alignement selon colonne
    nom_gauche_style = ParagraphStyle(
        'NomGaucheStyle', 
        parent=getSampleStyleSheet()['Normal'], 
        fontSize=9, 
        leading=10,
        alignment=0,  # LEFT - aligné à gauche
        fontName='Helvetica-Bold'
    )
    
    nom_droite_style = ParagraphStyle(
        'NomDroiteStyle', 
        parent=getSampleStyleSheet()['Normal'], 
        fontSize=9, 
        leading=10,
        alignment=2,  # RIGHT - aligné à droite
        fontName='Helvetica-Bold'
    )
    
    # Style pour les titres
    titre_gauche_style = ParagraphStyle(
        'TitreGaucheStyle',
        parent=getSampleStyleSheet()['Normal'],
        fontSize=8,
        alignment=0,  # LEFT - aligné à gauche
        fontName='Helvetica-Bold'
    )
    
    titre_droite_style = ParagraphStyle(
        'TitreDroiteStyle',
        parent=getSampleStyleSheet()['Normal'],
        fontSize=8,
        alignment=2,  # RIGHT - aligné à droite
        fontName='Helvetica-Bold'
    )
    
    # Récupérer les données depuis la base de données
    try:
        classe = eleve_data['eleve'].classe
        ecole = Ecole.query.first()
        
        # Nom du titulaire avec gestion d'erreur
        nom_titulaire = "NON ASSIGNÉ"
        if classe.titulaire and hasattr(classe.titulaire, 'utilisateur') and classe.titulaire.utilisateur:
            civilite = getattr(classe.titulaire, 'civilite', 'M.')
            nom_titulaire = f"{civilite} {classe.titulaire.utilisateur.nom} {classe.titulaire.utilisateur.prenoms}".strip()
        elif classe.titulaire and hasattr(classe.titulaire, 'nom'):
            # Fallback si pas de relation utilisateur
            civilite = getattr(classe.titulaire, 'civilite', 'M.')
            nom_titulaire = f"{civilite} {classe.titulaire.nom}".strip()
        
        # Nom du chef d'établissement avec gestion d'erreur
        if ecole:
            nom_chef = ecole.chef_etablissement_nom or "NON DÉFINI"
            titre_chef = ecole.chef_etablissement_titre or "LE CHEF D'ÉTABLISSEMENT"
            civilite_chef = ecole.chef_etablissement_civilite or "M."
            nom_complet_chef = f"{civilite_chef} {nom_chef}".strip()
        else:
            nom_complet_chef = "NON DÉFINI"
            titre_chef = "LE CHEF D'ÉTABLISSEMENT"
        
    except Exception as e:
        print(f"⚠️ Erreur récupération signatures: {str(e)}")
        nom_titulaire = "NON ASSIGNÉ"
        nom_complet_chef = "NON DÉFINI"
        titre_chef = "LE CHEF D'ÉTABLISSEMENT"
    
    if include_titulaire:
        # VERSION AVEC ALIGNEMENT GAUCHE/DROITE et LIGNE D'ESPACE
        signatures_data = [
            [Paragraph('LE TITULAIRE', titre_gauche_style), Paragraph(titre_chef, titre_droite_style)],
            ['', ''],  # LIGNE D'ESPACE
            [Paragraph(nom_titulaire, nom_gauche_style), Paragraph(nom_complet_chef, nom_droite_style)]
        ]
        col_widths = [doc_width*0.45, doc_width*0.45]
        signatures_table = Table(signatures_data, colWidths=col_widths)
    else:
        # Version sans titulaire
        signatures_data = [
            [Paragraph(titre_chef, titre_droite_style)],
            [''],  # LIGNE D'ESPACE
            [Paragraph(nom_complet_chef, nom_droite_style)]
        ]
        signatures_table = Table(signatures_data, colWidths=[doc_width])
    
    signatures_table.setStyle(TableStyle([
        # Style général du tableau
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Espacement optimisé
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),  # RÉDUIT pour pousser à gauche
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # RÉDUIT pour pousser à droite
        
        # Pas de bordures
        ('GRID', (0, 0), (-1, -1), 0, colors.white),
        
        # Hauteur de la ligne d'espace
        ('LEADING', (0, 1), (1, 1), 8),
    ]))
    
    return signatures_table

def create_unified_bulletin_pdf(eleve_data, trimestre, annee_scolaire, mode='normal'):
    """Crée un bulletin PDF avec structure unifiée"""
    buffer = io.BytesIO()
    
    if mode == 'compact':
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=6*mm, bottomMargin=8*mm, leftMargin=6*mm, rightMargin=6*mm)
        elements = create_bulletin_content_compact(eleve_data, trimestre, annee_scolaire, doc)
    else:
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=8*mm, bottomMargin=12*mm, leftMargin=8*mm, rightMargin=8*mm)
        elements = create_bulletin_content(eleve_data, trimestre, annee_scolaire, doc)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_bulletin_elements(eleve_data, trimestre, annee_scolaire, doc):
    """Crée les éléments du bulletin avec la structure uniformisée"""
    try:
        return create_bulletin_content(eleve_data, trimestre, annee_scolaire, doc)
    except Exception as e:
        print(f"❌ Erreur version normale: {str(e)}")
        styles = getSampleStyleSheet()
        return [
            Paragraph("Erreur génération bulletin", styles['Normal']),
            Paragraph(f"Élève: {eleve_data['eleve'].nom}", styles['Normal']),
            Paragraph(f"Classe: {eleve_data['eleve'].classe.nom}", styles['Normal'])
        ]

# ========== CONTENU DES BULLETINS UNIFORMISÉS ==========

def create_bulletin_content(eleve_data, trimestre, annee_scolaire, doc=None):
    """Crée le contenu du bulletin normal - VERSION CORRIGÉE (M.CL → moyenne_notes)"""
    if doc is None:
        from reportlab.lib.pagesizes import A4
        temp_doc = SimpleDocTemplate(None, pagesize=A4)
        doc_width = temp_doc.width
    else:
        doc_width = doc.width
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles optimisés pour économiser l'espace
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=12, alignment=1, 
                                textColor=colors.HexColor('#2C3E50'), spaceAfter=2, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Heading2'], fontSize=8, alignment=1,
                                   textColor=colors.HexColor('#34495E'), spaceAfter=0.5, fontName='Helvetica-Bold')
    small_text_style = ParagraphStyle('SmallText', parent=styles['Normal'], fontSize=6, leading=7, spaceAfter=0.5)
    identite_field_style = ParagraphStyle('IdentiteField', parent=styles['Normal'], fontSize=8, alignment=0,
                                         fontName='Helvetica', leftIndent=0, spaceAfter=0)

    # En-tête professionnelle - ESPACES RÉDUITS
    ecole = Ecole.query.first()
    logo_path = r"C:\projets\python\gestion_scolaire\app\static\images\logo.png"
    
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=20*mm, height=20*mm)
            logo.hAlign = 'CENTER'
        except:
            logo = Paragraph("<b>[LOGO]</b>", styles['Normal'])
    else:
        logo = Paragraph("<b>[LOGO ÉCOLE]</b>", styles['Normal'])
    
    left_content = [
        Paragraph("<b>M.E.P.S</b>", ParagraphStyle('LeftHeader', parent=styles['Normal'], fontSize=9, alignment=0, spaceAfter=1, fontName='Helvetica-Bold')),
        Paragraph("D.R.E: MARITIME", ParagraphStyle('LeftSub', parent=styles['Normal'], fontSize=8, alignment=0, spaceAfter=1)),
        Paragraph("I.E.S.G: TSEVIE", ParagraphStyle('LeftSub', parent=styles['Normal'], fontSize=8, alignment=0))
    ]
    
    adresse_complete = f"{ecole.localite if ecole and ecole.localite else ''} - BP: {ecole.boite_postale if ecole else ''} - Tél: {ecole.telephone1 if ecole else ''}"
    
    center_content = [
        logo,
        Paragraph(f"<b>{ecole.nom if ecole else 'ÉCOLE SECONDAIRE'}</b>", ParagraphStyle('CenterHeader', parent=styles['Normal'], fontSize=10, alignment=1, spaceAfter=1, fontName='Helvetica-Bold')),
        Paragraph(adresse_complete, ParagraphStyle('CenterSub', parent=styles['Normal'], fontSize=8, alignment=1)),
        Paragraph(f"{ecole.devise if ecole else ''}", ParagraphStyle('CenterSub', parent=styles['Normal'], fontSize=8, alignment=1))
    ]
    
    right_content = [
        Paragraph("<b>RÉPUBLIQUE TOGOLAISE</b>", ParagraphStyle('RightHeader', parent=styles['Normal'], fontSize=9, alignment=2, spaceAfter=1, fontName='Helvetica-Bold')),
        Paragraph("Travail - Liberté - Patrie", ParagraphStyle('RightSub', parent=styles['Normal'], fontSize=8, alignment=2, fontName='Helvetica-Bold'))
    ]
    
    header_data = [[
        Table([[cell] for cell in left_content], colWidths=[doc_width/3], style=TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ])),
        Table([[cell] for cell in center_content], colWidths=[doc_width/3], style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ])),
        Table([[cell] for cell in right_content], colWidths=[doc_width/3], style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
    ]]
    
    header_table = Table(header_data, colWidths=[doc_width/3, doc_width/3, doc_width/3])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, 0), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, 0), 0), ('TOPPADDING', (0, 0), (-1, 0), 0),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 2*mm))
    
        # Titre principal
    title = Paragraph(f"<b>BULLETIN TRIM.{trimestre} - {annee_scolaire}</b>", title_style)
    elements.append(title)
    elements.append(Spacer(1, 2*mm))
    
    # Identité élève - COMPACTÉ
    identite_title = Paragraph("<b>IDENTITÉ ÉLÈVE</b>", 
                               ParagraphStyle('IdentityTitle', parent=styles['Heading2'], 
                                              fontSize=10, alignment=1, spaceAfter=2, 
                                              fontName='Helvetica-Bold'))
    elements.append(identite_title)
    
    eleve = eleve_data['eleve']
    classe = eleve.classe
    
    identite_data = [
        [
            Paragraph(f"<b>Matricule:</b> <font face='Helvetica-Bold'>{eleve.matricule}</font>", identite_field_style),
            Paragraph(f"<b>Nom & Prénoms:</b> <font face='Helvetica-Bold'>{eleve.nom} {eleve.prenoms}</font>", identite_field_style),
        ],
        [
            Paragraph(f"<b>Date de naissance:</b> <font face='Helvetica-Bold'>{eleve.date_naissance.strftime('%d/%m/%Y') if eleve.date_naissance else 'N/A'}</font>", identite_field_style),
            Paragraph(f"<b>Sexe:</b> <font face='Helvetica-Bold'>{eleve.sexe}</font>", identite_field_style),
        ],
        [
            Paragraph(f"<b>Classe:</b> <font face='Helvetica-Bold'>{classe.nom}</font>", identite_field_style),
            Paragraph(f"<b>Statut:</b> <font face='Helvetica-Bold'>{eleve.status}</font>", identite_field_style),
        ]
    ]
    
    identite_table = Table(identite_data, colWidths=[doc_width/2, doc_width/2])
    identite_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey), ('PADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
    ]))
    
    elements.append(identite_table)
    elements.append(Spacer(1, 1*mm))
    
    # Tableau des notes - COLONNES CORRIGÉES (M.CL → MOY. NOTES)
    headers = ['DISCIPLINE', 'MOY.NOTES', 'NOTE', 'M.MAT', 'COEF', 'M.COEF', 'RANG', 'OBS', 'PROF', 'SIGN']
    
    def create_matiere_section_compact(matiere_type, matieres_list, section_title, moyenne_categorie, rang_categorie=None):
        if not matieres_list: 
            return None
            
        section_elements = []
        section_elements.append(Paragraph(f"<b>{section_title}</b>", subtitle_style))
        section_elements.append(Spacer(1, 0.1*mm))
    
        data = [headers]
    
        for matiere in matieres_list:
            moyenne_notes = matiere['moyenne_notes'] or 0  # REMPLACE moy_clas
            note_comp = matiere['note_comp'] or 0
            moy_mat = matiere['moy_mat'] or 0
            coefficient = matiere['coefficient'] or 1
            moy_coef = matiere['moy_coef'] or 0

            rang = matiere['rang']
            rang_str = format_classement(rang) if rang != '-' else '-'
            observation = get_observation_for_note(moy_mat)

            # COLONNE DISCIPLINE ÉLARGIE
            libelle = matiere['libelle']        
            row = [
                Paragraph(libelle, small_text_style),
                Paragraph(f"{moyenne_notes:.1f}", small_text_style),  # MOY.NOTES au lieu de M.CL
                Paragraph(f"{note_comp:.1f}", small_text_style),
                Paragraph(f"{moy_mat:.1f}", small_text_style),
                Paragraph(str(coefficient), small_text_style),
                Paragraph(f"{moy_coef:.1f}", small_text_style),
                Paragraph(rang_str, small_text_style),
                Paragraph(observation, small_text_style),
                Paragraph(matiere['enseignant'], small_text_style),
                Paragraph(matiere.get('signature', ''), small_text_style) 
            ]
            data.append(row)
        
        moyenne_a_afficher = moyenne_categorie if moyenne_categorie and moyenne_categorie > 0 else 0
        data.append([
            Paragraph(f"<b>Moy {matiere_type}</b>", small_text_style),
            '', '', '', '',
            Paragraph(f"<b>{moyenne_a_afficher:.2f}</b>", small_text_style),
            '', '', '', ''
        ])
    
        # COLONNES COMPACTES
        section_table = Table(data, colWidths=[
            doc_width * 0.26,  # DISCIPLINE
            doc_width * 0.05,  # MOY.NOTES (remplace M.CL)
            doc_width * 0.05,  # NOTE
            doc_width * 0.05,  # M.MAT
            doc_width * 0.04,  # COEF
            doc_width * 0.06,  # M.COEF
            doc_width * 0.05,  # RANG
            doc_width * 0.11,  # OBS
            doc_width * 0.12,  # PROF
            doc_width * 0.06   # SIGN
        ])
    
        section_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 5),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -2), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.2, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 1),
            ('ALIGN', (1, 1), (5, -2), 'CENTER'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 6),
            ('ALIGN', (0, 1), (0, -2), 'LEFT'),
            ('ALIGN', (7, 1), (8, -2), 'LEFT')
        ]))
    
        section_elements.append(section_table)
        section_elements.append(Spacer(1, 0.1*mm))
        return section_elements
    
    # Sections matières avec version corrigée
    for matieres, categorie, titre in [
        (eleve_data['matieres_litteraires'], 'litteraire', "MATIÈRES LITTÉRAIRES"),
        (eleve_data['matieres_scientifiques'], 'scientifique', "MATIÈRES SCIENTIFIQUES"), 
        (eleve_data['matieres_specialisees'], 'specialise', "ENSEIGNEMENTS SPÉCIALISÉS")
    ]:
        if matieres:
            moyenne_categorie = eleve_data.get(f'moyenne_{categorie}', 0)
            section_elements = create_matiere_section_compact(
                categorie.capitalize(), 
                matieres, 
                titre,
                moyenne_categorie,
                eleve_data['rangs_categories'].get(categorie)
            )
            if section_elements:
                elements.extend(section_elements)
    
    # Totaux et moyenne générale - TABLEAU ÉLARGI
    stats = eleve_data.get('stats_classe')
    if not stats:
        StatsClasse = namedtuple('StatsClasse', ['moy_forte', 'moy_faible', 'moy_class', 'effectif_composant'])
        stats = StatsClasse(moy_forte=0, moy_faible=0, moy_class=0, effectif_composant=0)
    
    moy_forte = stats.moy_forte or 0 if stats else 0
    moy_faible = stats.moy_faible or 0 if stats else 0
    moy_class = stats.moy_class or 0 if stats else 0

    total_coeff_val = eleve_data['total_coeff'] or 0
    total_moy_coef_val = eleve_data['total_moy_coef'] or 0
    moyenne_generale_val = eleve_data['moyenne_generale'] or 0
    moyenne_generale_arrondie = arrondir_moyenne_metier(moyenne_generale_val)

    # CORRECTION: Tableau TOTAUX avec la même largeur que les autres tableaux
    totaux_data = [[
        Paragraph("<b>TOTAUX</b>", small_text_style), 
        '', 
        '', 
        '',
        Paragraph(f"<b>{total_coeff_val}</b>", small_text_style),
        Paragraph(f"<b>{total_moy_coef_val:.1f}</b>", small_text_style), 
        '', 
        '',
        Paragraph(f"<b>MOY.T{trimestre}: {moyenne_generale_arrondie:.1f}</b>", small_text_style),
        Paragraph(f"<b>{format_classement(eleve_data.get('rang_general', 'N/A'))}</b>", small_text_style)
    ]]
    
    # CORRECTION: Mêmes largeurs que les sous-tableaux de matières
    totaux_table = Table(totaux_data, colWidths=[
        doc_width * 0.26,  # Même largeur que DISCIPLINE
        doc_width * 0.05,  # M.CL
        doc_width * 0.05,  # NOTE
        doc_width * 0.05,  # M.MAT
        doc_width * 0.04,  # COEF
        doc_width * 0.06,  # M.COEF
        doc_width * 0.05,  # RANG
        doc_width * 0.11,  # OBS
        doc_width * 0.10,  # PROF
        doc_width * 0.07   # SIGN
    ])
    totaux_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6C757D')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
        ('FONTSIZE', (0, 0), (-1, 0), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ADB5BD')),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Alignement à gauche pour "TOTAUX"
        ('ALIGN', (8, 0), (9, 0), 'CENTER'),  # Alignement centré pour moyenne et rang
        # Fusion des cellules vides pour un meilleur visuel
        ('SPAN', (1, 0), (3, 0)),  # Fusion des 3 cellules vides
        ('SPAN', (6, 0), (7, 0)),  # Fusion des 2 cellules vides
    ]))

    elements.append(Spacer(1, 1*mm))
    elements.append(totaux_table)
    elements.append(Spacer(1, 1*mm))
    
    # Récapitulatif - STRUCTURE OPTIMISÉE
    moyennes_trimestres = get_moyennes_avec_fallback(eleve_data['eleve'].id, trimestre, annee_scolaire)

# CORRECTION: Forcer la cohérence - utiliser la même valeur pour le trimestre courant
    if trimestre in moyennes_trimestres:
       moyennes_trimestres[trimestre]['moyenne'] = moyenne_generale_val

 # 1. STATISTIQUES CLASSE - Structure compacte avec arrondi métier
    moy_forte_arrondie = arrondir_moyenne_metier(moy_forte)
    moy_faible_arrondie = arrondir_moyenne_metier(moy_faible)
    moy_class_arrondie = arrondir_moyenne_metier(moy_class)

    stats_classe_lines = [
         f"Moy.forte: {moy_forte_arrondie:.1f}   Moy.faible: {moy_faible_arrondie:.1f}",
         f"Moy.classe: {moy_class_arrondie:.1f}"
     ]

   # 2. MOYENNES - Structure en tableau interne avec arrondi métier
    moyennes_lines = []
    for trim in [1, 2, 3]:
          if trim <= trimestre and moyennes_trimestres[trim]['moyenne'] > 0:
             moy = moyennes_trimestres[trim]['moyenne']
             moy_arrondie = arrondir_moyenne_metier(moy)
             rang = format_classement(moyennes_trimestres[trim]['rang'])
             effectif_total = Eleve.query.filter_by(classe_id=eleve_data['eleve'].classe_id).count()
             moyennes_lines.append(f"Trim.{trim}: {moy_arrondie:.1f}     {rang} sur {effectif_total}")

    # Moyenne annuelle avec arrondi métier
    if trimestre == 3:
        moyennes_valides = []
        for trim in [1, 2, 3]:
           if trim in moyennes_trimestres and moyennes_trimestres[trim]['moyenne'] > 0:
               moyennes_valides.append(moyennes_trimestres[trim]['moyenne'])
    
        if moyennes_valides:
           moyenne_annuelle = sum(moyennes_valides) / len(moyennes_valides)
           moyenne_annuelle_arrondie = arrondir_moyenne_metier(moyenne_annuelle)
           effectif_total = Eleve.query.filter_by(classe_id=eleve_data['eleve'].classe_id).count()
           moyennes_lines.append(f"Moy.ann: {moyenne_annuelle_arrondie:.1f}")

    # Observation des moyennes
    moyenne_generale = eleve_data.get('moyenne_generale', 0)
    observation_auto = get_observation_for_trimestre(moyenne_generale)
    # observation_text = f"OBSERVATION AUTOMATIQUE:\n{observation_auto}"
    # 3. Tableau principal avec structure optimisée
    stats_decision_data = [
        # En-tête
        ['STATISTIQUES CLASSE', 'MOYENNES', 'OBSERVATION', 'DÉCISION DU CONSEIL'],
        
        # Première ligne avec toutes les données
        [
            "\n".join(stats_classe_lines),
            "\n".join(moyennes_lines),
             observation_auto,
            "[DÉCISION]\n[À COMPLÉTER]"
        ]
    ]
    
    stats_decision_table = Table(stats_decision_data, colWidths=[doc_width*0.25, doc_width*0.25, doc_width*0.25, doc_width*0.25])
    stats_decision_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8), 
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, 1), 7), 
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey), 
        ('PADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (0, 1), (0, 1), 'LEFT'),
        ('ALIGN', (1, 1), (1, 1), 'LEFT'),
        # Lignes de séparation internes pour les moyennes
        ('LINEBELOW', (1, 0), (1, 0), 1, colors.white),
        # CORRECTION 3: Ajustement spécifique pour la colonne MOYENNES
        ('LEFTPADDING', (1, 1), (1, 1), 8),  # Plus d'espace à gauche
        ('RIGHTPADDING', (1, 1), (1, 1), 8), # Plus d'espace à droit
    ]))

    elements.append(Spacer(1, 1*mm))
    elements.append(stats_decision_table)
    
    # Section appréciations compacte
    elements.append(Spacer(1, 1*mm))
    
    appreciations_data = [['Conduite: [ ]', 'Travail: [ ]', 'Honneur: [ ]', 'Encouragement: [ ]']]
    appreciations_table = Table(appreciations_data, colWidths=[doc_width*0.25, doc_width*0.25, doc_width*0.25, doc_width*0.25])
    appreciations_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),  # Réduit
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('GRID', (0, 0), (-1, 0), 0.3, colors.grey),
        ('PADDING', (0, 0), (-1, 0), 2),   # Réduit
    ]))
    
    elements.append(appreciations_table)

    # Pied de page ultra-compact
    elements.append(Spacer(1, 1*mm))


    elements.append(create_signatures_section(doc_width, eleve_data, include_titulaire=True))
    elements.append(Spacer(1, 2*mm))

    note_bas = Paragraph("<b><font size='6'>NB: Original unique - Copies autorisées</font></b>",
                ParagraphStyle('NoteStyle', parent=styles['Normal'], fontSize=6, alignment=1, 
                             textColor=colors.black, fontName='Helvetica-Bold'))  # Réduit
    elements.append(note_bas)

    return elements

def create_bulletin_content_compact(eleve_data, trimestre, annee_scolaire, doc=None):
    """Version compacte du bulletin - VERSION CORRIGÉE (M.CL → MOY.NOTES)"""
    if doc is None:
        from reportlab.lib.pagesizes import A4
        temp_doc = SimpleDocTemplate(None, pagesize=A4)
        doc_width = temp_doc.width
    else:
        doc_width = doc.width
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles compactes
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=12, alignment=1,
                                textColor=colors.HexColor('#2C3E50'), spaceAfter=3, fontName='Helvetica-Bold')
    small_text_style = ParagraphStyle('SmallText', parent=styles['Normal'], fontSize=6, leading=7, spaceAfter=0.5)

    # En-tête compacte
    ecole = Ecole.query.first()
    logo_path = r"C:\projets\python\gestion_scolaire\app\static\images\logo.png"
    
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=15*mm, height=15*mm)
            logo.hAlign = 'CENTER'
        except:
            logo = Paragraph("<b>[LOGO]</b>", styles['Normal'])
    else:
        logo = Paragraph("<b>[LOGO ÉCOLE]</b>", styles['Normal'])
    
    left_content = [
        Paragraph("<b>M.E.P.S</b>", ParagraphStyle('LeftHeader', parent=styles['Normal'], fontSize=8, alignment=0, spaceAfter=1, fontName='Helvetica-Bold')),
        Paragraph("D.R.E: MARITIME", ParagraphStyle('LeftSub', parent=styles['Normal'], fontSize=7, alignment=0, spaceAfter=1)),
        Paragraph("I.E.S.G: TSEVIE", ParagraphStyle('LeftSub', parent=styles['Normal'], fontSize=7, alignment=0))
    ]
    
    adresse_complete = f"{ecole.localite if ecole and ecole.localite else ''} - BP: {ecole.boite_postale if ecole else ''}"
    
    center_content = [
        logo,
        Paragraph(f"<b>{ecole.nom if ecole else 'ÉCOLE SECONDAIRE'}</b>", ParagraphStyle('CenterHeader', parent=styles['Normal'], fontSize=9, alignment=1, spaceAfter=1, fontName='Helvetica-Bold')),
        Paragraph(adresse_complete, ParagraphStyle('CenterSub', parent=styles['Normal'], fontSize=7, alignment=1)),
        Paragraph(f"{ecole.devise if ecole else ''}", ParagraphStyle('CenterSub', parent=styles['Normal'], fontSize=7, alignment=1))
    ]
    
    right_content = [
        Paragraph("<b>RÉPUBLIQUE TOGOLAISE</b>", ParagraphStyle('RightHeader', parent=styles['Normal'], fontSize=8, alignment=2, spaceAfter=1, fontName='Helvetica-Bold')),
        Paragraph("Travail - Liberté - Patrie", ParagraphStyle('RightSub', parent=styles['Normal'], fontSize=7, alignment=2, fontName='Helvetica-Bold'))
    ]
    
    header_data = [[
        Table([[cell] for cell in left_content], colWidths=[doc_width/3], style=TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ])),
        Table([[cell] for cell in center_content], colWidths=[doc_width/3], style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ])),
        Table([[cell] for cell in right_content], colWidths=[doc_width/3], style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
    ]]
    
    header_table = Table(header_data, colWidths=[doc_width/3, doc_width/3, doc_width/3])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, 0), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, 0), 0), ('TOPPADDING', (0, 0), (-1, 0), 0),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 2*mm))
    
    # Titre principal compact
    title = Paragraph(f"<b>BULLETIN TRIM.{trimestre} - {annee_scolaire}</b>", title_style)
    elements.append(title)
    elements.append(Spacer(1, 2*mm))
    
    # Identité élève compacte
    eleve = eleve_data['eleve']
    classe = eleve.classe
    
    identite_data = [
        [
            Paragraph(f"<b>Matricule:</b> {eleve.matricule}", small_text_style),
            Paragraph(f"<b>Nom & Prénoms:</b> {eleve.nom} {eleve.prenoms}", small_text_style)
        ],
        [
            Paragraph(f"<b>Classe:</b> {classe.nom}", small_text_style),
            Paragraph(f"<b>Effectif:</b> {classe.effectif}", small_text_style)
        ]
    ]
    
    identite_table = Table(identite_data, colWidths=[doc_width/2, doc_width/2])
    identite_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.2, colors.grey), ('PADDING', (0, 0), (-1, -1), 2),
        ('FONTSIZE', (0, 0), (-1, -1), 6), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
    ]))
    
    elements.append(identite_table)
    elements.append(Spacer(1, 1*mm))
    
    # Tableau des notes compact
    headers = ['DISCIPLINE', 'MOY.NOTES', 'NOTE', 'COEF', 'M.MAT', 'M.COEF', 'RANG', 'OBS', 'PROF', 'SIGN']
    
    all_matieres = (eleve_data['matieres_litteraires'] + 
                   eleve_data['matieres_scientifiques'] + 
                   eleve_data['matieres_specialisees'])
    
    data = [headers]
    total_moy_coef = 0
    total_coeff = 0
    
    for matiere in all_matieres:
        libelle = matiere['libelle'] or ''
        moyenne_notes = matiere['moyenne_notes'] or 0  # REMPLACE moy_clas
        note_comp = matiere['note_comp'] or 0
        coefficient = matiere['coefficient'] or 1
        moy_mat = matiere['moy_mat'] or 0
        moy_coef = matiere['moy_coef'] or 0
        rang = matiere['rang'] or '-'
        observation = get_observation_for_note(moy_mat)
        enseignant = matiere['enseignant'] or ''

        row = [
            Paragraph(libelle, small_text_style),
            Paragraph(f"{moyenne_notes:.1f}", small_text_style),  # MOY.NOTES au lieu de M.CL
            Paragraph(f"{note_comp:.1f}", small_text_style),
            Paragraph(str(coefficient), small_text_style),
            Paragraph(f"{moy_mat:.1f}", small_text_style),
            Paragraph(f"{moy_coef:.1f}", small_text_style),
            Paragraph(format_classement(rang), small_text_style),
            Paragraph(observation, small_text_style),
            Paragraph(enseignant, small_text_style),
            Paragraph("", small_text_style)
        ]
        data.append(row)
        total_moy_coef += moy_coef
        total_coeff += coefficient
    
    col_widths = [
        doc_width * 0.20, doc_width * 0.05, doc_width * 0.05, doc_width * 0.05,
        doc_width * 0.04, doc_width * 0.06, doc_width * 0.05, doc_width * 0.12,
        doc_width * 0.12, doc_width * 0.05
    ]
    
    notes_table = Table(data, colWidths=col_widths)
    notes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 5), ('FONTSIZE', (0, 1), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('GRID', (0, 0), (-1, -1), 0.1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 1), ('ALIGN', (1, 1), (4, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (7, 1), (8, -1), 'LEFT'),
    ]))
    
    elements.append(notes_table)
    elements.append(Spacer(1, 2*mm))
    
    # Totaux compacts
    moyenne_generale_val = eleve_data['moyenne_generale'] or 0
    moyenne_generale_arrondie = arrondir_moyenne_metier(moyenne_generale_val)
    total_line = Paragraph(
        f"<b>TOTAUX: Coeff={total_coeff} | Moy×Coef={total_moy_coef:.1f} | MOY. TRIM: {moyenne_generale_arrondie:.1f}</b>",
        ParagraphStyle('TotalLine', parent=styles['Normal'], fontSize=7, alignment=1, spaceAfter=2, 
                      fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.HexColor('#2C3E50'))
    )
    
    elements.append(total_line)
    
    # Signatures compactes
    date_text = Paragraph(
        f"Fait à {ecole.localite if ecole and ecole.localite else ''}, le {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=5, alignment=2)
    )
    elements.append(date_text)
    elements.append(Spacer(1, 0.5*mm))
    
    # Utilisation de la fonction unifiée pour les signatures
    elements.append(create_signatures_section(doc_width, eleve_data, include_titulaire=True))
    elements.append(Spacer(1, 1*mm))  # ESPACE AUGMENTÉ pour descendre
    
    return elements

# ========== ROUTES UNIFORMISÉES ==========

@bulletins_export_bp.route("/export/bulletin", methods=["GET"])
def export_bulletin_pdf():
    """Export PDF du bulletin individuel d'un élève - VERSION UNIFORMISÉE"""
    try:
        eleve_id = request.args.get("eleve_id", type=str)
        trimestre = request.args.get("trimestre", type=int, default=1)
        annee_scolaire = request.args.get("annee_scolaire", type=str)
        mode = request.args.get("mode", type=str, default="normal")
        
        if not eleve_id or not annee_scolaire:
            return jsonify({
                "error": "Paramètres manquants: eleve_id et annee_scolaire requis",
                "code": "MISSING_PARAMETERS"
            }), 400
        
        eleve_data = get_eleve_data(UUID(eleve_id), trimestre, annee_scolaire)
        if not eleve_data:
            return jsonify({
                "error": "Élève non trouvé ou pas de données pour ce trimestre",
                "code": "STUDENT_NOT_FOUND"
            }), 404
        
        pdf_buffer = create_unified_bulletin_pdf(eleve_data, trimestre, annee_scolaire, mode)
        
        eleve = eleve_data['eleve']
        filename = f"bulletin_{eleve.nom}_{eleve.prenoms}_T{trimestre}_{annee_scolaire.replace('/', '-')}.pdf"
        
        return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
        
    except ValueError as e:
        print(f"❌ Erreur format UUID: {str(e)}")
        return jsonify({"error": "Format d'identifiant invalide", "code": "INVALID_ID_FORMAT"}), 400
    except IntegrityError as e:
        print(f"❌ Erreur intégrité base de données: {str(e)}")
        return jsonify({"error": "Erreur de cohérence des données", "code": "DATA_INTEGRITY_ERROR"}), 500
    except SQLAlchemyError as e:
        print(f"❌ Erreur base de données: {str(e)}")
        return jsonify({"error": "Erreur d'accès aux données", "code": "DATABASE_ERROR"}), 500
    except Exception as e:
        print(f"❌ Erreur génération bulletin: {str(e)}")
        return jsonify({
            "error": "Erreur lors de la génération du bulletin",
            "code": "GENERATION_ERROR",
            "details": str(e)
        }), 500

@bulletins_export_bp.route("/export/bulletins_classe", methods=["GET"])
def export_bulletins_classe():
    """Export PDF de tous les bulletins d'une classe - VERSION COMPLÈTEMENT DEBUGGÉE"""
    try:
        # Récupération et validation des paramètres
        classe_id = request.args.get("classe_id", type=str)
        trimestre = request.args.get("trimestre", type=int, default=1)
        annee_scolaire = request.args.get("annee_scolaire", type=str)
        mode = request.args.get("mode", type=str, default="normal")

        print(f"🔍 DEBUG COMPLET - Paramètres reçus:")
        print(f"   classe_id: '{classe_id}' (type: {type(classe_id)})")
        print(f"   trimestre: {trimestre}")
        print(f"   annee_scolaire: '{annee_scolaire}'")
        print(f"   mode: '{mode}'")
        
        # Vérification CRITIQUE des paramètres
        if not classe_id or str(classe_id).strip() in ['', 'null', 'undefined', 'None', 'none', 'NaN']:
            print("❌ ERREUR: classe_id est vide ou invalide")
            return jsonify({
                "error": "Veuillez sélectionner une classe", 
                "code": "MISSING_CLASS",
                "received_classe_id": str(classe_id)
            }), 400

        if not annee_scolaire:
            print("❌ ERREUR: annee_scolaire manquant")
            return jsonify({
                "error": "Paramètre annee_scolaire requis", 
                "code": "MISSING_ACADEMIC_YEAR"
            }), 400
        
        # Conversion UUID avec gestion d'erreur améliorée
        try:
            classe_uuid = UUID(str(classe_id).strip())
            print(f"✅ UUID converti: {classe_uuid}")
        except ValueError as e:
            print(f"❌ ERREUR conversion UUID: {str(e)}")
            # Tentative de recherche par nom
            classe_par_nom = Classe.query.filter(Classe.nom.ilike(f"%{classe_id}%")).first()
            if classe_par_nom:
                classe_uuid = classe_par_nom.id
                print(f"✅ Classe trouvée par nom: {classe_par_nom.nom}")
            else:
                return jsonify({
                    "error": "Identifiant de classe invalide", 
                    "code": "INVALID_CLASS_ID",
                    "details": str(e)
                }), 400
        
        # Vérification de l'existence de la classe
        classe = Classe.query.get(classe_uuid)
        if not classe:
            print(f"❌ ERREUR: Classe non trouvée en base: {classe_uuid}")
            # Lister les classes disponibles pour debug
            classes_disponibles = Classe.query.all()
            print("📋 Classes disponibles en base:")
            for c in classes_disponibles:
                print(f"   - {c.nom} (ID: {c.id})")
            
            return jsonify({
                "error": "Classe non trouvée", 
                "code": "CLASS_NOT_FOUND",
                "requested_id": str(classe_uuid),
                "available_classes": [{"id": str(c.id), "nom": c.nom} for c in classes_disponibles]
            }), 404
        
        print(f"✅ Classe trouvée: {classe.nom} (ID: {classe.id})")
        
        # Récupération des élèves
        eleves = Eleve.query.filter_by(classe_id=classe_uuid).order_by(Eleve.nom).all()
        
        if not eleves:
            print(f"⚠️ ATTENTION: Aucun élève trouvé dans la classe {classe.nom}")
            return jsonify({
                "error": "Aucun élève trouvé dans cette classe", 
                "code": "NO_STUDENTS_IN_CLASS",
                "classe": classe.nom
            }), 404
        
        print(f"✅ {len(eleves)} élèves trouvés dans la classe {classe.nom}")
        
        # Vérification des données pour chaque élève
        eleves_avec_donnees = []
        for eleve in eleves:
            print(f"🔍 Vérification données pour {eleve.nom} {eleve.prenoms}:")
            
            # Vérifier si l'élève a des notes pour ce trimestre
            notes_count = Note.query.filter_by(
                eleve_id=eleve.id,
                trimestre=trimestre,
                annee_scolaire=annee_scolaire
            ).count()
            
            # Vérifier si l'élève a une moyenne pour ce trimestre
            moyenne_count = Moyenne.query.filter_by(
                eleve_id=eleve.id,
                trimestre=trimestre,
                annee_scolaire=annee_scolaire
            ).count()
            
            print(f"   - Notes: {notes_count}, Moyennes: {moyenne_count}")
            
            if notes_count > 0 or moyenne_count > 0:
                eleves_avec_donnees.append(eleve)
        
        if not eleves_avec_donnees:
            print(f"❌ ERREUR: Aucun élève n'a de données pour le trimestre {trimestre} {annee_scolaire}")
            return jsonify({
                "error": f"Aucun élève n'a de données pour le trimestre {trimestre} de l'année {annee_scolaire}",
                "code": "NO_DATA_FOR_TRIMESTER",
                "trimestre": trimestre,
                "annee_scolaire": annee_scolaire
            }), 404
        
        print(f"📊 {len(eleves_avec_donnees)} élèves sur {len(eleves)} ont des données pour ce trimestre")
        
        # Création du PDF
        buffer = io.BytesIO()
        
        # Configuration du document avec marges optimisées
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            topMargin=10*mm,
            bottomMargin=15*mm,
            leftMargin=10*mm,
            rightMargin=10*mm
        )
        
        all_elements = []
        successful_bulletins = 0
        failed_bulletins = 0
        
        # Génération des bulletins
        for i, eleve in enumerate(eleves_avec_donnees):
            if i > 0:
                all_elements.append(PageBreak())
            
            try:
                print(f"📝 Génération bulletin {i+1}/{len(eleves_avec_donnees)}: {eleve.nom} {eleve.prenoms}")
                
                # Récupération des données de l'élève
                eleve_data = get_eleve_data(eleve.id, trimestre, annee_scolaire)
                
                if eleve_data:
                    # Vérifier que les données sont valides
                    if (eleve_data.get('moyenne_generale', 0) > 0 or 
                        len(eleve_data.get('matieres_litteraires', [])) > 0 or
                        len(eleve_data.get('matieres_scientifiques', [])) > 0 or
                        len(eleve_data.get('matieres_specialisees', [])) > 0):
                        
                        # Génération du contenu selon le mode
                        if mode == "compact":
                            bulletin_elements = create_bulletin_content_compact(eleve_data, trimestre, annee_scolaire, doc)
                        else:
                            bulletin_elements = create_bulletin_content(eleve_data, trimestre, annee_scolaire, doc)
                        
                        if bulletin_elements:
                            all_elements.extend(bulletin_elements)
                            successful_bulletins += 1
                            print(f"✅ Bulletin généré avec succès pour {eleve.nom}")
                        else:
                            print(f"⚠️ Aucun élément généré pour {eleve.nom}")
                            failed_bulletins += 1
                    else:
                        print(f"⚠️ Données insuffisantes pour {eleve.nom} (moyenne: {eleve_data.get('moyenne_generale', 0)})")
                        failed_bulletins += 1
                        
                        # Créer un message d'erreur dans le PDF
                        error_style = ParagraphStyle(
                            'ErrorStyle', 
                            parent=getSampleStyleSheet()['Normal'], 
                            fontSize=12, 
                            alignment=1, 
                            textColor=colors.red,
                            spaceAfter=20
                        )
                        all_elements.append(Paragraph(f"DONNÉES INSUFFISANTES", error_style))
                        all_elements.append(Paragraph(f"Pour {eleve.nom} {eleve.prenoms}", error_style))
                        all_elements.append(Paragraph(f"Trimestre {trimestre} - {annee_scolaire}", error_style))
                        all_elements.append(Spacer(1, 20*mm))
                        
                else:
                    print(f"❌ Aucune donnée récupérée pour {eleve.nom}")
                    failed_bulletins += 1
                    
                    # Message d'erreur dans le PDF
                    error_style = ParagraphStyle(
                        'ErrorStyle', 
                        parent=getSampleStyleSheet()['Normal'], 
                        fontSize=12, 
                        alignment=1, 
                        textColor=colors.red,
                        spaceAfter=20
                    )
                    all_elements.append(Paragraph(f"AUCUNE DONNÉE DISPONIBLE", error_style))
                    all_elements.append(Paragraph(f"Pour {eleve.nom} {eleve.prenoms}", error_style))
                    all_elements.append(Spacer(1, 20*mm))
                    
            except Exception as e:
                print(f"❌ ERREUR génération bulletin {eleve.nom}: {str(e)}")
                import traceback
                traceback.print_exc()
                failed_bulletins += 1
                
                # Message d'erreur détaillé dans le PDF
                error_style = ParagraphStyle(
                    'ErrorStyle', 
                    parent=getSampleStyleSheet()['Normal'], 
                    fontSize=10, 
                    alignment=1, 
                    textColor=colors.red,
                    spaceAfter=10
                )
                all_elements.append(Paragraph(f"ERREUR DE GÉNÉRATION", error_style))
                all_elements.append(Paragraph(f"Pour {eleve.nom} {eleve.prenoms}", error_style))
                all_elements.append(Paragraph(f"Erreur: {str(e)}", error_style))
                all_elements.append(Spacer(1, 15*mm))
        
        # Vérification finale
        if not all_elements:
            print("❌ ERREUR FINALE: Aucun élément à exporter")
            return jsonify({
                "error": "Aucune donnée à exporter après traitement", 
                "code": "NO_ELEMENTS_TO_EXPORT",
                "statistics": {
                    "total_eleves": len(eleves),
                    "eleves_avec_donnees": len(eleves_avec_donnees),
                    "bulletins_reussis": successful_bulletins,
                    "bulletins_echoues": failed_bulletins
                }
            }), 404
        
        print(f"📄 Construction du PDF avec {len(all_elements)} éléments...")
        print(f"📊 Statistiques: {successful_bulletins} réussis, {failed_bulletins} échoués")
        
        try:
            # Construction du PDF
            doc.build(all_elements)
            buffer.seek(0)
            
            # Nom du fichier
            filename = f"bulletins_{classe.nom}_T{trimestre}_{annee_scolaire.replace('/', '-')}.pdf"
            print(f"✅ EXPORT RÉUSSI: {filename}")
            
            return send_file(
                buffer, 
                as_attachment=True, 
                download_name=filename, 
                mimetype='application/pdf'
            )
            
        except Exception as e:
            print(f"❌ ERREUR construction PDF: {str(e)}")
            return jsonify({
                "error": "Erreur lors de la construction du PDF", 
                "code": "PDF_BUILD_ERROR",
                "details": str(e)
            }), 500
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE dans export_bulletins_classe: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "error": "Erreur critique lors de la génération des bulletins de classe",
            "code": "CRITICAL_ERROR", 
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500


@bulletins_export_bp.route("/export/bulletins_toutes_classes", methods=["GET"])
def export_bulletins_toutes_classes():
    """Export PDF de tous les bulletins de toutes les classes - VERSION CORRIGÉE"""
    try:
        trimestre = request.args.get("trimestre", type=int, default=1)
        annee_scolaire = request.args.get("annee_scolaire", type=str)
        mode = request.args.get("mode", type=str, default="normal")
        
        if not annee_scolaire:
            return jsonify({"error": "Paramètre annee_scolaire requis", "code": "MISSING_ACADEMIC_YEAR"}), 400
        
        classes = Classe.query.order_by(Classe.nom).all()
        if not classes:
            return jsonify({"error": "Aucune classe trouvée", "code": "NO_CLASSES_FOUND"}), 404
        
        print(f"🎯 Export toutes classes - {len(classes)} classes trouvées")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              topMargin=6*mm, bottomMargin=8*mm, 
                              leftMargin=6*mm, rightMargin=6*mm)
        
        all_elements = []
        total_bulletins = 0
        
        for classe_index, classe in enumerate(classes):
            print(f"📚 Traitement classe {classe_index+1}/{len(classes)}: {classe.nom}")
            
            if classe_index > 0:
                all_elements.append(PageBreak())
            
            # Récupérer les élèves de cette classe
            eleves = Eleve.query.filter_by(classe_id=classe.id).order_by(Eleve.nom).all()
            
            if not eleves:
                print(f"⚠️ Aucun élève dans la classe {classe.nom}")
                continue
            
            print(f"   👥 {len(eleves)} élèves dans cette classe")
            
            for eleve_index, eleve in enumerate(eleves):
                if eleve_index > 0:
                    all_elements.append(PageBreak())
                
                try:
                    print(f"   📝 Génération bulletin {eleve_index+1}/{len(eleves)}: {eleve.nom}")
                    eleve_data = get_eleve_data(eleve.id, trimestre, annee_scolaire)
                    
                    if eleve_data:
                        if mode == "compact":
                            bulletin_elements = create_bulletin_content_compact(eleve_data, trimestre, annee_scolaire, doc)
                        else:
                            bulletin_elements = create_bulletin_content(eleve_data, trimestre, annee_scolaire, doc)
                        
                        all_elements.extend(bulletin_elements)
                        total_bulletins += 1
                        print(f"   ✅ Bulletin généré pour {eleve.nom}")
                    else:
                        print(f"   ⚠️ Pas de données pour {eleve.nom}")
                        # Ajouter un message d'erreur
                        error_style = ParagraphStyle('Error', parent=getSampleStyleSheet()['Normal'], 
                                                   fontSize=10, alignment=1, textColor=colors.red)
                        all_elements.append(Paragraph(f"Pas de données pour {eleve.nom} {eleve.prenoms}", error_style))
                        all_elements.append(Spacer(1, 10*mm))
                        
                except Exception as e:
                    print(f"   ❌ Erreur génération bulletin {eleve.nom}: {str(e)}")
                    # Ajouter un message d'erreur dans le PDF
                    error_style = ParagraphStyle('Error', parent=getSampleStyleSheet()['Normal'], 
                                               fontSize=9, alignment=1, textColor=colors.red)
                    all_elements.append(Paragraph(f"Erreur génération bulletin pour {eleve.nom}", error_style))
                    all_elements.append(Paragraph(f"Détails: {str(e)}", error_style))
                    all_elements.append(Spacer(1, 10*mm))
        
        if not all_elements:
            return jsonify({"error": "Aucune donnée à exporter", "code": "NO_DATA_TO_EXPORT"}), 404
        
        print(f"📄 Construction du PDF avec {len(all_elements)} éléments ({total_bulletins} bulletins)...")
        
        try:
            doc.build(all_elements)
            buffer.seek(0)
            
            filename = f"bulletins_toutes_classes_T{trimestre}_{annee_scolaire.replace('/', '-')}.pdf"
            print(f"✅ Export réussi: {filename}")
            
            return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
            
        except Exception as e:
            print(f"❌ Erreur construction PDF: {str(e)}")
            return jsonify({
                "error": "Erreur lors de la construction du PDF",
                "code": "PDF_BUILD_ERROR",
                "details": str(e)
            }), 500
        
    except Exception as e:
        print(f"❌ Erreur critique génération bulletins toutes classes: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Erreur lors de la génération des bulletins de toutes les classes",
            "code": "BULLETINS_GENERATION_ERROR",
            "details": str(e)
        }), 500

@bulletins_export_bp.route("/export/filters", methods=["GET"])
def get_bulletin_filters():
    """Renvoie les filtres disponibles pour l'export des bulletins"""
    try:
        classes = Classe.query.order_by(Classe.nom).all()
        annees_scolaires = [m[0] for m in db.session.query(Moyenne.annee_scolaire).distinct() if m[0]]
        
        classes_with_eleves = []
        for classe in classes:
            eleves = Eleve.query.filter_by(classe_id=classe.id).order_by(Eleve.nom).all()
            classes_with_eleves.append({
                "id": str(classe.id),
                "nom": classe.nom,
                "eleves": [{"id": str(e.id), "nom_complet": f"{e.nom} {e.prenoms}"} for e in eleves]
            })
        
        return jsonify({
            "classes": classes_with_eleves,
            "annees_scolaires": annees_scolaires,
            "trimestres": [1, 2, 3]
        })
        
    except Exception as e:
        print(f"Erreur dans get_bulletin_filters: {str(e)}")
        return jsonify({
            "error": f"Erreur lors du chargement des filtres: {str(e)}",
            "classes": [],
            "annees_scolaires": [],
            "trimestres": [1, 2, 3]
        }), 500
    
@bulletins_export_bp.route("/export/debug_calculs/<string:classe_id>", methods=["GET"])
def debug_calculs_essentiel(classe_id):
    """Debug minimal pour vérifier les calculs - VERSION CORRIGÉE"""
    try:
        trimestre = request.args.get("trimestre", type=int, default=1)
        annee_scolaire = request.args.get("annee_scolaire", type=str)
        
        if not annee_scolaire:
            return jsonify({"error": "L'année scolaire est requise"}), 400
        
        classe = Classe.query.get(UUID(classe_id))
        if not classe:
            return jsonify({"error": "Classe non trouvée"}), 404
        
        # Récupérer le PREMIER élève avec des notes dans cette classe
        eleve = Eleve.query.filter_by(classe_id=classe_id).join(Note).filter(
            Note.trimestre == trimestre,
            Note.annee_scolaire == annee_scolaire
        ).first()
        
        if not eleve:
            return jsonify({
                "error": "Aucun élève avec des notes trouvé dans cette classe",
                "classe": classe.nom,
                "trimestre": trimestre,
                "annee_scolaire": annee_scolaire
            }), 404
        
        # Récupérer TOUTES les notes de cet élève
        notes = Note.query.filter_by(
            eleve_id=eleve.id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire
        ).options(joinedload(Note.matiere)).all()
        
        if not notes:
            return jsonify({
                "error": "Aucune note trouvée pour cet élève",
                "eleve": f"{eleve.nom} {eleve.prenoms}",
                "classe": classe.nom
            }), 404
        
        # Test avec la première matière
        note_test = notes[0]
        
        # NOUVEAUX CALCULS CORRIGÉS
        moyenne_notes = calculer_moyenne_notes_eleve_matiere(note_test)  # REMPLACE M.CL
        moy_matiere = calculer_moyenne_matiere(moyenne_notes, note_test.note_comp)
        
        # Détails de toutes les matières
        details_matieres = []
        for note in notes:
            moy_notes = calculer_moyenne_notes_eleve_matiere(note)  # M.CL → moyenne_notes
            moy_mat = calculer_moyenne_matiere(moy_notes, note.note_comp)
            
            details_matieres.append({
                'matiere': note.matiere.libelle,
                'note1': note.note1,
                'note2': note.note2,
                'note3': note.note3,
                'note_comp': note.note_comp,
                'coefficient': note.coefficient,
                'moyenne_notes': moy_notes,  # REMPLACE M.CL
                'moyenne_matiere': moy_mat
            })
        
        return jsonify({
            'eleve': f"{eleve.nom} {eleve.prenoms}",
            'classe': classe.nom,
            'trimestre': trimestre,
            'annee_scolaire': annee_scolaire,
            'test_basique': {
                'matiere': note_test.matiere.libelle,
                'note1': note_test.note1,
                'note2': note_test.note2, 
                'note3': note_test.note3,
                'note_comp': note_test.note_comp,
                'coefficient': note_test.coefficient,
                'moyenne_notes_calculee': moyenne_notes,  # REMPLACE M.CL
                'moyenne_matiere_calculee': moy_matiere,
                'formule': f"moyenne_notes = moyenne des notes 1,2,3 = {moyenne_notes}",
                'formule_matiere': f"({moyenne_notes} + {note_test.note_comp or 0}) / 2 = {moy_matiere}"
            },
            'toutes_les_matieres': details_matieres,
            'explication': "M.CL a été remplacé par moyenne_notes (moyenne des notes 1,2,3 de l'élève)",
            'statut': 'Calculs de base OK' if moy_matiere > 0 else 'Problème détecté'
        })
        
    except Exception as e:
        return jsonify({"error": f"Erreur debug: {str(e)}"}), 500
    
@bulletins_export_bp.route("/export/liste_eleves", methods=["GET"])
def liste_eleves():
    """Liste tous les élèves avec leurs IDs pour faciliter les tests"""
    try:
        eleves = Eleve.query.options(joinedload(Eleve.classe)).order_by(Eleve.nom).all()
        
        result = {
            "eleves": []
        }
        
        for eleve in eleves:
            # Compter les notes pour chaque trimestre
            notes_count = {}
            for trim in [1, 2, 3]:
                count = Note.query.filter_by(
                    eleve_id=eleve.id,
                    trimestre=trim
                ).count()
                notes_count[f'trimestre_{trim}'] = count
            
            result["eleves"].append({
                "id": str(eleve.id),
                "nom_complet": f"{eleve.nom} {eleve.prenoms}",
                "classe": eleve.classe.nom if eleve.classe else "N/A",
                "matricule": eleve.matricule,
                "notes_par_trimestre": notes_count
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@bulletins_export_bp.route("/export/liste_classes", methods=["GET"])
def liste_classes():
    """Liste toutes les classes avec leurs IDs"""
    try:
        classes = Classe.query.order_by(Classe.nom).all()
        
        result = {
            "classes": []
        }
        
        for classe in classes:
            # Compter les élèves
            eleves_count = Eleve.query.filter_by(classe_id=classe.id).count()
            
            # Compter les notes pour le trimestre 1
            notes_count = Note.query.filter_by(trimestre=1).join(Eleve).filter(
                Eleve.classe_id == classe.id
            ).count()
            
            result["classes"].append({
                "id": str(classe.id),
                "nom": classe.nom,
                "effectif": eleves_count,
                "notes_trimestre_1": notes_count
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500
    
@bulletins_export_bp.route("/admin/signatures", methods=["GET"])
def get_signatures_config():
    """Récupère la configuration actuelle des signatures"""
    try:
        classes = Classe.query.options(
            joinedload(Classe.titulaire).joinedload(Enseignant.utilisateur)
        ).order_by(Classe.nom).all()
        
        enseignants = Enseignant.query.options(joinedload(Enseignant.utilisateur)).all()
        ecole = Ecole.query.first()
        
        result = {
            "ecole": {
                "id": str(ecole.id) if ecole else None,
                "chef_etablissement_nom": ecole.chef_etablissement_nom if ecole else None,
                "chef_etablissement_titre": ecole.chef_etablissement_titre if ecole else None,
                "chef_etablissement_civilite": ecole.chef_etablissement_civilite if ecole else "M."
            } if ecole else None,
            "classes": [],
            "enseignants": []
        }
        
        # Classes avec leurs titulaires
        for classe in classes:
            titulaire_info = None
            if classe.titulaire and classe.titulaire.utilisateur:
                titulaire_info = {
                    "id": str(classe.titulaire.id),
                    "nom_complet": f"{classe.titulaire.utilisateur.nom} {classe.titulaire.utilisateur.prenoms}",
                    "civilite": getattr(classe.titulaire, 'civilite', 'M.')
                }
            
            result["classes"].append({
                "id": str(classe.id),
                "nom": classe.nom,
                "titulaire": titulaire_info
            })
        
        # Liste des enseignants disponibles
        for enseignant in enseignants:
            if enseignant.utilisateur:
                result["enseignants"].append({
                    "id": str(enseignant.id),
                    "nom_complet": f"{enseignant.utilisateur.nom} {enseignant.utilisateur.prenoms}",
                    "civilite": getattr(enseignant, 'civilite', 'M.'),
                    "matieres": [ens.matiere.libelle for ens in enseignant.enseignements]
                })
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Erreur récupération configuration signatures: {str(e)}")
        return jsonify({"error": f"Erreur lors de la récupération: {str(e)}"}), 500

@bulletins_export_bp.route("/admin/signatures/titulaire", methods=["POST"])
def definir_titulaire():
    """Définit le titulaire d'une classe"""
    try:
        data = request.get_json()
        classe_id = data.get('classe_id')
        enseignant_id = data.get('enseignant_id')
        
        if not classe_id:
            return jsonify({"error": "ID de classe requis"}), 400
        
        classe = Classe.query.get(UUID(classe_id))
        if not classe:
            return jsonify({"error": "Classe non trouvée"}), 404
        
        if enseignant_id:
            enseignant = Enseignant.query.get(UUID(enseignant_id))
            if not enseignant:
                return jsonify({"error": "Enseignant non trouvé"}), 404
            classe.titulaire_id = UUID(enseignant_id)
        else:
            # Supprimer le titulaire
            classe.titulaire_id = None
        
        db.session.commit()
        
        return jsonify({
            "message": "Titulaire défini avec succès" if enseignant_id else "Titulaire supprimé avec succès",
            "classe": classe.nom
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur définition titulaire: {str(e)}")
        return jsonify({"error": f"Erreur lors de la définition: {str(e)}"}), 500

@bulletins_export_bp.route("/admin/signatures/chef", methods=["POST"])
def definir_chef_etablissement():
    """Définit le chef d'établissement"""
    try:
        data = request.get_json()
        nom = data.get('nom')
        titre = data.get('titre', "LE CHEF D'ÉTABLISSEMENT")
        civilite = data.get('civilite', 'M.')
        
        if not nom:
            return jsonify({"error": "Nom du chef d'établissement requis"}), 400
        
        ecole = Ecole.query.first()
        if not ecole:
            return jsonify({"error": "Aucune école trouvée"}), 404
        
        ecole.chef_etablissement_nom = nom.strip()
        ecole.chef_etablissement_titre = titre.strip()
        ecole.chef_etablissement_civilite = civilite.strip()
        
        db.session.commit()
        
        return jsonify({
            "message": "Chef d'établissement défini avec succès",
            "chef": {
                "nom": nom,
                "titre": titre,
                "civilite": civilite
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur définition chef établissement: {str(e)}")
        return jsonify({"error": f"Erreur lors de la définition: {str(e)}"}), 500

   #Contrôle , permission et autorisation pour les admin
def is_admin():
    return getattr(current_user, "role","").lower() in ["admin", "administrateur"]
 
@bulletins_export_bp.route("/admin/signatures/page")
@login_required
def admin_signatures_page():
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    """Page d'administration des signatures"""
    return render_template("admin_sign.html")
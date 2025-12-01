from flask import Blueprint, render_template, request, jsonify,current_app
from extensions import db
from ..models import Classe, Enseignant, Eleve
from sqlalchemy import cast, String
from flask_login import current_user, login_required
import random
import string
import uuid
from uuid import UUID
from ..utils import ecole_required, get_current_ecole_id

classes_bp = Blueprint("classes", __name__, url_prefix="/classes")

# Contrôle , permission et autorisation pour les admin
def is_admin():
    return getattr(current_user, "role", "").lower() in ["admin", "administrateur"]

@classes_bp.route("/")
@login_required
@ecole_required
def liste_classes():
    ecole_id = get_current_ecole_id()
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)
    
    # Requête de base - FILTRER PAR ÉCOLE
    query = Classe.query.filter_by(ecole_id=ecole_id)

    # Recherche texte
    if search:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Classe.code.ilike(f"%{search}%"),
                Classe.nom.ilike(f"%{search}%"),
                cast(Classe.effectif, String).ilike(f"%{search}%"),
                Classe.etat.ilike(f"%{search}%")
            )
        )
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    classes = pagination.items
    
    # Rôle de l'utilisateur connecté
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()
    
    # Enseignants de l'école courante uniquement
    enseignants = Enseignant.query.filter_by(ecole_id=ecole_id).all()

    return render_template("classes/e_listeClasse.html",
                           classes=classes,
                           pagination=pagination,
                           search=search,
                           per_page=per_page,
                           user_role=user_role,
                           enseignants=enseignants,
                           ecole_id=ecole_id)

def generate_classe_code():
    """Génère un code de classe de 6 caractères commençant par CLAS"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
    return f"CLAS{suffix}"

@classes_bp.route("/add", methods=["POST"])
@login_required
@ecole_required
def add_classe():
    """
    Ajouter une classe
    Nécessite les droits admin + contexte école
    """
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole_id = get_current_ecole_id()
    
    # Si un code est fourni manuellement, on l'utilise. Sinon on génère un code unique.
    code = request.form.get("code")
    if not code:
        code = f"CL-{uuid.uuid4().hex[:6].upper()}"
    
    nom = request.form.get("nom")
    effectif = int(request.form.get("effectif", 0))

    # Validation des données
    if not nom:
        return jsonify({"error": "Le nom de la classe est obligatoire"}), 400
    
    if effectif < 0:
        return jsonify({"error": "L'effectif ne peut pas être négatif"}), 400

    # Vérifier unicité du code (dans la même école)
    if Classe.query.filter_by(code=code, ecole_id=ecole_id).first():
        return jsonify({"error": "Cette classe existe déjà dans cette école"}), 400

    # Vérifier unicité du nom (dans la même école)
    if Classe.query.filter_by(nom=nom, ecole_id=ecole_id).first():
        return jsonify({"error": "Une classe avec ce nom existe déjà dans cette école"}), 400

    # Récupérer les enseignants sélectionnés (vérifier qu'ils appartiennent à l'école)
    enseignant_ids = request.form.getlist("enseignants[]")
    enseignants = Enseignant.query.filter(
        Enseignant.id.in_(enseignant_ids),
        Enseignant.ecole_id == ecole_id
    ).all()

    # Création de la classe avec ecole_id
    classe = Classe(
        code=code, 
        nom=nom, 
        effectif=effectif, 
        etat="Inactif",
        ecole_id=ecole_id  # IMPORTANT : lier la classe à l'école
    )
    
    if enseignants:
        classe.enseignants = enseignants

    db.session.add(classe)
    db.session.commit()

    return jsonify({
        "message": "Classe ajoutée avec succès",
        "classe_id": str(classe.id)
    })

WORKFLOW = {
    "Activer": {"from": "Inactif", "to": "Actif"},
    "Fermer": {"from": "Actif", "to": "Fermé"}
}

@classes_bp.route("/get/<string:id>", methods=["GET"])
@login_required
@ecole_required
def get_classe(id):
    """
    Récupérer une classe spécifique
    Vérifier qu'elle appartient à l'école courante
    """
    ecole_id = get_current_ecole_id()
    classe = Classe.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    return jsonify({
        "id": str(classe.id),
        "code": classe.code,
        "nom": classe.nom,
        "effectif": classe.effectif,
        "enseignants": [str(e.id) for e in classe.enseignants],
        "enseignants_nom": [f"{e.utilisateur.prenoms} {e.utilisateur.nom}" for e in classe.enseignants],
        "etat": classe.etat
    })

@classes_bp.route("/<string:id>/changer_etat", methods=["POST"])
@login_required
@ecole_required
def changer_etat(id):
    """
    Changer l'état d'une classe
    Nécessite les droits admin + contexte école
    """
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole_id = get_current_ecole_id()
    classe = Classe.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    action = request.json.get("action")

    if action not in WORKFLOW:
        return jsonify({"error": "Action non valide!"}), 400
    
    trans = WORKFLOW[action]
    if classe.etat != trans["from"]:
        return jsonify({"error": f"L'état actuel est {classe.etat}, impossible d'appliquer {action}"}), 400
    
    classe.etat = trans["to"]
    db.session.commit()
    
    return jsonify({
        "etat": classe.etat,
        "message": f"État de la classe changé à {classe.etat}"
    })

@classes_bp.route("/update/<string:id>", methods=["POST"])
@login_required
@ecole_required
def update_classe(id):
    """
    Modifier une classe
    Nécessite les droits admin + contexte école
    """
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole_id = get_current_ecole_id()
    classe = Classe.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    # Contrôle d'état
    if classe.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de modifier cette classe, état non inactif!"}), 400
    
    data = request.form
    nouveau_code = data.get("code")
    nouveau_nom = data.get("nom")
    nouvel_effectif = int(data.get("effectif", 0))

    # Vérifier l'unicité du code (exclure la classe actuelle)
    existing_code = Classe.query.filter(
        Classe.code == nouveau_code, 
        Classe.ecole_id == ecole_id,
        Classe.id != id
    ).first()
    
    if existing_code:
        return jsonify({"error": "Ce code est déjà utilisé par une autre classe"}), 400

    # Vérifier l'unicité du nom (exclure la classe actuelle)
    existing_nom = Classe.query.filter(
        Classe.nom == nouveau_nom, 
        Classe.ecole_id == ecole_id,
        Classe.id != id
    ).first()
    
    if existing_nom:
        return jsonify({"error": "Ce nom est déjà utilisé par une autre classe"}), 400

    # Mise à jour
    classe.code = nouveau_code
    classe.nom = nouveau_nom
    classe.effectif = nouvel_effectif
    
    # Récupérer les enseignants sélectionnés (vérifier qu'ils appartiennent à l'école)
    enseignant_ids = request.form.getlist("enseignants[]")
    if enseignant_ids:
        enseignants = Enseignant.query.filter(
            Enseignant.id.in_(enseignant_ids),
            Enseignant.ecole_id == ecole_id
        ).all()
        classe.enseignants = enseignants
    else:
        classe.enseignants = []
    
    db.session.commit()
    
    return jsonify({
        "id": str(classe.id),
        "code": classe.code,
        "nom": classe.nom,
        "effectif": classe.effectif,
        "enseignants": [str(e.id) for e in classe.enseignants],
        "enseignants_nom": [f"{e.utilisateur.prenoms} {e.utilisateur.nom}" for e in classe.enseignants],
        "etat": classe.etat,
        "message": "Classe modifiée avec succès"
    })

@classes_bp.route("/delete/<string:id>", methods=["POST"])
@login_required
@ecole_required
def delete_classe(id):
    """
    Supprimer une classe
    Nécessite les droits admin + contexte école
    Vérifications complètes d'intégrité référentielle
    """
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole_id = get_current_ecole_id()
    
    try:
        # Récupérer la classe avec vérification d'école
        classe = Classe.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
        
        # ========== VÉRIFICATIONS PRÉ-SUPPRESSION ==========
        
        # 1. Contrôle sur l'état
        if classe.etat.lower() != 'inactif':
            return jsonify({
                "error": "Impossible de supprimer cette classe, état non inactif",
                "details": f"État actuel : {classe.etat}"
            }), 400
        
        # 2. Vérifier si la classe a des élèves
        eleves_count = len(classe.eleves)
        if eleves_count > 0:
            return jsonify({
                "error": "Impossible de supprimer cette classe, des élèves y sont inscrits",
                "details": f"Nombre d'élèves : {eleves_count}",
                "suggestion": "Transférez ou supprimez d'abord les élèves de cette classe"
            }), 400
        
        # 3. Vérifier si la classe a des matières associées
        if hasattr(classe, 'matieres') and len(classe.matieres) > 0:
            return jsonify({
                "error": "Impossible de supprimer cette classe, des matières y sont associées",
                "details": f"Nombre de matières : {len(classe.matieres)}",
                "suggestion": "Détachez d'abord les matières de cette classe"
            }), 400
        
        # 4. Vérifier si la classe a un emploi du temps
        if hasattr(classe, 'emplois_du_temps') and len(classe.emplois_du_temps) > 0:
            return jsonify({
                "error": "Impossible de supprimer cette classe, un emploi du temps y est associé",
                "details": f"Nombre d'emplois du temps : {len(classe.emplois_du_temps)}",
                "suggestion": "Supprimez d'abord l'emploi du temps de cette classe"
            }), 400
        
        # 5. Vérifier si la classe a des notes associées
        if hasattr(classe, 'notes') and len(classe.notes) > 0:
            return jsonify({
                "error": "Impossible de supprimer cette classe, des notes y sont associées",
                "details": f"Nombre de notes : {len(classe.notes)}",
                "suggestion": "Supprimez ou transférez d'abord les notes de cette classe"
            }), 400
        
        # 6. Vérifier si la classe a des évaluations
        if hasattr(classe, 'evaluations') and len(classe.evaluations) > 0:
            return jsonify({
                "error": "Impossible de supprimer cette classe, des évaluations y sont associées",
                "details": f"Nombre d'évaluations : {len(classe.evaluations)}",
                "suggestion": "Supprimez d'abord les évaluations de cette classe"
            }), 400
        
        # 7. Vérifier si la classe a des bulletins
        if hasattr(classe, 'bulletins') and len(classe.bulletins) > 0:
            return jsonify({
                "error": "Impossible de supprimer cette classe, des bulletins y sont associés",
                "details": f"Nombre de bulletins : {len(classe.bulletins)}",
                "suggestion": "Supprimez d'abord les bulletins de cette classe"
            }), 400
        
        # 8. Vérification générale avec gestion d'erreur
        dependencies = check_classe_dependencies(classe)
        if dependencies['has_dependencies']:
            return jsonify({
                "error": "Impossible de supprimer cette classe, des dépendances existent",
                "details": dependencies['message'],
                "dependencies": dependencies['details']
            }), 400
        
        # ========== TENTATIVE DE SUPPRESSION ==========
        
        # Sauvegarder les informations pour le message de confirmation
        classe_info = {
            "code": classe.code,
            "nom": classe.nom,
            "effectif": classe.effectif
        }
        
        # Supprimer la classe
        db.session.delete(classe)
        db.session.commit()
        
        # Journaliser la suppression
        current_app.logger.info(
            f"Classe supprimée - ID: {id}, Code: {classe_info['code']}, "
            f"Nom: {classe_info['nom']}, Par utilisateur: {current_user.id}"
        )
        
        return jsonify({
            "success": True,
            "message": f"Classe '{classe_info['nom']}' ({classe_info['code']}) supprimée avec succès",
            "deleted_classe": classe_info
        })
        
    except Exception as e:
        db.session.rollback()
        
        # Gestion spécifique des erreurs d'intégrité référentielle
        if "foreign key constraint" in str(e).lower():
            return jsonify({
                "error": "Impossible de supprimer cette classe en raison de contraintes de base de données",
                "details": "La classe est probablement utilisée dans d'autres parties du système",
                "suggestion": "Vérifiez les élèves, notes, bulletins et autres données associées"
            }), 400
        
        # Journaliser l'erreur
        current_app.logger.error(
            f"Erreur suppression classe ID {id} - Utilisateur: {current_user.id}, Erreur: {str(e)}",
            exc_info=True
        )
        
        return jsonify({
            "error": "Erreur lors de la suppression de la classe",
            "details": str(e)
        }), 500


def check_classe_dependencies(classe):
    """
    Vérifie les dépendances d'une classe de manière complète
    """
    dependencies = {
        'has_dependencies': False,
        'message': '',
        'details': {}
    }
    
    # Liste exhaustive des relations à vérifier
    relations_to_check = {
        'eleves': "élèves inscrits",
        'matieres': "matières associées", 
        'emplois_du_temps': "emplois du temps",
        'notes': "notes",
        'evaluations': "évaluations",
        'bulletins': "bulletins",
        'cours': "cours programmés",
        'absences': "absences enregistrées",
        'sanctions': "sanctions disciplinaires"
    }
    
    used_in = []
    
    for relation, nom_affichage in relations_to_check.items():
        try:
            if hasattr(classe, relation):
                count = len(getattr(classe, relation))
                if count > 0:
                    used_in.append(f"{count} {nom_affichage}")
                    dependencies['details'][relation] = count
        except Exception as e:
            # Si une relation n'existe pas ou erreur de comptage, on continue
            continue
    
    if used_in:
        dependencies['has_dependencies'] = True
        dependencies['message'] = f"Dépendances détectées : {', '.join(used_in)}"
    
    return dependencies


# Version alternative avec suppression en cascade contrôlée
@classes_bp.route("/delete/<string:id>/force", methods=["POST"])
@login_required
@ecole_required
def force_delete_classe(id):
    """
    Suppression forcée d'une classe (ADMIN ONLY)
    À utiliser avec extrême prudence - peut supprimer des données associées
    """
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole_id = get_current_ecole_id()
    
    try:
        classe = Classe.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
        
        # Vérifications de sécurité supplémentaires
        if classe.etat == "Actif":
            return jsonify({
                "error": "Impossible de forcer la suppression d'une classe active",
                "details": "Une classe active ne peut pas être supprimée, même en mode forcé"
            }), 400
        
        # Comptage des données associées pour confirmation
        dependencies = check_classe_dependencies(classe)
        
        if dependencies['has_dependencies']:
            # Demander une confirmation explicite
            confirmation = request.json.get('confirmation')
            if not confirmation:
                return jsonify({
                    "warning": "Cette classe a des données associées qui seront perdues",
                    "dependencies": dependencies['details'],
                    "confirmation_required": True,
                    "message": "Envoyez une confirmation explicite pour procéder"
                }), 400
            
            if confirmation != "JE CONFIRME LA SUPPRESSION AVEC PERTE DE DONNÉES":
                return jsonify({
                    "error": "Confirmation incorrecte",
                    "details": "La phrase de confirmation exacte est requise"
                }), 400
        
        # Journalisation de la suppression forcée
        current_app.logger.warning(
            f"SUPPRESSION FORCÉE CLASSE - ID: {id}, Code: {classe.code}, "
            f"Nom: {classe.nom}, Dépendances: {dependencies['details']}, "
            f"Par utilisateur: {current_user.id}"
        )
        
        # Suppression
        db.session.delete(classe)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Classe '{classe.nom}' supprimée forcément avec ses dépendances",
            "deleted_dependencies": dependencies['details'],
            "warning": "Des données associées ont été perdues"
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur suppression forcée classe ID {id} - Erreur: {str(e)}",
            exc_info=True
        )
        
        return jsonify({
            "error": "Erreur lors de la suppression forcée",
            "details": str(e)
        }), 500


# Route pour obtenir un rapport de suppression
@classes_bp.route("/delete/<string:id>/report", methods=["GET"])
@login_required
@ecole_required
def delete_classe_report(id):
    """
    Génère un rapport détaillé des impacts d'une suppression de classe
    """
    ecole_id = get_current_ecole_id()
    classe = Classe.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    # Rapport complet des dépendances
    dependencies = check_classe_dependencies(classe)
    
    report = {
        "classe": {
            "id": str(classe.id),
            "code": classe.code,
            "nom": classe.nom,
            "effectif": classe.effectif,
            "etat": classe.etat
        },
        "can_delete": (classe.etat.lower() == 'inactif' and not dependencies['has_dependencies']),
        "dependencies_report": dependencies,
        "actions_required": []
    }
    
    # Suggestions d'actions selon les dépendances
    if classe.etat.lower() != 'inactif':
        report["actions_required"].append("Changer l'état de la classe à 'Inactif'")
    
    if dependencies['has_dependencies']:
        for dep, count in dependencies['details'].items():
            report["actions_required"].append(
                f"Supprimer ou transférer les {count} {dep} associés"
            )
    
    return jsonify(report)

@classes_bp.route("/detail/<string:id>", methods=["GET"])
@login_required
@ecole_required
def detail_classe(id):
    """
    Détails d'une classe
    Vérifier qu'elle appartient à l'école courante
    """
    ecole_id = get_current_ecole_id()
    classe = Classe.query.filter_by(id=id, ecole_id=ecole_id).first_or_404()
    
    # Statistiques supplémentaires
    nb_eleves = len(classe.eleves)
    nb_garcons = len([e for e in classe.eleves if e.sexe == 'M'])
    nb_filles = len([e for e in classe.eleves if e.sexe == 'F'])
    
    return jsonify({
        "code": classe.code,
        "nom": classe.nom,
        "effectif": classe.effectif,
        "enseignants": [f"{e.utilisateur.prenoms} {e.utilisateur.nom}" for e in classe.enseignants],
        "etat": classe.etat,
        "statistiques": {
            "nb_eleves": nb_eleves,
            "nb_garcons": nb_garcons,
            "nb_filles": nb_filles,
            "taux_remplissage": (nb_eleves / classe.effectif * 100) if classe.effectif > 0 else 0
        }
    })

@classes_bp.route("/actives", methods=["GET"])
@login_required
@ecole_required
def get_classes_actives():
    """
    Récupérer les classes actives de l'école courante
    Utile pour les selects dans les formulaires
    """
    ecole_id = get_current_ecole_id()
    classes = Classe.query.filter_by(ecole_id=ecole_id, etat="Actif").order_by(Classe.nom).all()
    
    classes_list = [{
        "id": str(classe.id),
        "code": classe.code,
        "nom": classe.nom,
        "effectif": classe.effectif,
        "nb_eleves_actuels": len(classe.eleves)
    } for classe in classes]
    
    return jsonify(classes_list)

@classes_bp.route("/statistiques", methods=["GET"])
@login_required
@ecole_required
def statistiques_classes():
    """
    Statistiques des classes de l'école courante
    """
    ecole_id = get_current_ecole_id()
    classes = Classe.query.filter_by(ecole_id=ecole_id).all()
    
    stats = {
        "total_classes": len(classes),
        "classes_actives": len([c for c in classes if c.etat == "Actif"]),
        "classes_inactives": len([c for c in classes if c.etat == "Inactif"]),
        "classes_fermees": len([c for c in classes if c.etat == "Fermé"]),
        "effectif_total": sum(c.effectif for c in classes),
        "eleves_total": sum(len(c.eleves) for c in classes),
        "taux_remplissage_moyen": 0
    }
    
    if stats["effectif_total"] > 0:
        stats["taux_remplissage_moyen"] = (stats["eleves_total"] / stats["effectif_total"]) * 100
    
    return jsonify(stats)
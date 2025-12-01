from extensions import db
from ..models import Appreciations
from flask import Blueprint, render_template, request, jsonify, current_app,abort
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from ..utils import ecole_required, get_current_ecole_id,is_system_admin

appreciations_bp = Blueprint(
    "appreciations", __name__, url_prefix="/appreciations"
)

def is_admin():
    return getattr(current_user, "role", "").lower() in ["admin", "administrateur"]

def get_appreciation_secure(appreciation_id, ecole_id):
    """Récupère une appréciation en vérifiant son appartenance à l'école"""
    appreciation = Appreciations.query.filter_by(id=appreciation_id, ecole_id=ecole_id).first()
    if not appreciation:
        abort(404, "Appréciation non trouvée")
    return appreciation

@appreciations_bp.route("/add", methods=["POST"])
@login_required
@ecole_required
def add_appreciations():
    """
    Ajouter une appréciation avec échelle dynamique
    """
    ecole_id = get_current_ecole_id()
    
    libelle = request.form.get("libelle", "").strip()
    seuil_min = request.form.get("seuil_min", type=float)
    seuil_max = request.form.get("seuil_max", type=float)
    description = request.form.get("description", "").strip()
    echelle_max = request.form.get("echelle_max", type=float, default=20.0)

    # Validation des données
    if seuil_min is None or seuil_max is None:
        return jsonify({"error": "Les seuils min et max sont obligatoires."}), 400
    if not libelle:
        return jsonify({"error": "Le libellé est obligatoire."}), 400
    if not echelle_max or echelle_max <= 0:
        return jsonify({"error": "L'échelle maximale doit être positive."}), 400

    # Vérifier la cohérence des seuils
    if seuil_min >= seuil_max:
        return jsonify({"error": "Le seuil min doit être inférieur au seuil max."}), 400

    # Validation des plages selon l'échelle
    if seuil_min < 0:
        return jsonify({"error": f"Le seuil min ne peut pas être inférieur à 0."}), 400
    
    if seuil_max > echelle_max:
        return jsonify({"error": f"Le seuil max ne peut pas être supérieur à {echelle_max}."}), 400

    # CORRECTION : Vérification selon la contrainte unique (libelle + description + ecole_id)
    existing = Appreciations.query.filter_by(
        libelle=libelle,
        description=description,  # Ajout de la description dans la vérification
        ecole_id=ecole_id
    ).first()
    
    if existing:
        return jsonify({"error": "Une appréciation avec ce libellé et cette description existe déjà."}), 400

    # Vérification des chevauchements de seuils (même échelle)
    existing_overlap = Appreciations.query.filter(
        Appreciations.ecole_id == ecole_id,
        Appreciations.echelle_max == echelle_max,
        db.and_(
            Appreciations.seuil_min < seuil_max,
            Appreciations.seuil_max > seuil_min
        )
    ).first()
    
    if existing_overlap:
        return jsonify({
            "error": f"Ces seuils chevauchent l'appréciation existante : '{existing_overlap.libelle}' ({existing_overlap.seuil_min}-{existing_overlap.seuil_max})"
        }), 400

    # Création de l'appréciation
    appreciation = Appreciations(
        seuil_min=seuil_min, 
        seuil_max=seuil_max,
        libelle=libelle, 
        description=description, 
        etat="Inactif",
        ecole_id=ecole_id,
        echelle_max=echelle_max
    )
    db.session.add(appreciation)

    try:
        db.session.commit()
        return jsonify({
            "id": str(appreciation.id),
            "libelle": appreciation.libelle,
            "seuil_min": appreciation.seuil_min,
            "seuil_max": appreciation.seuil_max,
            "description": appreciation.description,
            "etat": appreciation.etat,
            "echelle_max": appreciation.echelle_max
        }), 200
    except IntegrityError as db_err:
        db.session.rollback()
        current_app.logger.error(f"Erreur SQL lors du commit: {db_err}", exc_info=True)
        
        # CORRECTION : Gestion spécifique de l'erreur de contrainte unique
        error_str = str(db_err)
        if "uq_libelle_description" in error_str:
            return jsonify({
                "error": "Cette combinaison libellé/description existe déjà dans votre école. Veuillez utiliser une description différente."
            }), 400
        elif "unique" in error_str.lower():
            return jsonify({
                "error": "Cette appréciation existe déjà avec les mêmes caractéristiques."
            }), 400
        else:
            return jsonify({"error": "Erreur base de données lors de l'ajout."}), 500
        
@appreciations_bp.route("/")
@login_required
def liste_appr():
    """
    Liste des appréciations avec filtrage par échelle
    """
    ecole_id = get_current_ecole_id()
    
    # Paramètres de recherche
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)
    echelle_filter = request.args.get("echelle", type=float)  # Filtre par échelle
    
    # Requête de base
    query = Appreciations.query.filter_by(ecole_id=ecole_id)
    
    # Filtrage par échelle si spécifié
    if echelle_filter:
        query = query.filter_by(echelle_max=echelle_filter)
    
    # Recherche
    if search:
        from sqlalchemy import or_
        conditions = [
            Appreciations.libelle.ilike(f"%{search}%"),
            Appreciations.description.ilike(f"%{search}%"),
            Appreciations.etat.ilike(f"%{search}%"),
            db.cast(Appreciations.seuil_min, db.String).ilike(f"%{search}%"),
            db.cast(Appreciations.seuil_max, db.String).ilike(f"%{search}%"),
            db.cast(Appreciations.echelle_max, db.String).ilike(f"%{search}%")
        ]
        query = query.filter(or_(*conditions))

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    appreciations = pagination.items

    # Rôle de l'utilisateur
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()

    # Récupérer les échelles disponibles pour le filtre
    echelles_disponibles = db.session.query(Appreciations.echelle_max).filter_by(
        ecole_id=ecole_id
    ).distinct().all()
    echelles_disponibles = [e[0] for e in echelles_disponibles]

    return render_template(
        "appreciations/liste_appr.html",
        appreciations=appreciations,
        pagination=pagination,
        search=search,
        per_page=per_page,
        user_role=user_role,
        ecole_id=ecole_id,
        echelle_filter=echelle_filter,
        echelles_disponibles=echelles_disponibles
    )
    
@appreciations_bp.route("/get/<string:id>", methods=["GET"])
@login_required
@ecole_required
def get_appreciation(id):
    """
    Récupérer une appréciation spécifique
    """
    ecole_id = get_current_ecole_id()
    appreciation = get_appreciation_secure(id, ecole_id)
    
    return jsonify({
        "id": str(appreciation.id),
        "libelle": appreciation.libelle,
        "seuil_min": appreciation.seuil_min,
        "seuil_max": appreciation.seuil_max,
        "description": appreciation.description,
        "etat": appreciation.etat,
        "echelle_max": appreciation.echelle_max  # Ajouté
    })


WORKFLOW = {
    "Activer": {"from": "Inactif", "to": "Actif"},
    "Abandonner": {"from": "Actif", "to": "Abandonné"}
}
    
@appreciations_bp.route("/<string:id>/changer_etat", methods=["POST"])
@login_required
@ecole_required
def changer_etat(id):
    """
    Changer l'état d'une appréciation
    Nécessite les droits admin + contexte école
    """
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403

    ecole_id = get_current_ecole_id()
    appreciation = get_appreciation_secure(id, ecole_id)  # ⬅️ SÉCURISÉ
    
    action = request.json.get("action")

    if action not in WORKFLOW:
        return jsonify({"error": "Action non valide!"}), 400

    trans = WORKFLOW[action]
    if appreciation.etat != trans["from"]:
        return jsonify({
            "error": f"L'état actuel est {appreciation.etat}, impossible d'appliquer {action}"
        }), 400

    appreciation.etat = trans["to"]
    db.session.commit()

    return jsonify({
        "message": f"État changé : {appreciation.etat}",
        "etat": appreciation.etat
    }), 200

# ⚠️ SUPPRIMEZ CETTE FONCTION EN DOUBLE - ELLE EXISTE DÉJÀ PLUS HAUT ⚠️
# @appreciations_bp.route("/add", methods=["POST"])
# @login_required
# @ecole_required
# def add_appreciations():
#     ... (supprimez tout ce bloc)

@appreciations_bp.route("/update/<string:id>", methods=["POST"])
@login_required
@ecole_required
def update_appreciation(id):
    """
    Modifier une appréciation avec gestion de l'échelle
    """
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole_id = get_current_ecole_id()
    appreciation = get_appreciation_secure(id, ecole_id)
    
    # Contrôle sur l'état
    if appreciation.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de modifier cette appréciation, état non inactif"}), 403
    
    data = request.form
    nouveau_libelle = data.get("libelle")
    nouveau_seuil_min = float(data.get("seuil_min"))
    nouveau_seuil_max = float(data.get("seuil_max"))
    nouvelle_description = data.get("description")

    # Vérifier la cohérence des seuils
    if nouveau_seuil_min >= nouveau_seuil_max:
        return jsonify({"error": "Le seuil min doit être inférieur au seuil max."}), 400

    # Validation selon l'échelle existante
    if nouveau_seuil_min < 0:
        return jsonify({"error": f"Le seuil min ne peut pas être inférieur à 0."}), 400
    
    if nouveau_seuil_max > appreciation.echelle_max:
        return jsonify({"error": f"Le seuil max ne peut pas être supérieur à {appreciation.echelle_max}."}), 400

    # CORRECTION : Vérification de la contrainte unique pour la modification
    existing_duplicate = Appreciations.query.filter(
        Appreciations.ecole_id == ecole_id,
        Appreciations.libelle == nouveau_libelle,
        Appreciations.description == nouvelle_description,
        Appreciations.id != id  # Exclure l'enregistrement actuel
    ).first()
    
    if existing_duplicate:
        return jsonify({
            "error": "Une autre appréciation avec ce libellé et cette description existe déjà."
        }), 400

    # Vérification des chevauchements (même échelle)
    existing_overlap = Appreciations.query.filter(
        Appreciations.ecole_id == ecole_id,
        Appreciations.echelle_max == appreciation.echelle_max,
        Appreciations.id != id,
        db.and_(
            Appreciations.seuil_min < nouveau_seuil_max,
            Appreciations.seuil_max > nouveau_seuil_min
        )
    ).first()
    
    if existing_overlap:
        return jsonify({
            "error": f"Ces seuils chevauchent l'appréciation existante : '{existing_overlap.libelle}' ({existing_overlap.seuil_min}-{existing_overlap.seuil_max})"
        }), 400

    # Mise à jour
    appreciation.libelle = nouveau_libelle
    appreciation.seuil_min = nouveau_seuil_min
    appreciation.seuil_max = nouveau_seuil_max
    appreciation.description = nouvelle_description
    
    try:
        db.session.commit()
        return jsonify({
            "id": appreciation.id,
            "libelle": appreciation.libelle,
            "seuil_min": appreciation.seuil_min,
            "seuil_max": appreciation.seuil_max,
            "description": appreciation.description,
            "etat": appreciation.etat,
            "echelle_max": appreciation.echelle_max
        })
    except IntegrityError as db_err:
        db.session.rollback()
        current_app.logger.error(f"Erreur SQL lors de la modification: {db_err}", exc_info=True)
        if "uq_libelle_description" in str(db_err):
            return jsonify({"error": "Cette combinaison libellé/description existe déjà pour votre école."}), 400
        return jsonify({"error": "Erreur base de données lors de la modification."}), 500

@appreciations_bp.route("/delete/<string:id>", methods=["POST"])
@login_required
@ecole_required
def delete_appreciation(id):
    """
    Supprimer une appréciation
    Nécessite les droits admin + contexte école
    """
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole_id = get_current_ecole_id()
    appreciation = get_appreciation_secure(id, ecole_id)  # ⬅️ SÉCURISÉ
    
    # Contrôle sur l'état
    if appreciation.etat.lower() != 'inactif':
        return jsonify({"error": "Impossible de supprimer cette appréciation, état non inactif"}), 403
    
    # ========== VÉRIFICATIONS D'INTÉGRITÉ RÉFÉRENTIELLE ==========
    
    # 1. Vérifier si l'appréciation est utilisée dans des notes
    if hasattr(appreciation, 'notes') and appreciation.notes.count() > 0:
        return jsonify({
            "error": "Impossible de supprimer cette appréciation, elle est utilisée dans des notes."
        }), 403
    
    # 2. Vérifier si l'appréciation est utilisée dans des bulletins
    if hasattr(appreciation, 'bulletins') and appreciation.bulletins.count() > 0:
        return jsonify({
            "error": "Impossible de supprimer cette appréciation, elle est utilisée dans des bulletins."
        }), 403
    
    # 3. Vérifier si l'appréciation est utilisée dans des évaluations
    if hasattr(appreciation, 'evaluations') and appreciation.evaluations.count() > 0:
        return jsonify({
            "error": "Impossible de supprimer cette appréciation, elle est utilisée dans des évaluations."
        }), 403
    
    # 4. Vérifier si l'appréciation est utilisée dans des compétences
    if hasattr(appreciation, 'competences') and appreciation.competences.count() > 0:
        return jsonify({
            "error": "Impossible de supprimer cette appréciation, elle est utilisée dans des compétences."
        }), 403
    
    # 5. Vérifier généralisée (si vous avez d'autres relations)
    try:
        # Compte toutes les relations possibles
        total_utilisations = 0
        relations = ['notes', 'bulletins', 'evaluations', 'competences', 'appreciations_eleves']
        
        for relation in relations:
            if hasattr(appreciation, relation):
                total_utilisations += getattr(appreciation, relation).count()
        
        if total_utilisations > 0:
            return jsonify({
                "error": f"Impossible de supprimer cette appréciation, elle est utilisée dans {total_utilisations} endroit(s) du système."
            }), 403
            
    except Exception as e:
        # En cas d'erreur dans le comptage, on est prudent et on empêche la suppression
        return jsonify({
            "error": "Impossible de vérifier les utilisations de cette appréciation. Suppression annulée par sécurité."
        }), 403
    
    # Si toutes les vérifications passent, on peut supprimer
    try:
        db.session.delete(appreciation)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Appréciation supprimée avec succès"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": f"Erreur lors de la suppression : {str(e)}"
        }), 500

@appreciations_bp.route("/detail/<string:id>", methods=["GET"])
@login_required
@ecole_required
def detail_appreciation(id):
    """
    Détails d'une appréciation
    """
    ecole_id = get_current_ecole_id()
    appreciation = get_appreciation_secure(id, ecole_id)
    
    return jsonify({
        "libelle": appreciation.libelle,
        "seuil_min": appreciation.seuil_min,
        "seuil_max": appreciation.seuil_max,
        "description": appreciation.description,
        "etat": appreciation.etat,
        "echelle_max": appreciation.echelle_max  # Ajouté
    })

@appreciations_bp.route("/actives", methods=["GET"])
@login_required
@ecole_required
def get_appreciations_actives():
    """
    Récupérer les appréciations actives de l'école courante
    Utile pour les selects dans les formulaires
    """
    ecole_id = get_current_ecole_id()
    appreciations = Appreciations.query.filter_by(
        ecole_id=ecole_id, 
        etat="Actif"
    ).order_by(Appreciations.seuil_min).all()
    
    appreciations_list = [{
        "id": str(appreciation.id),
        "libelle": appreciation.libelle,
        "seuil_min": appreciation.seuil_min,
        "seuil_max": appreciation.seuil_max,
        "description": appreciation.description
    } for appreciation in appreciations]
    
    return jsonify(appreciations_list)

@appreciations_bp.route("/pour-moyenne/<float:moyenne>", methods=["GET"])
@login_required
@ecole_required
def get_appreciation_pour_moyenne(moyenne):
    """
    Trouver l'appréciation correspondante à une moyenne donnée
    """
    ecole_id = get_current_ecole_id()
    appreciation = Appreciations.query.filter(
        Appreciations.ecole_id == ecole_id,
        Appreciations.etat == "Actif",
        Appreciations.seuil_min <= moyenne,
        Appreciations.seuil_max >= moyenne
    ).first()
    
    if appreciation:
        return jsonify({
            "id": str(appreciation.id),
            "libelle": appreciation.libelle,
            "description": appreciation.description
        })
    else:
        return jsonify({"error": "Aucune appréciation trouvée pour cette moyenne"}), 404

def convertir_seuils_entre_echelles(seuil_min, seuil_max, echelle_origine, echelle_destination):
    """Convertit des seuils d'une échelle à une autre"""
    if echelle_origine == 0:
        return 0, 0
    
    ratio = echelle_destination / echelle_origine
    return seuil_min * ratio, seuil_max * ratio

@appreciations_bp.route("/generer-echelle/<float:echelle_destination>", methods=["POST"])
@login_required
@ecole_required
def generer_echelle_automatique(echelle_destination):
    """Génère automatiquement des appréciations pour une nouvelle échelle"""
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
    
    ecole_id = get_current_ecole_id()
    
    # Récupérer les appréciations de référence (sur 20 par défaut)
    appreciations_reference = Appreciations.query.filter_by(
        ecole_id=ecole_id,
        echelle_max=20.0,
        etat="Actif"
    ).all()
    
    nouvelles_appreciations = []
    
    for app_ref in appreciations_reference:
        nouveau_min, nouveau_max = convertir_seuils_entre_echelles(
            app_ref.seuil_min, app_ref.seuil_max, 20.0, echelle_destination
        )
        
        nouvelle_appreciation = Appreciations(
            libelle=app_ref.libelle,
            seuil_min=nouveau_min,
            seuil_max=nouveau_max,
            description=f"{app_ref.description} (converti de 20 à {echelle_destination})",
            etat="Inactif",
            ecole_id=ecole_id,
            echelle_max=echelle_destination
        )
        nouvelles_appreciations.append(nouvelle_appreciation)
    
    try:
        db.session.add_all(nouvelles_appreciations)
        db.session.commit()
        return jsonify({
            "message": f"{len(nouvelles_appreciations)} appréciations générées pour l'échelle {echelle_destination}",
            "count": len(nouvelles_appreciations)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la génération: {str(e)}"}), 500
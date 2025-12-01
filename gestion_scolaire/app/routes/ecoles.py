import os
import uuid
import re
from flask import Blueprint, render_template, request, jsonify, current_app, flash, session, redirect, url_for
from extensions import db
from ..models import Ecole, Classe, Eleve, Enseignant, Matiere, Appreciations, Note, Paiement, Service
from flask_login import current_user, login_required
from ..utils import system_admin_required, get_current_ecole_id, ecole_required, admin_required
from werkzeug.utils import secure_filename
from gestion_login.gestion_login.models import Utilisateur

# Création du blueprint avec préfixe /admin/ecoles
ecoles_bp = Blueprint('ecoles', __name__, url_prefix='/admin/ecoles')

# Configuration pour l'upload des logos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'logos')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_phone_format(phone):
    """Valide le format international du numéro de téléphone"""
    if not phone:
        return True, None
    
    pattern = r'^\+[1-9]\d{1,14}$'
    cleaned_phone = phone.replace(' ', '').replace('-', '')
    
    if re.match(pattern, cleaned_phone):
        return True, cleaned_phone
    else:
        return False, "Format invalide. Utilisez le format international: +228 XX XX XX XX"

def validate_email_format(email):
    """Valide le format d'email"""
    if not email:
        return True, None
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, email
    else:
        return False, "Format d'email invalide"

def check_ecole_dependencies(ecole):
    """
    Vérifie les dépendances d'une école de manière complète
    """
    dependencies = {
        'has_dependencies': False,
        'message': '',
        'details': {}
    }
    
    relations_to_check = {
        'utilisateurs': "utilisateurs",
        'classes': "classes",
        'eleves': "élèves",
        'enseignants': "enseignants",
        'matieres': "matières",
        'appreciations': "appréciations",
        'notes': "notes",
        'bulletins': "bulletins"
    }
    
    used_in = []
    
    for relation, nom_affichage in relations_to_check.items():
        try:
            if hasattr(ecole, relation):
                count = len(getattr(ecole, relation))
                if count > 0:
                    used_in.append(f"{count} {nom_affichage}")
                    dependencies['details'][relation] = count
        except Exception:
            continue
    
    if used_in:
        dependencies['has_dependencies'] = True
        dependencies['message'] = f"Dépendances détectées : {', '.join(used_in)}"
    
    return dependencies

# ========== ROUTES POUR LES SIGNATURES ==========

@ecoles_bp.route('/signatures')
@login_required
@admin_required
@ecole_required
def admin_signatures():
    """Page d'administration des signatures"""
    ecole_id = get_current_ecole_id()
    ecole = Ecole.query.get_or_404(ecole_id)
    return render_template('admin_sign.html', ecole=ecole)

@ecoles_bp.route('/api/signatures/data')
@login_required
@admin_required
@ecole_required
def api_signatures_data():
    """API pour récupérer les données de l'école courante"""
    ecole_id = get_current_ecole_id()
    ecole = Ecole.query.get_or_404(ecole_id)
    
    # Classes de l'école courante
    classes = Classe.query.filter_by(ecole_id=ecole_id).all()
    
    # CORRECTION: Récupérer tous les utilisateurs non-ADMIN
    utilisateurs = Utilisateur.query.filter_by(ecole_id=ecole_id).filter(
        Utilisateur.role != 'ADMIN'
    ).all()
    
    classes_data = []
    for classe in classes:
        titulaire_data = None
        if classe.titulaire_id:
            # CORRECTION: Chercher d'abord l'enseignant, puis l'utilisateur associé
            enseignant = Enseignant.query.filter_by(
                id=classe.titulaire_id, 
                ecole_id=ecole_id
            ).first()
            if enseignant:
                utilisateur = Utilisateur.query.get(enseignant.utilisateur_id)
                if utilisateur:
                    titulaire_data = {
                        'id': str(utilisateur.id),  # CORRECTION: Utiliser l'ID utilisateur pour le frontend
                        'nom_complet': f"{utilisateur.prenoms} {utilisateur.nom}"
                    }
        
        classes_data.append({
            'id': str(classe.id),
            'nom': classe.nom,
            'niveau': getattr(classe, 'niveau', 'Non spécifié'),
            'titulaire': titulaire_data
        })
    
    enseignants_data = []
    for utilisateur in utilisateurs:
        # CORRECTION: Vérifier si un enseignant existe pour cet utilisateur
        enseignant = Enseignant.query.filter_by(utilisateur_id=utilisateur.id).first()
        
        enseignants_data.append({
            'id': str(utilisateur.id),  # CORRECTION: Utiliser l'ID utilisateur pour le frontend
            'nom_complet': f"{utilisateur.prenoms} {utilisateur.nom}",
            'matieres': getattr(enseignant, 'matieres_enseignees', []) if enseignant else [],
            'signature': getattr(enseignant, 'signature', '') if enseignant else ''
        })
    
    return jsonify({
        'success': True,
        'ecole': {
            'id': str(ecole.id),
            'nom': ecole.nom,
            'chef_etablissement_civilite': ecole.chef_etablissement_civilite or 'M.',
            'chef_etablissement_nom': ecole.chef_etablissement_nom or '',
            'chef_etablissement_titre': ecole.chef_etablissement_titre or "LE CHEF D'ÉTABLISSEMENT"
        },
        'classes': classes_data,
        'enseignants': enseignants_data
    })

@ecoles_bp.route('/api/signatures/chef', methods=['POST'])
@login_required
@admin_required
@ecole_required
def api_update_chef():
    """API pour mettre à jour le chef d'établissement"""
    ecole_id = get_current_ecole_id()
    ecole = Ecole.query.get_or_404(ecole_id)
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Données manquantes'}), 400
    
    try:
        ecole.chef_etablissement_civilite = data.get('civilite', 'M.')
        ecole.chef_etablissement_nom = data.get('nom', '')
        ecole.chef_etablissement_titre = data.get('titre', "LE CHEF D'ÉTABLISSEMENT")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Informations du chef d\'établissement mises à jour avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500

@ecoles_bp.route('/api/signatures/titulaire', methods=['POST'])
@login_required
@admin_required
@ecole_required
def api_update_titulaire():
    """API pour mettre à jour le titulaire d'une classe - VERSION FINALE CORRIGÉE"""
    ecole_id = get_current_ecole_id()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Données manquantes'}), 400
    
    classe_id = data.get('classe_id')
    utilisateur_id = data.get('enseignant_id')  # CORRECTION: C'est l'ID utilisateur qu'on reçoit
    
    if not classe_id:
        return jsonify({'success': False, 'error': 'ID de classe manquant'}), 400
    
    # Vérifier que la classe appartient à l'école courante
    classe = Classe.query.filter_by(id=classe_id, ecole_id=ecole_id).first()
    if not classe:
        return jsonify({'success': False, 'error': 'Classe non trouvée ou non autorisée'}), 404
    
    try:
        if utilisateur_id:
            # CORRECTION: Vérifier que l'utilisateur existe et appartient à l'école
            utilisateur = Utilisateur.query.filter_by(
                id=utilisateur_id, 
                ecole_id=ecole_id
            ).filter(
                Utilisateur.role != 'ADMIN'
            ).first()
            
            if not utilisateur:
                return jsonify({'success': False, 'error': 'Utilisateur non trouvé ou non autorisé'}), 404
            
            # CORRECTION: Chercher ou créer l'enseignant correspondant à cet utilisateur
            enseignant = Enseignant.query.filter_by(utilisateur_id=utilisateur.id).first()
            
            if not enseignant:
                # Créer un nouvel enseignant si il n'existe pas
                enseignant = Enseignant(
                    id=str(uuid.uuid4()),
                    utilisateur_id=utilisateur.id,
                    ecole_id=ecole_id,
                    matieres_enseignees=[],
                    signature=''
                )
                db.session.add(enseignant)
                db.session.flush()
            
            # Utiliser l'ID de l'enseignant pour la classe
            classe.titulaire_id = enseignant.id
            
        else:
            # Supprimer le titulaire
            classe.titulaire_id = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Titulaire de classe mis à jour avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur mise à jour titulaire: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500

# ========== ROUTES EXISTANTES POUR LA GESTION DES ÉCOLES (ADMIN SYSTÈME) ==========

@ecoles_bp.route("/")
@login_required
@system_admin_required
def liste_ecoles():
    """
    Liste toutes les écoles - réservé aux administrateurs système
    """
    search = request.args.get("search", "", type=str)
    per_page = request.args.get("per_page", 5, type=int)
    page = request.args.get("page", 1, type=int)

    query = Ecole.query

    if search:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Ecole.code.ilike(f"%{search}%"),
                Ecole.nom.ilike(f"%{search}%"),
                Ecole.localite.ilike(f"%{search}%"),
                Ecole.boite_postale.ilike(f"%{search}%"),
                Ecole.telephone1.ilike(f"%{search}%"),
                Ecole.telephone2.ilike(f"%{search}%"),
                Ecole.email.ilike(f"%{search}%"),
                Ecole.site.ilike(f"%{search}%"),
                Ecole.devise.ilike(f"%{search}%"),
                Ecole.dre.ilike(f"%{search}%"),
                Ecole.inspection.ilike(f"%{search}%"),
                Ecole.prefecture.ilike(f"%{search}%")
            )
        )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    ecoles = pagination.items
    user_role = (getattr(current_user, "role", "guest") or "guest").lower()

    return render_template("ecoles/list_eco.html",
                           ecoles=ecoles,
                           pagination=pagination,
                           search=search,
                           per_page=per_page,
                           user_role=user_role)

@ecoles_bp.route("/add", methods=["POST"])
@login_required
@system_admin_required
def add_ecole():
    """
    Ajouter une nouvelle école - réservé aux administrateurs système
    """
    try:
        # Si un code est fourni manuellement, on l'utilise. Sinon on génère un code unique.
        code = request.form.get("code")
        if not code:
            code = f"EC-{uuid.uuid4().hex[:6].upper()}"

        # Vérifier unicité du code
        if Ecole.query.filter_by(code=code).first():
            return jsonify({"error": "Cette école existe déjà"}), 400

        # Validation des données obligatoires
        nom = request.form.get("nom")
        if not nom:
            return jsonify({"error": "Le nom de l'école est obligatoire"}), 400

        # Validation des formats
        email = request.form.get("email")
        if email:
            is_valid, error = validate_email_format(email)
            if not is_valid:
                return jsonify({"error": error}), 400

        telephone1 = request.form.get("telephone1")
        if telephone1:
            is_valid, formatted_phone = validate_phone_format(telephone1)
            if not is_valid:
                return jsonify({"error": formatted_phone}), 400
            telephone1 = formatted_phone

        telephone2 = request.form.get("telephone2")
        if telephone2:
            is_valid, formatted_phone = validate_phone_format(telephone2)
            if not is_valid:
                return jsonify({"error": formatted_phone}), 400
            telephone2 = formatted_phone

        # Gestion du logo
        logo_filename = None
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            if allowed_file(logo_file.filename):
                filename = secure_filename(logo_file.filename)
                # Créer le dossier s'il n'existe pas
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                logo_path = os.path.join(UPLOAD_FOLDER, filename)
                logo_file.save(logo_path)
                logo_filename = filename
            else:
                return jsonify({"error": "Type de fichier logo non autorisé"}), 400

        # Création de l'école
        ecole = Ecole(
            code=code,
            nom=nom,
            localite=request.form.get("localite", ""),
            boite_postale=request.form.get("boite_postale", ""),
            dre=request.form.get("dre", ""),
            inspection=request.form.get("inspection", ""),
            prefecture=request.form.get("prefecture", ""),
            site=request.form.get("site", ""),
            email=email,
            devise=request.form.get("devise", ""),
            telephone1=telephone1,
            telephone2=telephone2,
            logo_filename=logo_filename,
            chef_etablissement_nom=request.form.get("chef_etablissement_nom", ""),
            chef_etablissement_titre=request.form.get("chef_etablissement_titre", "LE CHEF D'ÉTABLISSEMENT"),
            chef_etablissement_civilite=request.form.get("chef_etablissement_civilite", "M.")
        )

        db.session.add(ecole)
        db.session.commit()

        # Journalisation
        current_app.logger.info(
            f"École créée - ID: {ecole.id}, Code: {ecole.code}, "
            f"Nom: {ecole.nom}, Par utilisateur: {current_user.id}"
        )

        return jsonify({
            "message": "École ajoutée avec succès",
            "ecole_id": str(ecole.id)
        })

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur création école - Utilisateur: {current_user.id}, Erreur: {str(e)}",
            exc_info=True
        )
        return jsonify({"error": "Erreur serveur lors de l'ajout"}), 500

@ecoles_bp.route("/get/<string:id>", methods=["GET"])
@login_required
@system_admin_required
def get_ecole(id):
    """
    Récupérer une école spécifique - réservé aux administrateurs système
    """
    ecole = Ecole.query.get_or_404(id)
    return jsonify({
        "id": str(ecole.id),
        "code": ecole.code,
        "nom": ecole.nom,
        "localite": ecole.localite,
        "boite_postale": ecole.boite_postale,
        "inspection": ecole.inspection,
        "email": ecole.email,
        "site": ecole.site,
        "devise": ecole.devise,
        "dre": ecole.dre,
        "telephone1": ecole.telephone1,
        "telephone2": ecole.telephone2,
        "prefecture": ecole.prefecture,
        "logo_filename": ecole.logo_filename,
        "chef_etablissement_nom": ecole.chef_etablissement_nom,
        "chef_etablissement_titre": ecole.chef_etablissement_titre,
        "chef_etablissement_civilite": ecole.chef_etablissement_civilite
    })

@ecoles_bp.route("/update/<string:id>", methods=["POST"])
@login_required
@system_admin_required
def update_ecole(id):
    """
    Modifier une école - réservé aux administrateurs système
    """
    try:
        ecole = Ecole.query.get_or_404(id)
        
        # Validation des données obligatoires
        nom = request.form.get("nom")
        if not nom:
            return jsonify({"error": "Le nom de l'école est obligatoire"}), 400

        code = request.form.get("code")
        if not code:
            return jsonify({"error": "Le code de l'école est obligatoire"}), 400

        # Vérifier l'unicité du code (exclure l'école actuelle)
        existing_code = Ecole.query.filter(
            Ecole.code == code,
            Ecole.id != id
        ).first()
        if existing_code:
            return jsonify({"error": "Ce code est déjà utilisé par une autre école"}), 400

        # Validation des formats
        email = request.form.get("email")
        if email:
            is_valid, error = validate_email_format(email)
            if not is_valid:
                return jsonify({"error": error}), 400

        telephone1 = request.form.get("telephone1")
        if telephone1:
            is_valid, formatted_phone = validate_phone_format(telephone1)
            if not is_valid:
                return jsonify({"error": formatted_phone}), 400
            telephone1 = formatted_phone

        telephone2 = request.form.get("telephone2")
        if telephone2:
            is_valid, formatted_phone = validate_phone_format(telephone2)
            if not is_valid:
                return jsonify({"error": formatted_phone}), 400
            telephone2 = formatted_phone

        # Gestion du logo
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            if allowed_file(logo_file.filename):
                filename = secure_filename(logo_file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                logo_path = os.path.join(UPLOAD_FOLDER, filename)
                logo_file.save(logo_path)
                ecole.logo_filename = filename
            else:
                return jsonify({"error": "Type de fichier logo non autorisé"}), 400

        # Mise à jour des champs
        ecole.code = code
        ecole.nom = nom
        ecole.localite = request.form.get("localite", "")
        ecole.boite_postale = request.form.get("boite_postale", "")
        ecole.dre = request.form.get("dre", "")
        ecole.site = request.form.get("site", "")
        ecole.email = email
        ecole.inspection = request.form.get("inspection", "")
        ecole.prefecture = request.form.get("prefecture", "")
        ecole.telephone1 = telephone1
        ecole.telephone2 = telephone2
        ecole.devise = request.form.get("devise", "")
        ecole.chef_etablissement_nom = request.form.get("chef_etablissement_nom", "")
        ecole.chef_etablissement_titre = request.form.get("chef_etablissement_titre", "LE CHEF D'ÉTABLISSEMENT")
        ecole.chef_etablissement_civilite = request.form.get("chef_etablissement_civilite", "M.")

        db.session.commit()

        # Journalisation
        current_app.logger.info(
            f"École modifiée - ID: {ecole.id}, Code: {ecole.code}, "
            f"Nom: {ecole.nom}, Par utilisateur: {current_user.id}"
        )

        return jsonify({
            "id": str(ecole.id),
            "code": ecole.code,
            "nom": ecole.nom,
            "localite": ecole.localite,
            "boite_postale": ecole.boite_postale,
            "inspection": ecole.inspection,
            "email": ecole.email,
            "site": ecole.site,
            "devise": ecole.devise,
            "dre": ecole.dre,
            "telephone1": ecole.telephone1,
            "telephone2": ecole.telephone2,
            "prefecture": ecole.prefecture,
            "logo_filename": ecole.logo_filename,
            "chef_etablissement_nom": ecole.chef_etablissement_nom,
            "chef_etablissement_titre": ecole.chef_etablissement_titre,
            "chef_etablissement_civilite": ecole.chef_etablissement_civilite,
            "message": "École modifiée avec succès"
        })

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur modification école ID {id} - Utilisateur: {current_user.id}, Erreur: {str(e)}",
            exc_info=True
        )
        return jsonify({"error": "Erreur serveur lors de la modification"}), 500

@ecoles_bp.route("/delete/<string:id>", methods=["POST"])
@login_required
@system_admin_required
def delete_ecole(id):
    """
    Supprimer une école - réservé aux administrateurs système
    Vérifications complètes d'intégrité référentielle
    """
    try:
        ecole = Ecole.query.get_or_404(id)
        
        # ========== VÉRIFICATIONS PRÉ-SUPPRESSION ==========
        
        # 1. Vérifier si l'école a des utilisateurs
        if len(ecole.utilisateurs) > 0: 
            return jsonify({
                "error": "Impossible de supprimer cette école, des utilisateurs y sont associés",
                "details": f"Nombre d'utilisateurs : {len(ecole.utilisateurs)}",
                "suggestion": "Supprimez ou transférez d'abord les utilisateurs de cette école"
            }), 400
        
        # 2. Vérifier si l'école a des classes
        if len(ecole.classes) > 0:
            return jsonify({
                "error": "Impossible de supprimer cette école, des classes y sont associées",
                "details": f"Nombre de classes : {len(ecole.classes)}",
                "suggestion": "Supprimez d'abord les classes de cette école"
            }), 400
        
        # 3. Vérifier si l'école a des élèves
        if len(ecole.eleves) > 0:
            return jsonify({
                "error": "Impossible de supprimer cette école, des élèves y sont inscrits",
                "details": f"Nombre d'élèves : {len(ecole.eleves)}",
                "suggestion": "Supprimez ou transférez d'abord les élèves de cette école"
            }), 400
        
        # 4. Vérification générale des dépendances
        dependencies = check_ecole_dependencies(ecole)
        if dependencies['has_dependencies']:
            return jsonify({
                "error": "Impossible de supprimer cette école, des dépendances existent",
                "details": dependencies['message'],
                "dependencies": dependencies['details']
            }), 400
        
        # ========== SUPPRESSION ==========
        
        ecole_info = {
            "id": str(ecole.id),
            "code": ecole.code,
            "nom": ecole.nom
        }
        
        db.session.delete(ecole)
        db.session.commit()
        
        # Journalisation
        current_app.logger.warning(
            f"École supprimée - ID: {ecole.id}, Code: {ecole.code}, "
            f"Nom: {ecole.nom}, Par utilisateur: {current_user.id}"
        )
        
        return jsonify({
            "success": True,
            "message": f"École '{ecole.nom}' ({ecole.code}) supprimée avec succès",
            "deleted_ecole": ecole_info
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erreur suppression école ID {id} - Utilisateur: {current_user.id}, Erreur: {str(e)}",
            exc_info=True
        )
        
        # Gestion spécifique des erreurs d'intégrité référentielle
        if "foreign key constraint" in str(e).lower():
            return jsonify({
                "error": "Impossible de supprimer cette école en raison de contraintes de base de données",
                "details": "L'école est probablement utilisée dans d'autres parties du système"
            }), 400
        
        return jsonify({
            "error": "Erreur lors de la suppression de l'école",
            "details": str(e)
        }), 500

@ecoles_bp.route("/detail/<string:id>", methods=["GET"])
@login_required
@system_admin_required
def detail_ecole(id):
    """
    Détails d'une école - réservé aux administrateurs système
    """
    ecole = Ecole.query.get_or_404(id)
    
    # Statistiques supplémentaires
    stats = {
        "nb_utilisateurs": len(ecole.utilisateurs),
        "nb_classes": len(ecole.classes),
        "nb_eleves": len(ecole.eleves),
        "nb_enseignants": len(ecole.enseignants) if hasattr(ecole, 'enseignants') else 0,
        "nb_matieres": len(ecole.matieres) if hasattr(ecole, 'matieres') else 0
    }
    
    return jsonify({
        "code": ecole.code,
        "nom": ecole.nom,
        "localite": ecole.localite,
        "boite_postale": ecole.boite_postale,
        "inspection": ecole.inspection,
        "email": ecole.email,
        "site": ecole.site,
        "devise": ecole.devise,
        "dre": ecole.dre,
        "telephone1": ecole.telephone1,
        "telephone2": ecole.telephone2,
        "prefecture": ecole.prefecture,
        "logo_filename": ecole.logo_filename,
        "chef_etablissement_nom": ecole.chef_etablissement_nom,
        "chef_etablissement_titre": ecole.chef_etablissement_titre,
        "chef_etablissement_civilite": ecole.chef_etablissement_civilite,
        "statistiques": stats
    })

@ecoles_bp.route("/statistiques", methods=["GET"])
@login_required
@system_admin_required
def statistiques_ecoles():
    """
    Statistiques globales sur toutes les écoles
    """
    ecoles = Ecole.query.all()
    
    stats_globales = {
        "total_ecoles": len(ecoles),
        "total_utilisateurs": sum(len(ecole.utilisateurs) for ecole in ecoles),
        "total_classes": sum(len(ecole.classes) for ecole in ecoles),
        "total_eleves": sum(len(ecole.eleves) for ecole in ecoles),
        "total_enseignants": sum(len(ecole.enseignants) for ecole in ecoles if hasattr(ecole, 'enseignants'))
    }
    
    stats_par_ecole = []
    for ecole in ecoles:
        stats_par_ecole.append({
            "ecole": {
                "id": str(ecole.id),
                "code": ecole.code,
                "nom": ecole.nom
            },
            "utilisateurs": len(ecole.utilisateurs),
            "classes": len(ecole.classes),
            "eleves": len(ecole.eleves),
            "enseignants": len(ecole.enseignants) if hasattr(ecole, 'enseignants') else 0
        })
    
    return jsonify({
        "globales": stats_globales,
        "par_ecole": stats_par_ecole
    })

# ========== ROUTES POUR LA SÉLECTION D'ÉCOLE ==========

@ecoles_bp.route('/select-ecole', methods=['POST'])
@login_required
@system_admin_required
def select_ecole():
    """
    Sélection d'une école par l'admin système
    """
    ecole_id = request.json.get('ecole_id')
    
    if ecole_id:
        # Vérifier que l'école existe
        ecole = Ecole.query.get(ecole_id)
        if not ecole:
            return jsonify({'success': False, 'error': 'École non trouvée'}), 404
        
        session['selected_ecole_id'] = ecole_id
        flash(f'École sélectionnée : {ecole.nom}', 'success')
    else:
        session.pop('selected_ecole_id', None)
        flash('Aucune école sélectionnée', 'info')
    
    return jsonify({'success': True})

# ========== ROUTES AVEC CONTEXTE D'ÉCOLE SPÉCIFIQUE ==========

@ecoles_bp.route('/ma-ecole/dashboard')
@login_required
@ecole_required
def dashboard_ecole_courante():
    """
    Dashboard de l'école actuellement sélectionnée
    """
    ecole_id = get_current_ecole_id()
    ecole = Ecole.query.get_or_404(ecole_id)
    
    stats = {
        'nb_eleves': len(ecole.eleves),
        'nb_classes': len(ecole.classes),
        'nb_utilisateurs': len(ecole.utilisateurs),
        'nb_eleves_actifs': len([e for e in ecole.eleves if e.etat == 'Actif']),
        'nb_eleves_inactifs': len([e for e in ecole.eleves if e.etat == 'Inactif'])
    }
    
    return render_template('admin/dashboard_ecole.html', ecole=ecole, stats=stats)

@ecoles_bp.route('/ma-ecole/utilisateurs')
@login_required
@ecole_required
def gestion_utilisateurs_ecole_courante():
    """
    Gestion des utilisateurs de l'école actuellement sélectionnée
    """
    ecole_id = get_current_ecole_id()
    ecole = Ecole.query.get_or_404(ecole_id)
    utilisateurs = Utilisateur.query.filter_by(ecole_id=ecole_id).all()
    
    return render_template('admin/utilisateurs_ecole.html', 
                         ecole=ecole, 
                         utilisateurs=utilisateurs)

@ecoles_bp.route('/ma-ecole/rapport')
@login_required
@ecole_required
@system_admin_required
def rapport_ecole_courante():
    """
    Rapport détaillé de l'école actuellement sélectionnée
    """
    ecole_id = get_current_ecole_id()
    ecole = Ecole.query.get_or_404(ecole_id)
    
    classes = ecole.classes.all()
    eleves_par_classe = []
    
    for classe in classes:
        eleves_par_classe.append({
            'classe': classe,
            'nb_eleves': len(classe.eleves),
            'nb_garcons': len([e for e in classe.eleves if e.sexe == 'M']),
            'nb_filles': len([e for e in classe.eleves if e.sexe == 'F'])
        })
    
    return render_template('admin/rapport_ecole.html', 
                         ecole=ecole, 
                         eleves_par_classe=eleves_par_classe)

@ecoles_bp.route("/test")
def test_route():
    return jsonify({"message": "Blueprint ecoles fonctionne!"}), 200
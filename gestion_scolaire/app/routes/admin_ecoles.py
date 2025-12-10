from flask import Blueprint, render_template, request, flash, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from app.models import Ecole, Utilisateur, Classe
from ..utils import system_admin_required, get_current_ecole_id, ecole_required, admin_required
from extensions import db
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

admin_ecoles_bp = Blueprint('admin_ecoles', __name__, url_prefix='/admin')

# ========== ROUTES POUR LES SIGNATURES (FILTRÉES PAR ÉCOLE) ==========

@admin_ecoles_bp.route('/signatures')
@login_required
@admin_required
@ecole_required
def admin_signatures():
    """Page d'administration des signatures - réservée aux admins avec contexte d'école"""
    ecole_id = get_current_ecole_id()
    ecole = Ecole.query.get_or_404(ecole_id)
    
    return render_template('admin_sign.html', ecole=ecole)

@admin_ecoles_bp.route('/api/signatures/data')
@login_required
@admin_required
@ecole_required
def api_signatures_data():
    """
    API pour récupérer les données de signature de l'école courante
    AVEC GESTION DES DONNÉES MANQUANTES
    """
    try:
        ecole_id = get_current_ecole_id()
        ecole = Ecole.query.get_or_404(ecole_id)
        
        # VÉRIFICATION CRITIQUE : S'assurer que les champs du chef d'établissement ont des valeurs par défaut
        chef_nom = ecole.chef_etablissement_nom or "NON DÉFINI"
        chef_titre = ecole.chef_etablissement_titre or "LE CHEF D'ÉTABLISSEMENT"
        chef_civilite = ecole.chef_etablissement_civilite or "M."
        
        print(f"🔍 Données chef établissement - Nom: {chef_nom}, Titre: {chef_titre}, Civilité: {chef_civilite}")
        
        # Récupérer les classes de l'école courante SEULEMENT
        classes = Classe.query.filter_by(ecole_id=ecole_id).all()
        
        # Récupérer les enseignants de l'école courante SEULEMENT
        enseignants = Utilisateur.query.filter_by(
            ecole_id=ecole_id, 
            role='ENSEIGNANT'
        ).all()
        
        # Préparer les données des classes
        classes_data = []
        for classe in classes:
            titulaire_data = None
            if classe.titulaire_id:
                titulaire = Utilisateur.query.filter_by(
                    id=classe.titulaire_id, 
                    ecole_id=ecole_id
                ).first()
                if titulaire:
                    titulaire_data = {
                        'id': str(titulaire.id),
                        'nom_complet': f"{titulaire.prenom} {titulaire.nom}"
                    }
            
            classes_data.append({
                'id': str(classe.id),
                'nom': classe.nom,
                'niveau': classe.niveau or 'Non spécifié',
                'titulaire': titulaire_data
            })
        
        # Préparer les données des enseignants
        enseignants_data = []
        for enseignant in enseignants:
            enseignants_data.append({
                'id': str(enseignant.id),
                'nom_complet': f"{enseignant.prenom} {enseignant.nom}",
                'matieres': getattr(enseignant, 'matieres_enseignees', []) or [],
                'signature': getattr(enseignant, 'signature', '') or ''
            })
        
        response_data = {
            'success': True,
            'ecole': {
                'id': str(ecole.id),
                'nom': ecole.nom,
                'chef_etablissement_civilite': chef_civilite,
                'chef_etablissement_nom': chef_nom,
                'chef_etablissement_titre': chef_titre
            },
            'classes': classes_data,
            'enseignants': enseignants_data,
            'statut_chef': 'défini' if ecole.chef_etablissement_nom and ecole.chef_etablissement_nom.strip() != '' else 'non défini'
        }
        
        print(f"✅ Données envoyées - Chef: {response_data['ecole']['chef_etablissement_nom']}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Erreur dans api_signatures_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur lors du chargement des données: {str(e)}'
        }), 500

@admin_ecoles_bp.route('/api/signatures/chef', methods=['POST'])
@login_required
@admin_required
@ecole_required
def api_update_chef():
    """
    VERSION DE TEST SIMPLIFIÉE pour identifier l'erreur
    """
    try:
        print("🔍 Début de api_update_chef")
        
        # DEBUG: Vérifier les données reçues
        if not request.is_json:
            print("❌ La requête n'est pas en JSON")
            return jsonify({'success': False, 'error': 'Format JSON requis'}), 400
        
        data = request.get_json()
        print(f"🔍 Données JSON reçues: {data}")
        
        ecole_id = get_current_ecole_id()
        print(f"🔍 ID école courante: {ecole_id}")
        
        ecole = Ecole.query.get(ecole_id)
        if not ecole:
            print(f"❌ École non trouvée: {ecole_id}")
            return jsonify({'success': False, 'error': 'École non trouvée'}), 404
        
        print(f"🔍 École trouvée: {ecole.nom}")
        
        # Validation minimaliste
        nom = data.get('nom', '').strip()
        if not nom:
            print("❌ Nom vide")
            return jsonify({'success': False, 'error': 'Nom requis'}), 400
        
        # Mise à jour directe (pas de validation complexe)
        ecole.chef_etablissement_civilite = data.get('civilite', 'M.').strip()
        ecole.chef_etablissement_nom = nom
        ecole.chef_etablissement_titre = data.get('titre', "LE CHEF D'ÉTABLISSEMENT").strip()
        
        # DEBUG: Afficher ce qu'on va sauvegarder
        print(f"🔍 Valeurs à sauvegarder:")
        print(f"  - Civilité: {ecole.chef_etablissement_civilite}")
        print(f"  - Nom: {ecole.chef_etablissement_nom}")
        print(f"  - Titre: {ecole.chef_etablissement_titre}")
        
        try:
            db.session.commit()
            print("✅ Commit réussi")
        except Exception as commit_error:
            print(f"❌ Erreur lors du commit: {str(commit_error)}")
            db.session.rollback()
            return jsonify({
                'success': False, 
                'error': f'Erreur base de données: {str(commit_error)}'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Chef mis à jour avec succès'
        })
        
    except Exception as e:
        print(f"❌ Erreur globale dans api_update_chef: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500

@admin_ecoles_bp.route('/api/signatures/titulaire', methods=['POST'])
@login_required
@admin_required
@ecole_required
def api_update_titulaire():
    """
    API pour mettre à jour le titulaire d'une classe
    AVEC VÉRIFICATIONS DE SÉCURITÉ POUR L'ÉCOLE
    """
    try:
        ecole_id = get_current_ecole_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        classe_id = data.get('classe_id')
        enseignant_id = data.get('enseignant_id')
        
        if not classe_id:
            return jsonify({'success': False, 'error': 'ID de classe manquant'}), 400
        
        # Vérifier que la classe appartient à l'école courante
        classe = Classe.query.filter_by(id=classe_id, ecole_id=ecole_id).first()
        if not classe:
            return jsonify({'success': False, 'error': 'Classe non trouvée ou non autorisée'}), 404
        
        # Si un enseignant est spécifié, vérifier qu'il appartient à l'école courante
        if enseignant_id:
            enseignant = Utilisateur.query.filter_by(
                id=enseignant_id, 
                ecole_id=ecole_id,  # FILTRE IMPORTANT : même école
                role='ENSEIGNANT'
            ).first()
            if not enseignant:
                return jsonify({'success': False, 'error': 'Enseignant non trouvé ou non autorisé'}), 404
        
        classe.titulaire_id = enseignant_id if enseignant_id else None
        db.session.commit()
        
        print(f"✅ Titulaire mis à jour - Classe: {classe.nom}, Titulaire ID: {enseignant_id or 'Aucun'}")
        
        return jsonify({
            'success': True,
            'message': 'Titulaire de classe mis à jour avec succès'
        })
        
    except IntegrityError as e:
        db.session.rollback()
        print(f"❌ Erreur d'intégrité lors de la mise à jour du titulaire: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur de base de données lors de la mise à jour'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de la mise à jour du titulaire: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500

@admin_ecoles_bp.route('/api/signatures/fix-chef', methods=['POST'])
@login_required
@admin_required
@ecole_required
def api_fix_chef_etablissement():
    """
    API pour corriger les données manquantes du chef d'établissement
    """
    try:
        ecole_id = get_current_ecole_id()
        ecole = Ecole.query.get_or_404(ecole_id)
        
        # Vérifier et corriger les champs manquants
        corrections = []
        
        if not ecole.chef_etablissement_nom or ecole.chef_etablissement_nom.strip() == '':
            # Essayer de trouver un enseignant comme chef par défaut
            enseignant_chef = Utilisateur.query.filter_by(
                ecole_id=ecole_id, 
                role='ENSEIGNANT'
            ).first()
            
            if enseignant_chef:
                ecole.chef_etablissement_nom = f"{enseignant_chef.prenom} {enseignant_chef.nom}"
                corrections.append(f"Nom du chef défini sur: {enseignant_chef.prenom} {enseignant_chef.nom}")
            else:
                ecole.chef_etablissement_nom = "CHEF À DÉFINIR"
                corrections.append("Nom du chef défini sur valeur par défaut")
        
        if not ecole.chef_etablissement_titre or ecole.chef_etablissement_titre.strip() == '':
            ecole.chef_etablissement_titre = "LE CHEF D'ÉTABLISSEMENT"
            corrections.append("Titre du chef défini sur valeur par défaut")
        
        if not ecole.chef_etablissement_civilite or ecole.chef_etablissement_civilite.strip() == '':
            ecole.chef_etablissement_civilite = "M."
            corrections.append("Civilité du chef définie sur M.")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Données du chef d\'établissement corrigées avec succès',
            'corrections': corrections,
            'chef': {
                'nom': ecole.chef_etablissement_nom,
                'titre': ecole.chef_etablissement_titre,
                'civilite': ecole.chef_etablissement_civilite
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de la correction automatique du chef: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la correction: {str(e)}'
        }), 500

# ========== ROUTES EXISTANTES POUR LES ÉCOLES (inchangées) ==========

@admin_ecoles_bp.route('/ecoles')
@login_required
@system_admin_required
def liste_ecoles():
    """
    Liste toutes les écoles - réservé aux administrateurs système
    """
    ecoles = Ecole.query.all()
    return render_template('admin/ecoles.html', ecoles=ecoles)

@admin_ecoles_bp.route('/select-ecole', methods=['POST'])
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

@admin_ecoles_bp.route('/ecoles/inscription', methods=['GET', 'POST'])
@login_required
@system_admin_required
def inscription_ecole():
    """
    Création d'une nouvelle école - réservé aux administrateurs système
    """
    if request.method == 'POST':
        try:
            # Validation des données
            code = request.form['code']
            nom = request.form['nom']
            email = request.form['email']
            telephone1 = request.form['telephone1']
            
            # Vérifier l'unicité du code
            if Ecole.query.filter_by(code=code).first():
                flash('Ce code d\'école existe déjà', 'error')
                return render_template('admin/inscription_ecole.html')
            
            # Vérifier l'unicité du nom
            if Ecole.query.filter_by(nom=nom).first():
                flash('Ce nom d\'école existe déjà', 'error')
                return render_template('admin/inscription_ecole.html')
            
            # Création de l'école
            ecole = Ecole(
                code=code,
                nom=nom,
                email=email,
                telephone1=telephone1,
                localite=request.form.get('localite', ''),
                site=request.form.get('site', ''),
                telephone2=request.form.get('telephone2', ''),
                dre=request.form.get('dre', ''),
                inspection=request.form.get('inspection', ''),
                boite_postale=request.form.get('boite_postale', ''),
                devise=request.form.get('devise', ''),
                prefecture=request.form.get('prefecture', ''),
            )
            
            db.session.add(ecole)
            db.session.commit()
            
            flash(f'École "{nom}" créée avec succès', 'success')
            return redirect(url_for('admin_ecoles.liste_ecoles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de l\'école : {str(e)}', 'error')
            return render_template('admin/inscription_ecole.html')
    
    return render_template('admin/inscription_ecole.html')

@admin_ecoles_bp.route('/ecoles/<int:ecole_id>/edit', methods=['GET', 'POST'])
@login_required
@system_admin_required
def edit_ecole(ecole_id):
    """
    Modification d'une école - réservé aux administrateurs système
    """
    ecole = Ecole.query.get_or_404(ecole_id)
    
    if request.method == 'POST':
        try:
            # Validation des données
            code = request.form['code']
            nom = request.form['nom']
            email = request.form['email']
            telephone1 = request.form['telephone1']
            
            # Vérifier l'unicité du code (exclure l'école actuelle)
            existing_code = Ecole.query.filter(Ecole.code == code, Ecole.id != ecole_id).first()
            if existing_code:
                flash('Ce code d\'école est déjà utilisé par une autre école', 'error')
                return render_template('admin/edit_ecole.html', ecole=ecole)
            
            # Vérifier l'unicité du nom (exclure l'école actuelle)
            existing_nom = Ecole.query.filter(Ecole.nom == nom, Ecole.id != ecole_id).first()
            if existing_nom:
                flash('Ce nom d\'école est déjà utilisé par une autre école', 'error')
                return render_template('admin/edit_ecole.html', ecole=ecole)
            
            # Mise à jour de l'école
            ecole.code = code
            ecole.nom = nom
            ecole.email = email
            ecole.telephone1 = telephone1
            ecole.localite = request.form.get('localite', '')
            ecole.site = request.form.get('site', '')
            ecole.telephone2 = request.form.get('telephone2', '')
            ecole.dre = request.form.get('dre', '')
            ecole.inspection = request.form.get('inspection', '')
            ecole.boite_postale = request.form.get('boite_postale', '')
            ecole.devise = request.form.get('devise', '')
            ecole.prefecture = request.form.get('prefecture', '')
            
            db.session.commit()
            
            flash(f'École "{nom}" modifiée avec succès', 'success')
            return redirect(url_for('admin_ecoles.liste_ecoles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification de l\'école : {str(e)}', 'error')
            return render_template('admin/edit_ecole.html', ecole=ecole)
    
    return render_template('admin/edit_ecole.html', ecole=ecole)

@admin_ecoles_bp.route('/ecoles/<int:ecole_id>/delete', methods=['POST'])
@login_required
@system_admin_required
def delete_ecole(ecole_id):
    """
    Suppression d'une école - réservé aux administrateurs système
    """
    ecole = Ecole.query.get_or_404(ecole_id)
    
    try:
        # Vérifier s'il y a des données associées (élèves, classes, etc.)
        if ecole.eleves.count() > 0:
            flash('Impossible de supprimer cette école : des élèves y sont associés', 'error')
            return redirect(url_for('admin_ecoles.liste_ecoles'))
        
        if ecole.classes.count() > 0:
            flash('Impossible de supprimer cette école : des classes y sont associées', 'error')
            return redirect(url_for('admin_ecoles.liste_ecoles'))
        
        nom_ecole = ecole.nom
        db.session.delete(ecole)
        db.session.commit()
        
        flash(f'École "{nom_ecole}" supprimée avec succès', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'école : {str(e)}', 'error')
    
    return redirect(url_for('admin_ecoles.liste_ecoles'))

@admin_ecoles_bp.route('/ecoles/<int:ecole_id>/utilisateurs')
@login_required
@system_admin_required
def gestion_utilisateurs_ecole(ecole_id):
    """
    Gestion des utilisateurs d'une école spécifique
    """
    ecole = Ecole.query.get_or_404(ecole_id)
    utilisateurs = Utilisateur.query.filter_by(ecole_id=ecole_id).all()
    
    return render_template('admin/utilisateurs_ecole.html', 
                         ecole=ecole, 
                         utilisateurs=utilisateurs)

@admin_ecoles_bp.route('/ecoles/ma-ecole/utilisateurs')
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

@admin_ecoles_bp.route('/ecoles/statistiques')
@login_required
@system_admin_required
def statistiques_ecoles():
    """
    Statistiques globales sur toutes les écoles
    """
    ecoles = Ecole.query.all()
    
    stats = []
    for ecole in ecoles:
        stat_ecole = {
            'ecole': ecole,
            'nb_eleves': ecole.eleves.count(),
            'nb_classes': ecole.classes.count(),
            'nb_utilisateurs': ecole.utilisateurs.count()
        }
        stats.append(stat_ecole)
    
    return render_template('admin/statistiques_ecoles.html', stats=stats)

# ========== ROUTES AVEC CONTEXTE D'ÉCOLE SPÉCIFIQUE ==========

@admin_ecoles_bp.route('/ecoles/ma-ecole/dashboard')
@login_required
@ecole_required
def dashboard_ecole_courante():
    """
    Dashboard de l'école actuellement sélectionnée
    """
    ecole_id = get_current_ecole_id()
    ecole = Ecole.query.get_or_404(ecole_id)
    
    stats = {
        'nb_eleves': ecole.eleves.count(),
        'nb_classes': ecole.classes.count(),
        'nb_utilisateurs': ecole.utilisateurs.count(),
        'nb_eleves_actifs': ecole.eleves.filter_by(etat='Actif').count(),
        'nb_eleves_inactifs': ecole.eleves.filter_by(etat='Inactif').count()
    }
    
    return render_template('admin/dashboard_ecole.html', ecole=ecole, stats=stats)

@admin_ecoles_bp.route('/ecoles/ma-ecole/rapport')
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
            'nb_eleves': classe.eleves.count(),
            'nb_garcons': classe.eleves.filter_by(sexe='M').count(),
            'nb_filles': classe.eleves.filter_by(sexe='F').count()
        })
    
    return render_template('admin/rapport_ecole.html', 
                         ecole=ecole, 
                         eleves_par_classe=eleves_par_classe)


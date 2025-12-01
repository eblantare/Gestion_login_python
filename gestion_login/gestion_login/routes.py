import os
import re
import hashlib
from uuid import UUID
from math import ceil
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, current_app, jsonify
from flask_login import login_user, current_user, login_required
from flask_mail import Message
from extensions import db, login_manager, mail
from .models import Utilisateur, ALLOWED_EXTENSIONS
from gestion_scolaire.app.models import Ecole
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/auth_static"
)

# === CONFIGURATIONS ===
LOCK_WINDOW_MINUTES = 45
MAX_FAILED_ATTEMPTS = 5
ADMIN_ROLE = {"administrateur", "admin"}
serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY", "fallback_secret"))
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "upload")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === DÉCORATEURS POUR LES PERMISSIONS ===
def ecole_required(f):
    """Vérifie que l'utilisateur a une école assignée ou est admin système"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.ecole_id and not current_user.is_system_admin:
            flash("Vous n'êtes assigné à aucune école. Contactez l'administrateur.", "warning")
            return redirect(url_for('auth.home'))
        
        return f(*args, **kwargs)
    return wrapper

def system_admin_required(f):
    """Nécessite d'être admin système"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_system_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    """Nécessite des droits d'administration"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        
        # CORRECTION : Permettre aux admins système ET aux admins d'école
        user_role = getattr(current_user, 'role', '').lower()
        is_admin_system = getattr(current_user, 'is_system_admin', False)
        
        if not (is_admin_system or user_role in ['admin', 'administrateur']):
            abort(403)
            
        return f(*args, **kwargs)
    return wrapper

# === FONCTIONS UTILITAIRES ===
def password_is_strong(password):
    pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$'
    return re.match(pattern, password) is not None

def email_is_valid(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def phone_is_valid(telephone):
    pattern = r'^\+?\d{8,15}$'
    return re.match(pattern, telephone) is not None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def utcnow():
    return datetime.now(timezone.utc)

def to_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@login_manager.user_loader
def load_user(user_id):
    try:
        return Utilisateur.query.get(UUID(user_id))
    except ValueError:
        return None

# === ROUTES D'AUTHENTIFICATION ===
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Veuillez renseigner le nom d'utilisateur et le mot de passe", "danger")
            return redirect(url_for("auth.login"))

        user = Utilisateur.query.filter_by(username=username).first()
        if user is None:
            flash("Nom d'utilisateur ou mot de passe incorrect ❌", "danger")
            return render_template("auth/login.html")
        
        user.locked_until = to_utc(user.locked_until)
        now = utcnow()

        if user.locked_until and user.locked_until <= now:
            user.failed_attempts = 0
            user.locked_until = None
            db.session.commit()
        
        if user.locked_until and user.locked_until > now:
            until = user.locked_until.strftime("%d/%m/%Y %H:%M")
            flash(f"Votre compte est bloqué jusqu'à {until}. Veuillez contacter l'administrateur.", "danger")
            return render_template("auth/login.html")
        
        if user.check_password(password):
            user.failed_attempts = 0
            user.locked_until = None
            db.session.commit()
            login_user(user)
            flash("Connexion réussie ✅", "success")
            return redirect(url_for("auth.home"))
        else:
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCK_WINDOW_MINUTES)
                flash(f"Votre compte est bloqué. Attendez {LOCK_WINDOW_MINUTES} minutes.", "danger")
            else:
                flash(f"Mot de passe incorrect ❌ (tentative {user.failed_attempts}/{MAX_FAILED_ATTEMPTS})", "danger")
            db.session.commit()
            return render_template("auth/login.html")
    
    return render_template("auth/login.html")

@auth_bp.route("/home")
@login_required
def home():
    return render_template("auth/home.html", username=current_user.username)

@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("auth/dashboard.html", username=current_user.username)

@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Déconnecté avec succès.", "info")
    return redirect(url_for("auth.login"))

# === GESTION DES UTILISATEURS ===
@auth_bp.route("/register", methods=["GET", "POST"])
@login_required
@ecole_required
@admin_required
def register():
    # CORRECTION : Les admins d'école ne voient que leur école
    if current_user.is_system_admin:
        ecoles = current_user.get_accessible_ecoles()
    else:
        # Admin d'école - seulement son école
        ecoles = [current_user.ecole] if current_user.ecole else []
    
    if request.method == "POST":
        # Récupération des données
        nom = request.form.get("nom", "").strip()
        prenoms = request.form.get("prenoms", "").strip()
        sexe = request.form.get("sexe", "").strip()
        username = request.form.get("username", "").strip()
        telephone = request.form.get("telephone", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "").strip()
        ecole_id = request.form.get("ecole_id", "").strip()
        photo = request.files.get("photo")

        # CORRECTION : Pour les admins d'école, forcer l'école de l'admin
        if not current_user.is_system_admin:
            ecole_id = str(current_user.ecole_id)

        # DEBUG: Afficher les données reçues
        print("=== 🔍 VALIDATION EN COURS ===")
        print(f"Password: '{password}' -> Valide: {password_is_strong(password)}")
        print(f"Téléphone: '{telephone}' -> Valide: {phone_is_valid(telephone)}")
        print(f"Email: '{email}' -> Valide: {email_is_valid(email)}")
        print(f"École ID: '{ecole_id}'")

        # VALIDATION RENFORCÉE - BLOQUANTE
        errors = []
        
        # Validation école
        if not ecole_id:
            errors.append("Veuillez sélectionner une école")
        elif not current_user.can_access_ecole(ecole_id):
            errors.append("Vous n'avez pas la permission de créer des utilisateurs dans cette école")

        # Validation champs obligatoires
        if not nom:
            errors.append("Le nom est obligatoire")
        if not prenoms:
            errors.append("Le prénom est obligatoire")
        if not sexe:
            errors.append("Le sexe est obligatoire")
        if not username:
            errors.append("Le nom d'utilisateur est obligatoire")
        if not telephone:
            errors.append("Le téléphone est obligatoire")
        if not email:
            errors.append("L'email est obligatoire")
        if not password:
            errors.append("Le mot de passe est obligatoire")
        if not role:
            errors.append("Le rôle est obligatoire")

        # Validation format mot de passe (SEULEMENT si non vide)
        if password and not password_is_strong(password):
            errors.append("❌ Le mot de passe doit contenir au moins 1 majuscule, 1 chiffre, 1 caractère spécial et 8 caractères minimum")

        # Validation format téléphone (SEULEMENT si non vide)
        if telephone and not phone_is_valid(telephone):
            errors.append("❌ Numéro de téléphone invalide. Format attendu: +22812345678")

        # Validation format email (SEULEMENT si non vide)
        if email and not email_is_valid(email):
            errors.append("❌ Format d'email invalide")

        # Vérification des doublons (SEULEMENT si username/email non vides)
        if username and Utilisateur.query.filter_by(username=username).first():
            errors.append("❌ Ce nom d'utilisateur est déjà pris")

        if email and Utilisateur.query.filter_by(email=email).first():
            errors.append("❌ Cette adresse email est déjà utilisée")

        # Si erreurs, AFFICHER et BLOQUER
        if errors:
            print(f"🚫 ERREURS DÉTECTÉES: {errors}")
            for error in errors:
                flash(error, "danger")
            return render_template("auth/register.html", ecoles=ecoles, username=current_user.username)

        # Gestion de la photo
        photo_filename = None
        if photo and photo.filename != "":
            if allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(UPLOAD_FOLDER, filename)
                photo.save(photo_path)
                photo_filename = filename
            else:
                flash("Type de fichier photo non autorisé", "danger")
                return render_template("auth/register.html", ecoles=ecoles, username=current_user.username)

        # ✅ TOUTES LES VALIDATIONS PASSÉES - CRÉATION
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            new_user = Utilisateur(
                nom=nom,
                prenoms=prenoms,
                sexe=sexe,
                username=username,
                telephone=telephone,
                email=email,
                password_hash=password_hash,
                role=role,
                photo_filename=photo_filename,
                ecole_id=ecole_id
            )
            
            db.session.add(new_user)
            db.session.commit()

            print(f"✅ UTILISATEUR CRÉÉ: {username}")
            flash(f"Utilisateur {username} créé avec succès ✅", "success")
            return redirect(url_for("auth.listUsers"))

        except IntegrityError as e:
            db.session.rollback()
            if "utilisateurs_email_key" in str(e.orig):
                flash("❌ Cet email est déjà utilisé par un autre utilisateur", "danger")
            elif "utilisateurs_username_key" in str(e.orig):
                flash("❌ Ce nom d'utilisateur est déjà pris", "danger")
            else:
                flash(f"❌ Erreur base de données: {str(e)}", "danger")
            return render_template("auth/register.html", ecoles=ecoles, username=current_user.username)
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur inattendue: {str(e)}", "danger")
            return render_template("auth/register.html", ecoles=ecoles, username=current_user.username)

    return render_template("auth/register.html", ecoles=ecoles, username=current_user.username)

@auth_bp.route("/listUsers")
@login_required
@ecole_required
def listUsers():
    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role","").strip()
    ecole_filter = request.args.get("ecole", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 5))

    if current_user.is_system_admin:
        query = Utilisateur.query
    else:
        # CORRECTION : Les admins d'école ne voient que les utilisateurs de leur école
        query = Utilisateur.query.filter_by(ecole_id=current_user.ecole_id)

    if search:
        query = query.filter(
            Utilisateur.nom.ilike(f'%{search}%')|
            Utilisateur.prenoms.ilike(f'%{search}%')|
            Utilisateur.sexe.ilike(f'%{search}%') |
            Utilisateur.email.ilike(f'%{search}%')|
            Utilisateur.telephone.ilike(f'%{search}%')|
            Utilisateur.username.ilike(f'%{search}%')
        )

    if role_filter:
        role_lower = role_filter.lower()
        if role_lower in ['admin', 'administrateur']:     
            query = query.filter(func.lower(Utilisateur.role).in_(['admin','administrateur']))
        elif role_lower == 'user':
            query = query.filter(func.lower(Utilisateur.role) == 'user')
    
    if ecole_filter and current_user.is_system_admin:
        query = query.filter_by(ecole_id=ecole_filter)

    total_users = query.count()
    total_pages = ceil(total_users / per_page)
    users = query.order_by(Utilisateur.nom).offset((page-1)*per_page).limit(per_page).all()

    # CORRECTION : Précharger les écoles pour éviter les requêtes N+1
    ecole_ids = {user.ecole_id for user in users if user.ecole_id}
    ecoles_dict = {}
    if ecole_ids:
        ecoles = Ecole.query.filter(Ecole.id.in_(ecole_ids)).all()
        ecoles_dict = {ecole.id: ecole for ecole in ecoles}
    
    # CORRECTION : Assigner les écoles aux utilisateurs
    for user in users:
        if user.ecole_id and user.ecole_id in ecoles_dict:
            user.ecole = ecoles_dict[user.ecole_id]
        
        if user.locked_until:
            user.locked_until = to_utc(user.locked_until)
        user.is_locked = user.locked_until and user.locked_until > utcnow()

    ecoles_list = []
    if current_user.is_system_admin:
        ecoles_list = Ecole.query.all()
    
    return render_template(
        "auth/listUsers.html",
        users=users,
        ecoles=ecoles_list,
        page=page,
        total_pages=total_pages,
        search=search,
        role_filter=role_filter,
        ecole_filter=ecole_filter,
        per_page=per_page,
        username=current_user.username,
        is_system_admin=current_user.is_system_admin
    )

@auth_bp.route("/user/<string:id>")
@login_required
@ecole_required
def user_detail(id):
    user = Utilisateur.query.get_or_404(id)
    
    if not current_user.can_access_ecole(user.ecole_id):
        abort(403)
    
    return render_template("auth/user_detail.html", user=user)

@auth_bp.route("/user/<string:id>/edit", methods=["GET", "POST"])
@login_required
@ecole_required
@admin_required
def user_edit(id):
    user = Utilisateur.query.get_or_404(id)
    
    if not current_user.can_access_ecole(user.ecole_id):
        abort(403)
    
    # CORRECTION : Les admins d'école ne peuvent modifier que les utilisateurs de leur école
    if current_user.is_system_admin:
        ecoles = current_user.get_accessible_ecoles()
    else:
        ecoles = [current_user.ecole] if current_user.ecole else []
    
    if request.method == "POST":
        user.nom = request.form.get("nom") 
        user.prenoms = request.form.get("prenoms")
        user.sexe = request.form.get("sexe")
        user.email = request.form.get("email")
        user.telephone = request.form.get("telephone")
        user.username = request.form.get("username")
        user.role = request.form.get("role")
        
        # CORRECTION : Seul l'admin système peut changer l'école
        if current_user.is_system_admin:
            nouvelle_ecole_id = request.form.get("ecole_id")
            if nouvelle_ecole_id and current_user.can_access_ecole(nouvelle_ecole_id):
                user.ecole_id = nouvelle_ecole_id

        if "photo" in request.files:
            file = request.files["photo"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                uploadpath = os.path.join(current_app.root_path, "static/upload", filename)
                file.save(uploadpath)
                user.photo_filename = filename
        
        nouveau_password = request.form.get("password")
        if nouveau_password and nouveau_password.strip():
            if password_is_strong(nouveau_password):
                user.set_password(nouveau_password)
            else:
                flash("Le mot de passe ne respecte pas les critères de sécurité", "danger")
                return render_template("auth/user_edit.html", user=user, ecoles=ecoles)
        
        try:
            db.session.commit()
            flash("✅ Modification réussie", "success")
        except IntegrityError as e:
            db.session.rollback()
            if "utilisateurs_email_key" in str(e.orig):
                flash("❌ Cet email est déjà utilisé par un autre utilisateur", "danger")
            elif "utilisateurs_username_key" in str(e.orig):
                flash("❌ Ce nom d'utilisateur est déjà pris", "danger")
            else:
                flash("❌ Erreur lors de la mise à jour", "danger")
            return render_template("auth/user_edit.html", user=user, ecoles=ecoles)
        
        return redirect(url_for("auth.listUsers"))
    
    return render_template("auth/user_edit.html", user=user, ecoles=ecoles)

@auth_bp.route("/user/<string:id>/delete", methods=["POST"])
@login_required
@ecole_required
@admin_required
def user_delete(id):
    user = Utilisateur.query.get_or_404(id)
    
    if not current_user.can_access_ecole(user.ecole_id):
        abort(403)
    
    if user.id == current_user.id:
        flash("❌ Vous ne pouvez pas supprimer votre propre compte", "danger")
        return redirect(url_for("auth.listUsers"))
    
    db.session.delete(user)
    db.session.commit()
    flash(f"✅ Suppression réussie de {user.nom} {user.prenoms}", "success")
    return redirect(url_for("auth.listUsers"))

@auth_bp.route("/user/<string:id>/unlock", methods=["POST"])
@login_required
@admin_required
def user_unlock(id):
    user = Utilisateur.query.get_or_404(id)
    
    if not current_user.can_access_ecole(user.ecole_id):
        abort(403)
    
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit() 

    flash(f"✅ Le compte de {user.username} a été débloqué", "success")
    return redirect(url_for("auth.listUsers"))

# === RÉINITIALISATION DE MOT DE PASSE ===
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = Utilisateur.query.filter(func.lower(Utilisateur.email) == email).first()
        if user:
            token = serializer.dumps(email, salt='reset-password-salt')
            reset_link = url_for('auth.reset_password', token=token, _external=True)

            msg = Message(
                subject="Réinitialisation du mot de passe",
                recipients=[email],
                body=f"Bonjour {user.username},\n\nCliquez ici pour réinitialiser votre mot de passe : {reset_link}"
            )
            try:
                mail.send(msg)
                flash("Un email de réinitialisation a été envoyé.", "success")
            except Exception as e:
                flash(f"Erreur lors de l'envoi de l'email : {e}", "danger")
        else:
            flash("Cet email n'existe pas.", "danger")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password-salt', max_age=1800)
    except SignatureExpired:
        flash("Lien de réinitialisation a expiré ❌.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("Lien invalide.", "danger")
        return redirect(url_for("auth.forgot_password"))
    
    user = Utilisateur.query.filter_by(email=email).first()
    if not user:
        flash("Utilisateur introuvable ❌", "danger")
        return redirect(url_for("auth.forgot_password"))
    
    if request.method == "POST":
        new_password = request.form.get("password")
    
        if not password_is_strong(new_password):
            flash("⚠️ Le mot de passe doit contenir : 8 caractères min, 1 majuscule, 1 chiffre et 1 caractère spécial.", "danger")
            return redirect(request.url)
        
        user.set_password(new_password)
        db.session.commit()
        flash("Mot de passe réinitialisé avec succès.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("auth/reset_password.html")

@auth_bp.app_context_processor
def inject_utils():
    return {"utcnow": utcnow}

@auth_bp.route("/liste", methods=["GET"])
@login_required
@ecole_required
def liste_utilisateurs():
    if current_user.is_system_admin:
        utilisateurs = Utilisateur.query.all()
    else:
        utilisateurs = Utilisateur.query.filter_by(ecole_id=current_user.ecole_id).all()
    
    return jsonify([
        {
            "id": str(u.id),
            "nom": u.nom,
            "prenoms": u.prenoms,
            "sexe": u.sexe,
            "email": u.email,
            "telephone": u.telephone,
            "photo_filename": u.photo_filename,
            "ecole": u.ecole.nom if u.ecole else "Non assigné"
        } for u in utilisateurs
    ])
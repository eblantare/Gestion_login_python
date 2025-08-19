import os
import re
import hashlib
from uuid import UUID
from math import ceil
from datetime import datetime,timedelta, timezone
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, current_app
from flask_login import login_user,current_user,login_required
from flask_mail import Message
from .extensions import db, login_manager, mail
from .models import Utilisateur, ALLOWED_EXTENSIONS
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
# from .__init__ import app


auth_bp = Blueprint("auth",__name__,template_folder="templates")



# def password_is_strong(password):
#          # Doit contenir au moins :
#     # - une majuscule [A-Z]
#     # - un chiffre [0-9]
#     # - un caractère spécial [^A-Za-z0-9]
#     # - longueur minimum de 8 caractères
#      pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$'
#      return re.match(pattern, password) is not None




#Infos de limitation de nombre de tentative
LOCK_WINDOW_MINUTES = 45
MAX_FAILED_ATTEMPTS = 5
ADMIN_ROLE = {"administrateur", "admin"}

#Paramètre  :forgot_password et envoie par mail
serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY", "fallback_secret"))

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "upload")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



#Encodage de mot de passe pour l'URL(si besoin de caractère spéciaux)
# DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

#⚙Configuration POSTGRESQL
# uri = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# print("URI:", repr(uri))
# app.config['SQLALCHEMY_DATABASE_URI'] = uri
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_SCHEMA'] = 'geslog_schema'
# db.init_app(app)



# Import de la classe Utilisateur depuis entities.py
# from models import Utilisateur
    
    # Fonctions utilitaires
# =========================
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

@login_manager.user_loader
def load_user(user_id):
     try:
          return Utilisateur.query.get(UUID(user_id))
     except ValueError:
          return None
     
# --- Helpers pour gérer le temps ---
def utcnow():
    """Retourne un datetime UTC avec tzinfo."""
    return datetime.now(timezone.utc)

def to_utc(dt):
    """Normalise un datetime (naïf ou aware) en UTC-aware."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Supposons que c'était déjà UTC naïf en DB
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

# =========================
# Routes
# =========================
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
        
     # Normaliser locked_until (au cas où des anciennes valeurs soient 'aware')
        user.locked_until = to_utc(user.locked_until)
        now = utcnow()

        #🔓Déblocage automatique si l'échéance est passée
        if user.locked_until and user.locked_until <= now:
             user.failed_attempts = 0
             user.locked_until = None
             db.session.commit()
        
        # 🚫 Si toujours bloqué
        if user.locked_until and user.locked_until > now:
             until = user.locked_until.strftime("%d%m%Y %H:%M")
             flash(
                f"Votre compte est bloqué jusqu'à {until}. "
                f"Veuillez contacter l'administrateur ou attendre {LOCK_WINDOW_MINUTES} minutes.",
                "danger",
            )
             return render_template("auth/login.html")
        #Vérification de mot de passe hashé
        if user.check_password(password):
             user.failed_attempts = 0
             user.locked_until = None
             db.session.commit()
             login_user(user)
             flash("Connexion réussie ✅", "success")
             return redirect(url_for("auth.home"))
        else:
 # ❌ Mauvais mot de passe
            user.failed_attempts = (user.failed_attempts or 0) + 1

            if user.failed_attempts > MAX_FAILED_ATTEMPTS:  # 🔒 À partir de la 6e tentative
                user.locked_until = now + timedelta(minutes=LOCK_WINDOW_MINUTES)
                flash(f"Votre compte est bloqué. "
                      f"Veuillez contacter l'administrateur ou attendre {LOCK_WINDOW_MINUTES} minutes.", "danger")
            else:
                 flash(f"Mot de passe incorrect ❌ (tentative {user.failed_attempts}/{MAX_FAILED_ATTEMPTS})", "danger")
            db.session.commit()
            return render_template("auth/login.html")
    # Si c'est un GET → afficher le formulaire
    return render_template("auth/login.html")

#Petit décorateur pour restreindre aux admin
def admin_required(f):
     @wraps(f)
     def wrapper(*args, **kwargs):
          if not current_user.is_authenticated or current_user.role.lower() not in ["admin","administrateur"]:
               abort(403)
          return f(*args, **kwargs)
     return wrapper
          
#Route de déblocage
@auth_bp.route("/user/<string:id>/unlock", methods = ["POST"])
@login_required
@admin_required
def user_unlock(id):
     user = Utilisateur.query.get_or_404(id)
     
     #réinitialisation
     user.failed_attempts = 0
     user.locked_until = None
     db.session.commit() 

     flash(f"Le compte de {user.username} a été débloque ✅.", "success")
     #on revient sur la liste
     return redirect(url_for("auth.listUsers"))


#Ceci permet de pouvoir utiliser utccnow()
@auth_bp.app_context_processor
def inject_utils():
     return {"utcnow": lambda:datetime.now(timezone.utc)}


@auth_bp.route("/register", methods=["GET", "POST"])
@login_required
@admin_required
def register():
    
    if current_user.role.lower() not in ["admin", "administrateur"]:
         abort(403)
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        prenoms = request.form.get("prenoms", "").strip()
        username = request.form.get("username", "").strip()
        telephone = request.form.get("telephone", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "").strip()
        photo = request.files.get("photo")

        # Vérifications
        if not (nom and prenoms and username and email and password and role):
            flash("Veuillez remplir tous les champs obligatoires", "danger")
            return redirect(url_for("auth.register"))

        if not password_is_strong(password):
            flash("Le mot de passe doit contenir au moins 1 majuscule, 1 chiffre, 1 caractère spécial et 8 caractères minimum", "danger")
            return redirect(url_for("auth.register"))

        if not email_is_valid(email):
            flash("Format d'email invalide", "danger")
            return redirect(url_for("auth.register"))

        if not phone_is_valid(telephone):
            flash("Numéro de téléphone invalide (doit respecter le standard international)", "danger")
            return redirect(url_for("auth.register"))

        if Utilisateur.query.filter_by(username=username).first():
            flash("Nom d'utilisateur déjà pris", "danger")
            return redirect(url_for("auth.register"))

        if Utilisateur.query.filter_by(email=email).first():
            flash("Adresse email déjà utilisée", "danger")
            return redirect(url_for("auth.register"))

        # Gestion de la photo
        photo_filename = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(photo_path)
            photo_filename = filename
        elif photo and photo.filename != "":
            flash("Type de fichier photo non autorisé", "danger")
            return redirect(url_for("auth.register"))

        # Hash du mot de passe
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Création de l'utilisateur
        new_user = Utilisateur(
            nom=nom,
            prenoms=prenoms,
            username=username,
            telephone=telephone,
            email=email,
            password_hash=password_hash,
            role=role,
            photo_filename=photo_filename
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Ajout réussie, vous pouvez vous connecter.", "success")
     #    return redirect(url_for("auth.login"))

    return render_template("auth/register.html", username=current_user.username)


@auth_bp.route("/home")
@login_required
def home():
#     if current_user.is_authenticated:
         return render_template("auth/home.html", username=current_user.username)
#     else:
#         return redirect(url_for("auth.login"))
   


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    # if "username" not in session:
    #     flash("Veuillez vous connecter.", "warning")
    #     return redirect(url_for("login"))
    return render_template("auth/dashboard.html", username=current_user.username)


@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Déconnecté avec succès.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/listUsers")
@login_required
def listUsers():
    #paramètres
    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role","").strip()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page",5))

    #Requête de base
    query = Utilisateur.query

    #Filtrage par recherche
    if search:
         query = query.filter(
              Utilisateur.nom.ilike(f'%{search}%')|
              Utilisateur.prenoms.ilike(f'%{search}%')|
              Utilisateur.email.ilike(f'%{search}%')|
              Utilisateur.telephone.ilike(f'%{search}%')|
              Utilisateur.username.ilike(f'%{search}%')
         )

         #Filtrage par rôle
    if role_filter:
         role_lower = role_filter.lower()
         if role_lower in ['admin', 'administrateur']:     
            query = query.filter(func.lower(Utilisateur.role).in_(['admin','administrateur']))
         elif role_lower == 'user':
              query = query.filter(func.lower(Utilisateur.role) == 'user')

    #Pagination
    total_users = query.count()
    total_pages = ceil(total_users / per_page)
    users = query.order_by(Utilisateur.id).offset((page-1)*per_page).limit(per_page).all()

    # 👉 Ici tu ajoutes la logique "is_locked"
    for user in users:
         if user.locked_until:
              # Si locked_until est naive, on lui assigne UTC
              if user.locked_until.tzinfo is None:
                   user.locked_until = user.locked_until.replace(tzinfo = timezone.utc)
           #calculer is_locked
         user.is_locked = user.locked_until and user.locked_until > datetime.now(timezone.utc)
    
    return render_template(
         "auth/listUsers.html",
         users = users,
         page=page,
         total_pages=total_pages,
         search=search,
         role_filter=role_filter,
         per_page=per_page,username=current_user.username
    )

#voir détail
@auth_bp.route("/user/<string:id>")
@login_required
def user_detail(id):
     user = Utilisateur.query.get_or_404(id)
     return render_template("auth/user_detail.html", user=user)

#Modifier réservé aux admin
@auth_bp.route("/user/<string:id>/edit", methods = ["GET", "POST"])
@login_required
@admin_required
def user_edit(id):
     if current_user.role .lower() not in ["admin", "administrateur"] :
          abort(403) #interdit
     user = Utilisateur.query.get_or_404(id)
     if request.method == "POST":
         user.nom = request.form["nom"] 
         user.prenoms = request.form["prenoms"]
         user.email = request.form["email"]
         user.telephone = request.form["telephone"]
         user.username = request.form["username"]
         user.role = request.form["role"]

         #Gestion de la photo
         if "photo" in request.files:
              file = request.files["photo"]
              if file and allowed_file(file.filename):
                   filename = secure_filename(file.filename)
                   uploadpath = os.path.join(current_app.rootpath, "static/upload", filename)
                   file.save(uploadpath)
                   user.photo_filename = filename
         try:
           db.session.commit()
           flash("✅ Succès modification", "success")
         except IntegrityError as e:
               db.session.rollback()
               if "utilisateurs_email_key" in str(e.orig):
                   flash("❌ Cet email est déjà utilisé par un autre utilisateur", "danger")
               else:
                    flash("❌ Erreur lors de la mise à jour", "danger")
         return redirect(url_for("auth.listUsers"))
     return render_template("auth/user_edit.html", user=user)

#Suppression
@auth_bp.route("/user/<string:id>/delete", methods=["POST"])
@login_required
@admin_required
def user_delete(id):
     if current_user.role .lower() not in ["admin", "administrateur"] :
          abort(403) #interdit
     user = Utilisateur.query.get_or_404(id)
     db.session.delete(user)
     db.session.commit()
     flash(f"Suppression réussie de {user.nom} {user.prenoms}", "success")
     return redirect(url_for("auth.listUsers"))

#route « Mot de passe oublié »
@auth_bp.route("/forot-password", methods = ["GET","POST"])
def forgot_password():
     if request.method == "POST":
          email = request.form.get("email", "").strip().lower()
          user = Utilisateur.query.filter(func.lower(Utilisateur.email) == email).first()
          if user:
               #Générer un token valable 30 min
               token = serializer.dumps(email, salt='reset-password-salt')
               reset_link = url_for('auth.reset_password', token=token, _external = True)

               msg = Message(
                    subject="Réinitialisation du mot de passe",
                    # sender=current_app.config['MAIL_USERNAME'],
                    recipients=[email],
                    body=f"Bonjour {user.username},\n\nCliquez ici pour réinitialiser votre mot de passe : {reset_link}"
               )
               try:
                   mail.send(msg)
                   flash("un email de réinitialisation a éte envoyé.","success")
               except Exception as e:
                   flash(f"Erreur lors de l'envoi de l'email : {e}", "danger")
          else:
               flash("Cet email n'existe pas. ", "danger")
          return redirect(url_for("auth.login"))
     return render_template("auth/forgot_password.html")

#La route de réinitialisation
@auth_bp.route("/reset-password/<token>", methods = ["GET","POST"])
def reset_password(token):
     try:
          email = serializer.loads(token, salt='reset-password-salt', max_age=1800)
     except SignatureExpired:
          flash("Lien de réinitialisation a expiré ❌.","danger")
          return redirect(url_for("auth.forgot_password"))
     except BadSignature:
             flash("Lien invalide.", "danger")
             return redirect(url_for("auth.forgot_password"))
     user = Utilisateur.query.filter_by(email=email).first()
     if not user:
          flash("Utilisateur introuvable ❌","danger")
          return redirect(url_for("auth.forgot_password"))
     
     if request.method == "POST":
          new_password = request.form.get("password")
     
     #Vérification de la robustesse
          if not password_is_strong(new_password):
             flash("⚠️ Le mot de passe doit contenir : 8 caractères min, 1 majuscule, 1 minuscule, 1 chiffre et 1 caractère spécial.", "danger")
             return redirect(request.url)
     #Mise à jour en base
          user.set_password(new_password)
          db.session.commit()
          flash("Mot de passe réinitialisé avec succès.", "success")
          return redirect(url_for("auth.login"))
     return render_template("auth/reset_password.html")

#admin pour le déblocage 
def is_admin(user) -> bool:
     return (user.role or "").strip().lower() in ADMIN_ROLE

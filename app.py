from flask import Flask, render_template, request, redirect, url_for, flash, session,abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import hashlib
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv
import sys
import re
from extensions import db
from entity.entities import ALLOWED_EXTENSIONS
from sqlalchemy import or_
from math import ceil
from flask_login import LoginManager ,login_user,current_user,login_required
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError
# from sqlalchemy import event
# from sqlalchemy.engine import Engine



def password_is_strong(password):
         # Doit contenir au moins :
    # - une majuscule [A-Z]
    # - un chiffre [0-9]
    # - un caractère spécial [^A-Za-z0-9]
    # - longueur minimum de 8 caractères
     pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$'
     return re.match(pattern, password) is not None


#charger le fichier .env
load_dotenv()
sys.stdout.flush()

app = Flask(__name__)
#clé secrète flask
app.secret_key = os.getenv("SECRET_KEY","falback_secret")

#configuration mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT']= 465
app.config['MAIL_USERNAME'] = 'romain.blantare@gmail.com'
app.config['MAIL_PASSWORD'] = 'hcztvxjoazwschge'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" #page vers laquelle rediriger si non connecté.

# Récupération des infs DB
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")  # Attention à ce mot de passe, pas d’accents ni espaces invisibles
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

#Encodage de mot de passe pour l'URL(si besoin de caractère spéciaux)
DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

#⚙Configuration POSTGRESQL
uri = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print("URI:", repr(uri))
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_SCHEMA'] = 'geslog_schema'
db.init_app(app)

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "upload")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Import de la classe Utilisateur depuis entities.py
from entity.entities import Utilisateur
    
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
     return Utilisateur.query.get(int(user_id))
     


# =========================
# Routes
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Veuillez renseigner le nom d'utilisateur et le mot de passe", "danger")
            return redirect(url_for("login"))

        user = Utilisateur.query.filter_by(username=username).first()
        if user is None:
             flash("Nom d'utilisateur ou mot de passe incorrect ❌", "danger")
             return render_template("login.html")
        
        #Vérification de mot de passe hashé
        if user.check_password(password):
             login_user(user)
          #    flash(f"Bienvenue {user.username} 🎉", "success")
             return redirect(url_for("home"))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect ❌", "danger")
            return render_template("login.html")  # rester sur login si erreur

    # Si c'est un GET → afficher le formulaire
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
@login_required
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
            return redirect(url_for("register"))

        if not password_is_strong(password):
            flash("Le mot de passe doit contenir au moins 1 majuscule, 1 chiffre, 1 caractère spécial et 8 caractères minimum", "danger")
            return redirect(url_for("register"))

        if not email_is_valid(email):
            flash("Format d'email invalide", "danger")
            return redirect(url_for("register"))

        if not phone_is_valid(telephone):
            flash("Numéro de téléphone invalide (doit respecter le standard international)", "danger")
            return redirect(url_for("register"))

        if Utilisateur.query.filter_by(username=username).first():
            flash("Nom d'utilisateur déjà pris", "danger")
            return redirect(url_for("register"))

        if Utilisateur.query.filter_by(email=email).first():
            flash("Adresse email déjà utilisée", "danger")
            return redirect(url_for("register"))

        # Gestion de la photo
        photo_filename = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(photo_path)
            photo_filename = filename
        elif photo and photo.filename != "":
            flash("Type de fichier photo non autorisé", "danger")
            return redirect(url_for("register"))

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
        # return redirect(url_for("login"))

    return render_template("register.html", username=current_user.username)


@app.route("/home")
def home():
    if current_user.is_authenticated:
         return render_template("home.html", username=current_user.username)
    else:
        return redirect(url_for("login"))
   


@app.route("/dashboard")
@login_required
def dashboard():
    # if "username" not in session:
    #     flash("Veuillez vous connecter.", "warning")
    #     return redirect(url_for("login"))
    return render_template("dashboard.html", username=current_user.username)


@app.route("/logout")
def logout():
    session.clear()
    flash("Déconnecté avec succès.", "info")
    return redirect(url_for("login"))

@app.route("/listUsers")
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
         query = query.filter(Utilisateur.role == role_filter)

    #Pagination
    total_users = query.count()
    total_pages = ceil(total_users / per_page)
    users = query.order_by(Utilisateur.id).offset((page-1)*per_page).limit(per_page).all()
    
    return render_template(
         "listUsers.html",
         users = users,
         page=page,
         total_pages=total_pages,
         search=search,
         role_filter=role_filter,
         per_page=per_page,username=current_user.username
    )

#voir détail
@app.route("/user/<int:id>")
def user_detail(id):
     user = Utilisateur.query.get_or_404(id)
     return render_template("user_detail.html", user=user)

#Modifier réservé aux admin
@app.route("/user/<int:id>/edit", methods = ["GET", "POST"])
@login_required
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
                   filenane = secure_filename(file.filename)
                   uploadpath = os.path.join(current_app.rootpath, "static/upload", filename)
                   file.save(uploadpath)
                   user.photo_filename = filenane
         try:
           db.session.commit()
           flash("✅ Succès modification", "success")
         except IntegrityError as e:
               db.session.rollback()
               if "utilisateurs_email_key" in str(e.orig):
                   flash("❌ Cet email est déjà utilisé par un autre utilisateur", "danger")
               else:
                    flash("❌ Erreur lors de la mise à jour", "danger")
         return redirect(url_for("listUsers"))
     return render_template("user_edit.html", user=user)

#Suppression
@app.route("/user/<int:id>/delete", methods=["POST"])
def user_delete(id):
     if current_user.role .lower() not in ["admin", "administrateur"] :
          abort(403) #interdit
     user = Utilisateur.query.get_or_404(id)
     db.session.delete(user)
     db.session.commit()
     flash(f"Suppression réussie de {user.nom} {user.prenoms}", "success")
     return redirect(url_for("listUsers"))

#route « Mot de passe oublié »
@app.route("/forot-password", methods = ["GET","POST"])
def forgot_password():
     if request.method == "POST":
          email = request.form.get("email")
          user = Utilisateur.query.filter_by(email=email).first()
          if user:
               #Générer un token valable 30 min
               token = serializer.dumps(email, salt='reset-password-salt')
               reset_link = url_for('reset_password', token=token, _external = True)

               msg = Message(
                    subject="Réinitialisation du mot de passe",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[email],
                    body=f"Bonjour {user.username},\n\nCliquez ici pour réinitialiser votre mot de passe : {reset_link}"
               )
               mail.send(msg)
               flash("un email de réinitialisation a éte envoyé.","success")
          else:
               flash("Cet email n'existe pas. ", "danger")
          return redirect(url_for("login"))
     return render_template("forgot_password.html")

#La route de réinitialisation
@app.route("/reset-password/<token>", methods = ["GET","POST"])
def reset_password(token):
     try:
          email = serializer.loads(token, salt='reset-password-salt', max_age=1800)
     except:
          flash("Lien invalide ou expiré ❌.","danger")
          return redirect(url_for("forgot_password"))
     user = Utilisateur.query.filter_by(email=email).first()
     if not user:
          flash("Utilisateur introuvable ❌","danger")
          return redirect(url_for("forgot_password"))
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
          return redirect(url_for("login"))
     return render_template("reset_password.html")
     

# =========================
# Lancement de l'application
# =========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crée la table utilisateurs si elle n'existe pas
    app.run(debug=True)
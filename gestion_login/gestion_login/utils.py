from flask import session,redirect,url_for,flash,request
from pathlib import Path

def login_required_middleware(app, protected_paths=None):
        """
    Middleware global qui force la connexion pour accéder à certaines routes.
    
    :param app: instance Flask
    :param protected_paths: liste des préfixes d’URL à protéger
    """
        if protected_paths is None:
                protected_paths = ["/home", "auth/login", "listUsers"]

        @app.before_request
        def required_login():
              path = request.path
              #Autoriser certaines routes publiques
              if path.startswith("/auth") or path.startswith('/static'):
                    return
              
        # Protéger les routes sensibles
              for prefix in protected_paths:
                 if Path.startswith(prefix):
                   if "user_id" not in session:
                       flash("Veuillez vous connecter ❌", "danger")
                       return redirect(url_for("auth.login"))
                   break
from flask import redirect, url_for, flash, request
from flask_login import current_user

def login_required_middleware(app, protected_paths=None, admin_only_paths=None):
    """
    Middleware global qui force la connexion pour accéder à certaines routes.

    :param app: instance Flask
    :param protected_paths: liste des préfixes d’URL à protéger
    """
    if protected_paths is None:
        protected_paths = ["/home", "/eleves", "/enseignants", "/matieres",
                           "/classes", "/appreciations"]
    if admin_only_paths is None:
        admin_only_paths = ["/listUsers","/register"]

    @app.before_request
    def required_login():
        path = request.path
        # Autoriser certaines routes publiques
        if path.startswith("/auth") or path.startswith('/static'):
            return

        # Protéger l'authenticité générale
        for prefix in protected_paths:
            if path.startswith(prefix):
                if not current_user.is_authenticated:
                    flash("Veuillez vous connecter ❌", "danger")
                    return redirect(url_for("auth.login"))
                break

                # Vérifier les routes réservées aux admins
        for prefix in admin_only_paths:
            if path.startswith(prefix):
                if not current_user.is_authenticated or current_user.role not in ["admin", "administrateur"] :
                    flash("Accès réservé aux administrateurs ❌", "danger")
                    return redirect(url_for("auth.login"))
                break
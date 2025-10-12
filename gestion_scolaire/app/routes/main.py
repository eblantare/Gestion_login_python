from flask import Blueprint, render_template
from flask_login import current_user, login_required

main_bp = Blueprint(
    "main",
    __name__,
    template_folder="../templates/scolaire",
    static_folder="../static/scolaire",
    static_url_path="/scolaire_static"
)

@main_bp.route("/")
@login_required
def index():
    #Vérifier si l'utilisateur est connecté
    if current_user.is_authenticated:
        username = current_user.username
    else:
        username = "Invité" #Valeur par défaut pour les non-connectés

    return render_template("edashboard.html", username=username)
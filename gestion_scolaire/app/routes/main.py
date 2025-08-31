from flask import Blueprint, render_template
from flask_login import current_user
main_bp = Blueprint(
    "main",
    __name__,
    template_folder="../templates/scolaire",
    static_folder="../static/scolaire",
    static_url_path="/scolaire_static"
)

@main_bp.route("/")
def index():
    return render_template("edashboard.html", username=current_user.username)
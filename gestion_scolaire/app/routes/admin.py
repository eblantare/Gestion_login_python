# app/routes/admin.py - VERSION SIMPLIFIÉE
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from ..models import Ecole, SystemeEvaluation
from ..utils.systeme_helper import get_or_create_systeme_evaluation

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/config-systeme-evaluation/<string:ecole_id>", methods=["GET", "POST"])
@login_required
def config_systeme_evaluation(ecole_id):
    """Configuration simple du système d'évaluation"""
    
    # Vérifications de sécurité
    if not current_user.is_admin():
        from flask import abort
        abort(403)
    
    ecole = Ecole.query.get_or_404(ecole_id)
    
    # Vérifier l'accès à l'école
    if str(current_user.ecole_id) != str(ecole_id):
        flash("Accès non autorisé", "error")
        return redirect(url_for('main.index'))
    
    # UTILISER LA FONCTION HELPER (pas de duplication)
    systeme = get_or_create_systeme_evaluation(ecole_id)
    
    if request.method == "POST":
        try:
            # Seulement 2 champs à gérer
            systeme.type_systeme = request.form.get("type_systeme", "trimestriel")
            
            # Mettre à jour l'école
            ecole.systeme_evaluation = systeme.type_systeme
            
            db.session.commit()
            flash("✅ Configuration mise à jour avec succès!", "success")
            return redirect(url_for('admin.config_systeme_evaluation', ecole_id=ecole_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Erreur: {str(e)}", "error")
    
    return render_template(
        "admin/config_systeme_evaluation.html",
        ecole=ecole,
        systeme=systeme
    )
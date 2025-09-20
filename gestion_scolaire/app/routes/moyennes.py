from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy import func, or_
from extensions import db
from ..models import Moyenne, Eleve, Classe
from flask_login import current_user, login_required
from ..tasks import BatchMoyennes  # import fonction directement
from datetime import date

moyennes_bp = Blueprint('moyennes', __name__, url_prefix='/moyennes')

# ---------------- Routes ---------------- #

@moyennes_bp.route('/')
def liste_moyennes():
    # Récupération des filtres
    search = request.args.get('search', '', type=str).strip()
    classe_id = request.args.get('classe_id', '', type=str)
    annee_scolaire = request.args.get('annee_scolaire', '', type=str)
    moy_field = request.args.get('moy_field', '')
    moy_filter = request.args.get('moy_filter', '', type=str).strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Base query
    query = db.session.query(Moyenne).join(Eleve, Moyenne.eleve).join(Classe, Eleve.classe)

    # Recherche
    if search:
        like_q = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Eleve.nom).like(like_q),
                func.lower(Eleve.prenoms).like(like_q),
                func.lower(Moyenne.code).like(like_q)
            )
        )

    # Filtre classe
    if classe_id:
        query = query.filter(Eleve.classe_id == classe_id)

    # Filtre année scolaire
    if annee_scolaire:
        query = query.filter(Moyenne.code.like(f"{annee_scolaire}-%"))

    # Filtre moyenne
    if moy_filter:
        try:
            mf = moy_filter
            if '-' in mf:
                low, high = map(float, mf.split('-', 1))
                query = query.filter(getattr(Moyenne, moy_field) >= low,
                                     getattr(Moyenne, moy_field) <= high)
            elif mf.startswith(('>=', '<=', '>', '<')):
                op, val = (mf[:2], float(mf[2:])) if mf[:2] in ('>=', '<=') else (mf[0], float(mf[1:]))
                col = getattr(Moyenne, moy_field)
                if op == '>=': query = query.filter(col >= val)
                if op == '<=': query = query.filter(col <= val)
                if op == '>': query = query.filter(col > val)
                if op == '<': query = query.filter(col < val)
            else:
                val = float(mf)
                col = getattr(Moyenne, moy_field)
                query = query.filter(func.round(col, 2) == val)
        except ValueError:
            pass

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Liste classes
    classes = Classe.query.order_by(Classe.nom).all()

    # ✅ Récupération des années scolaires dynamiques
    codes = db.session.query(Moyenne.code).filter(Moyenne.code != None).distinct().all()
    annees_scolaires = sorted({
        '-'.join(code.split('-')[:2]) for (code,) in codes if code and len(code.split('-')) >= 2
    }, reverse=True)

    if not annees_scolaires:
        # Génération automatique autour de l'année en cours si aucune moyenne
        current_year = date.today().year
        start_year = current_year if date.today().month >= 9 else current_year - 1
        annees_scolaires = [f"{y}-{y+1}" for y in range(start_year-5, start_year+2)]
        annees_scolaires.sort(reverse=True)

    # 🔄 Détection automatique du trimestre courant
    today = date.today()
    if today.month in (9, 10, 11, 12):
        trimestre_courant = 1
    elif today.month in (1, 2, 3, 4):
        trimestre_courant = 2
    else:
        trimestre_courant = 3

    return render_template(
        'moyennes/list_moy.html',
        pagination=pagination,
        classes=classes,
        annees_scolaires=annees_scolaires,
        search=search,
        classe_id=classe_id,
        annee_scolaire=annee_scolaire,
        moy_field=moy_field,
        moy_filter=moy_filter,
        per_page=per_page,
        trimestre_courant=trimestre_courant
    )

@moyennes_bp.route('/lancer-batch/<int:trimestre>', methods=['POST'])
@login_required
def lancer_batch(trimestre):
    if current_user.role not in ['admin', 'administrateur']:
        flash("Vous n'êtes pas autorisé à lancer le batch.", "danger")
        return redirect(url_for('moyennes.liste_moyennes'))

    classe_id = request.form.get("classe_id")
    annee_scolaire = request.form.get("annee_scolaire")
    enseignant_id = current_user.id

    if not classe_id or not annee_scolaire:
        flash("Veuillez sélectionner une classe et une année scolaire.", "warning")
        return redirect(url_for('moyennes.liste_moyennes'))
    print("AVANT BATCH")
    message = BatchMoyennes.run(annee_scolaire, trimestre, classe_id, enseignant_id)
    flash(message, "success")
    print("APRES BATCH")
    return redirect(url_for('moyennes.liste_moyennes'))

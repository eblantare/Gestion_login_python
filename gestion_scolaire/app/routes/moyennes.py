from flask import Blueprint, request, render_template, redirect, url_for, flash
from extensions import db
from ..models import Moyenne, Eleve, Classe, Note, Appreciations, Enseignement
from flask_login import current_user
from gestion_scolaire.app.tasks.batchMoyennes import calculer_moyennes
import uuid, time

moyennes_bp = Blueprint('moyennes', __name__, url_prefix='/moyennes')


@moyennes_bp.route("/")
def liste_moyennes():
    search = request.args.get("search", "").strip()
    classe_id = request.args.get("classe_id", "").strip()
    annee_scolaire = request.args.get("annee_scolaire", "").strip()
    
    # Sécurisation du trimestre
    trimestre_str = request.args.get("trimestre", "1")
    try:
        trimestre = int(trimestre_str)
    except ValueError:
        trimestre = 1
    if trimestre not in [1,2,3]:
        trimestre = 1

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Requête principale
    query = (
        db.session.query(
            Eleve.id.label("eleve_id"),
            Eleve.nom,
            Eleve.prenoms,
            Classe.nom.label("classe_nom"),
            Moyenne.moy_trim,
            Moyenne.moy_gen,
            Moyenne.classement.label("classement"),
            Moyenne.classement_str.label("classement_str"),
            Moyenne.classement_gen.label("classement_gen"),
            Moyenne.moy_class,
            Moyenne.moy_forte,
            Moyenne.moy_faible,
            Moyenne.eff_comp.label("effectif_composants"),
            Appreciations.libelle.label("appreciation"),
        )
        .join(Eleve, Eleve.id == Moyenne.eleve_id)
        .join(Classe, Classe.id == Eleve.classe_id)
        .outerjoin(Appreciations, Appreciations.id == Moyenne.appreciation_id)
        .filter(Moyenne.trimestre == trimestre)
    )

    if search:
        query = query.filter(
            db.or_(
                Eleve.nom.ilike(f"%{search}%"),
                Eleve.prenoms.ilike(f"%{search}%"),
            )
        )
    if classe_id:
        query = query.filter(Eleve.classe_id == classe_id)
    if annee_scolaire:
        query = query.filter(Moyenne.annee_scolaire == annee_scolaire)

    query = query.order_by(Moyenne.classement.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    classes = Classe.query.all()
    annees_scolaires = [m.annee_scolaire for m in db.session.query(Moyenne.annee_scolaire).distinct()]

    # Calcul du récapitulatif
    if items:
        moy_forte = max([i.moy_forte for i in items if i.moy_forte is not None], default=0)
        moy_faible = min([i.moy_faible for i in items if i.moy_faible is not None], default=0)
        moy_class = round((moy_forte + moy_faible) / 2, 2) if (moy_forte or moy_faible) else 0
        effectif_composants = sum([1 for i in items if i.moy_trim is not None and i.moy_trim > 0])
        classe_recap = {
            "moy_class": moy_class,
            "moy_forte": moy_forte,
            "moy_faible": moy_faible,
            "effectif_composants": effectif_composants,
        }
    else:
        classe_recap = {"moy_class": 0, "moy_forte": 0, "moy_faible": 0, "effectif_composants": 0}

    return render_template(
        "moyennes/list_moy.html",
        items=items,
        pagination=pagination,
        search=search,
        classe_id=classe_id,
        annee_scolaire=annee_scolaire,
        trimestre=trimestre,
        per_page=per_page,
        classes=classes,
        annees_scolaires=annees_scolaires,
        classe_recap=classe_recap,
    )


@moyennes_bp.route("/lancer-batch", methods=["POST"])
def lancer_batch():
    try:
        classe_id = request.form.get("classe_id")
        annee_scolaire = request.form.get("annee_scolaire")
        trimestre = int(request.form.get("trimestre", 1))

        if not annee_scolaire or trimestre not in [1, 2, 3]:
            return {"status": "error", "message": "Année scolaire ou trimestre invalide"}

        # 🔹 Lancer le batch
        result = calculer_moyennes(classe_id, annee_scolaire, trimestre)

        # 🔹 Retourner items + résumé pour le JS
        items_query = (
            db.session.query(
                Eleve.nom, Eleve.prenoms, Classe.nom.label("classe_nom"),
                Moyenne.moy_trim, Moyenne.moy_gen, Moyenne.classement_str,
                Appreciations.libelle.label("appreciation"), Moyenne.moy_class
            )
            .join(Eleve, Eleve.id == Moyenne.eleve_id)
            .join(Classe, Classe.id == Eleve.classe_id)
            .outerjoin(Appreciations, Appreciations.id == Moyenne.appreciation_id)
            .filter(Moyenne.trimestre == trimestre, Moyenne.annee_scolaire == annee_scolaire)
            .all()
        )
        items = [dict(row._mapping) for row in items_query]

        # Récapitulatif
        valeurs_non_nulles = [i["moy_trim"] for i in items if i["moy_trim"] is not None and i["moy_trim"] > 0]
        classe_recap = {
            "moy_class": round((max(valeurs_non_nulles, default=0) + min(valeurs_non_nulles, default=0))/2, 2),
            "moy_forte": max(valeurs_non_nulles, default=0),
            "moy_faible": min(valeurs_non_nulles, default=0),
            "effectif_composants": len(valeurs_non_nulles)
        }

        return {"status": "ok", **result, "items": items, "classe_recap": classe_recap, "trimestre": trimestre}

    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}


def calculer_moyennes_toutes_classes(annee_scolaire, trimestre):
    resume_global = {"success": [], "errors": [], "created": 0, "updated": 0, "total": 0}
    for classe in Classe.query.all():
        result = calculer_moyennes(classe.id, annee_scolaire, trimestre)
        resume_global["success"].extend(result.get("success", []))
        resume_global["errors"].extend(result.get("errors", []))
        resume_global["created"] += result.get("created", 0)
        resume_global["updated"] += result.get("updated", 0)
        resume_global["total"] += result.get("total", 0)
    return resume_global



@moyennes_bp.route("/test-batch")
def test_batch():
    """
    Endpoint de test pour vérifier le batch.
    """
    try:
        # Prendre la première classe trouvée
        classe = Classe.query.first()
        if not classe:
            return {"status": "error", "message": "Aucune classe trouvée"}

        # Lancer le batch pour cette classe et l'année scolaire "2025-2026"
        result = calculer_moyennes(classe.id, "2025-2026", 1)  # trimestre 1
        return {"status": "ok", "classe": classe.nom, "result": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}



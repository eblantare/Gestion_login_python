
from app.models.matieres import Matiere
from app import db
import re
import uuid

def generer_code_matiere(libelle, ecole_id):
    if not libelle:
        base_code = "MAT"
    else:
        base_code = libelle.upper()[:4]
        base_code = re.sub(r'[^A-Z]', '', base_code)
        if len(base_code) < 3:
            base_code = "MAT"
    
    code_final = base_code
    compteur = 1
    
    while Matiere.query.filter_by(code=code_final, ecole_id=ecole_id).first():
        compteur += 1
        code_final = f"{base_code}{compteur:02d}"
        if compteur > 99:
            code_final = f"{base_code}_{uuid.uuid4().hex[:4].upper()}"
            break
    
    return code_final

print("🔧 Correction des codes matières...")
matieres = Matiere.query.all()
print(f"📚 {len(matieres)} matières trouvées")

corrections = []
for matiere in matieres:
    ancien_code = matiere.code
    nouveau_code = generer_code_matiere(matiere.libelle, matiere.ecole_id)
    
    if ancien_code != nouveau_code:
        matiere.code = nouveau_code
        corrections.append({
            'ancien': ancien_code,
            'nouveau': nouveau_code,
            'libelle': matiere.libelle
        })
        print(f"✅ {ancien_code} → {nouveau_code}")

if corrections:
    db.session.commit()
    print(f"🎉 {len(corrections)} codes corrigés")
else:
    print("✅ Aucune correction nécessaire")

document.addEventListener('DOMContentLoaded', function() {
    const batchBtn = document.getElementById('batchBtn');
    const batchForm = document.getElementById('batchForm');
    const classeSelect = document.getElementById('classeSelect');
    const anneeSelect = document.getElementById('anneeSelect');
    const batchBtnText = document.getElementById('batchBtnText');

    // Initialiser le texte du bouton
    if (batchBtnText) {
        batchBtnText.textContent = 'Calculer moyenne';
    }

    // Si les éléments n'existent pas sur cette page, on arrête
    if (!batchBtn || !batchForm) {
        console.log('Éléments batch non trouvés - page services probablement');
        return;
    }

    const batchSpinner = document.getElementById('batchSpinner');
    const batchResult = document.getElementById('batchResult');

    // Fonction pour activer/désactiver le bouton
    function toggleBatchBtn() {
        const hasClasse = classeSelect && classeSelect.value;
        const hasAnnee = anneeSelect && anneeSelect.value;
        
        // CORRECTION : Vérifier que les valeurs ne sont pas vides
        batchBtn.disabled = !(hasClasse && hasAnnee);
        
        console.log('État bouton batch:', {
            classe: hasClasse,
            annee: hasAnnee,
            disabled: batchBtn.disabled
        });
    }

    // Initialiser l'état du bouton
    toggleBatchBtn();

    // Écouter les changements sur les selects
    if (classeSelect) {
        classeSelect.addEventListener('change', toggleBatchBtn);
    }
    
    if (anneeSelect) {
        anneeSelect.addEventListener('change', toggleBatchBtn);
    }

    // Gestion de la soumission du formulaire
    batchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validation supplémentaire
        if (!classeSelect || !classeSelect.value || !anneeSelect || !anneeSelect.value) {
            alert('Veuillez sélectionner une classe et une année scolaire');
            return;
        }

        // Désactiver le bouton et afficher le spinner
        batchBtn.disabled = true;
        if (batchSpinner) batchSpinner.classList.remove('d-none');
        if (batchBtnText) batchBtnText.textContent = 'Calcul en cours...';
        
        // Créer FormData avec les valeurs actuelles
        const formData = new FormData();
        formData.append('classe_id', classeSelect.value);
        formData.append('annee_scolaire', anneeSelect.value);
        formData.append('trimestre', '1'); // Vous pouvez récupérer ça d'un select si nécessaire

        fetch(batchForm.action, {
            method: "POST",
            body: formData,
        })
        .then(resp => {
            if (!resp.ok) {
                throw new Error(`Erreur HTTP: ${resp.status}`);
            }
            return resp.json();
        })
        .then(data => {
            console.log('Réponse batch:', data);
            
            // Cacher le spinner
            if (batchSpinner) batchSpinner.classList.add('d-none');
            if (batchBtnText) batchBtnText.textContent = 'Calculer moyenne';

            if (data.status === "ok") {
                // Afficher le résultat
                if (batchResult) {
                    batchResult.innerHTML = `
                        <div class="alert alert-success mt-2">
                            ✅ Batch terminé !<br>
                            Créés: ${data.created || 0}, 
                            Mis à jour: ${data.updated || 0}, 
                            Erreurs: ${data.errors ? data.errors.length : 0}
                        </div>
                    `;
                }
                
                // Recharger la page pour voir les nouvelles données
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
                
            } else {
                if (batchResult) {
                    batchResult.innerHTML = `
                        <div class="alert alert-danger mt-2">
                            ⚠️ Erreur : ${data.message || 'Erreur inconnue'}
                        </div>
                    `;
                }
                // Réactiver le bouton en cas d'erreur
                toggleBatchBtn();
            }
        })
        .catch(err => {
            console.error('Erreur fetch:', err);
            
            if (batchSpinner) batchSpinner.classList.add('d-none');
            if (batchBtnText) batchBtnText.textContent = 'Calculer moyenne';
            
            if (batchResult) {
                batchResult.innerHTML = `
                    <div class="alert alert-danger mt-2">
                        ❌ Erreur réseau : ${err.message}
                    </div>
                `;
            }
            
            // Réactiver le bouton en cas d'erreur
            toggleBatchBtn();
        });
    });
});
document.addEventListener("DOMContentLoaded", function() {

    // Fonction pour activer/désactiver le bouton Batch
    function toggleBatchBtn() {
        const selectClasse = document.getElementById('classeSelect');
        const selectAnnee = document.getElementById('anneeSelect');
        const batchBtn = document.getElementById('batchBtn');
        const hiddenClasse = document.getElementById('batchClasseId');
        const hiddenAnnee = document.getElementById('batchAnneeScolaire');

        const classeVal = selectClasse.value;
        const anneeVal = selectAnnee.value;

        hiddenClasse.value = classeVal;
        hiddenAnnee.value = anneeVal;

        batchBtn.disabled = !(classeVal && anneeVal); // actif seulement si les 2 remplis
    }

    // Initialisation
    toggleBatchBtn();

    // Événements de changement
    const selectClasse = document.getElementById('classeSelect');
    const selectAnnee = document.getElementById('anneeSelect');
    selectClasse.addEventListener('change', toggleBatchBtn);
    selectAnnee.addEventListener('change', toggleBatchBtn);

});

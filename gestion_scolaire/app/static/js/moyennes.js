document.addEventListener('DOMContentLoaded', function() {
    const batchBtn = document.getElementById('batchBtn');
    const batchBtnText = document.getElementById('batchBtnText');
    const batchSpinner = document.getElementById('batchSpinner');
    const batchResult = document.getElementById('batchResult');
    const batchForm = document.getElementById('batchForm');
    const classeSelect = document.getElementById('classeSelect');
    const anneeSelect = document.getElementById('anneeSelect');

    function toggleBatchBtn() {
        batchBtn.disabled = !(classeSelect.value && anneeSelect.value);
    }
    classeSelect.addEventListener('change', toggleBatchBtn);
    anneeSelect.addEventListener('change', toggleBatchBtn);
    toggleBatchBtn();

    batchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        batchBtn.disabled = true;
        batchSpinner.classList.remove('d-none');
        batchBtnText.textContent = 'Calcul en cours...';
        batchResult.textContent = '';

        const formData = new FormData(batchForm);

        fetch(batchForm.action, {
            method: "POST",
            body: formData,
        })
        .then(resp => resp.json())
        .then(data => {
            batchSpinner.classList.add('d-none');
            batchBtnText.textContent = 'Lancer Batch';

            if (data.status === "ok") {
                batchResult.innerHTML = `✅ Batch terminé ! Créés: ${data.created}, Mis à jour: ${data.updated}, Erreurs: ${data.errors.length}`;

                const tbody = document.querySelector("table tbody");
                tbody.innerHTML = "";

                data.items.forEach((row, idx) => {
                    const tr = document.createElement("tr");
                    if (row.moy_trim === row.moy_class && row.moy_trim > 0) tr.classList.add("table-success");

                    tr.innerHTML = `
                        <td>${idx + 1}</td>
                        <td>${row.nom} ${row.prenoms}</td>
                        <td>${row.classe_nom}</td>
                        <td>${row.moy_trim > 0 ? row.moy_trim : "—"}</td>
                        ${row.moy_gen !== undefined ? `<td>${row.moy_gen > 0 ? row.moy_gen : "—"}</td>` : ""}
                        <td>${row.moy_trim > 0 ? (row.classement_str ?? "—") : "—"}</td>
                        <td>${row.moy_trim > 0 ? (row.appreciation ?? "—") : "—"}</td>
                        <td>${row.moy_trim > 0 ? (row.moy_class ?? "—") : "—"}</td>
                    `;
                    tbody.appendChild(tr);
                });

                const recapRow = document.querySelector("table tbody tr.table-info");
                if (recapRow && data.classe_recap) {
                    recapRow.innerHTML = `
                        <td colspan="${data.trimestre == 3 ? 7 : 6}">
                            Résumé Classe (effectif composé: ${data.classe_recap.effectif_composants})
                            &nbsp;|&nbsp; Moy_class = ${data.classe_recap.moy_class ?? "—"}
                            &nbsp;|&nbsp; Moy_faible = ${data.classe_recap.moy_faible ?? "—"}
                            &nbsp;|&nbsp; Moy_forte = ${data.classe_recap.moy_forte ?? "—"}
                        </td>
                    `;
                }
            } else {
                batchResult.innerHTML = `⚠️ Erreur : ${data.message}`;
            }

            batchBtn.disabled = false;
        })
        .catch(err => {
            batchSpinner.classList.add('d-none');
            batchBtnText.textContent = 'Lancer Batch';
            batchResult.innerHTML = `❌ Erreur inattendue : ${err}`;
            batchBtn.disabled = false;
        });
    });
});

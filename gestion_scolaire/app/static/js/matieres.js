// Vérification de la disponibilité de Bootstrap
function checkBootstrapDependencies() {
    if (typeof bootstrap === 'undefined') {
        console.warn('⚠️ Bootstrap non disponible - certaines fonctionnalités seront limitées');
        return false;
    }
    return true;
}

// Attendre que Bootstrap soit chargé
function waitForBootstrap(maxWait = 3000) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        
        function check() {
            if (checkBootstrapDependencies()) {
                resolve();
            } else if (Date.now() - startTime >= maxWait) {
                reject(new Error('Timeout attente de Bootstrap'));
            } else {
                setTimeout(check, 100);
            }
        }
        
        check();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    'use strict';

    // Initialisation avec gestion de la compatibilité
    waitForBootstrap().then(() => {
        console.log('✅ Bootstrap chargé - initialisation des matières');
        initializeMatieres();
    }).catch(err => {
        console.warn('⚠️ Initialisation sans Bootstrap:', err);
        initializeMatieres();
    });

    function initializeMatieres() {
        // ======================= TOOLTIP =======================
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(el => new bootstrap.Tooltip(el));
        }

        // ======================= NOTIFICATIONS =======================
        function showNotification(message, type = "success", delay = 3000) {
            const container = document.getElementById("notificationContainer");
            if (!container) return;
            
            const toast = document.createElement("div");
            toast.className = `toast align-items-center text-bg-${type} border-0`;
            toast.setAttribute("role", "alert");
            toast.setAttribute("aria-live", "assertive");
            toast.setAttribute("aria-atomic", "true");
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            container.appendChild(toast);
            
            if (typeof bootstrap !== 'undefined') {
                const bsToast = new bootstrap.Toast(toast, { delay });
                bsToast.show();
            } else {
                toast.style.display = 'block';
                setTimeout(() => {
                    if (toast.parentNode) toast.remove();
                }, delay);
            }
            
            toast.addEventListener("hidden.bs.toast", () => toast.remove());
        }

        // ======================= UTILS MODAL CLEANUP =======================
        function cleanupModal(modalEl) {
            if (typeof bootstrap !== 'undefined') {
                const inst = bootstrap.Modal.getInstance(modalEl);
                if (inst) inst.hide();
                document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
                document.body.classList.remove('modal-open');
                document.body.style.paddingRight = '';
            } else {
                modalEl.style.display = 'none';
            }
        }

        // ======================= TABLE CLICK HANDLER =======================
        const table = document.getElementById("table-matieres");
        if (table) {
            table.addEventListener("click", e => {
                const btn = e.target.closest("button");
                if (!btn) return;
                
                const id = btn.dataset.id;
                if (!id) { 
                    showNotification("Identifiant matière manquant !", "danger"); 
                    return; 
                }
                
                if (btn.classList.contains("btn-detail")) {
                    showMatDetail(id);
                } else if (btn.classList.contains("btn-edit")) {
                    editMat(id);
                } else if (btn.classList.contains("btn-delete")) {
                    deleteMat(id);
                }
            });
        }

        // ======================= MISE À JOUR LIGNE APRÈS ETAT =======================
        function updateRowAfterStateChange(row, id, etat) {
            if (!row) return;
            
            // Badge état
            const badge = row.querySelector(".etat span.badge");
            if (badge) {
                const lower = (etat || "").toString().toLowerCase();
                badge.textContent = etat;
                badge.className = "badge " + (lower === "actif" ? "bg-success" : (lower === "bloqué" || lower === "abandonné" ? "bg-dark" : "bg-secondary"));
            }

            // Select action
            const select = row.querySelector(".select-action");
            if (select) {
                const lower = (etat || "").toString().toLowerCase();
                if (lower === "bloqué" || lower === "abandonné") {
                    select.remove();
                } else {
                    select.innerHTML = '<option value="">---Action---</option>';
                    if (lower === "inactif") select.innerHTML += '<option value="Activer">Activer</option>';
                    if (lower === "actif") select.innerHTML += '<option value="Bloquer">Bloquer</option>';
                }
            }

            // Boutons actions
            const actionsCell = row.querySelector("td.text-nowrap");
            if (actionsCell) {
                const lower = (etat || "").toString().toLowerCase();
                let html = `<button class="btn btn-info btn-sm btn-detail" data-id="${id}" title="Détail"><i class="bi bi-eye"></i></button>`;
                
                if (lower === "inactif") {
                    html += ` <button class="btn btn-warning btn-sm btn-edit" data-id="${id}" title="Modifier"><i class="bi bi-pencil"></i></button>`;
                    html += ` <button class="btn btn-danger btn-sm btn-delete" data-id="${id}" title="Supprimer"><i class="bi bi-trash"></i></button>`;
                }
                actionsCell.innerHTML = html;
            }
        }

        // ======================= WORKFLOW CHANGE =======================
        let currentAction = null, currentMatId = null, currentSelect = null, actionConfirmed = false;
        const confirmModalMat = document.getElementById("confirmMatActionModal");
        const confirmYesMatBtn = document.getElementById("confirmYesMatBtn");

        function attachWorkflowChange(select) {
            if (!select || select.dataset.listenerAttached) return;
            select.dataset.listenerAttached = "1";
            
            select.addEventListener("change", function () {
                const action = this.value;
                if (!action) return;
                
                currentAction = action;
                currentMatId = this.dataset.id;
                currentSelect = this;
                actionConfirmed = false;
                
                const msgMat = document.getElementById("confirmMatMessage");
                if (msgMat) msgMat.textContent = `Voulez-vous vraiment ${action.toLowerCase()} cette matière ?`;
                
                if (typeof bootstrap !== 'undefined') {
                    bootstrap.Modal.getOrCreateInstance(confirmModalMat).show();
                } else {
                    confirmModalMat.style.display = 'block';
                }
            });
        }

        // Attacher aux selects existants
        document.querySelectorAll(".select-action").forEach(attachWorkflowChange);

        // ======================= CONFIRM BUTTON =======================
        confirmYesMatBtn?.addEventListener("click", async () => {
            if (!currentAction || !currentMatId || actionConfirmed) return;
            actionConfirmed = true;
            confirmYesMatBtn.disabled = true;
            
            try {
                const res = await fetch(`/matieres/${currentMatId}/changer_etat`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ action: currentAction })
                });

                const data = await res.json().catch(() => ({}));

                if (!res.ok) {
                    showNotification(data.error || "Erreur lors du changement d'état", "danger");
                    cleanupModal(confirmModalMat);
                    return;
                }

                // Mise à jour dynamique de la ligne
                const row = document.querySelector(`tr[data-id="matiere-${currentMatId}"]`);
                const returnedId = data.id || currentMatId;
                updateRowAfterStateChange(row, returnedId, data.etat || "");

                showNotification(data.message || `État changé en ${data.etat}`, "success");

                if (currentSelect && currentSelect instanceof HTMLSelectElement) {
                    currentSelect.value = "";
                }
                
                cleanupModal(confirmModalMat);

            } catch (err) {
                console.error(err);
                showNotification("Erreur réseau lors du changement d'état", "danger");
                cleanupModal(confirmModalMat);
            } finally {
                confirmYesMatBtn.disabled = false;
                currentAction = null; currentMatId = null; currentSelect = null; actionConfirmed = false;
            }
        });

        // Reset modal fermeture
        if (confirmModalMat) {
            confirmModalMat.addEventListener("hidden.bs.modal", function () {
                if (!actionConfirmed && currentSelect) currentSelect.value = "";
                currentAction = null; currentMatId = null; currentSelect = null; actionConfirmed = false;
            });
        }

        // ======================= AJOUT MATIERE =======================
        const addMatForm = document.getElementById("addMatForm");
        if (addMatForm) {
            addMatForm.addEventListener("submit", async e => {
                e.preventDefault();
                if (!addMatForm.checkValidity()) { 
                    addMatForm.classList.add("was-validated"); 
                    return; 
                }
                
                const formData = new FormData(addMatForm);
                try {
                    const res = await fetch("/matieres/add", { 
                        method: "POST", 
                        body: formData 
                    });
                    const data = await res.json();
                    
                    if (!res.ok) { 
                        showNotification(data.error || "Erreur lors de l'ajout", "danger"); 
                        return; 
                    }
                    
                    showNotification(`Matière ajoutée avec succès ! Code: ${data.code}`, "success");
                    addMatForm.reset(); 
                    addMatForm.classList.remove("was-validated");
                    cleanupModal(document.getElementById("addMatModal"));

                    // Recharger la page
                    setTimeout(() => window.location.reload(), 1500);

                } catch (err) {
                    console.error(err);
                    showNotification("Erreur réseau", "danger");
                }
            });
        }

        // ======================= SUPPRESSION MATIERE =======================
        window.deleteMat = async (id) => {
            try {
                const res = await fetch(`/matieres/get/${id}`);
                const data = await res.json();
                if (!res.ok) { 
                    showNotification("Erreur lecture matière", "danger"); 
                    return; 
                }
                
                document.getElementById("deleteMat_id").value = id;
                document.getElementById("deleteMat_info").textContent = `${data.code} - ${data.libelle}`;
                
                const deleteModalEl = document.getElementById("deleteMatModal");
                if (typeof bootstrap !== 'undefined') {
                    bootstrap.Modal.getOrCreateInstance(deleteModalEl).show();
                } else {
                    deleteModalEl.style.display = 'block';
                }
                
            } catch (err) {
                console.error(err);
                showNotification("Erreur réseau", "danger");
            }
        };

        const deleteMatForm = document.getElementById("deleteMatForm");
        if (deleteMatForm) {
            deleteMatForm.addEventListener("submit", async e => {
                e.preventDefault();
                const id = document.getElementById("deleteMat_id").value;
                
                try {
                    const res = await fetch(`/matieres/delete/${id}`, { method: "POST" });
                    const data = await res.json();
                    
                    if (!res.ok) { 
                        showNotification(data.error || "Erreur lors de la suppression", "danger"); 
                        return; 
                    }
                    
                    const row = document.querySelector(`tr[data-id="matiere-${id}"]`);
                    if (row) row.remove();
                    
                    showNotification("Matière supprimée avec succès", "success");
                    cleanupModal(document.getElementById("deleteMatModal"));
                    
                } catch (err) {
                    console.error(err);
                    showNotification("Erreur réseau lors de la suppression", "danger");
                    cleanupModal(document.getElementById("deleteMatModal"));
                }
            });
        }

        // ======================= EDITION MATIERE =======================
        window.editMat = id => {
            const row = document.querySelector(`tr[data-id="matiere-${id}"]`);
            const editMatForm = document.getElementById("editMatForm");
            if (!row || !editMatForm) return;
            
            document.getElementById("editMat_id").value = id;
            document.getElementById("editMat_code").value = row.querySelector(".col-code")?.innerText.trim() || "";
            document.getElementById("editMat_libelle").value = row.querySelector(".col-libelle")?.innerText.trim() || "";
            document.getElementById("editMat_type").value = row.querySelector(".col-type")?.innerText.trim() || "";
            
            const editModalEl = document.getElementById("editMatModal");
            if (typeof bootstrap !== 'undefined') {
                bootstrap.Modal.getOrCreateInstance(editModalEl).show();
            } else {
                editModalEl.style.display = 'block';
            }
        };

        const editMatForm = document.getElementById("editMatForm");
        if (editMatForm) {
            editMatForm.addEventListener("submit", async e => {
                e.preventDefault();
                
                if (!editMatForm.checkValidity()) {
                    editMatForm.classList.add("was-validated");
                    return;
                }
                
                const id = document.getElementById("editMat_id").value;
                const formData = new FormData(editMatForm);
                
                try {
                    const res = await fetch(`/matieres/update/${id}`, {
                        method: "POST",
                        body: formData
                    });
                    
                    const data = await res.json();
                    
                    if (!res.ok) {
                        showNotification(data.error || "Erreur lors de la modification", "danger");
                        return;
                    }
                    
                    showNotification("Matière modifiée avec succès", "success");
                    
                    const row = document.querySelector(`tr[data-id="matiere-${id}"]`);
                    if (row) {
                        row.querySelector(".col-code").textContent = data.code;
                        row.querySelector(".col-libelle").textContent = data.libelle;
                        row.querySelector(".col-type").textContent = data.type;
                    }
                    
                    editMatForm.reset();
                    editMatForm.classList.remove("was-validated");
                    cleanupModal(document.getElementById("editMatModal"));
                    
                } catch (err) {
                    console.error(err);
                    showNotification("Erreur réseau lors de la modification", "danger");
                }
            });
        }

        // ======================= DETAIL MATIERE =======================
        window.showMatDetail = async id => {
            try {
                const res = await fetch(`/matieres/detail/${id}`);
                const data = await res.json();
                if (!res.ok) { 
                    showNotification("Erreur récupération détail", "danger"); 
                    return; 
                }
                
                const detailMatContent = document.getElementById("detailMatContent");
                if (detailMatContent) {
                    detailMatContent.innerHTML = `
                        <p><b>Code:</b> ${data.code}</p>
                        <p><b>Libellé:</b> ${data.libelle}</p>
                        <p><b>Type:</b> ${data.type}</p>
                        <p><b>Etat:</b> ${data.etat || ""}</p>
                    `;
                }
                
                const detailModalEl = document.getElementById("detailMatModal");
                if (typeof bootstrap !== 'undefined') {
                    bootstrap.Modal.getOrCreateInstance(detailModalEl).show();
                } else {
                    detailModalEl.style.display = 'block';
                }
            } catch (err) {
                console.error(err);
                showNotification("Erreur réseau", "danger");
            }
        };
    }
});
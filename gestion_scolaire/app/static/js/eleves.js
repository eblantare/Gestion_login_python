// eleves.js - Version finale complète avec exports fonctionnels - v1.2

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

// Fonction utilitaire pour fermer les modales
function closeModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;
    
    if (typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        } else {
            // Si l'instance n'existe pas, créer une nouvelle instance et la fermer
            const newModal = new bootstrap.Modal(modalElement);
            newModal.hide();
        }
    } else {
        // Fallback sans Bootstrap
        modalElement.style.display = 'none';
        modalElement.classList.remove('show');
        document.body.classList.remove('modal-open');
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
    }
}

// Fonction utilitaire pour réinitialiser les formulaires
function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        form.classList.remove('was-validated');
    }
}

// FONCTION NOTIFICATION CORRIGÉE - HAUT DROITE
function showNotification(message, type = "success", delay = 4000) {
    console.log(`📢 Notification: ${message} (${type})`);
    
    // Créer une div Bootstrap simple
    const notificationEl = document.createElement('div');
    notificationEl.className = `alert alert-${type} alert-dismissible fade show`;
    notificationEl.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        margin: 10px;
    `;
    
    notificationEl.innerHTML = `
        <strong>${type === 'success' ? '✅' : type === 'danger' ? '❌' : '⚠️'}</strong>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Ajouter au body
    document.body.appendChild(notificationEl);
    
    // Initialiser le comportement Bootstrap si disponible
    if (typeof bootstrap !== 'undefined') {
        // Fermeture automatique après délai
        setTimeout(() => {
            if (notificationEl.parentNode) {
                const bsAlert = new bootstrap.Alert(notificationEl);
                bsAlert.close();
            }
        }, delay);
    } else {
        // Fallback sans Bootstrap
        setTimeout(() => {
            if (notificationEl.parentNode) {
                notificationEl.remove();
            }
        }, delay);
    }
    
    // Gestion de la fermeture manuelle
    notificationEl.querySelector('.btn-close').addEventListener('click', function() {
        if (notificationEl.parentNode) {
            notificationEl.remove();
        }
    });
}

// ========== GESTION DES EXPORTS ÉLÈVES ==========

// ========== GESTION DES EXPORTS ÉLÈVES ==========

// Variable pour suivre les exports en cours
let exportInProgress = false;

// Fonction pour initialiser les exports
function initializeExports() {
    console.log('🔄 Initialisation des exports élèves');
    
    // Gestion des clics sur les liens d'export
    const exportLinks = document.querySelectorAll('.export-link');
    console.log(`🔍 ${exportLinks.length} liens d'export trouvés`);
    
    exportLinks.forEach(link => {
        // Supprimer les écouteurs existants pour éviter les doublons
        link.replaceWith(link.cloneNode(true));
    });
    
    // Réattacher les écouteurs sur les nouveaux éléments
    document.querySelectorAll('.export-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const format = this.getAttribute('data-format');
            console.log(`🖱️ Clic sur export ${format}`);
            
            handleExport(format);
        });
    });
}

// Fonction centralisée pour gérer les exports
function handleExport(format) {
    // Empêcher les exports multiples
    if (exportInProgress) {
        console.log('⏳ Export déjà en cours, veuillez patienter...');
        showNotification('⏳ Export déjà en cours, veuillez patienter...', 'warning');
        return;
    }
    
    // CORRECTION RENFORCÉE: Vérification STRICTE de la classe - BLOQUER si aucune classe sélectionnée
    const classeSelectionValid = checkClasseSelection();
    console.log('🔍 Résultat vérification classe:', classeSelectionValid);
    
    if (!classeSelectionValid) {
        return;
    }
    
    exportInProgress = true;
    
    try {
        exportEleves(format);
    } catch (error) {
        console.error('❌ Erreur lors de l\'export:', error);
        showNotification('❌ Erreur lors de l\'export: ' + error.message, 'danger');
        exportInProgress = false;
    }
}

// Fonction principale d'export
function exportEleves(format) {
    try {
        console.log(`📤 Début de l'export ${format}`);
        
        // Récupérer l'ID de la classe
        let classeId = getCurrentClasseId();
        
        // Vérification finale de sécurité (double vérification)
        if (!classeId || classeId === 'null' || classeId === 'undefined') {
            showNotification('❌ Erreur: classe non spécifiée. Export annulé.', 'warning');
            exportInProgress = false;
            return;
        }

        console.log(`📤 Export ${format} pour la classe ID: ${classeId}`);
        
        // Afficher un indicateur de chargement
        showNotification(`⏳ Génération du fichier ${format.toUpperCase()} en cours...`, 'info', 3000);
        
        // Méthode unique pour éviter les doublons
        const url = `/eleves/export/${format}/${encodeURIComponent(classeId)}`;
        console.log(`🔗 URL d'export: ${url}`);
        
        // Créer un iframe invisible pour le téléchargement
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = url;
        document.body.appendChild(iframe);
        
        // Nettoyer après téléchargement
        setTimeout(() => {
            if (iframe.parentNode) {
                iframe.parentNode.removeChild(iframe);
            }
            exportInProgress = false;
        }, 10000);
        
        console.log(`✅ Export ${format} déclenché avec succès`);
        
    } catch (error) {
        console.error('❌ Erreur lors de l\'export:', error);
        showNotification('❌ Erreur lors de l\'export: ' + error.message, 'danger');
        exportInProgress = false;
    }
}


// Fonction pour récupérer l'ID de la classe actuelle - VERSION FIABLE
function getCurrentClasseId() {
    console.log('🔍 Recherche fiable de l\'ID de classe...');
    
    // 1. Chercher dans le filtre actuel (méthode la plus fiable)
    const filterSelect = document.querySelector('select[name="filter"]');
    if (filterSelect && filterSelect.value) {
        const filterValue = filterSelect.value;
        if (filterValue.startsWith('classe:')) {
            // Trouver l'option correspondante pour récupérer l'ID
            const selectedOption = filterSelect.options[filterSelect.selectedIndex];
            if (selectedOption && selectedOption.dataset.id) {
                console.log('✅ ID de classe trouvé via filtre data-id:', selectedOption.dataset.id);
                return selectedOption.dataset.id;
            }
        }
    }
    
    // 2. Vérifier dans l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlClasseId = urlParams.get('classe_id');
    if (urlClasseId && urlClasseId !== 'null' && urlClasseId !== 'undefined') {
        console.log('✅ ID de classe trouvé dans l\'URL:', urlClasseId);
        return urlClasseId;
    }
    
    // 3. Chercher dans la première ligne du tableau (fallback)
    const firstRow = document.querySelector('#table-eleves tbody tr');
    if (firstRow) {
        const classeCell = firstRow.querySelector('.col-classe');
        if (classeCell && classeCell.dataset.id) {
            console.log('✅ ID de classe trouvé dans le tableau:', classeCell.dataset.id);
            return classeCell.dataset.id;
        }
    }
    
    console.warn('❌ Aucun ID de classe valide trouvé');
    return null;
}

// Fonction pour vérifier si une classe est sélectionnée - VERSION STRICTE
function checkClasseSelection() {
    console.log('🔍 DÉBUT Vérification stricte de la sélection de classe');
    
    // 1. Vérifier si un filtre de classe est activement sélectionné
    const filterSelect = document.querySelector('select[name="filter"]');
    let isClasseSelected = false;
    let selectedClasseName = '';
    
    if (filterSelect && filterSelect.value) {
        const filterValue = filterSelect.value;
        console.log('🔍 Filtre actuel:', filterValue);
        
        if (filterValue.startsWith('classe:')) {
            isClasseSelected = true;
            selectedClasseName = filterValue.replace('classe:', '');
            console.log('✅ Classe sélectionnée dans le filtre:', selectedClasseName);
        } else {
            console.log('❌ Aucune classe sélectionnée dans le filtre');
        }
    } else {
        console.log('❌ Aucun filtre sélectionné ou filtre vide');
    }
    
    // 2. Vérifier que ce n'est pas la valeur par défaut vide
    if (!isClasseSelected) {
        showNotification('❌ Vous devez d\'abord sélectionner une classe spécifique dans le filtre avant de pouvoir exporter.', 'warning');
        return false;
    }
    
    // 3. Vérifier que l'ID de classe est valide
    const classeId = getCurrentClasseId();
    console.log('🔍 ID de classe récupéré:', classeId);
    
    if (!classeId || classeId === 'null' || classeId === 'undefined' || classeId === '') {
        showNotification('❌ Impossible de déterminer la classe sélectionnée. Veuillez réessayer.', 'warning');
        return false;
    }
    
    // 4. Vérification UUID
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(classeId)) {
        showNotification('❌ Identifiant de classe invalide. Veuillez sélectionner une classe valide.', 'warning');
        return false;
    }
    
    console.log('✅ Classe valide sélectionnée:', selectedClasseName, 'ID:', classeId);
    return true;
}

// Fonction pour nettoyer les backdrops
function cleanupModalBackdrops() {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => {
        backdrop.remove();
    });
    document.body.classList.remove('modal-open');
}

// Fonction pour mettre à jour l'état du bouton d'export
function updateExportButtonState() {
    const exportBtn = document.getElementById('exportDropdownBtn');
    const hasValidClasse = checkClasseSelectionSilent(); // Version silencieuse
    
    if (exportBtn) {
        if (!hasValidClasse) {
            exportBtn.disabled = true;
            exportBtn.title = "Sélectionnez d'abord une classe pour exporter";
            exportBtn.classList.add('btn-secondary');
            exportBtn.classList.remove('btn-success');
        } else {
            exportBtn.disabled = false;
            exportBtn.title = "Exporter la liste des élèves";
            exportBtn.classList.add('btn-success');
            exportBtn.classList.remove('btn-secondary');
        }
    }
}

// Version silencieuse de checkClasseSelection (sans notification)
function checkClasseSelectionSilent() {
    const filterSelect = document.querySelector('select[name="filter"]');
    let isClasseSelected = false;
    
    if (filterSelect && filterSelect.value) {
        const filterValue = filterSelect.value;
        if (filterValue.startsWith('classe:')) {
            isClasseSelected = true;
        }
    }
    
    if (!isClasseSelected) {
        return false;
    }
    
    const classeId = getCurrentClasseId();
    if (!classeId || classeId === 'null' || classeId === 'undefined' || classeId === '') {
        return false;
    }
    
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(classeId);
}

// Surveiller les changements de filtre
function monitorFilterChanges() {
    const filterSelect = document.querySelector('select[name="filter"]');
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            console.log('🔍 Filtre modifié, mise à jour état export...');
            setTimeout(updateExportButtonState, 100);
        });
    }
}
// ========== INITIALISATION PRINCIPALE ==========

document.addEventListener("DOMContentLoaded", () => {
    'use strict';

    // Variables globales pour le workflow
    let currentAction = null;
    let currentEleveId = null;
    let currentSelect = null;
    let actionConfirmed = false;

    // Initialisation avec gestion de la compatibilité
    waitForBootstrap().then(() => {
        console.log('✅ Bootstrap chargé - initialisation des élèves v1.2');
        initializeEleves();
    }).catch(err => {
        console.warn('⚠️ Initialisation sans Bootstrap:', err);
        initializeEleves();
    });

    function initializeEleves() {
        const confirmModalEl = document.getElementById("confirmActionModal");
        const confirmYesBtn = document.getElementById("confirmYesBtn");
        
        console.log('Initialisation eleves.js v1.2 - Cache forcé');

        // Nettoyer les backdrops existants au chargement
        cleanupModalBackdrops();

        // Activer les tooltip seulement si Bootstrap est disponible
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerlist = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerlist.map(function(tooltipTriggerEl){
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }

        // ✅ INITIALISER LES EXPORTS
        initializeExports();

         // ✅ SURVEILLER LES CHANGEMENTS DE FILTRE
        monitorFilterChanges();
    
       // ✅ METTRE À JOUR L'ÉTAT INITIAL DU BOUTON
        setTimeout(updateExportButtonState, 500);
        // Gestion des clics sur le tableau
        const table = document.getElementById("table-eleves");
        if (table) {
            table.addEventListener("click", function(e){
                // Bouton modifier
                const editBtn = e.target.closest(".btn-edit");
                if(editBtn){
                    console.log('Bouton modifier cliqué:', editBtn.dataset.id);
                    editEleve(editBtn.dataset.id);
                    return;
                }

                // Bouton détail
                const detailBtn = e.target.closest(".btn-detail");
                if(detailBtn){
                    console.log('Bouton détail cliqué:', detailBtn.dataset.id);
                    showDetail(detailBtn.dataset.id);
                    return;
                }

                // Bouton supprimer
                const deleteBtn = e.target.closest(".btn-danger");
                if(deleteBtn){
                    console.log('Bouton supprimer cliqué:', deleteBtn.dataset.id);
                    const id = deleteBtn.dataset.id;
                    if (!id) {
                        showNotification("Impossible de supprimer : identifiant non défini !", "danger");
                        return;
                    }
                    deleteEleve(id);
                    return;
                }
            });
        }

        // ---------- Bootstrap validation ----------
        (function () {
            const forms = document.querySelectorAll('.needs-validation');
            Array.from(forms).forEach(form => {
                form.addEventListener('submit', event => {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    form.classList.add('was-validated');
                }, false);
            });
        })();

        // ---------- Ajout élève (AJAX) ----------
        const addForm = document.getElementById("addForm");
        if (addForm) {
            addForm.replaceWith(addForm.cloneNode(true));
            const newAddForm = document.getElementById("addForm");
            newAddForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                newAddForm.classList.add("was-validated");
                if (!newAddForm.checkValidity()) return;
                const formData = new FormData(newAddForm);
                const res = await fetch("/eleves/add", { method: "POST", body: formData });
                if (res.ok) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById("addElModal"));
                    if (modal) modal.hide();
                    showNotification("Ajout réussi", "success");
                    location.reload();
                } else {
                    alert("Erreur lors de l'ajout");
                }
            });
        }

        // Réinitialiser le formulaire quand la modal se ferme
        const addModal = document.getElementById('addElModal');
        if (addModal) {
            addModal.addEventListener('hidden.bs.modal', function() {
                const form = document.getElementById('addForm');
                if (form) {
                    form.reset();
                    form.classList.remove('was-validated');
                }
            });
        }

        // Fonction pour vérifier les doublons AVANT ajout
        async function checkDuplicateEleve(nom, prenoms, classeId) {
            try {
                console.log(`🔍 Vérification doublon: ${nom} ${prenoms} - Classe: ${classeId}`);
                
                const response = await fetch('/eleves/check_duplicate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        nom: nom.toUpperCase().trim(),
                        prenoms: prenoms.trim(),
                        classe_id: classeId
                    })
                });
                
                if (!response.ok) {
                    console.error('❌ Erreur vérification doublon');
                    return false;
                }
                
                const data = await response.json();
                console.log('📊 Résultat vérification doublon:', data);
                
                return data.exists;
            } catch (error) {
                console.error('❌ Erreur vérification doublon:', error);
                return false;
            }
        }

        // ---------- Détail élève ----------
        window.showDetail = async function (id) {
            try {
                const res = await fetch(`/eleves/detail/${id}`);
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({ error: "Erreur serveur" }));
                    showNotification(errorData.error || "Erreur lors de la récupération des détails", "danger");
                    return;
                }
                const data = await res.json();
                const content = `
                <p><b>Matricule:</b> ${data.matricule}</p>
                <p><b>Nom:</b> ${data.nom}</p>
                <p><b>Prénoms:</b> ${data.prenoms}</p>
                <p><b>Date naissance:</b> ${data.date_naissance || ""}</p>
                <p><b>Sexe:</b> ${data.sexe}</p>
                <p><b>Status:</b> ${data.status}</p>
                <p><b>Classe:</b> ${data.classe}</p>
                <p><b>Etat:</b> ${data.etat || ""}</p>
                `;
                const detailContent = document.getElementById("detailContent");
                if (detailContent) detailContent.innerHTML = content;
                
                // Afficher la modal
                if (typeof bootstrap !== 'undefined') {
                const modal = new bootstrap.Modal(document.getElementById("detailModal"));
                modal.show();
                
                // Nettoyer à la fermeture
                document.getElementById("detailModal").addEventListener('hidden.bs.modal', function () {
                    cleanupModalBackdrops();
                });
                } else {
                document.getElementById("detailModal").style.display = 'block';
                }
            } catch (error) {
                console.error('Erreur détail:', error);
                showNotification("Erreur réseau", "danger");
            }
        };

        // ---------- Édition ----------
        window.editEleve = async function (id) {
            try {
                const res = await fetch(`/eleves/get/${id}`);
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({ error: "Erreur serveur" }));
                    showNotification(errorData.error || "Erreur lors de la récupération des données", "danger");
                    return;
                }
                const data = await res.json();
                
                document.getElementById("edit_id").value = id;
                document.getElementById("edit_matricule").value = data.matricule || "";
                document.getElementById("edit_nom").value = data.nom || "";
                document.getElementById("edit_prenoms").value = data.prenoms || "";
                document.getElementById("edit_date_naissance").value = data.date_naissance || "";

                // Sexe radio
                if (data.sexe === "M") {
                    document.getElementById("sexeM").checked = true;
                } else if (data.sexe === "F") {
                    document.getElementById("sexeF").checked = true;
                }

                // Status radio
                if (data.status === "Nouveau") {
                    document.getElementById("statusNouveau").checked = true;
                } else if (data.status === "Ancien") {
                    document.getElementById("statusAncien").checked = true;
                }

                // Classe select
                const selectClasse = document.getElementById("edit_classe");
                if (selectClasse) {
                    Array.from(selectClasse.options).forEach(opt => {
                        opt.selected = (opt.value === data.classe_id);
                    });
                }
                
                // Afficher la modal
                if (typeof bootstrap !== 'undefined') {
                const modal = new bootstrap.Modal(document.getElementById("editModal"));
                modal.show();
                
                // Nettoyer à la fermeture
                document.getElementById("editModal").addEventListener('hidden.bs.modal', function () {
                    cleanupModalBackdrops();
                });
                } else {
                document.getElementById("editModal").style.display = 'block';
                }
            } catch (error) {
                console.error('Erreur édition:', error);
                showNotification("Erreur réseau", "danger");
            }
        };

        const editForm = document.getElementById("editForm");
        if (editForm) {
            editForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                if (!e.target.checkValidity()) return;

                const id = document.getElementById("edit_id").value;
                const formData = new FormData(e.target);
                
                try {
                const res = await fetch(`/eleves/update/${id}`, { 
                    method: "POST", 
                    body: formData 
                });
                
                if (res.ok) {
                    const updated = await res.json();
                    console.log('Données mises à jour:', updated);
                    
                    // Fermer la modal
                    closeModal("editModal");
                    resetForm("editForm");
                    showNotification("Modification réussie", "success");
                    
                    // Mettre à jour la ligne du tableau sans recharger
                    const row = document.querySelector(`tr[data-id="eleve-${id}"]`);
                    if (row) {
                    // Mettre à jour les données de base
                    if (row.querySelector(".col-matricule")) 
                        row.querySelector(".col-matricule").textContent = updated.matricule;
                    if (row.querySelector(".col-nom")) 
                        row.querySelector(".col-nom").textContent = updated.nom;
                    if (row.querySelector(".col-prenoms")) 
                        row.querySelector(".col-prenoms").textContent = updated.prenoms;
                    if (row.querySelector(".col-date_naissance")) 
                        row.querySelector(".col-date_naissance").textContent = updated.date_naissance || "";
                    if (row.querySelector(".col-sexe")) 
                        row.querySelector(".col-sexe").textContent = updated.sexe;
                    if (row.querySelector(".col-status")) 
                        row.querySelector(".col-status").textContent = updated.status;
                    
                    // Mettre à jour la classe
                    const classeCell = row.querySelector(".col-classe");
                    if (classeCell) {
                        classeCell.dataset.id = updated.classe_id;
                        if (classeCell.querySelector(".badge")) {
                        classeCell.querySelector(".badge").textContent = updated.classe_nom || "";
                        }
                    }
                    }
                    
                } else {
                    const errorData = await res.json().catch(() => ({ error: "Erreur serveur" }));
                    showNotification(errorData.error || "Erreur lors de la modification", "danger");
                }
                } catch (error) {
                console.error('Erreur:', error);
                showNotification("Erreur réseau lors de la modification", "danger");
                }
            });
        }

        // ---------- Suppression ----------
        window.deleteEleve = async function (id) {
            try {
                const res = await fetch(`/eleves/get/${id}`);
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({ error: "Erreur serveur" }));
                    showNotification(errorData.error || "Erreur lors de la récupération des données", "danger");
                    return;
                }
                const data = await res.json();
                document.getElementById("delete_id").value = id;
                document.getElementById("delete_info").textContent = `${data.matricule} - ${data.nom} ${data.prenoms}`;
                
                // Afficher la modal
                if (typeof bootstrap !== 'undefined') {
                const modal = new bootstrap.Modal(document.getElementById("deleteModal"));
                modal.show();
                
                // Nettoyer à la fermeture
                document.getElementById("deleteModal").addEventListener('hidden.bs.modal', function () {
                    cleanupModalBackdrops();
                });
                } else {
                document.getElementById("deleteModal").style.display = 'block';
                }
            } catch (error) {
                console.error('Erreur suppression:', error);
                showNotification("Erreur réseau", "danger");
            }
        };

        const deleteForm = document.getElementById("deleteForm");
        if (deleteForm) {
            deleteForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const id = document.getElementById("delete_id").value;
                try {
                    const res = await fetch(`/eleves/delete/${id}`, { method: "POST" });
                    if (res.ok){
                    // Fermer la modal
                    closeModal("deleteModal");
                    showNotification("Suppression réussie", "success");
                    // Recharger après un court délai
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                    } else {
                        const errorData = await res.json().catch(() => ({ error: "Erreur serveur" }));
                        showNotification(errorData.error || "Erreur lors de la suppression", "danger");
                    }
                } catch (error) {
                    console.error('Erreur suppression:', error);
                    showNotification("Erreur réseau lors de la suppression", "danger");
                }
            });
        }

        // ---------- Workflow : changer état ----------

        // Fonction pour attacher le comportement workflow sur un select
        function attachWorkflowChange(select) {
            select.addEventListener("change", function () {
                const action = this.value;
                if (!action) return;

                currentAction = action;
                currentEleveId = this.dataset.id;
                currentSelect = this;
                actionConfirmed = false;

                // Message dans le modal
                const msgEl = document.getElementById("confirmMessage");
                if (msgEl) msgEl.textContent = `Voulez-vous vraiment ${action.toLowerCase()} cet élève ?`;

                // Ouvrir le modal
                if (typeof bootstrap !== 'undefined') {
                    const modal = new bootstrap.Modal(confirmModalEl);
                    modal.show();
                    
                    // Nettoyer à la fermeture
                    confirmModalEl.addEventListener('hidden.bs.modal', function () {
                        cleanupModalBackdrops();
                    });
                } else {
                    confirmModalEl.style.display = 'block';
                }
            });
        }

        // Attacher à tous les selects existants au chargement
        document.querySelectorAll(".select-action").forEach(attachWorkflowChange);

        // Si l'utilisateur confirme (Oui)
        if (confirmYesBtn) {
            confirmYesBtn.addEventListener("click", async function () {
                if (!currentAction || !currentEleveId || !currentSelect) return;

                confirmYesBtn.disabled = true;

                try {
                    const res = await fetch(`/eleves/${currentEleveId}/changer_etat`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ action: currentAction })
                    });

                    const data = await res.json();

                    if (!res.ok || data.error) {
                        const errorMessage = data.error || "Erreur lors de l'opération";
                        console.error(`❌ Erreur changement état: ${errorMessage}`);
                        showNotification(errorMessage, "danger");
                        currentSelect.value = "";
                        actionConfirmed = false;
                        
                        closeModal("confirmActionModal");
                        return;
                    }

                    // Succès : mise à jour
                    actionConfirmed = true;
                    
                    const successMessage = data.message || `État changé avec succès: ${data.etat}`;
                    const row = document.querySelector(`tr[data-id="eleve-${currentEleveId}"]`);
                    
                    if (!row) {
                        console.error("Ligne non trouvée pour l'élève:", currentEleveId);
                        showNotification(successMessage, "success");
                        closeModal("confirmActionModal");
                        return;
                    }
                    
                    // Mettre à jour le badge d'état
                    const etatCell = row.querySelector(".etat");
                    if (etatCell) {
                        const badge = etatCell.querySelector("span.badge");
                        if (badge) {
                            badge.textContent = data.etat;

                            // Mettre à jour la classe du badge
                            let badgeClass;
                            const etat = data.etat.toLowerCase();

                            if (etat === "inactif") {
                                badgeClass = "bg-secondary";
                            } else if (etat === "actif") {
                                badgeClass = "bg-success";
                            } else if (etat === "suspendu") {
                                badgeClass = "bg-warning text-dark";
                            } else if (etat === "validé") {
                                badgeClass = "bg-primary";
                            } else if (etat === "sorti") {
                                badgeClass = "bg-dark";
                            } else {
                                badgeClass = "bg-secondary";
                            }

                            badge.className = "badge " + badgeClass;
                            console.log('✅ Badge mis à jour:', data.etat, 'Classe:', badgeClass);
                        }

                        // Mettre à jour le select d'actions
                        updateWorkflowSelect(etatCell, data.etat);
                    }

                    // Mettre à jour les boutons d'action selon le nouvel état
                    const actionCell = row.querySelector('td.text-nowrap');
                    const btnEdit = actionCell ? actionCell.querySelector('.btn-edit') : null;
                    const btnDelete = actionCell ? actionCell.querySelector('.btn-danger') : null;

                    if (data.etat.toLowerCase() !== "inactif") {
                        if (btnEdit) btnEdit.remove();
                        if (btnDelete) btnDelete.remove();
                    }

                    // Fermer la modal et afficher la notification UNE SEULE FOIS
                    closeModal("confirmActionModal");
                    showNotification(successMessage, "success");

                } catch (err) {
                    console.error(err);
                    showNotification("Erreur réseau", "danger");
                    if (currentSelect) currentSelect.value = "";
                } finally {
                    confirmYesBtn.disabled = false;
                }
            });
        }

        // Fonction pour mettre à jour le select d'actions après modification
        function updateWorkflowSelect(etatCell, newEtat) {
            console.log('Mise à jour workflow select pour état:', newEtat);
            
            // Supprimer l'ancien select s'il existe
            const oldSelect = etatCell.querySelector('.select-action');
            if (oldSelect) {
                console.log('Suppression ancien select');
                oldSelect.remove();
            }

            // Vérifier si l'utilisateur est admin et si l'état n'est pas "Sorti"
            const userRole = document.body.dataset.userRole || '';
            const isAdmin = userRole.toLowerCase().includes('admin');
            const isNotSorti = newEtat.toLowerCase() !== "sorti";
            
            console.log('Admin:', isAdmin, 'Pas sorti:', isNotSorti);
            
            if (isAdmin && isNotSorti) {
                // Créer un nouveau select
                const newSelect = document.createElement("select");
                newSelect.className = "form-select form-select-sm d-inline-block w-auto ms-2 select-action";
                newSelect.dataset.id = currentEleveId;
                newSelect.style.display = 'inline-block';

                // Ajouter les options selon le nouvel état
                let options = `<option value="">---Action---</option>`;
                switch (newEtat.toLowerCase()) {
                case "inactif":
                    options += `<option value="Activer">Activer</option>`;
                    break;
                case "actif":
                    options += `<option value="Suspendre">Suspendre</option>`;
                    break;
                case "suspendu":
                    options += `<option value="Valider">Valider</option>`;
                    break;
                case "validé":
                    options += `<option value="Sortir">Sortir</option>`;
                    break;
                }
                newSelect.innerHTML = options;

                // Ajouter le nouveau select dans la cellule
                etatCell.appendChild(newSelect);
                console.log('Nouveau select ajouté pour état:', newEtat);

                // Réattacher le comportement
                attachWorkflowChange(newSelect);
            } else {
                console.log('Select non créé (admin:', isAdmin, 'état:', newEtat, ')');
            }
        }

        // Reset du select si modal fermé sans confirmation
        if (confirmModalEl) {
            confirmModalEl.addEventListener("hidden.bs.modal", function () {
                if (!actionConfirmed && currentSelect) {
                    currentSelect.value = "";
                }
                currentAction = null;
                currentEleveId = null;
                currentSelect = null;
                actionConfirmed = false;
                cleanupModalBackdrops();
            });

            // Fallback pour le cas où Bootstrap n'est pas disponible
            confirmModalEl.addEventListener("click", function(e) {
                if (e.target === this || e.target.classList.contains('btn-close')) {
                    if (!actionConfirmed && currentSelect) {
                        currentSelect.value = "";
                    }
                    currentAction = null;
                    currentEleveId = null;
                    currentSelect = null;
                    actionConfirmed = false;
                    this.style.display = 'none';
                    cleanupModalBackdrops();
                }
            });
        }

        // Nettoyer les backdrops au clic sur les boutons de fermeture
        document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(btn => {
            btn.addEventListener('click', cleanupModalBackdrops);
        });
    }
});

// Ajouter les exports au scope global
window.exportEleves = exportEleves;
window.getCurrentClasseId = getCurrentClasseId;
window.checkClasseSelection = checkClasseSelection;
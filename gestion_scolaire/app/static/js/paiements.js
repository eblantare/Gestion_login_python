document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // ======================
  // GESTION D'ÉTAT GLOBALE
  // ======================
  const appState = {
    isSubmitting: false,
    pendingRequests: new Set(),
    lastSubmissionTime: 0
  };

  // ======================
  // 1️⃣ Filtrage par classe et per_page
  // ======================
  function initFilterClasse() {
    const classeSelect = document.querySelector("select[name='classe_id']");
    const perPageSelect = document.querySelector("select[name='per_page']");
    const filterForm = document.getElementById("filterForm");
    
    classeSelect?.addEventListener("change", () => filterForm?.submit());
    perPageSelect?.addEventListener("change", () => filterForm?.submit());
  }

  // ======================
  // 2️⃣ Calcul montant restant
  // ======================
  function bindCalculRest(montantNetInput, montantPayInput, montantRestInput) {
    if (!montantNetInput || !montantPayInput || !montantRestInput) return;
    
    const calculerRest = () => {
      const net = parseFloat(montantNetInput.value) || 0;
      const pay = parseFloat(montantPayInput.value) || 0;
      const reste = net - pay;
      
      montantRestInput.value = reste.toFixed(2);
      
      montantRestInput.classList.remove('text-danger', 'text-success', 'text-warning');
      if (reste < 0) {
        montantRestInput.classList.add('text-danger');
      } else if (reste === 0) {
        montantRestInput.classList.add('text-success');
      } else {
        montantRestInput.classList.add('text-warning');
      }
    };
    
    montantNetInput.addEventListener("input", calculerRest);
    montantPayInput.addEventListener("input", calculerRest);
    calculerRest();
  }

  function initCalculRest() {
    bindCalculRest(
      document.getElementById("montant_net"),
      document.getElementById("montant_pay"),
      document.getElementById("montant_rest")
    );
  }

  // ======================
  // 3️⃣ Modal confirmation
  // ======================
  let confirmModal = null;
  let confirmMessageEl = null;
  let confirmYesBtn = null;
  let confirmCallback = null;

  function initConfirmModal() {
    const modalEl = document.getElementById("confirmPayActionModal");
    if (!modalEl) return;

    confirmModal = new bootstrap.Modal(modalEl, { backdrop: 'static' });
    confirmMessageEl = document.getElementById("confirmPayMessage");
    confirmYesBtn = document.getElementById("confirmYesPayBtn");

    confirmYesBtn.addEventListener("click", () => {
      if (confirmCallback) confirmCallback();
      confirmModal.hide();
    });

    modalEl.addEventListener("hidden.bs.modal", () => confirmCallback = null);
  }

  function showConfirm(message, callback) {
    if (!confirmModal || !confirmMessageEl) return;
    confirmMessageEl.textContent = message;
    confirmCallback = callback;
    confirmModal.show();
  }

// ======================
// 4️⃣ NOTIFICATIONS SIMPLIFIÉES
// ======================
function showNotification(message, type = "success", delay = 3000) {
    console.log('🔔 Notification:', message);
    
    const container = document.getElementById("notificationContainer");
    if (!container) return;
    
    // Vider TOUTES les anciennes notifications
    container.innerHTML = '';
    
    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-bg-${type} border-0 mb-2`;
    toastEl.role = "alert";
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: delay });
    toast.show();
}

  function cleanupExpiredNotifications() {
    const container = document.getElementById("notificationContainer");
    if (!container) return;
    
    const now = Date.now();
    const toasts = container.querySelectorAll('.toast');
    
    toasts.forEach(toast => {
      const createdAt = parseInt(toast.dataset.createdAt || '0');
      const notificationKey = toast.dataset.notificationKey;
      
      if (!toast.classList.contains('show') || (now - createdAt) > 10000) {
        if (notificationKey) activeNotifications.delete(notificationKey);
        toast.remove();
      }
    });
  }

  setInterval(cleanupExpiredNotifications, 3000);

  // ======================
  // 5️⃣ Workflow paiements
  // ======================
  function initWorkflowButtons() {
    document.querySelectorAll(".select-action").forEach(select => {
      select.addEventListener("change", workflowChangeHandler);
    });
  }

  function workflowChangeHandler(e) {
    const action = e.target.value;
    if (!action) return;

    const paiementId = e.target.dataset.id;
    const currentSelect = e.target;

    showConfirm(`Voulez-vous vraiment ${action.toLowerCase()} ce paiement ?`, async () => {
      // Protection contre les doublons
      const requestKey = `workflow-${paiementId}-${Date.now()}`;
      if (appState.pendingRequests.has(requestKey)) return;
      appState.pendingRequests.add(requestKey);

      try {
        const res = await fetch(`/paiements/workflow/${paiementId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action })
        });
        
        if (!res.ok) throw new Error('Erreur réseau');
        
        const result = await res.json();

        if (result.error) {
          showNotification(result.error, "danger");
        } else {
          showNotification(result.message || "Action effectuée avec succès", "success");
          setTimeout(() => window.location.reload(), 1500);
        }
      } catch (err) {
        console.error(err);
        showNotification("Erreur lors de la modification de l'état", "danger");
      } finally {
        appState.pendingRequests.delete(requestKey);
        currentSelect.value = "";
      }
    });
  }

  // ======================
  // 6️⃣ Paiement Actions
  // ======================
  function initPaiementActions() {
    const tbody = document.querySelector("table tbody");
    tbody?.addEventListener("click", async (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      
      const paiementId = btn.dataset.id;
      if (!paiementId) return;

      if (btn.classList.contains("btnPay-detail")) {
        showDetailPaiement(paiementId);
      } else if (btn.classList.contains("btnPay-edit")) {
        showEditPaiementModal(paiementId);
      } else if (btn.classList.contains("btnPay-delete")) {
        showConfirm("Voulez-vous vraiment supprimer ce paiement ?", () => deletePaiement(paiementId));
      }
    });
  }

  async function showDetailPaiement(id) {
    try {
      const res = await fetch(`/paiements/detail/${id}`);
      if (!res.ok) throw new Error('Erreur chargement détails');
      
      const p = await res.json();
      const modal = new bootstrap.Modal(document.getElementById("paiementDetailModal"));
      
      document.getElementById("detail_code").textContent = p.code;
      document.getElementById("detail_eleve").textContent = p.eleve;
      document.getElementById("detail_classe").textContent = p.classe;
      document.getElementById("detail_libelle").textContent = p.libelle;
      document.getElementById("detail_date").textContent = p.date_payement;
      document.getElementById("detail_montant_net").textContent = (p.montant_net || 0).toFixed(2);
      document.getElementById("detail_montant_pay").textContent = (p.montant_pay || 0).toFixed(2);
      document.getElementById("detail_montant_rest").textContent = (p.montant_rest || 0).toFixed(2);
      
      modal.show();
    } catch (error) {
      console.error('Erreur détail paiement:', error);
      showNotification('Erreur lors du chargement des détails', 'danger');
    }
  }

  async function showEditPaiementModal(id) {
    try {
      const res = await fetch(`/paiements/detail/${id}`);
      if (!res.ok) throw new Error('Erreur chargement données');
      
      const p = await res.json();
      const modalEl = document.getElementById("paiementEditModal");
      const modal = new bootstrap.Modal(modalEl);

      const eleveSelect = document.getElementById("edit_eleve_id");
      const classeSelect = document.getElementById("edit_classe_id");
      
      if (eleveSelect && classeSelect) {
        eleveSelect.innerHTML = `<option value="${p.eleve_id}" selected>${p.eleve}</option>`;
        classeSelect.innerHTML = `<option value="${p.classe_id}" selected>${p.classe}</option>`;
        eleveSelect.disabled = true;
        classeSelect.disabled = true;
      }

      document.getElementById("edit_paiement_id").value = p.id;
      document.getElementById("edit_libelle").value = p.libelle || '';
      document.getElementById("edit_date_payement").value = p.date_payement || '';
      document.getElementById("edit_montant_net").value = p.montant_net || 0;
      document.getElementById("edit_montant_pay").value = p.montant_pay || 0;
      document.getElementById("edit_montant_rest").value = (p.montant_rest || 0).toFixed(2);

      bindCalculRest(
        document.getElementById("edit_montant_net"),
        document.getElementById("edit_montant_pay"),
        document.getElementById("edit_montant_rest")
      );

      modal.show();
    } catch (error) {
      console.error('Erreur édition paiement:', error);
      showNotification('Erreur lors du chargement des données', 'danger');
    }
  }

// ======================
// SUPPRESSION - CORRECTION DÉFINITIVE
// ======================
async function deletePaiement(id) {
    console.log('🗑️ Début suppression paiement:', id);
    
    // État local simple
    let isDeleting = false;
    
    if (isDeleting) {
        console.log('🚫 Suppression déjà en cours');
        return;
    }
    
    isDeleting = true;

    try {
        const response = await fetch(`/paiements/delete/${id}`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        console.log('📨 Réponse suppression:', response.status);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('📊 Résultat suppression:', result);

        // UNE SEULE NOTIFICATION
        if (result.status === "success") {
            showNotification("Paiement supprimé avec succès", "success");
            setTimeout(() => {
                window.location.reload();
            }, 1200);
        } else {
            showNotification(result.message || "Erreur lors de la suppression", "danger");
        }
        
    } catch (error) {
        console.error('❌ Erreur suppression:', error);
        showNotification("Erreur lors de la suppression", "danger");
    } finally {
        isDeleting = false;
    }
}

  // ======================
  // 7️⃣ Formulaire édition
  // ======================
  function initEditForm() {
    const editForm = document.getElementById("editPaiementForm");
    if (!editForm) return;

    editForm.addEventListener("submit", (e) => {
      e.preventDefault();
      
      showConfirm("Voulez-vous vraiment modifier ce paiement ?", async () => {
        const paiementId = editForm.edit_paiement_id.value;
        const requestKey = `edit-${paiementId}-${Date.now()}`;
        if (appState.pendingRequests.has(requestKey)) return;
        appState.pendingRequests.add(requestKey);

        try {
          const res = await fetch(`/paiements/edit/${paiementId}`, { 
            method: "POST", 
            body: new FormData(editForm) 
          });
          
          if (!res.ok) throw new Error('Erreur réseau');
          
          const result = await res.json();
          
          if (result.status === "success") {
            showNotification(result.message, "success");
            bootstrap.Modal.getInstance(document.getElementById("paiementEditModal"))?.hide();
            setTimeout(() => window.location.reload(), 1500);
          } else {
            const errorMessage = result.message || result.error || "Erreur lors de la modification";
            showNotification(errorMessage, "warning");
          }
        } catch (err) {
          console.error('Erreur modification paiement:', err);
          showNotification("Erreur lors de la modification du paiement", "danger");
        } finally {
          appState.pendingRequests.delete(requestKey);
        }
      });
    });
  }

  // ======================
  // 8️⃣ Synchronisation élève ↔ classe
  // ======================
  function initEleveClasseSync() {
    const eleveSelect = document.getElementById("eleve_id");
    const classeSelect = document.getElementById("classe_id");
    if (!eleveSelect || !classeSelect) return;

    eleveSelect.addEventListener("change", () => {
      const selectedOption = eleveSelect.options[eleveSelect.selectedIndex];
      const classeId = selectedOption?.dataset.classeId;
      if (classeId) {
        classeSelect.value = classeId;
      }
    });
  }

// ======================
// 9️⃣ AJOUT PAIEMENT - CORRECTION DÉFINITIVE DES DOUBLONS
// ======================
function addPaiementInit() {
    const paiementForm = document.getElementById("paiementForm");
    if (!paiementForm) return;

    setDefaultDate();

    // État local renforcé
    let isSubmitting = false;
    let lastSubmitTime = 0;

    paiementForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        console.log('=== DÉBUT SOUMISSION FORMULAIRE ===');
        
        // Protection renforcée contre les doublons
        const now = Date.now();
        if (isSubmitting || (now - lastSubmitTime < 3000)) {
            console.log('🚫 SOUMISSION BLOQUÉE - Déjà en cours ou trop rapide');
            return;
        }
        
        isSubmitting = true;
        lastSubmitTime = now;
        
        const submitButton = paiementForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        
        submitButton.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Ajout en cours...';
        submitButton.disabled = true;

        try {
            const formData = new FormData(paiementForm);
            
            // Créer une clé unique pour cette soumission
            const submissionKey = `${formData.get('eleve_id')}-${formData.get('libelle')}-${formData.get('date_payement')}-${now}`;
            console.log('📦 Soumission avec clé:', submissionKey);
            
            const response = await fetch(paiementForm.action, {
                method: "POST",
                body: formData,
                // Ajouter un header pour identifier la requête
                headers: {
                    'X-Submission-Key': submissionKey
                }
            });
            
            console.log('📨 Statut réponse:', response.status);
            
            if (!response.ok) {
                // Si c'est une erreur 429 (trop de requêtes), c'est normal
                if (response.status === 429) {
                    console.log('⚠️ Requête doublon détectée par le serveur');
                    const result = await response.json();
                    showNotification(result.message || "Cette action a déjà été effectuée", "warning");
                    return;
                }
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📊 Résultat serveur:', result);
            
            if (result.status === "success") {
                // UNE SEULE NOTIFICATION
                showNotification("Paiement ajouté avec succès", "success");
                
                // Fermer le modal IMMÉDIATEMENT
                const modal = bootstrap.Modal.getInstance(document.getElementById("paiementModal"));
                if (modal) {
                    modal.hide();
                }
                
                // Réinitialiser le formulaire
                paiementForm.reset();
                setDefaultDate();
                document.getElementById("montant_rest").value = "";
                
                // Recharger la page après 1.5 secondes
                setTimeout(() => {
                    console.log('🔄 Rechargement de la page');
                    window.location.reload();
                }, 1500);
                
            } else {
                // Si c'est un warning pour doublon, afficher un message spécifique
                if (result.status === "warning") {
                    showNotification(result.message || "Cet élève a déjà un paiement pour cette date", "warning");
                } else {
                    showNotification(result.message || "Erreur lors de l'ajout", "warning");
                }
            }
            
        } catch (error) {
            console.error('❌ Erreur:', error);
            showNotification("Erreur lors de l'ajout du paiement", "danger");
        } finally {
            // Réactiver le bouton après un délai
            setTimeout(() => {
                isSubmitting = false;
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
                console.log('=== FIN SOUMISSION FORMULAIRE ===');
            }, 2000);
        }
    });

    // Réinitialiser l'état quand le modal se ferme
    const modal = document.getElementById("paiementModal");
    if (modal) {
        modal.addEventListener('hidden.bs.modal', () => {
            isSubmitting = false;
            lastSubmitTime = 0;
            const submitButton = paiementForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-plus-circle me-1"></i>Ajouter';
            }
        });
    }
}

  function setDefaultDate() {
    const dateInput = document.getElementById("date_payement");
    if (dateInput) {
      const today = new Date().toISOString().split('T')[0];
      dateInput.value = today;
    }
  }
  // ======================
// 🔍 RECHERCHE AUTOMATIQUE AVEC DÉLAI
// ======================
function initSearchFunctionality() {
    const searchInput = document.querySelector('input[name="search"]');
    const searchButton = document.querySelector('.search-btn');
    const filterForm = document.getElementById("filterForm");
    
    if (!searchInput || !filterForm) return;
    
    console.log('🔍 Initialisation de la recherche...');
    
    let searchTimeout;
    
    // Recherche automatique lors de la frappe (avec délai)
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const searchTerm = this.value.trim();
            console.log('🔍 Recherche en cours:', searchTerm);
            
            // Soumettre le formulaire
            filterForm.submit();
        }, 800); // Délai de 800ms
    });
    
    // Recherche immédiate avec le bouton
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            console.log('🔍 Recherche manuelle déclenchée');
            filterForm.submit();
        });
    }
    
    // Soumission avec Enter
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            console.log('🔍 Recherche avec Enter');
            filterForm.submit();
        }
    });
}

// ======================
// 📤 EXPORT LISTE PAIEMENTS PAR CLASSE
// ======================
function initExportListe() {
    const btnExport = document.getElementById("btnExportList");
    const classeSelect = document.querySelector("select[name='classe_id']");
    
    if (!btnExport || !classeSelect) return;
    
    console.log('📤 Initialisation export liste...');
    
    // Activer/désactiver le bouton selon la sélection de classe
    function updateExportButton() {
        const isClasseSelected = classeSelect.value !== "";
        btnExport.disabled = !isClasseSelected;
        
        if (isClasseSelected) {
            btnExport.classList.remove('btn-outline-secondary');
            btnExport.classList.add('btn-outline-info');
        } else {
            btnExport.classList.remove('btn-outline-info');
            btnExport.classList.add('btn-outline-secondary');
        }
    }
    
    // Mettre à jour l'état du bouton au chargement
    updateExportButton();
    
    // Mettre à jour quand la classe change
    classeSelect.addEventListener('change', updateExportButton);
    
    // Gestion du clic sur le bouton d'export
    btnExport.addEventListener('click', async function() {
        const classeId = classeSelect.value;
        if (!classeId) {
            showNotification("Veuillez sélectionner une classe pour exporter", "warning");
            return;
        }
        
        console.log('📤 Export liste pour classe:', classeId);
        
        // Afficher un indicateur de chargement
        const originalHtml = this.innerHTML;
        this.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Génération...';
        this.disabled = true;
        
        try {
            const response = await fetch(`/paiements/export/liste/classe?classe_id=${classeId}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Erreur lors de l'export");
            }
            
            // Télécharger le fichier
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Récupérer le nom du fichier depuis les headers
            const contentDisposition = response.headers.get('content-disposition');
            let filename = `liste_paiements_${new Date().toISOString().split('T')[0]}.pdf`;
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showNotification("Liste exportée avec succès", "success");
            
        } catch (error) {
            console.error('❌ Erreur export liste:', error);
            showNotification(error.message || "Erreur lors de l'export", "danger");
        } finally {
            // Restaurer le bouton
            this.innerHTML = originalHtml;
            this.disabled = false;
        }
    });
}

// ======================
// 🔹 Initialisation globale
// ======================
function init() {
    initConfirmModal();
    initFilterClasse();
    initCalculRest();
    initPaiementActions();
    initEditForm();
    initWorkflowButtons();
    initEleveClasseSync();
    addPaiementInit();
    
    // 🔍 AJOUT DE LA RECHERCHE
    initSearchFunctionality();
    
    // 📤 AJOUT DE L'EXPORT LISTE
    initExportListe();
    
    console.log('✅ Module paiements initialisé avec recherche et export');
}

  init();
});
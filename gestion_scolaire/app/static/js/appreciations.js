// appreciations.js - Version avec compatibilité

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
      console.log('✅ Bootstrap chargé - initialisation des appréciations');
      initializeAppreciations();
  }).catch(err => {
      console.warn('⚠️ Initialisation sans Bootstrap:', err);
      initializeAppreciations();
  });

  function initializeAppreciations() {
    // ======================= //
    // INITIALISATION GÉNÉRALE //
    // ======================= //

    // Activer les tooltips seulement si Bootstrap est disponible
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerlist = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerlist.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

      initializeEventListeners();

    // Validation Bootstrap
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

    // ======================= //
    // GESTION DE L'ÉCHELLE DYNAMIQUE //
    // ======================= //

    // Gestion de l'échelle dans le modal d'ajout
    const echelleSelect = document.getElementById('add_echelle_max');
    const customContainer = document.getElementById('custom_echelle_container');
    const seuilMinInput = document.getElementById('add_seuil_min');
    const seuilMaxInput = document.getElementById('add_seuil_max');

    if (echelleSelect) {
      echelleSelect.addEventListener('change', function() {
        if (this.value === 'custom') {
          customContainer.style.display = 'block';
          // Réinitialiser les max des seuils
          if (seuilMinInput) seuilMinInput.max = '';
          if (seuilMaxInput) seuilMaxInput.max = '';
        } else {
          customContainer.style.display = 'none';
          // Mettre à jour les max des seuils selon l'échelle
          const echelleMax = parseFloat(this.value);
          if (seuilMinInput) {
            seuilMinInput.max = echelleMax;
            seuilMinInput.placeholder = `0-${echelleMax}`;
          }
          if (seuilMaxInput) {
            seuilMaxInput.max = echelleMax;
            seuilMaxInput.placeholder = `0-${echelleMax}`;
          }
        }
      });

      // Déclencher l'événement au chargement
      echelleSelect.dispatchEvent(new Event('change'));
    }

    // ======================= //
    // GESTION DES INTERACTIONS DU TABLEAU //
    // ======================= //

    const table = document.getElementById("table-appreciations");
    if (table) {
      table.addEventListener("click", function (e) {
        // Bouton modifier
        const editBtn = e.target.closest(".btn-edit");
        if (editBtn) {
          editAppreciation(editBtn.dataset.id);
          return;
        }

        // Bouton détail
        const detailBtn = e.target.closest(".btn-detail");
        if (detailBtn) {
          showAppDetail(detailBtn.dataset.id);
          return;
        }

        // Bouton supprimer
        const deleteBtn = e.target.closest(".btn-delete");
        if (deleteBtn) {
          const id = deleteBtn.dataset.id;
          if (!id) {
            showNotification("Impossible de supprimer : identifiant non défini !", "danger");
            return;
          }
          deleteAppreciation(id);
          return;
        }
      });
    }

    // ======================= //
    // FONCTIONS CRUD - APPRÉCIATIONS //
    // ======================= //


    // Validation des seuils avant soumission
function validateSeuils(seuilMin, seuilMax, echelleMax) {
  if (seuilMin >= seuilMax) {
    showNotification("Le seuil min doit être inférieur au seuil max", "danger");
    return false;
  }
  
  if (seuilMin < 0 || seuilMax > echelleMax) {
    showNotification(`Les seuils doivent être entre 0 et ${echelleMax}`, "danger");
    return false;
  }
  
  return true;
  }
    // ---------- Ajout appréciation (AJAX) ----------
    const addAppForm = document.getElementById("addAppForm");
    if (addAppForm) {
      // Cloner le formulaire pour éviter les duplications d'écouteurs
      addAppForm.replaceWith(addAppForm.cloneNode(true));
      const newAddAppForm = document.getElementById("addAppForm");
      
      // Gestion de la soumission avec échelle personnalisée
      newAddAppForm.addEventListener('submit', function(e) {
        const echelleSelect = document.getElementById('add_echelle_max');
        const customInput = document.getElementById('add_echelle_custom');
        
        // Si échelle personnalisée, utiliser la valeur du champ personnalisé
        if (echelleSelect && echelleSelect.value === 'custom' && customInput && customInput.value) {
          // Créer un champ caché pour l'échelle
          const hiddenInput = document.createElement('input');
          hiddenInput.type = 'hidden';
          hiddenInput.name = 'echelle_max';
          hiddenInput.value = customInput.value;
          this.appendChild(hiddenInput);
        }
      });

      newAddAppForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        newAddAppForm.classList.add("was-validated");
        
        if (!newAddAppForm.checkValidity()) {
          console.log("❌ Formulaire invalide");
          return;
        }
        const seuilMin = parseFloat(document.getElementById('add_seuil_min').value);
        const seuilMax = parseFloat(document.getElementById('add_seuil_max').value);
        const echelleMax = parseFloat(document.getElementById('add_echelle_max').value);
         if (!validateSeuils(seuilMin, seuilMax, echelleMax)) {
          return;
       }
        const formData = new FormData(newAddAppForm);
        
        // DEBUG: Afficher les données envoyées
        console.log("📤 Données envoyées:");
        for (let [key, value] of formData.entries()) {
          console.log(`   ${key}: ${value}`);
        }

        try {
          const res = await fetch("/appreciations/add", { 
            method: "POST", 
            body: formData 
          });
          
          const data = await res.json();
          console.log("📥 Réponse serveur:", data);
          
          if (res.ok) {
            // Fermer la modal seulement si Bootstrap est disponible
            if (typeof bootstrap !== 'undefined') {
              const modal = bootstrap.Modal.getInstance(document.getElementById("addAppModal"));
              if (modal) modal.hide();
            } else {
              // Fallback simple pour cacher la modal
              document.getElementById("addAppModal").style.display = 'none';
            }
            showNotification(data.message || "Ajout réussi", "success");
            
            // Recharger après un délai pour voir la notification
            setTimeout(() => location.reload(), 1500);
          } else {
            showNotification(data.error || "Erreur lors de l'ajout", "danger");
          }
        } catch (err) {
          console.error("❌ Erreur réseau:", err);
          showNotification("Erreur réseau lors de l'ajout", "danger");
        }
      });
    }

    // ---------- Édition appréciation ----------
    window.editAppreciation = async function(id) {
      try {
        const res = await fetch(`/appreciations/get/${id}`);
        if (!res.ok) {
          showNotification(`Erreur récupération appréciation : ${res.status}`, "danger");
          return;
        }
        
        const data = await res.json();

        // Remplir le formulaire d'édition
        document.getElementById("editApp_id").value = data.id;
        document.getElementById("editApp_libelle").value = data.libelle;
        document.getElementById("editApp_seuil_min").value = data.seuil_min;
        document.getElementById("editApp_seuil_max").value = data.seuil_max;
        document.getElementById("editApp_description").value = data.description;

        // Afficher l'échelle en lecture seule
        const echelleField = document.getElementById("editApp_echelle_max");
        if (echelleField) {
          echelleField.value = data.echelle_max || 20;
        }

        // Afficher la modal selon la disponibilité de Bootstrap
        if (typeof bootstrap !== 'undefined') {
          bootstrap.Modal.getOrCreateInstance(document.getElementById("editAppModal")).show();
        } else {
          document.getElementById("editAppModal").style.display = 'block';
        }
        
      } catch (err) {
        console.error("Erreur édition:", err);
        showNotification("Erreur lors du chargement des données", "danger");
      }
    };

    // Gestion de la soumission du formulaire d'édition
    const editAppForm = document.getElementById("editAppForm");
    if (editAppForm && !editAppForm.dataset.listenerAttached) {
      editAppForm.dataset.listenerAttached = "true";

      editAppForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!e.target.checkValidity()) return;

        const id = document.getElementById("editApp_id").value;
        const formData = new FormData(e.target);

        const row = document.querySelector(`tr[data-id="appreciation-${id}"]`);
        if (!row) {
          showNotification("Impossible de trouver l'appréciation dans le tableau", "danger");
          return;
        }

        // Vérifier s'il y a des modifications
        const originalLibelle = row.querySelector(".col-libelle")?.innerText.trim() || "";
        const originalSeuilMin = row.querySelector(".col-seuil_min")?.innerText.trim() || "";
        const originalSeuilMax = row.querySelector(".col-seuil_max")?.innerText.trim() || "";
        const originalDescription = row.querySelector(".col-description")?.innerText.trim() || "";

        if (
          formData.get("libelle") === originalLibelle &&
          String(formData.get("seuil_min")) === originalSeuilMin &&
          String(formData.get("seuil_max")) === originalSeuilMax &&
          formData.get("description") === originalDescription
        ) {
          if (typeof bootstrap !== 'undefined') {
            bootstrap.Modal.getInstance(document.getElementById("editAppModal"))?.hide();
          } else {
            document.getElementById("editAppModal").style.display = 'none';
          }
          showNotification("Aucune modification détectée", "info");
          return;
        }

        try {
          const res = await fetch(`/appreciations/update/${id}`, { 
            method: "POST", 
            body: formData 
          });
          const updated = await res.json();

          if (!res.ok) {
            showNotification(updated.error || "Erreur lors de la modification", "danger");
            return;
          }

          // Mise à jour du tableau
          updateTableRow(id, updated);

          if (typeof bootstrap !== 'undefined') {
            bootstrap.Modal.getInstance(document.getElementById("editAppModal"))?.hide();
          } else {
            document.getElementById("editAppModal").style.display = 'none';
          }
          showNotification("Modification réussie", "success");
        } catch (err) {
          console.error(err);
          showNotification("Erreur serveur lors de la modification", "danger");
        }
      });
    }

    // ---------- Détail appréciation ----------
    window.showAppDetail = async function (id) {
      try {
        const res = await fetch(`/appreciations/detail/${id}`);
        if (!res.ok) {
          showNotification("Erreur lors de la récupération des détails", "danger");
          return;
        }
        
        const data = await res.json();
        const content = `
          <p><b>Libellé:</b> ${data.libelle}</p>
          <p><b>Seuil minimal:</b> ${data.seuil_min}</p>
          <p><b>Seuil maximal:</b> ${data.seuil_max}</p>
          <p><b>Échelle maximale:</b> ${data.echelle_max || 20}</p>
          <p><b>Description:</b> ${data.description || "—"}</p>
          <p><b>État:</b> ${data.etat || ""}</p>
        `;
        
        const detailAppContent = document.getElementById("detailAppContent");
        if (detailAppContent) {
          detailAppContent.innerHTML = content;
          if (typeof bootstrap !== 'undefined') {
            new bootstrap.Modal(document.getElementById("detailAppModal")).show();
          } else {
            document.getElementById("detailAppModal").style.display = 'block';
          }
        }
      } catch (err) {
        console.error("Erreur détail:", err);
        showNotification("Erreur lors du chargement des détails", "danger");
      }
    };

    // ---------- Suppression appréciation ----------
    window.deleteAppreciation = async function (id) {
      try {
        const res = await fetch(`/appreciations/get/${id}`);
        if (!res.ok) {
          showNotification("Impossible de récupérer l'appréciation", "danger");
          return;
        }

        const data = await res.json();
        document.getElementById("deleteApp_id").value = id;
        document.getElementById("deleteApp_info").textContent = `${data.libelle} - ${data.description || "Sans description"}`;
        if (typeof bootstrap !== 'undefined') {
          new bootstrap.Modal(document.getElementById("deleteAppModal")).show();
        } else {
          document.getElementById("deleteAppModal").style.display = 'block';
        }
      } catch (err) {
        console.error("Erreur suppression:", err);
        showNotification("Erreur lors de la préparation de la suppression", "danger");
      }
    };

    // Gestion de la soumission du formulaire de suppression
    const deleteAppForm = document.getElementById("deleteAppForm");
    if (deleteAppForm) {
      deleteAppForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("deleteApp_id").value;
        
        try {
          const res = await fetch(`/appreciations/delete/${id}`, { method: "POST" });
          if (res.ok) {
            location.reload();
          } else {
            const data = await res.json();
            showNotification(data.error || "Erreur lors de la suppression", "danger");
          }
        } catch (err) {
          console.error("Erreur suppression:", err);
          showNotification("Erreur réseau lors de la suppression", "danger");
        }
      });
    }

    // ======================= //
    // WORKFLOW - CHANGEMENT D'ÉTAT //
    // ======================= //

    const confirmModalApp = document.getElementById("confirmActionAppModal");
    const confirmYesAppBtn = document.getElementById("confirmYesAppBtn");

    let currentAction = null;
    let currentAppreciationId = null;
    let currentSelect = null;
    let actionConfirmed = false;

    function attachWorkflowChange(select) {
      select.addEventListener("change", function () {
        const action = this.value;
        if (!action) return;

        currentAction = action;
        currentAppreciationId = this.dataset.id;
        currentSelect = this;
        actionConfirmed = false;

        const msgEl = document.getElementById("confirmAppMessage");
        if (msgEl) {
          msgEl.textContent = `Voulez-vous vraiment ${action.toLowerCase()} cette appréciation ?`;
        }

        if (typeof bootstrap !== 'undefined') {
          const modal = new bootstrap.Modal(confirmModalApp);
          modal.show();
        } else {
          confirmModalApp.style.display = 'block';
        }
      });
    }

    // Attacher les écouteurs aux selects existants
    document.querySelectorAll(".select-action-app").forEach(attachWorkflowChange);

    if (confirmYesAppBtn) {
      confirmYesAppBtn.addEventListener("click", async function () {
        if (!currentAction || !currentAppreciationId || !currentSelect) return;

        confirmYesAppBtn.disabled = true;

        try {
          const res = await fetch(`/appreciations/${currentAppreciationId}/changer_etat`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({ action: currentAction })
          });

          const data = await res.json();

          if (!res.ok || data.error) {
            showNotification(data.error || "Erreur lors de l'opération", "danger");
            currentSelect.value = "";
            actionConfirmed = false;
            if (typeof bootstrap !== 'undefined') {
              bootstrap.Modal.getInstance(confirmModalApp)?.hide();
            } else {
              confirmModalApp.style.display = 'none';
            }
            return;
          }

          // Succès
          actionConfirmed = true;
          updateAppreciationState(currentAppreciationId, data.etat, currentSelect);

          if (typeof bootstrap !== 'undefined') {
            bootstrap.Modal.getInstance(confirmModalApp)?.hide();
          } else {
            confirmModalApp.style.display = 'none';
          }
          showNotification("Opération réussie", "success");

        } catch (err) {
          console.error(err);
          showNotification("Erreur réseau", "danger");
          if (currentSelect) currentSelect.value = "";
        } finally {
          confirmYesAppBtn.disabled = false;
        }
      });

      // Reset du select si modal fermé sans confirmation
      if (confirmModalApp) {
        confirmModalApp.addEventListener("hidden.bs.modal", function () {
          if (!actionConfirmed && currentSelect) {
            currentSelect.value = "";
          }
          currentAction = null;
          currentAppreciationId = null;
          currentSelect = null;
          actionConfirmed = false;
        });

        // Fallback pour le cas où Bootstrap n'est pas disponible
        confirmModalApp.addEventListener("click", function(e) {
          if (e.target === this || e.target.classList.contains('btn-close')) {
            if (!actionConfirmed && currentSelect) {
              currentSelect.value = "";
            }
            currentAction = null;
            currentAppreciationId = null;
            currentSelect = null;
            actionConfirmed = false;
            this.style.display = 'none';
          }
        });
      }
    }

    // ======================= //
    // FONCTIONS UTILITAIRES //
    // ======================= //

    // Fonction de notification améliorée avec fallback
    function showNotification(message, type = "success", delay = 3000) {
      // Créer le conteneur s'il n'existe pas
      let container = document.getElementById("notificationContainer");
      if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
      }

      const toastId = 'toast-' + Date.now();
      const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
        </div>
      `;

      container.insertAdjacentHTML('beforeend', toastHtml);
      
      const toastElement = document.getElementById(toastId);
      
      // Utiliser Bootstrap Toast si disponible, sinon fallback simple
      if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(toastElement, { 
          autohide: true,
          delay: delay 
        });
        toast.show();
      } else {
        // Fallback simple
        toastElement.style.display = 'block';
        setTimeout(() => {
          if (toastElement.parentNode) {
            toastElement.remove();
          }
        }, delay);
      }
      
      // Nettoyer après fermeture
      toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
      });
    }

    // Mise à jour de l'état d'une appréciation
   // Mise à jour de l'état d'une appréciation - VERSION CORRIGÉE
// Mise à jour de l'état d'une appréciation - VERSION COMPLÈTEMENT CORRIGÉE
function updateAppreciationState(appreciationId, newEtat, currentSelect) {
    console.log(`🔄 Mise à jour état: ${appreciationId} -> ${newEtat}`);
    
    const row = document.querySelector(`tr[data-id="appreciation-${appreciationId}"]`);
    if (!row) {
        console.error("❌ Ligne non trouvée:", `appreciation-${appreciationId}`);
        return;
    }

    // 1. Mettre à jour le badge d'état
    const badge = row.querySelector(".etat .badge");
    if (badge) {
        badge.textContent = newEtat;
        
        let badgeClass = "bg-secondary";
        const etat = newEtat.toLowerCase();

        if (etat === "actif") {
            badgeClass = "bg-success";
        } else if (etat === "abandonné") {
            badgeClass = "bg-dark";
        }

        badge.className = "badge " + badgeClass;
        console.log("✅ Badge mis à jour:", newEtat);
    }

    // 2. Mettre à jour les boutons d'action (Modifier/Supprimer)
    const actionCell = row.querySelector('td.actions-cell');
    if (actionCell) {
        // Supprimer tous les boutons existants sauf le bouton Détail
        const existingEditBtn = actionCell.querySelector('.btn-edit');
        const existingDeleteBtn = actionCell.querySelector('.btn-delete');
        
        if (existingEditBtn) existingEditBtn.remove();
        if (existingDeleteBtn) existingDeleteBtn.remove();

        // Recréer les boutons selon le nouvel état
        if (newEtat.toLowerCase() === "inactif") {
            // Bouton Modifier
            const editBtn = document.createElement('button');
            editBtn.type = 'button';
            editBtn.className = 'btn btn-warning btn-sm btn-edit';
            editBtn.dataset.id = appreciationId;
            editBtn.title = 'Modifier';
            editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
            actionCell.appendChild(editBtn);

            // Bouton Supprimer
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-danger btn-sm btn-delete';
            deleteBtn.dataset.id = appreciationId;
            deleteBtn.title = 'Supprimer';
            deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
            actionCell.appendChild(deleteBtn);

            console.log("🔓 Boutons Modifier/Supprimer créés");
        } else {
            console.log("🔒 Boutons Modifier/Supprimer supprimés (état non inactif)");
        }

        // Réattacher les écouteurs d'événements aux nouveaux boutons
        attachActionEventListeners();
    }

    // 3. Mettre à jour le select d'action
    const selectContainer = row.querySelector('.etat .d-flex');
    if (selectContainer) {
        // Supprimer tous les selects existants dans ce container
        const existingSelects = selectContainer.querySelectorAll('.select-action-app');
        existingSelects.forEach(select => select.remove());
        
        // Créer le nouveau select selon le nouvel état
        if (newEtat.toLowerCase() !== "abandonné") {
            createActionSelect(appreciationId, newEtat, selectContainer);
            console.log("✅ Nouveau select créé pour état:", newEtat);
        } else {
            console.log("❌ Aucun select créé (état Abandonné)");
        }
    }
}

// Fonction pour réattacher les écouteurs d'événements aux boutons
function attachActionEventListeners() {
    // Réattacher les écouteurs pour les boutons Modifier
    const editButtons = document.querySelectorAll('.btn-edit');
    editButtons.forEach(btn => {
        // Supprimer les anciens écouteurs
        btn.replaceWith(btn.cloneNode(true));
        
        // Réattacher le nouvel écouteur
        const newBtn = document.querySelector(`.btn-edit[data-id="${btn.dataset.id}"]`);
        if (newBtn) {
            newBtn.addEventListener('click', function() {
                editAppreciation(this.dataset.id);
            });
        }
    });

    // Réattacher les écouteurs pour les boutons Supprimer
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        // Supprimer les anciens écouteurs
        btn.replaceWith(btn.cloneNode(true));
        
        // Réattacher le nouvel écouteur
        const newBtn = document.querySelector(`.btn-delete[data-id="${btn.dataset.id}"]`);
        if (newBtn) {
            newBtn.addEventListener('click', function() {
                deleteAppreciation(this.dataset.id);
            });
        }
    });

    console.log("🎯 Écouteurs d'événements réattachés aux boutons");
}

// Fonction pour initialiser tous les écouteurs d'événements
function initializeEventListeners() {
    // Écouteurs pour les boutons existants
    const table = document.getElementById("table-appreciations");
    if (table) {
        table.addEventListener("click", function (e) {
            // Bouton modifier
            const editBtn = e.target.closest(".btn-edit");
            if (editBtn) {
                editAppreciation(editBtn.dataset.id);
                return;
            }

            // Bouton détail
            const detailBtn = e.target.closest(".btn-detail");
            if (detailBtn) {
                showAppDetail(detailBtn.dataset.id);
                return;
            }

            // Bouton supprimer
            const deleteBtn = e.target.closest(".btn-delete");
            if (deleteBtn) {
                const id = deleteBtn.dataset.id;
                if (!id) {
                    showNotification("Impossible de supprimer : identifiant non défini !", "danger");
                    return;
                }
                deleteAppreciation(id);
                return;
            }
        });
    }
    
    console.log("🎯 Écouteurs d'événements initialisés");
}
    // Créer un select d'action
   // Créer un select d'action - VERSION CORRIGÉE
function createActionSelect(appreciationId, etat, parentElement) {
    const newSelect = document.createElement("select");
    newSelect.className = "form-select form-select-sm select-action-app";
    newSelect.dataset.id = appreciationId;
    newSelect.style.minWidth = "100px";
    newSelect.style.maxWidth = "110px";

    let options = `<option value="">Action</option>`;
    const etatLower = etat.toLowerCase();
    
    if (etatLower === "inactif") {
        options += `<option value="Activer">Activer</option>`;
    } else if (etatLower === "actif") {
        options += `<option value="Abandonner">Abandonner</option>`;
    }
    
    newSelect.innerHTML = options;
    parentElement.appendChild(newSelect);
    attachWorkflowChange(newSelect);
}

    // Mise à jour d'une ligne du tableau après édition
    function updateTableRow(id, updatedData) {
      const row = document.querySelector(`tr[data-id="appreciation-${id}"]`);
      if (!row) return;

      // Mettre à jour les cellules
      const libelleCell = row.querySelector(".col-libelle");
      const seuilMinCell = row.querySelector(".col-seuil_min");
      const seuilMaxCell = row.querySelector(".col-seuil_max");
      const descriptionCell = row.querySelector(".col-description");
      const badge = row.querySelector(".etat .badge");

      if (libelleCell) libelleCell.textContent = updatedData.libelle;
      if (seuilMinCell) seuilMinCell.textContent = updatedData.seuil_min;
      if (seuilMaxCell) seuilMaxCell.textContent = updatedData.seuil_max;
      if (descriptionCell) descriptionCell.textContent = updatedData.description;
      
      if (badge && updatedData.etat) {
        badge.textContent = updatedData.etat;
        badge.className = `badge ${
          updatedData.etat === "Actif" ? "bg-success" :
          updatedData.etat === "Abandonné" ? "bg-dark" : "bg-secondary"
        }`;
      }
    }
  }
  // Validation des seuils avant soumission

});
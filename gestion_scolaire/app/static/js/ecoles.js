document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // ========== INITIALISATION DES COMPOSANTS ==========
  initializeTooltips();
  initializeActionConfirmations();
  initializeTableEvents();
  initializeForms();
  initializeValidation();
  initializeCustomValidation();

  // ========== VALIDATION PERSONNALISÉE ==========
  function initializeCustomValidation() {
      // Validation téléphone
      const phoneInputs = document.querySelectorAll('input[type="tel"]');
      phoneInputs.forEach(input => {
          input.addEventListener('input', function(e) {
              validatePhoneFormat(this);
          });
          
          input.addEventListener('blur', function(e) {
              validatePhoneFormat(this);
          });
      });

      // Validation email
      const emailInputs = document.querySelectorAll('input[type="email"]');
      emailInputs.forEach(input => {
          input.addEventListener('input', function(e) {
              validateEmailFormat(this);
          });
          
          input.addEventListener('blur', function(e) {
              validateEmailFormat(this);
          });
      });
  }

  function validatePhoneFormat(input) {
      const value = input.value.trim();
      if (!value) {
          input.setCustomValidity('');
          return true;
      }

      // Format international: +228 12 34 56 78 ou +22812345678
      const phoneRegex = /^\+\d{1,3}[\s\d]{7,15}$/;
      const cleanedValue = value.replace(/\s/g, '');
      
      if (phoneRegex.test(value) || /^\+\d{8,15}$/.test(cleanedValue)) {
          input.setCustomValidity('');
          input.classList.remove('is-invalid');
          input.classList.add('is-valid');
          return true;
      } else {
          input.setCustomValidity('Format invalide. Utilisez le format international: +228 XX XX XX XX');
          input.classList.remove('is-valid');
          input.classList.add('is-invalid');
          return false;
      }
  }

  function validateEmailFormat(input) {
      const value = input.value.trim();
      if (!value) {
          input.setCustomValidity('');
          return true;
      }

      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (emailRegex.test(value)) {
          input.setCustomValidity('');
          input.classList.remove('is-invalid');
          input.classList.add('is-valid');
          return true;
      } else {
          input.setCustomValidity('Format d\'email invalide');
          input.classList.remove('is-valid');
          input.classList.add('is-invalid');
          return false;
      }
  }

  function validateForm(form) {
      let isValid = true;
      
      // Valider tous les champs téléphone
      const phoneInputs = form.querySelectorAll('input[type="tel"]');
      phoneInputs.forEach(input => {
          if (!validatePhoneFormat(input)) {
              isValid = false;
          }
      });

      // Valider tous les champs email
      const emailInputs = form.querySelectorAll('input[type="email"]');
      emailInputs.forEach(input => {
          if (!validateEmailFormat(input)) {
              isValid = false;
          }
      });

      return isValid;
  }

  // ========== GESTION DES CONFIRMATIONS D'ACTIONS ==========
  let pendingAction = null;

  function initializeActionConfirmations() {
      const confirmModal = document.getElementById('confirmActionModal');
      const confirmYesBtn = document.getElementById('confirmYesBtn');
      const confirmMessage = document.getElementById('confirmMessage');

      if (!confirmModal || !confirmYesBtn || !confirmMessage) return;

      confirmYesBtn.addEventListener('click', function() {
          if (pendingAction && typeof pendingAction === 'function') {
              pendingAction();
          }
          bootstrap.Modal.getInstance(confirmModal).hide();
          pendingAction = null;
      });

      confirmModal.addEventListener('hidden.bs.modal', function() {
          pendingAction = null;
          confirmMessage.textContent = '';
      });
  }

  function confirmAction(message, actionCallback) {
      const confirmModal = document.getElementById('confirmActionModal');
      const confirmMessage = document.getElementById('confirmMessage');

      if (!confirmModal || !confirmMessage) {
          if (actionCallback && typeof actionCallback === 'function') {
              actionCallback();
          }
          return;
      }

      confirmMessage.textContent = message;
      pendingAction = actionCallback;

      const modal = new bootstrap.Modal(confirmModal);
      modal.show();
  }

  // ========== FONCTIONS D'INITIALISATION ==========
  
  function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
  }

  function initializeTableEvents() {
    const table = document.getElementById("table-ecoles");
    if (!table) return;

    table.addEventListener("click", function (e) {
      const editBtn = e.target.closest(".btnEco-edit");
      if (editBtn) {
        editEcole(editBtn.dataset.id);
        return;
      }

      const detailBtn = e.target.closest(".btnEco-detail");
      if (detailBtn) {
        showEcoDetail(detailBtn.dataset.id);
        return;
      }

      const deleteBtn = e.target.closest(".btnEco-danger");
      if (deleteBtn) {
        const id = deleteBtn.dataset.id;
        if (!id) {
          showNotification("Impossible de supprimer : identifiant non défini !", "danger");
          return;
        }
        
        confirmAction(
          `Voulez-vous vraiment supprimer cette école ? Cette action est irréversible.`,
          () => deleteEcoleConfirmed(id)
        );
        return;
      }
    });
  }

  function initializeForms() {
    initializeAddForm();
    initializeEditForm();
    initializeDeleteForm();
  }

  function initializeValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
      form.addEventListener('submit', event => {
        // Validation personnalisée avant la validation native
        if (!validateForm(form)) {
          event.preventDefault();
          event.stopPropagation();
        }
        
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    });
  }

  // ========== GESTION DES NOTIFICATIONS ==========

  function showNotification(message, type = "success", delay = 3000) {
    const container = document.getElementById("notificationContainer");
    if (!container) return;

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    toastEl.role = "alert";
    toastEl.ariaLive = "assertive";
    toastEl.ariaAtomic = "true";

    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    container.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay });
    toast.show();

    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
  }

  // ========== GESTION DE L'AJOUT ==========

  function initializeAddForm() {
    const addEcoForm = document.getElementById("addEcoForm");
    if (!addEcoForm) return;

    addEcoForm.replaceWith(addEcoForm.cloneNode(true));
    const newAddEcoForm = document.getElementById("addEcoForm");

    newAddEcoForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      newAddEcoForm.classList.add("was-validated");
      
      // Validation personnalisée
      if (!validateForm(newAddEcoForm) || !newAddEcoForm.checkValidity()) {
        return;
      }

      try {
        const formData = new FormData(newAddEcoForm);
        const res = await fetch("/ecoles/add", { 
          method: "POST", 
          body: formData 
        });
        const data = await res.json();

        if (res.ok) {
          const modal = bootstrap.Modal.getInstance(document.getElementById("addEcoModal"));
          if (modal) modal.hide();
          showNotification(data.message || "École ajoutée avec succès", "success");
          location.reload();
        } else {
          showNotification(data.error || "Erreur lors de l'ajout", "danger");
        }
      } catch (error) {
        console.error("Erreur ajout école:", error);
        showNotification("Erreur serveur", "danger");
      }
    });
  }

  // ========== GESTION DE LA SUPPRESSION ==========

  async function deleteEcole(id) {
    try {
      const res = await fetch(`/ecoles/get/${id}`);
      if (!res.ok) {
        showNotification("Impossible de récupérer les données de l'école", "danger");
        return;
      }

      const data = await res.json();
      document.getElementById("deleteEco_id").value = id;
      document.getElementById("deleteEco_info").textContent = `${data.code} - ${data.nom}`;
      new bootstrap.Modal(document.getElementById("deleteEcoModal")).show();
    } catch (error) {
      console.error("Erreur suppression école:", error);
      showNotification("Erreur lors de la suppression", "danger");
    }
  }

  async function deleteEcoleConfirmed(id) {
    try {
      const res = await fetch(`/ecoles/delete/${id}`, { method: "POST" });
      if (res.ok) {
        showNotification("École supprimée avec succès", "success");
        const row = document.querySelector(`tr[data-id="ecole-${id}"]`);
        if (row) {
          row.remove();
        } else {
          location.reload();
        }
      } else {
        const data = await res.json();
        showNotification(data.error || "Erreur lors de la suppression", "danger");
      }
    } catch (error) {
      console.error("Erreur suppression école:", error);
      showNotification("Erreur serveur lors de la suppression", "danger");
    }
  }

  function initializeDeleteForm() {
    const deleteEcoForm = document.getElementById("deleteEcoForm");
    if (!deleteEcoForm) return;

    deleteEcoForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = document.getElementById("deleteEco_id").value;

      confirmAction(
        "Voulez-vous vraiment supprimer cette école ? Cette action est irréversible.",
        async () => {
          try {
            const res = await fetch(`/ecoles/delete/${id}`, { method: "POST" });
            if (res.ok) {
              const modal = bootstrap.Modal.getInstance(document.getElementById("deleteEcoModal"));
              if (modal) modal.hide();
              showNotification("École supprimée avec succès", "success");
              location.reload();
            } else {
              showNotification("Erreur lors de la suppression", "danger");
            }
          } catch (error) {
            console.error("Erreur suppression:", error);
            showNotification("Erreur serveur", "danger");
          }
        }
      );
    });
  }

  // ========== GESTION DE L'ÉDITION ==========

  async function editEcole(id) {
    try {
      const res = await fetch(`/ecoles/get/${id}`);
      if (!res.ok) {
        showNotification("Erreur lors de la récupération des données", "danger");
        return;
      }

      const data = await res.json();
      openEditModal(data);
    } catch (error) {
      console.error("Erreur édition école:", error);
      showNotification("Erreur serveur", "danger");
    }
  }

  function openEditModal(ecole) {
    const fields = {
        "editEco_id": ecole.id,
        "editEco_code": ecole.code,
        "editEco_nom": ecole.nom,
        "editEco_localite": ecole.localite,
        "editEco_dre": ecole.dre,
        "editEco_site": ecole.site,
        "editEco_email": ecole.email,
        "editEco_telephone1": ecole.telephone1,
        "editEco_telephone2": ecole.telephone2,
        "editEco_devise": ecole.devise,
        "editEco_inspection": ecole.inspection,
        "editEco_boite_postale": ecole.boite_postale,
        "editEco_prefecture": ecole.prefecture
    };

    Object.entries(fields).forEach(([fieldId, value]) => {
        const element = document.getElementById(fieldId);
        if (element) {
            if (element.tagName === 'SELECT') {
                element.value = value || "";
            } else {
                element.value = value || "";
            }
        }
    });

    new bootstrap.Modal(document.getElementById("editEcoModal")).show();
  }

  function initializeEditForm() {
    const editEcoForm = document.getElementById("editEcoForm");
    if (!editEcoForm) return;

    if (editEcoForm.dataset.listenerAttached) return;
    editEcoForm.dataset.listenerAttached = "true";

    editEcoForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      // Validation personnalisée
      if (!validateForm(editEcoForm) || !editEcoForm.checkValidity()) {
        editEcoForm.classList.add("was-validated");
        return;
      }

      const id = document.getElementById("editEco_id").value;
      const formData = new FormData(e.target);

      try {
        const res = await fetch(`/ecoles/update/${id}`, { 
          method: "POST", 
          body: formData 
        });
        const updatedData = await res.json();

        if (!res.ok) {
          showNotification(updatedData.error || "Erreur lors de la modification", "danger");
          return;
        }

        updateTableRow(id, updatedData);
        
        bootstrap.Modal.getInstance(document.getElementById("editEcoModal"))?.hide();
        showNotification("École modifiée avec succès", "success");
      } catch (error) {
        console.error("Erreur modification école:", error);
        showNotification("Erreur serveur", "danger");
      }
    });
  }

  function updateTableRow(id, data) {
    const row = document.querySelector(`tr[data-id="ecole-${id}"]`);
    if (!row) return;

    const fieldMappings = {
      ".col-code": data.code,
      ".col-nom": data.nom,
      ".col-localite": data.localite,
      ".col-site": data.site,
      ".col-email": data.email,
      ".col-telephone1": data.telephone1,
      ".col-telephone2": data.telephone2,
      ".col-dre": data.dre,
      ".col-prefecture": data.prefecture,
      ".col-devise": data.devise,
      ".col-inspection": data.inspection,
      ".col-boite_postale": data.boite_postale
    };

    Object.entries(fieldMappings).forEach(([selector, value]) => {
      const element = row.querySelector(selector);
      if (element) element.textContent = value || "";
    });
  }

  // ========== GESTION DES DÉTAILS ==========

  async function showEcoDetail(id) {
    try {
      const res = await fetch(`/ecoles/detail/${id}`);
      if (!res.ok) {
        showNotification("Erreur lors de la récupération des détails", "danger");
        return;
      }

      const data = await res.json();
      displayDetailModal(data);
    } catch (error) {
      console.error("Erreur détail école:", error);
      showNotification("Erreur serveur", "danger");
    }
  }

  function displayDetailModal(data) {
    const detailContent = document.getElementById("detailEcoContent");
    if (!detailContent) return;

    const content = `
      <p><b>Code:</b> ${data.code || 'Non renseigné'}</p>
      <p><b>Nom:</b> ${data.nom || 'Non renseigné'}</p>
      <p><b>Localité:</b> ${data.localite || 'Non renseigné'}</p>
      <p><b>Site Web:</b> ${data.site || 'Non renseigné'}</p>
      <p><b>Email:</b> ${data.email || 'Non renseigné'}</p>
      <p><b>Téléphone 1:</b> ${data.telephone1 || 'Non renseigné'}</p>
      <p><b>Téléphone 2:</b> ${data.telephone2 || 'Non renseigné'}</p>
      <p><b>DRE:</b> ${data.dre || 'Non renseigné'}</p>
      <p><b>B.P:</b> ${data.boite_postale || 'Non renseigné'}</p>
      <p><b>IESG:</b> ${data.inspection || 'Non renseigné'}</p>
      <p><b>Préfecture:</b> ${data.prefecture || 'Non renseigné'}</p>
      <p><b>Devise:</b> ${data.devise || 'Non renseigné'}</p>
    `;

    detailContent.innerHTML = content;
    new bootstrap.Modal(document.getElementById("detailEcoModal")).show();
  }
});
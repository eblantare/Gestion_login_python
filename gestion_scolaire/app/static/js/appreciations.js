document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // Activer les tooltips
  const tooltipTriggerlist = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerlist.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Sélection du tableau des APPRÉCIATIONS (corrigé)
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
          alert("Impossible de supprimer : identifiant non défini !");
          return;
        }
        deleteAppreciation(id);
        return;
      }
    });
  }

  // ---------- Ajout appréciation (AJAX) ----------
  const addAppForm = document.getElementById("addAppForm");
  if (addAppForm) {
    addAppForm.replaceWith(addAppForm.cloneNode(true));
    const newAddAppForm = document.getElementById("addAppForm");
    newAddAppForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      newAddAppForm.classList.add("was-validated");
      if (!newAddAppForm.checkValidity()) return;
      const formData = new FormData(newAddAppForm);
      const res = await fetch("/appreciations/add", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        const modal = bootstrap.Modal.getInstance(document.getElementById("addAppModal"));
        if (modal) modal.hide();
        showNotification(data.message || "Ajout réussi", "success");
        location.reload();
      } else {
        showNotification(data.error || "Erreur lors de l'ajout", "danger");
      }
    });
  }

  // Notifications
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

    const bsToast = new bootstrap.Toast(toastEl, { delay: delay });
    bsToast.show();

    toastEl.addEventListener("hidden.bs.toast", () => {
      toastEl.remove();
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

  // ---------- Workflow : changer état (modal dynamique) ----------
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
      if (msgEl) msgEl.textContent = `Voulez-vous vraiment ${action.toLowerCase()} cette appréciation ?`;

      const modal = new bootstrap.Modal(confirmModalApp);
      modal.show();
    });
  }

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
          alert(data.error || "Erreur lors de l'opération");
          currentSelect.value = "";
          actionConfirmed = false;
          bootstrap.Modal.getInstance(confirmModalApp)?.hide();
          return;
        }

        // Succès
        actionConfirmed = true;

        const td = currentSelect.closest("td");
        const badge = td && td.querySelector("span");
        if (badge) {
          badge.textContent = data.etat;

          let badgeClass;
          const etat = data.etat.toLowerCase();

          if (etat === "actif") {
            badgeClass = "bg-success";
          } else if (etat === "abandonné") {
            badgeClass = "bg-dark";
          } else {
            badgeClass = "bg-secondary";
          }

          badge.className = "badge " + badgeClass;
        }

        // Cacher/montrer boutons selon l'état
        const row = currentSelect.closest('tr');
        if (row) {
          const actionCell = row.querySelector('td.actions-cell') || row.lastElementChild;
          const btnEdit = actionCell ? actionCell.querySelector('.btn-edit') : null;
          const btnDelete = actionCell ? actionCell.querySelector('.btn-delete') : null;

          if (data.etat.toLowerCase() !== "inactif") {
            if (btnEdit) btnEdit.remove();
            if (btnDelete) btnDelete.remove();
          } else {
            if (btnEdit) btnEdit.style.display = "";
            if (btnDelete) btnDelete.style.display = "";
          }
        }

        // Recréer le select
        if (data.etat.toLowerCase() === "abandonné") {
          currentSelect.remove();
        } else {
          currentSelect.remove();

          const newSelect = document.createElement("select");
          newSelect.className = "form-select form-select-sm d-inline-block w-auto ms-1 select-action-app";
          newSelect.dataset.id = currentAppreciationId;

          let options = `<option value="">Action</option>`;
          switch (data.etat.toLowerCase()) {
            case "inactif":
              options += `<option value="Activer">Activer</option>`;
              break;
            case "actif":
              options += `<option value="Abandonner">Abandonner</option>`;
              break;
          }
          newSelect.innerHTML = options;

          td.appendChild(newSelect);
          attachWorkflowChange(newSelect);
        }

        bootstrap.Modal.getInstance(confirmModalApp)?.hide();

      } catch (err) {
        console.error(err);
        alert("Erreur réseau");
        if (currentSelect) currentSelect.value = "";
      } finally {
        confirmYesAppBtn.disabled = false;
      }
    });

    // Reset du select si modal fermé sans confirmation
    confirmModalApp?.addEventListener("hidden.bs.modal", function () {
      if (!actionConfirmed && currentSelect) {
        currentSelect.value = "";
      }
      currentAction = null;
      currentAppreciationId = null;
      currentSelect = null;
      actionConfirmed = false;
    });
  }

  // ---------- Suppression ----------
  window.deleteAppreciation = async function (id) {
    const res = await fetch(`/appreciations/get/${id}`);
    if (!res.ok) return console.error("Impossible de récupérer l'appréciation :", id);

    const data = await res.json();
    document.getElementById("deleteApp_id").value = id;
    document.getElementById("deleteApp_info").textContent = `${data.libelle} - ${data.description}`;
    new bootstrap.Modal(document.getElementById("deleteAppModal")).show();
  };

  const deleteAppForm = document.getElementById("deleteAppForm");
  if (deleteAppForm) {
    deleteAppForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = document.getElementById("deleteApp_id").value;
      const res = await fetch(`/appreciations/delete/${id}`, { method: "POST" });
      if (res.ok) location.reload();
      else alert("Erreur suppression");
    });
  }

  // ---------- Édition appréciation ----------
  window.editAppreciation = async function(id) {
    const res = await fetch(`/appreciations/get/${id}`);
    if (!res.ok) {
        alert(`Erreur récupération appréciation : ${res.status}`);
        return;
    }
    const data = await res.json();

    document.getElementById("editApp_id").value = data.id;
    document.getElementById("editApp_libelle").value = data.libelle;
    document.getElementById("editApp_seuil_min").value = data.seuil_min;
    document.getElementById("editApp_seuil_max").value = data.seuil_max;
    document.getElementById("editApp_description").value = data.description;

    bootstrap.Modal.getOrCreateInstance(document.getElementById("editAppModal")).show();
  };

  const editAppForm = document.getElementById("editAppForm");
  if (editAppForm && !editAppForm.dataset.listenerAttached) {
    editAppForm.dataset.listenerAttached = "true";

    editAppForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!e.target.checkValidity()) return;

      const id = document.getElementById("editApp_id").value;
      const formData = new FormData(e.target);

      const row = document.querySelector(`tr[data-id="appreciation-${id}"]`);
      if (!row) return;

      const originalLibelle = row.querySelector(".col-libelle")?.innerText.trim() || "";
      const originalSeuilMin = row.querySelector(".col-seuil_min")?.innerText.trim() || "";
      const originalSeuilMax = row.querySelector(".col-seuil_max")?.innerText.trim() || "";
      const originalDescription = row.querySelector(".col-description")?.innerText.trim() || "";

      // Pas de modif
      if (
        formData.get("libelle") === originalLibelle &&
        String(formData.get("seuil_min")) === originalSeuilMin &&
        String(formData.get("seuil_max")) === originalSeuilMax &&
        formData.get("description") === originalDescription
      ) {
        bootstrap.Modal.getInstance(document.getElementById("editAppModal"))?.hide();
        showNotification("Aucune modification détectée", "info");
        return;
      }

      try {
        const res = await fetch(`/appreciations/update/${id}`, { method: "POST", body: formData });
        const updated = await res.json();

        if (!res.ok) {
          showNotification(updated.error || "Erreur lors de la modification", "danger");
          return;
        }

        // MAJ tableau
        row.querySelector(".col-libelle") && (row.querySelector(".col-libelle").textContent = updated.libelle);
        row.querySelector(".col-seuil_min") && (row.querySelector(".col-seuil_min").textContent = updated.seuil_min);
        row.querySelector(".col-seuil_max") && (row.querySelector(".col-seuil_max").textContent = updated.seuil_max);
        row.querySelector(".col-description") && (row.querySelector(".col-description").textContent = updated.description);

        const badge = row.querySelector(".etat .badge");
        if (badge && updated.etat) {
          badge.textContent = updated.etat;
          badge.className = `badge ${
            updated.etat === "Actif" ? "bg-success" :
            updated.etat === "Abandonné" ? "bg-dark" : "bg-secondary"
          }`;
        }

        bootstrap.Modal.getInstance(document.getElementById("editAppModal"))?.hide();
        showNotification("Modification réussie", "success");
      } catch (err) {
        console.error(err);
        showNotification("Erreur serveur", "danger");
      }
    });
  }

  // ---------- Détail appréciation ----------
  window.showAppDetail = async function (id) {
    const res = await fetch(`/appreciations/detail/${id}`);
    if (!res.ok) return alert("Erreur récupération détail");
    const data = await res.json();
    const content = `
      <p><b>Libellé:</b> ${data.libelle}</p>
      <p><b>Seuil minimal:</b> ${data.seuil_min}</p>
      <p><b>Seuil maximal:</b> ${data.seuil_max}</p>
      <p><b>Description:</b> ${data.description}</p>
      <p><b>État:</b> ${data.etat || ""}</p>
    `;
    const detailAppContent = document.getElementById("detailAppContent");
    if (detailAppContent) detailAppContent.innerHTML = content;
    new bootstrap.Modal(document.getElementById("detailAppModal")).show();
  };
});
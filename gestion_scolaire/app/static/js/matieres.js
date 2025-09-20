document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // ======================= TOOLTIP =======================
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

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
    const bsToast = new bootstrap.Toast(toast, { delay });
    bsToast.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
  }

  // ======================= UTILS MODAL CLEANUP =======================
  function cleanupModal(modalEl) {
    // hide instance if exists, then remove any leftover backdrop and modal-open class
    const inst = bootstrap.Modal.getInstance(modalEl);
    if (inst) inst.hide();
    // cleanup possible leftover backdrops and body classes
    document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
    document.body.classList.remove('modal-open');
    document.body.style.paddingRight = '';
  }

  // ======================= TABLE CLICK HANDLER (delegation) =======================
  const table = document.getElementById("table-matieres");
  if (table) {
    table.addEventListener("click", e => {
      const btn = e.target.closest("button");
      if (!btn) return;
      const id = btn.dataset.id;
      if (!id) { showNotification("Identifiant matière manquant !", "danger"); return; }
      if (btn.classList.contains("btn-detail")) showMatDetail(id);
      else if (btn.classList.contains("btn-edit")) editMat(id);
      else if (btn.classList.contains("btn-danger")) deleteMat(id);
    });
  }

  // ======================= AIDE: METTRE A JOUR UNE LIGNE APRÈS ETAT =======================
  function updateRowAfterStateChange(row, id, etat) {
    if (!row) return;
    // badge
    const badge = row.querySelector(".etat span.badge");
    if (badge) {
      const lower = (etat || "").toString().toLowerCase();
      badge.textContent = etat;
      badge.className = "badge " + (lower === "actif" ? "bg-success" : (lower === "bloqué" || lower === "abandonné" ? "bg-dark" : "bg-secondary"));
    }

    // select (on garde le même element quand possible - évite de casser les listeners)
    const select = row.querySelector(".select-action");
    if (select) {
      const lower = (etat || "").toString().toLowerCase();
      if (lower === "bloqué" || lower === "abandonné") {
        select.remove();
      } else {
        // Regénère les options selon l'état
        select.innerHTML = '<option value="">---Action---</option>';
        if (lower === "inactif") select.innerHTML += '<option value="Activer">Activer</option>';
        if (lower === "actif") select.innerHTML += '<option value="Bloquer">Bloquer</option>';
      }
    }

    // actions (boutons) : on remplace la cellule entière mais en conservant le dataset id correct
    const actionsCell = row.querySelector("td.text-nowrap");
    if (actionsCell) {
      const lower = (etat || "").toString().toLowerCase();
      let html = `<button class="btn btn-info btn-sm btn-detail" data-id="${id}" title="Détail"><i class="bi bi-eye"></i></button>`;
      // si on veut garder modifier/supprimer uniquement pour INACTIF (ta logique)
      if (lower === "inactif") {
        html += ` <button class="btn btn-warning btn-sm btn-edit" data-id="${id}" title="Modifier"><i class="bi bi-pencil"></i></button>`;
        html += ` <button class="btn btn-danger btn-sm" data-id="${id}" title="Supprimer"><i class="bi bi-trash"></i></button>`;
      }
      actionsCell.innerHTML = html;
      // Pas besoin de ré-attacher les events : la delegation sur `table` les captera.
    }
  }

  // ======================= ATTACH WORKFLOW CHANGE (with duplicate guard) =======================
  let currentAction = null, currentMatId = null, currentSelect = null, actionConfirmed = false;
  const confirmModalMat = document.getElementById("confirmMatActionModal");
  const confirmYesMatBtn = document.getElementById("confirmYesMatBtn");

  function attachWorkflowChange(select) {
    if (!select) return;
    if (select.dataset.listenerAttached) return;
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
      bootstrap.Modal.getOrCreateInstance(confirmModalMat).show();
    });
  }

  // attach to existing selects on load
  document.querySelectorAll(".select-action").forEach(attachWorkflowChange);

  // ======================= CONFIRM BUTTON handler =======================
  confirmYesMatBtn?.addEventListener("click", async () => {
    if (!currentAction || !currentMatId || actionConfirmed) return;
    actionConfirmed = true;
    confirmYesMatBtn.disabled = true;
    const modalInstance = bootstrap.Modal.getInstance(confirmModalMat) || bootstrap.Modal.getOrCreateInstance(confirmModalMat);

    try {
      const res = await fetch(`/matieres/${currentMatId}/changer_etat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: currentAction })
      });

      // try to parse JSON even if status != 200 to have error message
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        // backend error -> show message if any
        showNotification(data.error || "Erreur lors du changement d'état", "danger");
        // hide modal, cleanup backdrop
        cleanupModal(confirmModalMat);
        return;
      }

      // success -> mise à jour dynamique de la ligne
      const row = document.querySelector(`tr[data-id="matiere-${currentMatId}"]`);
      // si le backend retourne l'id, utilise data.id sinon currentMatId
      const returnedId = data.id || currentMatId;
      updateRowAfterStateChange(row, returnedId, data.etat || "");

      showNotification(data.message || `État changé en ${data.etat}`, "success");

      // reset select value only if select still exists
      if (currentSelect && currentSelect instanceof HTMLSelectElement) {
        currentSelect.value = "";
      }
      actionConfirmed = true;
      // hide modal and cleanup any leftover backdrop
      cleanupModal(confirmModalMat);

    } catch (err) {
      console.error(err);
      showNotification("Erreur réseau lors du changement d'état", "danger");
      // ensure modal hidden and cleaned
      cleanupModal(confirmModalMat);
    } finally {
      confirmYesMatBtn.disabled = false;
      // reset context
      currentAction = null; currentMatId = null; currentSelect = null; actionConfirmed = false;
    }
  });

  // If the modal is closed (by user), reset the select value
  confirmModalMat?.addEventListener("hidden.bs.modal", function () {
    if (!actionConfirmed && currentSelect) currentSelect.value = "";
    currentAction = null; currentMatId = null; currentSelect = null; actionConfirmed = false;
  });

  // ======================= ADD MATIERE (AJAX) =======================
  const addMatForm = document.getElementById("addMatForm");
  if (addMatForm) {
    addMatForm.addEventListener("submit", async e => {
      e.preventDefault();
      if (!addMatForm.checkValidity()) { addMatForm.classList.add("was-validated"); return; }
      const formData = new FormData(addMatForm);
      try {
        const res = await fetch("/matieres/add", { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) { showNotification(data.error || "Erreur lors de l'ajout", "danger"); return; }
        showNotification(`Matière ajoutée avec succès ! Code: ${data.code}`, "success");
        addMatForm.reset(); addMatForm.classList.remove("was-validated");
        cleanupModal(document.getElementById("addMatModal"));

        // Ajout dynamique dans la table
        if (table) {
          const row = table.insertRow();
          row.dataset.id = `matiere-${data.id}`;
          row.innerHTML = `
            <td class="col-code">${data.code}</td>
            <td class="col-libelle">${formData.get("libelle")}</td>
            <td class="col-type">${formData.get("type")}</td>
            <td class="etat text-center">
              <span class="badge bg-secondary">Inactif</span>
              <select class="form-select form-select-sm d-inline-block w-auto ms-2 select-action" data-id="${data.id}">
                <option value="">---Action---</option>
                <option value="Activer">Activer</option>
              </select>
            </td>
            <td class="text-nowrap">
              <button class="btn btn-info btn-sm btn-detail" data-id="${data.id}" title="Détail"><i class="bi bi-eye"></i></button>
              <button class="btn btn-warning btn-sm btn-edit" data-id="${data.id}" title="Modifier"><i class="bi bi-pencil"></i></button>
              <button class="btn btn-danger btn-sm" data-id="${data.id}" title="Supprimer"><i class="bi bi-trash"></i></button>
            </td>
          `;
          // Attache listener au select nouvellement créé
          attachWorkflowChange(row.querySelector(".select-action"));
        }
      } catch (err) {
        console.error(err);
        showNotification("Erreur réseau", "danger");
      }
    });
  }

  // ======================= DELETE MATIERE (avec cleanup backdrop) =======================
  const deleteMatForm = document.getElementById("deleteMatForm");
  window.deleteMat = async id => {
    try {
      const res = await fetch(`/matieres/get/${id}`);
      const data = await res.json();
      if (!res.ok) { showNotification("Erreur lecture matière", "danger"); return; }
      document.getElementById("deleteMat_id").value = id;
      document.getElementById("deleteMat_info").textContent = `${data.code} - ${data.libelle}`;
      const deleteModalEl = document.getElementById("deleteMatModal");
      bootstrap.Modal.getOrCreateInstance(deleteModalEl).show();
    } catch (err) {
      console.error(err);
      showNotification("Erreur réseau", "danger");
    }
  };

  if (deleteMatForm) {
    deleteMatForm.addEventListener("submit", async e => {
      e.preventDefault();
      const id = document.getElementById("deleteMat_id").value;
      try {
        const res = await fetch(`/matieres/delete/${id}`, { method: "POST" });
        if (!res.ok) { showNotification("Erreur suppression", "danger"); return; }
        document.querySelector(`tr[data-id="matiere-${id}"]`)?.remove();
        cleanupModal(document.getElementById("deleteMatModal"));
        showNotification("Matière supprimée avec succès", "success");
      } catch (err) {
        console.error(err);
        showNotification("Erreur réseau", "danger");
        cleanupModal(document.getElementById("deleteMatModal"));
      }
    });
  }

  // ================ EDIT / DETAIL : on s'appuie sur la délégation pour boutons ================
  window.editMat = id => {
    const row = document.querySelector(`tr[data-id="matiere-${id}"]`);
    const editMatForm = document.getElementById("editMatForm");
    if (!row || !editMatForm) return;
    document.getElementById("editMat_id").value = id;
    document.getElementById("editMat_code").value = row.querySelector(".col-code")?.innerText.trim() || "";
    document.getElementById("editMat_libelle").value = row.querySelector(".col-libelle")?.innerText.trim() || "";
    document.getElementById("editMat_type").value = row.querySelector(".col-type")?.innerText.trim() || "";
    bootstrap.Modal.getOrCreateInstance(document.getElementById("editMatModal")).show();
  };

  window.showMatDetail = async id => {
    try {
      const res = await fetch(`/matieres/detail/${id}`);
      const data = await res.json();
      if (!res.ok) { showNotification("Erreur récupération détail", "danger"); return; }
      const detailMatContent = document.getElementById("detailMatContent");
      if (detailMatContent) {
        detailMatContent.innerHTML = `
          <p><b>Code:</b> ${data.code}</p>
          <p><b>Libellé:</b> ${data.libelle}</p>
          <p><b>Type:</b> ${data.type}</p>
          <p><b>Etat:</b> ${data.etat || ""}</p>
        `;
      }
      bootstrap.Modal.getOrCreateInstance(document.getElementById("detailMatModal")).show();
    } catch (err) {
      console.error(err);
      showNotification("Erreur réseau", "danger");
    }
  };

});

document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // Fonction pour créer une notification
  function showNotification(message, type = "success", delay = 3000) {
    const container = document.getElementById("notificationContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute("role", "alert");
    toast.setAttribute("aria-live", "assertive");
    toast.setAttribute("aria-atomic", "true");
    toast.setAttribute("data-bs-delay", delay);

    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;

    container.appendChild(toast);

    // Initialiser le toast et l'afficher
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Supprimer après disparition
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
  }


  function attachListenersToRow(row, id) {
  // Bouton Modifier
  const editBtn = row.querySelector(".btn-edit");
  if (editBtn) {
    editBtn.addEventListener("click", () => editAppreciation(id));
  }

  // Select Action
  const select = row.querySelector(".select-action-app");
  if (select) {
    select.addEventListener("change", async (e) => {
      const action = select.value;
      if (!action) return;

      const confirmModalEl = document.getElementById("confirmActionAppModal");
      const confirmMessageEl = document.getElementById("confirmAppMessage");
      const confirmYesBtn = document.getElementById("confirmYesAppBtn");

      confirmMessageEl.textContent = `Voulez-vous vraiment effectuer l'action "${action}" ?`;
      const modalInstance = bootstrap.Modal.getOrCreateInstance(confirmModalEl);
      modalInstance.show();

      confirmYesBtn.replaceWith(confirmYesBtn.cloneNode(true));
      const newConfirmYesBtn = document.getElementById("confirmYesAppBtn");

      newConfirmYesBtn.addEventListener("click", async () => {
        modalInstance.hide();
        try {
          const res = await fetch(`/appreciations/${id}/changer_etat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action })
          });
          const data = await res.json();
          if (!res.ok) {
            showNotification(data.error || "Erreur lors du changement d'état", "danger");
            return;
          }
          showNotification(data.message, "success");
          select.value = "";

          // Mettre à jour le DOM
          const badge = row.querySelector(".etat .badge");
          if (badge) {
            badge.textContent = data.etat;
            badge.className = `badge ${
              data.etat === "Actif" ? "bg-success" :
              data.etat === "Abandonné" ? "bg-dark" : "bg-secondary"
            }`;
          }

          if (data.etat.toLowerCase() !== "inactif") {
            row.querySelector(".btn-edit")?.remove();
            row.querySelector(".btn-danger")?.remove();
          }

          const selectRow = row.querySelector(".select-action-app");
          if (selectRow) {
            selectRow.innerHTML = '<option value="">---Action---</option>';
            if (data.etat === "Actif") selectRow.innerHTML += '<option value="Abandonner">Abandonner</option>';
            else if (data.etat === "Inactif") selectRow.innerHTML += '<option value="Activer">Activer</option>';
            else if (data.etat === "Abandonné") selectRow.remove();
          }

        } catch (err) {
          console.error(err);
          showNotification("Une erreur est survenue.", "danger");
        }
      });
    });
  }
}
// Listener formulaire ajout appréciation
const form = document.getElementById("addAppreciationForm");
if (form && !form.dataset.listenerAttached) {
    form.dataset.listenerAttached = "true";

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(form);

        try {
            const res = await fetch(form.action, { method: "POST", body: formData });
            const data = await res.json();
            console.log("+++++++++++++++++++",data, res.ok)

            if (!res.ok) {
                showNotification(data.error || "Erreur serveur", "danger");
                return;
            }

            showNotification("Appréciation ajoutée avec succès", "success");
            form.reset();
            bootstrap.Modal.getInstance(document.getElementById("addAppModal"))?.hide();

// --- Ajouter la nouvelle ligne dans DataTable ---
if (window.appreciationsTable) {
    const rowNode = appreciationsTable.row.add([
        `<td class="col-libelle">${data.libelle}</td>`,
        `<td class="col-description">${data.description}</td>`,
        `<td class="etat text-center">
            <span class="badge bg-secondary">${data.etat || "Inactif"}</span>
            <select class="form-select form-select-sm d-inline-block w-auto ms-2 select-action-app rounded-pill" data-id="${data.id}">
              <option value="">---Action---</option>
              <option value="Activer">Activer</option>
            </select>
        </td>`,
        `<td class="text-nowrap">
            <button class="btn btn-info btn-sm" onclick="showAppDetail('${data.id}')">
              <i class="bi bi-eye"></i>
            </button>
            <button class="btn btn-sm btn-warning btn-edit" data-id="${data.id}">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteAppreciation('${data.id}')">
              <i class="bi bi-trash"></i>
            </button>
        </td>`
    ]).draw(false).node();

    rowNode.setAttribute("data-id", `appreciation-${data.id}`);
    rowNode.classList.add("appreciation-row");

    // Réattacher les listeners
    attachListenersToRow(rowNode, data.id);
}


        } catch (err) {
            console.error(err);
            showNotification("Impossible de joindre le serveur.", "danger");
        }
    });
}
//Avancement du workflow
if (!window.workflowListenerAdded) {
  document.addEventListener("change", function (e) {
    if (!e.target.classList.contains("select-action-app")) return;

    const select = e.target;
    const id = select.dataset.id;
    const action = select.value;
    if (!action) return;

    const confirmModalEl = document.getElementById("confirmActionAppModal");
    const confirmMessageEl = document.getElementById("confirmAppMessage");
    const confirmYesBtn = document.getElementById("confirmYesAppBtn");

    // Message personnalisé selon l'action
    confirmMessageEl.textContent = `Voulez-vous vraiment effectuer l'action "${action}" ?`;

    // Afficher le modal
    const modalInstance = bootstrap.Modal.getOrCreateInstance(confirmModalEl);
    modalInstance.show();

    // Supprimer tout listener précédent pour éviter doublons
    confirmYesBtn.replaceWith(confirmYesBtn.cloneNode(true));
    const newConfirmYesBtn = document.getElementById("confirmYesAppBtn");

newConfirmYesBtn.addEventListener("click", async () => {
  modalInstance.hide(); // Masquer le modal

  try {
    const res = await fetch(`/appreciations/${id}/changer_etat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action })
    });
    const data = await res.json();

    if (!res.ok) {
      showNotification(data.error || "Erreur lors du changement d'état", "danger");
      return;
    }

    showNotification(data.message, "success");
    select.value = "";

    // --- Mettre à jour le DOM immédiatement ---
    const row = document.querySelector(`tr[data-id="appreciation-${id}"]`);
    if (row) {
      // Badge
      const badge = row.querySelector(".etat .badge");
      if (badge) {
        badge.textContent = data.etat;
        badge.className = `badge ${
          data.etat === "Actif" ? "bg-success" :
          data.etat === "Abandonné" ? "bg-dark" : "bg-secondary"
        }`;
      }

      // Select d'action
      const selectRow = row.querySelector(".select-action-app");
      if (selectRow) {
        selectRow.innerHTML = '<option value="">---Action---</option>';
        if (data.etat === "Actif") selectRow.innerHTML += '<option value="Abandonner">Abandonner</option>';
        else if (data.etat === "Inactif") selectRow.innerHTML += '<option value="Activer">Activer</option>';
        else if (data.etat === "Abandonné") selectRow.remove();
      }

      // **Masquer les boutons Modifier et Supprimer si état ≠ Inactif**
      const editBtn = row.querySelector(".btn-edit");
      const deleteBtn = row.querySelector(".btn-danger");
      if (data.etat.toLowerCase() !== "inactif") {
        if (editBtn) editBtn.remove();
        if (deleteBtn) deleteBtn.remove();
      }
    }

  } catch (err) {
    console.error(err);
    showNotification("Une erreur est survenue.", "danger");
  }
});
// Masquer les boutons 'modifier' et 'supprimer' si l'état n'est plus Inactif
if (row) {
  const editBtn = row.querySelector(".btn-edit");
  const deleteBtn = row.querySelector(".btn-danger");

  if (data.etat.toLowerCase() !== "inactif") {
    if (editBtn) editBtn.remove();
    if (deleteBtn) deleteBtn.remove();
  } else {
    // Facultatif : tu peux recréer les boutons si l'état redevient 'Inactif'
  }
}

  });
  window.workflowListenerAdded = true; // évite ajout multiple
}

// ---------- Suppression ----------
  window.deleteAppreciation = async function (id) {
    const res = await fetch(`/appreciations/get/${id}`);
    if (!res.ok) return alert("Erreur lecture appreciation");
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

// ---------- Édition ----------
window.editAppreciation = function (id) {
  const row = document.querySelector(`tr[data-id="appreciation-${id}"]`);
  if (!row) return;

  document.getElementById("editApp_id").value = id;
  document.getElementById("editApp_libelle").value = row.querySelector(".col-libelle")?.innerText.trim() || "";
  document.getElementById("editApp_description").value = row.querySelector(".col-description")?.innerText.trim() || "";

  const editModalEl = document.getElementById("editAppModal");
  if (!editModalEl) return console.error("Modal #editAppModal introuvable");

  const modalInstance = bootstrap.Modal.getOrCreateInstance(editModalEl);
  modalInstance.show();
};

// Attacher le listener click une seule fois
document.querySelectorAll(".btn-edit").forEach(btn => {
  btn.addEventListener("click", () => editAppreciation(btn.dataset.id));
});

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
    const originalDescription = row.querySelector(".col-description")?.innerText.trim() || "";

    // Vérifie si les valeurs ont changé
    if (
      formData.get("libelle") === originalLibelle &&
      formData.get("description") === originalDescription
    ) {
      const modalInstance = bootstrap.Modal.getInstance(document.getElementById("editAppModal"));
      modalInstance?.hide();
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

      // Mise à jour du tableau
      row.querySelector(".col-libelle") && (row.querySelector(".col-libelle").textContent = updated.libelle);
      row.querySelector(".col-description") && (row.querySelector(".col-description").textContent = updated.description);

      const badge = row.querySelector(".etat .badge");
      if (badge && updated.etat) {
        badge.textContent = updated.etat;
        badge.className = `badge ${
          updated.etat === "Actif" ? "bg-success" :
          updated.etat === "Abandonné" ? "bg-dark" : "bg-secondary"
        }`;
      }

      // Masquer le modal
      const modalInstance = bootstrap.Modal.getInstance(document.getElementById("editAppModal"));
      modalInstance?.hide();

      // Notification succès
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
      <p><b>Libelle:</b> ${data.libelle}</p>
      <p><b>Description:</b> ${data.description}</p>
      <p><b>Etat:</b> ${data.etat || ""}</p>
    `;
    const detailAppContent = document.getElementById("detailAppContent");
    if (detailAppContent) detailAppContent.innerHTML = content;
    new bootstrap.Modal(document.getElementById("detailAppModal")).show();
  };

});
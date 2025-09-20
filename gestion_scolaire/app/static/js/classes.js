document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // Activer les tooltips
  const tooltipTriggerlist = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerlist.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Sélection du tableau (sécurisé si on n'est pas sur la page)
  const table = document.getElementById("table-classes");
  if (table) {
    table.addEventListener("click", function (e) {
      // Bouton modifier
      const editClBtn = e.target.closest(".btn-edit");
      if (editClBtn) {
        editClasse(editClBtn.dataset.id);
        return;
      }

      // Bouton détail
      const detailClBtn = e.target.closest(".btn-detail");
      if (detailClBtn) {
        showClDetail(detailClBtn.dataset.id);
        return;
      }

      // Bouton supprimer
      const deleteClBtn = e.target.closest(".btn-danger");
      if (deleteClBtn) {
        const id = deleteClBtn.dataset.id;
        if (!id) {
          alert("Impossible de supprimer : identifiant non défini !");
          return;
        }
        deleteClasse(id);
        return;
      }
    });
  }

  // ---------- Ajout classe (AJAX) ----------
  const addClForm = document.getElementById("addClForm");
  if (addClForm) {
    addClForm.replaceWith(addClForm.cloneNode(true));
    const newAddClForm = document.getElementById("addClForm");
    newAddClForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      newAddClForm.classList.add("was-validated");
      if (!newAddClForm.checkValidity()) return;
      const formData = new FormData(newAddClForm);
      const res = await fetch("/classes/add", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        const modal = bootstrap.Modal.getInstance(document.getElementById("addClModal"));
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

    const toastCl = document.createElement("div");
    toastCl.className = `toast align-items-center text-bg-${type} border-0`;
    toastCl.role = "alert";
    toastCl.ariaLive = "assertive";
    toastCl.ariaAtomic = "true";

    toastCl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    container.appendChild(toastCl);

    const clToast = new bootstrap.Toast(toastCl, { delay: delay });
    clToast.show();

    toastCl.addEventListener("hidden.bs.toast", () => {
      toastCl.remove();
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
  const confirmModalCl = document.getElementById("confirmClActionModal");
  const confirmYesClBtn = document.getElementById("confirmYesClBtn");

  let currentAction = null;
  let currentClasseId = null;
  let currentSelect = null;
  let actionConfirmed = false;

  function attachWorkflowChange(select) {
    select.addEventListener("change", function () {
      const action = this.value;
      if (!action) return;

      currentAction = action;
      currentClasseId = this.dataset.id;
      currentSelect = this;
      actionConfirmed = false;

      const msgCl = document.getElementById("confirmClMessage");
      if (msgCl) msgCl.textContent = `Voulez-vous vraiment ${action.toLowerCase()} cette classe ?`;

      const modal = new bootstrap.Modal(confirmModalCl);
      modal.show();
    });
  }

  document.querySelectorAll(".select-action").forEach(attachWorkflowChange);

  if (confirmYesClBtn) {
    confirmYesClBtn.addEventListener("click", async function () {
      if (!currentAction || !currentClasseId || !currentSelect) return;

      confirmYesClBtn.disabled = true;

      try {
        // ⚠️ URL et variable corrigées (minuscule + bon nom de variable)
        const res = await fetch(`/classes/${currentClasseId}/changer_etat`, {
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
          bootstrap.Modal.getInstance(confirmModalCl)?.hide();
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
          } else if (etat === "fermé") {
            badgeClass = "bg-dark";
          } else {
            badgeClass = "bg-secondary";
          }

          badge.className = "badge " + badgeClass;
        }

        // Cacher/montrer boutons selon l'état
        const row = currentSelect.closest('tr');
        if (row) {
          const actionCell = row.querySelector('td.text-nowrap') || row.lastElementChild;
          const btnClEdit = actionCell ? actionCell.querySelector('.btn-edit') : null;
          const btnClDelete = actionCell ? actionCell.querySelector('.btn-danger') : null;

          if (data.etat.toLowerCase() !== "inactif") {
            if (btnClEdit) btnClEdit.remove();
            if (btnClDelete) btnClDelete.remove();
          } else {
            if (btnClEdit) btnClEdit.style.display = "";
            if (btnClDelete) btnClDelete.style.display = "";
          }
        }

        // Recréer le select
        if (data.etat.toLowerCase() === "fermé") {
          currentSelect.remove();
        } else {
          currentSelect.remove();

          const newSelect = document.createElement("select");
          newSelect.className = "form-select form-select-sm d-inline-block w-auto ms-2 select-action";
          newSelect.dataset.id = currentClasseId;

          let options = `<option value="">---Action---</option>`;
          switch (data.etat.toLowerCase()) {
            case "inactif":
              options += `<option value="Activer">Activer</option>`;
              break;
            case "actif":
              options += `<option value="Fermer">Fermer</option>`;
              break;
          }
          newSelect.innerHTML = options;

          td.appendChild(newSelect);
          attachWorkflowChange(newSelect);
        }

        bootstrap.Modal.getInstance(confirmModalCl)?.hide();

      } catch (err) {
        console.error(err);
        alert("Erreur réseau");
        if (currentSelect) currentSelect.value = "";
      } finally {
        confirmYesClBtn.disabled = false;
      }
    });

    // Reset du select si modal fermé sans confirmation
    confirmModalCl?.addEventListener("hidden.bs.modal", function () {
      if (!actionConfirmed && currentSelect) {
        currentSelect.value = "";
      }
      currentAction = null;
      currentClasseId = null;
      currentSelect = null;
      actionConfirmed = false;
    });
  }

  // ---------- Suppression ----------
  window.deleteClasse = async function (id) {
    const res = await fetch(`/classes/get/${id}`);
    if (!res.ok) return console.error("Impossible de supprimer :", id);

    const data = await res.json();
    document.getElementById("deleteCl_id").value = id;
    document.getElementById("deleteCl_info").textContent = `${data.code} - ${data.nom}`;
    new bootstrap.Modal(document.getElementById("deleteClModal")).show();
  };

  const deleteClForm = document.getElementById("deleteClForm");
  if (deleteClForm) {
    deleteClForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = document.getElementById("deleteCl_id").value;
      const res = await fetch(`/classes/delete/${id}`, { method: "POST" });
      if (res.ok) location.reload();
      else alert("Erreur suppression");
    });
  }

  // ---------- Édition classe ----------
 window.editClasse = async function(id) {
    const res = await fetch(`/classes/get/${id}`);
    if (!res.ok) {
        alert(`Erreur récupération classe : ${res.status}`);
    return;
  }
   const data = await res.json();

    document.getElementById("editCl_id").value = data.id;
    document.getElementById("editCl_code").value = data.code;
    document.getElementById("editCl_nom").value = data.nom;
    document.getElementById("editCl_effectif").value = data.effectif;

    const select = document.getElementById("editCl_enseignants");
    [...select.options].forEach(opt => {
        opt.selected = data.enseignants.includes(opt.value);
    });

    bootstrap.Modal.getOrCreateInstance(document.getElementById("editClModal")).show();
};

  // ❌ Supprimé : ancien listener qui appelait une fonction inexistante editCl(...)
  // document.querySelectorAll(".btn-editCl").forEach(btn => {
  //   btn.addEventListener("click", () => editCl(btn.dataset.id));
  // });

  const editClForm = document.getElementById("editClForm");
  if (editClForm && !editClForm.dataset.listenerAttached) {
    editClForm.dataset.listenerAttached = "true";

    editClForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!e.target.checkValidity()) return;

      const id = document.getElementById("editCl_id").value;
      const formData = new FormData(e.target);

      const row = document.querySelector(`tr[data-id="classe-${id}"]`);
      if (!row) return;

      const originalCode = row.querySelector(".col-code")?.innerText.trim() || "";
      const originalNom = row.querySelector(".col-nom")?.innerText.trim() || "";
      const originalEffectif = row.querySelector(".col-effectif")?.innerText.trim() || "";
      const originalEnseignant = row.querySelector(".col-enseignant")?.innerText.trim() || "";

      // Pas de modif
      if (
        formData.get("code") === originalCode &&
        formData.get("nom") === originalNom &&
        String(formData.get("effectif")) === originalEffectif &&
        String(formData.get("enseignant")) === originalEnseignant
      ) {
        bootstrap.Modal.getInstance(document.getElementById("editClModal"))?.hide();
        showNotification("Aucune modification détectée", "info");
        return;
      }

      try {
        const res = await fetch(`/classes/update/${id}`, { method: "POST", body: formData });
        const updated = await res.json();

        if (!res.ok) {
          showNotification(updated.error || "Erreur lors de la modification", "danger");
          return;
        }

        // MAJ tableau (⚠️ .col-nom corrigé)
        row.querySelector(".col-code") && (row.querySelector(".col-code").textContent = updated.code);
        row.querySelector(".col-nom") && (row.querySelector(".col-nom").textContent = updated.nom);
        row.querySelector(".col-effectif") && (row.querySelector(".col-effectif").textContent = updated.effectif);
        row.querySelector(".col-enseignant") && (row.querySelector(".col-enseignant").textContent = updated.enseignants_nom.join(", "));

        const badge = row.querySelector(".etat .badge");
        if (badge && updated.etat) {
          badge.textContent = updated.etat;
          badge.className = `badge ${
            updated.etat === "Actif" ? "bg-success" :
            updated.etat === "Fermé" ? "bg-dark" : "bg-secondary"
          }`;
        }

        bootstrap.Modal.getInstance(document.getElementById("editClModal"))?.hide();
        showNotification("Modification réussie", "success");
      } catch (err) {
        console.error(err);
        showNotification("Erreur serveur", "danger");
      }
    });
  }

  // ---------- Détail classe ----------
  window.showClDetail = async function (id) {
    const res = await fetch(`/classes/detail/${id}`);
    if (!res.ok) return alert("Erreur récupération détail");
    const data = await res.json();
    const content = `
      <p><b>Code:</b> ${data.code}</p>
      <p><b>Nom:</b> ${data.nom}</p>
      <p><b>Effectif:</b> ${data.effectif}</p>
      <p><b>Enseignant:</b> ${data.enseignants.join(", ")}</p>
      <p><b>Etat:</b> ${data.etat || ""}</p>
    `;
    const detailClContent = document.getElementById("detailClContent");
    if (detailClContent) detailClContent.innerHTML = content;
    new bootstrap.Modal(document.getElementById("detailClModal")).show();
  };

  // 🔽 Insérer ici
window.openEditModal = function (classe) {
  document.getElementById("editCl_id").value = classe.id;
  document.getElementById("editCl_code").value = classe.code;
  document.getElementById("editCl_nom").value = classe.nom;
  document.getElementById("editCl_effectif").value = classe.effectif;

  const select = document.getElementById("editCl_enseignants");
  [...select.options].forEach(opt => {
      opt.selected = classe.enseignants.includes(opt.textContent.trim());
  });

  new bootstrap.Modal(document.getElementById("editClModal")).show();
};
// Toggle sélection des enseignants sans Ctrl
function enableMultiSelectToggle(selectId) {
  const select = document.getElementById(selectId);
  if (!select) return;

  select.addEventListener('mousedown', function(e) {
    e.preventDefault(); // empêche le comportement par défaut Ctrl
    const option = e.target;
    if (option.tagName === 'OPTION') {
      option.selected = !option.selected;
    }
    // déclenche l'événement change pour mises à jour
    const event = new Event('change', { bubbles: true });
    select.dispatchEvent(event);
  });
}

// Appliquer sur ajout et édition
enableMultiSelectToggle('addCl_enseignants');
enableMultiSelectToggle('editCl_enseignants');
});
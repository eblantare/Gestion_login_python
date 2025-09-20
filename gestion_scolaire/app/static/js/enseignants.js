document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // ===============================
  // 1️⃣ Initialisation tooltips
  // ===============================
  function initTooltips() {
    const tooltipList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipList.map(el => new bootstrap.Tooltip(el));
  }

  // ===============================
  // 2️⃣ Validation des formulaires Bootstrap
  // ===============================
  function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
      form.addEventListener('submit', event => {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      });
    });
  }

  // ===============================
  // 3️⃣ Notifications
  // ===============================
  function showNotification(message, type = "success", delay = 3000) {
    const container = document.getElementById("notificationContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.role = "alert";
    toast.ariaLive = "assertive";
    toast.ariaAtomic = "true";

    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    container.appendChild(toast);
    const bToast = new bootstrap.Toast(toast, { delay });
    bToast.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
  }

  // ===============================
  // 4️⃣ Workflow / Changer état
  // ===============================
  function initWorkflow() {
    const modal = document.getElementById("confirmEnsActionModal");
    const btnConfirm = document.getElementById("confirmYesEnsBtn");
    let currentAction, currentEnsId, currentSelect, actionConfirmed = false;

    function attach(select) {
      select.addEventListener("change", () => {
        const action = select.value;
        if (!action) return;

        currentAction = action;
        currentEnsId = select.dataset.id;
        currentSelect = select;
        actionConfirmed = false;

        const msg = document.getElementById("confirmEnsMessage");
        if (msg) msg.textContent = `Voulez-vous vraiment ${action.toLowerCase()} cet enseignant ?`;
        new bootstrap.Modal(modal).show();
      });
    }

    document.querySelectorAll(".select-action").forEach(attach);

    if (!btnConfirm) return;

    btnConfirm.addEventListener("click", async () => {
      if (!currentAction || !currentEnsId || !currentSelect) return;
      btnConfirm.disabled = true;

      try {
        const res = await fetch(`/enseignants/${currentEnsId}/changer_etat`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
          body: JSON.stringify({ action: currentAction })
        });
        const data = await res.json();

        if (!res.ok || data.error) {
          alert(data.error || "Erreur lors de l'opération");
          currentSelect.value = "";
          bootstrap.Modal.getInstance(modal)?.hide();
          return;
        }

        actionConfirmed = true;

        const td = currentSelect.closest("td");
        const badge = td?.querySelector("span");
        if (badge) {
          badge.textContent = data.etat;
          badge.className = "badge " + (
            data.etat.toLowerCase() === "actif" ? "bg-success" :
            data.etat.toLowerCase() === "muté" ? "bg-primary" :
            data.etat.toLowerCase() === "retraité" ? "bg-dark" : "bg-secondary"
          );
        }

        const row = currentSelect.closest('tr');
        const actionCell = row?.querySelector('td.text-nowrap') || row?.lastElementChild;
        const btnEdit = actionCell?.querySelector('.btn-edit');
        const btnDelete = actionCell?.querySelector('.btn-danger');

        if (data.etat.toLowerCase() !== "inactif") {
          btnEdit?.remove();
          btnDelete?.remove();
        } else {
          if (btnEdit) btnEdit.style.display = "";
          if (btnDelete) btnDelete.style.display = "";
        }

        currentSelect.remove();
        if (data.etat.toLowerCase() !== "retraité") {
          const newSelect = document.createElement("select");
          newSelect.className = "form-select form-select-sm d-inline-block w-auto ms-2 select-action";
          newSelect.dataset.id = currentEnsId;

          let options = `<option value="">---Action---</option>`;
          if (data.etat.toLowerCase() === "inactif") options += `<option value="Activer">Activer</option>`;
          if (data.etat.toLowerCase() === "actif") options += `<option value="Muter">Muter</option>`;
          if (data.etat.toLowerCase() === "muté") options += `<option value="Retraiter">Retraiter</option>`;

          newSelect.innerHTML = options;
          td?.appendChild(newSelect);
          attach(newSelect);
        }

        bootstrap.Modal.getInstance(modal)?.hide();

      } catch (err) {
        console.error(err);
        alert("Erreur réseau");
        currentSelect.value = "";
      } finally {
        btnConfirm.disabled = false;
      }
    });

    modal?.addEventListener("hidden.bs.modal", () => {
      if (!actionConfirmed && currentSelect) currentSelect.value = "";
      currentAction = currentEnsId = currentSelect = null;
      actionConfirmed = false;
    });
  }

  // ===============================
  // 5️⃣ Ajout enseignant (version avancée)
  // ===============================
  function initAddEns() {
    const form = document.getElementById("addEnsForm");
    if (!form) return;

    form.replaceWith(form.cloneNode(true));
    const newForm = document.getElementById("addEnsForm");

    newForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      newForm.classList.add("was-validated");
      if (!newForm.checkValidity()) return;

      try {
        const fd = new FormData(newForm);
        const res = await fetch("/enseignants/add", { method: "POST", body: fd });
        const data = await res.json();
        if (res.ok) {
          bootstrap.Modal.getInstance(document.getElementById("addEnsModal"))?.hide();
          showNotification(data.message || "Ajout réussi", "success");
          setTimeout(() => location.reload(), 200);
        } else {
          showNotification(data.error || "Erreur lors de l'ajout", "danger");
        }
      } catch (err) {
        console.error(err);
        showNotification("Erreur réseau lors de l'ajout", "danger");
      }
    });
  }

  // ===============================
  // 6️⃣ Édition enseignant
  // ===============================
  function initEditEns() {
    const form = document.getElementById("editEnsForm");
    if (!form || form.dataset.listenerAttached) return;
    form.dataset.listenerAttached = "true";

    window.editEns = function (id) {
      const row = document.querySelector(`tr[data-id="enseignant-${id}"]`);
      if (!row) return;

      document.getElementById("editEns_id").value = id;

      ["nom","prenoms","matiere","email","telephone","date_fonction","titre","sexe","photo_filename"].forEach(f => {
        if (f === "sexe") {
          const val = row.querySelector(".col-sexe")?.innerText.trim() || "";
          document.getElementById("sexeM").checked = (val === "M" || val.toLowerCase().startsWith("masc"));
          document.getElementById("sexeF").checked = (val === "F" || val.toLowerCase().startsWith("fém"));
        } else {
          const input = document.getElementById(`editEns_${f}`);
          if (input) {
            input.value = row.querySelector(`.col-${f}`)?.innerText.trim() || "";
            if (["nom","prenoms","email","telephone","photo_filename"].includes(f)) {
              input.readOnly = true;
              input.classList.add("bg-light");
            }
          }
        }
      });

      const inputPhoto = document.getElementById("editEns_photo_filename");
      const imgPreview = document.getElementById("edit_photo_preview");

// Ici on récupère la photo directement depuis la ligne du tableau
     const photoFile = row.dataset.photo || "";
     inputPhoto.value = photoFile;
     if(photoFile) {
        imgPreview.src = `/static/upload/${photoFile}`;
        imgPreview.style.display = 'block';
    } else {
        imgPreview.style.display = 'none';
   }

      bootstrap.Modal.getOrCreateInstance(document.getElementById("editEnsModal")).show();
    };

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!e.target.checkValidity()) return;

      const id = document.getElementById("editEns_id").value;
      const row = document.querySelector(`tr[data-id="enseignant-${id}"]`);
      if (!row) return;

      const formData = new FormData(form);

      try {
        const res = await fetch(`/enseignants/update/${id}`, { method: "POST", body: formData });
        const updated = await res.json();
        if (!res.ok) return showNotification(updated.error || "Erreur lors de la modification", "danger");

        Object.keys(updated).forEach(f => {
          const td = row.querySelector(`.col-${f}`);
          if (td && updated[f] !== undefined) td.textContent = updated[f];
        });

        if (updated.photo_filename !== undefined) {
          row.dataset.photo = updated.photo_filename;
          const photoPreview = document.getElementById("edit_photo_preview");
          if (photoPreview) {
            photoPreview.src = updated.photo_filename ? "/static/upload/" + updated.photo_filename : "";
            photoPreview.style.display = updated.photo_filename ? "inline-block" : "none";
          }
          const photoInput = document.getElementById("editEns_photo_filename");
          if (photoInput) photoInput.value = updated.photo_filename;
        }

        bootstrap.Modal.getInstance(document.getElementById("editEnsModal"))?.hide();
        showNotification("Modification réussie", "success");

      } catch (err) {
        console.error(err);
        showNotification("Erreur serveur", "danger");
      }
    });
  }

  // ===============================
  // 7️⃣ Suppression enseignant
  // ===============================
  function initDeleteEns() {
    const form = document.getElementById("deleteEnsForm");
    const submitBtn = document.getElementById("deleteEns_submit");
    const info = document.getElementById("deleteEns_info");

    window.deleteEns = async (id) => {
      try {
        const res = await fetch(`/enseignants/get/${id}`);
        if (!res.ok) throw new Error("Erreur lecture enseignant");
        const data = await res.json();

        document.getElementById("deleteEns_id").value = id;
        info.textContent = `${data.nom} - ${data.prenoms}`;
        submitBtn.disabled = false;

        new bootstrap.Modal(document.getElementById("deleteEnsModal")).show();
      } catch (err) {
        console.error(err);
        alert(err.message);
      }
    };

    if (!form) return;
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      submitBtn.disabled = true;

      const id = document.getElementById("deleteEns_id").value;
      try {
        const res = await fetch(`/enseignants/delete/${id}`, { 
          method: "POST", 
          headers: { "X-Requested-With": "XMLHttpRequest" } 
        });
        if (res.ok) location.reload();
        else throw new Error("Erreur suppression");
      } catch (err) {
        console.error(err);
        alert(err.message);
        submitBtn.disabled = false;
      }
    });
  }

  // ===============================
  // 8️⃣ Détails enseignant
  // ===============================
  function initDetailEns() {
    window.showEnsDetail = async (id) => {
      try {
        const res = await fetch(`/enseignants/detail/${id}`);
        if (!res.ok) throw new Error("Erreur récupération détail");

        const data = await res.json();
        const content = document.getElementById("detailEnsContent");
        if (!content) return;

        content.innerHTML = `
          <dl class="row">
            <dt class="col-sm-4">Nom :</dt><dd class="col-sm-8">${data.nom}</dd>
            <dt class="col-sm-4">Prénoms :</dt><dd class="col-sm-8">${data.prenoms}</dd>
            <dt class="col-sm-4">Matière :</dt><dd class="col-sm-8">${data.matiere}</dd>
            <dt class="col-sm-4">Email :</dt><dd class="col-sm-8">${data.email || ''}</dd>
            <dt class="col-sm-4">Téléphone :</dt><dd class="col-sm-8">${data.telephone}</dd>
            <dt class="col-sm-4">Sexe :</dt><dd class="col-sm-8">${data.sexe}</dd>
            <dt class="col-sm-4">Titre :</dt><dd class="col-sm-8">${data.titre}</dd>
            <dt class="col-sm-4">Date prise fonction :</dt><dd class="col-sm-8">${data.date_fonction}</dd>
            <dt class="col-sm-4">Photo :</dt><dd class="col-sm-8">
              ${data.photo_filename ? `<img src="/static/upload/${data.photo_filename}" class="img-thumbnail rounded" style="max-width:120px; height:auto;" alt="Photo de ${data.nom}">` : '—'}
            </dd>
            <dt class="col-sm-4">État :</dt><dd class="col-sm-8">${data.etat || ''}</dd>
          </dl>
        `;

        new bootstrap.Modal(document.getElementById("detailEnsModal")).show();
      } catch (err) {
        console.error(err);
        alert("Impossible de récupérer les détails de l'enseignant.");
      }
    };
  }

  // ===============================
  // 9️⃣ Gestion des clics tableau
  // ===============================
  function initTableClick() {
    const table = document.getElementById("table-enseignants");
    if (!table) return;

    table.addEventListener("click", (e) => {
      const btn = e.target.closest(".btn-edit, .btn-detail, .btn-danger");
      if (!btn) return;
      const id = btn.dataset.id;
      if (!id) return;

      if (btn.classList.contains("btn-edit")) window.editEns(id);
      else if (btn.classList.contains("btn-detail")) window.showEnsDetail(id);
      else if (btn.classList.contains("btn-danger")) window.deleteEns(id);
    });
  }

  // ===============================
  // 🔟 Charger utilisateurs et matières
  // ===============================
  async function chargerSelects() {
    try {
      const res = await fetch("/enseignants/options");
      if (!res.ok) throw new Error("Impossible de récupérer options");
      const payload = await res.json();

      window.utilisateursMap = {};
      window.matieresMap = {};

      const selUsers = document.getElementById("utilisateur_id");
      if (selUsers) {
        selUsers.innerHTML = `<option value="">-- Sélectionnez un utilisateur --</option>`;
        (payload.utilisateurs || []).forEach(u => {
          selUsers.innerHTML += `<option value="${u.id}">${u.nom} ${u.prenoms}${u.email ? ' — ' + u.email : ''}</option>`;
          utilisateursMap[u.id] = u;
        });
      }

      const selMat = document.getElementById("matiere_id");
      if (selMat) {
        selMat.innerHTML = `<option value="">-- Sélectionnez une matière --</option>`;
        (payload.matieres || []).forEach(m => {
          selMat.innerHTML += `<option value="${m.id}">${m.libelle}</option>`;
          matieresMap[m.id] = m;
        });
      }

      attachAutoFillListeners();

    } catch (err) {
      console.error(err);
      showNotification("Impossible de charger utilisateurs/matières.", "danger");
    }
  }

  function attachAutoFillListeners() {
    const selUser = document.getElementById("utilisateur_id");
    if (selUser) {
      selUser.addEventListener("change", function () {
        const user = window.utilisateursMap?.[this.value];
        [["add_nom","nom"],["add_prenoms","prenoms"],["add_sexe","sexe"],["add_email","email"],["add_telephone","telephone"],["add_photo_filename","photo_filename"]].forEach(([id,key]) => {
          const el = document.getElementById(id);
          if (el) el.value = (user && user[key]) ? user[key] : "";
        });

        const photoPreview = document.getElementById("add_photo_preview");
        if (photoPreview) {
          if (user && user.photo_filename) {
            photoPreview.src = "/static/upload/" + user.photo_filename;
            photoPreview.style.display = "inline-block";
          } else photoPreview.style.display = "none";
        }
      });
    }

    const selMat = document.getElementById("matiere_id");
    const addMatiereLibelle = document.getElementById("add_matiere_libelle");

    if (selMat && addMatiereLibelle) {
      const selectedMatieres = new Set();

      selMat.addEventListener("mousedown", (e) => e.preventDefault());

      selMat.addEventListener("click", (e) => {
        const option = e.target;
        if (option.tagName !== "OPTION") return;

        const value = option.value;
        if (selectedMatieres.has(value)) {
          selectedMatieres.delete(value);
          option.selected = false;
        } else {
          selectedMatieres.add(value);
          option.selected = true;
        }

        const selectedText = Array.from(selectedMatieres)
          .map(v => selMat.querySelector(`option[value="${v}"]`).text)
          .join(", ");

        addMatiereLibelle.value = selectedText;
      });
    }
  }

  // ===============================
  // 🔹 Initialisation générale
  // ===============================
  initTooltips();
  initFormValidation();
  initWorkflow();
  initAddEns();
  initEditEns();
  initDeleteEns();
  initDetailEns();
  initTableClick();
  chargerSelects();
});

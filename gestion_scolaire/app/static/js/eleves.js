// eleves.js
document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // Au début du fichier, après DOMContentLoaded
  console.log('Initialisation eleves.js');
  console.log('Selects workflow trouvés:', document.querySelectorAll(".select-action").length);

  // Variables globales pour le workflow
  const confirmModalEl = document.getElementById("confirmActionModal");
  const confirmYesBtn = document.getElementById("confirmYesBtn");
  let currentAction = null;
  let currentEleveId = null;
  let currentSelect = null;
  let actionConfirmed = false;

  //Activer les tooltip
  const tooltipTriggerlist = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerlist.map(function(tooltipTriggerEl){
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  const table = document.getElementById("table-eleves");
  table.addEventListener("click", function(e){
    // Bouton modifier
    const editBtn = e.target.closest(".btn-edit");
    if(editBtn){
      editEleve(editBtn.dataset.id);
      return;
    }

    // Bouton détail
    const detailBtn = e.target.closest(".btn-detail");
    if(detailBtn){
      showDetail(detailBtn.dataset.id);
      return;
    }

    // Bouton supprimer
    const deleteBtn = e.target.closest(".btn-danger");
    if(deleteBtn){
      const id = deleteBtn.dataset.id;
      if (!id) {
        alert("Impossible de supprimer : identifiant non défini !");
        return;
      }
      deleteEleve(id);
      return;
    }
  });

  // Fonction pour les notifications
  function showNotification(message, type = "success", delay = 3000) {
    const container = document.getElementById("notificationContainer");
    if (!container) return;

    // Créer l'élément toast
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

    // Initialiser le toast Bootstrap
    const bsToast = new bootstrap.Toast(toastEl, { delay: delay });
    bsToast.show();

    // Supprimer du DOM après disparition
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

  // ---------- Détail élève ----------
  window.showDetail = async function (id) {
    const res = await fetch(`/eleves/detail/${id}`);
    if (!res.ok) return alert("Erreur récupération détail");
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
    new bootstrap.Modal(document.getElementById("detailModal")).show();
  };

 // ---------- Édition ----------
window.editEleve = function (id) {
  const row = document.querySelector(`tr[data-id="eleve-${id}"]`);
  if (!row) return;
  document.getElementById("edit_id").value = id;
  document.getElementById("edit_matricule").value = row.querySelector(".col-matricule")?.innerText.trim() || "";
  document.getElementById("edit_nom").value = row.querySelector(".col-nom")?.innerText.trim() || "";
  document.getElementById("edit_prenoms").value = row.querySelector(".col-prenoms")?.innerText.trim() || "";
  document.getElementById("edit_date_naissance").value = row.querySelector(".col-date_naissance")?.innerText.trim() || "";

  // sexe radio
  const sexe = row.querySelector(".col-sexe")?.innerText.trim();
  if(sexe === "M" || sexe.toLowerCase().includes("masc") ){
    document.getElementById("sexeM").checked = true;
  }else if(sexe === "F" || sexe.toLowerCase().includes( "fém")){
    document.getElementById("sexeF").checked = true;
  }
  // status radio
  const status = row.querySelector(".col-status")?.innerText.trim();
  if (status.toLowerCase() === "nouveau"){
    document.getElementById("statusNouveau").checked = true;
  }else if (status.toLowerCase() === "ancien") {
    document.getElementById("statusAncien").checked = true;
  }

  // classe select
  const classeId = row.dataset.classeId || row.querySelector(".col-classe")?.dataset.id;
  const selectClasse = document.getElementById("edit_classe");
  if (selectClasse) {
    Array.from(selectClasse.options).forEach(opt => {
      opt.selected = (opt.value === classeId);
    });
  }
  new bootstrap.Modal(document.getElementById("editModal")).show();
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
        
        const row = document.querySelector(`tr[data-id="eleve-${id}"]`);
        if (row) {
          // Mettre à jour les données de base
          row.querySelector(".col-matricule") && (row.querySelector(".col-matricule").textContent = updated.matricule);
          row.querySelector(".col-nom") && (row.querySelector(".col-nom").textContent = updated.nom);
          row.querySelector(".col-prenoms") && (row.querySelector(".col-prenoms").textContent = updated.prenoms);
          row.querySelector(".col-date_naissance") && (row.querySelector(".col-date_naissance").textContent = updated.date_naissance || "");
          row.querySelector(".col-sexe") && (row.querySelector(".col-sexe").textContent = updated.sexe);
          row.querySelector(".col-status") && (row.querySelector(".col-status").textContent = updated.status);
          
          // Mettre à jour la classe
          const classeCell = row.querySelector(".col-classe");
          if (classeCell) {
            classeCell.dataset.id = updated.classe_id;
            classeCell.innerHTML = `<span class="badge bg-info">${updated.classe_nom || ""}</span>`;
          }
          
          // CORRECTION CRITIQUE : Mettre à jour l'état
          const etatCell = row.querySelector(".etat");
          if (etatCell && updated.etat) {
            // Mettre à jour le badge
            const badge = etatCell.querySelector(".badge");
            if (badge) {
              badge.textContent = updated.etat;
              
              // Mettre à jour la couleur du badge
              let badgeClass = "bg-secondary";
              const etat = updated.etat.toLowerCase();
              if (etat === "actif") badgeClass = "bg-success";
              else if (etat === "suspendu") badgeClass = "bg-warning";
              else if (etat === "validé") badgeClass = "bg-primary";
              else if (etat === "sorti") badgeClass = "bg-dark";
              badge.className = "badge " + badgeClass;
            }
            
            // Mettre à jour le select d'actions
            updateWorkflowSelect(row, updated.etat);
            
            // Mettre à jour les boutons d'action selon le nouvel état
            const actionCell = row.querySelector('td.text-nowrap');
            const btnEdit = actionCell ? actionCell.querySelector('.btn-edit') : null;
            const btnDelete = actionCell ? actionCell.querySelector('.btn-danger') : null;
            
            if (updated.etat.toLowerCase() !== "inactif") {
              if (btnEdit) btnEdit.remove();
              if (btnDelete) btnDelete.remove();
            }
          }
        }
        
        bootstrap.Modal.getInstance(document.getElementById("editModal"))?.hide();
        showNotification("Modification réussie", "success");
        
      } else {
        const errorData = await res.json();
        alert(errorData.error || "Erreur lors de la modification");
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert("Erreur réseau lors de la modification");
    }
  });
}

  // ---------- Suppression ----------
  window.deleteEleve = async function (id) {
    const res = await fetch(`/eleves/get/${id}`);
    if (!res.ok) return alert("Erreur lecture élève");
    const data = await res.json();
    document.getElementById("delete_id").value = id;
    document.getElementById("delete_info").textContent = `${data.matricule} - ${data.nom} ${data.prenoms}`;
    new bootstrap.Modal(document.getElementById("deleteModal")).show();
  };

  const deleteForm = document.getElementById("deleteForm");
  if (deleteForm) {
    deleteForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = document.getElementById("delete_id").value;
      const res = await fetch(`/eleves/delete/${id}`, { method: "POST" });
      if (res.ok){
        showNotification("Suppression réussie", "success");
        location.reload();
      }
      else alert("Erreur suppression");
    });
  }

  // ---------- Workflow : changer état (modal dynamique) ----------

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
      const modal = new bootstrap.Modal(confirmModalEl);
      modal.show();
    });
  }

 // Fonction pour mettre à jour le select d'actions après modification
function updateWorkflowSelect(row, newEtat) {
  console.log('Mise à jour workflow select pour état:', newEtat);
  
  const etatCell = row.querySelector('.etat');
  if (!etatCell) {
    console.error('Cellule état non trouvée');
    return;
  }

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
    newSelect.dataset.id = row.dataset.id.replace('eleve-', '');
    newSelect.style.display = 'inline-block'; // Force l'affichage

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
    console.log('Nouveau select ajouté');

    // Réattacher le comportement
    attachWorkflowChange(newSelect);
  } else {
    console.log('Select non créé (admin:', isAdmin, 'état:', newEtat, ')');
  }
}

  // Attacher à tous les selects existants au chargement
  document.querySelectorAll(".select-action").forEach(attachWorkflowChange);

  // Si l'utilisateur confirme (Oui)
  confirmYesBtn.addEventListener("click", async function () {
    if (!currentAction || !currentEleveId || !currentSelect) return;

    confirmYesBtn.disabled = true;

    try {
      const res = await fetch(`/eleves/${currentEleveId}/changer_etat`, {
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
        bootstrap.Modal.getInstance(confirmModalEl)?.hide();
        return;
      }

      // Succès : mise à jour
      actionConfirmed = true;

      const row = document.querySelector(`tr[data-id="eleve-${currentEleveId}"]`);
      if (!row) {
        console.error("Ligne non trouvée pour l'élève:", currentEleveId);
        return;
      }

      const td = currentSelect.closest("td");
      const badge = td && td.querySelector("span");
      
      if (badge) {
        badge.textContent = data.etat;

        // Mettre à jour la classe du badge
        let badgeClass;
        const etat = data.etat.toLowerCase();

        if (etat === "actif") {
          badgeClass = "bg-success";
        } else if (etat === "suspendu") {
          badgeClass = "bg-warning";
        } else if (etat === "validé") {
          badgeClass = "bg-primary";
        } else if (etat === "sorti") {
          badgeClass = "bg-dark";
        } else {
          badgeClass = "bg-secondary";
        }

        badge.className = "badge " + badgeClass;
      }

      /* Mettre à jour les boutons Modifier / Supprimer selon le nouvel état */
      const actionCell = row.querySelector('td.text-nowrap') || row.lastElementChild;
      const btnEdit = actionCell ? actionCell.querySelector('.btn-edit') : null;
      const btnDelete = actionCell ? actionCell.querySelector('.btn-danger') : null;

      if (data.etat.toLowerCase() !== "inactif") {
        if (btnEdit) btnEdit.remove();
        if (btnDelete) btnDelete.remove();
      }

      // Mettre à jour le select d'actions
      updateWorkflowSelect(row, data.etat);

      bootstrap.Modal.getInstance(confirmModalEl)?.hide();
      showNotification(`État changé avec succès: ${data.etat}`, "success");

    } catch (err) {
      console.error(err);
      alert("Erreur réseau");
      if (currentSelect) currentSelect.value = "";
    } finally {
      confirmYesBtn.disabled = false;
    }
  });

  // Reset du select si modal fermé sans confirmation
  confirmModalEl.addEventListener("hidden.bs.modal", function () {
    if (!actionConfirmed && currentSelect) {
      currentSelect.value = "";
    }
    currentAction = null;
    currentEleveId = null;
    currentSelect = null;
    actionConfirmed = false;
  });

  // Mettre à jour les selects après modification d'un élève
  window.refreshWorkflowSelects = function() {
    document.querySelectorAll(".select-action").forEach(select => {
      // Réattacher les événements
      attachWorkflowChange(select);
    });
  };
});
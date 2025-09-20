document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // ======================
  // 1️⃣ Filtrage par classe
  // ======================
  function initFilterClasse() {
    const classeSelect = document.querySelector("select[name='classe_id']");
    classeSelect?.addEventListener("change", () => document.getElementById("filterForm")?.submit());
  }

  // ======================
  // 2️⃣ Calcul montant restant
  // ======================
  function bindCalculRest(montantNetInput, montantPayInput, montantRestInput) {
    if (!montantNetInput || !montantPayInput || !montantRestInput) return;
    const calculerRest = () => {
      const net = parseFloat(montantNetInput.value) || 0;
      const pay = parseFloat(montantPayInput.value) || 0;
      montantRestInput.value = (net - pay).toFixed(2);
    };
    montantNetInput.addEventListener("input", calculerRest);
    montantPayInput.addEventListener("input", calculerRest);
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
  // 4️⃣ Notifications
  // ======================
  function showNotification(message, type = "success", delay = 3000) {
    const container = document.getElementById("notificationContainer");
    if (!container) return;

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-bg-${type} border-0 mb-2`;
    toastEl.role = "alert";
    toastEl.ariaLive = "assertive";
    toastEl.ariaAtomic = "true";
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast" aria-label="Fermer"></button>
      </div>
    `;
    container.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay });
    toast.show();
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
  }

  // ======================
  // 5️⃣ Workflow paiements
  // ======================
  function initWorkflowButtons() {
    document.querySelectorAll(".select-action").forEach(select => {
      select.removeEventListener("change", workflowChangeHandler); // éviter doublons
      select.addEventListener("change", workflowChangeHandler);
    });
  }

  async function workflowChangeHandler(e) {
     const action = e.target.value;
     if (!action) return;

     const paiementId = e.target.dataset.id;
     const currentSelect = e.target;
     const tr = currentSelect.closest("tr"); // ligne du paiement

    showConfirm(`Voulez-vous vraiment ${action.toLowerCase()} ce paiement ?`, async () => {
    try {
      const res = await fetch(`/paiements/workflow/${paiementId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action })
      });
      const result = await res.json();

      if (res.ok && !result.error) {
        // Mettre à jour le badge
        const badge = tr.querySelector(".badge");
        if (badge) {
          badge.textContent = result.etat;
          badge.className = "badge " + (
            result.etat === "Actif" ? "bg-success" :
            result.etat === "Validé" ? "bg-dark" :
            "bg-secondary"
            );
          }
                
          // 🔹 Supprimer boutons edit/delete après première action
        if (result.etat.toLowerCase() === "actif") {
          tr.querySelectorAll(".btn-edit, .btn-delete").forEach(btn => btn.remove());
        }
          rebuildWorkflowSelect(currentSelect, paiementId, result.etat, tr);
          showNotification(result.message, "success");
        } else {
          showNotification(result.error || result.message, "danger");
        }
      } catch (err) {
        console.error(err);
        showNotification("Erreur lors de la modification de l'état", "danger");
      } finally {
        currentSelect.value = "";
      }
    });
  }

function rebuildWorkflowSelect(select, id, etat, tr) {
  const td = select.closest("td");
  if (!td) return;

  // On supprime l'ancien select
  select.remove();

  // 🔹 Si état final "Validé", on ne recrée pas le select
  if (etat.toLowerCase() === "validé") return;

  // 🔹 Recréer le select pour les états intermédiaires
  const newSelect = document.createElement("select");
  newSelect.className = "form-select form-select-sm d-inline-block w-auto ms-2 select-action";
  newSelect.dataset.id = id;

  let options = `<option value="">---Action---</option>`;
  switch (etat.toLowerCase()) {
    case "inactif":
      options += `<option value="Activer">Activer</option>`;
      break;
    case "actif":
      options += `<option value="Valider">Valider</option>`;
      break;
  }

  newSelect.innerHTML = options;
  td.appendChild(newSelect);

  // 🔹 Réattacher le handler
  initWorkflowButtons();
}


  // ======================
  // 6️⃣ Paiement Actions (edit, detail, delete)
  // ======================
  function initPaiementActions() {
    const tbody = document.querySelector("table tbody");
    tbody?.addEventListener("click", async (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      const paiementId = btn.dataset.id;

      if (btn.classList.contains("btnPay-detail")) showDetailPaiement(paiementId);
      else if (btn.classList.contains("btnPay-edit")) showEditPaiementModal(paiementId);
      else if (btn.classList.contains("btnPay-delete")) {
        showConfirm("Voulez-vous supprimer ce paiement ?", () => deletePaiement(paiementId));
      }
    });
  }

  async function showDetailPaiement(id) {
    const res = await fetch(`/paiements/detail/${id}`);
    const p = await res.json();
    const modal = new bootstrap.Modal(document.getElementById("paiementDetailModal"));
    document.getElementById("detail_code").textContent = p.code;
    document.getElementById("detail_eleve").textContent = p.eleve;
    document.getElementById("detail_classe").textContent = p.classe;
    document.getElementById("detail_libelle").textContent = p.libelle;
    document.getElementById("detail_date").textContent = p.date_payement;
    document.getElementById("detail_montant_net").textContent = p.montant_net.toFixed(2);
    document.getElementById("detail_montant_pay").textContent = p.montant_pay.toFixed(2);
    document.getElementById("detail_montant_rest").textContent = p.montant_rest.toFixed(2);
    modal.show();
  }

  async function showEditPaiementModal(id) {
    const res = await fetch(`/paiements/detail/${id}`);
    const p = await res.json();
    const modalEl = document.getElementById("paiementEditModal");
    const modal = new bootstrap.Modal(modalEl);

    const eleveSelect = document.getElementById("edit_eleve_id");
    const classeSelect = document.getElementById("edit_classe_id");
    eleveSelect.innerHTML = `<option value="${p.eleve_id}" selected>${p.eleve}</option>`;
    classeSelect.innerHTML = `<option value="${p.classe_id}" selected>${p.classe}</option>`;
    eleveSelect.disabled = true;
    classeSelect.disabled = true;

    document.getElementById("edit_paiement_id").value = p.id;
    document.getElementById("edit_libelle").value = p.libelle;
    document.getElementById("edit_date_payement").value = p.date_payement;
    document.getElementById("edit_montant_net").value = p.montant_net;
    document.getElementById("edit_montant_pay").value = p.montant_pay;
    document.getElementById("edit_montant_rest").value = p.montant_rest.toFixed(2);

    bindCalculRest(
      document.getElementById("edit_montant_net"),
      document.getElementById("edit_montant_pay"),
      document.getElementById("edit_montant_rest")
    );

    modal.show();
  }

 async function deletePaiement(id) {
  const res = await fetch(`/paiements/delete/${id}`, { method: "POST" });
  const result = await res.json();

  if (res.ok && result.status === "success") {
    showNotification(result.message, "success");
    location.reload();
  } else {
    showNotification(result.error || result.message, "danger");
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
      const submitter = e.submitter;
      if (submitter && submitter.dataset.bsDismiss === "modal") return;

      showConfirm("Voulez-vous vraiment modifier ce paiement ?", async () => {
        const paiementId = editForm.edit_paiement_id.value;
        try {
          const res = await fetch(`/paiements/edit/${paiementId}`, { method: "POST", body: new FormData(editForm) });
          if (!res.ok) throw new Error(await res.text());

          const result = await res.json();
          showNotification(result.message, "success");
          bootstrap.Modal.getInstance(document.getElementById("paiementEditModal"))?.hide();
          location.reload();
        } catch (err) {
          console.error(err);
          showNotification("Erreur lors de la modification", "danger");
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
      classeSelect.value = classeId || "";
    });
  }

  // ======================
  // 9️⃣ AJAX ajout paiement
  // ======================
  function addPaiementInit() {
    const paiementForm = document.getElementById("paiementForm");
    if (!paiementForm) return;

    paiementForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(paiementForm);

      try {
        const res = await fetch(paiementForm.action, { method: "POST", body: formData });
        if (!res.ok) throw new Error(await res.text());

        const result = await res.json();
        if (result.status === "success") {
          showNotification(result.message, "success");
          bootstrap.Modal.getInstance(document.getElementById("paiementModal"))?.hide();
          paiementForm.reset();
          document.getElementById("montant_rest").value = "";
          location.reload();
        } else {
          showNotification(result.message, "warning");
        }
      } catch (err) {
        console.error(err);
        showNotification("Erreur lors de l'ajout du paiement", "danger");
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
  }

  init();
});

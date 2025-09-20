document.addEventListener("DOMContentLoaded", () => {
  const modalEl = document.getElementById("addNoteModal");
  if (!modalEl) return;

  const trimestreSelect = modalEl.querySelector("#trimestre");
  const anneeSelect = modalEl.querySelector("#anneeScolaire");
  const treesContainer = modalEl.querySelector("#treesContainer");
  const classeFilter = modalEl.querySelector("#classeFilter");
  const noteInputsContainer = modalEl.querySelector("#noteInputsContainer");
  const note1Input = modalEl.querySelector("#note1");
  const note2Input = modalEl.querySelector("#note2");
  const note3Input = modalEl.querySelector("#note3");
  const noteCompInput = modalEl.querySelector("#note_comp");
  const coefficientSelect = modalEl.querySelector("#coefficient");
  const btnSaveNote = modalEl.querySelector("#btnSaveNote");
  const notificationContainer = modalEl.querySelector("#notificationContainer");
  const btnCloture = modalEl.querySelector("#btnCloture");

  let selectedEleve = null;
  let selectedMatiere = null;

  // ===============================
  // Notifications
  // ===============================
  function showNotification(message, type = "success", delay = 3000) {
    const div = document.createElement("div");
    div.className = `alert alert-${type} alert-dismissible fade show`;
    div.textContent = message;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-close";
    btn.dataset.bsDismiss = "alert";
    div.appendChild(btn);
    notificationContainer.appendChild(div);
    setTimeout(() => div.remove(), delay);
  }

  // ===============================
  // Générer années scolaires
  // ===============================
// Charger uniquement les années actives depuis le backend
async function loadAnneesActives() {
  try {
    const resp = await fetch("/notes/annees/actives");
    const annees = await resp.json();

    anneeSelect.innerHTML = '<option value="">-- Sélectionnez une année --</option>';
    annees.forEach(a => {
      const option = document.createElement("option");
      option.value = a;
      option.textContent = a;
      anneeSelect.appendChild(option);
    });
    return annees;
  } catch (err) {
    console.error("Erreur chargement années actives:", err);
    return[];
  }
}


  // ===============================
  // Affichage des arbres élèves/matières
  // ===============================
  function checkShowTrees() {
    if (trimestreSelect.value && anneeSelect.value) {
      treesContainer.classList.remove("d-none");
      loadElevesMatieres();
    } else {
      treesContainer.classList.add("d-none");
      noteInputsContainer.classList.add("d-none");
    }
  }

  trimestreSelect.addEventListener("change", checkShowTrees);
  anneeSelect.addEventListener("change", checkShowTrees);
  modalEl.addEventListener("show.bs.modal", async () => {
  await loadAnneesActives();
  checkShowTrees();
});

// ===============================
// Création noeuds matières (parents + feuilles)
// ===============================
function createMatiereNode(m, level = 0) {
  const li = document.createElement("li");
  const paddingLeft = 10 + level * 25;
  // Un parent est défini par la présence de children
  const isParent = m.children && m.children.length > 0;

  li.classList.add("matiere-item");
  li.dataset.id = m.id || "";
  li.dataset.isParent = isParent ? "true" : "false";

  li.innerHTML = `
    <div class="matiere-label d-flex align-items-center ${isParent ? "parent-label" : ""}" 
         style="padding-left:${paddingLeft}px;">
      ${isParent ? '<span class="chevron me-2">▶</span>' : ''}
      <span>${m.libelle}</span>
    </div>
  `;

  if (isParent) {
    const ul = document.createElement("ul");
    ul.className = "child-list list-group mt-1 d-none";

    if (m.children && m.children.length > 0) {
      m.children.forEach(c => ul.appendChild(createMatiereNode(c, level + 1)));
    }
    li.appendChild(ul);

    const chevron = li.querySelector(".chevron");
    const labelDiv = li.querySelector(".matiere-label");
    labelDiv.addEventListener("click", (e) => {
      ul.classList.toggle("d-none");
      chevron.classList.toggle("expanded");
      e.stopPropagation();
    });
  }

  return li;
}


  // ===============================
  // Charger élèves et matières
  // ===============================
  async function loadElevesMatieres() {
    try {
      const resp = await fetch("/notes/list_elements");
      const data = await resp.json();

      // Classes
      classeFilter.innerHTML = '<option value="">Toutes les classes</option>';
      data.classes.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.nom;
        classeFilter.appendChild(opt);
      });

      // Élèves
      const eleveTree = modalEl.querySelector("#eleveTree");
      eleveTree.innerHTML = "";
      data.eleves.forEach(e => {
        const li = document.createElement("li");
        li.className = "list-group-item eleve-item";
        li.dataset.classe = e.classe_id;
        li.dataset.id = e.id;
        li.textContent = `${e.nom} ${e.prenoms}`;
        li.style.cursor = "pointer";
        eleveTree.appendChild(li);
      });

      // Matières
      const matiereTree = modalEl.querySelector("#matiereTree");
      matiereTree.innerHTML = "";
      data.matieres.forEach(m => matiereTree.appendChild(createMatiereNode(m)));

      initListeners();
    } catch (err) {
      console.error("Erreur chargement :", err);
    }
  }

  function updateNoteInputsVisibility() {
    noteInputsContainer.classList.toggle("d-none", !(selectedEleve && selectedMatiere));
  }

// ===============================
// Sélection matière + élève (désélection possible)
// ===============================
function initListeners() {
  // Filtrer par classe
  classeFilter.addEventListener("change", e => {
    const val = e.target.value;
    document.querySelectorAll("#eleveTree .eleve-item").forEach(li => {
      li.style.display = (!val || li.dataset.classe === val) ? "" : "none";
    });
  });

  // Sélection élève
  document.querySelectorAll("#eleveTree .eleve-item").forEach(li => {
    li.addEventListener("click", () => {
      const wasActive = li.classList.contains("active");
      document.querySelectorAll("#eleveTree .eleve-item").forEach(x => x.classList.remove("active"));
      if (!wasActive) li.classList.add("active");
      selectedEleve = li.classList.contains("active") ? li.dataset.id : null;
      updateNoteInputsVisibility();
    });
  });

  // Sélection matière (uniquement feuilles)
  document.querySelectorAll("#matiereTree .matiere-item").forEach(li => {
    if (li.dataset.isParent === "true") return; // ignorer les parents
    li.addEventListener("click", (e) => {
      const wasActive = li.classList.contains("active");
      document.querySelectorAll("#matiereTree .matiere-item").forEach(x => x.classList.remove("active"));
      if (!wasActive) li.classList.add("active");
      selectedMatiere = li.classList.contains("active") ? li.dataset.id : null;
      updateNoteInputsVisibility();
      e.stopPropagation(); // empêche le toggle parent si nested
    });
  });
}

  // ===============================
  // Sauvegarde note
  // ===============================
  btnSaveNote.addEventListener("click", async () => {
    const data = {
      eleve_id: selectedEleve,
      matiere_id: selectedMatiere,
      trimestre: trimestreSelect.value,
      annee_scolaire: anneeSelect.value,
      note1: note1Input.value || null,
      note2: note2Input.value || null,
      note3: note3Input.value || null,
      note_comp: noteCompInput.value || null,
      coefficient: coefficientSelect.value
    };

    if (!data.eleve_id || !data.matiere_id || !data.trimestre || !data.annee_scolaire) {
      showNotification("Veuillez sélectionner le trimestre, l'année scolaire, un élève et une matière.", "warning");
      return;
    }

    try {
      const resp = await fetch("/notes/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      const result = await resp.json();

      if (resp.ok) {
        showNotification(result.message || "Note enregistrée !", "success");

        // Ajouter / Mettre à jour la ligne dans le tableau
        const tbody = document.querySelector("#notesTable tbody");
        if (tbody && result.note_html) {
          const wrapper = document.createElement("tbody");
          wrapper.innerHTML = result.note_html.trim();
          const rowEl = wrapper.querySelector("tr");
          if (rowEl) {
            const existingRow = tbody.querySelector(`tr[data-id='${rowEl.dataset.id}']`);
            if (existingRow) existingRow.outerHTML = rowEl.outerHTML;
            else tbody.insertAdjacentHTML("beforeend", rowEl.outerHTML);
          }
        }

        note1Input.value = "";
        note2Input.value = "";
        note3Input.value = "";
        noteCompInput.value = "";
      } else {
        showNotification(result.error, "danger");
      }
    } catch (err) {
      showNotification("Erreur serveur : " + err.message, "danger");
    }
  });

  // ===============================
  // Détail note
  // ===============================
  document.addEventListener("click", async (e) => {
    const detailBtn = e.target.closest(".btn-detail-note");
    if (detailBtn) {
      const id = detailBtn.dataset.id;
      const modal = new bootstrap.Modal(document.getElementById("noteDetailModal"));
      const body = document.getElementById("noteDetailContent");
      body.innerHTML = "<p>Chargement...</p>";
      try {
        const resp = await fetch(`/notes/${id}`);
        const note = await resp.json();
        if (resp.ok) {
          body.innerHTML = `
            <ul class="list-group">
              <li class="list-group-item"><b>Élève:</b> ${note.eleve_nom}</li>
              <li class="list-group-item"><b>Matière:</b> ${note.matiere_nom}</li>
              <li class="list-group-item"><b>Notes:</b> ${note.note1 || ""}, ${note.note2 || ""}, ${note.note3 || ""}, Comp: ${note.note_comp || ""}</li>
              <li class="list-group-item"><b>Coefficient:</b> ${note.coefficient}</li>
              <li class="list-group-item"><b>Trimestre:</b> ${note.trimestre}</li>
              <li class="list-group-item"><b>Année:</b> ${note.annee_scolaire}</li>
              <li class="list-group-item"><b>État:</b> ${note.etat}</li>
            </ul>
          `;
        } else body.innerHTML = `<p class="text-danger">${note.error}</p>`;
      } catch (err) {
        body.innerHTML = `<p class="text-danger">Erreur : ${err.message}</p>`;
      }
      modal.show();
    }
  });

  // ===============================
  // Modification note
  // ===============================
  document.addEventListener("click", async (e) => {
    const editBtn = e.target.closest(".btn-edit-note");
    if (!editBtn) return;
    const id = editBtn.dataset.id;
    const modalEl = document.getElementById("editNoteModal");
    const modal = new bootstrap.Modal(modalEl);
    const form = modalEl.querySelector("#editNoteForm");

    try {
      const resp = await fetch(`/notes/${id}`);
      const note = await resp.json();
      if (resp.ok) {
        form.note_id.value = note.id;
        form.note1.value = note.note1 || "";
        form.note2.value = note.note2 || "";
        form.note3.value = note.note3 || "";
        form.note_comp.value = note.note_comp || "";
        form.coefficient.value = note.coefficient || "";
        modal.show();
      } else {
        showNotification(note.error, "danger");
      }
    } catch (err) {
      showNotification("Erreur : " + err.message, "danger");
    }
  });

  document.getElementById("editNoteForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const id = form.note_id.value;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
      const resp = await fetch(`/notes/${id}/edit`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      const result = await resp.json();
      if (resp.ok) {
        showNotification(result.message, "success");
        const tbody = document.querySelector("#notesTable tbody");
        if (tbody && result.note_html) {
          const wrapper = document.createElement("tbody");
          wrapper.innerHTML = result.note_html.trim();
          const rowEl = wrapper.querySelector("tr");
          if (rowEl) {
            const existingRow = tbody.querySelector(`tr[data-id='${rowEl.dataset.id}']`);
            if (existingRow) existingRow.outerHTML = rowEl.outerHTML;
          }
        }
        bootstrap.Modal.getInstance(form.closest(".modal")).hide();
      } else {
        showNotification(result.error, "danger");
      }
    } catch (err) {
      showNotification("Erreur serveur : " + err.message, "danger");
    }
  });

  // ===============================
  // Suppression note
  // ===============================
  let noteToDelete = null;

  document.addEventListener("click", (e) => {
    const delBtn = e.target.closest(".btn-delete-note");
    if (!delBtn) return;
    noteToDelete = delBtn.dataset.id;
    const modal = new bootstrap.Modal(document.getElementById("deleteNoteModal"));
    modal.show();
  });

  document.getElementById("confirmDeleteNote")?.addEventListener("click", async () => {
    if (!noteToDelete) return;
    try {
      const resp = await fetch(`/notes/${noteToDelete}/delete`, { method: "DELETE" });
      const result = await resp.json();
      if (resp.ok) {
        document.querySelector(`#notesTable tbody tr[data-id='${noteToDelete}']`)?.remove();
        showNotification(result.message, "success");
        bootstrap.Modal.getInstance(document.getElementById("deleteNoteModal")).hide();
      } else {
        showNotification(result.error, "danger");
      }
    } catch (err) {
      showNotification("Erreur serveur : " + err.message, "danger");
    }
  });

  // ===============================
  // Gestion clôtures
  // ===============================
  async function loadClotures() {
    try {
      const resp = await fetch("/notes/clotures/actifs");
      const data = await resp.json();
      const clotureList = document.getElementById("clotureList");
      clotureList.innerHTML = "";

      if (!data.length) {
        clotureList.innerHTML = "<li class='list-group-item'>Aucune période active</li>";
        return;
      }

      // Grouper par année
      const grouped = {};
      data.forEach(p => {
        if (!grouped[p.annee]) grouped[p.annee] = [];
        grouped[p.annee].push(p.trimestre);
      });

      for (const [annee, trimestres] of Object.entries(grouped)) {
        const li = document.createElement("li");
        li.className = "list-group-item";
        li.innerHTML = `<b>${annee}</b>`;
        const btnAll = document.createElement("button");
        btnAll.className = "btn btn-sm btn-danger ms-2";
        btnAll.textContent = "Clôturer toute l'année";
        btnAll.addEventListener("click", () => cloturerPeriode(annee, null));
        li.appendChild(btnAll);

        trimestres.forEach(t => {
          const btnTrim = document.createElement("button");
          btnTrim.className = "btn btn-sm btn-warning ms-2";
          btnTrim.textContent = `T${t}`;
          btnTrim.addEventListener("click", () => cloturerPeriode(annee, t));
          li.appendChild(btnTrim);
        });

        clotureList.appendChild(li);
      }
    } catch (err) {
      console.error("Erreur chargement clotures :", err);
      showNotification("Erreur serveur : " + err.message, "danger");
    }
  }

  async function cloturerPeriode(annee, trimestre = null) {
    try {
      const resp = await fetch("/notes/clotures/close", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ annee, trimestre })
      });
      const result = await resp.json();
      if (resp.ok) {
        showNotification(result.message, "success");
        loadClotures();
      } else {
        showNotification(result.error, "danger");
      }
    } catch (err) {
      showNotification("Erreur serveur : " + err.message, "danger");
    }
  }

  btnCloture?.addEventListener("click", loadClotures);
});

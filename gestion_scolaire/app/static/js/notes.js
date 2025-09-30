document.addEventListener("DOMContentLoaded", () => {
  // ===============================
  // Références DOM
  // ===============================
  const addModalEl = document.getElementById("addNoteModal");
  const editModalEl = document.getElementById("editNoteModal");
  const deleteModalEl = document.getElementById("deleteNoteModal");
  const detailModalEl = document.getElementById("noteDetailModal");

  if (!addModalEl) return;

  const trimestreSelect = addModalEl.querySelector("#trimestre");
  const anneeSelect = addModalEl.querySelector("#anneeScolaire");
  const treesContainer = addModalEl.querySelector("#treesContainer");
  const classeFilter = addModalEl.querySelector("#classeFilterModal");
  const noteInputsContainer = addModalEl.querySelector("#noteInputsContainer");
  const note1Input = addModalEl.querySelector("#note1");
  const note2Input = addModalEl.querySelector("#note2");
  const note3Input = addModalEl.querySelector("#note3");
  const noteCompInput = addModalEl.querySelector("#note_comp");
  const coefficientSelect = addModalEl.querySelector("#coefficient");
  const btnSaveNote = addModalEl.querySelector("#btnSaveNote");
  const notificationContainer = document.getElementById("notificationContainer");
  const btnCloture = document.getElementById("btnCloture");

  // ===============================
  // Variables globales
  // ===============================
  let selectedEleve = null;
  let selectedMatiere = null;
  let selectedEnseignant = null;
  let noteToDelete = null;

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
      return [];
    }
  }

  // ===============================
  // Affichage arbres élèves/matières
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
  addModalEl.addEventListener("show.bs.modal", async () => {
    await loadAnneesActives();
    checkShowTrees();
  });

  // ===============================
  // Création noeud matière
  // ===============================
  function createMatiereNode(m, level = 0) {
    const li = document.createElement("li");
    const paddingLeft = 10 + level * 25;
    const isParent = m.children && m.children.length > 0;

    li.classList.add("matiere-item");
    li.dataset.id = m.id || "";
    li.dataset.isParent = isParent ? "true" : "false";

    if (m.enseignant_id) {
      li.dataset.enseignantId = m.enseignant_id;
      li.dataset.enseignantNom = m.enseignant_nom || "";
      li.dataset.enseignantPrenoms = m.enseignant_prenoms || "";
    }

    li.innerHTML = `
      <div class="matiere-label d-flex align-items-center ${isParent ? "parent-label" : ""}" 
           style="padding-left:${paddingLeft}px;">
        ${isParent ? '<span class="chevron me-2">▶</span>' : ""}
        <span>${m.libelle}</span>
      </div>
    `;

    if (isParent) {
      const ul = document.createElement("ul");
      ul.className = "child-list list-group mt-1 d-none";
      m.children.forEach(c => ul.appendChild(createMatiereNode(c, level + 1)));
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
        const option = document.createElement('option');
        option.value = c.id;
        option.textContent = c.nom;
        classeFilter.appendChild(option);
      });

      // Élèves
      const eleveTree = addModalEl.querySelector("#eleveTree");
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

      // Enseignants
      const enseignantSelect = addModalEl.querySelector("#enseignantSelect");
      enseignantSelect.innerHTML = '<option value="">-- Sélectionnez un enseignant --</option>';
      data.enseignants.forEach(e => {
        const opt = document.createElement("option");
        opt.value = e.id;
        opt.textContent = `${e.nom || e.noms} ${e.prenoms}`;
        enseignantSelect.appendChild(opt);
      });

      // Matières
      const matiereTree = addModalEl.querySelector("#matiereTree");
      matiereTree.innerHTML = "";
      data.matieres.forEach(m => matiereTree.appendChild(createMatiereNode(m)));

      // Edition enseignants
      const enseignantEditSelect = editModalEl?.querySelector("#editEnseignantSelect");
      if (enseignantEditSelect) {
        enseignantEditSelect.innerHTML = '<option value="">-- Sélectionnez un enseignant --</option>';
        data.enseignants.forEach(e => {
          const opt = document.createElement("option");
          opt.value = e.id;
          opt.textContent = `${e.noms} ${e.prenoms}`;
          enseignantEditSelect.appendChild(opt);
        });
      }

      initListeners();
    } catch (err) {
      console.error("Erreur chargement :", err);
    }
  }

  function updateNoteInputsVisibility() {
    noteInputsContainer.classList.toggle("d-none", !(selectedEleve && selectedMatiere));
  }

  // ===============================
  // Sélection élève & matière
  // ===============================
  function initListeners() {
    // Filtrer par classe
    classeFilter.addEventListener("change", e => {
      const val = e.target.value;
      document.querySelectorAll("#eleveTree .eleve-item").forEach(li => {
        li.style.display = (!val || li.dataset.classe === val) ? "" : "none";
      });
    });

    // Élève
    document.querySelectorAll("#eleveTree .eleve-item").forEach(li => {
      li.addEventListener("click", () => {
        const wasActive = li.classList.contains("active");
        document.querySelectorAll("#eleveTree .eleve-item").forEach(x => x.classList.remove("active"));
        if (!wasActive) li.classList.add("active");
        selectedEleve = li.classList.contains("active") ? li.dataset.id : null;
        updateNoteInputsVisibility();
      });
    });

    // Matière
    document.querySelectorAll("#matiereTree .matiere-item").forEach(li => {
      if (li.dataset.isParent === "true") return;
      li.addEventListener("click", (e) => {
        const wasActive = li.classList.contains("active");
        document.querySelectorAll("#matiereTree .matiere-item").forEach(x => x.classList.remove("active"));
        if (!wasActive) li.classList.add("active");
        selectedMatiere = li.classList.contains("active") ? li.dataset.id : null;
        selectedEnseignant = li.classList.contains("active") ? li.dataset.enseignantId : null;
        updateNoteInputsVisibility();
        e.stopPropagation();
      });
    });
  }

  // ===============================
  // Contrôle temps réel sur les notes
  // ===============================
function validateNoteInput(input) {
  input.addEventListener("input", () => {
    if (!input.value) return;
    let raw = input.value.replace(",", ".");
    let val = parseFloat(raw);
    if (isNaN(val) || val < 0 || val > 20) {
      input.value = "";
      showNotification("Veuillez saisir un nombre compris entre 0 et 20", "warning");
      return;
    }
    input.value = raw;
  });
}


  [note1Input, note2Input, note3Input, noteCompInput].forEach(inp => inp && validateNoteInput(inp));
  editModalEl?.querySelectorAll("#editNoteForm input[type='number']")?.forEach(inp => validateNoteInput(inp));

  // ===============================
  // Sauvegarde note
  // ===============================
  btnSaveNote.addEventListener("click", async () => {
    const enseignantSelect = addModalEl.querySelector("#enseignantSelect");
    const chosenEnseignant = enseignantSelect.value || selectedEnseignant;

    const n1 = note1Input.value ? parseFloat(note1Input.value.replace(",", ".")) : null;
    const n2 = note2Input.value ? parseFloat(note2Input.value.replace(",", ".")) : null;
    const n3 = note3Input.value ? parseFloat(note3Input.value.replace(",", ".")) : null;
    const nComp = noteCompInput.value ? parseFloat(noteCompInput.value.replace(",", ".")) : null;

    const allNotes = [n1, n2, n3, nComp].filter(v => v !== null);
    if (allNotes.some(v => isNaN(v) || v < 0 || v > 20)) {
      showNotification("Veuillez saisir un nombre compris entre 0 et 20", "warning");
      return;
    }

    const data = {
      eleve_id: selectedEleve,
      matiere_id: selectedMatiere,
      enseignant_id: chosenEnseignant,
      trimestre: trimestreSelect.value,
      annee_scolaire: anneeSelect.value,
      note1: n1,
      note2: n2,
      note3: n3,
      note_comp: nComp,
      coefficient: coefficientSelect.value
    };

    if (!data.eleve_id || !data.matiere_id || !data.trimestre || !data.annee_scolaire || !data.enseignant_id) {
      showNotification("Veuillez sélectionner le trimestre, l'année scolaire, un élève, une matière et un enseignant.", "warning");
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
        [note1Input, note2Input, note3Input, noteCompInput].forEach(inp => inp.value = "");
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
    const detailBtn = e.target.closest("button.btn-detail-note");
    if (!detailBtn) return;
    const id = detailBtn.dataset.id;
    const modal = new bootstrap.Modal(detailModalEl);
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
            <li class="list-group-item"><b>Enseignant:</b> ${note.enseignant_nom || ""} ${note.enseignant_prenoms || ""}</li>
            <li class="list-group-item"><b>Notes:</b> ${note.note1 || ""}, ${note.note2 || ""}, ${note.note3 || ""}, Comp: ${note.note_comp || ""}</li>
            <li class="list-group-item"><b>Coefficient:</b> ${note.coefficient}</li>
            <li class="list-group-item"><b>Trimestre:</b> ${note.trimestre}</li>
            <li class="list-group-item"><b>Année:</b> ${note.annee_scolaire}</li>
            <li class="list-group-item"><b>État:</b> ${note.etat}</li>
          </ul>
        `;
      } else {
        body.innerHTML = `<p class="text-danger">${note.error}</p>`;
      }
    } catch (err) {
      body.innerHTML = `<p class="text-danger">Erreur : ${err.message}</p>`;
    }
    modal.show();
  });

  // ===============================
  // Modification note
  // ===============================
  document.addEventListener("click", async (e) => {
    const editBtn = e.target.closest("button.btn-edit-note");
    if (!editBtn) return;
    const id = editBtn.dataset.id;
    const modal = new bootstrap.Modal(editModalEl);
    const form = editModalEl.querySelector("#editNoteForm");

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
        // 🔹 Attacher la validation après remplissage
      [form.note1, form.note2, form.note3, form.note_comp].forEach(inp => validateNoteInput(inp));
        modal.show();
      } else {
        showNotification(note.error, "danger");
      }
    } catch (err) {
      showNotification("Erreur : " + err.message, "danger");
    }
  });

  editModalEl?.querySelector("#editNoteForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const id = form.note_id.value;

    const n1 = form.note1.value ? parseFloat(form.note1.value.replace(",", ".")) : null;
    const n2 = form.note2.value ? parseFloat(form.note2.value.replace(",", ".")) : null;
    const n3 = form.note3.value ? parseFloat(form.note3.value.replace(",", ".")) : null;
    const nComp = form.note_comp.value ? parseFloat(form.note_comp.value.replace(",", ".")) : null;

    if ([n1, n2, n3, nComp].filter(v => v !== null).some(v => isNaN(v) || v < 0 || v > 20)) {
      showNotification("Veuillez saisir un nombre compris entre 0 et 20", "warning");
      return;
    }

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
        bootstrap.Modal.getInstance(editModalEl).hide();
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
  document.addEventListener("click", (e) => {
    const delBtn = e.target.closest(".btn-delete-note");
    if (!delBtn) return;
    noteToDelete = delBtn.dataset.id;
    const modal = new bootstrap.Modal(deleteModalEl);
    modal.show();
  });

  deleteModalEl?.querySelector("#confirmDeleteNote")?.addEventListener("click", async () => {
    if (!noteToDelete) return;
    try {
      const resp = await fetch(`/notes/${noteToDelete}/delete`, { method: "DELETE" });
      const result = await resp.json();
      if (resp.ok) {
        document.querySelector(`#notesTable tbody tr[data-id='${noteToDelete}']`)?.remove();
        showNotification(result.message, "success");
        bootstrap.Modal.getInstance(deleteModalEl).hide();
      } else {
        showNotification(result.error, "danger");
      }
    } catch (err) {
      showNotification("Erreur serveur : " + err.message, "danger");
    }
  });


async function loadClasseFilterList() {
  try {
    const resp = await fetch("/notes/list_elements");
    const data = await resp.json();
    const classeFilterList = document.getElementById("classeFilterList");
    if (!classeFilterList) return;

    classeFilterList.innerHTML = '<option value="">Toutes les classes</option>';
    data.classes.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.nom;
      classeFilterList.appendChild(opt);
    });

    // 🔹 Filtrage dynamique
    classeFilterList.addEventListener("change", (e) => {
      const val = e.target.value;
      document.querySelectorAll("#notesTable tbody tr").forEach(tr => {
        tr.style.display = (!val || tr.dataset.classe === val) ? "" : "none";
      });
    });

    // 🔹 Appliquer le filtre initial si une valeur est déjà sélectionnée
    const initialVal = classeFilterList.value;
    if (initialVal) {
      document.querySelectorAll("#notesTable tbody tr").forEach(tr => {
        tr.style.display = (tr.dataset.classe === initialVal) ? "" : "none";
      });
    }

  } catch (err) {
    console.error("Erreur chargement classes pour filtre :", err);
  }
}


// Appel au chargement de la page
loadClasseFilterList();

  // ===============================
  // Clôtures
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



// ===============================
// Exportation des notes
// ===============================

// async function openNotesExportModal() {
//     try {
//         // Charger les filtres disponibles
//         const resp = await fetch('/notes/export/filters');
//         const filters = await resp.json();
        
//         // Remplir les selects
//         const classeSelect = document.getElementById('export_notes_classe');
//         const matiereSelect = document.getElementById('export_notes_matiere');
//         const anneeSelect = document.getElementById('export_notes_annee');
        
//         if (!classeSelect || !matiereSelect || !anneeSelect) {
//             console.error('Éléments du modal d\'export non trouvés');
//             return;
//         }
        
//         // Classes
//         classeSelect.innerHTML = '<option value="">Toutes les classes</option>';
//         filters.classes.forEach(c => {
//             const option = document.createElement('option');
//             option.value = c.id;
//             option.textContent = c.nom;
//             classeSelect.appendChild(option);
//         });
        
//         // Matières
//         matiereSelect.innerHTML = '<option value="">Toutes les matières</option>';
//         filters.matieres.forEach(m => {
//             const option = document.createElement('option');
//             option.value = m.id;
//             option.textContent = m.libelle;
//             matiereSelect.appendChild(option);
//         });
        
//         // Années scolaires
//         anneeSelect.innerHTML = '<option value="">Toutes les années</option>';
//         filters.annees_scolaires.forEach(a => {
//             const option = document.createElement('option');
//             option.value = a;
//             option.textContent = a;
//             anneeSelect.appendChild(option);
//         });
        
//         // Afficher le modal
//         const modalElement = document.getElementById('notesExportModal');
//         if (modalElement) {
//             const modal = new bootstrap.Modal(modalElement);
//             modal.show();
//         } else {
//             console.error('Modal notesExportModal non trouvé');
//         }
        
//     } catch (error) {
//         console.error('Erreur chargement filtres export:', error);
//         showNotification('Erreur lors du chargement des filtres', 'danger');
//     }
// }

// function exportNotes(format) {
//     const form = document.getElementById('notesExportForm');
//     if (!form) {
//         console.error('Formulaire d\'export non trouvé');
//         return;
//     }
    
//     const formData = new FormData(form);
//     const params = new URLSearchParams(formData);
    
//     // Construire l'URL d'export
//     let url = `/notes/export/${format}?${params.toString()}`;
    
//     // Ouvrir dans une nouvelle fenêtre pour le téléchargement
//     window.open(url, '_blank');
    
//     // Fermer le modal
//     const modalElement = document.getElementById('notesExportModal');
//     if (modalElement) {
//         const modal = bootstrap.Modal.getInstance(modalElement);
//         if (modal) {
//             modal.hide();
//         }
//     }
    
//     showNotification(`Export ${format.toUpperCase()} des notes en cours...`, 'info');
// }
});

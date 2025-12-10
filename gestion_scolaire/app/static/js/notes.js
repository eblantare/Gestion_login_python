// Vérification de la disponibilité de Bootstrap
function checkBootstrapDependencies() {
    if (typeof bootstrap === 'undefined') {
        console.warn('⚠️ Bootstrap non disponible - certaines fonctionnalités seront limitées');
        return false;
    }
    return true;
}

// Attendre que Bootstrap soit chargé
function waitForBootstrap(maxWait = 3000) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        
        function check() {
            if (checkBootstrapDependencies()) {
                resolve();
            } else if (Date.now() - startTime >= maxWait) {
                reject(new Error('Timeout attente de Bootstrap'));
            } else {
                setTimeout(check, 100);
            }
        }
        
        check();
    });
}

// ===============================
// FONCTIONS GLOBALES POUR LES BOUTONS
// ===============================

// Fonction utilitaire pour afficher un modal
function showModal(modalId) {
    console.log(`🔍 Recherche du modal: ${modalId}`);
    const modalElement = document.getElementById(modalId);
    
    if (!modalElement) {
        console.error(`❌ Modal ${modalId} non trouvé dans le DOM`);
        console.log('📋 Modals disponibles:', Array.from(document.querySelectorAll('.modal')).map(m => m.id));
        return;
    }
    
    console.log(`✅ Modal ${modalId} trouvé`);
    
    if (typeof bootstrap !== 'undefined') {
        try {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            console.log(`✅ Modal ${modalId} affiché avec Bootstrap`);
        } catch (err) {
            console.error(`❌ Erreur affichage modal ${modalId}:`, err);
            // Fallback manuel
            modalElement.style.display = 'block';
            modalElement.classList.add('show');
            modalElement.setAttribute('aria-hidden', 'false');
            document.body.classList.add('modal-open');
            
            // Ajouter le backdrop manuellement
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            document.body.appendChild(backdrop);
        }
    } else {
        // Fallback sans Bootstrap
        console.log('⚠️ Bootstrap non disponible, fallback manuel');
        modalElement.style.display = 'block';
        modalElement.classList.add('show');
        modalElement.setAttribute('aria-hidden', 'false');
        document.body.classList.add('modal-open');
        
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        document.body.appendChild(backdrop);
    }
}

// Fonction utilitaire pour fermer un modal
function hideModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;
    
    if (typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        } else {
            // Fallback si l'instance n'existe pas
            modalElement.style.display = 'none';
            modalElement.classList.remove('show');
            modalElement.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('modal-open');
            
            // Supprimer le backdrop
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        }
    } else {
        modalElement.style.display = 'none';
        modalElement.classList.remove('show');
        modalElement.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
        
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) backdrop.remove();
    }
}

// Fonction pour charger les détails d'une note
function loadNoteDetail(noteId) {
    console.log(`📖 Chargement détail note: ${noteId}`);
    const body = document.getElementById("noteDetailContent");
    if (!body) {
        console.error("❌ Élément noteDetailContent non trouvé");
        return;
    }
    
    body.innerHTML = "<p>Chargement...</p>";
    
    fetch(`/notes/${noteId}`)
        .then(resp => {
            if (!resp.ok) {
                throw new Error(`Erreur HTTP: ${resp.status}`);
            }
            return resp.json();
        })
        .then(note => {
            if (note.error) {
                body.innerHTML = `<p class="text-danger">${note.error}</p>`;
                return;
            }
            
            body.innerHTML = `
                <ul class="list-group">
                    <li class="list-group-item"><b>Élève:</b> ${note.eleve_nom || 'N/A'}</li>
                    <li class="list-group-item"><b>Matière:</b> ${note.matiere_nom || 'N/A'}</li>
                    <li class="list-group-item"><b>Enseignant:</b> ${note.enseignant_nom || ""} ${note.enseignant_prenoms || ""}</li>
                    <li class="list-group-item"><b>Notes:</b> ${note.note1 || "-"}, ${note.note2 || "-"}, ${note.note3 || "-"}, Comp: ${note.note_comp || "-"}</li>
                    <li class="list-group-item"><b>Coefficient:</b> ${note.coefficient || "-"}</li>
                    <li class="list-group-item"><b>Trimestre:</b> ${note.trimestre || "-"}</li>
                    <li class="list-group-item"><b>Année:</b> ${note.annee_scolaire || "-"}</li>
                    <li class="list-group-item"><b>État:</b> ${note.etat || "-"}</li>
                </ul>
            `;
            
            // Afficher le modal APRÈS avoir chargé les données
            showModal('detailNoteModal');
        })
        .catch(err => {
            console.error("❌ Erreur chargement détail note:", err);
            body.innerHTML = `<p class="text-danger">Erreur : ${err.message}</p>`;
        });
}

// Fonction pour charger les données d'une note pour modification
function loadNoteData(noteId) {
    console.log(`✏️ Chargement données note pour édition: ${noteId}`);
    const form = document.getElementById("editNoteForm");
    if (!form) {
        console.error("❌ Formulaire d'édition non trouvé");
        return;
    }
    
    fetch(`/notes/${noteId}`)
        .then(resp => {
            if (!resp.ok) {
                throw new Error(`Erreur HTTP: ${resp.status}`);
            }
            return resp.json();
        })
        .then(note => {
            if (note.error) {
                showNotification("Erreur: " + note.error, "danger");
                return;
            }
            
            // Remplir le formulaire
            form.note_id.value = note.id;
            form.note1.value = note.note1 || "";
            form.note2.value = note.note2 || "";
            form.note3.value = note.note3 || "";
            form.note_comp.value = note.note_comp || "";
            form.coefficient.value = note.coefficient || "";
            form.trimestre.value = note.trimestre || "";
            form.annee_scolaire.value = note.annee_scolaire || "";
            form.etat.value = note.etat || "Actif";
            
            // Mettre à jour la liste des enseignants avec ceux de l'école
            const enseignantSelect = form.enseignant_id;
            if (enseignantSelect && note.enseignants_ecole) {
                // Sauvegarder la valeur sélectionnée actuelle
                const currentValue = enseignantSelect.value;
                
                // Vider et remplir la liste des enseignants
                enseignantSelect.innerHTML = '<option value="">-- Sélectionnez un enseignant --</option>';
                
                note.enseignants_ecole.forEach(ens => {
                    const option = document.createElement("option");
                    option.value = ens.id;
                    option.textContent = ens.nom_complet;
                    enseignantSelect.appendChild(option);
                });
                
                // Restaurer la valeur sélectionnée si elle existe
                if (note.enseignant_id) {
                    enseignantSelect.value = note.enseignant_id;
                } else if (currentValue) {
                    enseignantSelect.value = currentValue;
                }
                
                console.log(`✅ ${note.enseignants_ecole.length} enseignants de l'école chargés`);
            } else if (note.enseignant_id) {
                // Fallback si pas de liste d'enseignants
                form.enseignant_id.value = note.enseignant_id;
            }
            
            // Valider les inputs après remplissage
            [form.note1, form.note2, form.note3, form.note_comp].forEach(inp => {
                if (inp) validateNoteInput(inp);
            });
            
            // Afficher le modal APRÈS avoir chargé les données
            showModal('updateNoteModal');
        })
        .catch(err => {
            console.error("❌ Erreur chargement données note:", err);
            showNotification("Erreur: " + err.message, "danger");
        });
}

// Fonction de confirmation de suppression
function confirmDelete(noteId, noteLabel) {
    console.log(`🗑️ Confirmation suppression: ${noteId} - ${noteLabel}`);
    const messageElement = document.getElementById("deleteConfirmMessage");
    const confirmBtn = document.getElementById("deleteConfirmYesBtn");
    
    if (!messageElement || !confirmBtn) {
        console.error("❌ Éléments du modal de confirmation non trouvés");
        return;
    }
    
    // Mettre à jour le message
    messageElement.textContent = `Voulez-vous vraiment supprimer la note de "${noteLabel}" ?`;
    
    // Configurer l'action de suppression
    confirmBtn.onclick = function() {
        deleteNote(noteId);
    };
    
    // Afficher le modal
    showModal('deleteConfirmModal');
}

// Fonction pour supprimer une note
function deleteNote(noteId) {
    console.log(`🗑️ Suppression note: ${noteId}`);
    fetch(`/notes/${noteId}/delete`, { 
        method: "DELETE" 
    })
    .then(resp => {
        if (!resp.ok) {
            throw new Error(`Erreur HTTP: ${resp.status}`);
        }
        return resp.json();
    })
    .then(result => {
        if (result.error) {
            showNotification("Erreur: " + result.error, "danger");
            return;
        }
        
        // Supprimer la ligne du tableau
        const row = document.querySelector(`tr[data-id="${noteId}"]`);
        if (row) row.remove();
        
        // Afficher notification
        showNotification(result.message || "Note supprimée avec succès", "success");
        
        // Fermer le modal
        hideModal('deleteConfirmModal');
    })
    .catch(err => {
        console.error("❌ Erreur suppression note:", err);
        showNotification("Erreur: " + err.message, "danger");
    });
}

// Fonction utilitaire pour afficher les notifications
function showNotification(message, type = "success", delay = 3000) {
    const notificationContainer = document.getElementById("notificationContainer");
    if (!notificationContainer) {
        console.warn("⚠️ Container de notification non trouvé");
        // Fallback: utiliser alert si pas de container
        if (type === 'danger' || type === 'warning') {
            alert(message);
        }
        return;
    }
    
    const div = document.createElement("div");
    div.className = `alert alert-${type} alert-dismissible fade show`;
    div.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    notificationContainer.appendChild(div);
    
    setTimeout(() => {
        if (div.parentNode) div.remove();
    }, delay);
}

// Fonction de validation des inputs de note
function validateNoteInput(input) {
    if (!input) return;
    
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

// ===============================
// FONCTIONS POUR RÉINITIALISER LES ÉCOUTEURS D'ÉVÉNEMENTS
// ===============================
function reinitializeEventListenersForRow(rowElement) {
    if (!rowElement) return;
    
    console.log('🔄 Réinitialisation des écouteurs pour la ligne:', rowElement.dataset.id);
    
    // Réattacher les écouteurs pour les boutons de cette ligne spécifique
    const detailBtn = rowElement.querySelector('.btn-detail-note');
    const editBtn = rowElement.querySelector('.btn-edit-note');
    const deleteBtn = rowElement.querySelector('.btn-delete-note');
    
    if (detailBtn) {
        detailBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const noteId = this.getAttribute('data-note-id');
            console.log('👁️ Détail note (réinitialisé):', noteId);
            loadNoteDetail(noteId);
        });
    }
    
    if (editBtn) {
        editBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const noteId = this.getAttribute('data-note-id');
            console.log('✏️ Édition note (réinitialisé):', noteId);
            loadNoteData(noteId);
        });
    }
    
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const noteId = this.getAttribute('data-note-id');
            const noteLabel = this.getAttribute('data-note-label');
            console.log('🗑️ Suppression note (réinitialisé):', noteId, noteLabel);
            confirmDelete(noteId, noteLabel);
        });
    }
    
    console.log('✅ Écouteurs réinitialisés pour la ligne:', {
        detail: !!detailBtn,
        edit: !!editBtn,
        delete: !!deleteBtn
    });
}

// ===============================
// RÉINITIALISATION DE TOUS LES ÉCOUTEURS AU CHARGEMENT
// ===============================
function reinitializeAllEventListeners() {
    console.log('🔄 Réinitialisation de tous les écouteurs d\'événements...');
    
    const allRows = document.querySelectorAll('#notesTable tbody tr');
    allRows.forEach(row => {
        reinitializeEventListenersForRow(row);
    });
    
    console.log(`✅ ${allRows.length} lignes réinitialisées`);
}

// ===============================
// GESTION DES ÉVÉNEMENTS POUR LES BOUTONS (CSP COMPATIBLE)
// ===============================
function initializeEventListeners() {
    console.log('🔗 Initialisation des écouteurs d\'événements...');
    
    // Détail note - délégation d'événements
    document.addEventListener('click', function(e) {
        const detailBtn = e.target.closest('.btn-detail-note');
        if (detailBtn) {
            e.preventDefault();
            e.stopPropagation();
            const noteId = detailBtn.getAttribute('data-note-id');
            console.log('👁️ Détail note:', noteId);
            loadNoteDetail(noteId);
        }
    });
    
    // Édition note - délégation d'événements
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.btn-edit-note');
        if (editBtn) {
            e.preventDefault();
            e.stopPropagation();
            const noteId = editBtn.getAttribute('data-note-id');
            console.log('✏️ Édition note:', noteId);
            loadNoteData(noteId);
        }
    });
    
    // Suppression note - délégation d'événements
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.btn-delete-note');
        if (deleteBtn) {
            e.preventDefault();
            e.stopPropagation();
            const noteId = deleteBtn.getAttribute('data-note-id');
            const noteLabel = deleteBtn.getAttribute('data-note-label');
            console.log('🗑️ Suppression note:', noteId, noteLabel);
            confirmDelete(noteId, noteLabel);
        }
    });
    
    // Gestion des fermetures de modals avec les boutons de fermeture
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-bs-dismiss="modal"]') || e.target.closest('[data-bs-dismiss="modal"]')) {
            const modal = e.target.closest('.modal');
            if (modal) {
                console.log(`❌ Fermeture modal: ${modal.id}`);
                hideModal(modal.id);
            }
        }
    });
}

// ===============================
// FONCTIONS SPÉCIFIQUES AUX NOTES
// ===============================

// Création noeud matière avec gestion améliorée + double-clic + états de sélection
function createMatiereNode(m, level = 0) {
    const li = document.createElement("li");
    
    const isParent = m.is_parent || (m.children && m.children.length > 0);
    const isTypeNode = level === 0;

    li.classList.add("matiere-item");
    li.dataset.id = m.id || "";
    li.dataset.isParent = isParent ? "true" : "false";
    li.dataset.level = level;

    const labelDiv = document.createElement("div");
    labelDiv.className = `matiere-label d-flex align-items-center ${isParent ? "parent-label" : ""} matiere-level-${level}`;
    
    if (isParent && isTypeNode) {
        // C'est un type de matière (parent) - afficher avec chevron
        labelDiv.innerHTML = `<span class="chevron me-2">▶</span><span class="fw-bold">${m.libelle}</span>`;
    } else if (isParent) {
        // C'est un parent intermédiaire
        labelDiv.innerHTML = `<span class="chevron me-2">▶</span><span>${m.libelle}</span>`;
    } else {
        // C'est une feuille (matière sélectionnable)
        labelDiv.innerHTML = `<span class="ms-3">${m.libelle}</span>`;
    }

    li.appendChild(labelDiv);

    if (isParent && m.children && m.children.length > 0) {
        const ul = document.createElement("ul");
        ul.className = "child-list list-group mt-1 d-none";
        
        // Trier les enfants par libellé
        const sortedChildren = m.children.sort((a, b) => a.libelle.localeCompare(b.libelle));
        
        sortedChildren.forEach(c => {
            const childNode = createMatiereNode(c, level + 1);
            ul.appendChild(childNode);
        });
        
        li.appendChild(ul);

        const chevron = li.querySelector(".chevron");
        if (chevron) {
            labelDiv.addEventListener("click", (e) => {
                ul.classList.toggle("d-none");
                chevron.classList.toggle("expanded");
                e.stopPropagation();
            });
        }
        
        labelDiv.style.cursor = "pointer";
    } else if (!isParent) {
        // Pour les feuilles (matières sans enfants), rendre cliquable pour sélection
        labelDiv.style.cursor = "pointer";
        
        // Gestion du double-clic pour désélectionner
        let clickTimer = null;
        
        labelDiv.addEventListener("click", (e) => {
            if (clickTimer) {
                // Double-clic détecté
                clearTimeout(clickTimer);
                clickTimer = null;
                
                // Désélectionner cette matière
                if (li.classList.contains("active") || li.classList.contains("saved-selection")) {
                    li.classList.remove("active", "saved-selection");
                    labelDiv.classList.remove("bg-primary", "bg-success", "text-white");
                    selectedMatiere = null;
                    
                    console.log('❌ Matière désélectionnée par double-clic:', {
                        id: m.id,
                        libelle: m.libelle
                    });
                    
                    updateNoteInputsVisibility();
                }
            } else {
                // Premier clic - attendre pour voir si c'est un double-clic
                clickTimer = setTimeout(() => {
                    // Simple clic - sélectionner normalement
                    
                    // Désélectionner toutes les autres matières
                    document.querySelectorAll("#matiereTree .matiere-item").forEach(item => {
                        item.classList.remove("active", "saved-selection", "bg-primary", "bg-success", "text-white");
                        const label = item.querySelector('.matiere-label');
                        if (label) {
                            label.classList.remove("bg-primary", "bg-success", "text-white");
                        }
                    });
                    
                    // Sélectionner cette matière
                    li.classList.add("active");
                    labelDiv.classList.add("bg-primary", "text-white");
                    
                    selectedMatiere = m.id;
                    
                    console.log('✅ Matière sélectionnée:', {
                        id: selectedMatiere,
                        libelle: m.libelle,
                        level: level
                    });
                    
                    updateNoteInputsVisibility();
                    
                    clickTimer = null;
                }, 300); // Délai pour détecter le double-clic (300ms)
            }
            e.stopPropagation();
        });
    }

    return li;
}

// Fonction pour créer les éléments élèves avec gestion des états
function createEleveItem(e) {
    const li = document.createElement("li");
    li.className = "list-group-item eleve-item";
    li.dataset.classe = e.classe_id || "";
    li.dataset.id = e.id;
    li.dataset.searchText = `${e.nom || ''} ${e.prenoms || ''}`.toLowerCase().trim();
    li.textContent = `${e.nom || ''} ${e.prenoms || ''}`.trim() || `Élève ${e.id}`;
    li.style.cursor = "pointer";
    
    // Gestion du double-clic pour désélectionner
    let clickTimer = null;
    
    li.addEventListener("click", () => {
        if (clickTimer) {
            // Double-clic détecté
            clearTimeout(clickTimer);
            clickTimer = null;
            
            // Désélectionner cet élève
            if (li.classList.contains("active") || li.classList.contains("saved-selection")) {
                li.classList.remove("active", "saved-selection", "bg-primary", "bg-success", "text-white");
                selectedEleve = null;
                
                console.log('❌ Élève désélectionné par double-clic:', {
                    id: e.id,
                    nom: e.nom,
                    prenoms: e.prenoms
                });
                
                updateNoteInputsVisibility();
            }
        } else {
            // Premier clic - attendre pour voir si c'est un double-clic
            clickTimer = setTimeout(() => {
                // Simple clic - sélectionner normalement
                
                // Désélectionner tous les autres élèves
                document.querySelectorAll("#eleveTree .eleve-item").forEach(item => {
                    item.classList.remove("active", "saved-selection", "bg-primary", "bg-success", "text-white");
                });
                
                // Sélectionner cet élève
                li.classList.add("active", "bg-primary", "text-white");
                selectedEleve = li.dataset.id;
                
                console.log('✅ Élève sélectionné:', {
                    id: selectedEleve,
                    nom: e.nom,
                    prenoms: e.prenoms
                });
                
                updateNoteInputsVisibility();
                
                clickTimer = null;
            }, 300); // Délai pour détecter le double-clic (300ms)
        }
    });
    
    return li;
}

// Fonction pour marquer un élève comme "gardé en sélection" après sauvegarde
function markEleveAsSavedSelection(eleveId) {
    // Retirer tous les styles de sélection sauvegardée
    document.querySelectorAll("#eleveTree .eleve-item").forEach(item => {
        item.classList.remove("saved-selection", "bg-success");
    });
    
    // Appliquer le style "saved-selection" à l'élève spécifique
    const eleveItem = document.querySelector(`#eleveTree .eleve-item[data-id="${eleveId}"]`);
    if (eleveItem) {
        eleveItem.classList.add("saved-selection", "bg-success", "text-white");
        console.log('🎯 Élève marqué comme "gardé en sélection":', eleveId);
    }
}

// Fonction pour réinitialiser complètement la sélection
function resetAllSelections() {
    // Désélectionner tous les élèves
    document.querySelectorAll("#eleveTree .eleve-item").forEach(item => {
        item.classList.remove("active", "saved-selection", "bg-primary", "bg-success", "text-white");
    });
    
    // Désélectionner toutes les matières
    document.querySelectorAll("#matiereTree .matiere-item").forEach(item => {
        item.classList.remove("active", "saved-selection", "bg-primary", "bg-success", "text-white");
        const label = item.querySelector('.matiere-label');
        if (label) {
            label.classList.remove("bg-primary", "bg-success", "text-white");
        }
    });
    
    // 🔍 RÉINITIALISER LA RECHERCHE
    resetEleveSearch();
    
    // Réinitialiser les variables
    selectedEleve = null;
    selectedMatiere = null;
    
    updateNoteInputsVisibility();
    
    console.log('🗑️ Toutes les sélections réinitialisées');
}

// Fonction pour marquer une matière comme "gardée en sélection" après sauvegarde
function markMatiereAsSavedSelection(matiereId) {
    // Retirer tous les styles de sélection sauvegardée des matières
    document.querySelectorAll("#matiereTree .matiere-item").forEach(item => {
        item.classList.remove("saved-selection", "bg-success");
        const label = item.querySelector('.matiere-label');
        if (label) {
            label.classList.remove("bg-success", "text-white");
        }
    });
    
    // Appliquer le style "saved-selection" à la matière spécifique
    const matiereItem = document.querySelector(`#matiereTree .matiere-item[data-id="${matiereId}"]`);
    if (matiereItem) {
        matiereItem.classList.add("saved-selection");
        const label = matiereItem.querySelector('.matiere-label');
        if (label) {
            label.classList.add("bg-success", "text-white");
        }
        console.log('🎯 Matière marquée comme "gardée en sélection":', matiereId);
    }
}

// Charger élèves et matières - VERSION CORRIGÉE
async function loadElevesMatieres() {
    try {
        const addModalEl = document.getElementById("addNoteModal");
        if (!addModalEl) {
            console.error("❌ Modal d'ajout non trouvé");
            return;
        }

        const resp = await fetch("/notes/list_elements");
        if (!resp.ok) throw new Error(`HTTP error: ${resp.status}`);
        const data = await resp.json();

        console.log('🔍 Données reçues pour arbres:', data);

        // Classes
        const classeFilter = addModalEl.querySelector("#classeFilterModal");
        if (classeFilter) {
            classeFilter.innerHTML = '<option value="">Toutes les classes</option>';
            if (data.classes && data.classes.length > 0) {
                data.classes.forEach(c => {
                    const option = document.createElement('option');
                    option.value = c.id;
                    option.textContent = c.nom || `Classe ${c.id}`;
                    classeFilter.appendChild(option);
                });
                console.log(`✅ ${data.classes.length} classes chargées`);
            } else {
                console.warn('⚠️ Aucune classe disponible');
                const option = document.createElement('option');
                option.value = "";
                option.textContent = "Aucune classe disponible";
                classeFilter.appendChild(option);
            }
        }
        // Élèves avec la nouvelle fonction
// Élèves avec la nouvelle fonction
const eleveTree = addModalEl.querySelector("#eleveTree");
if (eleveTree) {
    eleveTree.innerHTML = "";
    
    if (data.eleves && data.eleves.length > 0) {
        // TRIER les élèves par nom
        const sortedEleves = data.eleves.sort((a, b) => {
            const nomA = (a.nom || '').toLowerCase();
            const nomB = (b.nom || '').toLowerCase();
            return nomA.localeCompare(nomB);
        });
        
        sortedEleves.forEach(e => {
            const eleveItem = createEleveItem(e);
            eleveTree.appendChild(eleveItem);
        });
        console.log(`✅ ${data.eleves.length} élèves chargés`);
        
    } else {
        console.warn('⚠️ Aucun élève disponible');
        const li = document.createElement("li");
        li.className = "list-group-item text-muted";
        li.textContent = "Aucun élève disponible";
        eleveTree.appendChild(li);
    }
    
    // 🔍 INITIALISER LA RECHERCHE APRÈS CHARGEMENT
    setTimeout(() => {
        initializeEleveSearch();
    }, 100);
}

        // Enseignants
        const enseignantSelect = addModalEl.querySelector("#enseignantSelect");
        if (enseignantSelect) {
            enseignantSelect.innerHTML = '<option value="">-- Sélectionnez un enseignant --</option>';
            
            if (data.enseignants && data.enseignants.length > 0) {
                // TRIER les enseignants par nom
                const sortedEnseignants = data.enseignants.sort((a, b) => {
                    const nomA = (a.noms || '').toLowerCase();
                    const nomB = (b.noms || '').toLowerCase();
                    return nomA.localeCompare(nomB);
                });
                
                sortedEnseignants.forEach(e => {
                    const opt = document.createElement("option");
                    opt.value = e.id;
                    const nomComplet = `${e.noms || ''} ${e.prenoms || ''}`.trim();
                    opt.textContent = nomComplet || `Enseignant ${e.id}`;
                    enseignantSelect.appendChild(opt);
                });
                console.log(`✅ ${data.enseignants.length} enseignants chargés`);
            } else {
                console.warn('⚠️ Aucun enseignant disponible');
                const opt = document.createElement("option");
                opt.value = "";
                opt.textContent = "Aucun enseignant disponible";
                enseignantSelect.appendChild(opt);
            }
        }

        // Matières - avec vérification des doublons côté client
        const matiereTree = addModalEl.querySelector("#matiereTree");
        if (matiereTree) {
            matiereTree.innerHTML = "";
            
            console.log('🌳 Structure des matières reçue:', data.matieres);
            
            if (data.matieres && data.matieres.length > 0) {
                // Vérification finale des doublons côté client
                const groupesUniques = [];
                const groupesDejaVus = new Set();
                
                data.matieres.forEach((typeGroupe, index) => {
                    const cleGroupe = `${typeGroupe.libelle}_${typeGroupe.id}`;
                    if (!groupesDejaVus.has(cleGroupe)) {
                        groupesDejaVus.add(cleGroupe);
                        
                        // Vérifier et dédoublonner les enfants
                        if (typeGroupe.children && typeGroupe.children.length > 0) {
                            const enfantsUniques = [];
                            const enfantsDejaVus = new Set();
                            
                            typeGroupe.children.forEach(enfant => {
                                const cleEnfant = `${enfant.libelle}_${enfant.id}`;
                                if (!enfantsDejaVus.has(cleEnfant)) {
                                    enfantsDejaVus.add(cleEnfant);
                                    enfantsUniques.push(enfant);
                                }
                            });
                            
                            // Remplacer les enfants par la liste dédoublonnée
                            typeGroupe.children = enfantsUniques;
                        }
                        
                        groupesUniques.push(typeGroupe);
                    }
                });
                
                groupesUniques.forEach((typeGroupe, index) => {
                    console.log(`📂 Groupe ${index + 1}:`, {
                        type: typeGroupe.libelle,
                        enfants: typeGroupe.children ? typeGroupe.children.length : 0
                    });
                    
                    if (typeGroupe.children && typeGroupe.children.length > 0) {
                        const typeNode = createMatiereNode(typeGroupe);
                        matiereTree.appendChild(typeNode);
                    } else {
                        console.warn(`⚠️ Groupe ${typeGroupe.libelle} n'a pas d'enfants`);
                        const emptyLi = document.createElement("li");
                        emptyLi.className = "list-group-item text-muted";
                        emptyLi.textContent = `${typeGroupe.libelle} (aucune matière)`;
                        matiereTree.appendChild(emptyLi);
                    }
                });
                
                console.log(`✅ ${groupesUniques.length} groupes de matières chargés`);
            } else {
                console.warn('⚠️ Aucune matière reçue');
                matiereTree.innerHTML = '<li class="list-group-item text-muted">Aucune matière disponible</li>';
            }
        }

        // Réinitialiser les sélections
        selectedEleve = null;
        selectedMatiere = null;
        updateNoteInputsVisibility();

    } catch (err) {
        console.error("❌ Erreur chargement éléments:", err);
        showNotification("Erreur chargement des données: " + err.message, "danger");
    }
}

// Variables globales pour la sélection
let selectedEleve = null;
let selectedMatiere = null;

// Mise à jour de la visibilité des inputs de notes
function updateNoteInputsVisibility() {
    const addModalEl = document.getElementById("addNoteModal");
    if (!addModalEl) return;
    
    const noteInputsContainer = addModalEl.querySelector("#noteInputsContainer");
    if (noteInputsContainer) {
        const shouldShow = !!(selectedEleve && selectedMatiere);
        noteInputsContainer.classList.toggle("d-none", !shouldShow);
        
        console.log('👀 Visibilité inputs notes:', {
            shouldShow: shouldShow,
            eleve: selectedEleve,
            matiere: selectedMatiere
        });
        
        if (shouldShow) {
            // Vérifier si c'est une sélection sauvegardée
            const savedEleve = document.querySelector("#eleveTree .eleve-item.saved-selection");
            const savedMatiere = document.querySelector("#matiereTree .matiere-item.saved-selection");
            
            if (savedEleve && savedMatiere) {
                showNotification("Prêt pour nouvelle saisie! L'élève et la matière sont maintenus.", "success", 3000);
            } else {
                showNotification("Sélection complète! Vous pouvez maintenant saisir les notes.", "success", 2000);
            }
        } else {
            // Vérifier les différents états de sélection
            const savedEleve = document.querySelector("#eleveTree .eleve-item.saved-selection");
            const savedMatiere = document.querySelector("#matiereTree .matiere-item.saved-selection");
            
            if (savedEleve && !selectedMatiere) {
                showNotification("Élève prêt. Choisissez une matière pour continuer.", "info", 2000);
            } else if (savedMatiere && !selectedEleve) {
                showNotification("Matière prête. Choisissez un élève pour continuer.", "info", 2000);
            } else if (selectedEleve && !selectedMatiere) {
                showNotification("Élève sélectionné. Choisissez maintenant une matière.", "info", 2000);
            } else if (!selectedEleve && selectedMatiere) {
                showNotification("Matière sélectionnée. Choisissez maintenant un élève.", "info", 2000);
            }
        }
    }
}

// Initialisation des écouteurs pour les arbres
function initTreeListeners() {
    const addModalEl = document.getElementById("addNoteModal");
    if (!addModalEl) return;

    // Filtrer par classe
    const classeFilter = addModalEl.querySelector("#classeFilterModal");
    if (classeFilter) {
        classeFilter.addEventListener("change", e => {
            const val = e.target.value;
            document.querySelectorAll("#eleveTree .eleve-item").forEach(li => {
                li.style.display = (!val || li.dataset.classe === val) ? "" : "none";
            });
        });
    }
    
    // 🔍 INITIALISER LA RECHERCHE
    initializeEleveSearch();
}

// Générer années scolaires
async function loadAnneesActives() {
    const addModalEl = document.getElementById("addNoteModal");
    if (!addModalEl) return [];
    
    try {
        const resp = await fetch("/notes/annees/actives");
        if (!resp.ok) throw new Error(`HTTP error: ${resp.status}`);
        const annees = await resp.json();
        const anneeSelect = addModalEl.querySelector("#anneeScolaire");
        if (anneeSelect) {
            anneeSelect.innerHTML = '<option value="">-- Sélectionnez une année --</option>';
            annees.forEach(a => {
                const option = document.createElement("option");
                option.value = a;
                option.textContent = a;
                anneeSelect.appendChild(option);
            });
        }
        return annees;
    } catch (err) {
        console.error("Erreur chargement années actives:", err);
        showNotification("Erreur chargement des années scolaires", "danger");
        return [];
    }
}

// Affichage arbres élèves/matières
function checkShowTrees() {
    const addModalEl = document.getElementById("addNoteModal");
    if (!addModalEl) return;
    
    const trimestreSelect = addModalEl.querySelector("#trimestre");
    const anneeSelect = addModalEl.querySelector("#anneeScolaire");
    const treesContainer = addModalEl.querySelector("#treesContainer");
    
    if (trimestreSelect && anneeSelect && treesContainer) {
        if (trimestreSelect.value && anneeSelect.value) {
            treesContainer.classList.remove("d-none");
            loadElevesMatieres();
        } else {
            treesContainer.classList.add("d-none");
            const noteInputsContainer = addModalEl.querySelector("#noteInputsContainer");
            if (noteInputsContainer) noteInputsContainer.classList.add("d-none");
        }
    }
}

// ===============================
// INITIALISATION PRINCIPALE
// ===============================
function initializeNotes() {
    console.log('🎯 Début de l\'initialisation des notes...');
    
    const addModalEl = document.getElementById("addNoteModal");
    if (!addModalEl) {
        console.error("❌ Modal d'ajout non trouvé");
        return;
    }

    // Écouteurs pour trimestre et année
    const trimestreSelect = addModalEl.querySelector("#trimestre");
    const anneeSelect = addModalEl.querySelector("#anneeScolaire");
    
    if (trimestreSelect) trimestreSelect.addEventListener("change", checkShowTrees);
    if (anneeSelect) anneeSelect.addEventListener("change", checkShowTrees);
    
    // Écouteur pour l'ouverture du modal d'ajout
    addModalEl.addEventListener("show.bs.modal", async () => {
        await loadAnneesActives();
        checkShowTrees();
    });

    // Initialisation des écouteurs des arbres
    initTreeListeners();

    // ===============================
    // SAUVEGARDE NOTE - VERSION AVEC ÉLÈVE ET MATIÈRE GARDÉS EN SÉLECTION
    // ===============================
    const btnSaveNote = addModalEl.querySelector("#btnSaveNote");
    if (btnSaveNote) {
        btnSaveNote.addEventListener("click", async () => {
            const enseignantSelect = addModalEl.querySelector("#enseignantSelect");
            const chosenEnseignant = enseignantSelect ? enseignantSelect.value : null;

            const note1Input = addModalEl.querySelector("#note1");
            const note2Input = addModalEl.querySelector("#note2");
            const note3Input = addModalEl.querySelector("#note3");
            const noteCompInput = addModalEl.querySelector("#note_comp");
            const coefficientSelect = addModalEl.querySelector("#coefficient");

            const n1 = note1Input?.value ? parseFloat(note1Input.value.replace(",", ".")) : null;
            const n2 = note2Input?.value ? parseFloat(note2Input.value.replace(",", ".")) : null;
            const n3 = note3Input?.value ? parseFloat(note3Input.value.replace(",", ".")) : null;
            const nComp = noteCompInput?.value ? parseFloat(noteCompInput.value.replace(",", ".")) : null;

            const allNotes = [n1, n2, n3, nComp].filter(v => v !== null);
            if (allNotes.some(v => isNaN(v) || v < 0 || v > 20)) {
                showNotification("Veuillez saisir un nombre compris entre 0 et 20", "warning");
                return;
            }

            const data = {
                eleve_id: selectedEleve,
                matiere_id: selectedMatiere,
                enseignant_id: chosenEnseignant,
                trimestre: trimestreSelect?.value || "",
                annee_scolaire: anneeSelect?.value || "",
                note1: n1,
                note2: n2,
                note3: n3,
                note_comp: nComp,
                coefficient: coefficientSelect?.value || "",
                cycle_type: currentCycleType  // ← Ajouter cette ligne
            };

            console.log("Données envoyées:", data);

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
                
                if (!resp.ok) {
                    throw new Error(result.error || `Erreur serveur (${resp.status})`);
                }
                
                if (result.message) {
                    showNotification(result.message, "success");
                    const tbody = document.querySelector("#notesTable tbody");
                    if (tbody && result.note_html) {
                        const wrapper = document.createElement("tbody");
                        wrapper.innerHTML = result.note_html.trim();
                        const rowEl = wrapper.querySelector("tr");
                        if (rowEl) {
                            const existingRow = tbody.querySelector(`tr[data-id='${rowEl.dataset.id}']`);
                            if (existingRow) {
                                // Mise à jour d'une note existante
                                existingRow.outerHTML = rowEl.outerHTML;
                                
                                // CORRECTION : Réinitialiser les écouteurs pour la ligne mise à jour
                                const updatedRow = tbody.querySelector(`tr[data-id='${rowEl.dataset.id}']`);
                                reinitializeEventListenersForRow(updatedRow);
                            } else {
                                // Nouvelle note
                                tbody.insertAdjacentHTML("beforeend", rowEl.outerHTML);
                                
                                // CORRECTION : Réinitialiser les écouteurs pour la nouvelle ligne
                                const newRow = tbody.querySelector(`tr[data-id='${rowEl.dataset.id}']`);
                                reinitializeEventListenersForRow(newRow);
                            }
                        }
                    }

                    // CORRECTION : Garder l'élève ET la matière sélectionnés après sauvegarde
                    if (result.action === "created") {
                        // Réinitialiser seulement les inputs de notes
                        [note1Input, note2Input, note3Input, noteCompInput].forEach(inp => inp && (inp.value = ""));
                        
                        // CORRECTION IMPORTANTE : NE PAS réinitialiser selectedEleve et selectedMatiere
                        // Ils restent définis pour permettre de garder la sélection
                        
                        // Marquer l'élève et la matière comme "gardés en sélection"
                        markEleveAsSavedSelection(selectedEleve);
                        markMatiereAsSavedSelection(selectedMatiere);
                        
                        // Les inputs restent visibles puisque les deux sont toujours sélectionnés
                        updateNoteInputsVisibility();
                        
                        // Afficher un message indiquant que la sélection est maintenue
                        showNotification("Note enregistrée! L'élève et la matière restent sélectionnés pour de nouvelles saisies.", "info", 4000);
                    }
                } else {
                    showNotification(result.error || "Erreur inconnue", "danger");
                }
            } catch (err) {
                console.error("Erreur sauvegarde note:", err);
                showNotification("Erreur : " + err.message, "danger");
            }
        });
    }

    // ===============================
    // MODIFICATION NOTE - VERSION CORRIGÉE
    // ===============================
    const editModalEl = document.getElementById("updateNoteModal");
    if (editModalEl) {
        const editForm = editModalEl.querySelector("#editNoteForm");
        if (editForm) {
            editForm.addEventListener("submit", async (e) => {
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
                    
                    if (!resp.ok) throw new Error(`Erreur HTTP: ${resp.status}`);
                    
                    const result = await resp.json();
                    if (result.message) {
                        showNotification(result.message, "success");
                        const tbody = document.querySelector("#notesTable tbody");
                        if (tbody && result.note_html) {
                            const wrapper = document.createElement("tbody");
                            wrapper.innerHTML = result.note_html.trim();
                            const rowEl = wrapper.querySelector("tr");
                            if (rowEl) {
                                const existingRow = tbody.querySelector(`tr[data-id='${rowEl.dataset.id}']`);
                                if (existingRow) {
                                    // CORRECTION : Remplacer la ligne ET réinitialiser les écouteurs
                                    existingRow.outerHTML = rowEl.outerHTML;
                                    
                                    // Réinitialiser les écouteurs pour la nouvelle ligne
                                    const newRow = tbody.querySelector(`tr[data-id='${rowEl.dataset.id}']`);
                                    reinitializeEventListenersForRow(newRow);
                                    
                                    console.log('✅ Ligne mise à jour avec boutons:', {
                                        rowId: newRow.dataset.id,
                                        hasEditBtn: !!newRow.querySelector('.btn-edit-note'),
                                        hasDeleteBtn: !!newRow.querySelector('.btn-delete-note')
                                    });
                                }
                            }
                        }
                        // Fermer le modal
                        hideModal('updateNoteModal');
                    } else {
                        showNotification(result.error || "Erreur inconnue", "danger");
                    }
                } catch (err) {
                    console.error("Erreur modification note:", err);
                    showNotification("Erreur serveur : " + err.message, "danger");
                }
            });
        }
    }

    // ===============================
    // FILTRE PAR CLASSE
    // ===============================// ===============================
// FILTRE PAR CLASSE - VERSION CORRIGÉE
// ===============================
async function loadClasseFilterList() {
    try {
        const resp = await fetch("/notes/list_elements");
        if (!resp.ok) throw new Error(`HTTP error: ${resp.status}`);
        const data = await resp.json();
        const classeFilterList = document.getElementById("classeFilterList");
        if (!classeFilterList) return;

        // Sauvegarder la valeur actuellement sélectionnée
        const currentValue = classeFilterList.value;
        
        // Mettre à jour la liste sans déclencher le changement
        classeFilterList.innerHTML = '<option value="">Toutes les classes</option>';
        data.classes.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.nom;
            classeFilterList.appendChild(opt);
        });

        // Restaurer la valeur sélectionnée
        if (currentValue) {
            classeFilterList.value = currentValue;
        }

        // CORRECTION : Gestion améliorée du changement de filtre
        classeFilterList.addEventListener("change", (e) => {
            const val = e.target.value;
            console.log('🎯 Filtre classe changé:', val);
            
            // Afficher un indicateur de chargement
            const originalText = e.target.options[e.target.selectedIndex].text;
            e.target.disabled = true;
            
            // Appliquer le filtre visuel immédiatement
            document.querySelectorAll("#notesTable tbody tr").forEach(tr => {
                if (!val || tr.dataset.classe === val) {
                    tr.style.display = "";
                } else {
                    tr.style.display = "none";
                }
            });
            
            // Réactiver le select après un court délai
            setTimeout(() => {
                e.target.disabled = false;
            }, 100);
            
            // Soumettre le formulaire pour le filtrage serveur
            e.target.form.submit();
        });

        // Appliquer le filtre initial si une valeur est déjà sélectionnée
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

    console.log('✅ Module notes initialisé avec succès');
    initializeCycleSelection();
}
// Fonction pour gérer le filtrage par classe
function handleClasseFilter() {
    const classeFilterList = document.getElementById("classeFilterList");
    if (!classeFilterList) return;
    
    classeFilterList.addEventListener("change", function(e) {
        const selectedClass = e.target.value;
        const selectedText = e.target.options[e.target.selectedIndex].text;
        
        // Sauvegarder visuellement la sélection
        e.target.style.backgroundColor = '#e8f5e8';
        e.target.style.borderColor = '#28a745';
        
        // Le formulaire se soumet automatiquement via onchange
        // La valeur restera sélectionnée grâce à l'attribut "selected" côté serveur
    });
}

// 🔍 FONCTIONS DE RECHERCHE AUTOMATIQUE PAR MOT-CLÉ
// ===============================
// RECHERCHE SIMPLE DES ÉLÈVES - VERSION CORRIGÉE
// ===============================

function initializeEleveSearch() {
    const searchInput = document.getElementById('eleveSearchInput');
    if (!searchInput) {
        console.log('❌ Champ de recherche non trouvé');
        return;
    }
    
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase().trim();
        const eleveItems = document.querySelectorAll('#eleveTree .eleve-item');
        let visibleCount = 0;
        
        eleveItems.forEach(item => {
            const eleveText = item.textContent.toLowerCase();
            if (searchTerm === '' || eleveText.includes(searchTerm)) {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        console.log(`🔍 Recherche: "${searchTerm}" - ${visibleCount} élève(s) trouvé(s)`);
    });
    
    console.log('✅ Recherche élèves initialisée');
}

function resetEleveSearch() {
    const searchInput = document.getElementById('eleveSearchInput');
    if (searchInput) {
        searchInput.value = '';
        document.querySelectorAll('#eleveTree .eleve-item').forEach(item => {
            item.style.display = '';
        });
    }
}

// Fonction pour filtrer les élèves par recherche
function filterElevesBySearch(searchTerm) {
    const eleveTree = document.getElementById('eleveTree');
    if (!eleveTree) return;
    
    const eleveItems = eleveTree.querySelectorAll('.eleve-item');
    let visibleCount = 0;
    
    eleveItems.forEach(item => {
        const eleveText = item.textContent.toLowerCase();
        const isVisible = !searchTerm || eleveText.includes(searchTerm);
        
        item.style.display = isVisible ? '' : 'none';
        if (isVisible) visibleCount++;
    });
    
    // Afficher un message si aucun résultat
    const noResultsMsg = eleveTree.querySelector('.no-results-message');
    if (searchTerm && visibleCount === 0) {
        if (!noResultsMsg) {
            const message = document.createElement('li');
            message.className = 'list-group-item text-muted text-center no-results-message';
            message.textContent = `Aucun élève trouvé pour "${searchTerm}"`;
            eleveTree.appendChild(message);
        }
    } else if (noResultsMsg) {
        noResultsMsg.remove();
    }
    
    console.log(`🔍 Recherche: "${searchTerm}" - ${visibleCount} résultat(s)`);
}


// ===============================
// RECHERCHE SIMPLE ET SÉCURISÉE DES ÉLÈVES
// ===============================

function initializeSimpleEleveSearch() {
    const searchInput = document.getElementById('eleveSearchInput');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase().trim();
        const eleveItems = document.querySelectorAll('#eleveTree .eleve-item');
        
        eleveItems.forEach(item => {
            const eleveText = item.textContent.toLowerCase();
            if (eleveText.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    console.log('🔍 Recherche simple initialisée');
}

function resetSimpleEleveSearch() {
    const searchInput = document.getElementById('eleveSearchInput');
    if (searchInput) {
        searchInput.value = '';
        document.querySelectorAll('#eleveTree .eleve-item').forEach(item => {
            item.style.display = '';
        });
    }
}

// ===============================
// GESTION DES CYCLES (COLLÈGE/LYCÉE)
// ===============================

let currentCycleType = 'college'; // Valeur par défaut

function initializeCycleSelection() {
    const addModalEl = document.getElementById("addNoteModal");
    if (!addModalEl) return;

    const cycleRadios = addModalEl.querySelectorAll('input[name="cycle_type"]');
    const trimestreSelect = addModalEl.querySelector("#trimestre");
    const anneeSelect = addModalEl.querySelector("#anneeScolaire");
    const trimestreLabel = addModalEl.querySelector("#trimestreLabel");

    if (!cycleRadios.length || !trimestreSelect || !trimestreLabel) {
        console.log('⚠️ Éléments de cycle non trouvés');
        return;
    }

    // Écouteur pour les boutons radio
    cycleRadios.forEach(radio => {
        radio.addEventListener('change', function(e) {
            currentCycleType = this.value;
            console.log(`🎯 Cycle sélectionné: ${currentCycleType}`);
            
            // Mettre à jour le label et les options
            updateTrimestreOptions(currentCycleType);
            
            // Griser/dégriser les champs
            updateFieldStates();
        });
    });

    // Initialiser les options
    updateTrimestreOptions(currentCycleType);
    updateFieldStates();
}

function updateTrimestreOptions(cycleType) {
    const trimestreSelect = document.querySelector("#trimestre");
    const trimestreLabel = document.querySelector("#trimestreLabel");
    
    if (!trimestreSelect || !trimestreLabel) return;

    // Vider les options actuelles
    trimestreSelect.innerHTML = '';
    
    let options = [];
    let label = '';
    
    if (cycleType === 'lycee') {
        options = [1, 2];
        label = 'Semestre';
        trimestreSelect.innerHTML = '<option value="">Sélectionnez un semestre</option>';
    } else {
        options = [1, 2, 3];
        label = 'Trimestre';
        trimestreSelect.innerHTML = '<option value="">Sélectionnez un trimestre</option>';
    }
    
    // Ajouter les options
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = `${label} ${opt}`;
        trimestreSelect.appendChild(option);
    });
    
    // Mettre à jour le label
    trimestreLabel.textContent = label;
    
    console.log(`✅ Options mises à jour pour ${cycleType}: ${options.join(', ')}`);
}

function updateFieldStates() {
    const trimestreSelect = document.querySelector("#trimestre");
    const anneeSelect = document.querySelector("#anneeScolaire");
    
    if (!trimestreSelect || !anneeSelect) return;
    
    // Si un cycle est sélectionné, dégriser les champs
    if (currentCycleType) {
        trimestreSelect.disabled = false;
        anneeSelect.disabled = false;
        trimestreSelect.classList.remove('bg-light', 'text-muted');
        anneeSelect.classList.remove('bg-light', 'text-muted');
    } else {
        // Sinon, griser les champs
        trimestreSelect.disabled = true;
        anneeSelect.disabled = true;
        trimestreSelect.classList.add('bg-light', 'text-muted');
        anneeSelect.classList.add('bg-light', 'text-muted');
    }
    
    console.log(`🔄 États des champs - Cycle: ${currentCycleType}, Trimestre actif: ${!trimestreSelect.disabled}`);
}
// ===============================
// INITIALISATION AU CHARGEMENT DU DOM
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    console.log('🚀 DOM chargé - initialisation du module notes...');
    
    // DEBUG: Lister tous les modals disponibles
    console.log('📋 Modals disponibles au chargement:', Array.from(document.querySelectorAll('.modal')).map(m => m.id));
    
    // Initialiser les écouteurs d'événements IMMÉDIATEMENT
    initializeEventListeners();
    handleClasseFilter();
    
    // Réinitialiser tous les écouteurs pour les lignes existantes
    setTimeout(() => {
        reinitializeAllEventListeners();
    }, 100);
    
    // Initialisation avec gestion de la compatibilité
    waitForBootstrap().then(() => {
        console.log('✅ Bootstrap chargé - initialisation des notes');
        initializeNotes();
    }).catch(err => {
        console.warn('⚠️ Initialisation sans Bootstrap:', err);
        initializeNotes();
    });
});
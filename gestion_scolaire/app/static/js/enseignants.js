// enseignants.js - VERSION FINALE CORRIGÉE
// Gestion complète des enseignants avec interface moderne

// ===============================
// 🚀 INITIALISATION PRINCIPALE
// ===============================

document.addEventListener('DOMContentLoaded', function() {
    initializeEnseignantsPage();
});

function initializeEnseignantsPage() {
    cleanupDataTable();
    
    // CORRECTION : Réinitialiser les selects en premier
    forceResetMatiereSelects();
    
    // Initialiser les composants de base
    applyTableStyles();
    initTooltips();
    initFormValidation();
    initModalCleanup();
    initToolbarHandlers();
    
    // Initialiser le tableau
    var tableElement = document.getElementById('enseignantsTable');
    if (tableElement) {
        initializeEnseignantsTable();
        initTableClickHandlers();
    }
    
    // Charger les données après un délai
    setTimeout(function() {
        initializeForms();
        chargerSelects().then(function() {
            initializeSelects();
            // CORRECTION : Réinitialiser une seconde fois après le chargement
            setTimeout(initMatiereSelects, 300);
        });
    }, 500);
}

// ===============================
// GESTION BARRE D'OUTILS
// ===============================

function initToolbarHandlers() {
    // Recherche
    var searchInput = document.getElementById('searchInput');
    var searchBtn = document.getElementById('searchBtn');
    
    if (searchInput && searchBtn) {
        var performSearch = function() {
            var searchValue = searchInput.value;
            var filterValue = document.getElementById('filterSelect').value;
            var perPageValue = document.getElementById('perPageSelect').value;
            
            var url = window.location.pathname;
            url += '?search=' + encodeURIComponent(searchValue);
            url += '&filter=' + encodeURIComponent(filterValue);
            url += '&per_page=' + perPageValue;
            
            // Ajouter le paramètre école si présent dans l'URL
            var urlParams = new URLSearchParams(window.location.search);
            var ecoleParam = urlParams.get('ecole');
            if (ecoleParam) {
                url += '&ecole=' + encodeURIComponent(ecoleParam);
            }
            
            window.location.href = url;
        };
        
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
    
    // Filtre et pagination
    var filterSelect = document.getElementById('filterSelect');
    var perPageSelect = document.getElementById('perPageSelect');
    
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            var searchValue = document.getElementById('searchInput').value;
            var perPageValue = document.getElementById('perPageSelect').value;
            var filterValue = this.value;
            
            var url = window.location.pathname;
            url += '?search=' + encodeURIComponent(searchValue);
            url += '&filter=' + encodeURIComponent(filterValue);
            url += '&per_page=' + perPageValue;
            
            // Ajouter le paramètre école si présent dans l'URL
            var urlParams = new URLSearchParams(window.location.search);
            var ecoleParam = urlParams.get('ecole');
            if (ecoleParam) {
                url += '&ecole=' + encodeURIComponent(ecoleParam);
            }
            
            window.location.href = url;
        });
    }
    
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            var searchValue = document.getElementById('searchInput').value;
            var filterValue = document.getElementById('filterSelect').value;
            var perPageValue = this.value;
            
            var url = window.location.pathname;
            url += '?search=' + encodeURIComponent(searchValue);
            url += '&filter=' + encodeURIComponent(filterValue);
            url += '&per_page=' + perPageValue;
            
            // Ajouter le paramètre école si présent dans l'URL
            var urlParams = new URLSearchParams(window.location.search);
            var ecoleParam = urlParams.get('ecole');
            if (ecoleParam) {
                url += '&ecole=' + encodeURIComponent(ecoleParam);
            }
            
            window.location.href = url;
        });
    }
}

// ===============================
// 1️⃣ GESTION TABLEAU
// ===============================

function initializeEnseignantsTable() {
    var table = $('#enseignantsTable');
    if (!table.length) return;

    // Vérifier si le tableau est VIDE
    var tbody = table.find('tbody');
    var dataRows = tbody.find('tr:not(.no-data)');
    var isEmptyMessage = tbody.find('td.text-muted').length > 0;
    
    // CAS 1 : Tableau VIDE
    if (dataRows.length === 0 || isEmptyMessage) {
        handleEmptyTable();
        return;
    }
    
    // CAS 2 : Tableau avec données - Vérifier la structure
    var thead = table.find('thead tr');
    var firstDataRow = dataRows.first();
    
    var headerCols = thead.find('th').length;
    var bodyCols = firstDataRow.find('td').length;
    
    if (headerCols !== bodyCols) {
        showNotification("Erreur d'affichage: Structure du tableau incompatible", "warning");
        applyBasicTableStyles();
        return;
    }
    
    // CAS 3 : Tableau valide avec données
    initializeDataTableWithData();
}

function handleEmptyTable() {
    var table = document.getElementById('enseignantsTable');
    if (!table) return;
    
    // Appliquer un style spécial pour tableau vide
    table.classList.add('table', 'table-striped', 'table-hover', 'table-bordered', 'empty-table');
    
    // Ajouter un conteneur avec message et bouton d'action
    var tableContainer = table.closest('.table-responsive') || table.parentElement;
    if (tableContainer && !tableContainer.querySelector('.empty-table-container')) {
        var emptyContainer = document.createElement('div');
        emptyContainer.className = 'empty-table-container';
        emptyContainer.innerHTML = '<div class="empty-table-message">' +
            '<i class="bi bi-people display-4 text-muted mb-3 d-block"></i>' +
            '<h4 class="text-muted">Aucun enseignant trouvé</h4>' +
            '<p class="mb-4">Commencez par ajouter votre premier enseignant</p>' +
            '</div>' +
            '<button type="button" class="btn btn-primary btn-lg" data-bs-toggle="modal" data-bs-target="#addEnsModal">' +
            '<i class="bi bi-person-plus"></i> Ajouter le premier enseignant' +
            '</button>' +
            '<div class="mt-3">' +
            '<small class="text-muted">' +
            'Ou <a href="javascript:location.reload()" class="text-decoration-none">actualiser la page</a> pour vérifier les données' +
            '</small>' +
            '</div>';
        tableContainer.appendChild(emptyContainer);
    }
}

function initializeDataTableWithData() {
    var table = $('#enseignantsTable');
    
    // Nettoyer DataTable existant
    if ($.fn.DataTable.isDataTable('#enseignantsTable')) {
        try {
            table.DataTable().destroy(true);
        } catch (e) {
            console.warn('Erreur lors de la destruction DataTable:', e);
        }
    }
    
    try {
        var dataTable = table.DataTable({
            searching: false, // Désactiver la recherche interne de DataTable
            paging: false,    // Désactiver la pagination interne de DataTable
            info: false,      // Désactiver les infos de DataTable
            ordering: true,
            responsive: true,
            destroy: true,
            retrieve: true,
            language: {
                "emptyTable": "Aucun enseignant trouvé",
                "zeroRecords": "Aucun enseignant correspondant trouvé"
            },
            columnDefs: [
                { 
                    orderable: false, 
                    targets: [0, 7] // Photo et Actions
                },
                { 
                    searchable: false, 
                    targets: [0, 7] // Photo et Actions
                }
            ],
            autoWidth: false
        });
        
        window.enseignantsDataTable = dataTable;
        
    } catch (error) {
        console.error('Erreur DataTable:', error);
        applyBasicTableStyles();
    }
}

function cleanupDataTable() {
    var table = $('#enseignantsTable');
    if (table.length && $.fn.DataTable.isDataTable('#enseignantsTable')) {
        try {
            table.DataTable().destroy();
        } catch (error) {
            table.removeAttr('style').removeData();
        }
    }
}

// ===============================
// 2️⃣ GESTION DES INTERACTIONS - CORRIGÉE
// ===============================

function initTooltips() {
    // Réinitialiser tous les tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initTableClickHandlers() {
    // Supprimer les anciens écouteurs
    $(document).off('click', '.btn-view');
    $(document).off('click', '.btn-edit'); 
    $(document).off('click', '.btn-delete');
    
    // Ajouter les nouveaux écouteurs
    $(document).on('click', '.btn-view', function() {
        var id = $(this).data('id');
        showEnsDetail(id);
    });
    
    $(document).on('click', '.btn-edit', function() {
        var id = $(this).data('id');
        editEns(id);
    });
    
    $(document).on('click', '.btn-delete', function() {
        var id = $(this).data('id');
        deleteEns(id);
    });
}

// ===============================
// 3️⃣ FONCTIONS CRUD - CORRIGÉES
// ===============================

window.showEnsDetail = function(id) {
    return fetch('/enseignants/detail/' + id)
        .then(function(response) {
            if (!response.ok) throw new Error("Erreur récupération détail: " + response.status);
            return response.json();
        })
        .then(function(data) {
            var content = document.getElementById("detailEnsContent");
            if (!content) {
                console.error('Element detailEnsContent non trouvé');
                return;
            }

            var photoUrl = data.photo_filename ? 
                '/static/upload/' + data.photo_filename : '';

            content.innerHTML = '<dl class="row">' +
                '<dt class="col-sm-4">Nom :</dt><dd class="col-sm-8">' + (data.nom || '') + '</dd>' +
                '<dt class="col-sm-4">Prénoms :</dt><dd class="col-sm-8">' + (data.prenoms || '') + '</dd>' +
                '<dt class="col-sm-4">Matière(s) :</dt><dd class="col-sm-8">' + (data.matiere || 'Non assigné') + '</dd>' +
                '<dt class="col-sm-4">Email :</dt><dd class="col-sm-8">' + (data.email || '') + '</dd>' +
                '<dt class="col-sm-4">Téléphone :</dt><dd class="col-sm-8">' + (data.telephone || '') + '</dd>' +
                '<dt class="col-sm-4">Sexe :</dt><dd class="col-sm-8">' + (data.sexe || '') + '</dd>' +
                '<dt class="col-sm-4">Titre :</dt><dd class="col-sm-8">' + (data.titre || '') + '</dd>' +
                '<dt class="col-sm-4">Date prise fonction :</dt><dd class="col-sm-8">' + (data.date_fonction || '') + '</dd>' +
                '<dt class="col-sm-4">Photo :</dt><dd class="col-sm-8">' +
                    (photoUrl ? '<img src="' + photoUrl + '" class="img-thumbnail rounded" style="max-width:120px; height:auto;" alt="Photo" onerror="this.style.display=\'none\'">' : '—') +
                '</dd>' +
                '<dt class="col-sm-4">État :</dt><dd class="col-sm-8">' + (data.etat || '') + '</dd>' +
            '</dl>';

            var modal = new bootstrap.Modal(document.getElementById("detailEnsModal"));
            modal.show();
        })
        .catch(function(err) {
            console.error('Erreur détail:', err);
            showNotification("Impossible de récupérer les détails de l'enseignant: " + err.message, "danger");
        });
};

window.editEns = function(id) {
    fetch('/enseignants/detail/' + id)
        .then(function(response) {
            if (!response.ok) throw new Error('HTTP ' + response.status);
            return response.json();
        })
        .then(function(data) {
            // Remplir les champs du formulaire
            document.getElementById("editEns_id").value = data.id;
            document.getElementById("editEns_nom").value = data.nom || "";
            document.getElementById("editEns_prenoms").value = data.prenoms || "";
            document.getElementById("editEns_email").value = data.email || "";
            document.getElementById("editEns_telephone").value = data.telephone || "";
            document.getElementById("editEns_titre").value = data.titre || "";
            
            // CORRECTION CRITIQUE : Charger les matières sélectionnées
            if (data.matiere_id) {
                var matiereIds = data.matiere_id.split(',').filter(function(id) { 
                    return id.trim() !== ''; 
                });
                var matiereSelect = document.getElementById("edit_matiere_id");
                
                if (matiereSelect) {
                    console.log("🎯 Matières à sélectionner:", matiereIds);
                    
                    // Désélectionner toutes les options d'abord
                    Array.from(matiereSelect.options).forEach(function(option) {
                        option.selected = false;
                    });
                    
                    // Sélectionner les matières de l'enseignant
                    matiereIds.forEach(function(matiereId) {
                        var option = matiereSelect.querySelector('option[value="' + matiereId.trim() + '"]');
                        if (option) {
                            option.selected = true;
                            console.log("✅ Matière sélectionnée:", option.text);
                        } else {
                            console.warn("⚠️ Option non trouvée pour ID:", matiereId);
                        }
                    });
                    
                    // Mettre à jour l'affichage IMMÉDIATEMENT
                    var selectedOptions = Array.from(matiereSelect.selectedOptions);
                    var selectedText = selectedOptions.map(function(opt) { 
                        return opt.text; 
                    }).join(", ");
                    document.getElementById("edit_matiere_libelle").value = selectedText;
                    
                    console.log("📋 Affichage mis à jour:", selectedText);
                }
            }
            
            // Date de fonction
            if (data.date_fonction) {
                document.getElementById("editEns_date_fonction").value = data.date_fonction;
            }
            
            // Sexe
            if (data.sexe) {
                var sexeValue = data.sexe.toUpperCase();
                document.getElementById("edit_sexeM").checked = (sexeValue === "M");
                document.getElementById("edit_sexeF").checked = (sexeValue === "F");
            }
            
            // Photo
            var photoInput = document.getElementById("editEns_photo_filename");
            var photoPreview = document.getElementById("edit_photo_preview");
            
            if (data.photo_filename) {
                photoInput.value = data.photo_filename;
                photoPreview.src = '/static/upload/' + data.photo_filename;
                photoPreview.style.display = "inline-block";
            } else {
                photoInput.value = "";
                photoPreview.style.display = "none";
            }
            
            // Réinitialiser la validation
            document.getElementById("editEnsForm").classList.remove('was-validated');
            
            // Ouvrir le modal
            var modal = new bootstrap.Modal(document.getElementById("editEnsModal"));
            modal.show();
            
        })
        .catch(function(err) {
            console.error('Erreur chargement modification:', err);
            showNotification("Impossible de charger les données de l'enseignant: " + err.message, "danger");
        });
};

window.deleteEns = function(id) {
    return fetch('/enseignants/get/' + id)
        .then(function(response) {
            if (!response.ok) throw new Error("Erreur lecture enseignant: " + response.status);
            return response.json();
        })
        .then(function(data) {
            document.getElementById("deleteEns_id").value = id;
            document.getElementById("deleteEns_info").textContent = (data.nom || '') + ' ' + (data.prenoms || '');
            document.getElementById("deleteEns_submit").disabled = false;

            var modal = new bootstrap.Modal(document.getElementById("deleteEnsModal"));
            modal.show();
        })
        .catch(function(err) {
            console.error('Erreur suppression:', err);
            showNotification("Erreur: " + err.message, "danger");
        });
};

// ===============================
// 4️⃣ GESTION DES FORMULAIRES
// ===============================

function initFormValidation() {
    var forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

function initializeForms() {
    initAddEns();
    initEditEns();
    initDeleteEns();
}

function initAddEns() {
    var form = document.getElementById("addEnsForm");
    if (!form) return;

    var addModal = document.getElementById('addEnsModal');
    if (addModal) {
        addModal.addEventListener('show.bs.modal', function() {
            form.reset();
            form.classList.remove('was-validated');
            
            var matiereSelect = document.getElementById("matiere_id");
            if (matiereSelect) {
                Array.from(matiereSelect.options).forEach(function(option) {
                    option.selected = false;
                });
                document.getElementById("add_matiere_libelle").value = "";
            }
            
            // CORRECTION : Filtrer les utilisateurs par école sélectionnée
            filtrerUtilisateursParEcole();
        });
    }

    form.addEventListener("submit", function(e) {
        e.preventDefault();
        form.classList.add("was-validated");
        
        if (!form.checkValidity()) {
            e.stopPropagation();
            showNotification("Veuillez remplir tous les champs obligatoires", "warning");
            return;
        }

        var fd = new FormData(form);
        fetch("/enseignants/add", { 
            method: "POST", 
            body: fd 
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.error) {
                showNotification(data.error, "danger");
            } else {
                var modal = bootstrap.Modal.getInstance(document.getElementById("addEnsModal"));
                if (modal) modal.hide();
                showNotification(data.message || "Ajout réussi", "success");
                setTimeout(function() { location.reload(); }, 1000);
            }
        })
        .catch(function(err) {
            showNotification("Erreur réseau lors de l'ajout: " + err.message, "danger");
        });
    });
}

// CORRECTION : Filtrer les utilisateurs par école sélectionnée
function filtrerUtilisateursParEcole() {
    var selectUtilisateur = document.getElementById("utilisateur_id");
    if (!selectUtilisateur || !window.utilisateursMap) return;
    
    // Récupérer l'école sélectionnée
    var ecoleId = getCurrentEcoleId();
    
    // Vider le select
    selectUtilisateur.innerHTML = '<option value="">-- Sélectionnez un utilisateur --</option>';
    
    // Filtrer les utilisateurs par école
    Object.values(window.utilisateursMap).forEach(function(user) {
        if (!ecoleId || user.ecole_id === ecoleId) {
            var ecoleInfo = user.ecole_nom ? ' - ' + user.ecole_nom : ' - Sans école';
            var optionText = user.nom + ' ' + user.prenoms + ecoleInfo;
            
            var option = document.createElement('option');
            option.value = user.id;
            option.textContent = optionText;
            selectUtilisateur.appendChild(option);
        }
    });
    
    // Si aucun utilisateur trouvé pour cette école
    if (selectUtilisateur.options.length === 1) {
        selectUtilisateur.innerHTML = '<option value="">Aucun utilisateur disponible pour cette école</option>';
    }
}

function initEditEns() {
    var form = document.getElementById("editEnsForm");
    if (!form) return;

    form.addEventListener("submit", function(e) {
        e.preventDefault();
        form.classList.add("was-validated");
        
        if (!form.checkValidity()) {
            e.stopPropagation();
            showNotification("Veuillez remplir tous les champs obligatoires", "warning");
            return;
        }

        var id = document.getElementById("editEns_id").value;
        var formData = new FormData(form);

        // Gestion des matières multiples
        var matiereSelect = document.getElementById("edit_matiere_id");
        if (matiereSelect) {
            if (formData.has('matiere_id')) formData.delete('matiere_id');
            
            var selectedMatieres = Array.from(matiereSelect.selectedOptions);
            selectedMatieres.forEach(function(option) {
                formData.append('matiere_id', option.value);
            });
        }

        fetch('/enseignants/update/' + id, { 
            method: "POST", 
            body: formData 
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(result) {
            if (result.error) {
                showNotification(result.error, "danger");
            } else {
                var modal = bootstrap.Modal.getInstance(document.getElementById("editEnsModal"));
                if (modal) modal.hide();
                showNotification(result.message || "Modification réussie", "success");
                setTimeout(function() { location.reload(); }, 1500);
            }
        })
        .catch(function(err) {
            showNotification("Erreur serveur lors de la modification: " + err.message, "danger");
        });
    });
}

function initDeleteEns() {
    var form = document.getElementById("deleteEnsForm");
    var submitBtn = document.getElementById("deleteEns_submit");

    if (!form) return;
    
    form.addEventListener("submit", function(e) {
        e.preventDefault();
        submitBtn.disabled = true;

        var id = document.getElementById("deleteEns_id").value;
        fetch('/enseignants/delete/' + id, { 
            method: "POST", 
            headers: { "X-Requested-With": "XMLHttpRequest" } 
        })
        .then(function(response) {
            if (response.ok) {
                var modal = bootstrap.Modal.getInstance(document.getElementById("deleteEnsModal"));
                if (modal) modal.hide();
                showNotification("Enseignant supprimé avec succès", "success");
                setTimeout(function() { location.reload(); }, 1000);
            } else {
                throw new Error("Erreur suppression: " + response.status);
            }
        })
        .catch(function(err) {
            showNotification("Erreur lors de la suppression: " + err.message, "danger");
            submitBtn.disabled = false;
        });
    });
}

// ===============================
// 5️⃣ GESTION DES SELECTS
// ===============================
// ===============================
// 5️⃣ GESTION DES SELECTS - CORRIGÉ
// ===============================

async function chargerSelects() {
    try {
        initEmptySelects();
        
        // CORRECTION : Ajouter le paramètre école dans la requête
        var ecoleId = getCurrentEcoleId();
        var url = "/enseignants/options";
        if (ecoleId) {
            url += "?ecole=" + encodeURIComponent(ecoleId);
        }
        
        var res = await fetch(url);
        if (!res.ok) throw new Error('Erreur serveur: ' + res.status);
        
        var payload = await res.json();
        
        // CORRECTION : Vérification améliorée des matières
        if (payload.matieres && payload.matieres.length === 0) {
            console.warn("⚠️ Aucune matière disponible pour cette école");
            if (isSystemAdmin()) {
                showNotification("Veuillez sélectionner une école pour voir ses matières", "info", 3000);
            }
        } else if (payload.matieres) {
            console.log("✅ Matières chargées:", payload.matieres.length);
        }

        populateSelects(payload);

    } catch (err) {
        console.error("❌ Erreur chargement selects:", err);
        showNotification("Impossible de charger les données: " + err.message, "danger", 5000);
    }
}

function initEmptySelects() {
    var selUsers = document.getElementById("utilisateur_id");
    if (selUsers) {
        selUsers.innerHTML = '<option value="">Chargement des utilisateurs...</option>';
    }

    var selMat = document.getElementById("matiere_id");
    var editSelMat = document.getElementById("edit_matiere_id");
    
    if (selMat) selMat.innerHTML = '<option value="">Chargement des matières...</option>';
    if (editSelMat) editSelMat.innerHTML = '<option value="">Chargement des matières...</option>';
}

function populateSelects(payload) {
    if (!payload || typeof payload !== 'object') return;

    // Réinitialiser les maps
    window.utilisateursMap = {};
    window.matieresMap = {};

    // CORRECTION : Peuplement des utilisateurs (PARTIE MANQUANTE !)
    var selUsers = document.getElementById("utilisateur_id");
    if (selUsers && Array.isArray(payload.utilisateurs)) {
        selUsers.innerHTML = '<option value="">-- Sélectionnez un utilisateur --</option>';
        
        // CORRECTION : Filtrer les utilisateurs pour admin système avec école sélectionnée
        var ecoleId = getCurrentEcoleId();
        var usersToShow = payload.utilisateurs;
        
        if (isSystemAdmin() && ecoleId) {
            // Admin système avec école sélectionnée : seulement les utilisateurs de cette école
            usersToShow = payload.utilisateurs.filter(function(user) {
                return user.ecole_id === ecoleId;
            });
            console.log(`🔍 Admin système - Utilisateurs filtrés pour école ${ecoleId}: ${usersToShow.length}`);
        }
        
        usersToShow.forEach(function(u) {
            var ecoleInfo = u.ecole_nom ? ' - ' + u.ecole_nom : ' - Sans école';
            var optionText = u.nom + ' ' + u.prenoms + ecoleInfo;
            
            selUsers.innerHTML += '<option value="' + u.id + '">' + optionText + '</option>';
            window.utilisateursMap[u.id] = u;
        });
        
        if (usersToShow.length === 0) {
            selUsers.innerHTML = '<option value="">Aucun utilisateur disponible</option>';
        }
        
        console.log(`✅ ${usersToShow.length} utilisateurs chargés dans le select`);
    }

    // CORRECTION : Peuplement des matières
    var selMat = document.getElementById("matiere_id");
    var editSelMat = document.getElementById("edit_matiere_id");
    
    if (Array.isArray(payload.matieres)) {
        // Stocker les matières dans la map globale
        payload.matieres.forEach(function(m) {
            window.matieresMap[m.id] = m;
        });
        
        console.log(`📦 ${Object.keys(window.matieresMap).length} matières chargées dans la map`);
        
        // Utiliser la nouvelle fonction de remplissage
        populateMatiereSelects();
    } else {
        console.warn("⚠️ Aucune matière disponible dans la réponse");
    }

    attachAutoFillListeners();
}

function initializeSelects() {
    initMatiereSelects();
}

function initMatiereSelects() {
    console.log("🔄 Initialisation des selects de matières...");
    
    // CORRECTION : Réinitialiser complètement les écouteurs
    function initializeSelectWithRetry(selectId, displayId, retryCount = 0) {
        const select = document.getElementById(selectId);
        const display = document.getElementById(displayId);
        
        if (!select || !display) {
            if (retryCount < 5) {
                console.log(`⏳ Réessai ${retryCount + 1}/5 pour ${selectId}...`);
                setTimeout(() => initializeSelectWithRetry(selectId, displayId, retryCount + 1), 200);
            } else {
                console.warn(`❌ Éléments non trouvés après 5 tentatives: ${selectId}`);
            }
            return;
        }

        // CORRECTION : Supprimer les anciens écouteurs
        select.replaceWith(select.cloneNode(true));
        const freshSelect = document.getElementById(selectId);
        const freshDisplay = document.getElementById(displayId);

        function updateDisplay() {
            const selectedOptions = Array.from(freshSelect.selectedOptions);
            const selectedText = selectedOptions.map(opt => opt.text).join(", ");
            freshDisplay.value = selectedText;
            console.log(`📝 ${selectId} - Matières sélectionnées:`, selectedText);
        }

        // Événement change standard
        freshSelect.addEventListener('change', updateDisplay);

        // CORRECTION CRITIQUE : Gestion du clic pour sélection/désélection
        freshSelect.addEventListener('mousedown', function(e) {
            e.preventDefault();
            const option = e.target;
            if (option.tagName === 'OPTION') {
                // Basculer la sélection
                option.selected = !option.selected;
                // Déclencher l'événement change
                const changeEvent = new Event('change', { bubbles: true });
                this.dispatchEvent(changeEvent);
            }
        });

        // CORRECTION : Gestion du clavier
        freshSelect.addEventListener('keydown', function(e) {
            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                const focusedOption = this.options[this.selectedIndex];
                if (focusedOption) {
                    focusedOption.selected = !focusedOption.selected;
                    this.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });

        console.log(`✅ Select ${selectId} initialisé avec succès`);
    }

    // Initialiser les deux selects avec réessai
    initializeSelectWithRetry('matiere_id', 'add_matiere_libelle');
    initializeSelectWithRetry('edit_matiere_id', 'edit_matiere_libelle');
}

// CORRECTION : Réinitialisation forcée des selects
function forceResetMatiereSelects() {
    console.log("🔄 Réinitialisation forcée des selects de matières...");
    
    const editSelect = document.getElementById('edit_matiere_id');
    const addSelect = document.getElementById('matiere_id');
    
    if (editSelect) {
        editSelect.innerHTML = '';
        console.log("✅ Select d'édition vidé");
    }
    
    if (addSelect) {
        addSelect.innerHTML = '';
        console.log("✅ Select d'ajout vidé");
    }
    
    // Réinitialiser après un court délai
    setTimeout(() => {
        if (window.matieresMap && Object.keys(window.matieresMap).length > 0) {
            populateMatiereSelects();
        }
    }, 100);
}

function populateMatiereSelects() {
    console.log("📦 Remplissage des selects de matières...");
    
    const editSelect = document.getElementById('edit_matiere_id');
    const addSelect = document.getElementById('matiere_id');
    
    if (!editSelect || !addSelect) {
        console.warn("❌ Selects non trouvés pour le remplissage");
        return;
    }
    
    // Vider les selects
    editSelect.innerHTML = '<option value="">-- Sélectionnez une ou plusieurs matières --</option>';
    addSelect.innerHTML = '<option value="">-- Sélectionnez une ou plusieurs matières --</option>';
    
    // Remplir avec les matières disponibles
    if (window.matieresMap && Object.keys(window.matieresMap).length > 0) {
        Object.values(window.matieresMap).forEach(matiere => {
            const optionHtml = `<option value="${matiere.id}">${matiere.libelle}</option>`;
            editSelect.innerHTML += optionHtml;
            addSelect.innerHTML += optionHtml;
        });
        console.log(`✅ ${Object.keys(window.matieresMap).length} matières chargées dans les selects`);
    } else {
        console.warn("⚠️ Aucune matière disponible dans window.matieresMap");
    }
    
    // Réinitialiser les écouteurs d'événements
    setTimeout(initMatiereSelects, 50);
}

function attachAutoFillListeners() {
    var selUser = document.getElementById("utilisateur_id");
    if (selUser) {
        selUser.addEventListener("change", function () {
            var user = window.utilisateursMap ? window.utilisateursMap[this.value] : null;
            var fields = [
                ["add_nom","nom"],
                ["add_prenoms","prenoms"],
                ["add_sexe","sexe"],
                ["add_email","email"],
                ["add_telephone","telephone"],
                ["add_photo_filename","photo_filename"]
            ];
            
            fields.forEach(function(field) {
                var el = document.getElementById(field[0]);
                if (el) el.value = (user && user[field[1]]) ? user[field[1]] : "";
            });

            var photoPreview = document.getElementById("add_photo_preview");
            if (photoPreview) {
                if (user && user.photo_filename) {
                    photoPreview.src = "/static/upload/" + user.photo_filename;
                    photoPreview.style.display = "inline-block";
                } else {
                    photoPreview.style.display = "none";
                }
            }
        });
    }

    var selMat = document.getElementById("matiere_id");
    var addMatiereLibelle = document.getElementById("add_matiere_libelle");

    if (selMat && addMatiereLibelle) {
        var selectedMatieres = new Set();

        document.getElementById('addEnsModal').addEventListener('show.bs.modal', function() {
            selectedMatieres.clear();
            addMatiereLibelle.value = "";
        });

        selMat.addEventListener("click", function(e) {
            var option = e.target;
            if (option.tagName !== "OPTION") return;

            var value = option.value;
            if (selectedMatieres.has(value)) {
                selectedMatieres.delete(value);
                option.selected = false;
            } else {
                selectedMatieres.add(value);
                option.selected = true;
            }

            var selectedText = Array.from(selectedMatieres)
                .map(function(v) { 
                    var option = selMat.querySelector('option[value="' + v + '"]');
                    return option ? option.text : '';
                })
                .join(", ");

            addMatiereLibelle.value = selectedText;
            addMatiereLibelle.dispatchEvent(new Event('input'));
        });

        selMat.addEventListener("change", function() {
            var selectedOptions = Array.from(this.selectedOptions);
            var selectedText = selectedOptions.map(function(opt) { return opt.text; }).join(", ");
            addMatiereLibelle.value = selectedText;
        });
    }
}

// ===============================
// 6️⃣ FONCTIONS UTILITAIRES
// ===============================

function initModalCleanup() {
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            var backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(function(backdrop) {
                backdrop.remove();
            });
            document.body.classList.remove('modal-open');
            document.body.style.overflow = 'auto';
            document.body.style.paddingRight = '0';
        });
    });
}

function applyTableStyles() {
    var style = document.createElement('style');
    style.textContent = '#enseignantsTable { border-collapse: collapse; width: 100%; }' +
        '.btn-group-sm > .btn { padding: 0.2rem 0.3rem; margin: 0; border-radius: 0; }' +
        '.btn-group-sm > .btn:first-child { border-top-left-radius: 0.25rem; border-bottom-left-radius: 0.25rem; }' +
        '.btn-group-sm > .btn:last-child { border-top-right-radius: 0.25rem; border-bottom-right-radius: 0.25rem; }' +
        'body.modal-open { overflow: auto !important; padding-right: 0 !important; }' +
        '.modal-backdrop { z-index: 1040; }' +
        '.modal { z-index: 1050; }' +
        '#matiere_id, #edit_matiere_id { height: auto; min-height: 100px; }' +
        '#matiere_id option, #edit_matiere_id option { padding: 8px 12px; border-bottom: 1px solid #eee; }' +
        '#matiere_id option:hover, #edit_matiere_id option:hover { background-color: #f8f9fa; }' +
        '#matiere_id option:checked, #edit_matiere_id option:checked { background-color: #007bff; color: white; }' +
        '#add_matiere_libelle, #edit_matiere_libelle { background-color: #f8f9fa; min-height: 38px; padding: 8px 12px; border-radius: 0.375rem; border: 1px solid #ced4da; }' +
        '.toast-container { z-index: 1090; position: fixed; top: 20px; right: 20px; }' +
        '.toast { background-color: white; border: 1px solid rgba(0,0,0,.1); box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15); }' +
        '.toast-success { border-left: 4px solid #28a745; }' +
        '.toast-danger { border-left: 4px solid #dc3545; }' +
        '.toast-warning { border-left: 4px solid #ffc107; }' +
        '.toast-info { border-left: 4px solid #17a2b8; }' +
        '.empty-table { opacity: 0.7; }' +
        '.empty-table th { background-color: #f8f9fa !important; color: #6c757d !important; border-color: #dee2e6; }' +
        '.empty-table td.text-muted { font-style: italic; background-color: #f8f9fa; }' +
        '.empty-table-container { text-align: center; padding: 2rem; border: 2px dashed #dee2e6; border-radius: 0.5rem; background-color: #f8f9fa; margin-top: 1rem; }' +
        '.empty-table-message { font-size: 1.1rem; color: #6c757d; margin-bottom: 1.5rem; }' +
        '.toolbar-container { background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; border: 1px solid #dee2e6; }';
    document.head.appendChild(style);
}

function applyBasicTableStyles() {
    var table = document.getElementById('enseignantsTable');
    if (!table) return;
    
    table.classList.add('table', 'table-striped', 'table-hover', 'table-bordered');
}

function showNotification(message, type, delay) {
    if (!delay) delay = 5000;
    var toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    var toastId = 'toast-' + Date.now();
    var toastHtml = '<div id="' + toastId + '" class="toast toast-' + type + '" role="alert" aria-live="assertive" aria-atomic="true">' +
        '<div class="toast-header">' +
        '<i class="bi ' + getToastIcon(type) + ' me-2"></i>' +
        '<strong class="me-auto">' + getToastTitle(type) + '</strong>' +
        '<small>' + new Date().toLocaleTimeString() + '</small>' +
        '<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>' +
        '</div>' +
        '<div class="toast-body">' + message + '</div>' +
        '</div>';

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    var toastElement = document.getElementById(toastId);
    var toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: delay
    });
    
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
    
    return toast;
}

function getToastIcon(type) {
    var icons = {
        'success': 'bi-check-circle-fill text-success',
        'danger': 'bi-exclamation-triangle-fill text-danger',
        'warning': 'bi-exclamation-circle-fill text-warning',
        'info': 'bi-info-circle-fill text-info'
    };
    return icons[type] || 'bi-info-circle-fill';
}

function getToastTitle(type) {
    var titles = {
        'success': 'Succès',
        'danger': 'Erreur',
        'warning': 'Attention',
        'info': 'Information'
    };
    return titles[type] || 'Notification';
}

// ===============================
// 7️⃣ FONCTIONS UTILITAIRES SUPPLÉMENTAIRES
// ===============================

// CORRECTION : Fonction pour détecter si l'utilisateur est admin système
function isSystemAdmin() {
    // Cette information devrait être disponible dans le template
    // Pour l'instant, on vérifie dans l'URL ou on fait une supposition
    var userRoleElement = document.querySelector('[data-user-role]');
    if (userRoleElement) {
        return userRoleElement.getAttribute('data-user-role') === 'admin';
    }
    
    // Fallback : vérifier l'URL ou d'autres indicateurs
    return window.location.pathname.includes('admin') || document.body.classList.contains('system-admin');
}

// CORRECTION : Fonction utilitaire pour récupérer l'ID de l'école courante
function getCurrentEcoleId() {
    // Récupérer depuis l'URL
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('ecole');
}
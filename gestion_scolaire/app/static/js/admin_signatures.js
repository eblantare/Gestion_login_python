// admin_signatures.js - Version avec modal de confirmation Bootstrap

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

// Nouvelle fonction pour corriger automatiquement le chef d'établissement
async function corrigerChefAutomatiquement() {
    try {
        showNotification('Correction automatique du chef d\'établissement en cours...', 'info');
        
        const response = await fetch('/admin/ecoles/api/signatures/fix-chef', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showNotification('✅ ' + result.message, 'success');
            if (result.corrections) {
                console.log('Corrections appliquées:', result.corrections);
            }
            // Recharger la configuration pour voir les changements
            await chargerConfiguration();
        } else {
            showNotification('❌ ' + (result.error || 'Erreur lors de la correction'), 'error');
        }
    } catch (error) {
        console.error('Erreur correction automatique:', error);
        showNotification('❌ Erreur de connexion: ' + error.message, 'error');
    }
}
// Fonction pour remplir automatiquement le formulaire
function remplirAutomatiquement() {
    const data = window.configurationData;
    if (!data || !data.enseignants || data.enseignants.length === 0) {
        showNotification('Aucun enseignant disponible pour le remplissage automatique', 'warning');
        return;
    }
    
    // Prendre le premier enseignant comme suggestion
    const premierEnseignant = data.enseignants[0];
    document.getElementById('nom-chef').value = premierEnseignant.nom_complet;
    
    showNotification(`Suggestion: ${premierEnseignant.nom_complet}`, 'info');
}

// Afficher le statut du chef d'établissement
function afficherStatutChef(statut) {
    const alertElement = document.getElementById('chef-status-alert');
    const statusTitle = document.getElementById('chef-status-title');
    const statusMessage = document.getElementById('chef-status-message');
    
    if (statut === 'défini') {
        alertElement.className = 'alert alert-chef-status defined alert-dismissible fade show';
        statusTitle.textContent = '✅ Chef d\'établissement défini';
        statusMessage.textContent = 'Les informations du chef d\'établissement sont complètes.';
    } else {
        alertElement.className = 'alert alert-chef-status alert-warning alert-dismissible fade show';
        statusTitle.textContent = '⚠️ Chef d\'établissement non défini';
        statusMessage.textContent = 'Veuillez définir les informations du chef d\'établissement.';
    }
    
    alertElement.classList.remove('d-none');
}


// Charger la configuration au démarrage
document.addEventListener('DOMContentLoaded', function() {
    waitForBootstrap().then(() => {
        console.log('✅ Bootstrap chargé - initialisation des signatures');
        chargerConfiguration();
        initialiserFormulaires();
    }).catch(err => {
        console.warn('⚠️ Initialisation sans Bootstrap:', err);
        // Initialiser les fonctionnalités de base même sans Bootstrap
        chargerConfiguration();
        initialiserFormulaires();
    });
});

// Initialiser les nouveaux écouteurs d'événements
function initialiserFormulaires() {
    const formChef = document.getElementById('form-chef');
    if (formChef) {
        formChef.addEventListener('submit', gererSoumissionChef);
    }
    
    const btnFixChef = document.getElementById('btn-fix-chef');
    if (btnFixChef) {
        btnFixChef.addEventListener('click', corrigerChefAutomatiquement);
    }
    
    const btnAutoFill = document.getElementById('btn-auto-fill');
    if (btnAutoFill) {
        btnAutoFill.addEventListener('click', remplirAutomatiquement);
    }
}

// Charger la configuration actuelle
async function chargerConfiguration() {
    try {
        showLoading('classes-list');
        const response = await fetch('/admin/ecoles/api/signatures/data');
        const data = await response.json();
        
        if (response.ok && data.success) {
            afficherConfiguration(data);
        } else {
            afficherErreur('classes-list', data.error || 'Erreur de chargement des données');
        }
    } catch (error) {
        afficherErreur('classes-list', 'Erreur de chargement: ' + error.message);
    }
}

// Modifier la fonction afficherConfiguration pour inclure le statut
function afficherConfiguration(data) {
    window.configurationData = data;

    // Afficher le statut du chef
    if (data.statut_chef) {
        afficherStatutChef(data.statut_chef);
    }

    // Chef d'établissement
    if (data.ecole) {
        document.getElementById('civilite-chef').value = data.ecole.chef_etablissement_civilite || 'M.';
        document.getElementById('titre-chef').value = data.ecole.chef_etablissement_titre || "LE CHEF D'ÉTABLISSEMENT";
        
        const nomChefSelect = document.getElementById('nom-chef');
        nomChefSelect.innerHTML = '<option value="">-- Sélectionner un enseignant --</option>';
        
        if (data.enseignants && data.enseignants.length > 0) {
            data.enseignants.forEach(enseignant => {
                const option = document.createElement('option');
                option.value = enseignant.nom_complet;
                option.textContent = enseignant.nom_complet;
                
                if (enseignant.nom_complet === data.ecole.chef_etablissement_nom) {
                    option.selected = true;
                }
                
                nomChefSelect.appendChild(option);
            });
            
            // Option pour le chef actuel s'il n'est pas dans la liste
            if (data.ecole.chef_etablissement_nom && 
                data.ecole.chef_etablissement_nom !== "NON DÉFINI" &&
                !data.enseignants.find(e => e.nom_complet === data.ecole.chef_etablissement_nom)) {
                const option = document.createElement('option');
                option.value = data.ecole.chef_etablissement_nom;
                option.textContent = `${data.ecole.chef_etablissement_nom} (actuel)`;
                option.selected = true;
                nomChefSelect.appendChild(option);
            }
        }
    }

    // Classes en grille
    const classesList = document.getElementById('classes-list');
    
    if (!data.classes || data.classes.length === 0) {
        classesList.innerHTML = '<div class="alert alert-info">Aucune classe trouvée</div>';
        return;
    }

    let html = '<div class="classes-grid">';
    
    data.classes.forEach(classe => {
        const currentTitulaire = classe.titulaire ? classe.titulaire.nom_complet : 'Aucun titulaire';
        
        html += `
            <div class="class-item" data-classe-id="${classe.id}">
                <div class="class-header">
                    <strong class="fs-6">${classe.nom}</strong>
                    <div class="current-titulaire" data-classe-id="${classe.id}">
                        <strong>Actuel:</strong> ${currentTitulaire}
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-semibold">Nouveau titulaire:</label>
                    <select class="form-select form-select-sm enseignant-select" data-classe-id="${classe.id}">
                        <option value="">-- Aucun titulaire --</option>
                        ${data.enseignants.map(ens => 
                            `<option value="${ens.id}" ${classe.titulaire && classe.titulaire.id === ens.id ? 'selected' : ''}>
                                ${ens.nom_complet}
                            </option>`
                        ).join('')}
                    </select>
                </div>
                <div class="class-actions">
                    <button class="btn btn-primary btn-sm" onclick="changerTitulaire('${classe.id}')">
                        <i class="bi bi-check-lg me-1"></i>Appliquer
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="afficherDetails('${classe.id}')" 
                            data-bs-toggle="tooltip" title="Voir les détails de la classe">
                        <i class="bi bi-info-circle"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    classesList.innerHTML = html;
    
    // Réinitialiser les tooltips Bootstrap seulement si disponible
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Afficher les détails d'une classe dans une modal
function afficherDetails(classeId) {
    const data = window.configurationData;
    const classe = data.classes.find(c => c.id === classeId);
    
    if (!classe) {
        showNotification('Classe non trouvée', 'error');
        return;
    }

    // Trouver le titulaire actuel avec ses informations complètes
    const titulaireComplet = classe.titulaire ? 
        data.enseignants.find(ens => ens.id === classe.titulaire.id) : null;

    // Préparer le contenu de la modal
    let modalContent = `
        <div class="modal fade" id="detailsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-info-circle me-2"></i>Détails de la classe ${classe.nom}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6 class="border-bottom pb-2">Informations de la classe</h6>
                                <ul class="list-unstyled">
                                    <li><strong>Nom:</strong> ${classe.nom}</li>
                                    <li><strong>ID:</strong> ${classe.id}</li>
                                    <li><strong>Niveau:</strong> ${classe.niveau || 'Non spécifié'}</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6 class="border-bottom pb-2">Titulaire actuel</h6>
    `;

    if (titulaireComplet) {
        modalContent += `
                                <ul class="list-unstyled">
                                    <li><strong>Nom:</strong> ${titulaireComplet.nom_complet}</li>
                                    <li><strong>Matières enseignées:</strong></li>
                                    <li>
                                        <ul class="small">
                                            ${titulaireComplet.matieres && titulaireComplet.matieres.length > 0 ? 
                                                titulaireComplet.matieres.map(matiere => 
                                                    `<li>${matiere}</li>`
                                                ).join('') : 
                                                '<li>Aucune matière assignée</li>'
                                            }
                                        </ul>
                                    </li>
                                </ul>
        `;
    } else {
        modalContent += `
                                <div class="alert alert-warning">
                                    <i class="bi bi-exclamation-triangle"></i> Aucun titulaire assigné
                                </div>
        `;
    }

    modalContent += `
                            </div>
                        </div>
                        
                        <div class="mt-4">
                            <h6 class="border-bottom pb-2">Enseignants disponibles</h6>
                            <div class="table-responsive">
                                <table class="table table-sm table-striped">
                                    <thead>
                                        <tr>
                                            <th>Nom</th>
                                            <th>Matières</th>
                                            <th>Classes déjà assignées</th>
                                        </tr>
                                    </thead>
                                    <tbody>
    `;

    // Lister tous les enseignants avec leurs informations
    data.enseignants.forEach(enseignant => {
        const classesEnseignant = data.classes.filter(c => 
            c.titulaire && c.titulaire.id === enseignant.id
        ).map(c => c.nom);
        
        modalContent += `
                                        <tr>
                                            <td>${enseignant.nom_complet}</td>
                                            <td>
                                                <small>
                                                    ${enseignant.matieres && enseignant.matieres.length > 0 ? 
                                                        enseignant.matieres.join(', ') : 
                                                        'Aucune'
                                                    }
                                                </small>
                                            </td>
                                            <td>
                                                <small>
                                                    ${classesEnseignant.length > 0 ? 
                                                        classesEnseignant.join(', ') : 
                                                        'Aucune'
                                                    }
                                                </small>
                                            </td>
                                        </tr>
        `;
    });

    modalContent += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x-lg me-1"></i>Fermer
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Supprimer toute modal existante
    const existingModal = document.getElementById('detailsModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Ajouter la nouvelle modal au body
    document.body.insertAdjacentHTML('beforeend', modalContent);

    // Afficher la modal seulement si Bootstrap est disponible
    if (typeof bootstrap !== 'undefined') {
        const modal = new bootstrap.Modal(document.getElementById('detailsModal'));
        modal.show();

        // Nettoyer la modal après fermeture
        document.getElementById('detailsModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    } else {
        // Fallback simple si Bootstrap n'est pas disponible
        document.getElementById('detailsModal').style.display = 'block';
        document.getElementById('detailsModal').addEventListener('click', function(e) {
            if (e.target === this || e.target.closest('.btn-close') || e.target.closest('.btn-secondary')) {
                this.remove();
            }
        });
    }
}

// Gérer la soumission du formulaire chef
async function gererSoumissionChef(e) {
    e.preventDefault();
    
    const data = {
        nom: document.getElementById('nom-chef').value,
        titre: document.getElementById('titre-chef').value,
        civilite: document.getElementById('civilite-chef').value
    };
    
    try {
        const response = await fetch('/admin/ecoles/api/signatures/chef', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            afficherMessage('message-chef', result.message || 'Chef d\'établissement mis à jour avec succès', 'success');
        } else {
            afficherMessage('message-chef', 'Erreur: ' + (result.error || 'Erreur inconnue'), 'error');
        }
    } catch (error) {
        afficherMessage('message-chef', 'Erreur: ' + error.message, 'error');
    }
}

// NOUVELLE FONCTION: Afficher un modal de confirmation Bootstrap
function afficherModalConfirmation(config, callback) {
    const modalContent = `
        <div class="modal fade" id="confirmationModal" tabindex="-1" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-warning">
                        <h5 class="modal-title">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>Confirmation requise
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-3">
                            <i class="bi bi-question-circle text-warning" style="font-size: 3rem;"></i>
                        </div>
                        <h6 class="text-center mb-3">${config.message}</h6>
                        <div class="alert alert-info">
                            <div class="small">
                                <strong>Classe:</strong> ${config.classeNom}<br>
                                ${config.currentTitulaireNom ? `<strong>Ancien titulaire:</strong> ${config.currentTitulaireNom}<br>` : ''}
                                ${config.nouveauTitulaireNom ? `<strong>Nouveau titulaire:</strong> ${config.nouveauTitulaireNom}` : '<strong>Action:</strong> Supprimer le titulaire'}
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x-lg me-1"></i>Non, annuler
                        </button>
                        <button type="button" class="btn btn-warning" id="confirmActionBtn">
                            <i class="bi bi-check-lg me-1"></i>Oui, confirmer
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Supprimer toute modal de confirmation existante
    const existingModal = document.getElementById('confirmationModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Ajouter la nouvelle modal au body
    document.body.insertAdjacentHTML('beforeend', modalContent);

    const modalElement = document.getElementById('confirmationModal');
    const modal = new bootstrap.Modal(modalElement);
    
    // Gérer le clic sur le bouton de confirmation
    document.getElementById('confirmActionBtn').addEventListener('click', function() {
        modal.hide();
        callback(true);
    });

    // Gérer la fermeture de la modal (annulation)
    modalElement.addEventListener('hidden.bs.modal', function() {
        this.remove();
        callback(false);
    });

    // Afficher la modal
    modal.show();
}

// Changer le titulaire d'une classe - VERSION AVEC MODAL BOOTSTRAP
async function changerTitulaire(classeId) {
    const select = document.querySelector(`.enseignant-select[data-classe-id="${classeId}"]`);
    const utilisateurId = select.value;

    // Récupérer les données de la classe
    const classe = window.configurationData.classes.find(c => c.id === classeId);
    const currentTitulaireId = classe.titulaire ? classe.titulaire.id : null;
    const currentTitulaireNom = classe.titulaire ? classe.titulaire.nom_complet : null;
    
    // Trouver le nom du nouvel enseignant sélectionné
    const nouvelEnseignant = window.configurationData.enseignants.find(e => e.id === utilisateurId);
    const nouvelEnseignantNom = nouvelEnseignant ? nouvelEnseignant.nom_complet : null;

    // Déterminer le type d'action et préparer la configuration du modal
    let config = {
        classeNom: classe.nom,
        currentTitulaireNom: currentTitulaireNom,
        nouveauTitulaireNom: nouvelEnseignantNom
    };

    // Vérifications des cas particuliers
    if (!utilisateurId && !currentTitulaireId) {
        showNotification(`Aucun changement : la classe ${classe.nom} n'a pas de titulaire à supprimer`, 'warning');
        return;
    }
    else if (utilisateurId && currentTitulaireId === utilisateurId) {
        showNotification(`Aucun changement : ${nouvelEnseignantNom} est déjà le titulaire de ${classe.nom}`, 'info');
        return;
    }

    // Définir le message selon le type d'action
    if (!utilisateurId && currentTitulaireId) {
        // Supprimer le titulaire actuel
        config.message = `Voulez-vous vraiment supprimer le titulaire de cette classe ?`;
    }
    else if (utilisateurId && !currentTitulaireId) {
        // Ajouter un nouveau titulaire
        config.message = `Voulez-vous vraiment assigner un nouveau titulaire à cette classe ?`;
    }
    else if (utilisateurId && currentTitulaireId && currentTitulaireId !== utilisateurId) {
        // Remplacer le titulaire actuel
        config.message = `Voulez-vous vraiment remplacer le titulaire de cette classe ?`;
    }

    // Afficher le modal de confirmation
    afficherModalConfirmation(config, async (confirmed) => {
        if (!confirmed) {
            console.log('Modification annulée par l\'utilisateur');
            return;
        }

        await executerChangementTitulaire(classeId, utilisateurId, classe, currentTitulaireNom, nouvelEnseignantNom);
    });
}

// NOUVELLE FONCTION: Exécuter le changement de titulaire après confirmation
async function executerChangementTitulaire(classeId, utilisateurId, classe, currentTitulaireNom, nouvelEnseignantNom) {
    try {
        // Afficher un indicateur de chargement
        const button = document.querySelector(`.enseignant-select[data-classe-id="${classeId}"]`).closest('.class-item').querySelector('button');
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Application...';
        button.disabled = true;
        
        const response = await fetch('/admin/ecoles/api/signatures/titulaire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                classe_id: classeId,
                enseignant_id: utilisateurId || null
            })
        });
        
        const result = await response.json();
        
        // Restaurer le bouton
        button.innerHTML = originalText;
        button.disabled = false;
        
        if (response.ok && result.success) {
            let message;
            if (!utilisateurId) {
                message = `✅ Titulaire supprimé : ${currentTitulaireNom} n'est plus titulaire de ${classe.nom}`;
            } else if (!currentTitulaireNom) {
                message = `✅ Titulaire ajouté : ${nouvelEnseignantNom} est maintenant titulaire de ${classe.nom}`;
            } else {
                message = `✅ Titulaire modifié : ${nouvelEnseignantNom} remplace ${currentTitulaireNom} pour la classe ${classe.nom}`;
            }
            
            showNotification(message, 'success');
            // Recharger IMMÉDIATEMENT la configuration pour voir le changement
            await chargerConfiguration();
        } else {
            showNotification('❌ Erreur: ' + (result.error || 'Erreur inconnue'), 'error');
        }
    } catch (error) {
        console.error('Erreur fetch:', error);
        showNotification('❌ Erreur de connexion: ' + error.message, 'error');
        
        // Restaurer le bouton en cas d'erreur
        const button = document.querySelector(`.enseignant-select[data-classe-id="${classeId}"]`).closest('.class-item').querySelector('button');
        button.innerHTML = '<i class="bi bi-check-lg me-1"></i>Appliquer';
        button.disabled = false;
    }
}

// Fonctions utilitaires (adaptées pour Bootstrap)
function afficherMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    element.innerHTML = `<div class="alert ${alertClass} alert-dismissible fade show">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
}

function afficherErreur(elementId, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="alert alert-danger">${message}</div>`;
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p class="text-muted">Chargement en cours...</p>
            </div>
        `;
    }
}

// Fonction de notification Bootstrap avec fallback
function showNotification(message, type = 'info') {
    // Créer le conteneur de notifications s'il n'existe pas
    let notificationContainer = document.getElementById('notificationContainer');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notificationContainer';
        notificationContainer.className = 'position-fixed top-0 end-0 p-3';
        notificationContainer.style.zIndex = '9999';
        document.body.appendChild(notificationContainer);
    }
    
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    notificationContainer.appendChild(notification);
    
    // Auto-remove after 5 seconds seulement si Bootstrap est disponible
    if (typeof bootstrap !== 'undefined') {
        setTimeout(() => {
            if (notification.parentNode) {
                const bsAlert = new bootstrap.Alert(notification);
                bsAlert.close();
            }
        }, 5000);
    } else {
        // Fallback simple
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}
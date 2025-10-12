// admin_signatures.js - Version compatible Bootstrap

// Charger la configuration au démarrage
document.addEventListener('DOMContentLoaded', function() {
    chargerConfiguration();
    initialiserFormulaires();
});

// Initialiser les écouteurs d'événements
function initialiserFormulaires() {
    const formChef = document.getElementById('form-chef');
    if (formChef) {
        formChef.addEventListener('submit', gererSoumissionChef);
    }
}

// Charger la configuration actuelle
async function chargerConfiguration() {
    try {
        showLoading('classes-list');
        const response = await fetch('/admin/signatures');
        const data = await response.json();
        
        if (response.ok) {
            afficherConfiguration(data);
        } else {
            afficherErreur('classes-list', data.error);
        }
    } catch (error) {
        afficherErreur('classes-list', 'Erreur de chargement: ' + error.message);
    }
}

// Afficher la configuration
function afficherConfiguration(data) {
    // Stocker les données globalement pour les utiliser dans les détails
    window.configurationData = data;

    // Chef d'établissement
    if (data.ecole) {
        document.getElementById('civilite-chef').value = data.ecole.chef_etablissement_civilite || 'M.';
        document.getElementById('nom-chef').value = data.ecole.chef_etablissement_nom || '';
        document.getElementById('titre-chef').value = data.ecole.chef_etablissement_titre || "LE CHEF D'ÉTABLISSEMENT";
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
            <div class="class-item">
                <div class="class-header">
                    <strong class="fs-6">${classe.nom}</strong>
                    <div class="current-titulaire">
                        <strong>Actuel:</strong> ${currentTitulaire}
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-semibold">Nouveau titulaire:</label>
                    <select class="form-select form-select-sm enseignant-select" data-classe-id="${classe.id}">
                        <option value="">-- Aucun titulaire --</option>
                        ${data.enseignants.map(ens => 
                            `<option value="${ens.id}">
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
    
    // Réinitialiser les tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
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

    // Afficher la modal
    const modal = new bootstrap.Modal(document.getElementById('detailsModal'));
    modal.show();

    // Nettoyer la modal après fermeture
    document.getElementById('detailsModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
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
        const response = await fetch('/admin/signatures/chef', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            afficherMessage('message-chef', 'Chef d\'établissement mis à jour avec succès', 'success');
        } else {
            afficherMessage('message-chef', 'Erreur: ' + result.error, 'error');
        }
    } catch (error) {
        afficherMessage('message-chef', 'Erreur: ' + error.message, 'error');
    }
}

// Changer le titulaire d'une classe
async function changerTitulaire(classeId) {
    const select = document.querySelector(`.enseignant-select[data-classe-id="${classeId}"]`);
    const enseignantId = select.value;
    
    try {
        const response = await fetch('/admin/signatures/titulaire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                classe_id: classeId,
                enseignant_id: enseignantId || null
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Titulaire mis à jour avec succès', 'success');
            // Recharger la configuration
            chargerConfiguration();
        } else {
            showNotification('Erreur: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Erreur: ' + error.message, 'error');
    }
}

// Fonctions utilitaires (adaptées pour Bootstrap)
function afficherMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show">
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

// Fonction de notification Bootstrap
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
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            const bsAlert = new bootstrap.Alert(notification);
            bsAlert.close();
        }
    }, 5000);
}
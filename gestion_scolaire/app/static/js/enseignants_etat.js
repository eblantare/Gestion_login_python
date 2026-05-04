// static/js/enseignants_etat.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les écouteurs pour les changements d'état
    initEtatChangeListeners();
    
    // Initialiser le modal de confirmation
    initConfirmationModal();
});

// Variables globales pour stocker les données de confirmation
let pendingEtatChange = {
    enseignantId: null,
    action: null,
    selectElement: null,
    confirmationMessage: ''
};

function initEtatChangeListeners() {
    // Déléguer l'événement aux selects d'action
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('select-action') && e.target.value) {
            if (typeof window.changerEtatEnseignant !== 'function') {
                console.warn('La fonction changerEtatEnseignant n\'est pas définie');
                handleEtatChange(e.target);
            }
        }
    });
}

// Initialiser le modal de confirmation
function initConfirmationModal() {
    const modal = document.getElementById('confirmationEtatModal');
    if (!modal) {
        // Créer le modal s'il n'existe pas
        createConfirmationModal();
    }
    
    // Initialiser les boutons du modal
    const confirmBtn = document.getElementById('confirmEtatBtn');
    const cancelBtn = document.getElementById('cancelEtatBtn');
    
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (pendingEtatChange.enseignantId && pendingEtatChange.action) {
                updateEnseignantEtat(
                    pendingEtatChange.enseignantId,
                    pendingEtatChange.action,
                    pendingEtatChange.selectElement
                );
            }
            hideConfirmationModal();
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', hideConfirmationModal);
    }
}

// Créer le modal de confirmation s'il n'existe pas
function createConfirmationModal() {
    const modalHTML = `
    <div class="modal fade" id="confirmationEtatModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="bi bi-question-circle-fill text-warning me-2"></i>
                        Confirmation requise
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="d-flex align-items-center mb-3">
                        <div class="flex-shrink-0">
                            <i class="bi bi-exclamation-triangle-fill text-warning fs-3"></i>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <p id="confirmationEtatMessage" class="mb-0 fw-medium"></p>
                        </div>
                    </div>
                    <div class="alert alert-info small mb-0">
                        <i class="bi bi-info-circle me-2"></i>
                        Cette action modifiera définitivement l'état de l'enseignant.
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" id="cancelEtatBtn">
                        <i class="bi bi-x-circle me-1"></i>Annuler
                    </button>
                    <button type="button" class="btn btn-warning" id="confirmEtatBtn">
                        <i class="bi bi-check-circle me-1"></i>Confirmer
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Initialiser le modal Bootstrap
    const modalElement = document.getElementById('confirmationEtatModal');
    window.confirmationEtatModal = new bootstrap.Modal(modalElement);
}

// Afficher le modal de confirmation
function showConfirmationModal(message, enseignantId, action, selectElement) {
    // Stocker les données en attente
    pendingEtatChange = {
        enseignantId: enseignantId,
        action: action,
        selectElement: selectElement,
        confirmationMessage: message
    };
    
    // Mettre à jour le message du modal
    const messageElement = document.getElementById('confirmationEtatMessage');
    if (messageElement) {
        messageElement.textContent = message;
    }
    
    // Afficher le modal
    if (!window.confirmationEtatModal) {
        const modalElement = document.getElementById('confirmationEtatModal');
        window.confirmationEtatModal = new bootstrap.Modal(modalElement);
    }
    
    window.confirmationEtatModal.show();
}

// Masquer le modal de confirmation
function hideConfirmationModal() {
    if (window.confirmationEtatModal) {
        window.confirmationEtatModal.hide();
    }
    
    // Réinitialiser les données en attente
    pendingEtatChange = {
        enseignantId: null,
        action: null,
        selectElement: null,
        confirmationMessage: ''
    };
}

// Fonction principale pour changer l'état d'un enseignant
window.changerEtatEnseignant = function(selectElement) {
    const enseignantId = selectElement.getAttribute('data-enseignant-id');
    const currentEtat = selectElement.getAttribute('data-current-etat');
    const action = selectElement.value;
    
    if (!action) return;
    
    // Réinitialiser le select
    selectElement.value = '';
    
    // Déterminer le message de confirmation
    let confirmationMessage = '';
    let actionDisplayText = '';
    
    switch(action) {
        case 'activer':
            confirmationMessage = `Voulez-vous vraiment activer cet enseignant ?`;
            actionDisplayText = 'Activer';
            break;
        case 'muter':
            confirmationMessage = `Voulez-vous vraiment muter cet enseignant ?`;
            actionDisplayText = 'Muter';
            break;
        case 'retraiter':
            confirmationMessage = `Voulez-vous vraiment mettre cet enseignant en retraite ?`;
            actionDisplayText = 'Mettre en retraite';
            break;
        case 'reinitialiser':
            confirmationMessage = `Voulez-vous vraiment réinitialiser l'état de cet enseignant à "Inactif" ?`;
            actionDisplayText = 'Réinitialiser';
            break;
        default:
            return;
    }
    
    // Personnaliser le message selon l'action
    const fullMessage = `${confirmationMessage}\n\nÉtat actuel: ${currentEtat}\nNouvel état: ${getNextEtat(currentEtat, action)}`;
    
    // Afficher le modal de confirmation
    showConfirmationModal(fullMessage, enseignantId, action, selectElement);
};

// Fonction pour déterminer le prochain état
function getNextEtat(currentEtat, action) {
    const transitions = {
        'inactif': { 'activer': 'Actif', 'reinitialiser': 'Inactif' },
        'actif': { 'muter': 'Muté', 'reinitialiser': 'Inactif' },
        'muté': { 'retraiter': 'Retraité', 'reinitialiser': 'Inactif' },
        'retraité': { 'reinitialiser': 'Inactif' }
    };
    
    const current = currentEtat.toLowerCase();
    const next = transitions[current]?.[action] || currentEtat;
    return next;
}

// Fonction pour mettre à jour l'état d'un enseignant
function updateEnseignantEtat(enseignantId, action, selectElement) {
    const url = `/enseignants/${enseignantId}/changer_etat`;
    
    // Afficher un indicateur de chargement sur le select
    const originalHtml = selectElement.innerHTML;
    selectElement.disabled = true;
    selectElement.innerHTML = '<span class="spinner-border spinner-border-sm" style="width: 1rem; height: 1rem;"></span>';
    
    // Désactiver tous les autres selects pendant la requête
    disableAllEtatSelects(true);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ action: action })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Mise à jour réussie
        showSuccessNotification(`État mis à jour avec succès: ${data.etat}`);
        
        // Mettre à jour le badge visuellement (optionnel)
        updateEtatBadge(selectElement, data.etat);
        
        // Recharger la page après un délai pour voir les changements
        setTimeout(() => {
            location.reload();
        }, 2000);
        
    })
    .catch(error => {
        console.error('Erreur mise à jour état:', error);
        
        // Réactiver le select
        selectElement.disabled = false;
        selectElement.innerHTML = originalHtml;
        
        // Réactiver tous les selects
        disableAllEtatSelects(false);
        
        // Afficher l'erreur
        showErrorNotification(`Erreur: ${error.message}`);
    });
}

// Mettre à jour visuellement le badge d'état (feedback immédiat)
function updateEtatBadge(selectElement, newEtat) {
    const badge = selectElement.parentElement.querySelector('.badge');
    if (badge) {
        // Animer le changement
        badge.classList.add('etat-changing');
        
        // Changer le texte et la couleur
        badge.textContent = newEtat;
        badge.className = 'badge ' + getEtatClass(newEtat) + ' etat-changing';
        
        // Supprimer l'animation après la fin
        setTimeout(() => {
            badge.classList.remove('etat-changing');
        }, 500);
    }
}

// Désactiver/réactiver tous les selects d'état
function disableAllEtatSelects(disable) {
    const allSelects = document.querySelectorAll('.select-action');
    allSelects.forEach(select => {
        if (disable) {
            select.disabled = true;
            select.classList.add('disabled');
        } else {
            select.disabled = false;
            select.classList.remove('disabled');
        }
    });
}

// Notification de succès stylisée
function showSuccessNotification(message) {
    showNotification(message, 'success', 'bi-check-circle-fill');
}

// Notification d'erreur stylisée
function showErrorNotification(message) {
    showNotification(message, 'danger', 'bi-exclamation-triangle-fill');
}

// Fonction de notification améliorée
function showNotification(message, type, iconClass = 'bi-info-circle') {
    // Vérifier si le conteneur de notifications existe
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // Créer l'ID unique pour le toast
    const toastId = 'toast-' + Date.now();
    
    // Déterminer la couleur et l'icône
    const colors = {
        'success': { bg: 'bg-success', text: 'text-white', icon: 'bi-check-circle-fill' },
        'danger': { bg: 'bg-danger', text: 'text-white', icon: 'bi-exclamation-triangle-fill' },
        'warning': { bg: 'bg-warning', text: 'text-dark', icon: 'bi-exclamation-circle-fill' },
        'info': { bg: 'bg-info', text: 'text-white', icon: 'bi-info-circle-fill' }
    };
    
    const colorConfig = colors[type] || colors.info;
    
    // Créer le HTML du toast
    const toastHTML = `
    <div id="${toastId}" class="toast align-items-center border-0 ${colorConfig.bg} ${colorConfig.text}" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
            <div class="toast-body d-flex align-items-center">
                <i class="bi ${iconClass} me-2 fs-5"></i>
                <span class="me-3">${message}</span>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    </div>
    `;
    
    // Ajouter le toast au conteneur
    container.insertAdjacentHTML('beforeend', toastHTML);
    
    // Initialiser et afficher le toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Nettoyer après la fermeture
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Fonction utilitaire pour récupérer le token CSRF
function getCsrfToken() {
    const tokenElement = document.querySelector('meta[name="csrf-token"]');
    if (tokenElement) {
        return tokenElement.getAttribute('content');
    }
    
    const cookieMatch = document.cookie.match(/csrf_token=([^;]+)/);
    if (cookieMatch) {
        return cookieMatch[1];
    }
    
    return '';
}

// Fonction de backup si l'API n'est pas disponible
function handleEtatChange(selectElement) {
    const enseignantId = selectElement.getAttribute('data-enseignant-id');
    const action = selectElement.value;
    
    // Réinitialiser le select
    selectElement.value = '';
    
    // Simuler la mise à jour
    const etatMap = {
        'activer': 'Actif',
        'muter': 'Muté',
        'retraiter': 'Retraité',
        'reinitialiser': 'Inactif'
    };
    
    const nouveauEtat = etatMap[action];
    
    if (nouveauEtat) {
        // Mettre à jour le badge immédiatement
        const badge = selectElement.parentElement.querySelector('.badge');
        if (badge) {
            badge.textContent = nouveauEtat;
            badge.className = 'badge ' + getEtatClass(nouveauEtat);
        }
        
        showSuccessNotification(`État mis à jour: ${nouveauEtat}`);
        console.log(`Mise à jour enseignant ${enseignantId}: ${action} → ${nouveauEtat}`);
    }
}

function getEtatClass(etat) {
    switch(etat) {
        case 'Actif': return 'bg-success';
        case 'Inactif': return 'bg-secondary';
        case 'Muté': return 'bg-warning text-dark';
        case 'Retraité': return 'bg-info';
        default: return 'bg-secondary';
    }
}

// CSS pour l'animation du changement d'état
function addEtatChangeStyles() {
    if (!document.getElementById('etat-change-styles')) {
        const style = document.createElement('style');
        style.id = 'etat-change-styles';
        style.textContent = `
            .etat-changing {
                animation: pulseEtat 0.5s ease-in-out;
            }
            
            @keyframes pulseEtat {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.1); opacity: 0.8; }
                100% { transform: scale(1); opacity: 1; }
            }
            
            .select-action.disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .toast {
                box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
                border-radius: 0.5rem;
            }
        `;
        document.head.appendChild(style);
    }
}


// Ajouter les styles au chargement
addEtatChangeStyles();
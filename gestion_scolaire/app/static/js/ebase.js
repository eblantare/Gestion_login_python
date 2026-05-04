// ebase.js - VERSION ORIGINALE COMPLÈTE
// ============================================

// Initialisation principale
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initialisation ebase.js...');
    
    // Initialisation des tooltips Bootstrap
    initializeTooltips();
    
    // Initialisation du sélecteur d'école
    initializeEcoleSelector();
    
    // Initialisation des interactions avec les cartes
    initializeCoursCards();
    
    // Debug après un délai
    setTimeout(debugEcoleSystem, 1000);
});

// ============================================
// FONCTIONS D'INITIALISATION
// ============================================

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    console.log(`🔧 ${tooltipList.length} tooltip(s) initialisé(s)`);
}

function initializeEcoleSelector() {
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (!ecoleSelect) {
        console.log('ℹ️ ecoleSelect non trouvé sur cette page');
        return;
    }
    
    const $ecoleSelect = $('#ecoleSelect');
    const userRole = ecoleSelect.dataset.userRole || '';
    const userEcoleId = ecoleSelect.dataset.userEcoleId || '';
    
    // Détection des droits
    const usernameElement = document.querySelector('.navbar .dropdown-toggle span');
    const username = usernameElement ? usernameElement.textContent.trim() : '';
    
    const isSystemAdmin = username === 'admin';
    const isEcoleAdmin = userRole.toLowerCase() === 'admin' && username !== 'admin';
    
    console.log('🔐 Détection des droits:', {
        username: username,
        userRole: userRole,
        isSystemAdmin: isSystemAdmin,
        isEcoleAdmin: isEcoleAdmin
    });
    
    // Configuration Select2
    const select2Config = {
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: isSystemAdmin ? "Sélectionnez une école" : "Votre école",
        language: 'fr'
    };
    
    // Seul l'admin système peut changer d'école
    if (isSystemAdmin) {
        select2Config.allowClear = true;
        ecoleSelect.disabled = false;
        console.log('✅ ADMIN SYSTÈME - Sélecteur ACTIVÉ');
    } else {
        select2Config.allowClear = false;
        ecoleSelect.disabled = true;
        console.log('🔒 UTILISATEUR - Sélecteur VERROUILLÉ');
    }
    
    // Initialiser Select2
    $ecoleSelect.select2(select2Config);
    
    // Gestion des événements UNIQUEMENT pour admin système
    if (isSystemAdmin) {
        $ecoleSelect.on('change', function() {
            const ecoleId = $(this).val();
            console.log('🔄 Changement d\'école sélectionnée:', ecoleId);
            changeEcole(ecoleId);
        });
    }
}

// ============================================
// GESTION DES CARTES DE COURS
// ============================================

function initializeCoursCards() {
    console.log('📋 Initialisation des interactions avec les cartes...');
    
    // Gestion des clics sur les cartes de cours
    document.addEventListener('click', function(e) {
        // Carte de cours
        const coursCard = e.target.closest('.cours-card');
        if (coursCard && !coursCard.classList.contains('cours-vide')) {
            e.preventDefault();
            e.stopPropagation();
            
            const serviceId = coursCard.getAttribute('data-service-id');
            if (serviceId) {
                console.log('🎯 Carte de cours cliquée, service ID:', serviceId);
                handleCoursCardClick(serviceId, coursCard);
            }
        }
        
        // Carte école
        const ecoleCard = e.target.closest('.ecole-card');
        if (ecoleCard) {
            e.preventDefault();
            e.stopPropagation();
            
            const ecoleUrl = ecoleCard.getAttribute('data-ecole-url');
            if (ecoleUrl) {
                console.log('🏫 Carte école cliquée, redirection vers:', ecoleUrl);
                window.location.href = ecoleUrl;
            }
        }
    });
}

function handleCoursCardClick(serviceId, coursCard) {
    // Utiliser la fonction globale si elle existe
    if (typeof window.showServiceDetails === 'function') {
        window.showServiceDetails(serviceId);
    } else {
        // Sinon, utiliser le fallback
        showServiceDetailsFallback(serviceId, coursCard);
    }
}

function showServiceDetailsFallback(serviceId, coursCard) {
    console.log('🔄 Fallback pour le service:', serviceId);
    
    // Extraire les informations de la carte
    const matiere = coursCard.querySelector('.cours-matiere')?.textContent || 'Non spécifié';
    const enseignant = coursCard.querySelector('.cours-enseignant')?.textContent || 'Non spécifié';
    const classe = coursCard.getAttribute('data-classe-nom') || 'Non spécifié';
    const cell = coursCard.closest('td');
    const jour = cell?.getAttribute('data-jour') || 'Non spécifié';
    const heure = cell?.getAttribute('data-heure') || 'Non spécifié';
    
    // Chercher la modal de détails
    const modal = document.getElementById('detailServiceModal');
    if (!modal) {
        console.warn('❌ Modal de détails non trouvée');
        alert(`Service ID: ${serviceId}\nMatière: ${matiere}\nEnseignant: ${enseignant}\nClasse: ${classe}`);
        return;
    }
    
    // Remplir les informations
    fillModalDetails(modal, {
        creneau: heure,
        jour: jour,
        matiere: matiere,
        enseignant: enseignant,
        classe: classe
    });
    
    // Stocker l'ID du service
    modal.dataset.serviceId = serviceId;
    
    // Ouvrir la modal
    openModalWithFallback(modal);
}

function fillModalDetails(modal, details) {
    const elements = {
        creneau: document.getElementById('detailService_creneau'),
        jour: document.getElementById('detailService_jour'),
        matiere: document.getElementById('detailService_matiere'),
        enseignant: document.getElementById('detailService_enseignant'),
        classe: document.getElementById('detailService_classe')
    };
    
    if (elements.creneau) elements.creneau.textContent = details.creneau;
    if (elements.jour) elements.jour.textContent = details.jour.charAt(0).toUpperCase() + details.jour.slice(1);
    if (elements.matiere) elements.matiere.textContent = details.matiere;
    if (elements.enseignant) elements.enseignant.textContent = details.enseignant;
    if (elements.classe) elements.classe.textContent = details.classe;
}

function openModalWithFallback(modalElement) {
    // Priorité 1: modal-fix.js
    if (typeof window.safeShowModal === 'function') {
        window.safeShowModal(modalElement.id);
        return;
    }
    
    // Priorité 2: Bootstrap direct
    try {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    } catch (error) {
        console.error('❌ Erreur ouverture modal:', error);
        // Fallback manuel
        modalElement.style.display = 'block';
        modalElement.classList.add('show');
        document.body.classList.add('modal-open');
    }
}

// ============================================
// FONCTIONS UTILITAIRES
// ============================================

function debugEcoleSystem() {
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (!ecoleSelect) {
        console.log('❌ ecoleSelect non trouvé');
        return;
    }
    
    const usernameElement = document.querySelector('.navbar .dropdown-toggle span');
    const username = usernameElement ? usernameElement.textContent.trim() : '';
    
    console.log('🔍 Debug système:', {
        username: username,
        selectDisabled: ecoleSelect.disabled,
        optionsCount: ecoleSelect.options.length,
        selectedValue: ecoleSelect.value
    });
}

function changeEcole(ecoleId) {
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (!ecoleSelect) return;
    
    const url = ecoleSelect.dataset.url || "/scolaire/select-ecole";
    
    console.log('🔄 Changement école:', ecoleId, 'URL:', url);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ecole_id: ecoleId})
    })
    .then(response => {
        if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'École sélectionnée', 'success');
            
            // Redirection intelligente - Mettre à jour la session et recharger
            console.log('✅ École changée, rechargement...');
            
            // Petit délai pour que la session soit mise à jour
            setTimeout(() => {
                window.location.reload();
            }, 500);
            
        } else {
            throw new Error(data.error || 'Erreur lors de la sélection');
        }
    })
    .catch(error => {
        console.error('❌ Erreur:', error);
        showNotification('Erreur: ' + error.message, 'error');
    });
}

function showNotification(message, type) {
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 4000);
}

// ============================================
// FONCTIONS GLOBALES
// ============================================

window.openModal = function(modalId) {
    if (typeof window.safeShowModal === 'function') {
        return window.safeShowModal(modalId);
    }
    
    const modalElement = document.getElementById(modalId);
    if (modalElement) {
        try {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            return modal;
        } catch (error) {
            console.error('❌ Erreur:', error);
            return null;
        }
    }
    console.warn(`⚠️ Modal ${modalId} non trouvée`);
    return null;
};

window.closeModal = function(modalId) {
    if (typeof window.safeHideModal === 'function') {
        window.safeHideModal(modalId);
        return;
    }
    
    const modalElement = document.getElementById(modalId);
    if (modalElement) {
        try {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();
        } catch (error) {
            console.error('❌ Erreur:', error);
        }
    }
};

// Fonction globale pour afficher les détails d'un service
window.showServiceDetails = function(serviceId) {
    console.log('🔍 Affichage des détails du service:', serviceId);
    
    const coursCard = document.querySelector(`[data-service-id="${serviceId}"]`);
    if (coursCard) {
        showServiceDetailsFallback(serviceId, coursCard);
    } else {
        console.warn('❌ Carte de service non trouvée:', serviceId);
        alert('Service ID: ' + serviceId);
    }
};
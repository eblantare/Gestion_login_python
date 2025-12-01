// ebase.js - VERSION FINALE CORRIGÉE AVEC REDIRECTION AVEC PARAMÈTRE ECOLE

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des tooltips
    var tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialisation du sélecteur d'école
    initializeEcoleSelector();
    
    // Debug après un délai
    setTimeout(debugEcoleSystem, 1000);
});

function initializeEcoleSelector() {
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (!ecoleSelect) {
        console.log('ℹ️ ecoleSelect non trouvé sur cette page');
        return;
    }
    
    const $ecoleSelect = $('#ecoleSelect');
    const userRole = ecoleSelect.dataset.userRole || '';
    const userEcoleId = ecoleSelect.dataset.userEcoleId || '';
    
    // CORRECTION CRITIQUE : Bonne détection des droits
    const usernameElement = document.querySelector('.navbar .dropdown-toggle span');
    const username = usernameElement ? usernameElement.textContent.trim() : '';
    
    // DÉTECTION CORRECTE :
    // - Admin système : UNIQUEMENT le username 'admin'
    // - Admin école : rôle 'admin' mais username différent de 'admin'
    // - Utilisateur normal : autre
    const isSystemAdmin = username === 'admin';
    const isEcoleAdmin = userRole.toLowerCase() === 'admin' && username !== 'admin';
    const isRegularUser = !isSystemAdmin && !isEcoleAdmin;
    
    console.log('🔐 DÉTECTION DROITS CORRIGÉE:', {
        username: username,
        userRole: userRole,
        userEcoleId: userEcoleId,
        isSystemAdmin: isSystemAdmin,
        isEcoleAdmin: isEcoleAdmin,
        isRegularUser: isRegularUser
    });
    
    // Configuration Select2
    const select2Config = {
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: isSystemAdmin ? "Sélectionnez une école" : "Votre école",
        language: 'fr'
    };
    
    // CORRECTION : Seul l'admin système peut changer d'école
    if (isSystemAdmin) {
        select2Config.allowClear = true;
        ecoleSelect.disabled = false;
        console.log('✅ ADMIN SYSTÈME - Sélecteur ACTIVÉ (peut changer d\'école)');
    } else {
        // Verrouillage pour admin école ET utilisateurs normaux
        select2Config.allowClear = false;
        ecoleSelect.disabled = true;
        
        if (isEcoleAdmin) {
            console.log('🔒 ADMIN ÉCOLE - Sélecteur VERROUILLÉ (école fixe)');
        } else {
            console.log('🔒 UTILISATEUR NORMAL - Sélecteur VERROUILLÉ (école fixe)');
        }
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

// Fonction de debug améliorée
function debugEcoleSystem() {
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (!ecoleSelect) {
        console.log('❌ ecoleSelect non trouvé');
        return;
    }
    
    const usernameElement = document.querySelector('.navbar .dropdown-toggle span');
    const username = usernameElement ? usernameElement.textContent.trim() : '';
    const userRole = ecoleSelect.dataset.userRole || '';
    
    const isSystemAdmin = username === 'admin';
    const isEcoleAdmin = userRole.toLowerCase() === 'admin' && username !== 'admin';
    
    console.log('🔍 DEBUG SYSTÈME COMPLET:', {
        username: username,
        userRole: userRole,
        userEcoleId: ecoleSelect.dataset.userEcoleId,
        
        // Détection des droits
        isSystemAdmin: isSystemAdmin,
        isEcoleAdmin: isEcoleAdmin,
        
        // État du sélecteur
        selectDisabled: ecoleSelect.disabled,
        optionsCount: ecoleSelect.options.length,
        selectedValue: ecoleSelect.value,
        
        // Calcul détaillé
        adminByUsername: username === 'admin',
        adminByRole: userRole.toLowerCase() === 'admin',
        shouldBeLocked: !isSystemAdmin // ← CRITIQUE : doit être verrouillé si pas admin système
    });
}

function changeEcole(ecoleId) {
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (!ecoleSelect) return;
    
    const url = ecoleSelect.dataset.url || "/select-ecole";
    
    console.log('🔄 Envoi changement école:', { ecole_id: ecoleId });
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ecole_id: ecoleId})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'École sélectionnée avec succès', 'success');
            
            // CORRECTION CRITIQUE : Redirection INTELLIGENTE qui conserve la page actuelle
            const currentUrl = new URL(window.location.href);
            const currentPath = currentUrl.pathname;
            
            console.log('📍 Redirection intelligente - Page actuelle:', currentPath);
            console.log('📍 Redirection intelligente - École ID:', ecoleId);
            
            // Construire la nouvelle URL en conservant la page actuelle
            let newUrl;
            
            // Mettre à jour ou ajouter le paramètre ecole dans l'URL actuelle
            currentUrl.searchParams.set('ecole', ecoleId);
            newUrl = currentUrl.toString();
            
            console.log('🔄 Redirection intelligente vers:', newUrl);
            
            // Redirection après un court délai pour voir la notification
            setTimeout(() => {
                window.location.href = newUrl;
            }, 800);
            
        } else {
            throw new Error(data.error || 'Erreur lors de la sélection');
        }
    })
    .catch(error => {
        console.error('❌ Erreur changement école:', error);
        showNotification('Erreur lors du changement d\'école: ' + error.message, 'error');
    });
}

function showNotification(message, type) {
    const container = document.getElementById('notificationContainer');
    if (!container) {
        // Créer le container s'il n'existe pas
        const newContainer = document.createElement('div');
        newContainer.id = 'notificationContainer';
        newContainer.className = 'position-fixed top-0 end-0 p-3';
        newContainer.style.zIndex = '9999';
        document.body.appendChild(newContainer);
        container = newContainer;
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
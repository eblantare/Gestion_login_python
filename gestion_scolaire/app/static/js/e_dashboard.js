// e_dashboard.js - Version simplifiée et fonctionnelle
document.addEventListener("DOMContentLoaded", () => {
    console.log('🚀 e_dashboard.js initialisé - Version simplifiée');
    
    // 1. Gestion des clics sur les cartes menu
    const cards = document.querySelectorAll('.menu-card');
    cards.forEach(card => {
        card.addEventListener('click', (e) => {
            // éviter que le clic sur un sous-menu déclenche une redirection
            if (e.target.closest('.menu-submenu a')) return;
            
            // Logique simple : utiliser l'attribut onclick s'il existe
            const onclickAttr = card.getAttribute('onclick');
            if (onclickAttr && onclickAttr.includes("window.location.href=")) {
                const urlMatch = onclickAttr.match(/window\.location\.href\s*=\s*'([^']+)'/);
                if (urlMatch && urlMatch[1]) {
                    console.log('Redirection vers:', urlMatch[1]);
                    window.location.href = urlMatch[1];
                    return;
                }
            }
            
            // Sinon, rediriger normalement (si la carte a un onclick simple)
            if (card.onclick && typeof card.onclick === 'function') {
                return; // Laisser gérer par l'attribut onclick
            }
        });
        
        // Ajouter le style de curseur
        card.style.cursor = 'pointer';
    });

    // 2. Initialisation Select2 pour le sélecteur d'école (si présent)
    initEcoleSelector();
});

function initEcoleSelector() {
    // Ce sélecteur est probablement pour une page spécifique
    if ($('#ecoleSelectDashboard').length) {
        $('#ecoleSelectDashboard').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: $('#ecoleSelectDashboard').data('placeholder'),
            allowClear: true,
            language: 'fr',
            minimumResultsForSearch: 1,
            dropdownParent: $('.ecole-selector-card')
        }).on('change', function() {
            changeEcole(this.value);
        });
    }
}

function changeEcole(ecoleId) {
    const url = document.querySelector('meta[name="select-ecole-url"]')?.getAttribute('content') || "/scolaire/select-ecole";
    
    fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ecole_id: ecoleId})
    }).then(response => {
        if (response.ok) {
            showNotification('École sélectionnée avec succès', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification('Erreur lors de la sélection', 'error');
        }
    }).catch(error => {
        console.error('Erreur:', error);
        showNotification('Erreur de connexion', 'error');
    });
}

function showNotification(message, type) {
    // Utiliser les notifications Bootstrap existantes
    const container = document.getElementById('notificationContainer');
    if (!container) {
        console.warn('Container de notification non trouvé');
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    new bootstrap.Toast(toast).show();
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}
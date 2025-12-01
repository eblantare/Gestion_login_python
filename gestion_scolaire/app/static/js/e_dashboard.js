document.addEventListener("DOMContentLoaded", () => {
    // Gestion des clics sur les cartes menu
    const cards = document.querySelectorAll('.menu-card');
    cards.forEach(card => {
        card.addEventListener('click', (e) => {
            // éviter que le clic sur un sous-menu déclenche une redirection
            if (e.target.closest('.menu-submenu a')) return;

            const url = card.getAttribute('data-url');
            if (url && url !== '#') {
                window.location.href = url;
            }
        });
    });

    // Initialisation Select2 pour le sélecteur d'école
    initEcoleSelector();

    // Gestion du bouton d'effacement
    const clearBtn = document.getElementById('clearEcoleBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearEcoleSelection);
    }
});

function initEcoleSelector() {
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

        // FORCER l'ouverture du dropdown au focus pour la recherche
        $('#ecoleSelectDashboard').on('select2:open', function() {
            document.querySelector('.select2-search__field').focus();
        });
    }
}

function changeEcole(ecoleId) {
    const url = document.querySelector('meta[name="select-ecole-url"]')?.getAttribute('content') || "{{ url_for('main.select_ecole') }}";
    
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

function clearEcoleSelection() {
    // Réinitialiser le select2
    if ($('#ecoleSelectDashboard').length) {
        $('#ecoleSelectDashboard').val('').trigger('change');
    }
    
    const url = document.querySelector('meta[name="select-ecole-url"]')?.getAttribute('content') || "{{ url_for('main.select_ecole') }}";
    
    fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ecole_id: ''})
    }).then(response => {
        if (response.ok) {
            showNotification('Sélection effacée', 'info');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification('Erreur lors de l\'effacement', 'error');
        }
    }).catch(error => {
        console.error('Erreur:', error);
        showNotification('Erreur de connexion', 'error');
    });
}

function showNotification(message, type) {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger', 
        'info': 'alert-info'
    }[type] || 'alert-info';
    
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
    
    const container = document.getElementById('notificationContainer');
    if (container) {
        container.appendChild(toast);
        new bootstrap.Toast(toast).show();
    }
}
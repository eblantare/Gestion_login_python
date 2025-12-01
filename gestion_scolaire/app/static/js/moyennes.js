// moyennes.js - Version COMPLÈTE avec notifications élégantes
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Module moyennes chargé');
    initializeNotifications();
    initializeExports();
    initializeBatchButton();
    setupButtonStates();
});

// ==================== SYSTÈME DE NOTIFICATIONS ====================

function initializeNotifications() {
    console.log('🔔 Initialisation du système de notifications...');
    
    // Créer le conteneur des notifications s'il n'existe pas
    if (!document.getElementById('notification-container')) {
        const notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        document.body.appendChild(notificationContainer);
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `notification alert alert-${getAlertType(type)} alert-dismissible fade show`;
    notification.style.cssText = `
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border: none;
        border-radius: 8px;
        animation: slideInRight 0.3s ease-out;
    `;

    const icon = getNotificationIcon(type);
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="me-3" style="font-size: 1.2rem;">${icon}</div>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(notification);

    // Auto-dismiss après la durée spécifiée
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }

    return notification;
}

function getAlertType(type) {
    const types = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return types[type] || 'info';
}

function getNotificationIcon(type) {
    const icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    };
    return icons[type] || 'ℹ️';
}

// Animation CSS pour les notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification {
        transition: all 0.3s ease;
    }
    
    .notification.fade:not(.show) {
        opacity: 0;
        transform: translateX(100%);
    }
`;
document.head.appendChild(style);

// ==================== FONCTIONS PRINCIPALES ====================

function initializeExports() {
    console.log('🔄 Configuration des exports...');
    
    const exportOptions = document.querySelectorAll('.export-option');
    console.log(`🔍 ${exportOptions.length} options d'export trouvées`);
    
    exportOptions.forEach(option => {
        option.onclick = function(e) {
            console.log('🎯 Clic export détecté:', this.getAttribute('data-format'));
            
            e.preventDefault();
            e.stopPropagation();
            
            handleExport(this.getAttribute('data-format'));
            return false;
        };
    });
    
    console.log(`✅ ${exportOptions.length} exports configurés`);
}

function initializeBatchButton() {
    console.log('🔄 Configuration du bouton batch...');
    
    const batchForm = document.getElementById('batchForm');
    if (!batchForm) {
        console.log('❌ Formulaire batch non trouvé');
        return;
    }
    
    batchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const classeSelect = document.getElementById('classeSelect');
        const anneeSelect = document.getElementById('anneeSelect');
        const batchBtn = document.getElementById('batchBtn');
        const batchSpinner = document.getElementById('batchSpinner');
        const batchBtnText = document.getElementById('batchBtnText');
        
        if (!classeSelect?.value || !anneeSelect?.value) {
            showNotification('Veuillez sélectionner une classe et une année scolaire', 'warning', 4000);
            return;
        }

        // UI feedback
        batchBtn.disabled = true;
        if (batchSpinner) batchSpinner.classList.remove('d-none');
        if (batchBtnText) batchBtnText.textContent = 'Calcul en cours...';
        
        const formData = new FormData();
        formData.append('classe_id', classeSelect.value);
        formData.append('annee_scolaire', anneeSelect.value);
        formData.append('trimestre', document.querySelector('select[name="trimestre"]').value);

        console.log('🚀 Lancement du calcul batch...');
        
        // Notification de démarrage
        const progressNotification = showNotification(
            '🔄 Calcul des moyennes en cours... Cette opération peut prendre quelques instants.',
            'info',
            0 // Ne pas auto-fermer
        );
        
        fetch(batchForm.action, {
            method: "POST",
            body: formData,
        })
        .then(resp => {
            if (!resp.ok) {
                throw new Error(`HTTP error! status: ${resp.status}`);
            }
            return resp.json();
        })
        .then(data => {
            console.log('✅ Réponse batch:', data);
            
            // Fermer la notification de progression
            if (progressNotification) {
                progressNotification.classList.remove('show');
                setTimeout(() => progressNotification.remove(), 300);
            }
            
            if (batchSpinner) batchSpinner.classList.add('d-none');
            if (batchBtnText) batchBtnText.textContent = 'Calculer moyenne';
            
            if (data.status === "ok") {
                showNotification(
                    `✅ Calcul terminé avec succès !<br><small>${data.created || 0} nouvelles moyennes créées, ${data.updated || 0} mises à jour.</small>`,
                    'success',
                    5000
                );
                
                // Recharger la page après un court délai pour voir les résultats
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
                
            } else {
                showNotification(
                    `❌ Erreur lors du calcul: ${data.message || 'Erreur inconnue'}`,
                    'error',
                    6000
                );
                batchBtn.disabled = false;
            }
        })
        .catch(err => {
            console.error('❌ Erreur batch:', err);
            
            // Fermer la notification de progression
            if (progressNotification) {
                progressNotification.classList.remove('show');
                setTimeout(() => progressNotification.remove(), 300);
            }
            
            if (batchSpinner) batchSpinner.classList.add('d-none');
            if (batchBtnText) batchBtnText.textContent = 'Calculer moyenne';
            batchBtn.disabled = false;
            
            showNotification(
                '❌ Erreur réseau ou serveur. Veuillez réessayer.',
                'error',
                5000
            );
        });
    });
    
    console.log('✅ Bouton batch configuré');
}

function setupButtonStates() {
    console.log('🔄 Configuration des états des boutons...');
    
    function updateButtons() {
        const classeSelect = document.getElementById('classeSelect');
        const anneeSelect = document.getElementById('anneeSelect');
        const batchBtn = document.getElementById('batchBtn');
        const exportDropdown = document.getElementById('exportDropdown');
        
        const isEnabled = classeSelect?.value && anneeSelect?.value;
        
        console.log(`🔧 État boutons - Classe: ${classeSelect?.value}, Année: ${anneeSelect?.value}, Activé: ${isEnabled}`);
        
        if (batchBtn) {
            batchBtn.disabled = !isEnabled;
            // Ajouter un tooltip si désactivé
            if (batchBtn.disabled) {
                batchBtn.title = 'Sélectionnez une classe et une année scolaire';
            } else {
                batchBtn.title = 'Lancer le calcul des moyennes';
            }
        }
        
        if (exportDropdown) {
            exportDropdown.disabled = !isEnabled;
            if (exportDropdown.disabled) {
                exportDropdown.title = 'Sélectionnez une classe et une année scolaire';
            } else {
                exportDropdown.title = 'Exporter les moyennes';
            }
        }
    }
    
    // Écouter les changements sur les selects
    const classeSelect = document.getElementById('classeSelect');
    const anneeSelect = document.getElementById('anneeSelect');
    
    if (classeSelect) {
        classeSelect.addEventListener('change', updateButtons);
        console.log('🎯 Écouteur changements classe ajouté');
    }
    
    if (anneeSelect) {
        anneeSelect.addEventListener('change', updateButtons);
        console.log('🎯 Écouteur changements année ajouté');
    }
    
    // Mettre à jour l'état initial
    updateButtons();
    
    console.log('✅ États des boutons configurés');
}

function handleExport(format) {
    // Validation des sélections
    const classeSelect = document.getElementById('classeSelect');
    const anneeSelect = document.getElementById('anneeSelect');
    const trimestreSelect = document.querySelector('select[name="trimestre"]');
    
    if (!classeSelect || !classeSelect.value) {
        showNotification('❌ Veuillez sélectionner une classe', 'warning', 4000);
        return;
    }
    
    if (!anneeSelect || !anneeSelect.value) {
        showNotification('❌ Veuillez sélectionner une année scolaire', 'warning', 4000);
        return;
    }
    
    const classeId = classeSelect.value;
    const annee = anneeSelect.value;
    const trimestre = trimestreSelect ? trimestreSelect.value : '1';
    
    console.log('📤 Paramètres export:', { classeId, annee, trimestre, format });
    
    // Notification de démarrage d'export
    showNotification(
        `📤 Préparation de l'export ${format.toUpperCase()}...`,
        'info',
        3000
    );
    
    triggerExportDirect(classeId, annee, trimestre, format);
}

function triggerExportDirect(classeId, annee, trimestre, format) {
    const url = `/moyennes/export?classe_id=${encodeURIComponent(classeId)}&annee_scolaire=${encodeURIComponent(annee)}&trimestre=${encodeURIComponent(trimestre)}&format=${format}`;
    
    console.log('🔗 URL d\'export:', url);
    
    // Méthode 1 : Ouverture dans un nouvel onglet (le plus fiable)
    const newWindow = window.open(url, '_blank');
    
    if (newWindow) {
        console.log('✅ Export ouvert dans un nouvel onglet');
        showNotification(
            `✅ Export ${format.toUpperCase()} lancé avec succès !<br><small>Le téléchargement devrait commencer automatiquement.</small>`,
            'success',
            5000
        );
    } else {
        console.log('⚠️ Nouvel onglet bloqué, utilisation de la méthode alternative');
        showNotification(
            '⚠️ Le nouvel onglet a été bloqué. Utilisation de la méthode alternative...',
            'warning',
            3000
        );
        
        // Méthode alternative : Téléchargement direct
        setTimeout(() => {
            const link = document.createElement('a');
            link.href = url;
            link.download = `moyennes_${classeId}_${annee}_T${trimestre}.${format}`;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showNotification(
                `✅ Téléchargement ${format.toUpperCase()} déclenché !`,
                'success',
                4000
            );
        }, 1000);
    }
}

// ==================== FONCTIONS UTILITAIRES ====================

// Gestion des erreurs globales
window.addEventListener('error', function(e) {
    console.error('❌ Erreur globale:', e.error);
    showNotification(
        '❌ Une erreur inattendue s\'est produite. Veuillez rafraîchir la page.',
        'error',
        6000
    );
});

// Gestion des promesses rejetées non attrapées
window.addEventListener('unhandledrejection', function(e) {
    console.error('❌ Promesse rejetée non attrapée:', e.reason);
    showNotification(
        '❌ Erreur de traitement. Veuillez réessayer.',
        'error',
        5000
    );
});
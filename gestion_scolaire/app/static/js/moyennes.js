// static/js/moyennes.js - VERSION COMPLÈTE CORRIGÉE
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Module moyennes chargé');
    
    // Initialiser seulement si ce n'est pas déjà fait
    if (!window.moyennesInitialized) {
        initializeNotifications();
        initializeExports();
        initializeBatchButton();
        setupButtonStates();
        window.moyennesInitialized = true;
    }
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
        
        // Ajouter le style CSS une seule fois
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
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
        }
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
    
    let isProcessing = false; // 🔥 CORRECTION : Variable pour suivre l'état du traitement
    
    batchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 🔥 CORRECTION : Empêcher les clics multiples
        if (isProcessing) {
            console.log('⚠️ Batch déjà en cours, ignore la requête');
            showNotification('⚠️ Calcul déjà en cours, veuillez patienter...', 'warning', 3000);
            return;
        }
        
        console.log('🎯 Soumission du formulaire batch détectée');
        
        // Récupérer les éléments du formulaire
        const classeSelect = document.getElementById('classeSelect');
        const anneeSelect = document.getElementById('anneeSelect');
        const periodeSelect = document.querySelector('select[name="periode"]');
        const batchBtn = document.getElementById('batchBtn');
        const batchSpinner = document.getElementById('batchSpinner');
        const batchBtnText = document.getElementById('batchBtnText');
        
        console.log('📋 Éléments trouvés:', {
            classeSelect: !!classeSelect,
            anneeSelect: !!anneeSelect,
            periodeSelect: !!periodeSelect,
            batchBtn: !!batchBtn,
            batchSpinner: !!batchSpinner,
            batchBtnText: !!batchBtnText
        });
        
        // Validation des champs obligatoires
        if (!classeSelect || !classeSelect.value) {
            showNotification('❌ Veuillez sélectionner une classe', 'warning', 4000);
            return;
        }
        
        if (!anneeSelect || !anneeSelect.value) {
            showNotification('❌ Veuillez sélectionner une année scolaire', 'warning', 4000);
            return;
        }

        // 🔥 CORRECTION : Marquer comme en cours de traitement
        isProcessing = true;
        
        // UI feedback
        if (batchBtn) {
            batchBtn.disabled = true;
            if (batchSpinner) batchSpinner.classList.remove('d-none');
            if (batchBtnText) batchBtnText.textContent = 'Calcul en cours...';
        }
        
        // Préparer les données du formulaire
        const formData = new FormData(batchForm);
        
        // Ajouter les valeurs manquantes si nécessaire
        if (!formData.has('classe_id')) {
            formData.append('classe_id', classeSelect.value);
        }
        
        if (!formData.has('annee_scolaire')) {
            formData.append('annee_scolaire', anneeSelect.value);
        }
        
        if (!formData.has('periode') && periodeSelect) {
            formData.append('periode', periodeSelect.value);
        } else if (!formData.has('periode')) {
            formData.append('periode', '1'); // Valeur par défaut
        }
        
        // Déterminer le type de système
        let typeSysteme = 'trimestriel';
        const typeSystemeInput = document.querySelector('input[name="type_systeme"]');
        if (typeSystemeInput) {
            formData.append('type_systeme', typeSystemeInput.value);
            typeSysteme = typeSystemeInput.value;
        } else {
            // Détecter automatiquement
            if (periodeSelect && periodeSelect.options.length <= 2) {
                formData.append('type_systeme', 'semestriel');
                typeSysteme = 'semestriel';
            } else {
                formData.append('type_systeme', 'trimestriel');
            }
        }

        console.log('🚀 Lancement du calcul batch...');
        console.log('📤 Données envoyées:', {
            classe_id: classeSelect.value,
            annee_scolaire: anneeSelect.value,
            periode: formData.get('periode'),
            type_systeme: typeSysteme
        });
        
        // Notification de démarrage
        const progressNotification = showNotification(
            '🔄 Calcul des moyennes en cours... Cette opération peut prendre quelques instants.',
            'info',
            0 // Ne pas auto-fermer
        );
        
        // Envoyer la requête
        fetch(batchForm.action, {
            method: "POST",
            body: formData,
        })
        .then(resp => {
            console.log('📨 Réponse du serveur:', resp.status, resp.statusText);
            
            // Si la réponse n'est pas OK, essayer de lire le message d'erreur
            if (!resp.ok) {
                return resp.text().then(text => {
                    let errorMessage = `HTTP error! status: ${resp.status}`;
                    
                    // Essayer de parser le JSON d'erreur
                    try {
                        const errorData = JSON.parse(text);
                        errorMessage = errorData.message || errorMessage;
                    } catch (e) {
                        // Si ce n'est pas du JSON, utiliser le texte brut
                        if (text) {
                            errorMessage += ` - ${text.substring(0, 100)}`;
                        }
                    }
                    
                    throw new Error(errorMessage);
                });
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
            
            // Restaurer le bouton
            if (batchSpinner) batchSpinner.classList.add('d-none');
            if (batchBtnText) batchBtnText.textContent = 'Calculer moyennes';
            
            // 🔥 CORRECTION : Réactiver le bouton après succès
            isProcessing = false;
            
            if (data.status === "ok" || data.status === "success") {
                showNotification(
                    `✅ ${data.message || 'Calcul terminé avec succès !'}<br><small>${data.details?.created || 0} nouvelles moyennes créées, ${data.details?.updated || 0} mises à jour.</small>`,
                    'success',
                    5000
                );
                
                // Recharger la page après un court délai pour voir les résultats
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
                
            } else {
                showNotification(
                    `❌ ${data.message || 'Erreur lors du calcul'}`,
                    'error',
                    6000
                );
                if (batchBtn) {
                    setTimeout(() => {
                        batchBtn.disabled = false;
                    }, 3000); // 🔥 Désactiver pendant 3 secondes
                }
            }
        })
        .catch(err => {
            console.error('❌ Erreur batch:', err);
            
            // Fermer la notification de progression
            if (progressNotification) {
                progressNotification.classList.remove('show');
                setTimeout(() => progressNotification.remove(), 300);
            }
            
            // 🔥 CORRECTION : Réactiver le bouton en cas d'erreur
            isProcessing = false;
            
            // Restaurer le bouton
            if (batchSpinner) batchSpinner.classList.add('d-none');
            if (batchBtnText) batchBtnText.textContent = 'Calculer moyennes';
            if (batchBtn) {
                setTimeout(() => {
                    batchBtn.disabled = false;
                }, 2000); // 🔥 Désactiver pendant 2 secondes après erreur
            }
            
            // Afficher un message d'erreur approprié
            let errorMessage = 'Erreur réseau ou serveur. Veuillez réessayer.';
            if (err.message.includes('500')) {
                errorMessage = 'Erreur interne du serveur (500). Contactez l\'administrateur.';
            } else if (err.message.includes('Failed to fetch')) {
                errorMessage = 'Erreur de connexion au serveur. Vérifiez votre réseau.';
            } else if (err.message) {
                errorMessage = err.message;
            }
            
            showNotification(`❌ ${errorMessage}`, 'error', 5000);
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
    const periodeSelect = document.querySelector('select[name="periode"]');
    
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
    const periode = periodeSelect ? periodeSelect.value : '1';
    
    console.log('📤 Paramètres export:', { classeId, annee, periode, format });
    
    // Notification de démarrage d'export
    showNotification(
        `📤 Préparation de l'export ${format.toUpperCase()}...`,
        'info',
        3000
    );
    
    triggerExportDirect(classeId, annee, periode, format);
}

function triggerExportDirect(classeId, annee, periode, format) {
    // Récupérer le type système
    let typeSysteme = 'trimestriel';
    const typeSystemeInput = document.querySelector('input[name="type_systeme"]');
    if (typeSystemeInput) {
        typeSysteme = typeSystemeInput.value;
    } else if (periode && parseInt(periode) <= 2) {
        // Si seulement 2 périodes, c'est probablement semestriel
        typeSysteme = 'semestriel';
    }
    
    // 🔥 CORRECTION : Utiliser encodeURIComponent pour tous les paramètres
    const url = `/moyennes/export?` + new URLSearchParams({
        classe_id: classeId,
        annee_scolaire: annee,
        periode: periode,
        type_systeme: typeSysteme,
        format: format
    }).toString();
    
    console.log('🔗 URL d\'export:', url);
    
    // 🔥 CORRECTION : Méthode améliorée pour l'export
    try {
        // Créer un iframe invisible pour le téléchargement
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = url;
        document.body.appendChild(iframe);
        
        // Supprimer l'iframe après un délai
        setTimeout(() => {
            if (iframe.parentNode) {
                document.body.removeChild(iframe);
            }
        }, 5000);
        
        showNotification(
            `✅ Export ${format.toUpperCase()} lancé avec succès !<br><small>Le téléchargement devrait commencer automatiquement.</small>`,
            'success',
            5000
        );
        
    } catch (error) {
        console.error('⚠️ Erreur lors de l\'export:', error);
        
        // Méthode alternative : Téléchargement direct
        showNotification(
            '⚠️ Méthode alternative d\'export utilisée...',
            'warning',
            2000
        );
        
        setTimeout(() => {
            const link = document.createElement('a');
            link.href = url;
            link.download = `moyennes_${classeId}_${annee}_${typeSysteme === 'semestriel' ? 'S' : 'T'}${periode}.${format}`;
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

// 🔥 NOUVEAU : Fonction pour détecter le changement de système
function detectSystemChange() {
    const periodeSelect = document.querySelector('select[name="periode"]');
    if (periodeSelect) {
        const oldOptionsLength = periodeSelect.options.length;
        
        periodeSelect.addEventListener('change', function() {
            // Si le nombre d'options change, recharger la page
            if (periodeSelect.options.length !== oldOptionsLength) {
                console.log('🔄 Changement de système détecté, rechargement de la page');
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            }
        });
    }
}

// 🔥 NOUVEAU : Initialiser la détection de changement de système
if (document.querySelector('select[name="periode"]')) {
    detectSystemChange();
}

// 🔥 NOUVEAU : Gestion des sessions expirées
function checkSessionValidity() {
    const currentTime = new Date().getTime();
    const lastActivity = localStorage.getItem('lastActivity') || currentTime;
    
    // Si plus de 30 minutes d'inactivité
    if (currentTime - lastActivity > 30 * 60 * 1000) {
        showNotification('⚠️ Session expirée, veuillez vous reconnecter', 'warning', 10000);
        setTimeout(() => {
            window.location.href = '/auth/login';
        }, 5000);
    }
    
    localStorage.setItem('lastActivity', currentTime);
}

// 🔥 NOUVEAU : Mettre à jour l'activité utilisateur
document.addEventListener('click', function() {
    localStorage.setItem('lastActivity', new Date().getTime());
});

// 🔥 NOUVEAU : Vérifier la session toutes les 5 minutes
setInterval(checkSessionValidity, 5 * 60 * 1000);
// Variables globales
let currentExportType = '';
let currentExportFormat = '';
let classesList = [];

// Charger les classes quand le modal s'ouvre
document.addEventListener('DOMContentLoaded', function() {
    // Écouter l'ouverture du modal pour charger les classes
    const modalElement = document.getElementById('classeSelectionModal');
    if (modalElement) {
        modalElement.addEventListener('show.bs.modal', function() {
            loadClasses();
        });
    }
});

// Charger la liste des classes
async function loadClasses() {
    const loadingElement = document.getElementById('loadingClasses');
    const errorElement = document.getElementById('classesError');
    const selectElement = document.getElementById('classeSelect');
    
    // Réinitialiser l'interface
    if (loadingElement) loadingElement.style.display = 'block';
    if (errorElement) {
        errorElement.style.display = 'none';
        errorElement.textContent = '';
    }
    if (selectElement) {
        selectElement.innerHTML = '<option value="">Chargement des classes...</option>';
        selectElement.disabled = true;
    }
    
    try {
        console.log('🔍 Chargement des classes depuis /eleves/classes...');
        
        const response = await fetch('/eleves/classes');
        console.log('📡 Réponse reçue:', response);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📊 Données reçues:', data);
        
        if (!Array.isArray(data)) {
            throw new Error('Les données reçues ne sont pas un tableau');
        }
        
        classesList = data;
        
        // Mettre à jour le select
        if (selectElement) {
            selectElement.innerHTML = '<option value="">Sélectionnez une classe</option>';
            
            if (data.length === 0) {
                selectElement.innerHTML = '<option value="">Aucune classe disponible</option>';
            } else {
                data.forEach(classe => {
                    // Vérifier que la classe a les propriétés attendues
                    if (classe && classe.id && classe.nom) {
                        const option = document.createElement('option');
                        option.value = classe.id;
                        option.textContent = classe.nom;
                        selectElement.appendChild(option);
                    } else {
                        console.warn('Classe invalide ignorée:', classe);
                    }
                });
            }
            selectElement.disabled = false;
        }
        
        console.log(`✅ ${data.length} classe(s) chargée(s) avec succès`);
        
    } catch (error) {
        console.error('❌ Erreur lors du chargement des classes:', error);
        
        // Afficher le message d'erreur
        if (errorElement) {
            errorElement.textContent = `Erreur: ${error.message}`;
            errorElement.style.display = 'block';
        }
        
        // Mettre à jour le select avec un message d'erreur
        if (selectElement) {
            selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
        }
        
        showAlert('Erreur lors du chargement des classes', 'danger');
    } finally {
        if (loadingElement) loadingElement.style.display = 'none';
    }
}

// Fonctions d'export pour les élèves
function exportEleves(format) {
    currentExportFormat = format;
    currentExportType = 'eleves';
    
    // Ouvrir le modal de sélection de classe
    const modalElement = document.getElementById('classeSelectionModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    } else {
        showAlert('Erreur: Modal de sélection non trouvé', 'danger');
    }
}

function confirmElevesExport() {
    const classeSelect = document.getElementById('classeSelect');
    if (!classeSelect) {
        showAlert('Erreur: Sélecteur de classe non trouvé', 'danger');
        return;
    }
    
    const classeId = classeSelect.value;
    
    if (!classeId) {
        showAlert('Veuillez sélectionner une classe', 'warning');
        return;
    }
    
    // Vérifier que la classe sélectionnée est valide
    const selectedClasse = classesList.find(classe => classe.id === classeId);
    if (!selectedClasse) {
        showAlert('Classe sélectionnée invalide', 'danger');
        return;
    }
    
    console.log(`🚀 Export ${currentExportFormat} pour la classe:`, selectedClasse.nom);
    
    // Fermer le modal
    const modalElement = document.getElementById('classeSelectionModal');
    if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement);
        modal.hide();
    }
    
    // Lancer l'export
    const url = `/eleves/export/${currentExportFormat}/${classeId}`;
    console.log('📤 URL d\'export:', url);
    
    // Ouvrir dans un nouvel onglet
    const newWindow = window.open(url, '_blank');
    
    if (!newWindow) {
        showAlert('Le navigateur a bloqué la fenêtre popup. Autorisez les popups pour ce site.', 'warning');
        return;
    }
    
    showAlert(`Export PDF de la classe ${selectedClasse.nom} en cours...`, 'success');
}

// Fonctions d'export pour les enseignants
function exportEnseignants(format) {
    console.log(`🚀 Export ${format} des enseignants`);
    const url = `/enseignants/export/${format}`;
    
    // Ouvrir dans un nouvel onglet
    const newWindow = window.open(url, '_blank');
    
    if (!newWindow) {
        showAlert('Le navigateur a bloqué la fenêtre popup. Autorisez les popups pour ce site.', 'warning');
        return;
    }
    
    showAlert('Export des enseignants en cours...', 'success');
}

// Fonction pour les exports en développement
function showComingSoon(type) {
    const types = {
        'notes': 'des notes',
        'moyennes': 'des moyennes', 
        'statistiques': 'des statistiques'
    };
    showAlert(`Export ${types[type] || ''} en cours de développement`, 'info');
}

// Fonction utilitaire pour afficher des alertes
function showAlert(message, type) {
    console.log(`[ALERTE ${type.toUpperCase()}] ${message}`);
    
    // Vérifier si Bootstrap est disponible
    if (typeof bootstrap === 'undefined') {
        // Fallback simple si Bootstrap n'est pas disponible
        alert(`[${type.toUpperCase()}] ${message}`);
        return;
    }
    
    try {
        // Créer l'alerte Bootstrap
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;';
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi ${getAlertIcon(type)} me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Supprimer automatiquement après 4 secondes
        setTimeout(() => {
            if (alertDiv.parentNode) {
                // Ajouter une animation de sortie
                alertDiv.style.opacity = '0';
                alertDiv.style.transition = 'opacity 0.3s ease';
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.parentNode.removeChild(alertDiv);
                    }
                }, 300);
            }
        }, 4000);
    } catch (error) {
        console.error('Erreur lors de l\'affichage de l\'alerte:', error);
        alert(message); // Fallback ultime
    }
}

// Helper pour les icônes d'alerte
function getAlertIcon(type) {
    const icons = {
        'success': 'bi-check-circle-fill',
        'danger': 'bi-exclamation-triangle-fill',
        'warning': 'bi-exclamation-circle-fill',
        'info': 'bi-info-circle-fill'
    };
    return icons[type] || 'bi-info-circle-fill';
}

// Gestion des erreurs globales
window.addEventListener('error', function(e) {
    // Ignorer les erreurs liées à des éléments DOM manquants sur cette page
    if (e.message.includes('null') && (e.message.includes('addEventListener') || e.message.includes('value'))) {
        console.warn('Erreur DOM ignorée (élément non présent sur cette page):', e.error);
        return;
    }
    console.error('Erreur JavaScript critique:', e.error);
});

// Test manuel des classes (pour debug)
function testClassesAPI() {
    console.log('🧪 Test manuel de l\'API classes...');
    loadClasses();
}

//<!-- AJOUTER CE SCRIPT POUR LES FONCTIONS D'EXPORT DES NOTES -->
// ===============================
// Fonctions d'exportation des notes (globales)
// ===============================

async function openNotesExportModal() {
    try {
        // Charger les filtres disponibles
        const resp = await fetch('/notes/export/filters');
        const filters = await resp.json();
        
        // Remplir les selects
        const classeSelect = document.getElementById('export_notes_classe');
        const matiereSelect = document.getElementById('export_notes_matiere');
        const anneeSelect = document.getElementById('export_notes_annee');
        
        if (!classeSelect || !matiereSelect || !anneeSelect) {
            console.error('Éléments du modal d\'export non trouvés');
            return;
        }
        
        // Classes
        classeSelect.innerHTML = '<option value="">Toutes les classes</option>';
        filters.classes.forEach(c => {
            const option = document.createElement('option');
            option.value = c.id;
            option.textContent = c.nom;
            classeSelect.appendChild(option);
        });
        
        // Matières
        matiereSelect.innerHTML = '<option value="">Toutes les matières</option>';
        filters.matieres.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = m.libelle;
            matiereSelect.appendChild(option);
        });
        
        // Années scolaires
        anneeSelect.innerHTML = '<option value="">Toutes les années</option>';
        filters.annees_scolaires.forEach(a => {
            const option = document.createElement('option');
            option.value = a;
            option.textContent = a;
            anneeSelect.appendChild(option);
        });
        
        // Afficher le modal
        const modalElement = document.getElementById('notesExportModal');
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        }
        
    } catch (error) {
        console.error('Erreur chargement filtres export:', error);
        showAlert('Erreur lors du chargement des filtres', 'danger');
    }
}

function exportNotes(format) {
    const form = document.getElementById('notesExportForm');
    if (!form) {
        console.error('Formulaire d\'export non trouvé');
        return;
    }
    
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    // Construire l'URL d'export
    let url = `/notes/export/${format}?${params.toString()}`;
    
    // Ouvrir dans une nouvelle fenêtre pour le téléchargement
    window.open(url, '_blank');
    
    // Fermer le modal
    const modalElement = document.getElementById('notesExportModal');
    if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    }
    
    showAlert(`Export ${format.toUpperCase()} des notes en cours...`, 'info');
}

// S'assurer que les fonctions sont globales
// window.openNotesExportModal = openNotesExportModal;
// window.exportNotes = exportNotes;


// Fonctions pour l'export des moyennes
async function openMoyennesExportModal() {
    try {
        // Charger les filtres disponibles
        const resp = await fetch('/moyennes/export/filters');
        const filters = await resp.json();
        
        // Remplir les selects
        const classeSelect = document.getElementById('export_moyennes_classe');
        const matiereSelect = document.getElementById('export_moyennes_matiere');
        const anneeSelect = document.getElementById('export_moyennes_annee');
        const mentionSelect = document.getElementById('export_moyennes_mention');
        
        if (!classeSelect || !matiereSelect || !anneeSelect || !mentionSelect) {
            console.error('Éléments du modal d\'export des moyennes non trouvés');
            return;
        }
        
        // Classes
        classeSelect.innerHTML = '<option value="">Toutes les classes</option>';
        filters.classes.forEach(c => {
            const option = document.createElement('option');
            option.value = c.id;
            option.textContent = c.nom;
            classeSelect.appendChild(option);
        });
        
        // Matières
        matiereSelect.innerHTML = '<option value="">Toutes les matières</option>';
        filters.matieres.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = m.libelle;
            matiereSelect.appendChild(option);
        });
        
        // Années scolaires
        anneeSelect.innerHTML = '<option value="">Toutes les années</option>';
        filters.annees_scolaires.forEach(a => {
            const option = document.createElement('option');
            option.value = a;
            option.textContent = a;
            anneeSelect.appendChild(option);
        });
        
        // Mentions
        mentionSelect.innerHTML = '<option value="">Toutes les mentions</option>';
        filters.mentions.forEach(m => {
            const option = document.createElement('option');
            option.value = m;
            option.textContent = m;
            mentionSelect.appendChild(option);
        });
        
        // Afficher le modal
        const modalElement = document.getElementById('moyennesExportModal');
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        }
        
    } catch (error) {
        console.error('Erreur chargement filtres export moyennes:', error);
        showAlert('Erreur lors du chargement des filtres', 'danger');
    }
}

function exportMoyennes(format) {
    const form = document.getElementById('moyennesExportForm');
    if (!form) {
        console.error('Formulaire d\'export des moyennes non trouvé');
        return;
    }
    
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    // Construire l'URL d'export
    let url = `/moyennes/export/${format}?${params.toString()}`;
    
    // Ouvrir dans une nouvelle fenêtre pour le téléchargement
    window.open(url, '_blank');
    
    // Fermer le modal
    const modalElement = document.getElementById('moyennesExportModal');
    if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    }
    
    showAlert(`Export ${format.toUpperCase()} des moyennes en cours...`, 'info');
}

// S'assurer que les fonctions sont globales
window.openMoyennesExportModal = openMoyennesExportModal;
window.exportMoyennes = exportMoyennes;
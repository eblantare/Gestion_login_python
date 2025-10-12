// Variables globales
let currentExportType = '';
let currentExportFormat = '';
let classesList = [];

// ======================= FONCTIONS UTILITAIRES SÉCURISÉES =======================

// Fonction sécurisée pour les modals Bootstrap
function safeModalShow(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) {
        console.warn(`Modal ${modalId} non trouvé`);
        return null;
    }
    try {
        return bootstrap.Modal.getOrCreateInstance(modalElement).show();
    } catch (error) {
        console.error(`Erreur ouverture modal ${modalId}:`, error);
        return null;
    }
}

function safeModalHide(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;
    try {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();
    } catch (error) {
        console.error(`Erreur fermeture modal ${modalId}:`, error);
    }
}

// Fonction utilitaire pour afficher des alertes (UNE SEULE VERSION)
function showAlert(message, type = 'info') {
    console.log(`[ALERTE ${type.toUpperCase()}] ${message}`);
    
    // Vérifier si Bootstrap est disponible
    if (typeof bootstrap === 'undefined') {
        alert(`[${type.toUpperCase()}] ${message}`);
        return;
    }
    
    try {
        const alertClass = {
            'success': 'alert-success',
            'danger': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
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
                alertDiv.remove();
            }
        }, 4000);
    } catch (error) {
        console.error('Erreur affichage alerte:', error);
        alert(message);
    }
}

function getAlertIcon(type) {
    const icons = {
        'success': 'bi-check-circle-fill',
        'danger': 'bi-exclamation-triangle-fill',
        'warning': 'bi-exclamation-circle-fill',
        'info': 'bi-info-circle-fill'
    };
    return icons[type] || 'bi-info-circle-fill';
}

// ======================= CHARGEMENT DES CLASSES =======================

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
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
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
                    if (classe && classe.id && classe.nom) {
                        const option = document.createElement('option');
                        option.value = classe.id;
                        option.textContent = classe.nom;
                        selectElement.appendChild(option);
                    }
                });
            }
            selectElement.disabled = false;
        }
        
        console.log(`✅ ${data.length} classe(s) chargée(s)`);
        
    } catch (error) {
        console.error('❌ Erreur chargement classes:', error);
        
        if (errorElement) {
            errorElement.textContent = `Erreur: ${error.message}`;
            errorElement.style.display = 'block';
        }
        
        if (selectElement) {
            selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
        }
        
        showAlert('Erreur lors du chargement des classes', 'danger');
    } finally {
        if (loadingElement) loadingElement.style.display = 'none';
    }
}

// ======================= EXPORT ÉLÈVES =======================

function exportEleves(format) {
    currentExportFormat = format;
    currentExportType = 'eleves';
    safeModalShow('classeSelectionModal');
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
    
    const selectedClasse = classesList.find(classe => classe.id === classeId);
    if (!selectedClasse) {
        showAlert('Classe sélectionnée invalide', 'danger');
        return;
    }
    
    console.log(`🚀 Export ${currentExportFormat} pour:`, selectedClasse.nom);
    
    safeModalHide('classeSelectionModal');
    
    const url = `/eleves/export/${currentExportFormat}/${classeId}`;
    const newWindow = window.open(url, '_blank');
    
    if (!newWindow) {
        showAlert('Autorisez les popups pour ce site', 'warning');
        return;
    }
    
    showAlert(`Export PDF de ${selectedClasse.nom} en cours...`, 'success');
}

// ======================= EXPORT ENSEIGNANTS =======================

function exportEnseignants(format) {
    console.log(`🚀 Export ${format} des enseignants`);
    const url = `/enseignants/export/${format}`;
    const newWindow = window.open(url, '_blank');
    
    if (!newWindow) {
        showAlert('Autorisez les popups pour ce site', 'warning');
        return;
    }
    
    showAlert('Export des enseignants en cours...', 'success');
}

// ======================= EXPORT NOTES =======================

async function openNotesExportModal() {
    try {
        const resp = await fetch('/notes/export/filters');
        const filters = await resp.json();
        
        const classeSelect = document.getElementById('export_notes_classe');
        const matiereSelect = document.getElementById('export_notes_matiere');
        const anneeSelect = document.getElementById('export_notes_annee');
        
        if (!classeSelect || !matiereSelect || !anneeSelect) {
            console.error('Éléments du modal d\'export non trouvés');
            return;
        }
        
        // Classes
        classeSelect.innerHTML = '<option value="">Toutes les classes</option>';
        filters.classes?.forEach(c => {
            const option = document.createElement('option');
            option.value = c.id;
            option.textContent = c.nom;
            classeSelect.appendChild(option);
        });
        
        // Matières
        matiereSelect.innerHTML = '<option value="">Toutes les matières</option>';
        filters.matieres?.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = m.libelle;
            matiereSelect.appendChild(option);
        });
        
        // Années
        anneeSelect.innerHTML = '<option value="">Toutes les années</option>';
        filters.annees_scolaires?.forEach(a => {
            const option = document.createElement('option');
            option.value = a;
            option.textContent = a;
            anneeSelect.appendChild(option);
        });
        
        safeModalShow('notesExportModal');
        
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
    const url = `/notes/export/${format}?${params.toString()}`;
    
    window.open(url, '_blank');
    safeModalHide('notesExportModal');
    showAlert(`Export ${format.toUpperCase()} des notes en cours...`, 'info');
}

// ======================= EXPORT MOYENNES =======================

async function openMoyennesExportModal() {
    try {
        const resp = await fetch('/moyennes/export/filters');
        const filters = await resp.json();
        
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
        filters.classes?.forEach(c => {
            const option = document.createElement('option');
            option.value = c.id;
            option.textContent = c.nom;
            classeSelect.appendChild(option);
        });
        
        // Matières
        matiereSelect.innerHTML = '<option value="">Toutes les matières</option>';
        filters.matieres?.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = m.libelle;
            matiereSelect.appendChild(option);
        });
        
        // Années
        anneeSelect.innerHTML = '<option value="">Toutes les années</option>';
        filters.annees_scolaires?.forEach(a => {
            const option = document.createElement('option');
            option.value = a;
            option.textContent = a;
            anneeSelect.appendChild(option);
        });
        
        // Mentions
        mentionSelect.innerHTML = '<option value="">Toutes les mentions</option>';
        filters.mentions?.forEach(m => {
            const option = document.createElement('option');
            option.value = m;
            option.textContent = m;
            mentionSelect.appendChild(option);
        });
        
        safeModalShow('moyennesExportModal');
        
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
    const url = `/moyennes/export/${format}?${params.toString()}`;
    
    window.open(url, '_blank');
    safeModalHide('moyennesExportModal');
    showAlert(`Export ${format.toUpperCase()} des moyennes en cours...`, 'info');
}

// ======================= EXPORT BULLETINS =======================

function openBulletinsExportModal() {
    console.log('📋 Ouverture modal bulletins...');
    loadBulletinsFilters();
    safeModalShow('bulletinsExportModal');
}

function updateBulletinsExportUI() {
    const exportType = document.querySelector('input[name="export_type"]:checked')?.value;
    const eleveSection = document.getElementById('eleve_selection');
    const classeSection = document.getElementById('classe_selection');
    
    console.log('🔄 Mise à jour UI - Type:', exportType);
    
    if (!exportType) return;
    
    if (exportType === 'individuel') {
        if (eleveSection) eleveSection.style.display = 'flex';
        if (classeSection) classeSection.style.display = 'none';
    } else if (exportType === 'classe') {
        if (eleveSection) eleveSection.style.display = 'none';
        if (classeSection) classeSection.style.display = 'block';
    } else {
        if (eleveSection) eleveSection.style.display = 'none';
        if (classeSection) classeSection.style.display = 'none';
    }
}

async function loadElevesForBulletins(classeId, selectElementId) {
    const eleveSelect = document.getElementById(selectElementId);
    if (!eleveSelect) {
        console.error('❌ Select élève non trouvé:', selectElementId);
        return;
    }
    
    if (!classeId) {
        eleveSelect.innerHTML = '<option value="">Sélectionnez d\'abord une classe</option>';
        eleveSelect.disabled = true;
        return;
    }
    
    try {
        console.log('👥 Chargement élèves pour classe:', classeId);
        eleveSelect.disabled = true;
        eleveSelect.innerHTML = '<option value="">Chargement des élèves...</option>';
        
        const response = await fetch('/export/filters');
        if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);
        
        const data = await response.json();
        console.log('📦 Données filtres reçues:', data);
        
        const classe = data.classes?.find(c => c.id === classeId);
        console.log('🔍 Classe trouvée:', classe);
        
        if (classe && classe.eleves?.length > 0) {
            eleveSelect.innerHTML = '<option value="">Sélectionnez un élève</option>';
            classe.eleves.forEach(eleve => {
                const option = document.createElement('option');
                option.value = eleve.id;
                option.textContent = eleve.nom_complet;
                eleveSelect.appendChild(option);
            });
            eleveSelect.disabled = false;
            console.log(`✅ ${classe.eleves.length} élèves chargés`);
        } else {
            eleveSelect.innerHTML = '<option value="">Aucun élève trouvé</option>';
            console.warn('⚠️ Aucun élève trouvé pour cette classe');
        }
    } catch (error) {
        console.error('❌ Erreur chargement élèves:', error);
        eleveSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        showAlert('Erreur lors du chargement des élèves', 'danger');
    }
}

function onClasseSelectChange(selectElement, targetSelectId = 'export_bulletins_eleve') {
    const classeId = selectElement.value;
    console.log('🔄 Changement classe:', classeId, '->', targetSelectId);
    loadElevesForBulletins(classeId, targetSelectId);
}

async function loadBulletinsFilters() {
    try {
        console.log('🔍 Chargement des filtres bulletins...');
        const response = await fetch('/export/filters');
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📦 Filtres reçus:', data);
        
        if (!data.classes || !Array.isArray(data.classes)) {
            throw new Error('Format de données invalide pour les classes');
        }
        
        // Charger les classes pour les deux selects
        const classeSelectEleve = document.getElementById('export_bulletins_classe_eleve');
        const classeSelectClasse = document.getElementById('export_bulletins_classe');
        
        if (classeSelectEleve) {
            classeSelectEleve.innerHTML = '<option value="">Sélectionnez une classe</option>';
            data.classes.forEach(classe => {
                if (classe && classe.id && classe.nom) {
                    const option = document.createElement('option');
                    option.value = classe.id;
                    option.textContent = classe.nom;
                    classeSelectEleve.appendChild(option);
                }
            });
            console.log(`✅ ${data.classes.length} classes chargées dans select élève`);
        }
        
        if (classeSelectClasse) {
            classeSelectClasse.innerHTML = '<option value="">Sélectionnez une classe</option>';
            data.classes.forEach(classe => {
                if (classe && classe.id && classe.nom) {
                    const option = document.createElement('option');
                    option.value = classe.id;
                    option.textContent = classe.nom;
                    classeSelectClasse.appendChild(option);
                }
            });
            console.log(`✅ ${data.classes.length} classes chargées dans select classe`);
        }
        
        // Charger les années
        const anneeSelect = document.getElementById('export_bulletins_annee');
        if (anneeSelect && data.annees_scolaires) {
            anneeSelect.innerHTML = '<option value="">Sélectionnez une année</option>';
            data.annees_scolaires.forEach(annee => {
                const option = document.createElement('option');
                option.value = annee;
                option.textContent = annee;
                anneeSelect.appendChild(option);
            });
            console.log(`✅ ${data.annees_scolaires.length} années chargées`);
        }
        
        // Mettre à jour l'UI
        updateBulletinsExportUI();
        
    } catch (error) {
        console.error('❌ Erreur chargement filtres bulletins:', error);
        showAlert('Erreur lors du chargement des données: ' + error.message, 'danger');
    }
}

function exportBulletins() {
    console.log('🚀 Début export bulletins...');
    
    const form = document.getElementById('bulletinsExportForm');
    if (!form) {
        console.error('❌ Formulaire bulletins non trouvé');
        showAlert('Formulaire non trouvé', 'danger');
        return;
    }
    
    // Debug complet du formulaire
    debugBulletinsForm();
    
    const formData = new FormData(form);
    const exportType = formData.get('export_type');
    const trimestre = formData.get('trimestre');
    const annee_scolaire = formData.get('annee_scolaire');
    
    console.log('📋 Paramètres export:', { exportType, trimestre, annee_scolaire });
    
    // Validation des paramètres obligatoires
    if (!trimestre || !annee_scolaire) {
        showAlert('Veuillez sélectionner le trimestre et l\'année scolaire', 'warning');
        return;
    }
    
    let url = '';
    const params = new URLSearchParams();
    params.append('trimestre', trimestre);
    params.append('annee_scolaire', annee_scolaire);
    
    try {
        if (exportType === 'individuel') {
            const eleveSelect = document.getElementById('export_bulletins_eleve');
            const eleveId = eleveSelect ? eleveSelect.value : null;
            
            if (!eleveId || eleveId === '') {
                showAlert('Veuillez sélectionner un élève', 'warning');
                return;
            }
            
            params.append('eleve_id', eleveId);
            url = `/export/bulletin?${params}`;
            console.log('👤 URL export individuel:', url);
            
        } else if (exportType === 'classe') {
            const classeSelect = document.getElementById('export_bulletins_classe');
            const classeId = classeSelect ? classeSelect.value : null;
            
            console.log('🔍 Debug export classe:', {
                selectElement: classeSelect,
                classeId: classeId,
                options: classeSelect ? Array.from(classeSelect.options).map(opt => ({value: opt.value, text: opt.text})) : 'non trouvé'
            });
            
            if (!classeId || classeId === '') {
                showAlert('Veuillez sélectionner une classe', 'warning');
                return;
            }
            
            params.append('classe_id', classeId);
            url = `/export/bulletins_classe?${params}`;
            console.log('👥 URL export classe:', url);
            
        } else if (exportType === 'toutes_classes') {
            url = `/export/bulletins_toutes_classes?${params}`;
            console.log('🏫 URL export toutes classes:', url);
            
        } else {
            showAlert('Type d\'export non reconnu', 'danger');
            return;
        }
        
        console.log('🌐 Ouverture URL:', url);
        const newWindow = window.open(url, '_blank');
        
        if (!newWindow) {
            showAlert('Autorisez les popups pour ce site', 'warning');
            return;
        }
        
        safeModalHide('bulletinsExportModal');
        showAlert('Génération des bulletins en cours...', 'success');
        
    } catch (error) {
        console.error('❌ Erreur lors de l\'export:', error);
        showAlert('Erreur lors de la génération des bulletins: ' + error.message, 'danger');
    }
}

function debugBulletinsForm() {
    const form = document.getElementById('bulletinsExportForm');
    if (!form) {
        console.error('❌ Formulaire non trouvé');
        return;
    }
    
    const formData = new FormData(form);
    const exportType = formData.get('export_type');
    
    console.log('🔍 DEBUG FORMULAIRE BULLETINS:');
    console.log('   Type d\'export:', exportType);
    console.log('   Trimestre:', formData.get('trimestre'));
    console.log('   Année scolaire:', formData.get('annee_scolaire'));
    
    if (exportType === 'individuel') {
        const classeEleveSelect = document.getElementById('export_bulletins_classe_eleve');
        const eleveSelect = document.getElementById('export_bulletins_eleve');
        console.log('   Classe (individuel):', classeEleveSelect ? classeEleveSelect.value : 'non trouvé');
        console.log('   Élève:', eleveSelect ? eleveSelect.value : 'non trouvé');
    } else if (exportType === 'classe') {
        const classeSelect = document.getElementById('export_bulletins_classe');
        console.log('   Classe (export classe):', classeSelect ? classeSelect.value : 'non trouvé');
    }
}

// Appelez cette fonction dans la console pour debugger
window.debugBulletinsForm = debugBulletinsForm;

// ======================= INITIALISATION =======================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM chargé - Initialisation exports');
    
    // Écouter l'ouverture du modal pour charger les classes élèves
    const modalElement = document.getElementById('classeSelectionModal');
    if (modalElement) {
        modalElement.addEventListener('show.bs.modal', loadClasses);
    }
    
    // Gérer la visibilité des sections bulletins
    document.querySelectorAll('input[name="export_type"]').forEach(radio => {
        radio.addEventListener('change', updateBulletinsExportUI);
    });
    
    // Initialiser l'UI des bulletins
    updateBulletinsExportUI();
    
    console.log('✅ Script d\'export complètement initialisé');
});

// ======================= FONCTIONS GLOBALES =======================

// Exposer les fonctions globales
window.exportEleves = exportEleves;
window.confirmElevesExport = confirmElevesExport;
window.exportEnseignants = exportEnseignants;
window.openNotesExportModal = openNotesExportModal;
window.exportNotes = exportNotes;
window.openMoyennesExportModal = openMoyennesExportModal;
window.exportMoyennes = exportMoyennes;
window.openBulletinsExportModal = openBulletinsExportModal;
window.exportBulletins = exportBulletins;
window.onClasseSelectChange = onClasseSelectChange;

console.log('✅ Script d\'export chargé avec succès');
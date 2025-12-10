// services.js - VERSION FINALE COMPLÈTE POUR LES EXPORTATIONS

// ======================= VARIABLES GLOBALES =======================
let currentExportType = '';
let currentExportFormat = '';
let currentEcoleId = '';
let currentNotesExportFormat = '';

// ======================= FONCTIONS UTILITAIRES =======================

function showAlert(message, type = 'info') {
    console.log(`[ALERTE ${type.toUpperCase()}] ${message}`);
    
    // Supprimer les alertes existantes pour éviter les doublons
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => {
        if (alert.parentNode) {
            alert.remove();
        }
    });
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'custom-alert';
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#28a745' : type === 'danger' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#007bff'};
        color: white;
        border-radius: 5px;
        z-index: 9999;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        font-weight: 500;
        max-width: 400px;
        word-wrap: break-word;
    `;
    alertDiv.textContent = message;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function safeModalShow(modalId) {
    const modalElement = document.getElementById(modalId);
    if (modalElement && typeof bootstrap !== 'undefined') {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        return modal;
    }
    return null;
}

function safeModalHide(modalId) {
    const modalElement = document.getElementById(modalId);
    if (modalElement && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();
    }
}

// ======================= RÉCUPÉRATION DE L'ÉCOLE SÉLECTIONNÉE =======================


// ======================= FONCTIONS UTILITAIRES CORRIGÉES =======================

function getSelectedEcoleId() {
    // Priorité 1: Sélecteur dans l'interface
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (ecoleSelect && ecoleSelect.value) {
        console.log(`🎯 École sélectionnée dans l'interface: ${ecoleSelect.value}`);
        return ecoleSelect.value;
    }
    
    // Priorité 2: Paramètre URL
    const urlParams = new URLSearchParams(window.location.search);
    const ecoleIdFromUrl = urlParams.get('ecole_id');
    if (ecoleIdFromUrl) {
        console.log(`🎯 École depuis URL: ${ecoleIdFromUrl}`);
        return ecoleIdFromUrl;
    }
    
    // Priorité 3: Données de l'utilisateur connecté (si disponibles)
    if (typeof currentUser !== 'undefined' && currentUser && currentUser.ecole_id) {
        console.log(`🎯 École de l'utilisateur connecté: ${currentUser.ecole_id}`);
        return currentUser.ecole_id;
    }
    
    console.log('⚠️ Aucune école sélectionnée détectée');
    return '';
}


// ======================= FONCTIONS CORRIGÉES POUR LE BUG 2 =======================

async function loadClasses() {
    const loadingElement = document.getElementById('loadingClasses');
    const errorElement = document.getElementById('classesError');
    const selectElement = document.getElementById('classeSelect');
    
    console.log('🔄 Début du chargement des classes...');
    
    currentEcoleId = getSelectedEcoleId();
    console.log(`🏫 Chargement des classes pour l'école: ${currentEcoleId}`);
    
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
        // CORRECTION BUG 2: Utilisation de l'endpoint correct pour filtrer par école
        let url = '/services/classes';
        const params = new URLSearchParams();
        
        if (currentEcoleId) {
            params.append('ecole_id', currentEcoleId);
        }
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        console.log('🔍 Envoi requête à:', url);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        console.log('📡 Réponse reçue, status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Erreur HTTP:', response.status, errorText);
            throw new Error(`Erreur serveur: ${response.status}`);
        }
        
        const classes = await response.json();
        console.log('📦 Données reçues:', classes);
        
        // Mettre à jour le select
        if (selectElement) {
            selectElement.innerHTML = '<option value="">Sélectionnez une classe</option>';
            
            if (classes && classes.length > 0) {
                classes.forEach(classe => {
                    const option = document.createElement('option');
                    option.value = classe.id;
                    option.textContent = classe.nom;
                    selectElement.appendChild(option);
                });
                selectElement.disabled = false;
                console.log(`✅ ${classes.length} classe(s) chargée(s) dans le select`);
            } else {
                selectElement.innerHTML = '<option value="">Aucune classe disponible</option>';
                console.warn('⚠️ Aucune classe disponible pour cette école');
                
                if (currentEcoleId) {
                    showAlert('Aucune classe trouvée pour cette école', 'warning');
                }
            }
        }
        
    } catch (error) {
        console.error('❌ Erreur chargement classes:', error);
        
        if (errorElement) {
            errorElement.textContent = `Erreur: ${error.message}`;
            errorElement.style.display = 'block';
        }
        
        if (selectElement) {
            selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
        }
        
        showAlert(`Erreur lors du chargement des classes: ${error.message}`, 'danger');
    } finally {
        if (loadingElement) loadingElement.style.display = 'none';
        console.log('🏁 Chargement des classes terminé');
    }
}

// ======================= EXPORT ÉLÈVES =======================

function exportEleves(format) {
    currentExportFormat = format;
    currentExportType = 'eleves';
    
    currentEcoleId = getSelectedEcoleId();
    console.log(`🎯 Début export élèves en format ${format} pour l'école: ${currentEcoleId}`);
    
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
    
    const selectedOption = classeSelect.options[classeSelect.selectedIndex];
    const classeNom = selectedOption.textContent;
    
    console.log(`🚀 Export ${currentExportFormat} pour la classe:`, classeNom);
    console.log(`🏫 École utilisée: ${currentEcoleId}`);
    
    safeModalHide('classeSelectionModal');
    
    let url = `/services/export/eleves?type=${currentExportFormat}&classe_id=${classeId}`;
    if (currentEcoleId) {
        url += `&ecole_id=${currentEcoleId}`;
    }
    
    console.log('🌐 Ouverture URL:', url);
    
    const newWindow = window.open(url, '_blank');
    
    if (!newWindow) {
        showAlert('Veuillez autoriser les popups pour ce site afin de télécharger les exports', 'warning');
        return;
    }
    
    showAlert(`Export ${currentExportFormat.toUpperCase()} de la classe ${classeNom} en cours...`, 'success');
}

// ======================= EXPORT ENSEIGNANTS =======================

function exportEnseignants(format) {
    currentEcoleId = getSelectedEcoleId();
    console.log(`🎯 Export enseignants ${format} pour l'école: ${currentEcoleId}`);
    
    let url = `/services/export/enseignants?type=${format}`;
    if (currentEcoleId) {
        url += `&ecole_id=${currentEcoleId}`;
    }
    
    console.log('🌐 Ouverture URL enseignants:', url);
    
    const newWindow = window.open(url, '_blank');
    
    if (!newWindow) {
        showAlert('Veuillez autoriser les popups pour ce site afin de télécharger les exports', 'warning');
        return;
    }
    
    showAlert(`Export ${format.toUpperCase()} des enseignants en cours...`, 'success');
}

// ======================= EXPORT NOTES =======================

function openNotesExportModal() {
    currentNotesExportFormat = '';
    console.log('📊 Ouverture modal export notes');
    
    loadNotesFilters();
    safeModalShow('notesExportModal');
}



// ======================= FONCTIONS POUR LE CHARGEMENT DES NOTES =======================

async function loadNotesClasses() {
    try {
        const ecoleId = getSelectedEcoleId();
        let url = '/services/notes/classes';
        const params = new URLSearchParams();
        
        if (ecoleId) {
            params.append('ecole_id', ecoleId);
        }
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erreur chargement classes');
        
        const classes = await response.json();
        const select = document.getElementById('export_notes_classe');
        
        if (select) {
            // ✅ CORRECTION : Ajouter l'option "Toutes les classes"
            select.innerHTML = '<option value="toutes">Toutes les classes</option>';
            if (classes && classes.length > 0) {
                classes.forEach(classe => {
                    const option = document.createElement('option');
                    option.value = classe.id;
                    option.textContent = classe.nom;
                    select.appendChild(option);
                });
            } else {
                select.innerHTML = '<option value="">Aucune classe disponible</option>';
            }
        }
    } catch (error) {
        console.error('❌ Erreur chargement classes notes:', error);
        showAlert('Erreur lors du chargement des classes', 'danger');
    }
}

async function loadNotesMatieres() {
    try {
        const ecoleId = getSelectedEcoleId();
        let url = '/services/notes/matieres';
        if (ecoleId) {
            url += `?ecole_id=${ecoleId}`;
        }
        
        console.log('🔄 Chargement des matières depuis:', url);
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erreur chargement matières');
        
        const matieres = await response.json();
        const select = document.getElementById('export_notes_matiere');
        
        console.log('📦 Matières reçues:', matieres);
        
        if (select) {
            select.innerHTML = '<option value="">Toutes les matières</option>';
            matieres.forEach(matiere => {
                const option = document.createElement('option');
                option.value = matiere.id;
                option.textContent = matiere.libelle;
                // Log pour Agriculture
                if (matiere.libelle === 'Agriculture') {
                    console.log('🎯 Agriculture trouvée - ID:', matiere.id);
                }
                select.appendChild(option);
            });
            
            console.log(`✅ ${matieres.length} matière(s) chargée(s) dans le select`);
        }
    } catch (error) {
        console.error('❌ Erreur chargement matières notes:', error);
        showAlert('Erreur lors du chargement des matières', 'danger');
    }
}

async function loadNotesAnneesScolaires() {
    try {
        const response = await fetch('/services/notes/annees-scolaires');
        if (!response.ok) throw new Error('Erreur chargement années scolaires');
        
        const annees = await response.json();
        const select = document.getElementById('export_notes_annee');
        
        if (select) {
            select.innerHTML = '<option value="">Toutes les années</option>';
            annees.forEach(annee => {
                const option = document.createElement('option');
                option.value = annee.annee;
                option.textContent = annee.annee;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('❌ Erreur chargement années scolaires:', error);
        showAlert('Erreur lors du chargement des années scolaires', 'danger');
    }
}



// ======================= FONCTIONS POUR LES AUTRES EXPORTS (À VENIR) =======================


// ======================= EXPORT BULLETINS =======================

function openBulletinsExportModal() {
    console.log('📋 Ouverture modal export bulletins');
    currentNotesExportFormat = '';
    
    // Charger les filtres pour les bulletins
    loadBulletinsFilters();
    
    // Afficher le modal
    const modal = safeModalShow('bulletinsExportModal');
    
    // Initialiser l'interface
    setupBulletinsExportType();
    
    // Initialiser les options de période
    updateBulletinsPeriodOptions();
    
    return modal;
}
// Fonction utilitaire pour charger les classes dans un select
// Fonction utilitaire pour charger les classes dans un select
function loadClassesIntoSelect(classes, selectId) {
    const select = document.getElementById(selectId);
    if (select && classes) {
        select.innerHTML = '<option value="">Sélectionnez une classe</option>';
        classes.forEach(classe => {
            const option = document.createElement('option');
            option.value = classe.id;
            option.textContent = classe.nom;
            select.appendChild(option);
        });
    }
}
function loadAnneesScolaires(annees, selectId) {
    const select = document.getElementById(selectId);
    if (select && annees) {
        select.innerHTML = '<option value="">Sélectionnez une année</option>';
        annees.forEach(annee => {
            const option = document.createElement('option');
            option.value = annee;
            option.textContent = annee;
            select.appendChild(option);
        });
    }
}
// Fonction pour charger les filtres des bulletins
async function loadBulletinsFilters() {
    console.log('🔄 Chargement des filtres bulletins...');
    
    try {
        const ecoleId = getSelectedEcoleId();
        let url = '/export/filters';
        const params = new URLSearchParams();
        
        if (ecoleId) {
            params.append('ecole_id', ecoleId);
        }
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        console.log('🔍 Chargement des filtres depuis:', url);
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erreur chargement des filtres');
        
        const data = await response.json();
        console.log('📦 Données filtres reçues:', data);
        
        // CORRECTION BUG 2: Charger les classes filtrées par école
        if (data.classes && data.classes.length > 0) {
            loadClassesIntoSelect(data.classes, 'export_bulletins_classe_eleve');
            loadClassesIntoSelect(data.classes, 'export_bulletins_classe');
            loadAnneesScolaires(data.annees_scolaires, 'export_bulletins_annee');
            console.log('✅ Filtres bulletins chargés avec succès');
        } else {
            console.warn('⚠️ Aucune classe disponible pour les bulletins');
            showAlert('Aucune classe disponible pour cette école', 'warning');
        }
        
    } catch (error) {
        console.error('❌ Erreur chargement filtres bulletins:', error);
        showAlert('Erreur lors du chargement des filtres', 'danger');
    }
}


// Configuration du type d'export
function setupBulletinsExportType() {
    const exportTypeRadios = document.querySelectorAll('input[name="export_type"]');
    const eleveSection = document.getElementById('eleve_selection');
    const classeSection = document.getElementById('classe_selection');
    
    // Initialiser l'affichage
    updateBulletinsSections();
    
    // Ajouter les écouteurs d'événements
    exportTypeRadios.forEach(radio => {
        radio.addEventListener('change', updateBulletinsSections);
    });
    
    function updateBulletinsSections() {
        const exportType = document.querySelector('input[name="export_type"]:checked').value;
        
        if (exportType === 'individuel') {
            eleveSection.style.display = 'flex';
            classeSection.style.display = 'none';
        } else if (exportType === 'classe') {
            eleveSection.style.display = 'none';
            classeSection.style.display = 'block';
        } else if (exportType === 'toutes_classes') {
            eleveSection.style.display = 'none';
            classeSection.style.display = 'none';
        }
    }
}

async function loadBulletinsClasses() {
    try {
        const ecoleId = getSelectedEcoleId();
        let url = '/export/filters';
        if (ecoleId) {
            url += `?ecole_id=${ecoleId}`;
        }
        
        console.log('🔄 Chargement des classes pour bulletins...');
        const response = await fetch(url);
        
        if (!response.ok) throw new Error('Erreur chargement classes bulletins');
        
        const data = await response.json();
        console.log('📦 Données classes bulletins reçues:', data);
        
        // Charger pour les différentes sections
        loadBulletinsClassesForEleves(data.classes);
        loadBulletinsClassesForExport(data.classes);
        loadBulletinsAnneesScolaires(data.annees_scolaires);
        
    } catch (error) {
        console.error('❌ Erreur chargement classes bulletins:', error);
        showAlert('Erreur lors du chargement des classes', 'danger');
    }
}

async function loadBulletinsClassesForEleves(classesData = null) {
    try {
        let classes = classesData;
        
        if (!classes) {
            const ecoleId = getSelectedEcoleId();
            let url = '/export/filters';
            if (ecoleId) {
                url += `?ecole_id=${ecoleId}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) throw new Error('Erreur chargement classes');
            const data = await response.json();
            classes = data.classes;
        }
        
        const select = document.getElementById('export_bulletins_classe_eleve');
        if (select && classes) {
            select.innerHTML = '<option value="">Sélectionnez une classe</option>';
            classes.forEach(classe => {
                const option = document.createElement('option');
                option.value = classe.id;
                option.textContent = classe.nom;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('❌ Erreur chargement classes pour élèves:', error);
    }
}

async function loadBulletinsClassesForExport(classesData = null) {
    try {
        let classes = classesData;
        
        if (!classes) {
            const ecoleId = getSelectedEcoleId();
            let url = '/export/filters';
            if (ecoleId) {
                url += `?ecole_id=${ecoleId}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) throw new Error('Erreur chargement classes');
            const data = await response.json();
            classes = data.classes;
        }
        
        const select = document.getElementById('export_bulletins_classe');
        if (select && classes) {
            select.innerHTML = '<option value="">Sélectionnez une classe</option>';
            classes.forEach(classe => {
                const option = document.createElement('option');
                option.value = classe.id;
                option.textContent = classe.nom;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('❌ Erreur chargement classes pour export:', error);
    }
}

async function loadBulletinsAnneesScolaires(anneesData = null) {
    try {
        let annees = anneesData;
        
        if (!annees) {
            const response = await fetch('/export/filters');
            if (!response.ok) throw new Error('Erreur chargement années scolaires');
            const data = await response.json();
            annees = data.annees_scolaires;
        }
        
        const select = document.getElementById('export_bulletins_annee');
        if (select && annees) {
            select.innerHTML = '<option value="">Sélectionnez une année</option>';
            annees.forEach(annee => {
                const option = document.createElement('option');
                option.value = annee;
                option.textContent = annee;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('❌ Erreur chargement années scolaires bulletins:', error);
        showAlert('Erreur lors du chargement des années scolaires', 'danger');
    }
}

// Fonction pour charger les élèves quand une classe est sélectionnée
async function onClasseSelectChange(selectElement, eleveSelectId) {
    const classeId = selectElement.value;
    const eleveSelect = document.getElementById(eleveSelectId);
    
    if (!classeId) {
        eleveSelect.innerHTML = '<option value="">Sélectionnez d\'abord une classe</option>';
        eleveSelect.disabled = true;
        return;
    }
    
    console.log(`🔄 Chargement des élèves pour la classe: ${classeId}`);
    await loadElevesForClasse(classeId, eleveSelectId);
}


async function loadElevesForClasse(classeId, eleveSelectId) {
    try {
        const eleveSelect = document.getElementById(eleveSelectId);
        eleveSelect.innerHTML = '<option value="">Chargement des élèves...</option>';
        eleveSelect.disabled = true;
        
        const ecoleId = getSelectedEcoleId();
        let url = `/export/filters`;
        if (ecoleId) {
            url += `?ecole_id=${ecoleId}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erreur chargement des élèves');
        
        const data = await response.json();
        const classe = data.classes.find(c => c.id === classeId);
        
        if (classe && classe.eleves) {
            eleveSelect.innerHTML = '<option value="">Sélectionnez un élève</option>';
            classe.eleves.forEach(eleve => {
                const option = document.createElement('option');
                option.value = eleve.id;
                option.textContent = eleve.nom_complet;
                eleveSelect.appendChild(option);
            });
            eleveSelect.disabled = false;
            console.log(`✅ ${classe.eleves.length} élève(s) chargé(s)`);
        } else {
            eleveSelect.innerHTML = '<option value="">Aucun élève trouvé</option>';
            console.warn('⚠️ Aucun élève trouvé pour cette classe');
        }
        
    } catch (error) {
        console.error('❌ Erreur chargement élèves:', error);
        const eleveSelect = document.getElementById(eleveSelectId);
        eleveSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        showAlert('Erreur lors du chargement des élèves', 'danger');
    }
}

// Fonction pour les exports "bientôt disponibles"
function showComingSoon(service) {
    showAlert(`La fonction d'export ${service} sera disponible prochainement`, 'info');
}

// Fonction pour l'export personnalisé
function openCustomExport() {
    showAlert('L\'export personnalisé sera disponible dans une prochaine version', 'info');
}

function exportBulletins() {
    const exportType = document.querySelector('input[name="export_type"]:checked').value;
    const ecoleType = document.getElementById('export_bulletins_ecole_type').value;
    const periode = document.getElementById('export_bulletins_periode').value;
    const anneeScolaire = document.getElementById('export_bulletins_annee').value;
    const ecoleId = getSelectedEcoleId();
    
    // Validation
    if (!periode) {
        showAlert('Veuillez sélectionner une période', 'warning');
        return;
    }
    
    if (!anneeScolaire) {
        showAlert('Veuillez sélectionner une année scolaire', 'warning');
        return;
    }
    
    let url = '';
    let filename = '';
    
    try {
        if (exportType === 'individuel') {
            const classeId = document.getElementById('export_bulletins_classe_eleve').value;
            const eleveId = document.getElementById('export_bulletins_eleve').value;
            
            if (!classeId) {
                showAlert('Veuillez sélectionner une classe', 'warning');
                return;
            }
            
            if (!eleveId) {
                showAlert('Veuillez sélectionner un élève', 'warning');
                return;
            }
            
            // URL CORRIGÉE : /export/bulletin (pas /export/bulletin/)
            url = `/export/bulletin?eleve_id=${eleveId}&trimestre=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}&mode=normal`;
            url += `&ecole_type=${ecoleType}`; // AJOUT IMPORTANT
            
            const periodeTexte = ecoleType === 'lycee' ? `S${periode}` : `T${periode}`;
            filename = `bulletin_eleve_${periodeTexte}_${anneeScolaire.replace('/', '-')}.pdf`;
            
            console.log(`🚀 Export bulletin individuel: ${url}`);
            
        } else if (exportType === 'classe') {
            const classeId = document.getElementById('export_bulletins_classe').value;
            
            if (!classeId) {
                showAlert('Veuillez sélectionner une classe', 'warning');
                return;
            }
            
            // URL CORRIGÉE : /export/bulletins-classe (avec tiret)
            url = `/export/bulletins-classe?classe_id=${classeId}&trimestre=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}&mode=normal`;
            url += `&ecole_type=${ecoleType}`; // AJOUT IMPORTANT
            
            const periodeTexte = ecoleType === 'lycee' ? `S${periode}` : `T${periode}`;
            filename = `bulletins_classe_${periodeTexte}_${anneeScolaire.replace('/', '-')}.pdf`;
            
            console.log(`🚀 Export bulletins classe: ${url}`);
            
        } else if (exportType === 'toutes_classes') {
            // URL CORRIGÉE : /export/bulletins-toutes-classes (avec tirets)
            url = `/export/bulletins-toutes-classes?trimestre=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}&mode=normal`;
            url += `&ecole_type=${ecoleType}`; // AJOUT IMPORTANT
            
            const periodeTexte = ecoleType === 'lycee' ? `S${periode}` : `T${periode}`;
            filename = `bulletins_toutes_classes_${periodeTexte}_${anneeScolaire.replace('/', '-')}.pdf`;
            
            console.log(`🚀 Export bulletins toutes classes: ${url}`);
        }
        
        // Ajouter les paramètres communs
        if (ecoleId) {
            url += `&ecole_id=${ecoleId}`;
        }
        
        console.log('🌐 URL finale:', url);
        
        safeModalHide('bulletinsExportModal');
        showAlert(`Génération des bulletins en cours...`, 'info');
        
        // Utiliser une nouvelle fenêtre pour le téléchargement
        const newWindow = window.open(url, '_blank');
        
        if (!newWindow) {
            // Si les popups sont bloqués, utiliser fetch
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Erreur HTTP: ${response.status}`);
                    }
                    return response.blob();
                })
                .then(blob => {
                    const downloadUrl = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = downloadUrl;
                    a.download = filename;
                    
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(downloadUrl);
                    document.body.removeChild(a);
                    
                    showAlert(`Export des bulletins réussi !`, 'success');
                })
                .catch(error => {
                    console.error('❌ Erreur export bulletins:', error);
                    showAlert(`Erreur lors de l'export: ${error.message}`, 'danger');
                });
        }
            
    } catch (error) {
        console.error('❌ Erreur préparation export bulletins:', error);
        showAlert(`Erreur: ${error.message}`, 'danger');
    }
}

// ======================= FONCTIONS POUR LE MODE COMPACT =======================

function exportBulletinsCompact() {
    const exportType = document.querySelector('input[name="export_type"]:checked').value;
    const ecoleType = document.getElementById('export_bulletins_ecole_type').value;
    const periode = document.getElementById('export_bulletins_periode').value;
    const anneeScolaire = document.getElementById('export_bulletins_annee').value;
    const ecoleId = getSelectedEcoleId();
    
    // Validation
    if (!periode) {
        showAlert('Veuillez sélectionner une période', 'warning');
        return;
    }
    
    if (!anneeScolaire) {
        showAlert('Veuillez sélectionner une année scolaire', 'warning');
        return;
    }
    
    let url = '';
    let filename = '';
    
    try {
        if (exportType === 'individuel') {
            const classeId = document.getElementById('export_bulletins_classe_eleve').value;
            const eleveId = document.getElementById('export_bulletins_eleve').value;
            
            if (!classeId) {
                showAlert('Veuillez sélectionner une classe', 'warning');
                return;
            }
            
            if (!eleveId) {
                showAlert('Veuillez sélectionner un élève', 'warning');
                return;
            }
            
            // URL CORRIGÉE POUR MODE COMPACT
            url = `/export/bulletin?eleve_id=${eleveId}&trimestre=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}&mode=compact`;
            url += `&ecole_type=${ecoleType}`; // AJOUT IMPORTANT
            
            const periodeTexte = ecoleType === 'lycee' ? `S${periode}` : `T${periode}`;
            filename = `bulletin_compact_eleve_${periodeTexte}_${anneeScolaire.replace('/', '-')}.pdf`;
            
            console.log(`🚀 Export bulletin compact individuel: ${url}`);
            
        } else if (exportType === 'classe') {
            const classeId = document.getElementById('export_bulletins_classe').value;
            
            if (!classeId) {
                showAlert('Veuillez sélectionner une classe', 'warning');
                return;
            }
            
            // URL CORRIGÉE : /export/bulletins-classe (avec tiret)
            url = `/export/bulletins-classe?classe_id=${classeId}&trimestre=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}&mode=compact`;
            url += `&ecole_type=${ecoleType}`; // AJOUT IMPORTANT
            
            const periodeTexte = ecoleType === 'lycee' ? `S${periode}` : `T${periode}`;
            filename = `bulletins_compact_classe_${periodeTexte}_${anneeScolaire.replace('/', '-')}.pdf`;
            
            console.log(`🚀 Export bulletins compact classe: ${url}`);
            
        } else if (exportType === 'toutes_classes') {
            // URL CORRIGÉE : /export/bulletins-toutes-classes (avec tirets)
            url = `/export/bulletins-toutes-classes?trimestre=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}&mode=compact`;
            url += `&ecole_type=${ecoleType}`; // AJOUT IMPORTANT
            
            const periodeTexte = ecoleType === 'lycee' ? `S${periode}` : `T${periode}`;
            filename = `bulletins_compact_toutes_classes_${periodeTexte}_${anneeScolaire.replace('/', '-')}.pdf`;
            
            console.log(`🚀 Export bulletins compact toutes classes: ${url}`);
        }
        
        // Ajouter les paramètres communs
        if (ecoleId) {
            url += `&ecole_id=${ecoleId}`;
        }
        
        console.log('🌐 URL finale compacte:', url);
        
        safeModalHide('bulletinsExportModal');
        showAlert(`Génération des bulletins compacts en cours...`, 'info');
        
        // Utiliser fetch pour le téléchargement
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.blob();
            })
            .then(blob => {
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = downloadUrl;
                a.download = filename;
                
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(downloadUrl);
                document.body.removeChild(a);
                
                showAlert(`Export des bulletins compacts réussi !`, 'success');
            })
            .catch(error => {
                console.error('❌ Erreur export bulletins compact:', error);
                showAlert(`Erreur lors de l'export compact: ${error.message}`, 'danger');
            });
            
    } catch (error) {
        console.error('❌ Erreur préparation export bulletins compact:', error);
        showAlert(`Erreur: ${error.message}`, 'danger');
    }
}

function openBulletinsCompactModal() {
    console.log('📋 Ouverture modal export bulletins compact');
    
    // Charger les filtres pour les bulletins
    loadBulletinsFilters();
    
    // Afficher le modal
    const modal = safeModalShow('bulletinsExportModal');
    
    // Initialiser l'interface
    setupBulletinsExportType();
    
    // Initialiser les options de période
    updateBulletinsPeriodOptions();
    
    // Ajouter un indicateur que c'est le mode compact
    const modalTitle = document.querySelector('#bulletinsExportModal .modal-title');
    if (modalTitle) {
        modalTitle.innerHTML = '<span style="color: #28a745;"><i class="fas fa-compress"></i> Export Bulletins Compact</span>';
    }
    
    // Ajouter un champ caché pour indiquer le mode compact
    let compactIndicator = document.getElementById('compactModeIndicator');
    if (!compactIndicator) {
        compactIndicator = document.createElement('input');
        compactIndicator.type = 'hidden';
        compactIndicator.id = 'compactModeIndicator';
        compactIndicator.value = 'true';
        const modalBody = document.querySelector('#bulletinsExportModal .modal-body');
        if (modalBody) {
            modalBody.appendChild(compactIndicator);
        }
    }
    
    return modal;
}

// ======================= EXPORT MOYENNES =======================

// Fonction pour ouvrir le modal d'export des moyennes
function openMoyennesExportModal() {
    const modal = new bootstrap.Modal(document.getElementById('moyennesExportModal'));
    
    // Charger les données initiales
    loadExportMoyennesData();
    
    // Afficher le modal
    modal.show();
}

function loadExportMoyennesData() {
    // Charger les classes
    $.ajax({
        url: '/services/moyennes/classes',
        method: 'GET',
        success: function(classes) {
            const select = $('#export_moyennes_classe');
            select.empty();
            select.append('<option value="">Sélectionnez une classe</option>');
            select.append('<option value="toutes">Toutes les classes</option>');
            
            classes.forEach(classe => {
                select.append(`<option value="${classe.id}">${classe.nom}</option>`);
            });
        },
        error: function() {
            showError('Erreur lors du chargement des classes');
        }
    });
    
    // Charger les matières
    $.ajax({
        url: '/services/moyennes/matieres',
        method: 'GET',
        success: function(matieres) {
            const select = $('#export_moyennes_matiere');
            select.empty();
            select.append('<option value="">Toutes les matières</option>');
            
            matieres.forEach(matiere => {
                select.append(`<option value="${matiere.id}">${matiere.libelle}</option>`);
            });
        },
        error: function() {
            showError('Erreur lors du chargement des matières');
        }
    });
    
    // Charger les années scolaires
    $.ajax({
        url: '/services/moyennes/annees-scolaires',
        method: 'GET',
        success: function(annees) {
            const select = $('#export_moyennes_annee');
            select.empty();
            select.append('<option value="">Toutes les années</option>');
            
            annees.forEach(annee => {
                select.append(`<option value="${annee.annee}">${annee.annee}</option>`);
            });
        },
        error: function() {
            showError('Erreur lors du chargement des années scolaires');
        }
    });
    
    // Charger les mentions
    $.ajax({
        url: '/services/moyennes/mentions',
        method: 'GET',
        success: function(mentions) {
            const select = $('#export_moyennes_mention');
            select.empty();
            select.append('<option value="">Toutes les mentions</option>');
            
            mentions.forEach(mention => {
                select.append(`<option value="${mention.code}">${mention.libelle}</option>`);
            });
        },
        error: function() {
            showError('Erreur lors du chargement des mentions');
        }
    });
    
    // Initialiser les options de période
    updatePeriodOptions('moyennes');
}


// ======================= FONCTIONS POUR LE CHARGEMENT DES MOYENNES =======================

async function loadMoyennesClasses() {
    try {
        const ecoleId = getSelectedEcoleId();
        let url = '/services/moyennes/classes';
        const params = new URLSearchParams();
        
        if (ecoleId) {
            params.append('ecole_id', ecoleId);
        }
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erreur chargement classes');
        
        const classes = await response.json();
        const select = document.getElementById('export_moyennes_classe');
        
        if (select) {
            select.innerHTML = '<option value="">Toutes les classes</option>';
            if (classes && classes.length > 0) {
                classes.forEach(classe => {
                    const option = document.createElement('option');
                    option.value = classe.id;
                    option.textContent = classe.nom;
                    select.appendChild(option);
                });
            } else {
                select.innerHTML = '<option value="">Aucune classe disponible</option>';
            }
        }
    } catch (error) {
        console.error('❌ Erreur chargement classes moyennes:', error);
        showAlert('Erreur lors du chargement des classes', 'danger');
    }
}

async function loadMoyennesMatieres() {
    try {
        const ecoleId = getSelectedEcoleId();
        let url = '/services/moyennes/matieres';
        if (ecoleId) {
            url += `?ecole_id=${ecoleId}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erreur chargement matières');
        
        const matieres = await response.json();
        const select = document.getElementById('export_moyennes_matiere');
        
        if (select) {
            select.innerHTML = '<option value="">Toutes les matières</option>';
            matieres.forEach(matiere => {
                const option = document.createElement('option');
                option.value = matiere.id;
                option.textContent = matiere.libelle;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('❌ Erreur chargement matières moyennes:', error);
        showAlert('Erreur lors du chargement des matières', 'danger');
    }
}

async function loadMoyennesAnneesScolaires() {
    try {
        const response = await fetch('/services/moyennes/annees-scolaires');
        if (!response.ok) throw new Error('Erreur chargement années scolaires');
        
        const annees = await response.json();
        const select = document.getElementById('export_moyennes_annee');
        
        if (select) {
            select.innerHTML = '<option value="">Toutes les années</option>';
            annees.forEach(annee => {
                const option = document.createElement('option');
                option.value = annee.annee;
                option.textContent = annee.annee;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('❌ Erreur chargement années scolaires:', error);
        showAlert('Erreur lors du chargement des années scolaires', 'danger');
    }
}

async function loadMoyennesMentions() {
    try {
        const response = await fetch('/services/moyennes/mentions');
        if (!response.ok) throw new Error('Erreur chargement mentions');
        
        const mentions = await response.json();
        const select = document.getElementById('export_moyennes_mention');
        
        if (select) {
            select.innerHTML = '<option value="">Toutes les mentions</option>';
            mentions.forEach(mention => {
                const option = document.createElement('option');
                option.value = mention.code;
                option.textContent = mention.libelle;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('❌ Erreur chargement mentions:', error);
        showAlert('Erreur lors du chargement des mentions', 'danger');
    }
}


// ======================= GESTION DU CHANGEMENT D'ÉCOLE =======================

function setupEcoleChangeListener() {
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (ecoleSelect) {
        ecoleSelect.addEventListener('change', function() {
            currentEcoleId = this.value;
            const ecoleName = this.options[this.selectedIndex].text;
            console.log(`🔄 École changée: ${currentEcoleId} - ${ecoleName}`);
            
            // Recharger tous les filtres qui dépendent de l'école
            reloadAllFilters();
            
            showAlert(`École sélectionnée: ${ecoleName}`, 'success');
        });
    }
}

function reloadAllFilters() {
    console.log('🔄 Rechargement de tous les filtres après changement d\'école');
    
    // Recharger les classes pour l'export élèves
    if (document.getElementById('classeSelect')) {
        loadClasses();
    }
    
    // Recharger les filtres pour les bulletins
    if (document.getElementById('export_bulletins_classe_eleve')) {
        loadBulletinsFilters();
    }
    
    // Recharger les filtres pour les notes
    if (document.getElementById('export_notes_classe')) {
        loadNotesFilters();
    }
    
    // Recharger les filtres pour les moyennes
    if (document.getElementById('export_moyennes_classe')) {
        loadMoyennesFilters();
    }
}
// ======================= FONCTIONS POUR LA GESTION DES SEMESTRES =======================

// Fonction pour mettre à jour les options de période
function updatePeriodOptions(context) {
    const ecoleType = $(`#export_${context}_ecole_type`).val();
    const periodeSelect = $(`#export_${context}_periode`);
    
    periodeSelect.empty();
    
    if (ecoleType === 'college') {
        // Collège : trimestres
        for (let i = 1; i <= 3; i++) {
            periodeSelect.append(`<option value="${i}">Trimestre ${i}</option>`);
        }
        
        // Mettre à jour l'affichage
        $(`#${context}PeriodType`).text('Trimestre');
        $(`#${context}PeriodValue`).text('1');
    } else {
        // Lycée : semestres
        for (let i = 1; i <= 2; i++) {
            periodeSelect.append(`<option value="${i}">Semestre ${i}</option>`);
        }
        
        // Mettre à jour l'affichage
        $(`#${context}PeriodType`).text('Semestre');
        $(`#${context}PeriodValue`).text('1');
    }
}

// Fonction utilitaire pour afficher les erreurs
function showError(message) {
    // Vous pouvez utiliser un système de notification existant
    alert(message); // À remplacer par votre système de notification
}

function loadNotesFilters() {
    console.log('🔄 Chargement des filtres notes...');
    
    loadNotesClasses();
    loadNotesMatieres();
    loadNotesAnneesScolaires();
    
    // Initialiser les options de période
    updatePeriodOptions('notes');
}

function loadMoyennesFilters() {
    console.log('🔄 Chargement des filtres moyennes...');
    
    loadMoyennesClasses();
    loadMoyennesMatieres();
    loadMoyennesAnneesScolaires();
    loadMoyennesMentions();
    
    // Initialiser les options de période
    updatePeriodOptions('moyennes');
}

function exportNotes(format) {
    currentNotesExportFormat = format;
    
    const classeId = document.getElementById('export_notes_classe').value;
    const matiereId = document.getElementById('export_notes_matiere').value;
    const ecoleType = document.getElementById('export_notes_ecole_type').value;
    const periode = document.getElementById('export_notes_periode').value;
    const anneeScolaire = document.getElementById('export_notes_annee').value;
    
    // ✅ CORRECTION : Validation modifiée - la classe n'est plus obligatoire
    if (!periode) {
        showAlert('Veuillez sélectionner une période', 'warning');
        return;
    }
    
    if (!anneeScolaire) {
        showAlert('Veuillez sélectionner une année scolaire', 'warning');
        return;
    }
    
    console.log(`🚀 Export notes ${format} - Classe:${classeId}, Matière:${matiereId}, École:${ecoleType}, Période:${periode}, Année:${anneeScolaire}`);
    
    safeModalHide('notesExportModal');
    
    let url = `/services/export/notes?type=${format}`;
    // ✅ CORRECTION : Envoyer classe_id même si c'est "toutes"
    if (classeId) {
        url += `&classe_id=${classeId}`;
    }
    
    if (matiereId) url += `&matiere_id=${matiereId}`;
    url += `&ecole_type=${ecoleType}`;
    url += `&periode=${periode}`;
    url += `&annee_scolaire=${encodeURIComponent(anneeScolaire)}`;
    
    const ecoleId = getSelectedEcoleId();
    if (ecoleId) {
        url += `&ecole_id=${ecoleId}`;
    }
    
    console.log('🌐 Ouverture URL notes:', url);
    
    showAlert(`Export ${format.toUpperCase()} des notes en cours...`, 'info');
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error || `Erreur HTTP: ${response.status}`);
                });
            }
            return response.blob();
        })
        .then(blob => {
            if (blob.size === 0) {
                throw new Error('Le fichier exporté est vide');
            }
            
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            
            const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
            const extension = format === 'pdf' ? 'pdf' : 'xlsx';
            
            const classeSelect = document.getElementById('export_notes_classe');
            let classeNom = 'toutes_classes';
            if (classeId && classeId !== 'toutes') {
                classeNom = classeSelect.options[classeSelect.selectedIndex].text.replace(/[^a-zA-Z0-9]/g, '_');
            }
            
            const matiereSelect = document.getElementById('export_notes_matiere');
            let matiereNom = 'toutes_matieres';
            if (matiereId) {
                matiereNom = matiereSelect.options[matiereSelect.selectedIndex].text.replace(/[^a-zA-Z0-9]/g, '_');
            }
            
            const periodeSelect = document.getElementById('export_notes_periode');
            const periodeNom = periodeSelect.options[periodeSelect.selectedIndex].text.replace(/[^a-zA-Z0-9]/g, '_');
            
            a.download = `notes_${classeNom}_${matiereNom}_${periodeNom}_${timestamp}.${extension}`;
            
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            
            showAlert(`Export ${format.toUpperCase()} des notes réussi !`, 'success');
        })
        .catch(error => {
            console.error('❌ Erreur export notes:', error);
            showAlert(`Erreur lors de l'export: ${error.message}`, 'danger');
        });
}

// Fonction pour exporter les moyennes
function exportMoyennes(type) {
    const ecoleType = $('#export_moyennes_ecole_type').val();
    const periode = $('#export_moyennes_periode').val();
    const classeId = $('#export_moyennes_classe').val();
    const matiereId = $('#export_moyennes_matiere').val();
    const anneeScolaire = $('#export_moyennes_annee').val();
    const mention = $('#export_moyennes_mention').val();
    
    // Validation
    if (!periode) {
        showError('Veuillez sélectionner une période');
        return;
    }
    
    if (!classeId) {
        showError('Veuillez sélectionner une classe');
        return;
    }
    
    if (!anneeScolaire) {
        showError('Veuillez sélectionner une année scolaire');
        return;
    }
    
    // Construire l'URL
    let url = `/services/export/moyennes?type=${type}`;
    url += `&ecole_type=${encodeURIComponent(ecoleType)}`;
    url += `&periode=${encodeURIComponent(periode)}`;
    url += `&classe_id=${encodeURIComponent(classeId)}`;
    url += `&matiere_id=${encodeURIComponent(matiereId || '')}`;
    url += `&annee_scolaire=${encodeURIComponent(anneeScolaire)}`;
    url += `&mention=${encodeURIComponent(mention || '')}`;
    
    // Ouvrir dans une nouvelle fenêtre/télécharger
    window.open(url, '_blank');
    
    // Fermer le modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('moyennesExportModal'));
    modal.hide();
}


function updateBulletinsPeriodOptions() {
    const ecoleTypeSelect = document.getElementById('export_bulletins_ecole_type');
    const periodeSelect = document.getElementById('export_bulletins_periode');
    const periodTypeSpan = document.getElementById('bulletinPeriodType');
    
    if (!ecoleTypeSelect || !periodeSelect) return;
    
    const ecoleType = ecoleTypeSelect.value;
    console.log(`🔄 Mise à jour des options de période bulletins: école=${ecoleType}`);
    
    // Sauvegarder la valeur sélectionnée avant la mise à jour
    const savedValue = periodeSelect.value;
    
    let options = [];
    
    if (ecoleType === 'college') {
        // Collège : 3 trimestres
        options = [
            { value: '1', text: 'Trimestre 1' },
            { value: '2', text: 'Trimestre 2' },
            { value: '3', text: 'Trimestre 3' }
        ];
        
        // Mettre à jour l'affichage du type de période
        if (periodTypeSpan) {
            periodTypeSpan.textContent = 'Trimestre';
        }
    } else if (ecoleType === 'lycee') {
        // Lycée : 2 semestres
        options = [
            { value: '1', text: 'Semestre 1' },
            { value: '2', text: 'Semestre 2' }
        ];
        
        // Mettre à jour l'affichage du type de période
        if (periodTypeSpan) {
            periodTypeSpan.textContent = 'Semestre';
        }
    }
    
    // Mettre à jour le select
    periodeSelect.innerHTML = '';
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.value;
        optionElement.textContent = option.text;
        periodeSelect.appendChild(optionElement);
    });
    
    // Restaurer la valeur sélectionnée si elle existe
    if (savedValue && options.some(opt => opt.value === savedValue)) {
        periodeSelect.value = savedValue;
    } else {
        // Sinon, sélectionner la première option
        periodeSelect.value = options[0]?.value || '1';
    }
    
    console.log(`✅ Options de période bulletins mises à jour pour ${ecoleType}`);
}

// Remplacer les anciennes fonctions par celles-ci

function exportBulletinIndividuel() {
    const eleveId = document.getElementById('export_bulletins_eleve').value;
    const periode = document.getElementById('export_bulletins_periode').value;
    const anneeScolaire = document.getElementById('export_bulletins_annee').value;
    const ecoleType = document.getElementById('export_bulletins_ecole_type').value;
    const ecoleId = getSelectedEcoleId();
    
    // Validation
    if (!eleveId || !periode || !anneeScolaire) {
        showAlert('Veuillez remplir tous les champs obligatoires', 'warning');
        return;
    }
    
    let url = `/export/bulletin/individuel?eleve_id=${eleveId}&periode=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}`;
    url += `&ecole_type=${ecoleType}`;
    if (ecoleId) url += `&ecole_id=${ecoleId}`;
    
    // Téléchargement du bulletin
    downloadBulletin(url, 'individuel', periode, anneeScolaire, ecoleType);
}

function exportBulletinClasse() {
    const classeId = document.getElementById('export_bulletins_classe').value;
    const periode = document.getElementById('export_bulletins_periode').value;
    const anneeScolaire = document.getElementById('export_bulletins_annee').value;
    const ecoleType = document.getElementById('export_bulletins_ecole_type').value;
    const ecoleId = getSelectedEcoleId();
    
    // Validation
    if (!classeId || !periode || !anneeScolaire) {
        showAlert('Veuillez remplir tous les champs obligatoires', 'warning');
        return;
    }
    
    let url = `/export/bulletin/classe?classe_id=${classeId}&periode=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}`;
    url += `&ecole_type=${ecoleType}`;
    if (ecoleId) url += `&ecole_id=${ecoleId}`;
    
    // Téléchargement des bulletins
    downloadBulletin(url, 'classe', periode, anneeScolaire, ecoleType);
}

function exportBulletinToutesClasses() {
    const periode = document.getElementById('export_bulletins_periode').value;
    const anneeScolaire = document.getElementById('export_bulletins_annee').value;
    const ecoleType = document.getElementById('export_bulletins_ecole_type').value;
    const ecoleId = getSelectedEcoleId();
    
    // Validation
    if (!periode || !anneeScolaire) {
        showAlert('Veuillez remplir tous les champs obligatoires', 'warning');
        return;
    }
    
    let url = `/export/bulletin/toutes-classes?periode=${periode}&annee_scolaire=${encodeURIComponent(anneeScolaire)}`;
    url += `&ecole_type=${ecoleType}`;
    if (ecoleId) url += `&ecole_id=${ecoleId}`;
    
    // Téléchargement des bulletins
    downloadBulletin(url, 'toutes_classes', periode, anneeScolaire, ecoleType);
}

// REMPLACER ces 4 fonctions (si elles existent) par cette fonction unique :

function downloadBulletin(url, type, periode, anneeScolaire, ecoleType) {
    showAlert(`Génération des bulletins en cours...`, 'info');
    
    // S'assurer que l'URL contient ecole_type
    if (!url.includes('ecole_type=')) {
        url += `&ecole_type=${ecoleType}`;
    }
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error || `Erreur HTTP: ${response.status}`);
                });
            }
            return response.blob();
        })
        .then(blob => {
            if (blob.size === 0) {
                throw new Error('Le fichier généré est vide');
            }
            
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            
            // Génération du nom de fichier
            const periodePrefixe = ecoleType === 'lycee' ? 'S' : 'T';
            let filename = '';
            
            if (type === 'individuel') {
                filename = `bulletin_individuel_${periodePrefixe}${periode}_${anneeScolaire.replace('/', '-')}.pdf`;
            } else if (type === 'classe') {
                filename = `bulletins_classe_${periodePrefixe}${periode}_${anneeScolaire.replace('/', '-')}.pdf`;
            } else {
                filename = `bulletins_toutes_classes_${periodePrefixe}${periode}_${anneeScolaire.replace('/', '-')}.pdf`;
            }
            
            a.download = filename;
            
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            
            showAlert(`Export des bulletins réussi !`, 'success');
        })
        .catch(error => {
            console.error('❌ Erreur export bulletins:', error);
            showAlert(`Erreur lors de l'export: ${error.message}`, 'danger');
        });
}
// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM chargé - Initialisation des services d\'exportation');
    
    // Configurer les écouteurs pour la mise à jour des périodes
    const notesEcoleType = document.getElementById('export_notes_ecole_type');
    const moyennesEcoleType = document.getElementById('export_moyennes_ecole_type');
    
    if (notesEcoleType) {
        notesEcoleType.addEventListener('change', () => updatePeriodOptions('notes'));
    }
    if (moyennesEcoleType) {
        moyennesEcoleType.addEventListener('change', () => updatePeriodOptions('moyennes'));
    }
    
    // Initialiser le reste
    setupEcoleChangeListener();
    currentEcoleId = getSelectedEcoleId();
    console.log(`🏫 École initiale détectée: ${currentEcoleId}`);
    
    const modalElement = document.getElementById('classeSelectionModal');
    if (modalElement) {
        modalElement.addEventListener('show.bs.modal', function() {
            console.log('🎯 Modal ouvert - Chargement des classes déclenché');
            loadClasses();
        });
    } else {
        console.warn('⚠️ Modal classeSelectionModal non trouvé');
    }
    
    const ecoleSelect = document.getElementById('ecoleSelect');
    if (ecoleSelect) {
        ecoleSelect.addEventListener('change', function() {
            currentEcoleId = this.value;
            console.log(`🔄 École changée: ${currentEcoleId}`);
            showAlert(`École sélectionnée: ${this.options[this.selectedIndex].text}`, 'success');
        });
    }
    
    console.log('✅ Script d\'exportation initialisé avec gestion des périodes par type d\'établissement');
});

// ======================= EXPOSITION DES FONCTIONS GLOBALES =======================

window.exportEleves = exportEleves;
window.confirmElevesExport = confirmElevesExport;
window.exportEnseignants = exportEnseignants;
window.openNotesExportModal = openNotesExportModal;
window.exportNotes = exportNotes;
window.openMoyennesExportModal = openMoyennesExportModal;
window.exportMoyennes = exportMoyennes;
window.openBulletinsExportModal = openBulletinsExportModal;
window.exportBulletins = exportBulletins;
window.exportBulletinsCompact = exportBulletinsCompact; // AJOUT
window.openBulletinsCompactModal = openBulletinsCompactModal; // AJOUT
window.onClasseSelectChange = onClasseSelectChange;
window.openCustomExport = openCustomExport;
window.showComingSoon = showComingSoon;
window.updateBulletinsPeriodOptions = updateBulletinsPeriodOptions; // AJOUT

console.log('✅ Script services.js chargé avec succès - Version finale complète');
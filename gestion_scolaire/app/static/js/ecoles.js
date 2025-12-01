/**
 * GESTION DES ÉCOLES - SCRIPT PRINCIPAL
 * Organisation modulaire pour une meilleure maintenabilité
 * Version avec compatibilité
 */

// Vérification de la disponibilité de Bootstrap
function checkBootstrapDependencies() {
    if (typeof bootstrap === 'undefined') {
        console.warn('⚠️ Bootstrap non disponible - certaines fonctionnalités seront limitées');
        return false;
    }
    return true;
}

// Attendre que Bootstrap soit chargé
function waitForBootstrap(maxWait = 3000) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        
        function check() {
            if (checkBootstrapDependencies()) {
                resolve();
            } else if (Date.now() - startTime >= maxWait) {
                reject(new Error('Timeout attente de Bootstrap'));
            } else {
                setTimeout(check, 100);
            }
        }
        
        check();
    });
}

class EcolesManager {
    constructor() {
        this.pendingAction = null;
        
        // Initialisation avec gestion de compatibilité
        waitForBootstrap().then(() => {
            console.log('✅ Bootstrap chargé - initialisation des écoles');
            this.init();
        }).catch(err => {
            console.warn('⚠️ Initialisation sans Bootstrap:', err);
            this.init();
        });
    }

    // Dans la classe EcolesManager, méthode init()
    init() {
        // Attendre que le DOM soit complètement chargé
        setTimeout(() => {
            this.initializeTooltips();
            this.initializeActionConfirmations();
            this.initializeTableEvents();
            this.initializeForms();
            this.initializeValidation();
        }, 100);
    }

    // ========== INITIALISATIONS ==========

    initializeTooltips() {
        // Activer les tooltips seulement si Bootstrap est disponible
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(
                document.querySelectorAll('[data-bs-toggle="tooltip"]')
            );
            tooltipTriggerList.map(tooltipTriggerEl => 
                new bootstrap.Tooltip(tooltipTriggerEl)
            );
        }
    }

    initializeActionConfirmations() {
        const confirmYesBtn = document.getElementById('confirmYesBtn');
        const confirmModal = document.getElementById('confirmActionModal');

        if (!confirmYesBtn || !confirmModal) return;

        confirmYesBtn.addEventListener('click', () => this.executePendingAction());
        
        if (typeof bootstrap !== 'undefined') {
            confirmModal.addEventListener('hidden.bs.modal', () => {
                this.pendingAction = null;
            });
        } else {
            // Fallback pour la fermeture du modal
            confirmModal.addEventListener('click', (e) => {
                if (e.target === confirmModal || e.target.classList.contains('btn-close')) {
                    this.pendingAction = null;
                    confirmModal.style.display = 'none';
                }
            });
        }
    }

    initializeTableEvents() {
        const table = document.getElementById('table-ecoles');
        if (!table) return;

        table.addEventListener('click', (e) => this.handleTableClick(e));
    }

    initializeForms() {
        this.initializeAddForm();
        this.initializeEditForm();
        this.initializeDeleteForm();
    }

    initializeValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormValidation(e, form));
        });

        this.initializeCustomValidation();
    }

    // ========== GESTION DES ÉVÉNEMENTS ==========

    handleTableClick(e) {
        const handlers = {
            'btnEco-edit': (btn) => this.editEcole(btn.dataset.id),
            'btnEco-detail': (btn) => this.showEcoDetail(btn.dataset.id),
            'btnEco-danger': (btn) => this.confirmDeleteEcole(btn.dataset.id)
        };

        for (const [className, handler] of Object.entries(handlers)) {
            const button = e.target.closest(`.${className}`);
            if (button) {
                handler(button);
                break;
            }
        }
    }

    handleFormValidation(event, form) {
        if (!this.validateForm(form) || !form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    }

    // ========== VALIDATION PERSONNALISÉE ==========

    initializeCustomValidation() {
        this.initializePhoneValidation();
        this.initializeEmailValidation();
    }

    initializePhoneValidation() {
        const phoneInputs = document.querySelectorAll('input[type="tel"]');
        phoneInputs.forEach(input => {
            input.addEventListener('input', () => this.validatePhoneFormat(input));
            input.addEventListener('blur', () => this.validatePhoneFormat(input));
        });
    }

    initializeEmailValidation() {
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('input', () => this.validateEmailFormat(input));
            input.addEventListener('blur', () => this.validateEmailFormat(input));
        });
    }

    validatePhoneFormat(input) {
        const value = input.value.trim();
        if (!value) {
            this.clearValidation(input);
            return true;
        }

        const phoneRegex = /^\+\d{1,3}[\s\d]{7,15}$/;
        const cleanedValue = value.replace(/\s/g, '');
        
        if (phoneRegex.test(value) || /^\+\d{8,15}$/.test(cleanedValue)) {
            this.setValid(input);
            return true;
        } else {
            this.setInvalid(input, 'Format invalide. Utilisez le format international: +228 XX XX XX XX');
            return false;
        }
    }

    validateEmailFormat(input) {
        const value = input.value.trim();
        if (!value) {
            this.clearValidation(input);
            return true;
        }

        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (emailRegex.test(value)) {
            this.setValid(input);
            return true;
        } else {
            this.setInvalid(input, 'Format d\'email invalide');
            return false;
        }
    }

    // ========== HELPERS DE VALIDATION ==========

    setValid(input) {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    }

    setInvalid(input, message) {
        input.setCustomValidity(message);
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
    }

    clearValidation(input) {
        input.setCustomValidity('');
        input.classList.remove('is-valid', 'is-invalid');
    }

    validateForm(form) {
        let isValid = true;
        
        const phoneInputs = form.querySelectorAll('input[type="tel"]');
        phoneInputs.forEach(input => {
            if (!this.validatePhoneFormat(input)) isValid = false;
        });

        const emailInputs = form.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            if (!this.validateEmailFormat(input)) isValid = false;
        });

        return isValid;
    }

    // ========== GESTION DES ACTIONS ==========

    confirmAction(message, actionCallback) {
        const confirmModal = document.getElementById('confirmActionModal');
        const confirmMessage = document.getElementById('confirmMessage');

        if (!confirmModal || !confirmMessage) {
            actionCallback?.();
            return;
        }

        confirmMessage.textContent = message;
        this.pendingAction = actionCallback;

        // Afficher la modal selon la disponibilité de Bootstrap
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Modal(confirmModal).show();
        } else {
            confirmModal.style.display = 'block';
        }
    }

    executePendingAction() {
        if (this.pendingAction && typeof this.pendingAction === 'function') {
            this.pendingAction();
        }
        
        const confirmModal = document.getElementById('confirmActionModal');
        // Fermer la modal selon la disponibilité de Bootstrap
        if (typeof bootstrap !== 'undefined') {
            bootstrap.Modal.getInstance(confirmModal)?.hide();
        } else {
            confirmModal.style.display = 'none';
        }
        this.pendingAction = null;
    }

    // ========== NOTIFICATIONS ==========

    showNotification(message, type = 'success', delay = 3000) {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-bg-${type} border-0`;
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast"></button>
            </div>
        `;

        container.appendChild(toastEl);
        
        // Utiliser Bootstrap Toast si disponible, sinon fallback simple
        if (typeof bootstrap !== 'undefined') {
            const toast = new bootstrap.Toast(toastEl, { delay });
            toast.show();
        } else {
            toastEl.style.display = 'block';
            setTimeout(() => {
                if (toastEl.parentNode) {
                    toastEl.remove();
                }
            }, delay);
        }

        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    // ========== GESTION AJOUT ==========

    initializeAddForm() {
        const form = document.getElementById('addEcoForm');
        if (!form) return;

        form.addEventListener('submit', (e) => this.handleAddSubmit(e));
    }

    async handleAddSubmit(e) {
        e.preventDefault();
        const form = e.target;
        form.classList.add('was-validated');
        
        if (!this.validateForm(form) || !form.checkValidity()) return;

        try {
            const formData = new FormData(form);
            const data = await this.handleApiCall('/admin/ecoles/add', { 
                method: 'POST', 
                body: formData 
            });

            // Fermer la modal selon la disponibilité de Bootstrap
            if (typeof bootstrap !== 'undefined') {
                bootstrap.Modal.getInstance(document.getElementById('addEcoModal'))?.hide();
            } else {
                document.getElementById('addEcoModal').style.display = 'none';
            }
            
            this.showNotification(data.message || 'École ajoutée avec succès');
            setTimeout(() => location.reload(), 1500);
            
        } catch (error) {
            console.error('Erreur ajout école:', error);
            this.showNotification(
                error.message || 'Erreur lors de l\'ajout de l\'école', 
                'danger'
            );
        }
    }

    // ========== GESTION ÉDITION ==========

    async editEcole(id) {
        try {
            const res = await fetch(`/admin/ecoles/get/${id}`);
            if (!res.ok) throw new Error('Erreur de récupération');
            
            const data = await res.json();
            this.openEditModal(data);
        } catch (error) {
            console.error('Erreur édition école:', error);
            this.showNotification('Erreur lors de la récupération des données', 'danger');
        }
    }

    openEditModal(ecole) {
        const fields = {
            'editEco_id': ecole.id,
            'editEco_code': ecole.code,
            'editEco_nom': ecole.nom,
            'editEco_localite': ecole.localite,
            'editEco_dre': ecole.dre,
            'editEco_site': ecole.site,
            'editEco_email': ecole.email,
            'editEco_telephone1': ecole.telephone1,
            'editEco_telephone2': ecole.telephone2,
            'editEco_devise': ecole.devise,
            'editEco_inspection': ecole.inspection,
            'editEco_boite_postale': ecole.boite_postale,
            'editEco_prefecture': ecole.prefecture,
            'editEco_chef_etablissement_nom': ecole.chef_etablissement_nom,
            'editEco_chef_etablissement_titre': ecole.chef_etablissement_titre,
            'editEco_chef_etablissement_civilite': ecole.chef_etablissement_civilite
        };

        Object.entries(fields).forEach(([fieldId, value]) => {
            const element = document.getElementById(fieldId);
            if (element) element.value = value || '';
        });

        // Gestion de l'aperçu du logo
        const logoPreview = document.getElementById('editEco_logo_preview');
        if (logoPreview) {
            if (ecole.logo_filename) {
                logoPreview.style.display = 'block';
                const logoImg = logoPreview.querySelector('img');
                if (logoImg) {
                    logoImg.src = `/static/logos/${ecole.logo_filename}`;
                    logoImg.alt = `Logo ${ecole.nom}`;
                }
            } else {
                logoPreview.style.display = 'none';
            }
        }

        // Afficher la modal selon la disponibilité de Bootstrap
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Modal(document.getElementById('editEcoModal')).show();
        } else {
            document.getElementById('editEcoModal').style.display = 'block';
        }
    }

    initializeEditForm() {
        const form = document.getElementById('editEcoForm');
        if (!form || form.dataset.listenerAttached) return;

        form.dataset.listenerAttached = 'true';
        form.addEventListener('submit', (e) => this.handleEditSubmit(e));
    }

    async handleEditSubmit(e) {
        e.preventDefault();
        const form = e.target;
        
        if (!this.validateForm(form) || !form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }

        const id = document.getElementById('editEco_id').value;
        const formData = new FormData(form);

        try {
            const res = await fetch(`/admin/ecoles/update/${id}`, { 
                method: 'POST', 
                body: formData 
            });
            const updatedData = await res.json();

            if (!res.ok) {
                this.showNotification(updatedData.error || 'Erreur lors de la modification', 'danger');
                return;
            }

            this.updateTableRow(id, updatedData);
            
            // Fermer la modal selon la disponibilité de Bootstrap
            if (typeof bootstrap !== 'undefined') {
                bootstrap.Modal.getInstance(document.getElementById('editEcoModal'))?.hide();
            } else {
                document.getElementById('editEcoModal').style.display = 'none';
            }
            this.showNotification('École modifiée avec succès');
        } catch (error) {
            console.error('Erreur modification école:', error);
            this.showNotification('Erreur serveur', 'danger');
        }
    }

    // ========== MISE À JOUR DU TABLEAU ==========

    updateTableRow(id, data) {
        const row = document.querySelector(`tr[data-id="ecole-${id}"]`);
        if (!row) return;

        const fieldMappings = {
            '.col-code': data.code,
            '.col-nom': data.nom,
            '.col-localite': data.localite,
            '.col-site': data.site,
            '.col-email': data.email,
            '.col-telephone1': data.telephone1,
            '.col-telephone2': data.telephone2,
            '.col-dre': data.dre,
            '.col-prefecture': data.prefecture,
            '.col-devise': data.devise,
            '.col-inspection': data.inspection,
            '.col-boite_postale': data.boite_postale
        };

        Object.entries(fieldMappings).forEach(([selector, value]) => {
            const element = row.querySelector(selector);
            if (element) element.textContent = value || '';
        });

        // Mise à jour du logo
        const logoCell = row.querySelector('.col-logo');
        if (logoCell) {
            if (data.logo_filename) {
                logoCell.innerHTML = `
                    <img src="/static/logos/${data.logo_filename}" 
                         alt="Logo ${data.nom}" 
                         class="img-thumbnail" 
                         style="max-height: 40px; max-width: 40px; object-fit: contain;">
                `;
            } else {
                logoCell.innerHTML = `
                    <div class="text-muted text-center">
                        <i class="bi bi-building" style="font-size: 1.5rem;"></i>
                    </div>
                `;
            }
        }
    }

    // ========== GESTION SUPPRESSION ==========

    confirmDeleteEcole(id) {
        this.confirmAction(
            'Voulez-vous vraiment supprimer cette école ? Cette action est irréversible.',
            () => this.deleteEcoleConfirmed(id)
        );
    }

    async deleteEcoleConfirmed(id) {
        try {
            const res = await fetch(`/admin/ecoles/delete/${id}`, { method: 'POST' });
            
            if (res.ok) {
                this.showNotification('École supprimée avec succès');
                const row = document.querySelector(`tr[data-id="ecole-${id}"]`);
                row ? row.remove() : location.reload();
            } else {
                const data = await res.json();
                this.showNotification(data.error || 'Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            console.error('Erreur suppression école:', error);
            this.showNotification('Erreur serveur lors de la suppression', 'danger');
        }
    }

    initializeDeleteForm() {
        const form = document.getElementById('deleteEcoForm');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const id = document.getElementById('deleteEco_id').value;
            this.confirmDeleteEcole(id);
        });
    }

    // ========== GESTION DÉTAILS ==========

    async showEcoDetail(id) {
        try {
            const res = await fetch(`/admin/ecoles/detail/${id}`);
            if (!res.ok) throw new Error('Erreur de récupération');
            
            const data = await res.json();
            this.displayDetailModal(data);
        } catch (error) {
            console.error('Erreur détail école:', error);
            this.showNotification('Erreur lors de la récupération des détails', 'danger');
        }
    }

    displayDetailModal(data) {
        const detailContent = document.getElementById('detailEcoContent');
        if (!detailContent) return;

        const logoHtml = data.logo_filename 
            ? `<div class="text-center mb-3">
                  <img src="/static/logos/${data.logo_filename}" 
                       alt="Logo ${data.nom}" 
                       class="img-fluid rounded" 
                       style="max-height: 120px;">
               </div>`
            : '<div class="text-center mb-3 text-muted"><i class="bi bi-building" style="font-size: 3rem;"></i></div>';

        const content = `
            ${logoHtml}
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Code:</strong> ${data.code || 'Non renseigné'}</p>
                    <p><strong>Nom:</strong> ${data.nom || 'Non renseigné'}</p>
                    <p><strong>Localité:</strong> ${data.localite || 'Non renseigné'}</p>
                    <p><strong>Site Web:</strong> ${data.site ? `<a href="${data.site}" target="_blank">${data.site}</a>` : 'Non renseigné'}</p>
                    <p><strong>Email:</strong> ${data.email ? `<a href="mailto:${data.email}">${data.email}</a>` : 'Non renseigné'}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Téléphone 1:</strong> ${data.telephone1 || 'Non renseigné'}</p>
                    <p><strong>Téléphone 2:</strong> ${data.telephone2 || 'Non renseigné'}</p>
                    <p><strong>DRE:</strong> ${data.dre || 'Non renseigné'}</p>
                    <p><strong>B.P:</strong> ${data.boite_postale || 'Non renseigné'}</p>
                    <p><strong>IESG:</strong> ${data.inspection || 'Non renseigné'}</p>
                    <p><strong>Préfecture:</strong> ${data.prefecture || 'Non renseigné'}</p>
                    <p><strong>Devise:</strong> ${data.devise || 'Non renseigné'}</p>
                </div>
            </div>
        `;

        detailContent.innerHTML = content;
        
        // Afficher la modal selon la disponibilité de Bootstrap
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Modal(document.getElementById('detailEcoModal')).show();
        } else {
            document.getElementById('detailEcoModal').style.display = 'block';
        }
    }

    // Ajouter cette méthode dans la classe EcolesManager
    async handleApiCall(url, options = {}) {
        try {
            console.log('🔍 Envoi de la requête vers:', url);
            const res = await fetch(url, options);
            
            // Vérifier si la réponse est du HTML au lieu du JSON
            const contentType = res.headers.get('content-type');
            if (contentType && contentType.includes('text/html')) {
                const text = await res.text();
                console.error('❌ Réponse HTML reçue au lieu de JSON:', text.substring(0, 500));
                
                // Essayer de détecter si c'est une page d'erreur 404
                if (text.includes('404 Not Found') || text.includes('Not Found')) {
                    throw new Error(`Route non trouvée (404): ${url}. Vérifiez l'enregistrement du blueprint Flask.`);
                }
                
                throw new Error('Erreur de serveur - réponse au format incorrect');
            }
            
            const data = await res.json();
            
            if (!res.ok) {
                throw new Error(data.error || `Erreur HTTP ${res.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('❌ Erreur API:', error);
            throw error;
        }
    }
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    new EcolesManager();
});
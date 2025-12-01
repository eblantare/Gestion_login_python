document.addEventListener("DOMContentLoaded", function(){
    const form = document.getElementById("registerForm");
    
    // === BLOCAGE PHYSIQUE DE LA SAISIE POUR LE TÉLÉPHONE ===
    const telephoneInput = form.querySelector('input[name="telephone"]');
    
    // Empêcher la saisie de caractères non autorisés
    telephoneInput.addEventListener('keydown', function(e) {
        // Autoriser: chiffres (0-9), backspace, delete, tab, flèches, home, end
        const allowedKeys = [
            'Backspace', 'Delete', 'Tab', 'ArrowLeft', 'ArrowRight', 
            'Home', 'End', 'Enter'
        ];
        
        // Autoriser le + seulement au début
        if (e.key === '+' && telephoneInput.selectionStart === 0) {
            return true; // Autoriser le + au début
        }
        
        // Autoriser les chiffres
        if (/^\d$/.test(e.key)) {
            return true;
        }
        
        // Autoriser les touches de contrôle
        if (allowedKeys.includes(e.key)) {
            return true;
        }
        
        // Bloquer toutes les autres touches
        e.preventDefault();
        return false;
    });
    
    // Validation en temps réel supplémentaire
    telephoneInput.addEventListener('input', function(e) {
        let value = e.target.value;
        
        // Nettoyer la valeur (au cas où via copier-coller)
        let cleaned = value.replace(/[^\d+]/g, '');
        
        // S'assurer qu'il n'y a qu'un seul + au début
        if (cleaned.startsWith('+')) {
            cleaned = '+' + cleaned.substring(1).replace(/\+/g, '');
        }
        
        // Limiter la longueur
        if (cleaned.length > 16) {
            cleaned = cleaned.substring(0, 16);
        }
        
        // Mettre à jour la valeur si nécessaire
        if (value !== cleaned) {
            e.target.value = cleaned;
        }
        
        // Valider le champ
        validateField(e.target);
    });

    // === VALIDATION EN TEMPS RÉEL POUR TOUS LES CHAMPS ===
    const inputs = form.querySelectorAll('input[required], select[required]');
    inputs.forEach(input => {
        // Validation à chaque frappe
        input.addEventListener('input', function() {
            validateField(this);
        });
        
        // Validation quand on quitte le champ
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        // Validation initiale
        if (input.value.trim() !== '') {
            validateField(input);
        }
    });

    // === FONCTION DE VALIDATION PRINCIPALE ===
    function validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        switch(field.name) {
            case 'nom':
                if (value.length < 2) {
                    isValid = false;
                    errorMessage = "Le nom doit contenir au moins 2 caractères";
                }
                break;
                
            case 'prenoms':
                if (value.length < 2) {
                    isValid = false;
                    errorMessage = "Le prénom doit contenir au moins 2 caractères";
                }
                break;
                
            case 'username':
                if (value.length < 3) {
                    isValid = false;
                    errorMessage = "Le nom d'utilisateur doit contenir au moins 3 caractères";
                } else if (!/^[a-zA-Z0-9_.-]+$/.test(value)) {
                    isValid = false;
                    errorMessage = "Caractères autorisés: lettres, chiffres, . _ -";
                }
                break;
                
            case 'telephone':
                const phonePattern = /^\+?\d{8,15}$/;
                if (value.length > 0) {
                    if (!phonePattern.test(value)) {
                        isValid = false;
                        if (value.length < 8) {
                            errorMessage = "Le numéro doit avoir au moins 8 chiffres";
                        } else if (value.length > 15) {
                            errorMessage = "Le numéro est trop long (max 15 chiffres)";
                        } else if (!/^\d+$/.test(value.replace('+', ''))) {
                            errorMessage = "Seuls les chiffres sont autorisés";
                        } else {
                            errorMessage = "Format invalide. Exemple: +22812345678 ou 01234567";
                        }
                    }
                }
                break;
                
            case 'email':
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (value.length > 0 && !emailPattern.test(value)) {
                    isValid = false;
                    if (!value.includes('@')) {
                        errorMessage = "L'email doit contenir @";
                    } else if (!value.includes('.')) {
                        errorMessage = "L'email doit contenir un domaine (.com, .fr, etc.)";
                    } else {
                        errorMessage = "Format d'email invalide. Exemple: exemple@domain.com";
                    }
                }
                break;
                
            case 'password':
                const strongPassword = /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
                if (value.length > 0) {
                    if (!strongPassword.test(value)) {
                        isValid = false;
                        if (value.length < 8) {
                            errorMessage = "8 caractères minimum requis";
                        } else if (!/(?=.*[A-Z])/.test(value)) {
                            errorMessage = "Au moins 1 majuscule requise";
                        } else if (!/(?=.*\d)/.test(value)) {
                            errorMessage = "Au moins 1 chiffre requis";
                        } else if (!/(?=.*[^A-Za-z0-9])/.test(value)) {
                            errorMessage = "Au moins 1 caractère spécial requis (!@#$%^&* etc.)";
                        } else {
                            errorMessage = "Mot de passe trop faible";
                        }
                    }
                }
                break;
                
            case 'role':
            case 'ecole_id':
                if (value === "") {
                    isValid = false;
                    errorMessage = "Ce champ est obligatoire";
                }
                break;
        }

        // Mise à jour visuelle du champ
        updateFieldValidation(field, isValid, errorMessage);
        
        // Vérifier si le formulaire peut être soumis
        updateSubmitButton();
    }

    function updateFieldValidation(field, isValid, errorMessage) {
        // Supprimer les états précédents
        field.classList.remove('is-valid', 'is-invalid');
        
        // Supprimer les messages d'erreur existants
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Si le champ est vide et obligatoire
        if (field.value.trim() === '' && field.hasAttribute('required')) {
            field.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-danger small mt-1';
            errorDiv.textContent = "Ce champ est obligatoire";
            field.parentNode.appendChild(errorDiv);
            return;
        }
        
        // Ne pas valider les champs vides non obligatoires
        if (field.value.trim() === '') {
            return;
        }
        
        // Appliquer les styles de validation
        if (isValid) {
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
            // Afficher un message d'erreur contextuel
            if (errorMessage) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'field-error text-danger small mt-1';
                errorDiv.textContent = errorMessage;
                field.parentNode.appendChild(errorDiv);
            }
        }
    }

    function updateSubmitButton() {
        const submitBtn = form.querySelector('button[type="submit"]');
        const invalidFields = form.querySelectorAll('.is-invalid');
        const requiredFields = form.querySelectorAll('[required]');
        
        // Vérifier si tous les champs requis sont valides
        let allValid = true;
        requiredFields.forEach(field => {
            if (field.value.trim() === '' || field.classList.contains('is-invalid')) {
                allValid = false;
            }
        });
        
        // Vérifier aussi le sexe (boutons radio)
        const sexeSelected = form.querySelector('input[name="sexe"]:checked');
        if (!sexeSelected) {
            allValid = false;
        }
        
        // Activer/désactiver le bouton
        if (allValid && invalidFields.length === 0) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-success');
        } else {
            submitBtn.disabled = true;
            submitBtn.classList.remove('btn-success');
            submitBtn.classList.add('btn-secondary');
        }
    }

    // === VALIDATION DES BOUTONS RADIO (sexe) ===
    const sexeInputs = form.querySelectorAll('input[name="sexe"]');
    sexeInputs.forEach(input => {
        input.addEventListener('change', function() {
            updateSubmitButton();
        });
    });

    // === VALIDATION À LA SOUMISSION (sécurité) ===
    form.addEventListener("submit", function(e){
        let errors = [];

        // Récupération des valeurs
        let nom = form.nom.value.trim();
        let prenoms = form.prenoms.value.trim();
        let sexe = form.querySelector('input[name="sexe"]:checked');
        sexe = sexe ? sexe.value.trim() : "";
        let username = form.username.value.trim();
        let telephone = form.telephone.value.trim();
        let email = form.email.value.trim();
        let password = form.password.value.trim();
        let role = form.role.value.trim();
        let ecole_id = form.ecole_id ? form.ecole_id.value.trim() : "";

        // Double vérification (sécurité)
        let phonePattern = /^\+?\d{8,15}$/;
        if (!phonePattern.test(telephone)){
            errors.push("❌ Numéro de téléphone invalide. Format: +22812345678");
        }

        let emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(email)){
            errors.push("❌ Format d'email invalide. Exemple: exemple@domain.com");
        }

        let strongPassword = /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
        if (!strongPassword.test(password)){
            errors.push("❌ Mot de passe trop faible : 8 caractères minimum, 1 majuscule, 1 chiffre, 1 caractère spécial.");
        }

        if (!sexe) errors.push("❌ Veuillez sélectionner le sexe!");
        if (!role) errors.push("❌ Veuillez sélectionner un rôle");
        if (!ecole_id) errors.push("❌ Veuillez sélectionner une école");

        // Affichage des erreurs
        let errorContainer = document.getElementById("formErrors");
        errorContainer.innerHTML = "";
        
        if (errors.length > 0){
            e.preventDefault();
            errors.forEach(err => {
                let li = document.createElement("li");
                li.textContent = err;
                li.classList.add("text-danger", "fw-semibold");
                errorContainer.appendChild(li);
            });
            errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });

    // === VALIDATION INITIALE ===
    updateSubmitButton();
});
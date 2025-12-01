document.addEventListener("DOMContentLoaded", function(){
    const form = document.getElementById("registerForm");
    
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
    });

    // === FONCTION DE VALIDATION PRINCIPALE ===
    function validateField(field) {
        const value = field.value.trim();
        let isValid = field.checkValidity();
        let errorMessage = field.validationMessage;

        // Messages d'erreur personnalisés
        if (!isValid && field.name === 'telephone') {
            errorMessage = "❌ Format invalide. Exemple: +22812345678 (chiffres uniquement)";
        }
        if (!isValid && field.name === 'password') {
            errorMessage = "❌ 8 caractères min, 1 majuscule, 1 chiffre, 1 caractère spécial";
        }
        if (!isValid && field.name === 'email') {
            errorMessage = "❌ Format: exemple@domain.com";
        }

        // Mise à jour visuelle
        updateFieldValidation(field, isValid, errorMessage);
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
        
        if (isValid && field.value.trim() !== '') {
            field.classList.add('is-valid');
        } else if (!isValid && field.value.trim() !== '') {
            field.classList.add('is-invalid');
            if (errorMessage) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'field-error';
                errorDiv.textContent = errorMessage;
                field.parentNode.appendChild(errorDiv);
            }
        }
    }

    function updateSubmitButton() {
        const submitBtn = form.querySelector('button[type="submit"]');
        const isFormValid = form.checkValidity();
        
        submitBtn.disabled = !isFormValid;
        submitBtn.classList.toggle('btn-success', isFormValid);
        submitBtn.classList.toggle('btn-secondary', !isFormValid);
    }

    // Validation initiale
    updateSubmitButton();
});
document.addEventListener("DOMContentLoaded", function(){
    const form = document.querySelector(".register-form");
    if(!form) return;
    const emailInput = form.querySelector("input[name='email']");
    const phoneInput = form.querySelector("input[name='telephone']");
    const passwordInput = form.querySelector("input[name='password']");

    const emailRegex = /^[\w\.-]+@[\w\.-]+\.\w+$/;
    const phoneRegex = /^\+?\d{8,15}$/;
    const passwordRegex = /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

    function showError(input,message){
        let group = input.closest(".form-group");
        let error = group.querySelector(".form-error");
        let icon = group.querySelector(".validation-icon");

        if(!error){
            error = document.createElement("div");
            error.classList.add("form-error","text-danger","small","mt-1");
            group.appendChild(error);
        }
        error.textContent = message;
        if(icon){
            icon.innerHTML = "❌";
            icon.style.color = "red";
        }
        input.classList.add("is-invalid");
        input.classList.remove("is-valid");
    }
    function showSuccess(input){
        let group = input.closest(".form-group");
        let error = group.querySelector(".form-error");
        let icon = group.querySelector(".validation-icon");

        if (error) error.textContent = "";
        if (icon){
            icon.innerHTML = "✅";
            icon.style.color = "green";
        }
        input.classList.add("is-valid");
        input.classList.remove("is-invalid");
    }

    function validateEmail(){
        if (!emailRegex.test(emailInput.value.trim())){
            showError(emailInput, "Format d'email invalide.");
            return false;
        }
        showSuccess(emailInput)
           return true;
       
    }

    function validatePhone(){
        if (!phoneRegex.test(phoneInput.value.trim())){
            showError(phoneInput,"Numéro de téléphone invalide");
            return false;
        }
        showSuccess(phoneInput);
        return true;
    }
    function validatePassword(){
        if (!passwordRegex.test(passwordInput.value.trim())){
            showError(passwordInput, "Mot de passe invalide");
            return false;
        }
        showSuccess(passwordInput);
        return true;
    }
    emailInput.addEventListener("input", validateEmail);
    phoneInput.addEventListener("input", validatePhone);
    passwordInput.addEventListener("input", validatePassword);

    form.addEventListener("submit", function(e){
        let valid = true;
        if (!validateEmail()) valid = false;
        if( !validatePhone()) valid = false;    
        if ( !validatePassword()) valid = false;
        if( !valid) e.preventDefault();
    });
});
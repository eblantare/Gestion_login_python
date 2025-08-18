document.addEventListener("DOMContentLoaded", function(){
    const passwordInput = document.getElementById("password");
    const passwordHelp = document.getElementById("passwordHelp");
    
    passwordInput.addEventListener('input', () =>{
        const value = passwordInput.value;

        //Expression régulière, au moins 1 majuscule, 1 chiffre et 1 caractère spécial
        const regex = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).+$/;
        if(regex.test(value) || value === "" ){
           passwordHelp.style.display = 'none';
        }else{
            passwordHelp.style.display = 'block';
            passwordHelp.style.color = 'red';
        }

    });

});
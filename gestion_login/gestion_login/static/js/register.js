document.addEventListener("DOMContentLoaded", function(){
    const form =document.getElementById("registerForm");
    form.addEventListener("submit", function(e){
      let nom = form.nom.value.trim();
      let prenoms = form.prenoms.value.trim();
      let sexe = form.querySelector('input[name ="sexe"]:checked');
      sexe =sexe ? sexe.value.trim() :"";
      let username = form.username.value.trim();
      let telephone = form.telephone.value.trim();
      let email = form.email.value.trim();
      let password = form.password.value.trim();
      let role = form.role.value.trim();
      let photo = form.photo.value;

      let errors = [];

      //vérif nom
      if(nom.length < 2){
        errors.push("Le nom doit contenir au moins deux caractères");
      }

      //vérif prénoms
      if(prenoms.length < 2){
        errors.push("Le prénoms doit contenir au moins deux caractères.");
      }
        //Verif sexe
      if(sexe == ""){
        errors.push("Veuillez sélectionner le sexe!");
      }
      //vérif username
      if(username.length < 3){
        errors.push("Le nom d'utilisateur doit avoir au moins 3 caractères");
      }

      //Vérif téléphone
      let phonePattern = /^\+?\d{8,15}$/;
      if (!phonePattern.test(telephone)){
        errors.push("Numéro de téléphone invalide")
      }

      //Vérif email
      let emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(email)){
        errors.push("L'adresse email est invalide");
      }

    // verif password
    let strongPassword = /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
    if ( !strongPassword.test(password)){
        errors.push("Mot de passe trop faible : 8 caractères minimum, 1 majuscule, 1 chiffre, 1 caractère spécial.");
    }
    //vérif role
    if (role === ""){
        errors.push("Veuillez sélectionner un role....");
    }

    //vérif photo
     if (photo){
        let allowedExtensions = /\.(jpg|jpeg|png|gif)$/i;
        if (!allowedExtensions.test(photo)){
            errors.push("Format d'image invalide (jpg, jpeg, png, gif uniquement).");
        }

     }

     //Affichage des erreurs
     let errorContainer = document.getElementById("formErrors");
     errorContainer.innerHTML = "";
     if (errors.length > 0){
        e.preventDefault();
        errors.forEach(err => {
            let li = document.createElement("li");
            li.textContent = err;
            li.classList.add("text-danger");
            errorContainer.appendChild(li);
        });
     }
    });
});
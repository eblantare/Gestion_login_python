document.addEventListener('DOMContentLoaded',() =>{
    const alerts = document.querySelectorAll('#flash-messages .alert');
    alerts.forEach(alert =>{
            setTimeout(() =>{
                alert.style.opacity='0' ;
                setTimeout(() =>{
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            },500);
        },4000);
    });
});


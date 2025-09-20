
document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll('.menu-card');

    cards.forEach(card => {
        card.addEventListener('click', (e) => {
            // éviter que le clic sur un sous-menu déclenche une redirection
            if (e.target.closest('.menu-submenu a')) return;

            const url = e.currentTarget.dataset.url; // toujours la carte
            if (url && url !== '#') {
                window.location.href = url;
            }
        });
    });
});
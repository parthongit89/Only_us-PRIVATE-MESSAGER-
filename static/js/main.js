// OnlyUs Global Interactive JS
document.addEventListener('DOMContentLoaded', () => {
    // Drawer sidebar menu toggle
    const menuBtn = document.getElementById('menuToggleBtn');
    const drawer = document.getElementById('sideDrawer');
    const overlay = document.getElementById('drawerOverlay');

    if (menuBtn && drawer && overlay) {
        menuBtn.addEventListener('click', () => {
            drawer.classList.add('open');
            overlay.classList.add('active');
        });

        overlay.addEventListener('click', () => {
            drawer.classList.remove('open');
            overlay.classList.remove('active');
        });
    }

    // Auto-dismiss alerts after 4 seconds
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 4000);
    });
});

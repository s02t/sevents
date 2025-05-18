window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

});

// Fix chart sizing issues for the entire application
function fixChartSizing() {
    // Wait for Chart.js to be loaded
    if (typeof Chart !== 'undefined') {
        // Set global defaults for all charts
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        
        // Add resize listener to handle chart resizing properly
        window.addEventListener('resize', function() {
            // Resize all chart instances
            if (Chart.instances) {
                Object.keys(Chart.instances).forEach(function(key) {
                    if (Chart.instances[key]) {
                        Chart.instances[key].resize();
                    }
                });
            }
        });
        
        // Apply resize on initial load to ensure proper sizing
        setTimeout(function() {
            if (Chart.instances) {
                Object.keys(Chart.instances).forEach(function(key) {
                    if (Chart.instances[key]) {
                        Chart.instances[key].resize();
                    }
                });
            }
        }, 300);
    }
}

// Run on document ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltips.length > 0) {
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
    
    // Initialize popovers
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    if (popovers.length > 0) {
        popovers.forEach(popover => {
            new bootstrap.Popover(popover);
        });
    }
    
    // Fix chart sizing issues
    fixChartSizing();
});


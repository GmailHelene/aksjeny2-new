/**
 * Mobile Navigation Fix
 * - Fixes stuck/hanging dropdowns on mobile
 * - Ensures smooth dropdown transitions
 * - Cleans up state after closing
 */

document.addEventListener('DOMContentLoaded', () => {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    const dropdowns = document.querySelectorAll('.navbar-nav .dropdown');
    
    // Close other dropdowns when one is opened
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        toggle.addEventListener('click', (e) => {
            // Prevent ghost clicks
            e.stopPropagation();
            
            // Close other dropdowns
            dropdowns.forEach(other => {
                if (other !== dropdown && other.classList.contains('show')) {
                    other.querySelector('.dropdown-menu').classList.remove('show');
                    other.classList.remove('show');
                }
            });
        });
        
        // Clean up on dropdown hidden
        menu.addEventListener('hidden.bs.dropdown', () => {
            menu.style.transform = '';
            menu.style.transition = '';
        });
    });
    
    // Clean up when mobile menu is closed
    navbarCollapse.addEventListener('hidden.bs.collapse', () => {
        // Close all dropdowns
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('show');
            const menu = dropdown.querySelector('.dropdown-menu');
            if (menu) {
                menu.classList.remove('show');
                menu.style.transform = '';
                menu.style.transition = '';
            }
        });
    });
    
    // Add smooth transitions
    const addDropdownTransitions = () => {
        dropdowns.forEach(dropdown => {
            const menu = dropdown.querySelector('.dropdown-menu');
            if (menu) {
                menu.style.transition = 'transform 0.2s ease-out';
                menu.style.transform = 'translateY(0)';
            }
        });
    };
    
    // Initialize on mobile menu open
    navbarCollapse.addEventListener('shown.bs.collapse', addDropdownTransitions);
});

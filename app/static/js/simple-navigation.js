/**
 * AKSJERADAR - SIMPLE NAVIGATION SOLUTION
 * Clean, minimal approach working WITH Bootstrap
 */

console.log('� Simple Navigation Loading - Version 174000');

document.addEventListener('DOMContentLoaded', function() {
    console.log('� DOM ready - setting up navigation');
    
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        setupMobileNavigation();
    } else {
        setupDesktopNavigation();
    }
    
    // Handle resize
    window.addEventListener('resize', function() {
        const newIsMobile = window.innerWidth <= 768;
        if (newIsMobile !== isMobile) {
            location.reload(); // Reload if switching between mobile/desktop
        }
    });
});

function setupDesktopNavigation() {
    console.log('💻 Setting up desktop navigation');
    
    // Let Bootstrap handle dropdowns completely
    // Just ensure they work with hover too
    const dropdowns = document.querySelectorAll('.navbar-nav .dropdown');
    
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu) {
            // Add hover support ON TOP of Bootstrap
            dropdown.addEventListener('mouseenter', function() {
                // Show dropdown on hover
                menu.classList.add('show');
                toggle.setAttribute('aria-expanded', 'true');
            });
            
            dropdown.addEventListener('mouseleave', function() {
                // Hide dropdown when leaving
                menu.classList.remove('show');
                toggle.setAttribute('aria-expanded', 'false');
            });
        }
    });
    
    console.log('✅ Desktop navigation ready');
}

function setupMobileNavigation() {
    console.log('📱 Setting up mobile navigation');
    
    // Let Bootstrap handle the hamburger menu toggle
    // We only need to handle dropdown behavior for mobile
    
    const dropdownToggles = document.querySelectorAll('.navbar-nav .dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        // Remove Bootstrap dropdown behavior on mobile - use direct navigation
        toggle.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                e.stopPropagation();
                
                const href = this.getAttribute('href');
                if (href && href !== '#' && href !== '') {
                    console.log('📱 Mobile navigation to:', href);
                    window.location.href = href;
                }
            }
        });
    });
    
    console.log('✅ Mobile navigation ready');
}

console.log('✅ Simple Navigation Ready');

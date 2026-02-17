/**
 * AKSJERADAR NAVIGATION - NUCLEAR OPTION - FORCE FIX ALL ISSUES
 * This will override everything and make navigation work no matter what
 */

console.log('🚨 NUCLEAR NAVIGATION FIX LOADING...');

// Wait for DOM and force multiple initialization attempts
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔥 DOM READY - Starting aggressive navigation fix...');
    
    // Force fix after multiple delays to ensure everything is loaded
    setTimeout(initNavigationFix, 100);
    setTimeout(initNavigationFix, 500);
    setTimeout(initNavigationFix, 1000);
    
    // Also fix on window load
    window.addEventListener('load', function() {
        setTimeout(initNavigationFix, 100);
    });
});

function initNavigationFix() {
    console.log('🛠️ INITIALIZING NAVIGATION FIX...');
    
    const isMobile = window.innerWidth <= 768;
    console.log('📱 Device type:', isMobile ? 'MOBILE' : 'DESKTOP');
    
    if (isMobile) {
        fixMobileNavigation();
    } else {
        fixDesktopNavigation();
    }
}

function fixDesktopNavigation() {
    console.log('💻 FIXING DESKTOP NAVIGATION...');
    
    // Find all dropdown toggles
    const dropdownToggles = document.querySelectorAll('.navbar-nav .dropdown-toggle');
    
    dropdownToggles.forEach((toggle, index) => {
        console.log(`💻 Processing desktop dropdown ${index + 1}:`, toggle.textContent.trim());
        
        // FORCE Bootstrap attributes
        toggle.setAttribute('data-bs-toggle', 'dropdown');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('role', 'button');
        
        // Remove ALL existing event listeners by replacing the element
        const newToggle = toggle.cloneNode(true);
        toggle.parentNode.replaceChild(newToggle, toggle);
        
        // Force click handler that ensures Bootstrap works
        newToggle.addEventListener('click', function(e) {
            console.log('💻 Desktop click detected:', this.textContent.trim());
            
            // If Bootstrap dropdown exists, use it
            if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
                e.preventDefault();
                
                // Get or create Bootstrap dropdown instance
                let dropdown = bootstrap.Dropdown.getInstance(this);
                if (!dropdown) {
                    dropdown = new bootstrap.Dropdown(this);
                }
                
                // Toggle the dropdown
                dropdown.toggle();
                console.log('💻 Bootstrap dropdown toggled');
            }
            // Fallback: manual toggle
            else {
                console.log('💻 Bootstrap not available, using manual toggle');
                e.preventDefault();
                const menu = this.nextElementSibling;
                if (menu && menu.classList.contains('dropdown-menu')) {
                    const isOpen = menu.style.display === 'block';
                    menu.style.display = isOpen ? 'none' : 'block';
                }
            }
        });
        
        console.log('✅ Desktop dropdown fixed:', newToggle.textContent.trim());
    });
    
    console.log('💻 Desktop navigation fix complete');
}

function fixMobileNavigation() {
    console.log('📱 FIXING MOBILE NAVIGATION...');
    
    // Fix hamburger menu auto-closing issue
    const navbarCollapse = document.getElementById('navbarNav');
    if (navbarCollapse) {
        // Remove any auto-closing behavior
        navbarCollapse.addEventListener('show.bs.collapse', function() {
            console.log('📱 Mobile menu opening');
        });
        
        navbarCollapse.addEventListener('shown.bs.collapse', function() {
            console.log('📱 Mobile menu opened - preventing auto-close');
            // Remove any automatic closing timers
            clearTimeout(window.mobileMenuTimer);
        });
    }
    
    // Fix dropdown toggles for mobile
    const dropdownToggles = document.querySelectorAll('.navbar-nav .dropdown-toggle');
    
    dropdownToggles.forEach((toggle, index) => {
        console.log(`📱 Processing mobile dropdown ${index + 1}:`, toggle.textContent.trim());
        
        // Remove Bootstrap dropdown behavior
        toggle.removeAttribute('data-bs-toggle');
        toggle.removeAttribute('aria-expanded');
        
        // Get the href for direct navigation
        const href = toggle.getAttribute('href');
        console.log('📱 Dropdown href:', href);
        
        // Replace with clean element
        const newToggle = toggle.cloneNode(true);
        toggle.parentNode.replaceChild(newToggle, toggle);
        
        // Add mobile-specific click handler
        newToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('📱 Mobile dropdown clicked:', this.textContent.trim());
            
            // Direct navigation to main page
            if (href && href !== '#' && href !== '') {
                console.log('📱 Navigating to:', href);
                window.location.href = href;
                return;
            }
            
            // Toggle dropdown menu if no href
            const menu = this.nextElementSibling;
            if (menu && menu.classList.contains('dropdown-menu')) {
                toggleMobileDropdown(menu);
            }
        });
        
        console.log('✅ Mobile dropdown fixed:', newToggle.textContent.trim());
    });
    
    // Fix regular nav links to close menu properly
    const regularNavLinks = document.querySelectorAll('.navbar-nav .nav-link:not(.dropdown-toggle)');
    regularNavLinks.forEach(link => {
        link.addEventListener('click', function() {
            setTimeout(closeMobileMenu, 150);
        });
    });
    
    // Fix dropdown items to close menu
    const dropdownItems = document.querySelectorAll('.navbar-nav .dropdown-item');
    dropdownItems.forEach(item => {
        item.addEventListener('click', function() {
            setTimeout(closeMobileMenu, 150);
        });
    });
    
    console.log('📱 Mobile navigation fix complete');
}

function toggleMobileDropdown(menu) {
    const isOpen = menu.style.display === 'block';
    
    // Close all other mobile dropdowns
    document.querySelectorAll('.navbar-nav .dropdown-menu').forEach(otherMenu => {
        if (otherMenu !== menu) {
            otherMenu.style.display = 'none';
        }
    });
    
    // Toggle this dropdown
    menu.style.display = isOpen ? 'none' : 'block';
    console.log('📱 Mobile dropdown', isOpen ? 'closed' : 'opened');
}

function closeMobileMenu() {
    const navbarCollapse = document.getElementById('navbarNav');
    if (navbarCollapse && navbarCollapse.classList.contains('show')) {
        console.log('📱 Closing mobile menu...');
        
        // Force close with Bootstrap
        if (typeof bootstrap !== 'undefined' && bootstrap.Collapse) {
            const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse) || 
                              new bootstrap.Collapse(navbarCollapse, { toggle: false });
            bsCollapse.hide();
        } else {
            // Manual fallback
            navbarCollapse.classList.remove('show');
        }
        
        // Also close any open mobile dropdowns
        document.querySelectorAll('.navbar-nav .dropdown-menu').forEach(menu => {
            menu.style.display = 'none';
        });
        
        console.log('📱 Mobile menu closed');
    }
}

// Handle window resize with cleanup
window.addEventListener('resize', function() {
    clearTimeout(window.resizeTimer);
    window.resizeTimer = setTimeout(function() {
        const newIsMobile = window.innerWidth <= 768;
        console.log('🔄 Viewport changed, reinitializing navigation...');
        initNavigationFix();
    }, 250);
});

// Emergency override for any Bootstrap conflicts
document.addEventListener('click', function(e) {
    // If click is on a dropdown toggle that's not working, force it
    if (e.target.classList.contains('dropdown-toggle')) {
        const isDesktop = window.innerWidth > 768;
        if (isDesktop) {
            console.log('🚨 Emergency desktop dropdown override');
            const menu = e.target.nextElementSibling;
            if (menu && menu.classList.contains('dropdown-menu')) {
                const isOpen = menu.classList.contains('show') || menu.style.display === 'block';
                if (!isOpen) {
                    menu.classList.add('show');
                    menu.style.display = 'block';
                    e.target.setAttribute('aria-expanded', 'true');
                }
            }
        }
    }
});

console.log('🚨 NUCLEAR NAVIGATION FIX LOADED - All issues should be resolved!');

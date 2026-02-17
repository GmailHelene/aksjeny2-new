/**
 * Mobile Dropdown Fix for Aksjeradar
 * Fixes the issue where dropdown menus get "stuck" on mobile devices
 */

(function() {
    'use strict';
    
    // Mobile detection
    const isMobile = () => {
        return window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    };
    
    // State tracking
    let activeDropdown = null;
    let touchStartPos = { x: 0, y: 0 };
    let isInitialized = false;
    
    function initMobileDropdownFix() {
        if (isInitialized) return;
        isInitialized = true;
        
        console.log('Initializing mobile dropdown fix');
        
        // Wait for DOM and Bootstrap to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupMobileDropdowns);
        } else {
            setupMobileDropdowns();
        }
    }
    
    function setupMobileDropdowns() {
        if (!isMobile()) return;
        
        // Find all dropdown toggles
        const dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        
        dropdownToggles.forEach(toggle => {
            setupSingleDropdown(toggle);
        });
        
        // Setup global click handler for mobile
        setupGlobalClickHandler();
        
        // Setup touch handlers
        setupTouchHandlers();
        
        // Setup navbar collapse handler
        setupNavbarCollapseHandler();
        
        console.log(`Mobile dropdown fix applied to ${dropdownToggles.length} dropdowns`);
    }
    
    function setupSingleDropdown(toggle) {
        // Prevent multiple instances
        if (toggle.hasAttribute('data-mobile-dropdown-fixed')) return;
        toggle.setAttribute('data-mobile-dropdown-fixed', 'true');
        
        // Get or create Bootstrap dropdown instance
        let dropdownInstance;
        try {
            dropdownInstance = bootstrap.Dropdown.getInstance(toggle);
            if (!dropdownInstance) {
                dropdownInstance = new bootstrap.Dropdown(toggle);
            }
        } catch (e) {
            console.warn('Error creating dropdown instance:', e);
            return;
        }
        
        // Enhanced mobile event handling
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Close any other open dropdowns first
            closeAllDropdowns(toggle);
            
            // Toggle current dropdown
            const dropdownMenu = this.nextElementSibling;
            const isVisible = dropdownMenu && dropdownMenu.classList.contains('show');
            
            if (isVisible) {
                closeDropdown(dropdownInstance, this);
            } else {
                openDropdown(dropdownInstance, this);
            }
        });
        
        // Handle dropdown show/hide events
        toggle.addEventListener('shown.bs.dropdown', function() {
            activeDropdown = { toggle: this, instance: dropdownInstance };
            this.setAttribute('aria-expanded', 'true');
        });
        
        toggle.addEventListener('hidden.bs.dropdown', function() {
            if (activeDropdown && activeDropdown.toggle === this) {
                activeDropdown = null;
            }
            this.setAttribute('aria-expanded', 'false');
        });
    }
    
    function openDropdown(instance, toggle) {
        try {
            instance.show();
            // Add mobile-specific class for styling
            const dropdownMenu = toggle.nextElementSibling;
            if (dropdownMenu) {
                dropdownMenu.classList.add('mobile-dropdown-active');
            }
        } catch (e) {
            console.warn('Error opening dropdown:', e);
        }
    }
    
    function closeDropdown(instance, toggle) {
        try {
            instance.hide();
            // Remove mobile-specific class
            const dropdownMenu = toggle.nextElementSibling;
            if (dropdownMenu) {
                dropdownMenu.classList.remove('mobile-dropdown-active');
            }
        } catch (e) {
            console.warn('Error closing dropdown:', e);
        }
    }
    
    function closeAllDropdowns(except = null) {
        const allDropdowns = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        allDropdowns.forEach(toggle => {
            if (toggle === except) return;
            
            const instance = bootstrap.Dropdown.getInstance(toggle);
            if (instance) {
                closeDropdown(instance, toggle);
            }
        });
        activeDropdown = null;
    }
    
    function setupGlobalClickHandler() {
        // Close dropdowns when clicking outside
        document.addEventListener('click', function(e) {
            if (!activeDropdown) return;
            
            const clickedElement = e.target;
            const dropdownElement = activeDropdown.toggle.closest('.dropdown');
            
            // Check if click is outside the dropdown
            if (!dropdownElement || !dropdownElement.contains(clickedElement)) {
                closeDropdown(activeDropdown.instance, activeDropdown.toggle);
            }
        }, { passive: true });
        
        // Close dropdowns when clicking dropdown items (for mobile)
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('dropdown-item')) {
                // Small delay to allow navigation
                setTimeout(() => {
                    closeAllDropdowns();
                }, 100);
            }
        }, { passive: true });
    }
    
    function setupTouchHandlers() {
        // Track touch start position
        document.addEventListener('touchstart', function(e) {
            touchStartPos.x = e.touches[0].clientX;
            touchStartPos.y = e.touches[0].clientY;
        }, { passive: true });
        
        // Handle touch end to distinguish from scroll
        document.addEventListener('touchend', function(e) {
            if (!activeDropdown) return;
            
            const touch = e.changedTouches[0];
            const touchEndPos = {
                x: touch.clientX,
                y: touch.clientY
            };
            
            // Calculate touch distance
            const distance = Math.sqrt(
                Math.pow(touchEndPos.x - touchStartPos.x, 2) + 
                Math.pow(touchEndPos.y - touchStartPos.y, 2)
            );
            
            // If touch moved significantly, it's likely a scroll - don't close dropdown
            if (distance < 10) {
                const target = document.elementFromPoint(touchEndPos.x, touchEndPos.y);
                const dropdownElement = activeDropdown.toggle.closest('.dropdown');
                
                if (!dropdownElement || !dropdownElement.contains(target)) {
                    closeDropdown(activeDropdown.instance, activeDropdown.toggle);
                }
            }
        }, { passive: true });
    }
    
    function setupNavbarCollapseHandler() {
        // Close dropdowns when navbar collapses
        const navbarCollapse = document.querySelector('.navbar-collapse');
        if (navbarCollapse) {
            navbarCollapse.addEventListener('hidden.bs.collapse', function() {
                closeAllDropdowns();
            });
        }
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        // Reinitialize on orientation change or significant resize
        setTimeout(() => {
            if (isMobile()) {
                closeAllDropdowns();
            }
        }, 300);
    });
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMobileDropdownFix);
    } else {
        initMobileDropdownFix();
    }
    
    // Reinitialize after page navigation
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            isInitialized = false;
            setTimeout(initMobileDropdownFix, 100);
        }
    });
    
    // Export for debugging
    window.mobileDropdownFix = {
        closeAllDropdowns,
        reinitialize: () => {
            isInitialized = false;
            initMobileDropdownFix();
        }
    };
    
})();

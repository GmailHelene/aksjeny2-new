/**
 * Script loader to ensure proper loading order and avoid conflicts
 */
(function() {
    'use strict';
    
    // Define loading order for scripts
    const scriptLoadOrder = [
        // Core utilities first
        'cookie-consent.js',
        'realtime-data.js',
        
        // Enhanced features (ensure EnhancedRealTimeService is loaded first)
        'enhanced-realtime.js',
        
        // Dependent scripts
        'notification-filter.js',
        'navigation-fix.js',
        'watchlist-fix.js',
        'performance-optimizer.js',
        
        // Main app script last
        'main.js'
    ];
    
    // Track loaded scripts
    const loadedScripts = new Set();
    
    // Load scripts sequentially
    function loadScriptsSequentially(scripts, index = 0) {
        if (index >= scripts.length) {
            console.log('All scripts loaded successfully');
            return;
        }
        
        const scriptName = scripts[index];
        
        // Check if already loaded
        if (loadedScripts.has(scriptName)) {
            loadScriptsSequentially(scripts, index + 1);
            return;
        }
        
        // Check if script already exists in DOM
        const existingScript = document.querySelector(`script[src*="${scriptName}"]`);
        if (existingScript) {
            loadedScripts.add(scriptName);
            loadScriptsSequentially(scripts, index + 1);
            return;
        }
        
        // Create and load script
        const script = document.createElement('script');
        script.src = `/static/js/${scriptName}?v=${Date.now()}`;
        script.async = false;
        
        script.onload = () => {
            console.log(`Loaded: ${scriptName}`);
            loadedScripts.add(scriptName);
            
            // Special handling for enhanced-realtime.js
            if (scriptName === 'enhanced-realtime.js') {
                // Ensure global variable is available
                if (!window.EnhancedRealTimeService) {
                    window.EnhancedRealTimeService = window.enhancedRealTime?.constructor || function() {
                        console.warn('EnhancedRealTimeService is not available');
                    };
                }
            }
            
            // Load next script
            loadScriptsSequentially(scripts, index + 1);
        };
        
        script.onerror = (error) => {
            console.error(`Failed to load: ${scriptName}`, error);
            // Continue with next script even if one fails
            loadScriptsSequentially(scripts, index + 1);
        };
        
        document.head.appendChild(script);
    }
    
    // Start loading when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            loadScriptsSequentially(scriptLoadOrder);
        });
    } else {
        // DOM already loaded
        loadScriptsSequentially(scriptLoadOrder);
    }
})();

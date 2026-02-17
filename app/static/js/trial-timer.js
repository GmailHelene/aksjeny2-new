/**
 * Trial Timer Management System - COMPLETELY DISABLED
 * Timer functionality permanently removed per user request
 * "Den trial timeren skal vi vel ha helt vekk forresten?"
 */

class TrialTimerManager {
    static instance = null;
    
    constructor() {
        // Singleton pattern
        if (TrialTimerManager.instance) {
            return TrialTimerManager.instance;
        }
        
        // DISABLED: All timer functionality removed
        this.disabled = true;
        this.initialized = true;
        
        TrialTimerManager.instance = this;
        
        console.log('TrialTimerManager: Timer functionality permanently disabled');
    }

    async initializeTimer() {
        // DISABLED: Timer functionality completely removed
        console.log('TrialTimerManager: Timer is disabled - no initialization');
        return;
    }

    startBackgroundTimer() {
        // DISABLED: No background timer
        return;
    }

    updateDisplay() {
        // DISABLED: No display updates
        return;
    }

    clearTimer() {
        // DISABLED: Nothing to clear
        return;
    }

    destroy() {
        // DISABLED: Nothing to destroy
        return;
    }

    // Static methods for backward compatibility
    static getInstance() {
        if (!TrialTimerManager.instance) {
            new TrialTimerManager();
        }
        return TrialTimerManager.instance;
    }
    
    static disable() {
        console.log('Trial timer is already permanently disabled');
    }
}

// Do not initialize - timer is disabled
document.addEventListener('DOMContentLoaded', function() {
    console.log('Trial timer system is permanently disabled');
    
    // Remove any existing timer displays
    const timerElements = document.querySelectorAll('[id*="timer"], [class*="timer"], [id*="trial"]');
    timerElements.forEach(element => {
        if (element.textContent && element.textContent.includes(':')) {
            element.style.display = 'none';
        }
    });
});

// Export for modules (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TrialTimerManager;
}

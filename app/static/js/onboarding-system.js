/**
 * Interactive Onboarding System for Aksjeradar
 * Provides guided tours for new users and feature discovery
 */

class OnboardingManager {
    constructor() {
        this.tours = {};
        this.currentTour = null;
        this.currentStep = 0;
        this.overlay = null;
        this.tooltip = null;
        this.isActive = false;
        
        this.init();
    }
    
    init() {
        this.createOverlay();
        this.createTooltip();
        this.definetours();
        this.checkAutoStart();
    }
    
    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'onboarding-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 9998;
            display: none;
            pointer-events: none;
        `;
        document.body.appendChild(this.overlay);
    }
    
    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'onboarding-tooltip';
        this.tooltip.style.cssText = `
            position: absolute;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            max-width: 300px;
            z-index: 9999;
            display: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        document.body.appendChild(this.tooltip);
    }
    
    defineTours() {
        // Main navigation tour for new users
        this.tours.mainNavigation = {
            name: 'Hovednavigasjon',
            description: 'Lær deg å navigere i Aksjeradar',
            steps: [
                {
                    target: '.navbar-brand',
                    title: '👋 Velkommen til Aksjeradar!',
                    content: 'Dette er din AI-drevne aksjeanalyseplattform. La oss ta en rask tur rundt funksjonene.',
                    position: 'bottom'
                },
                {
                    target: '[href*="/analysis"]',
                    title: '📈 Analyse-verktøy',
                    content: 'Her finner du teknisk analyse, AI-prediksjoner og ekspertanbefalinger for alle aksjer.',
                    position: 'bottom'
                },
                {
                    target: '[href*="/portfolio"]',
                    title: '💼 Portefølje',
                    content: 'Administrer din portefølje, følg ytelse og få AI-drevne optimaliseringsforslag.',
                    position: 'bottom'
                },
                {
                    target: '[href*="/stocks"]',
                    title: '📊 Aksjer',
                    content: 'Utforsk Oslo Børs og globale markeder med detaljerte analyser og data.',
                    position: 'bottom'
                },
                {
                    target: '.search-form',
                    title: '🔍 Søk',
                    content: 'Søk raskt etter aksjer, selskaper eller analyserapporter.',
                    position: 'bottom'
                }
            ]
        };
        
        // AI Analysis tour
        this.tours.aiAnalysis = {
            name: 'AI-analyse funksjoner',
            description: 'Oppdage kraften i AI-drevet aksjeanalyse',
            steps: [
                {
                    target: '[href*="/analysis/ai"]',
                    title: '🤖 AI-analyse',
                    content: 'Vår AI analyserer aksjer basert på tekniske indikatorer, markedssentiment og historiske data.',
                    position: 'right'
                },
                {
                    target: '[href*="/analysis/warren-buffett"]',
                    title: '💎 Warren Buffett analyse',
                    content: 'Analyser aksjer med Warren Buffetts verdiinvestering-prinsipper.',
                    position: 'right'
                },
                {
                    target: '[href*="/analysis/benjamin-graham"]',
                    title: '📚 Benjamin Graham analyse',
                    content: 'Bruk den klassiske verdiinvestering-metodikken fra "faren til verdiinvestering".',
                    position: 'right'
                },
                {
                    target: '[href*="/analysis/short-analysis"]',
                    title: '📉 Short-analyse',
                    content: '⚠️ Avansert: Identifiser potensielle short-muligheter med AI-assistanse. Høy risiko!',
                    position: 'right'
                }
            ]
        };
        
        // Portfolio management tour
        this.tours.portfolioManagement = {
            name: 'Porteføljestyring',
            description: 'Lær å optimalisere din portefølje med AI',
            steps: [
                {
                    target: '[href*="/portfolio/advanced"]',
                    title: '🚀 Avansert porteføljeanalyse',
                    content: 'Få dybdeanalyse av din portefølje med risiko-/avkastningsvurdering.',
                    position: 'bottom'
                },
                {
                    target: '[href*="/watchlist"]',
                    title: '⭐ Favorittliste',
                    content: 'Følg dine favorittaksjer og få varsler om prisendringer.',
                    position: 'bottom'
                },
                {
                    target: '[href*="/backtest"]',
                    title: '📊 Backtesting',
                    content: 'Test handelsstrategier mot historiske data for å optimalisere porteføljen.',
                    position: 'bottom'
                }
            ]
        };
    }
    
    startTour(tourName) {
        if (!this.tours[tourName]) {
            console.error(`Tour '${tourName}' not found`);
            return;
        }
        
        this.currentTour = this.tours[tourName];
        this.currentStep = 0;
        this.isActive = true;
        
        this.showOverlay();
        this.showStep();
        
        // Track tour start
        this.trackEvent('tour_started', { tour: tourName });
    }
    
    showStep() {
        if (!this.currentTour || this.currentStep >= this.currentTour.steps.length) {
            this.endTour();
            return;
        }
        
        const step = this.currentTour.steps[this.currentStep];
        const target = document.querySelector(step.target);
        
        if (!target) {
            console.warn(`Target '${step.target}' not found, skipping step`);
            this.nextStep();
            return;
        }
        
        this.highlightElement(target);
        this.showTooltip(target, step);
    }
    
    highlightElement(element) {
        // Remove previous highlights
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });
        
        // Add highlight class
        element.classList.add('onboarding-highlight');
        
        // Create spotlight effect
        const rect = element.getBoundingClientRect();
        const spotlight = document.createElement('div');
        spotlight.className = 'onboarding-spotlight';
        spotlight.style.cssText = `
            position: fixed;
            top: ${rect.top - 10}px;
            left: ${rect.left - 10}px;
            width: ${rect.width + 20}px;
            height: ${rect.height + 20}px;
            border-radius: 4px;
            box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.5), 0 0 0 9999px rgba(0, 0, 0, 0.7);
            z-index: 9998;
            pointer-events: none;
            animation: onboardingPulse 2s infinite;
        `;
        
        // Remove existing spotlight
        const existingSpotlight = document.querySelector('.onboarding-spotlight');
        if (existingSpotlight) existingSpotlight.remove();
        
        document.body.appendChild(spotlight);
    }
    
    showTooltip(target, step) {
        const rect = target.getBoundingClientRect();
        
        this.tooltip.innerHTML = `
            <div class="onboarding-tooltip-header">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">${step.title}</h4>
                <span class="onboarding-step-counter" style="color: #7f8c8d; font-size: 12px;">
                    Steg ${this.currentStep + 1} av ${this.currentTour.steps.length}
                </span>
            </div>
            <div class="onboarding-tooltip-content" style="margin-bottom: 15px; line-height: 1.5;">
                ${step.content}
            </div>
            <div class="onboarding-tooltip-actions" style="display: flex; justify-content: space-between; align-items: center;">
                <button class="btn-onboarding-skip" style="background: none; border: none; color: #7f8c8d; cursor: pointer; font-size: 14px;">
                    Hopp over
                </button>
                <div>
                    ${this.currentStep > 0 ? '<button class="btn-onboarding-prev" style="background: #ecf0f1; border: none; padding: 8px 16px; border-radius: 4px; margin-right: 8px; cursor: pointer;">Forrige</button>' : ''}
                    <button class="btn-onboarding-next" style="background: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        ${this.currentStep === this.currentTour.steps.length - 1 ? 'Fullfør' : 'Neste'}
                    </button>
                </div>
            </div>
        `;
        
        // Position tooltip
        let top, left;
        switch (step.position) {
            case 'bottom':
                top = rect.bottom + 10;
                left = rect.left + (rect.width / 2) - 150;
                break;
            case 'top':
                top = rect.top - this.tooltip.offsetHeight - 10;
                left = rect.left + (rect.width / 2) - 150;
                break;
            case 'right':
                top = rect.top + (rect.height / 2) - 75;
                left = rect.right + 10;
                break;
            case 'left':
                top = rect.top + (rect.height / 2) - 75;
                left = rect.left - 310;
                break;
            default:
                top = rect.bottom + 10;
                left = rect.left;
        }
        
        // Ensure tooltip stays within viewport
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        if (left < 10) left = 10;
        if (left + 300 > viewportWidth) left = viewportWidth - 310;
        if (top < 10) top = 10;
        if (top + 200 > viewportHeight) top = viewportHeight - 210;
        
        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.display = 'block';
        
        // Add event listeners
        this.tooltip.querySelector('.btn-onboarding-skip').onclick = () => this.endTour();
        this.tooltip.querySelector('.btn-onboarding-next').onclick = () => this.nextStep();
        
        const prevBtn = this.tooltip.querySelector('.btn-onboarding-prev');
        if (prevBtn) prevBtn.onclick = () => this.prevStep();
    }
    
    nextStep() {
        this.currentStep++;
        this.showStep();
    }
    
    prevStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep();
        }
    }
    
    endTour() {
        this.isActive = false;
        this.currentTour = null;
        this.currentStep = 0;
        
        this.hideOverlay();
        this.hideTooltip();
        this.removeHighlights();
        
        // Mark tour as completed
        this.markTourCompleted();
        
        // Track tour completion
        this.trackEvent('tour_completed');
    }
    
    showOverlay() {
        this.overlay.style.display = 'block';
    }
    
    hideOverlay() {
        this.overlay.style.display = 'none';
    }
    
    hideTooltip() {
        this.tooltip.style.display = 'none';
    }
    
    removeHighlights() {
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });
        
        const spotlight = document.querySelector('.onboarding-spotlight');
        if (spotlight) spotlight.remove();
    }
    
    checkAutoStart() {
        // Check if user is new and should see onboarding
        const hasSeenOnboarding = localStorage.getItem('aksjeradar_onboarding_seen');
        const isNewUser = document.body.dataset.newUser === 'true';
        
        if (!hasSeenOnboarding && isNewUser) {
            // Auto-start main navigation tour after 2 seconds
            setTimeout(() => {
                this.showWelcomePrompt();
            }, 2000);
        }
    }
    
    showWelcomePrompt() {
        const modal = document.createElement('div');
        modal.className = 'onboarding-welcome-modal';
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            text-align: center;
            max-width: 400px;
        `;
        
        modal.innerHTML = `
            <h2 style="color: #2c3e50; margin-bottom: 15px;">🎉 Velkommen til Aksjeradar!</h2>
            <p style="color: #34495e; margin-bottom: 25px; line-height: 1.6;">
                Vil du ha en rask guidet tur for å lære deg de viktigste funksjonene?
            </p>
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button class="btn-start-tour" style="background: #3498db; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                    Ja, start turen!
                </button>
                <button class="btn-skip-tour" style="background: #ecf0f1; color: #2c3e50; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer;">
                    Nei takk
                </button>
            </div>
        `;
        
        // Add backdrop
        const backdrop = document.createElement('div');
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9999;
        `;
        
        document.body.appendChild(backdrop);
        document.body.appendChild(modal);
        
        // Event listeners
        modal.querySelector('.btn-start-tour').onclick = () => {
            document.body.removeChild(backdrop);
            document.body.removeChild(modal);
            this.startTour('mainNavigation');
        };
        
        modal.querySelector('.btn-skip-tour').onclick = () => {
            document.body.removeChild(backdrop);
            document.body.removeChild(modal);
            this.markTourCompleted();
        };
        
        backdrop.onclick = () => {
            document.body.removeChild(backdrop);
            document.body.removeChild(modal);
            this.markTourCompleted();
        };
    }
    
    markTourCompleted() {
        localStorage.setItem('aksjeradar_onboarding_seen', 'true');
        localStorage.setItem('aksjeradar_onboarding_date', new Date().toISOString());
    }
    
    trackEvent(eventName, data = {}) {
        // Send analytics event
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, {
                event_category: 'onboarding',
                ...data
            });
        }
        
        console.log('Onboarding event:', eventName, data);
    }
    
    // Public methods for manual tour triggering
    startMainTour() {
        this.startTour('mainNavigation');
    }
    
    startAITour() {
        this.startTour('aiAnalysis');
    }
    
    startPortfolioTour() {
        this.startTour('portfolioManagement');
    }
    
    resetOnboarding() {
        localStorage.removeItem('aksjeradar_onboarding_seen');
        localStorage.removeItem('aksjeradar_onboarding_date');
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes onboardingPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .onboarding-highlight {
        position: relative;
        z-index: 9999 !important;
        pointer-events: auto !important;
    }
    
    .onboarding-tooltip {
        animation: onboardingFadeIn 0.3s ease-out;
    }
    
    @keyframes onboardingFadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .btn-onboarding-next:hover,
    .btn-onboarding-prev:hover {
        transform: translateY(-1px);
        transition: transform 0.2s ease;
    }
    
    .btn-onboarding-skip:hover {
        text-decoration: underline;
    }
`;
document.head.appendChild(style);

// Initialize onboarding when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.onboardingManager = new OnboardingManager();
});

// Global functions for easy access
function startOnboardingTour(tourName = 'mainNavigation') {
    if (window.onboardingManager) {
        window.onboardingManager.startTour(tourName);
    }
}

function resetOnboarding() {
    if (window.onboardingManager) {
        window.onboardingManager.resetOnboarding();
    }
}

/**
 * Advanced Tooltip and Onboarding System
 */
class OnboardingManager {
    constructor() {
        this.tooltips = new Map();
        this.onboardingSteps = [];
        this.currentStep = 0;
        this.isOnboardingActive = false;
        this.init();
    }

    init() {
        this.loadTooltipDefinitions();
        this.initializeTooltips();
        this.checkFirstVisit();
    }

    loadTooltipDefinitions() {
        // Define all tooltips with rich content
        this.tooltipDefinitions = {
            'ai-score': {
                title: 'AI Confidence Score',
                content: `
                    <div class="tooltip-content">
                        <p><strong>Hva er dette?</strong><br>
                        En score fra 0-100 som viser hvor sannsynlig det er at aksjen vil stige.</p>
                        
                        <div class="score-guide mb-2">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="badge bg-danger">0-30</span>
                                <small>Bearish - Sannsynlig nedgang</small>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="badge bg-warning">31-60</span>
                                <small>Nøytral - Usikker retning</small>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="badge bg-success">61-100</span>
                                <small>Bullish - Sannsynlig oppgang</small>
                            </div>
                        </div>
                        
                        <p class="small text-muted mb-0">
                            <i class="bi bi-info-circle"></i>
                            Basert på 15+ tekniske indikatorer og historisk data
                        </p>
                    </div>
                `,
                placement: 'bottom'
            },
            
            'rsi': {
                title: 'RSI (Relative Strength Index)',
                content: `
                    <div class="tooltip-content">
                        <p><strong>Momentum-indikator</strong><br>
                        Måler om aksjen er overkjøpt eller oversolgt.</p>
                        
                        <div class="rsi-guide mb-2">
                            <div class="progress mb-1" style="height: 20px;">
                                <div class="progress-bar bg-success" style="width: 30%;">
                                    <small>0-30 Oversolgt</small>
                                </div>
                                <div class="progress-bar bg-warning" style="width: 40%;">
                                    <small>30-70 Normal</small>
                                </div>
                                <div class="progress-bar bg-danger" style="width: 30%;">
                                    <small>70-100 Overkjøpt</small>
                                </div>
                            </div>
                        </div>
                        
                        <p class="small text-muted mb-0">
                            💡 <strong>Tip:</strong> RSI under 30 kan indikere kjøpsmulighet, 
                            over 70 kan indikere salgsmulighet.
                        </p>
                    </div>
                `,
                placement: 'right'
            },
            
            'macd': {
                title: 'MACD (Moving Average Convergence Divergence)',
                content: `
                    <div class="tooltip-content">
                        <p><strong>Trend-indikator</strong><br>
                        Viser forholdet mellom to glidende gjennomsnitt.</p>
                        
                        <ul class="small mb-2">
                            <li><strong>Positiv MACD:</strong> Opptrend, bullish signal</li>
                            <li><strong>Negativ MACD:</strong> Nedtrend, bearish signal</li>
                            <li><strong>Crossover:</strong> Når linjen krysser, kan det indikere trendskifte</li>
                        </ul>
                        
                        <p class="small text-muted mb-0">
                            📈 Brukes ofte sammen med andre indikatorer for bekreftelse.
                        </p>
                    </div>
                `,
                placement: 'left'
            },
            
            'volume': {
                title: 'Handelsvolum',
                content: `
                    <div class="tooltip-content">
                        <p><strong>Antall aksjer handlet</strong><br>
                        Høyt volum bekrefter ofte prisbevegelser.</p>
                        
                        <div class="volume-tips small mb-2">
                            <div class="mb-1">
                                <i class="bi bi-arrow-up text-success"></i>
                                <strong>Høyt volum + oppgang:</strong> Sterk bullish signal
                            </div>
                            <div class="mb-1">
                                <i class="bi bi-arrow-down text-danger"></i>
                                <strong>Høyt volum + nedgang:</strong> Sterk bearish signal
                            </div>
                            <div>
                                <i class="bi bi-dash text-warning"></i>
                                <strong>Lavt volum:</strong> Svak trend, kan snu lett
                            </div>
                        </div>
                        
                        <p class="small text-muted mb-0">
                            💡 "Volume leads price" - Volum kommer ofte før prisendringer.
                        </p>
                    </div>
                `,
                placement: 'top'
            },

            'portfolio-diversification': {
                title: 'Portefølje-diversifisering',
                content: `
                    <div class="tooltip-content">
                        <p><strong>Spredning av risiko</strong><br>
                        Ikke legg alle eggene i én kurv!</p>
                        
                        <div class="diversification-guide small mb-2">
                            <div class="mb-1">
                                <span class="badge bg-success">Godt:</span>
                                Maksimum 20% i én aksje
                            </div>
                            <div class="mb-1">
                                <span class="badge bg-warning">Middels:</span>
                                20-40% i én aksje
                            </div>
                            <div>
                                <span class="badge bg-danger">Risikabelt:</span>
                                Over 40% i én aksje
                            </div>
                        </div>
                        
                        <p class="small text-muted mb-0">
                            🎯 Anbefaling: Minst 5-10 forskjellige aksjer i ulike sektorer.
                        </p>
                    </div>
                `,
                placement: 'bottom'
            }
        };
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips with custom content
        document.addEventListener('DOMContentLoaded', () => {
            // Enhanced tooltips for data attributes
            const tooltipElements = document.querySelectorAll('[data-tooltip-key]');
            
            tooltipElements.forEach(element => {
                const key = element.getAttribute('data-tooltip-key');
                const tooltipDef = this.tooltipDefinitions[key];
                
                if (tooltipDef) {
                    new bootstrap.Tooltip(element, {
                        title: tooltipDef.content,
                        html: true,
                        placement: tooltipDef.placement || 'top',
                        trigger: 'hover focus',
                        customClass: 'advanced-tooltip',
                        delay: { show: 300, hide: 100 }
                    });
                }
            });

            // Initialize standard tooltips
            const standardTooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]:not([data-tooltip-key])');
            standardTooltips.forEach(element => {
                new bootstrap.Tooltip(element);
            });
        });
    }

    checkFirstVisit() {
        if (!localStorage.getItem('aksjeradar_visited')) {
            this.startOnboarding();
            localStorage.setItem('aksjeradar_visited', 'true');
        }
    }

    startOnboarding() {
        this.defineOnboardingSteps();
        this.isOnboardingActive = true;
        this.currentStep = 0;
        this.showOnboardingStep();
    }

    defineOnboardingSteps() {
        this.onboardingSteps = [
            {
                target: '.navbar-brand',
                title: 'Velkommen til Aksjeradar! 👋',
                content: `
                    <p>La oss ta en rask rundtur og vise deg de viktigste funksjonene.</p>
                    <p>Dette tar bare 60 sekunder, og du kan hoppe over når som helst.</p>
                `,
                placement: 'bottom'
            },
            {
                target: '[data-market="oslo"]',
                title: 'Oslo Børs aksjer 📈',
                content: `
                    <p>Her ser du sanntidsdata for norske aksjer med:</p>
                    <ul class="small">
                        <li>Live priser og endringer</li>
                        <li>AI-drevne kjøps/salgs-signaler</li>
                        <li>Tekniske indikatorer som RSI</li>
                    </ul>
                `,
                placement: 'top'
            },
            {
                target: '.live-indicator',
                title: 'Live data 🔴',
                content: `
                    <p>Den røde prikken viser at dataene oppdateres i sanntid!</p>
                    <p>Du får de nyeste prisene og signalene uten å måtte oppdatere siden.</p>
                `,
                placement: 'left'
            },
            {
                target: '[data-tooltip-key="ai-score"]',
                title: 'AI Confidence Score 🤖',
                content: `
                    <p>Vår AI analyserer 15+ indikatorer og gir en score fra 0-100.</p>
                    <p>Høyere score = større sannsynlighet for positiv utvikling.</p>
                    <p><strong>Prøv å hover over AI-scoren for mer info!</strong></p>
                `,
                placement: 'bottom'
            },
            {
                target: '#userDropdown, .btn-outline-light',
                title: 'Din konto 👤',
                content: `
                    <p>Registrer deg for å få tilgang til:</p>
                    <ul class="small">
                        <li>Porteføljetracking</li>
                        <li>Personlige varsler</li>
                        <li>Utvidede AI-analyser</li>
                        <li>Historiske data og grafer</li>
                    </ul>
                `,
                placement: 'bottom'
            }
        ];
    }

    showOnboardingStep() {
        if (this.currentStep >= this.onboardingSteps.length) {
            this.completeOnboarding();
            return;
        }

        const step = this.onboardingSteps[this.currentStep];
        const target = document.querySelector(step.target);
        
        if (!target) {
            this.nextStep();
            return;
        }

        this.createOnboardingPopover(target, step);
    }

    createOnboardingPopover(target, step) {
        // Create backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'onboarding-backdrop';
        backdrop.id = 'onboarding-backdrop';
        document.body.appendChild(backdrop);

        // Highlight target element
        target.classList.add('onboarding-highlight');
        target.style.position = 'relative';
        target.style.zIndex = '9999';

        // Create popover
        const popover = document.createElement('div');
        popover.className = 'onboarding-popover';
        popover.innerHTML = `
            <div class="onboarding-content">
                <div class="onboarding-header">
                    <h5 class="mb-0">${step.title}</h5>
                    <button type="button" class="btn-close" onclick="onboardingManager.skipOnboarding()"></button>
                </div>
                <div class="onboarding-body">
                    ${step.content}
                </div>
                <div class="onboarding-footer">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="progress flex-grow-1 me-3" style="height: 4px;">
                            <div class="progress-bar" style="width: ${((this.currentStep + 1) / this.onboardingSteps.length) * 100}%"></div>
                        </div>
                        <div class="btn-group">
                            ${this.currentStep > 0 ? '<button class="btn btn-outline-secondary btn-sm" onclick="onboardingManager.previousStep()">Tilbake</button>' : ''}
                            <button class="btn btn-primary btn-sm" onclick="onboardingManager.nextStep()">
                                ${this.currentStep === this.onboardingSteps.length - 1 ? 'Ferdig' : 'Neste'}
                            </button>
                        </div>
                    </div>
                    <div class="text-center mt-2">
                        <button class="btn btn-link btn-sm text-muted" onclick="onboardingManager.skipOnboarding()">
                            Hopp over rundturen
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(popover);
        this.positionPopover(popover, target, step.placement);

        // Add event listeners
        backdrop.addEventListener('click', () => this.skipOnboarding());
    }

    positionPopover(popover, target, placement = 'bottom') {
        const targetRect = target.getBoundingClientRect();
        const popoverRect = popover.getBoundingClientRect();
        
        let top, left;

        switch (placement) {
            case 'top':
                top = targetRect.top - popoverRect.height - 10;
                left = targetRect.left + (targetRect.width / 2) - (popoverRect.width / 2);
                break;
            case 'bottom':
                top = targetRect.bottom + 10;
                left = targetRect.left + (targetRect.width / 2) - (popoverRect.width / 2);
                break;
            case 'left':
                top = targetRect.top + (targetRect.height / 2) - (popoverRect.height / 2);
                left = targetRect.left - popoverRect.width - 10;
                break;
            case 'right':
                top = targetRect.top + (targetRect.height / 2) - (popoverRect.height / 2);
                left = targetRect.right + 10;
                break;
            default:
                top = targetRect.bottom + 10;
                left = targetRect.left;
        }

        // Ensure popover stays within viewport
        top = Math.max(10, Math.min(top, window.innerHeight - popoverRect.height - 10));
        left = Math.max(10, Math.min(left, window.innerWidth - popoverRect.width - 10));

        popover.style.top = `${top}px`;
        popover.style.left = `${left}px`;
    }

    nextStep() {
        this.cleanupCurrentStep();
        this.currentStep++;
        this.showOnboardingStep();
    }

    previousStep() {
        this.cleanupCurrentStep();
        this.currentStep--;
        this.showOnboardingStep();
    }

    cleanupCurrentStep() {
        // Remove backdrop
        const backdrop = document.getElementById('onboarding-backdrop');
        if (backdrop) backdrop.remove();

        // Remove popover
        const popover = document.querySelector('.onboarding-popover');
        if (popover) popover.remove();

        // Remove highlight
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
            el.style.position = '';
            el.style.zIndex = '';
        });
    }

    skipOnboarding() {
        this.cleanupCurrentStep();
        this.isOnboardingActive = false;
        localStorage.setItem('aksjeradar_onboarding_completed', 'true');
        
        // Show skip confirmation
        this.showNotification('Rundtur hoppet over. Du kan starte den igjen fra innstillinger.', 'info');
    }

    completeOnboarding() {
        this.cleanupCurrentStep();
        this.isOnboardingActive = false;
        localStorage.setItem('aksjeradar_onboarding_completed', 'true');
        
        // Show completion message
        this.showCompletionMessage();
    }

    showCompletionMessage() {
        const modal = `
            <div class="modal fade" id="onboardingCompleteModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-check-circle me-2"></i>
                                Gratulerer! 🎉
                            </h5>
                        </div>
                        <div class="modal-body text-center">
                            <i class="bi bi-trophy text-warning" style="font-size: 3rem;"></i>
                            <h4 class="mt-3">Du er klar til å investere smartere!</h4>
                            <p class="text-muted">Du har nå lært de grunnleggende funksjonene i Aksjeradar.</p>
                            
                            <div class="row text-center mt-4">
                                <div class="col-4">
                                    <i class="bi bi-robot text-primary"></i>
                                    <div class="small mt-1">AI-analyser</div>
                                </div>
                                <div class="col-4">
                                    <i class="bi bi-graph-up text-success"></i>
                                    <div class="small mt-1">Live data</div>
                                </div>
                                <div class="col-4">
                                    <i class="bi bi-lightbulb text-warning"></i>
                                    <div class="small mt-1">Smart tips</div>
                                </div>
                            </div>
                            
                            <div class="d-grid gap-2 mt-4">
                                <a href="{{ url_for('main.register') }}" class="btn btn-primary">
                                    <i class="bi bi-person-plus"></i> Registrer deg nå
                                </a>
                                <button class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                    Fortsett uten registrering
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modal);
        const modalEl = new bootstrap.Modal(document.getElementById('onboardingCompleteModal'));
        modalEl.show();
        
        // Clean up modal after it's hidden
        document.getElementById('onboardingCompleteModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `toast align-items-center text-white bg-${type} border-0 position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        notification.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-info-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        document.body.appendChild(notification);
        const toast = new bootstrap.Toast(notification, { delay: 5000 });
        toast.show();

        notification.addEventListener('hidden.bs.toast', () => {
            notification.remove();
        });
    }

    // Public API
    restartOnboarding() {
        localStorage.removeItem('aksjeradar_onboarding_completed');
        this.startOnboarding();
    }

    showTooltip(element, key) {
        const tooltipDef = this.tooltipDefinitions[key];
        if (tooltipDef && element) {
            const tooltip = new bootstrap.Tooltip(element, {
                title: tooltipDef.content,
                html: true,
                placement: tooltipDef.placement || 'top',
                trigger: 'manual',
                customClass: 'advanced-tooltip'
            });
            tooltip.show();
            
            // Auto-hide after 5 seconds
            setTimeout(() => tooltip.hide(), 5000);
        }
    }
}

// CSS for onboarding and advanced tooltips
const onboardingStyles = `
    .onboarding-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 9998;
        animation: fadeIn 0.3s ease-out;
    }
    
    .onboarding-highlight {
        box-shadow: 0 0 0 4px rgba(13, 110, 253, 0.5), 0 0 0 8px rgba(13, 110, 253, 0.25) !important;
        border-radius: 8px !important;
        animation: highlight-pulse 2s infinite;
    }
    
    @keyframes highlight-pulse {
        0% { box-shadow: 0 0 0 4px rgba(13, 110, 253, 0.5), 0 0 0 8px rgba(13, 110, 253, 0.25); }
        50% { box-shadow: 0 0 0 6px rgba(13, 110, 253, 0.7), 0 0 0 12px rgba(13, 110, 253, 0.15); }
        100% { box-shadow: 0 0 0 4px rgba(13, 110, 253, 0.5), 0 0 0 8px rgba(13, 110, 253, 0.25); }
    }
    
    .onboarding-popover {
        position: fixed;
        z-index: 9999;
        max-width: 400px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        animation: slideIn 0.3s ease-out;
    }
    
    .onboarding-content {
        padding: 0;
    }
    
    .onboarding-header {
        display: flex;
        justify-content: between;
        align-items: center;
        padding: 1rem 1rem 0.5rem;
        border-bottom: 1px solid #dee2e6;
    }
    
    .onboarding-body {
        padding: 1rem;
    }
    
    .onboarding-footer {
        padding: 0.5rem 1rem 1rem;
        border-top: 1px solid #dee2e6;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .advanced-tooltip {
        max-width: 350px;
    }
    
    .advanced-tooltip .tooltip-inner {
        background: #fff;
        color: #333;
        border: 1px solid #ddd;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        padding: 1rem;
        text-align: left;
        border-radius: 8px;
    }
    
    .advanced-tooltip .tooltip-arrow::before {
        border-color: #ddd transparent;
    }
    
    .tooltip-content {
        line-height: 1.4;
    }
    
    .tooltip-content .badge {
        font-size: 0.7rem;
    }
    
    .score-guide, .rsi-guide, .volume-tips, .diversification-guide {
        font-size: 0.85rem;
    }
    
    /* Dark mode support for tooltips */
    [data-theme="dark"] .advanced-tooltip .tooltip-inner {
        background: #2c3034;
        color: #fff;
        border-color: #444;
    }
    
    [data-theme="dark"] .advanced-tooltip .tooltip-arrow::before {
        border-color: #444 transparent;
    }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = onboardingStyles;
document.head.appendChild(styleSheet);

// Initialize onboarding manager
const onboardingManager = new OnboardingManager();

// Export for global access
window.onboardingManager = onboardingManager;

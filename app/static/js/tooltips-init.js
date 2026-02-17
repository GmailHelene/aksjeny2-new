/**
 * Centralized Tooltip and Glossary System
 * Provides consistent tooltips across the application
 */

class TooltipManager {
    constructor() {
        this.tooltips = new Map();
        this.glossaryTerms = {
            // Financial terms in Norwegian
            'RSI': 'Relativ Styrkeindeks - måler momentum og identifiserer overkjøpte/oversolgte nivåer',
            'MACD': 'Moving Average Convergence Divergence - viser forholdet mellom to glidende gjennomsnitt',
            'P/E': 'Pris/Inntjening - viser forholdet mellom aksjepris og inntjening per aksje',
            'EPS': 'Inntjening Per Aksje - selskapets nettoinntekt delt på antall aksjer',
            'ROE': 'Avkastning på Egenkapital - måler lønnsomhet i forhold til egenkapital',
            'Market Cap': 'Markedsverdi - total verdi av alle utestående aksjer',
            'Dividend Yield': 'Utbytteavkastning - årlig utbytte som prosent av aksjekurs',
            'Beta': 'Volatilitet i forhold til markedet - 1.0 = følger markedet',
            'Volume': 'Handelsvolum - antall aksjer omsatt i en periode',
            'Volatility': 'Volatilitet - hvor mye prisen svinger over tid',
            
            // AI terms
            'AI Score': 'Kunstig intelligens-score basert på multiple faktorer og historiske data',
            'Sentiment': 'Markedssentiment - samlet stemning basert på nyheter og sosiale medier',
            'Prediction Confidence': 'Hvor sikker AI-modellen er på sin prediksjon (0-100%)',
            
            // Trading terms
            'Support': 'Støttenivå - prisnivå hvor kjøpsinteresse ofte øker',
            'Resistance': 'Motstandsnivå - prisnivå hvor salgspress ofte øker',
            'Breakout': 'Utbrudd - når prisen bryter gjennom støtte eller motstand',
            'Trend': 'Retning på prisbevegelsen over tid',
            'Moving Average': 'Glidende gjennomsnitt - gjennomsnittspris over en periode'
        };
        
        this.init();
    }
    
    init() {
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeTooltips();
            this.initializeGlossaryTerms();
            this.observeNewElements();
        });
    }
    
    initializeTooltips() {
        // Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            const tooltip = new bootstrap.Tooltip(tooltipTriggerEl, {
                html: true,
                sanitize: false,
                trigger: 'hover focus',
                delay: { show: 300, hide: 100 }
            });
            this.tooltips.set(tooltipTriggerEl, tooltip);
        });
    }
    
    initializeGlossaryTerms() {
        // Add tooltips to glossary terms
        document.querySelectorAll('.glossary-term').forEach(element => {
            const term = element.textContent.trim();
            if (this.glossaryTerms[term]) {
                element.setAttribute('data-bs-toggle', 'tooltip');
                element.setAttribute('data-bs-placement', 'top');
                element.setAttribute('title', this.glossaryTerms[term]);
                element.classList.add('text-decoration-underline', 'text-decoration-style-dotted');
                element.style.cursor = 'help';
                
                // Initialize tooltip
                const tooltip = new bootstrap.Tooltip(element);
                this.tooltips.set(element, tooltip);
            }
        });
    }
    
    observeNewElements() {
        // Watch for dynamically added elements
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        this.initializeTooltipsInElement(node);
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    initializeTooltipsInElement(element) {
        // Initialize tooltips in a specific element
        const tooltipElements = element.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(el => {
            if (!this.tooltips.has(el)) {
                const tooltip = new bootstrap.Tooltip(el);
                this.tooltips.set(el, tooltip);
            }
        });
        
        // Check if element itself needs tooltip
        if (element.hasAttribute('data-bs-toggle') && element.getAttribute('data-bs-toggle') === 'tooltip') {
            if (!this.tooltips.has(element)) {
                const tooltip = new bootstrap.Tooltip(element);
                this.tooltips.set(element, tooltip);
            }
        }
    }
    
    addGlossaryTerm(term, definition) {
        this.glossaryTerms[term] = definition;
    }
    
    destroy() {
        // Clean up all tooltips
        this.tooltips.forEach(tooltip => tooltip.dispose());
        this.tooltips.clear();
    }
}

// Initialize tooltip manager
const tooltipManager = new TooltipManager();

// Export for use in other modules
window.TooltipManager = TooltipManager;
window.tooltipManager = tooltipManager;

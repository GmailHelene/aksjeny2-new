/**
 * TradingView Widget Integration and Fixes
 * Implements robust widget initialization and error handling
 */

// TradingView configuration and state
const TV_CONFIG = {
    default_symbol: 'NASDAQ:AAPL',
    supported_exchanges: ['NASDAQ', 'NYSE', 'OSL', 'BINANCE', 'FX'],
    exchange_mappings: {
        'OL': 'OSL',  // Oslo Børs
        'ST': 'STO',  // Stockholm
        'CO': 'CPH',  // Copenhagen
        'HE': 'HEL'   // Helsinki
    }
};

// Format symbol for TradingView
function formatSymbolForTradingView(symbol) {
    try {
        if (!symbol || typeof symbol !== 'string') {
            console.warn('Invalid symbol provided:', symbol);
            return TV_CONFIG.default_symbol;
        }

        const cleanSymbol = symbol.trim().toUpperCase();

        // Handle special cases
        if (cleanSymbol.includes('-USD')) {
            return `BINANCE:${cleanSymbol.replace('-USD', 'USD')}`;
        }
        
        if (cleanSymbol.includes('=X')) {
            return `FX:${cleanSymbol.replace('=X', '')}`;
        }

        // Handle Oslo Børs and other Nordic exchanges
        for (const [suffix, exchange] of Object.entries(TV_CONFIG.exchange_mappings)) {
            if (cleanSymbol.endsWith(`.${suffix}`)) {
                return `${exchange}:${cleanSymbol.replace(`.${suffix}`, '')}`;
            }
        }

        // Default to NASDAQ for US stocks
        if (!cleanSymbol.includes(':')) {
            return `NASDAQ:${cleanSymbol}`;
        }

        return cleanSymbol;
    } catch (error) {
        console.error('Error formatting symbol:', error);
        return TV_CONFIG.default_symbol;
    }
}

// Initialize TradingView widgets with enhanced loading detection
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 TradingView Integration Initializing...');
    
    // Wait for TradingView to load
    let attempts = 0;
    const maxAttempts = 20;
    
    function checkTradingView() {
        attempts++;
        console.log(`Checking TradingView availability (attempt ${attempts}/${maxAttempts})`);
        
        if (typeof TradingView !== 'undefined' && TradingView.widget) {
            console.log('✅ TradingView is ready');
            initializeTradingViewCharts();
        } else if (attempts >= maxAttempts) {
            console.warn('❌ TradingView failed to load - showing fallback');
            showTradingViewFallback();
        } else {
            setTimeout(checkTradingView, 500);
        }
    }
    
    checkTradingView();
});

// Initialize TradingView widgets
let widgets = {
    main: null,
    technical: null,
    market: null,
    calendar: null
};

// Create and initialize TradingView widget
function createTradingViewWidget(containerId, symbol, widgetType = 'main') {
    try {
        // Hide any error messages
        const errorElement = document.querySelector('.tradingview-widget-error');
        if (errorElement) {
            errorElement.style.display = 'none';
        }

        // Show loading indicator
        const loadingElement = document.querySelector(`#${containerId} .loading-indicator`);
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }

        // Format symbol
        const formattedSymbol = formatSymbolForTradingView(symbol);

        // Widget configuration based on type
        let widgetConfig;
        switch (widgetType) {
            case 'main':
                widgetConfig = {
                    symbol: formattedSymbol,
                    interval: 'D',
                    timezone: 'Europe/Oslo',
                    theme: 'light',
                    style: '1',
                    locale: 'en',
                    toolbar_bg: '#f1f3f6',
                    enable_publishing: false,
                    allow_symbol_change: true,
                    container_id: containerId,
                    hide_side_toolbar: false,
                    studies: [
                        'MASimple@tv-basicstudies',
                        'RSI@tv-basicstudies',
                        'MACD@tv-basicstudies'
                    ]
                };
                break;

            case 'technical':
                widgetConfig = {
                    interval: '1D',
                    width: '100%',
                    isTransparent: true,
                    height: '100%',
                    symbol: formattedSymbol,
                    showIntervalTabs: true,
                    locale: 'en',
                    colorTheme: 'light',
                    container_id: containerId
                };
                break;

            case 'market':
                widgetConfig = {
                    width: '100%',
                    height: '100%',
                    symbolsGroups: [
                        { name: 'Oslo Børs', symbols: [
                            { name: 'OSL:EQNR' },
                            { name: 'OSL:DNB' },
                            { name: 'OSL:TEL' }
                        ]},
                        { name: 'US Tech', symbols: [
                            { name: 'NASDAQ:AAPL' },
                            { name: 'NASDAQ:MSFT' },
                            { name: 'NASDAQ:GOOGL' }
                        ]}
                    ],
                    showSymbolLogo: true,
                    colorTheme: 'light',
                    isTransparent: true,
                    container_id: containerId,
                    locale: 'en'
                };
                break;

            case 'calendar':
                widgetConfig = {
                    width: '100%',
                    height: '100%',
                    colorTheme: 'light',
                    isTransparent: true,
                    container_id: containerId,
                    locale: 'en'
                };
                break;
        }

        // Create widget based on type
        if (widgetType === 'main') {
            widgets[widgetType] = new TradingView.widget(widgetConfig);
        } else if (widgetType === 'technical') {
            widgets[widgetType] = new TradingView.TechnicalAnalysis(widgetConfig);
        } else if (widgetType === 'market') {
            widgets[widgetType] = new TradingView.MarketOverview(widgetConfig);
        } else if (widgetType === 'calendar') {
            widgets[widgetType] = new TradingView.EconomicCalendar(widgetConfig);
        }

        // Add error handling
        widgets[widgetType].onChartReady(() => {
            // Hide loading indicator
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
        });

    } catch (error) {
        console.error(`Error creating ${widgetType} widget:`, error);
        showWidgetError(containerId, error);
    }
}

// Show widget error
function showWidgetError(containerId, error) {
    const container = document.getElementById(containerId);
    if (container) {
        // Hide loading indicator
        const loadingElement = container.querySelector('.loading-indicator');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        // Show error message
        const errorHtml = `
            <div class="tradingview-widget-error text-center p-4">
                <i class="bi bi-exclamation-triangle text-warning" style="font-size: 2rem;"></i>
                <h6 class="mt-3">Kunne ikke laste TradingView chart</h6>
                <p class="text-muted small">Vennligst prøv å laste siden på nytt</p>
                <button onclick="reloadWidget('${containerId}')" class="btn btn-sm btn-outline-primary mt-2">
                    <i class="bi bi-arrow-clockwise"></i> Last på nytt
                </button>
            </div>
        `;
        container.innerHTML = errorHtml;
    }
}

// Reload widget
function reloadWidget(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        // Show loading indicator
        container.innerHTML = `
            <div class="loading-indicator text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Laster...</span>
                </div>
                <p class="text-muted mt-3">Laster TradingView chart...</p>
            </div>
        `;

        // Get current symbol from URL or default
        const urlParams = new URLSearchParams(window.location.search);
        const symbol = urlParams.get('symbol') || TV_CONFIG.default_symbol;

        // Determine widget type from container ID
        let widgetType = 'main';
        if (containerId.includes('technical')) widgetType = 'technical';
        if (containerId.includes('market')) widgetType = 'market';
        if (containerId.includes('calendar')) widgetType = 'calendar';

        // Recreate widget
        setTimeout(() => {
            createTradingViewWidget(containerId, symbol, widgetType);
        }, 500);
    }
}

// Load symbol and update widgets
function loadSymbol(symbol) {
    try {
        if (!symbol) return;

        // Update URL without reloading page
        const url = new URL(window.location);
        url.searchParams.set('symbol', symbol);
        window.history.pushState({}, '', url);

        // Update widgets
        const formattedSymbol = formatSymbolForTradingView(symbol);
        
        if (widgets.main && widgets.main.chart) {
            widgets.main.chart().setSymbol(formattedSymbol);
        }
        if (widgets.technical) {
            widgets.technical.setSymbol(formattedSymbol);
        }

        // Update page title
        document.title = `${symbol} - TradingView Charts - Aksjeradar`;

    } catch (error) {
        console.error('Error loading symbol:', error);
        showToast('Kunne ikke laste symbol. Prøv igjen senere.', 'error');
    }
}

// Show fallback when TradingView fails to load
function showTradingViewFallback() {
    const containers = [
        'tradingview_main_widget',
        'tradingview_technical_analysis',
        'tradingview_market_overview',
        'tradingview_economic_calendar'
    ];

    containers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="tradingview-widget-error text-center p-4">
                    <i class="bi bi-exclamation-triangle text-warning" style="font-size: 2rem;"></i>
                    <h6 class="mt-3">TradingView laster ikke</h6>
                    <p class="text-muted small">Vennligst sjekk nettverkstilkobling og prøv igjen</p>
                    <button onclick="location.reload()" class="btn btn-sm btn-outline-primary mt-2">
                        <i class="bi bi-arrow-clockwise"></i> Last siden på nytt
                    </button>
                </div>
            `;
        }
    });
}

// Initialize TradingView charts
function initializeTradingViewCharts() {
    // Get symbol from URL or default
    const urlParams = new URLSearchParams(window.location.search);
    const symbol = urlParams.get('symbol') || TV_CONFIG.default_symbol.split(':')[1];

    // Initialize main chart
    if (document.getElementById('tradingview_main_widget')) {
        createTradingViewWidget('tradingview_main_widget', symbol, 'main');
    }

    // Initialize technical analysis
    if (document.getElementById('tradingview_technical_analysis')) {
        createTradingViewWidget('tradingview_technical_analysis', symbol, 'technical');
    }

    // Initialize market overview
    if (document.getElementById('tradingview_market_overview')) {
        createTradingViewWidget('tradingview_market_overview', symbol, 'market');
    }

    // Initialize economic calendar
    if (document.getElementById('tradingview_economic_calendar')) {
        createTradingViewWidget('tradingview_economic_calendar', symbol, 'calendar');
    }

    // Add event listener for symbol search
    const symbolSearch = document.getElementById('symbolSearch');
    const loadChartButton = document.getElementById('loadChart');

    if (symbolSearch && loadChartButton) {
        // Set initial value
        symbolSearch.value = symbol;

        // Add event listeners
        loadChartButton.addEventListener('click', () => {
            loadSymbol(symbolSearch.value);
        });

        symbolSearch.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                loadSymbol(symbolSearch.value);
            }
        });
    }
    
    // We already handle chart creation in the createTradingViewWidget function above
}

// Enhanced fallback function has already been defined above

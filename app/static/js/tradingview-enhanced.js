/* TradingView Widget Enhanced Error Handling and Fallback */

// Global TradingView configuration
window.TRADINGVIEW_CONFIG = {
    script_loaded: false,
    retry_count: 0,
    max_retries: 3,
    default_symbol: 'NASDAQ:AAPL'
};

// Enhanced TradingView script loader with multiple fallbacks
function loadTradingViewScript() {
    return new Promise((resolve, reject) => {
        // Check if TradingView is already loaded
        if (typeof TradingView !== 'undefined' && TradingView.widget) {
            window.TRADINGVIEW_CONFIG.script_loaded = true;
            resolve();
            return;
        }

        // Try to load the script
        const script = document.createElement('script');
        script.src = 'https://s3.tradingview.com/tv.js';
        script.async = true;
        
        script.onload = function() {
            console.log('✅ TradingView script loaded successfully');
            window.TRADINGVIEW_CONFIG.script_loaded = true;
            
            // Wait a bit for TradingView to initialize
            setTimeout(() => {
                if (typeof TradingView !== 'undefined' && TradingView.widget) {
                    resolve();
                } else {
                    console.warn('⚠️ TradingView object not available after script load');
                    reject(new Error('TradingView not initialized'));
                }
            }, 500);
        };
        
        script.onerror = function() {
            console.error('❌ Failed to load TradingView script');
            reject(new Error('Failed to load TradingView script'));
        };
        
        // Add to head
        document.head.appendChild(script);
        
        // Timeout fallback
        setTimeout(() => {
            if (!window.TRADINGVIEW_CONFIG.script_loaded) {
                console.error('❌ TradingView script load timeout');
                reject(new Error('TradingView script load timeout'));
            }
        }, 10000);
    });
}

// Create TradingView widget with comprehensive error handling
function createTradingViewWidget(containerId, symbol = 'NASDAQ:AAPL') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('❌ TradingView container not found:', containerId);
        return false;
    }

    try {
        // Clear any existing content
        container.innerHTML = '';
        
        // Add loading message
        container.innerHTML = `
            <div class="d-flex align-items-center justify-content-center" style="height: 400px;">
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Laster...</span>
                    </div>
                    <div>Laster TradingView chart...</div>
                </div>
            </div>
        `;

        // Format symbol for TradingView
        const formattedSymbol = formatSymbolForTradingView(symbol);
        console.log('🚀 Creating TradingView widget for:', formattedSymbol);

        // Create the widget
        new TradingView.widget({
            autosize: true,
            symbol: formattedSymbol,
            interval: "D",
            timezone: "Europe/Oslo",
            theme: "light",
            style: "1",
            locale: "no",
            toolbar_bg: "#f1f3f6",
            enable_publishing: false,
            container_id: containerId,
            studies: [
                "Volume@tv-basicstudies",
                "MACD@tv-basicstudies"
            ],
            onChartReady: function() {
                console.log('✅ TradingView chart loaded successfully');
                // Remove loading message on success
            }
        });

        return true;
    } catch (error) {
        console.error('❌ Error creating TradingView widget:', error);
        showTradingViewError(container, symbol);
        return false;
    }
}

// Show error message when TradingView fails
function showTradingViewError(container, symbol) {
    container.innerHTML = `
        <div class="alert alert-warning h-100 d-flex align-items-center justify-content-center" style="min-height: 400px;">
            <div class="text-center">
                <i class="bi bi-exclamation-triangle fs-1 text-warning mb-3"></i>
                <h5>Kunne ikke laste TradingView chart</h5>
                <p class="mb-3">Chart for ${symbol} er midlertidig utilgjengelig.</p>
                <button class="btn btn-outline-primary" onclick="retryTradingView('${container.id}', '${symbol}')">
                    <i class="bi bi-arrow-clockwise me-2"></i>Prøv igjen
                </button>
            </div>
        </div>
    `;
}

// Retry TradingView widget creation
function retryTradingView(containerId, symbol) {
    if (window.TRADINGVIEW_CONFIG.retry_count >= window.TRADINGVIEW_CONFIG.max_retries) {
        console.error('❌ Max TradingView retries reached');
        return;
    }
    
    window.TRADINGVIEW_CONFIG.retry_count++;
    console.log(`🔄 Retrying TradingView (attempt ${window.TRADINGVIEW_CONFIG.retry_count})`);
    
    initializeTradingView(containerId, symbol);
}

// Format symbol for TradingView compatibility
function formatSymbolForTradingView(symbol) {
    if (!symbol) return 'NASDAQ:AAPL';
    
    const cleanSymbol = symbol.trim().toUpperCase();
    
    // Handle cryptocurrency
    if (cleanSymbol.includes('-USD') || cleanSymbol.includes('USD')) {
        const base = cleanSymbol.replace('-USD', '').replace('USD', '');
        return `BINANCE:${base}USD`;
    }
    
    // Handle Oslo Børs (.OL suffix)
    if (cleanSymbol.endsWith('.OL')) {
        const base = cleanSymbol.replace('.OL', '');
        return `OSL:${base}`;
    }
    
    // Handle other exchanges
    if (cleanSymbol.includes('.')) {
        return cleanSymbol; // Keep as is for other exchanges
    }
    
    // Default to NASDAQ for US symbols
    return `NASDAQ:${cleanSymbol}`;
}

// Main initialization function
function initializeTradingView(containerId, symbol) {
    loadTradingViewScript()
        .then(() => {
            // Small delay to ensure TradingView is fully ready
            setTimeout(() => {
                createTradingViewWidget(containerId, symbol);
            }, 100);
        })
        .catch(error => {
            console.error('❌ Failed to initialize TradingView:', error);
            const container = document.getElementById(containerId);
            if (container) {
                showTradingViewError(container, symbol);
            }
        });
}

// Auto-initialize TradingView widgets on page load
document.addEventListener('DOMContentLoaded', function() {
    // Find all TradingView containers and initialize them
    const containers = document.querySelectorAll('[id*="tradingview"]');
    containers.forEach(container => {
        const symbol = container.dataset.symbol || 'AAPL';
        setTimeout(() => {
            initializeTradingView(container.id, symbol);
        }, 500);
    });
});

// Export functions for global use
window.initializeTradingView = initializeTradingView;
window.retryTradingView = retryTradingView;
window.formatSymbolForTradingView = formatSymbolForTradingView;

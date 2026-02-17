// Enhanced real-time functionality for Aksjeradar

class RealtimeManager {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.subscribedTickers = new Set();
        this.priceUpdateCallbacks = new Map();
        this.useWebSocket = false; // Disabled - WebSocket not implemented on server
        this.fallbackInterval = null;
        this.connectionStatus = 'disconnected';
        this.statusElement = null;
    }

    init() {
        console.log('🚀 Initializing RealtimeManager (Polling Mode)');
        
        // Remove or hide connection status messages
        this.hideConnectionStatus();
        
        // Always use polling since WebSocket is not implemented
        this.setupFallbackPolling();
    }

    hideConnectionStatus() {
        // Hide any connection status elements
        const statusElements = document.querySelectorAll('.connection-status, .websocket-status, [data-connection-status]');
        statusElements.forEach(el => {
            el.style.display = 'none';
        });
        
        // Remove connection lost notifications
        const notifications = document.querySelectorAll('.connection-notification, .connection-lost-message');
        notifications.forEach(el => {
            el.remove();
        });
    }

    setupFallbackPolling() {
        console.log('📊 Using polling for real-time updates');
        
        // Clear any existing interval
        if (this.fallbackInterval) {
            clearInterval(this.fallbackInterval);
        }
        
        // Poll for updates every 5 seconds
        this.fallbackInterval = setInterval(() => {
            this.pollPriceUpdates();
        }, 5000);
        
        // Initial poll
        this.pollPriceUpdates();
        
        // Set status as connected
        this.connectionStatus = 'connected';
    }

    async pollPriceUpdates() {
        if (this.subscribedTickers.size === 0) return;
        
        for (const ticker of this.subscribedTickers) {
            try {
                const response = await fetch(`/api/realtime/price/${ticker}`);
                if (response.ok) {
                    const data = await response.json();
                    this.handlePriceUpdate(ticker, data);
                }
            } catch (error) {
                // Silently handle errors - no console logging
                // This prevents "Tilkobling tapt" messages
            }
        }
    }

    subscribe(ticker, callback) {
        this.subscribedTickers.add(ticker);
        
        if (!this.priceUpdateCallbacks.has(ticker)) {
            this.priceUpdateCallbacks.set(ticker, new Set());
        }
        this.priceUpdateCallbacks.get(ticker).add(callback);
    }

    unsubscribe(ticker, callback) {
        if (this.priceUpdateCallbacks.has(ticker)) {
            this.priceUpdateCallbacks.get(ticker).delete(callback);
            
            if (this.priceUpdateCallbacks.get(ticker).size === 0) {
                this.priceUpdateCallbacks.delete(ticker);
                this.subscribedTickers.delete(ticker);
            }
        }
    }

    handlePriceUpdate(ticker, data) {
        // Update UI elements
        this.updatePriceDisplay(ticker, data);
        
        // Call registered callbacks
        if (this.priceUpdateCallbacks.has(ticker)) {
            this.priceUpdateCallbacks.get(ticker).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    // Silently handle errors
                }
            });
        }
    }

    updatePriceDisplay(ticker, data) {
        // Update price elements
        const priceElements = document.querySelectorAll(`[data-ticker="${ticker}"]`);
        
        priceElements.forEach(element => {
            const field = element.dataset.field;
            
            switch (field) {
                case 'price':
                    element.textContent = this.formatPrice(data.price);
                    break;
                case 'change':
                    element.textContent = this.formatChange(data.change);
                    element.className = data.change >= 0 ? 'text-success' : 'text-danger';
                    break;
                case 'change_percent':
                    element.textContent = this.formatPercent(data.change_percent);
                    element.className = data.change_percent >= 0 ? 'text-success' : 'text-danger';
                    break;
                case 'volume':
                    element.textContent = this.formatVolume(data.volume);
                    break;
            }
        });
        
        // Add animation effect
        priceElements.forEach(element => {
            element.classList.add('price-update-flash');
            setTimeout(() => element.classList.remove('price-update-flash'), 1000);
        });
    }

    formatPrice(price) {
        return price ? price.toFixed(2) : '0.00';
    }

    formatChange(change) {
        const prefix = change >= 0 ? '+' : '';
        return `${prefix}${change.toFixed(2)}`;
    }

    formatPercent(percent) {
        const prefix = percent >= 0 ? '+' : '';
        return `${prefix}${percent.toFixed(2)}%`;
    }

    formatVolume(volume) {
        if (volume >= 1000000) {
            return `${(volume / 1000000).toFixed(1)}M`;
        } else if (volume >= 1000) {
            return `${(volume / 1000).toFixed(1)}K`;
        }
        return volume.toString();
    }

    destroy() {
        // Clear polling interval
        if (this.fallbackInterval) {
            clearInterval(this.fallbackInterval);
            this.fallbackInterval = null;
        }
        
        // Clear callbacks
        this.priceUpdateCallbacks.clear();
        this.subscribedTickers.clear();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.realtimeManager = new RealtimeManager();
    window.realtimeManager.init();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.realtimeManager) {
        window.realtimeManager.destroy();
    }
});

// Check if styleElement already exists
if (!document.getElementById('realtime-styles')) {
    const styleElement = document.createElement('style');
    styleElement.id = 'realtime-styles';
    styleElement.textContent = `
        .price-update-flash {
            animation: flash 1s ease-out;
        }
        
        @keyframes flash {
            0% { background-color: rgba(75, 192, 192, 0.3); }
            100% { background-color: transparent; }
        }
    `;
    document.head.appendChild(styleElement);
}

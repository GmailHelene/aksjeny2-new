/**
 * Real-time data service for frontend
 */
class RealTimeDataService {
    constructor() {
        this.updateInterval = 30000; // 30 seconds
        this.isRunning = false;
        this.intervalId = null;
        this.subscribers = new Map();
        this.lastUpdateTime = null;
        
        // Start automatically
        this.start();
    }
    
    /**
     * Start real-time updates
     */
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.updateMarketSummary();
        
        this.intervalId = setInterval(() => {
            this.updateMarketSummary();
            this.updateSubscribedTickers();
        }, this.updateInterval);
        
        console.log('Real-time data service started');
    }
    
    /**
     * Stop real-time updates
     */
    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        console.log('Real-time data service stopped');
    }
    
    /**
     * Subscribe to ticker updates
     */
    subscribeTicker(ticker, category, callback) {
        const key = `${category}_${ticker}`;
        if (!this.subscribers.has(key)) {
            this.subscribers.set(key, []);
        }
        this.subscribers.get(key).push(callback);
        
        // Immediately fetch data for this ticker
        this.fetchTickerData(ticker, category);
    }
    
    /**
     * Unsubscribe from ticker updates
     */
    unsubscribeTicker(ticker, category, callback) {
        const key = `${category}_${ticker}`;
        if (this.subscribers.has(key)) {
            const callbacks = this.subscribers.get(key);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
            if (callbacks.length === 0) {
                this.subscribers.delete(key);
            }
        }
    }
    
    /**
     * Update market summary
     */
    async updateMarketSummary() {
        try {
            const response = await fetch('/api/realtime/market-summary');
            const result = await response.json();
            
            if (result.success) {
                this.updateMarketSummaryUI(result.data);
                this.lastUpdateTime = new Date();
            }
        } catch (error) {
            console.error('Error updating market summary:', error);
        }
    }
    
    /**
     * Update subscribed tickers
     */
    async updateSubscribedTickers() {
        const tickersByCategory = new Map();
        
        // Group subscribers by category
        for (const [key, callbacks] of this.subscribers) {
            const [category, ticker] = key.split('_');
            if (!tickersByCategory.has(category)) {
                tickersByCategory.set(category, []);
            }
            tickersByCategory.get(category).push(ticker);
        }
        
        // Fetch data for each category
        for (const [category, tickers] of tickersByCategory) {
            try {
                const response = await fetch(`/api/realtime/batch-prices?tickers=${tickers.join(',')}&category=${category}`);
                const result = await response.json();
                
                if (result.success) {
                    for (const [ticker, data] of Object.entries(result.data)) {
                        const key = `${category}_${ticker}`;
                        if (this.subscribers.has(key)) {
                            this.subscribers.get(key).forEach(callback => {
                                callback({ticker, category, ...data});
                            });
                        }
                    }
                }
            } catch (error) {
                console.error(`Error updating ${category} tickers:`, error);
            }
        }
    }
    
    /**
     * Fetch data for a specific ticker
     */
    async fetchTickerData(ticker, category = 'oslo') {
        try {
            const response = await fetch(`/api/realtime/price/${ticker}?category=${category}`);
            const result = await response.json();
            
            if (result.success) {
                const key = `${category}_${ticker}`;
                if (this.subscribers.has(key)) {
                    this.subscribers.get(key).forEach(callback => {
                        callback(result.data);
                    });
                }
                return result.data;
            }
        } catch (error) {
            console.error(`Error fetching ${ticker} data:`, error);
        }
        return null;
    }
    
    /**
     * Update market summary UI elements
     */
    updateMarketSummaryUI(data) {
        // Update Oslo Børs summary
        if (data.oslo_bors && data.oslo_bors.status === 'active') {
            this.updateMarketCard('oslo', data.oslo_bors);
        }
        
        // Update Global markets summary
        if (data.global && data.global.status === 'active') {
            this.updateMarketCard('global', data.global);
        }
        
        // Update Crypto summary
        if (data.crypto && data.crypto.status === 'active') {
            this.updateMarketCard('crypto', data.crypto);
        }
        
        // Update last updated timestamp
        if (data.last_updated) {
            this.updateTimestamp(data.last_updated);
        }
    }
    
    /**
     * Update individual market card
     */
    updateMarketCard(market, data) {
        const cardSelector = `.market-card-${market}`;
        const card = document.querySelector(cardSelector);
        
        if (card) {
            // Update average change
            const avgChangeElement = card.querySelector('.avg-change');
            if (avgChangeElement && data.avg_change !== undefined) {
                const avgChange = data.avg_change;
                avgChangeElement.textContent = `${avgChange > 0 ? '+' : ''}${avgChange.toFixed(2)}%`;
                avgChangeElement.className = `avg-change ${avgChange > 0 ? 'text-success' : avgChange < 0 ? 'text-danger' : 'text-muted'}`;
            }
            
            // Update stock counts
            const positiveElement = card.querySelector('.positive-count');
            if (positiveElement && data.positive_count !== undefined) {
                positiveElement.textContent = data.positive_count;
            }
            
            const negativeElement = card.querySelector('.negative-count');
            if (negativeElement && data.negative_count !== undefined) {
                negativeElement.textContent = data.negative_count;
            }
        }
    }
    
    /**
     * Update price in table row
     */
    updatePriceInTable(ticker, data) {
        const row = document.querySelector(`tr[data-ticker="${ticker}"]`);
        if (!row) return;
        
        // Update price
        const priceCell = row.querySelector('.price-cell');
        if (priceCell) {
            priceCell.textContent = data.current_price.toFixed(2);
        }
        
        // Update change
        const changeCell = row.querySelector('.change-cell');
        if (changeCell) {
            const changeText = `${data.change > 0 ? '+' : ''}${data.change.toFixed(2)} (${data.change_percent > 0 ? '+' : ''}${data.change_percent.toFixed(2)}%)`;
            changeCell.textContent = changeText;
            changeCell.className = `change-cell ${data.change_percent > 0 ? 'text-success' : data.change_percent < 0 ? 'text-danger' : 'text-muted'}`;
        }
        
        // Update volume
        const volumeCell = row.querySelector('.volume-cell');
        if (volumeCell) {
            volumeCell.textContent = this.formatVolume(data.volume);
        }
        
        // Add flash effect
        row.classList.add('updated');
        setTimeout(() => row.classList.remove('updated'), 1000);
    }
    
    /**
     * Update timestamp display
     */
    updateTimestamp(timestamp) {
        const elements = document.querySelectorAll('.data-timestamp');
        const date = new Date(timestamp);
        const formatted = date.toLocaleString('no-NO', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        elements.forEach(element => {
            element.textContent = `Sist oppdatert: ${formatted}`;
        });
    }
    
    /**
     * Format volume for display
     */
    formatVolume(volume) {
        if (volume >= 1000000) {
            return `${(volume / 1000000).toFixed(1)}M`;
        } else if (volume >= 1000) {
            return `${(volume / 1000).toFixed(0)}K`;
        }
        return volume.toString();
    }
    
    /**
     * Get service status
     */
    async getStatus() {
        try {
            const response = await fetch('/api/realtime/status');
            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error getting service status:', error);
            return null;
        }
    }
}

// Global instance
const realTimeService = new RealTimeDataService();

// Auto-subscribe to visible tickers
document.addEventListener('DOMContentLoaded', function() {
    // Subscribe to tickers in tables
    const tickerRows = document.querySelectorAll('tr[data-ticker]');
    tickerRows.forEach(row => {
        const ticker = row.getAttribute('data-ticker');
        const category = row.getAttribute('data-category') || 'oslo';
        
        realTimeService.subscribeTicker(ticker, category, (data) => {
            realTimeService.updatePriceInTable(ticker, data);
        });
    });
    
    // Add live indicator
    const indicators = document.querySelectorAll('.live-indicator');
    indicators.forEach(indicator => {
        indicator.style.display = 'inline';
        indicator.classList.add('pulse');
    });
});

// CSS for update animations (add to existing styles)
const style = document.createElement('style');
style.textContent = `
    .updated {
        background-color: #fff3cd !important;
        transition: background-color 1s ease;
    }
    
    .live-indicator {
        display: none;
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .market-status-live {
        color: #28a745;
        font-weight: bold;
    }
    
    .market-status-closed {
        color: #dc3545;
        font-weight: bold;
    }
`;
document.head.appendChild(style);

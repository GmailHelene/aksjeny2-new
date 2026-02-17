/**
 * Norwegian Number and Currency Formatting Utilities
 */

class NorwegianFormatter {
    constructor() {
        this.locale = 'nb-NO';
        this.currencyCode = 'NOK';
    }

    /**
     * Format number with Norwegian thousand separators (space)
     * @param {number} value - The number to format
     * @param {number} decimals - Number of decimal places
     * @returns {string} Formatted number
     */
    formatNumber(value, decimals = 0) {
        if (value === null || value === undefined || isNaN(value)) {
            return '—';
        }
        
        return new Intl.NumberFormat(this.locale, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    }

    /**
     * Format currency in Norwegian format (kr suffix)
     * @param {number} value - The amount to format
     * @param {boolean} showDecimals - Whether to show decimals
     * @returns {string} Formatted currency
     */
    formatCurrency(value, showDecimals = true) {
        if (value === null || value === undefined || isNaN(value)) {
            return '—';
        }

        const decimals = showDecimals ? 2 : 0;
        const formatted = this.formatNumber(value, decimals);
        return `${formatted} kr`;
    }

    /**
     * Format percentage with Norwegian format
     * @param {number} value - The percentage value
     * @param {boolean} includeSign - Whether to include + for positive values
     * @returns {string} Formatted percentage
     */
    formatPercentage(value, includeSign = true) {
        if (value === null || value === undefined || isNaN(value)) {
            return '—';
        }

        const formatted = this.formatNumber(Math.abs(value), 2);
        const sign = value > 0 && includeSign ? '+' : value < 0 ? '-' : '';
        return `${sign}${formatted}%`;
    }

    /**
     * Format large numbers with abbreviations (k, M, B)
     * @param {number} value - The number to format
     * @returns {string} Formatted abbreviated number
     */
    formatLargeNumber(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '—';
        }

        const absValue = Math.abs(value);
        let formatted;

        if (absValue >= 1e9) {
            formatted = this.formatNumber(value / 1e9, 1) + ' mrd';
        } else if (absValue >= 1e6) {
            formatted = this.formatNumber(value / 1e6, 1) + ' mill';
        } else if (absValue >= 1e3) {
            formatted = this.formatNumber(value / 1e3, 1) + ' k';
        } else {
            formatted = this.formatNumber(value, 0);
        }

        return formatted;
    }

    /**
     * Format date in Norwegian format (dd.mm.yyyy)
     * @param {Date|string} date - The date to format
     * @param {boolean} includeTime - Whether to include time
     * @returns {string} Formatted date
     */
    formatDate(date, includeTime = false) {
        if (!date) return '—';

        const dateObj = date instanceof Date ? date : new Date(date);
        if (isNaN(dateObj.getTime())) return '—';

        const options = {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        };

        if (includeTime) {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }

        return new Intl.DateTimeFormat(this.locale, options).format(dateObj);
    }

    /**
     * Format relative time (e.g., "2 timer siden")
     * @param {Date|string} date - The date to format
     * @returns {string} Relative time string
     */
    formatRelativeTime(date) {
        if (!date) return '—';

        const dateObj = date instanceof Date ? date : new Date(date);
        if (isNaN(dateObj.getTime())) return '—';

        const now = new Date();
        const diffMs = now - dateObj;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Akkurat nå';
        if (diffMins < 60) return `${diffMins} ${diffMins === 1 ? 'minutt' : 'minutter'} siden`;
        if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? 'time' : 'timer'} siden`;
        if (diffDays < 30) return `${diffDays} ${diffDays === 1 ? 'dag' : 'dager'} siden`;

        return this.formatDate(dateObj);
    }

    /**
     * Format market cap with appropriate suffix
     * @param {number} value - Market cap value
     * @returns {string} Formatted market cap
     */
    formatMarketCap(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '—';
        }

        return this.formatLargeNumber(value) + ' kr';
    }

    /**
     * Format volume with appropriate suffix
     * @param {number} value - Volume value
     * @returns {string} Formatted volume
     */
    formatVolume(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '—';
        }

        return this.formatLargeNumber(value);
    }
}

// Create global instance
window.norwegianFormatter = new NorwegianFormatter();

// Auto-format elements with data-format attributes
document.addEventListener('DOMContentLoaded', function() {
    const formatter = window.norwegianFormatter;

    // Format numbers
    document.querySelectorAll('[data-format="number"]').forEach(el => {
        const value = parseFloat(el.textContent);
        const decimals = parseInt(el.getAttribute('data-decimals') || '0');
        el.textContent = formatter.formatNumber(value, decimals);
    });

    // Format currency
    document.querySelectorAll('[data-format="currency"]').forEach(el => {
        const value = parseFloat(el.textContent);
        const showDecimals = el.getAttribute('data-show-decimals') !== 'false';
        el.textContent = formatter.formatCurrency(value, showDecimals);
    });

    // Format percentages
    document.querySelectorAll('[data-format="percentage"]').forEach(el => {
        const value = parseFloat(el.textContent);
        const includeSign = el.getAttribute('data-include-sign') !== 'false';
        el.textContent = formatter.formatPercentage(value, includeSign);
    });

    // Format dates
    document.querySelectorAll('[data-format="date"]').forEach(el => {
        const date = el.textContent;
        const includeTime = el.getAttribute('data-include-time') === 'true';
        el.textContent = formatter.formatDate(date, includeTime);
    });

    // Format large numbers
    document.querySelectorAll('[data-format="large-number"]').forEach(el => {
        const value = parseFloat(el.textContent);
        el.textContent = formatter.formatLargeNumber(value);
    });

    // Format market cap
    document.querySelectorAll('[data-format="market-cap"]').forEach(el => {
        const value = parseFloat(el.textContent);
        el.textContent = formatter.formatMarketCap(value);
    });

    // Format volume
    document.querySelectorAll('[data-format="volume"]').forEach(el => {
        const value = parseFloat(el.textContent);
        el.textContent = formatter.formatVolume(value);
    });
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NorwegianFormatter;
}

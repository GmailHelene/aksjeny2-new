/**
 * Advanced Performance Optimization Service
 */
class PerformanceOptimizer {
    constructor() {
        this.imageObserver = null;
        this.intersectionObserver = null;
        this.prefetchQueue = new Set();
        this.componentObserver = null;
        this.performanceMetrics = new Map();
        this.cacheStrategies = new Map();
        this.init();
    }

    init() {
        this.setupLazyLoading();
        this.setupIntersectionObserver();
        this.setupPrefetching();
        this.optimizeScrolling();
        this.setupPerformanceMonitoring();
        this.setupComponentLazyLoading();
        this.setupServiceWorkerCaching();
        this.monitorCoreWebVitals();
        this.optimizeImageLoading();
    }

    setupLazyLoading() {
        // Lazy load images
        this.imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        this.imageObserver.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        // Observe all lazy images
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.classList.add('lazy');
            this.imageObserver.observe(img);
        });
    }

    setupComponentLazyLoading() {
        // Lazy load heavy components
        this.componentObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const component = entry.target;
                    this.loadComponent(component);
                    this.componentObserver.unobserve(component);
                }
            });
        }, {
            rootMargin: '100px 0px',
            threshold: 0.1
        });

        // Observe all lazy components
        document.querySelectorAll('.lazy-component').forEach(component => {
            this.componentObserver.observe(component);
        });
    }

    async loadComponent(component) {
        const componentType = component.dataset.component;
        const placeholder = component.querySelector('.component-placeholder');
        
        if (placeholder) {
            placeholder.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
        }

        try {
            switch (componentType) {
                case 'chart':
                    await this.loadChartComponent(component);
                    break;
                case 'table':
                    await this.loadTableComponent(component);
                    break;
                case 'widget':
                    await this.loadWidgetComponent(component);
                    break;
                case 'analysis':
                    await this.loadAnalysisComponent(component);
                    break;
                default:
                    console.warn('Unknown component type:', componentType);
            }
        } catch (error) {
            console.error('Failed to load component:', error);
            if (placeholder) {
                placeholder.innerHTML = '<div class="alert alert-warning alert-sm">Kunne ikke laste innhold</div>';
            }
        }
    }

    async loadChartComponent(component) {
        // Load Chart.js if not already loaded
        if (!window.Chart) {
            await this.loadScript('/static/js/chart.min.js');
        }

        const symbol = component.dataset.symbol;
        const chartType = component.dataset.chartType || 'line';
        const timeframe = component.dataset.timeframe || '1Y';

        const data = await this.fetchWithCache(`/api/stock/${symbol}/chart?timeframe=${timeframe}`);
        this.renderChart(component, data, chartType);
    }

    async loadTableComponent(component) {
        const endpoint = component.dataset.endpoint;
        const sortBy = component.dataset.sortBy || 'symbol';
        
        const data = await this.fetchWithCache(`${endpoint}?sort=${sortBy}`);
        this.renderTable(component, data);
    }

    async loadWidgetComponent(component) {
        const widgetType = component.dataset.widgetType;
        const refresh = component.dataset.refresh === 'true';
        
        const data = await this.fetchWithCache(`/api/widgets/${widgetType}`, refresh ? 0 : 300000);
        this.renderWidget(component, data, widgetType);
    }

    async loadAnalysisComponent(component) {
        const analysisType = component.dataset.analysisType;
        const symbol = component.dataset.symbol;
        
        const data = await this.fetchWithCache(`/api/analysis/${analysisType}/${symbol}`);
        this.renderAnalysis(component, data, analysisType);
    }

    setupServiceWorkerCaching() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/js/sw.js')
                .then(registration => {
                    console.log('ServiceWorker registered successfully');
                    this.setupAdvancedCaching();
                })
                .catch(error => {
                    console.log('ServiceWorker registration failed:', error);
                });
        }
    }

    setupAdvancedCaching() {
        // Override fetch for intelligent caching
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const [url, options] = args;
            
            // Check cache first for cacheable requests
            if (this.isCacheableRequest(url, options)) {
                const cached = this.getCachedResponse(url);
                if (cached && !this.isCacheExpired(cached)) {
                    return new Response(JSON.stringify(cached.data), {
                        headers: { 'Content-Type': 'application/json' }
                    });
                }
            }

            const startTime = performance.now();
            const response = await originalFetch(...args);
            const endTime = performance.now();

            // Track API performance
            this.trackAPIPerformance(url, endTime - startTime);

            // Cache successful responses
            if (response.ok && this.isCacheableRequest(url, options)) {
                const clonedResponse = response.clone();
                clonedResponse.json().then(data => {
                    this.cacheResponse(url, data);
                }).catch(() => {
                    // Ignore non-JSON responses
                });
            }

            return response;
        };
    }

    isCacheableRequest(url, options = {}) {
        if (options.method && options.method !== 'GET') return false;
        
        const cacheablePatterns = [
            '/api/market/',
            '/api/stock/',
            '/api/crypto/',
            '/api/currency/',
            '/api/analysis/',
            '/api/widgets/'
        ];
        
        return cacheablePatterns.some(pattern => url.includes(pattern));
    }

    getCachedResponse(url) {
        const cacheKey = `perf_cache_${url}`;
        const cached = sessionStorage.getItem(cacheKey);
        return cached ? JSON.parse(cached) : null;
    }

    isCacheExpired(cached) {
        return Date.now() > cached.expiry;
    }

    cacheResponse(url, data, ttl = 300000) { // 5 minutes default
        const cacheKey = `perf_cache_${url}`;
        const cacheEntry = {
            data: data,
            timestamp: Date.now(),
            expiry: Date.now() + ttl
        };
        
        try {
            sessionStorage.setItem(cacheKey, JSON.stringify(cacheEntry));
        } catch (error) {
            // Storage quota exceeded, clear old entries
            this.clearOldCacheEntries();
            try {
                sessionStorage.setItem(cacheKey, JSON.stringify(cacheEntry));
            } catch (retryError) {
                console.warn('Failed to cache response:', retryError);
            }
        }
    }

    clearOldCacheEntries() {
        const now = Date.now();
        Object.keys(sessionStorage).forEach(key => {
            if (key.startsWith('perf_cache_')) {
                try {
                    const cached = JSON.parse(sessionStorage.getItem(key));
                    if (now > cached.expiry) {
                        sessionStorage.removeItem(key);
                    }
                } catch (error) {
                    sessionStorage.removeItem(key);
                }
            }
        });
    }

    async fetchWithCache(url, ttl = 300000) {
        const cached = this.getCachedResponse(url);
        if (cached && !this.isCacheExpired(cached)) {
            return cached.data;
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        this.cacheResponse(url, data, ttl);
        return data;
    }

    monitorCoreWebVitals() {
        // Monitor Largest Contentful Paint (LCP)
        if ('PerformanceObserver' in window) {
            this.observeLCP();
            this.observeFID();
            this.observeCLS();
        }
    }

    observeLCP() {
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            
            this.performanceMetrics.set('LCP', lastEntry.startTime);
            this.sendPerformanceMetric('LCP', lastEntry.startTime);
        });
        
        observer.observe({ entryTypes: ['largest-contentful-paint'] });
    }

    observeFID() {
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            
            entries.forEach(entry => {
                const fid = entry.processingStart - entry.startTime;
                this.performanceMetrics.set('FID', fid);
                this.sendPerformanceMetric('FID', fid);
            });
        });
        
        observer.observe({ entryTypes: ['first-input'] });
    }

    observeCLS() {
        let cumulativeLayoutShift = 0;
        
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            
            entries.forEach(entry => {
                if (!entry.hadRecentInput) {
                    cumulativeLayoutShift += entry.value;
                }
            });
            
            this.performanceMetrics.set('CLS', cumulativeLayoutShift);
            this.sendPerformanceMetric('CLS', cumulativeLayoutShift);
        });
        
        observer.observe({ entryTypes: ['layout-shift'] });
    }

    trackAPIPerformance(url, duration) {
        const key = `api_${url.split('/').pop()}`;
        const existing = this.performanceMetrics.get(key) || [];
        existing.push(duration);
        
        // Keep only last 10 measurements
        if (existing.length > 10) {
            existing.shift();
        }
        
        this.performanceMetrics.set(key, existing);
        
        // Send if performance is degrading
        const avgDuration = existing.reduce((a, b) => a + b, 0) / existing.length;
        if (avgDuration > 2000) { // > 2 seconds
            this.sendPerformanceMetric('SlowAPI', avgDuration, url);
        }
    }

    sendPerformanceMetric(name, value, url = '') {
        // Send to analytics
        if (window.gtag) {
            gtag('event', 'performance_metric', {
                metric_name: name,
                metric_value: Math.round(value),
                page_url: url || window.location.pathname
            });
        }

        // Log in development
        if (window.location.hostname === 'localhost') {
            console.log(`${name}: ${Math.round(value)}${name === 'CLS' ? '' : 'ms'}${url ? ` (${url})` : ''}`);
        }
    }

    optimizeImageLoading() {
        // Convert to WebP if supported
        this.checkWebPSupport().then(supportsWebP => {
            if (supportsWebP) {
                document.querySelectorAll('img').forEach(img => {
                    if (img.src && !img.src.includes('.webp')) {
                        const webpSrc = img.src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
                        this.testImageExists(webpSrc).then(exists => {
                            if (exists) {
                                img.src = webpSrc;
                            }
                        });
                    }
                });
            }
        });

        // Add responsive image attributes
        this.addResponsiveImages();
    }

    async checkWebPSupport() {
        return new Promise(resolve => {
            const webP = new Image();
            webP.onload = webP.onerror = () => {
                resolve(webP.height === 2);
            };
            webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
        });
    }

    async testImageExists(src) {
        return new Promise(resolve => {
            const img = new Image();
            img.onload = () => resolve(true);
            img.onerror = () => resolve(false);
            img.src = src;
        });
    }

    addResponsiveImages() {
        document.querySelectorAll('img:not([sizes])').forEach(img => {
            if (img.offsetWidth > 300) {
                img.sizes = '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw';
            }
        });
    }

    renderChart(container, data, type) {
        const canvas = document.createElement('canvas');
        const chartId = `chart-${Date.now()}`;
        canvas.id = chartId;
        
        const placeholder = container.querySelector('.component-placeholder');
        if (placeholder) {
            placeholder.innerHTML = '';
            placeholder.appendChild(canvas);
        } else {
            container.appendChild(canvas);
        }

        // Simple chart rendering (replace with actual Chart.js implementation)
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: type,
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: data.label || 'Data',
                    data: data.values || [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }

    renderTable(container, data) {
        if (!Array.isArray(data) || data.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Ingen data tilgjengelig</div>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'table table-striped table-hover';
        
        // Headers
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = key.charAt(0).toUpperCase() + key.slice(1);
            th.style.cursor = 'pointer';
            th.addEventListener('click', () => this.sortTable(table, key));
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        data.forEach(row => {
            const tr = document.createElement('tr');
            Object.values(row).forEach(value => {
                const td = document.createElement('td');
                td.textContent = value;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        const placeholder = container.querySelector('.component-placeholder');
        if (placeholder) {
            placeholder.innerHTML = '';
            placeholder.appendChild(table);
        } else {
            container.appendChild(table);
        }
    }

    renderWidget(container, data, type) {
        const placeholder = container.querySelector('.component-placeholder');
        const target = placeholder || container;

        switch (type) {
            case 'market-summary':
                this.renderMarketSummary(target, data);
                break;
            case 'top-movers':
                this.renderTopMovers(target, data);
                break;
            case 'fear-greed':
                this.renderFearGreedIndex(target, data);
                break;
            default:
                target.innerHTML = '<div class="alert alert-info">Widget type ikke implementert</div>';
        }
    }

    renderAnalysis(container, data, type) {
        const placeholder = container.querySelector('.component-placeholder');
        const target = placeholder || container;

        const analysisHtml = `
            <div class="analysis-result">
                <h5>${data.title || 'Analyse'}</h5>
                <div class="analysis-content">
                    ${data.content || data.summary || 'Ingen analyse tilgjengelig'}
                </div>
                ${data.score ? `<div class="analysis-score">Score: ${data.score}/100</div>` : ''}
            </div>
        `;
        
        target.innerHTML = analysisHtml;
    }

    renderMarketSummary(container, data) {
        const html = `
            <div class="row">
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h6 class="card-title">Oslo Børs</h6>
                            <p class="h4 ${data.osebx?.change >= 0 ? 'text-success' : 'text-danger'}">
                                ${data.osebx?.value || '--'}
                            </p>
                            <small class="${data.osebx?.change >= 0 ? 'text-success' : 'text-danger'}">
                                ${data.osebx?.change >= 0 ? '+' : ''}${data.osebx?.change || 0}%
                            </small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h6 class="card-title">S&P 500</h6>
                            <p class="h4 ${data.sp500?.change >= 0 ? 'text-success' : 'text-danger'}">
                                ${data.sp500?.value || '--'}
                            </p>
                            <small class="${data.sp500?.change >= 0 ? 'text-success' : 'text-danger'}">
                                ${data.sp500?.change >= 0 ? '+' : ''}${data.sp500?.change || 0}%
                            </small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h6 class="card-title">NASDAQ</h6>
                            <p class="h4 ${data.nasdaq?.change >= 0 ? 'text-success' : 'text-danger'}">
                                ${data.nasdaq?.value || '--'}
                            </p>
                            <small class="${data.nasdaq?.change >= 0 ? 'text-success' : 'text-danger'}">
                                ${data.nasdaq?.change >= 0 ? '+' : ''}${data.nasdaq?.change || 0}%
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    renderTopMovers(container, data) {
        if (!Array.isArray(data) || data.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Ingen data tilgjengelig</div>';
            return;
        }

        let html = '<div class="list-group">';
        data.forEach(stock => {
            const changeClass = stock.change >= 0 ? 'text-success' : 'text-danger';
            const changeIcon = stock.change >= 0 ? '▲' : '▼';
            
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${stock.symbol}</h6>
                        <small class="text-muted">${stock.name || stock.symbol}</small>
                    </div>
                    <div class="text-end">
                        <span class="fw-bold">${stock.price || '--'}</span>
                        <br>
                        <small class="${changeClass}">
                            ${changeIcon} ${Math.abs(stock.change || 0).toFixed(2)}%
                        </small>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
    }

    renderFearGreedIndex(container, data) {
        const value = data.value || 50;
        const label = data.label || this.getFearGreedLabel(value);
        const color = this.getFearGreedColor(value);
        
        const html = `
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title">Fear & Greed Index</h5>
                    <div class="fear-greed-gauge mb-3">
                        <div class="gauge-value" style="color: ${color}">
                            <span class="display-4">${value}</span>
                        </div>
                        <div class="gauge-label" style="color: ${color}">
                            ${label}
                        </div>
                    </div>
                    <small class="text-muted">Kilde: Alternative.me</small>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    getFearGreedLabel(value) {
        if (value <= 25) return 'Extreme Fear';
        if (value <= 45) return 'Fear';
        if (value <= 55) return 'Neutral';
        if (value <= 75) return 'Greed';
        return 'Extreme Greed';
    }

    getFearGreedColor(value) {
        if (value <= 25) return '#d32f2f';
        if (value <= 45) return '#f57c00';
        if (value <= 55) return '#fbc02d';
        if (value <= 75) return '#689f38';
        return '#388e3c';
    }

    sortTable(table, column) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const columnIndex = Array.from(table.querySelectorAll('th')).findIndex(th => 
            th.textContent.toLowerCase() === column.toLowerCase()
        );

        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex].textContent;
            const bVal = b.cells[columnIndex].textContent;
            
            // Try numeric comparison first
            const aNum = parseFloat(aVal);
            const bNum = parseFloat(bVal);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return aNum - bNum;
            }
            
            // Fall back to string comparison
            return aVal.localeCompare(bVal);
        });

        rows.forEach(row => tbody.appendChild(row));
    }

    async loadScript(src) {
        return new Promise((resolve, reject) => {
            if (document.querySelector(`script[src="${src}"]`)) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
}

// Initialize performance optimizer
const performanceOptimizer = new PerformanceOptimizer();

// Export for use in other modules
window.performanceOptimizer = performanceOptimizer;

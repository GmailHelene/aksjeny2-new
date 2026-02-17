document.addEventListener('DOMContentLoaded', function() {
    let currentSymbol = '{{ symbol }}';
    let updateInterval;
    let priceChart; // Removed volumeChart and oscillatorChart as they no longer exist
    let currentTimeframe = '1m';
    let currentChartType = 'candlestick';
    let indicatorPanelVisible = false;
    let drawingMode = false;
    let isFullscreen = false;
    
    // Advanced Chart Configuration
    const chartConfig = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'day'
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    drawOnChartArea: true
                },
                border: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            y: {
                position: 'right',
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    drawOnChartArea: true
                },
                border: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    callback: function(value) {
                        return value.toFixed(2) + ' NOK';
                    }
                }
            }
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        size: 12
                    }
                }
            },
            tooltip: {
                enabled: false,
                external: function(context) {
                    showCustomTooltip(context);
                }
            }
        },
        elements: {
            point: {
                radius: 0,
                hoverRadius: 6
            },
            line: {
                borderWidth: 2
            }
        },
        animation: {
            duration: 750,
            easing: 'easeInOutQuart'
        }
    };

    // Initialize Charts
    initializeCharts();
    
    // Symbol autocomplete functionality
    const symbolInputs = ['#symbol', '#main-symbol-input'];
    const popularSymbols = ['EQNR.OL', 'DNB.OL', 'YAR.OL', 'TEL.OL', 'MOWI.OL', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL'];
    
    symbolInputs.forEach(inputSelector => {
        const input = document.querySelector(inputSelector);
        if (!input) return;
        
        const suggestionsId = inputSelector.includes('main') ? '#main-symbol-suggestions' : '#symbol-suggestions';
        const suggestions = document.querySelector(suggestionsId);
        
        input.addEventListener('input', function() {
            const query = this.value.toUpperCase();
            if (query.length < 1) {
                if (suggestions) suggestions.style.display = 'none';
                return;
            }
            
            // Call the search API endpoint to get stock suggestions
            fetch(`/api/stocks/search?q=${query}`)
                .then(response => response.json())
                .then(data => {
                    if (data.results && data.results.length > 0 && suggestions) {
                        suggestions.innerHTML = data.results.map(stock => 
                            `<a href="#" class="list-group-item list-group-item-action" data-symbol="${stock.symbol}">${stock.symbol} - ${stock.name}</a>`
                        ).join('');
                        suggestions.style.display = 'block';
                    } else if (suggestions) {
                        // Fallback to popular symbols if API returns no results
                        const matches = popularSymbols.filter(symbol => 
                            symbol.includes(query)
                        ).slice(0, 5);
                        
                        if (matches.length > 0) {
                            suggestions.innerHTML = matches.map(symbol => 
                                `<a href="#" class="list-group-item list-group-item-action" data-symbol="${symbol}">${symbol}</a>`
                            ).join('');
                            suggestions.style.display = 'block';
                        } else {
                            suggestions.style.display = 'none';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching stock suggestions:', error);
                    // Fallback to popular symbols on error
                    const matches = popularSymbols.filter(symbol => 
                        symbol.includes(query)
                    ).slice(0, 5);
                    
                    if (matches.length > 0 && suggestions) {
                        suggestions.innerHTML = matches.map(symbol => 
                            `<a href="#" class="list-group-item list-group-item-action" data-symbol="${symbol}">${symbol}</a>`
                        ).join('');
                        suggestions.style.display = 'block';
                    } else if (suggestions) {
                        suggestions.style.display = 'none';
                    }
                });
        });
        
        // Handle suggestion clicks
        const suggestionsList = document.querySelector(suggestionsId);
        if (suggestionsList) {
            suggestionsList.addEventListener('click', function(e) {
                e.preventDefault();
                const symbol = e.target.dataset.symbol;
                if (symbol) {
                    input.value = symbol;
                    suggestionsList.style.display = 'none';
                    
                    // Redirect to analysis if main input
                    if (inputSelector.includes('main')) {
                        window.location.href = `/analysis/technical?symbol=${symbol}`;
                    }
                }
            });
        }
    });
    
    // Initialize functions
    function initializeCharts() {
        initializePriceChart();
        // Volume and Oscillator charts removed as containers no longer exist
    }
    
    function initializePriceChart() {
        const ctx = document.getElementById('technicalChart');
        if (!ctx) return;
        
        // Hide loading spinner
        const loadingSpinner = document.getElementById('chart-loading');
        if (loadingSpinner) {
            setTimeout(() => loadingSpinner.style.display = 'none', 1000);
        }
        
        // Generate chart data
        const chartData = generateAdvancedChartData();
        
        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: 'Pris',
                        data: chartData.prices,
                        borderColor: '#0d6efd',
                        backgroundColor: currentChartType === 'area' ? 'rgba(13, 110, 253, 0.1)' : 'transparent',
                        fill: currentChartType === 'area',
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        borderWidth: 2
                    },
                    {
                        label: 'SMA 20',
                        data: chartData.sma20,
                        borderColor: '#dc3545',
                        backgroundColor: 'transparent',
                        borderDash: [5, 5],
                        pointRadius: 0,
                        borderWidth: 1.5,
                        hidden: !document.getElementById('showSMA20')?.checked
                    },
                    {
                        label: 'SMA 50',
                        data: chartData.sma50,
                        borderColor: '#198754',
                        backgroundColor: 'transparent',
                        borderDash: [10, 5],
                        pointRadius: 0,
                        borderWidth: 1.5,
                        hidden: !document.getElementById('showSMA50')?.checked
                    }
                ]
            },
            options: {
                ...chartConfig,
                onHover: (event, activeElements) => {
                    handleChartHover(event, activeElements);
                }
            }
        });
    }
    
    function generateAdvancedChartData() {
        const periods = currentTimeframe === '1d' ? 24 : 30;
        const labels = [];
        const prices = [];
        const volume = [];
        const sma20 = [];
        const sma50 = [];
        
        const basePrice = 100; // Default base price
        let currentPrice = basePrice * 0.95;
        
        for (let i = 0; i < periods; i++) {
            const date = new Date();
            date.setDate(date.getDate() - (periods - 1 - i));
            labels.push(date);
            
            // Generate realistic price movement
            const volatility = 0.02;
            const randomChange = (Math.random() - 0.5) * volatility;
            currentPrice *= (1 + randomChange);
            prices.push(parseFloat(currentPrice.toFixed(2)));
            
            // Generate volume
            const baseVolume = 2000000;
            const currentVolume = baseVolume * (0.5 + Math.random());
            volume.push(Math.round(currentVolume));
            
            // Simple moving averages
            if (i >= 19) {
                sma20.push(parseFloat((currentPrice * 0.98).toFixed(2)));
            } else {
                sma20.push(null);
            }
            
            if (i >= 49) {
                sma50.push(parseFloat((currentPrice * 0.97).toFixed(2)));
            } else {
                sma50.push(null);
            }
        }
        
        return { labels, prices, volume, sma20, sma50 };
    }
    
    function handleChartHover(event, activeElements) {
        // Chart hover functionality
    }
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.position-relative')) {
            document.querySelectorAll('[id$="-suggestions"]').forEach(el => {
                el.style.display = 'none';
            });
        }
    });
});

// Gauge Chart Implementation
function createGaugeChart(canvasId, value, min, max, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 60;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw gauge background
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, 0.25 * Math.PI);
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 8;
    ctx.stroke();
    
    // Draw gauge value
    const angle = 0.75 * Math.PI + (value / (max - min)) * 1.5 * Math.PI;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, angle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 8;
    ctx.stroke();
}

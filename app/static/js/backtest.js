// Backtest functionality for Aksjeradar
let currentChart = null;

async function quickBacktest(strategyType) {
    try {
        showLoading();
        const symbol = 'EQNR.OL'; // Default stock
        const startDate = getDefaultStartDate();
        const endDate = getDefaultEndDate();
        
        const response = await fetch('/backtest/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({
                symbol: symbol,
                start_date: startDate,
                end_date: endDate,
                strategy: strategyType
            })
        });

        if (!response.ok) throw new Error('Backtest request failed');
        
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        
        displayResults(data);
        showResultsSection();
    } catch (error) {
        console.error('Backtest error:', error);
        showError('Backtest feilet. Prøv igjen senere.');
    } finally {
        hideLoading();
    }
}

async function runBacktest(event) {
    event.preventDefault();
    
    try {
        showLoading();
        const form = document.getElementById('backtestForm');
        const formData = new FormData(form);
        
        const response = await fetch('/backtest/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify(Object.fromEntries(formData))
        });

        if (!response.ok) throw new Error('Backtest request failed');
        
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        
        displayResults(data);
        showResultsSection();
        $('#backtestModal').modal('hide');
    } catch (error) {
        console.error('Backtest error:', error);
        showError('Backtest feilet. Prøv igjen senere.');
    } finally {
        hideLoading();
    }
}

async function showComparison() {
    try {
        showLoading();
        const symbol = 'EQNR.OL'; // Default stock
        const startDate = getDefaultStartDate();
        const endDate = getDefaultEndDate();
        
        const response = await fetch('/backtest/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({
                symbol: symbol,
                start_date: startDate,
                end_date: endDate
            })
        });

        if (!response.ok) throw new Error('Strategy comparison failed');
        
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        
        displayComparisonResults(data);
    } catch (error) {
        console.error('Comparison error:', error);
        showError('Strategi-sammenligning feilet. Prøv igjen senere.');
    } finally {
        hideLoading();
    }
}

function displayResults(data) {
    // Display metrics
    document.getElementById('total-return').textContent = 
        formatPercentage(data.metrics.total_return);
    document.getElementById('annual-return').textContent = 
        formatPercentage(data.metrics.annual_return);
    document.getElementById('max-drawdown').textContent = 
        formatPercentage(data.metrics.max_drawdown);
    document.getElementById('sharpe-ratio').textContent = 
        data.metrics.sharpe_ratio.toFixed(2);
        
    // Update chart
    updateChart(data);
    
    // Show trade list if available
    if (data.trades) {
        displayTrades(data.trades);
    }
}

function displayComparisonResults(data) {
    const resultsDiv = document.getElementById('comparison-results');
    resultsDiv.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">Strategi-sammenligning: ${data.symbol}</h5>
                <div class="text-muted small">Periode: ${data.period}</div>
            </div>
            <div class="card-body">
                <div class="table-responsive mb-4">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Strategi</th>
                                <th>Total Avkastning</th>
                                <th>Årlig Avkastning</th>
                                <th>Volatilitet</th>
                                <th>Max Drawdown</th>
                                <th>Sluttverdi</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.results.map(result => `
                                <tr>
                                    <td><strong>${result.strategy}</strong></td>
                                    <td class="${getReturnClass(result.metrics.total_return)}">
                                        ${formatPercentage(result.metrics.total_return)}
                                    </td>
                                    <td class="${getReturnClass(result.metrics.annual_return)}">
                                        ${formatPercentage(result.metrics.annual_return)}
                                    </td>
                                    <td>${formatPercentage(result.metrics.volatility)}</td>
                                    <td class="text-danger">
                                        ${formatPercentage(result.metrics.max_drawdown)}
                                    </td>
                                    <td>${formatCurrency(result.final_value)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div style="height: 400px;">
                    <canvas id="comparisonChart"></canvas>
                </div>
            </div>
        </div>
    `;
    
    // Create comparison chart
    createComparisonChart(data);
    showResultsSection();
}

function updateChart(data) {
    const ctx = document.getElementById('resultChart').getContext('2d');
    if (currentChart) {
        currentChart.destroy();
    }
    
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.portfolio_data.dates,
            datasets: [{
                label: 'Porteføljeverdi',
                data: data.portfolio_data.total_value,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Backtest Resultat - ${data.symbol}`
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

function createComparisonChart(data) {
    const ctx = document.getElementById('comparisonChart').getContext('2d');
    const colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'];
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.results[0].portfolio_data.dates,
            datasets: data.results.map((result, index) => ({
                label: result.strategy,
                data: result.portfolio_data.total_value,
                borderColor: colors[index % colors.length],
                tension: 0.1
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Strategi-sammenligning'
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// Utility functions
function formatPercentage(value) {
    return `${(value * 100).toFixed(2)}%`;
}

function formatCurrency(value) {
    return new Intl.NumberFormat('nb-NO', {
        style: 'currency',
        currency: 'NOK'
    }).format(value);
}

function getReturnClass(value) {
    return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : '';
}

function getDefaultStartDate() {
    const date = new Date();
    date.setFullYear(date.getFullYear() - 1);
    return date.toISOString().split('T')[0];
}

function getDefaultEndDate() {
    return new Date().toISOString().split('T')[0];
}

function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function showError(message) {
    const alertDiv = document.getElementById('error-alert');
    alertDiv.textContent = message;
    alertDiv.style.display = 'block';
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 5000);
}

function showResultsSection() {
    document.getElementById('results-section').style.display = 'block';
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const backtestForm = document.getElementById('backtestForm');
    if (backtestForm) {
        backtestForm.addEventListener('submit', runBacktest);
    }
});

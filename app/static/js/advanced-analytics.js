/**
 * Advanced Analytics Module
 * Handles ML predictions, portfolio optimization, and risk management
 */

class AdvancedAnalytics {
    constructor() {
        this.baseURL = '/advanced-analytics/api';
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // ML Prediction listeners
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-ml-predict]')) {
                this.handleMLPrediction(e.target);
            }
            if (e.target.matches('[data-portfolio-optimize]')) {
                this.handlePortfolioOptimization(e.target);
            }
            if (e.target.matches('[data-risk-analysis]')) {
                this.handleRiskAnalysis(e.target);
            }
        });
    }

    // ML Prediction Methods
    async predictStock(symbol, days = 30) {
        try {
            const response = await fetch(`${this.baseURL}/ml/predict/${symbol}?days=${days}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayPrediction(data.prediction);
                return data.prediction;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Prediction error:', error);
            this.showError('Kunne ikke generere prediksjon');
        }
    }

    async batchPredict(symbols, days = 30) {
        try {
            const response = await fetch(`${this.baseURL}/ml/batch-predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbols, days })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayBatchPredictions(data.predictions);
                return data.predictions;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Batch prediction error:', error);
            this.showError('Kunne ikke generere batch-prediksjoner');
        }
    }

    async getMarketAnalysis() {
        try {
            const response = await fetch(`${this.baseURL}/ml/market-analysis`);
            const data = await response.json();
            
            if (data.success) {
                this.displayMarketAnalysis(data.analysis);
                return data.analysis;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Market analysis error:', error);
            this.showError('Kunne ikke hente markedsanalyse');
        }
    }

    // Portfolio Optimization Methods
    async optimizePortfolio(symbols, weights = null, method = 'sharpe') {
        try {
            const response = await fetch(`${this.baseURL}/portfolio/optimize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbols, weights, method })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayOptimization(data.optimization);
                return data.optimization;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Portfolio optimization error:', error);
            this.showError('Kunne ikke optimalisere portefølje');
        }
    }

    async generateEfficientFrontier(symbols, numPortfolios = 10000) {
        try {
            const response = await fetch(`${this.baseURL}/portfolio/efficient-frontier`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbols, num_portfolios: numPortfolios })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayEfficientFrontier(data.frontier);
                return data.frontier;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Efficient frontier error:', error);
            this.showError('Kunne ikke generere effisient frontier');
        }
    }

    async rebalancePortfolio(currentPortfolio, targetAllocation) {
        try {
            const response = await fetch(`${this.baseURL}/portfolio/rebalance`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    current_portfolio: currentPortfolio,
                    target_allocation: targetAllocation 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayRebalancing(data.rebalancing);
                return data.rebalancing;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Rebalancing error:', error);
            this.showError('Kunne ikke rebalansere portefølje');
        }
    }

    // Risk Management Methods
    async calculatePortfolioRisk(portfolio, timeframe = 252) {
        try {
            const response = await fetch(`${this.baseURL}/risk/portfolio-risk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ portfolio, timeframe })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayRiskMetrics(data.risk_metrics);
                return data.risk_metrics;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Risk calculation error:', error);
            this.showError('Kunne ikke beregne porteføljerisiko');
        }
    }

    async performVarAnalysis(portfolio, confidenceLevel = 0.95, timeHorizon = 1) {
        try {
            const response = await fetch(`${this.baseURL}/risk/var-analysis`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    portfolio,
                    confidence_level: confidenceLevel,
                    time_horizon: timeHorizon 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayVarAnalysis(data.var_analysis);
                return data.var_analysis;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('VaR analysis error:', error);
            this.showError('Kunne ikke utføre VaR-analyse');
        }
    }

    async stressTestPortfolio(portfolio, scenario = 'market_crash') {
        try {
            const response = await fetch(`${this.baseURL}/risk/stress-test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ portfolio, scenario })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayStressTest(data.stress_test);
                return data.stress_test;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Stress test error:', error);
            this.showError('Kunne ikke utføre stresstest');
        }
    }

    async runMonteCarloSimulation(portfolio, simulations = 10000, timeHorizon = 252) {
        try {
            const response = await fetch(`${this.baseURL}/risk/monte-carlo`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    portfolio,
                    simulations,
                    time_horizon: timeHorizon 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayMonteCarloResults(data.monte_carlo);
                return data.monte_carlo;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Monte Carlo simulation error:', error);
            this.showError('Kunne ikke kjøre Monte Carlo-simulering');
        }
    }

    // Display Methods
    displayPrediction(prediction) {
        const container = document.getElementById('ml-prediction-results');
        if (!container) return;

        const html = `
            <div class="card mt-3">
                <div class="card-header">
                    <h5>ML Prediksjon - ${prediction.symbol}</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Nåværende pris:</strong> $${prediction.current_price?.toFixed(2) || 'N/A'}</p>
                            <p><strong>Predikert pris:</strong> $${prediction.predicted_price?.toFixed(2) || 'N/A'}</p>
                            <p><strong>Forventet endring:</strong> ${prediction.price_change_percent?.toFixed(2) || 'N/A'}%</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Konfidens:</strong> ${(prediction.confidence * 100)?.toFixed(1) || 'N/A'}%</p>
                            <p><strong>Trend:</strong> ${prediction.trend || 'N/A'}</p>
                            <p><strong>Volatilitet:</strong> ${prediction.volatility?.toFixed(3) || 'N/A'}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    displayOptimization(optimization) {
        const container = document.getElementById('portfolio-optimization-results');
        if (!container) return;

        const weightsHtml = Object.entries(optimization.optimal_weights || {})
            .map(([symbol, weight]) => `
                <tr>
                    <td>${symbol}</td>
                    <td>${(weight * 100).toFixed(2)}%</td>
                </tr>
            `).join('');

        const html = `
            <div class="card mt-3">
                <div class="card-header">
                    <h5>Porteføljeoptimalisering</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Optimal Allokering</h6>
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Symbol</th>
                                        <th>Vekt</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${weightsHtml}
                                </tbody>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h6>Porteføljemetrikker</h6>
                            <p><strong>Forventet avkastning:</strong> ${(optimization.expected_return * 100)?.toFixed(2) || 'N/A'}%</p>
                            <p><strong>Volatilitet:</strong> ${(optimization.volatility * 100)?.toFixed(2) || 'N/A'}%</p>
                            <p><strong>Sharpe Ratio:</strong> ${optimization.sharpe_ratio?.toFixed(3) || 'N/A'}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    displayRiskMetrics(riskMetrics) {
        const container = document.getElementById('risk-analysis-results');
        if (!container) return;

        const html = `
            <div class="card mt-3">
                <div class="card-header">
                    <h5>Risikoanalyse</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Volatilitetsmetrikker</h6>
                            <p><strong>Volatilitet:</strong> ${(riskMetrics.volatility * 100)?.toFixed(2) || 'N/A'}%</p>
                            <p><strong>Beta:</strong> ${riskMetrics.beta?.toFixed(3) || 'N/A'}</p>
                            <p><strong>Treynor Ratio:</strong> ${riskMetrics.treynor_ratio?.toFixed(3) || 'N/A'}</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Drawdown Metrikker</h6>
                            <p><strong>Max Drawdown:</strong> ${(riskMetrics.max_drawdown * 100)?.toFixed(2) || 'N/A'}%</p>
                            <p><strong>VaR (95%):</strong> ${(riskMetrics.var_95 * 100)?.toFixed(2) || 'N/A'}%</p>
                            <p><strong>CVaR (95%):</strong> ${(riskMetrics.cvar_95 * 100)?.toFixed(2) || 'N/A'}%</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    // Event Handlers
    handleMLPrediction(element) {
        const symbol = element.dataset.symbol;
        const days = parseInt(element.dataset.days) || 30;
        
        if (symbol) {
            this.predictStock(symbol, days);
        }
    }

    handlePortfolioOptimization(element) {
        const symbols = element.dataset.symbols?.split(',') || [];
        const method = element.dataset.method || 'sharpe';
        
        if (symbols.length > 0) {
            this.optimizePortfolio(symbols, null, method);
        }
    }

    handleRiskAnalysis(element) {
        const portfolioData = element.dataset.portfolio;
        
        if (portfolioData) {
            try {
                const portfolio = JSON.parse(portfolioData);
                this.calculatePortfolioRisk(portfolio);
            } catch (error) {
                console.error('Invalid portfolio data:', error);
                this.showError('Ugyldig porteføljedata');
            }
        }
    }

    // Utility Methods
    showError(message) {
        // Show error message to user
        const errorContainer = document.getElementById('error-messages');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        } else {
            console.error('Error:', message);
        }
    }

    showSuccess(message) {
        // Show success message to user
        const successContainer = document.getElementById('success-messages');
        if (successContainer) {
            successContainer.innerHTML = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.advancedAnalytics = new AdvancedAnalytics();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedAnalytics;
}

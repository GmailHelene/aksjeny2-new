/**
 * Demo Page Interactive Functions - Clean Version
 * Provides working demonstrations of all premium features
 */

// Track demo progress
var demoProgress = 0;
var maxDemoFeatures = 8;

function updateDemoProgress() {
    demoProgress = Math.min(demoProgress + 1, maxDemoFeatures);
    var percentage = (demoProgress / maxDemoFeatures) * 100;
    
    var progressBar = document.getElementById('demo-progress-bar');
    if (progressBar) {
        var bar = progressBar.querySelector('.progress-bar');
        if (bar) {
            bar.style.width = percentage + '%';
        }
    }
}

function showNotification(message, type) {
    type = type || 'info';
    // Create and show notification
    var notification = document.createElement('div');
    notification.className = 'alert alert-' + type + ' alert-dismissible fade show position-fixed';
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(function() {
        if (notification && notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

function displayDemoResult(title, content, type) {
    type = type || 'success';
    var container = document.getElementById('demo-result-container');
    if (!container) return;
    
    var cardHTML = '<div class="card border-' + type + '">' +
        '<div class="card-header bg-' + type + ' text-white">' +
        '<h6 class="mb-0">' + title + '</h6>' +
        '</div>' +
        '<div class="card-body">' +
        content +
        '<div class="mt-3">' +
        '<small class="text-muted">' +
        '<i class="bi bi-info-circle"></i> Dette er demo-data. Oppgrader for ekte real-time analyser!' +
        '</small>' +
        '</div>' +
        '</div>' +
        '</div>';
        
    container.innerHTML = cardHTML;
    updateDemoProgress();
}

// Demo AI Analysis function
function demoAIAnalysis() {
    showNotification('Starter AI-analyse...', 'info');
    var container = document.getElementById('demo-result-container');
    if (container) {
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Analyserer med AI...</p></div>';
    }
    
    setTimeout(function() {
        var analysisHTML = '<div class="card border-primary">' +
            '<div class="card-header bg-primary text-white">' +
            '<h6 class="mb-0"><i class="bi bi-robot"></i> AI Markedsanalyse</h6>' +
            '</div>' +
            '<div class="card-body">' +
            '<div class="row">' +
            '<div class="col-md-6">' +
            '<h6>Teknisk Analyse</h6>' +
            '<p><strong>Trend:</strong> <span class="badge bg-success">Bullish</span></p>' +
            '<p><strong>RSI:</strong> 67.3 (Kjøp signal)</p>' +
            '<p><strong>MACD:</strong> Positiv crossover</p>' +
            '</div>' +
            '<div class="col-md-6">' +
            '<h6>Sentiment Analyse</h6>' +
            '<p><strong>Marked stemning:</strong> 78% Positiv</p>' +
            '<p><strong>Sosiale medier:</strong> Stigende interesse</p>' +
            '<p><strong>Nyheter:</strong> 85% Positive</p>' +
            '</div>' +
            '</div>' +
            '<div class="alert alert-info mt-3">' +
            '<i class="bi bi-lightbulb"></i> <strong>AI Anbefaling:</strong> Kjøp - Sterke tekniske signaler og positiv sentiment' +
            '</div>' +
            '</div>' +
            '</div>';
        
        if (container) {
            container.innerHTML = analysisHTML;
        }
        showNotification('AI-analyse fullført!', 'success');
        updateDemoProgress();
    }, 2000);
}

// Demo Graham Analysis function
function demoGrahamAnalysis() {
    showNotification('Starter Benjamin Graham analyse...', 'info');
    var container = document.getElementById('demo-result-container');
    if (container) {
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-success" role="status"></div><p class="mt-2">Beregner verdi...</p></div>';
    }
    
    setTimeout(function() {
        var grahamHTML = '<div class="card border-success">' +
            '<div class="card-header bg-success text-white">' +
            '<h6 class="mb-0"><i class="bi bi-calculator"></i> Benjamin Graham Verdsettelse</h6>' +
            '</div>' +
            '<div class="card-body">' +
            '<div class="row">' +
            '<div class="col-md-6">' +
            '<h6>Finansielle Nøkkeltall</h6>' +
            '<p><strong>P/E Ratio:</strong> 12.4 ✅</p>' +
            '<p><strong>P/B Ratio:</strong> 1.8 ✅</p>' +
            '<p><strong>Gjeld/Egenkapital:</strong> 0.34 ✅</p>' +
            '<p><strong>Current Ratio:</strong> 2.1 ✅</p>' +
            '</div>' +
            '<div class="col-md-6">' +
            '<h6>Graham Kriterier</h6>' +
            '<p><strong>Oppfylt:</strong> 8 av 9 kriterier</p>' +
            '<p><strong>Sikkerhet margin:</strong> 25%</p>' +
            '<p><strong>Estimert verdi:</strong> 142 NOK</p>' +
            '<p><strong>Nåværende pris:</strong> 106 NOK</p>' +
            '</div>' +
            '</div>' +
            '<div class="alert alert-success mt-3">' +
            '<i class="bi bi-check-circle"></i> <strong>Graham Vurdering:</strong> Undervurdert aksje med solid fundamental' +
            '</div>' +
            '</div>' +
            '</div>';
        
        if (container) {
            container.innerHTML = grahamHTML;
        }
        showNotification('Graham analyse fullført!', 'success');
        updateDemoProgress();
    }, 2200);
}

// Demo Short Analysis function  
function demoShortAnalysis() {
    showNotification('Analyserer short muligheter...', 'warning');
    var container = document.getElementById('demo-result-container');
    if (container) {
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-warning" role="status"></div><p class="mt-2">Søker etter svakheter...</p></div>';
    }
    
    setTimeout(function() {
        var shortHTML = '<div class="card border-warning">' +
            '<div class="card-header bg-warning text-dark">' +
            '<h6 class="mb-0"><i class="bi bi-graph-down"></i> Short Analyse</h6>' +
            '</div>' +
            '<div class="card-body">' +
            '<div class="row">' +
            '<div class="col-md-6">' +
            '<h6>Risikofaktorer</h6>' +
            '<p><strong>Høy P/E:</strong> 34.2 ⚠️</p>' +
            '<p><strong>Gjeld nivå:</strong> 78% ⚠️</p>' +
            '<p><strong>Insider salg:</strong> Økning ⚠️</p>' +
            '<p><strong>Margin press:</strong> Synkende ⚠️</p>' +
            '</div>' +
            '<div class="col-md-6">' +
            '<h6>Short Indikatorer</h6>' +
            '<p><strong>Short interesse:</strong> 18.5%</p>' +
            '<p><strong>Borrow rate:</strong> 12.3%</p>' +
            '<p><strong>Days to cover:</strong> 4.2</p>' +
            '<p><strong>Float short:</strong> 23%</p>' +
            '</div>' +
            '</div>' +
            '<div class="alert alert-warning mt-3">' +
            '<i class="bi bi-exclamation-triangle"></i> <strong>Short Vurdering:</strong> Moderat short kandidat - høy risiko/belønning' +
            '</div>' +
            '</div>' +
            '</div>';
        
        if (container) {
            container.innerHTML = shortHTML;
        }
        showNotification('Short analyse fullført!', 'warning');
        updateDemoProgress();
    }, 1800);
}

// Demo Warren Buffett function
function demoWarrenBuffett() {
    showNotification('Starter Buffett-stil analyse...', 'info');
    var container = document.getElementById('demo-result-container');
    if (container) {
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-info" role="status"></div><p class="mt-2">Evaluerer qualitet...</p></div>';
    }
    
    setTimeout(function() {
        var buffettHTML = '<div class="card border-info">' +
            '<div class="card-header bg-info text-white">' +
            '<h6 class="mb-0"><i class="bi bi-gem"></i> Warren Buffett Analyse</h6>' +
            '</div>' +
            '<div class="card-body">' +
            '<div class="row">' +
            '<div class="col-md-6">' +
            '<h6>Kvalitetskriterier</h6>' +
            '<p><strong>ROE (10 år avg):</strong> 16.8% ✅</p>' +
            '<p><strong>Konsistent vekst:</strong> 9 av 10 år ✅</p>' +
            '<p><strong>Konkurransefortrinn:</strong> Sterkt ✅</p>' +
            '<p><strong>Ledelse kvalitet:</strong> Høy ✅</p>' +
            '</div>' +
            '<div class="col-md-6">' +
            '<h6>Verdsettelse</h6>' +
            '<p><strong>FCF Yield:</strong> 8.2%</p>' +
            '<p><strong>ROIC:</strong> 14.5%</p>' +
            '<p><strong>Debt/EBITDA:</strong> 1.8</p>' +
            '<p><strong>Payout Ratio:</strong> 35%</p>' +
            '</div>' +
            '</div>' +
            '<div class="alert alert-primary mt-3">' +
            '<i class="bi bi-star"></i> <strong>Buffett Score:</strong> 8.4/10 - Høykvalitets selskap med rimelig pris' +
            '</div>' +
            '</div>' +
            '</div>';
        
        if (container) {
            container.innerHTML = buffettHTML;
        }
        showNotification('Buffett analyse fullført!', 'primary');
        updateDemoProgress();
    }, 2400);
}

// Demo Screener function
function demoScreener() {
    showNotification('Starter avansert screening...', 'info');
    var container = document.getElementById('demo-result-container');
    if (container) {
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-secondary" role="status"></div><p class="mt-2">Screener 2847 aksjer...</p></div>';
    }
    
    setTimeout(function() {
        var screenerHTML = '<div class="card border-secondary">' +
            '<div class="card-header bg-secondary text-white">' +
            '<h6 class="mb-0"><i class="bi bi-funnel"></i> Avansert Aksjescreener Resultater</h6>' +
            '</div>' +
            '<div class="card-body">' +
            '<p><strong>Screening kriterier:</strong> P/E < 15, ROE > 12%, Gjeld/Egenkapital < 0.5</p>' +
            '<div class="table-responsive">' +
            '<table class="table table-striped table-sm">' +
            '<thead><tr><th>Aksje</th><th>Pris</th><th>P/E</th><th>ROE</th><th>Score</th></tr></thead>' +
            '<tbody>' +
            '<tr><td><strong>DNB ASA</strong></td><td>188.50</td><td>8.2</td><td>14.8%</td><td><span class="badge bg-success">9.2</span></td></tr>' +
            '<tr><td><strong>Equinor ASA</strong></td><td>312.20</td><td>12.4</td><td>18.1%</td><td><span class="badge bg-success">8.9</span></td></tr>' +
            '<tr><td><strong>Telenor ASA</strong></td><td>142.80</td><td>13.1</td><td>15.2%</td><td><span class="badge bg-primary">8.1</span></td></tr>' +
            '<tr><td><strong>Norsk Hydro</strong></td><td>68.45</td><td>11.8</td><td>16.4%</td><td><span class="badge bg-primary">7.8</span></td></tr>' +
            '<tr><td><strong>Storebrand</strong></td><td>94.20</td><td>14.2</td><td>13.5%</td><td><span class="badge bg-warning">7.4</span></td></tr>' +
            '</tbody>' +
            '</table>' +
            '</div>' +
            '<p class="text-muted mt-3"><i class="bi bi-info-circle"></i> Demo resultater - oppgrader for avansert screening!</p>' +
            '</div>' +
            '</div>';
        
        if (container) {
            container.innerHTML = screenerHTML;
        }
        showNotification('Screener fullført! Fant 23 aksjer.', 'success');
        updateDemoProgress();
    }, 2500);
}

// Demo Insider Trading function
function demoInsiderTrading() {
    showNotification('Analyserer insider aktivitet...', 'info');
    var container = document.getElementById('demo-result-container');
    if (container) {
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-dark" role="status"></div><p class="mt-2">Henter insider data...</p></div>';
    }
    
    setTimeout(function() {
        var insiderHTML = '<div class="card border-dark">' +
            '<div class="card-header bg-dark text-white">' +
            '<h6 class="mb-0"><i class="bi bi-person-badge"></i> Insider Trading Analyse</h6>' +
            '</div>' +
            '<div class="card-body">' +
            '<div class="row">' +
            '<div class="col-md-6">' +
            '<h6>Siste Transaksjoner</h6>' +
            '<div class="list-group list-group-flush">' +
            '<div class="list-group-item d-flex justify-content-between align-items-center">' +
            'CEO kjøp: 50.000 aksjer <span class="badge bg-success">+2.8M</span>' +
            '</div>' +
            '<div class="list-group-item d-flex justify-content-between align-items-center">' +
            'CFO kjøp: 25.000 aksjer <span class="badge bg-success">+1.4M</span>' +
            '</div>' +
            '<div class="list-group-item d-flex justify-content-between align-items-center">' +
            'Styremedlem salg: 10.000 <span class="badge bg-warning">-0.6M</span>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="col-md-6">' +
            '<h6>Insider Sentiment</h6>' +
            '<p><strong>Kjøp/Salg Ratio:</strong> 3.2:1 ✅</p>' +
            '<p><strong>Netto volum:</strong> +4.6M NOK</p>' +
            '<p><strong>Aktivitet trend:</strong> Økende kjøp</p>' +
            '<p><strong>Confidence Score:</strong> 87%</p>' +
            '</div>' +
            '</div>' +
            '<div class="alert alert-success mt-3">' +
            '<i class="bi bi-trending-up"></i> <strong>Insider Signal:</strong> Sterkt kjøpssignal fra ledelsen' +
            '</div>' +
            '</div>' +
            '</div>';
        
        if (container) {
            container.innerHTML = insiderHTML;
        }
        showNotification('Insider analyse fullført!', 'success');
        updateDemoProgress();
    }, 2000);
}

// Make functions globally accessible
window.demoAIAnalysis = function(symbol) {
    symbol = symbol || 'EQNR.OL';
    showNotification('Starter AI-analyse...', 'info');
    
    setTimeout(function() {
        var content = '<div class="row">' +
            '<div class="col-md-6">' +
            '<h6><i class="bi bi-robot"></i> AI Anbefaling</h6>' +
            '<div class="alert alert-success">' +
            '<strong>KJØP</strong> - Høy konfidens (87%)' +
            '</div>' +
            '<p><strong>Kursmål:</strong> 320-350 NOK</p>' +
            '<p><strong>Tidshorisont:</strong> 6-12 måneder</p>' +
            '</div>' +
            '<div class="col-md-6">' +
            '<h6><i class="bi bi-graph-up"></i> Nøkkel Signaler</h6>' +
            '<ul class="list-unstyled">' +
            '<li>✅ Sterk teknisk momentum</li>' +
            '<li>✅ Økende institusjonell interesse</li>' +
            '<li>✅ Positive fundamental faktorer</li>' +
            '<li>⚠️ Økt volatilitet forventes</li>' +
            '</ul>' +
            '</div>' +
            '</div>';
        
        displayDemoResult('AI-Analyse: ' + symbol, content);
        showNotification('AI-analyse fullført!', 'success');
    }, 1500);
};

window.demoGrahamAnalysis = function() {
    showNotification('Utfører Benjamin Graham analyse...', 'info');
    
    setTimeout(function() {
        var content = '<div class="row">' +
            '<div class="col-md-8">' +
            '<h6><i class="bi bi-calculator"></i> Graham Nøkkeltall</h6>' +
            '<table class="table table-sm">' +
            '<tr><td>P/E Ratio</td><td><span class="text-success">12.5</span> (Under 15 ✓)</td></tr>' +
            '<tr><td>P/B Ratio</td><td><span class="text-success">1.8</span> (Under 2.5 ✓)</td></tr>' +
            '<tr><td>Debt/Equity</td><td><span class="text-warning">0.6</span> (Moderat)</td></tr>' +
            '<tr><td>Graham Number</td><td><span class="text-success">285 NOK</span></td></tr>' +
            '</table>' +
            '</div>' +
            '<div class="col-md-4">' +
            '<div class="text-center">' +
            '<div class="display-6 text-success">8.5/10</div>' +
            '<small class="text-muted">Graham Score</small>' +
            '<div class="mt-2">' +
            '<span class="badge bg-success">Value Opportunity</span>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';
        
        displayDemoResult('Benjamin Graham Analyse', content);
        showNotification('Value investing analyse fullført!', 'success');
    }, 1200);
};

window.demoWarrenBuffett = function() {
    showNotification('Analyserer med Buffett-kriterier...', 'info');
    
    setTimeout(function() {
        var content = '<div class="row">' +
            '<div class="col-md-6">' +
            '<h6><i class="bi bi-trophy"></i> Buffett Kriterier</h6>' +
            '<ul class="list-unstyled">' +
            '<li>✅ <strong>ROE:</strong> 18.5% (Høy)</li>' +
            '<li>✅ <strong>Debt/Equity:</strong> 0.4 (Lav)</li>' +
            '<li>✅ <strong>Profit Margin:</strong> 22% (Sterk)</li>' +
            '<li>✅ <strong>10-år vekst:</strong> 12% (Konsistent)</li>' +
            '<li>⚠️ <strong>P/E:</strong> 16.2 (Akseptabel)</li>' +
            '</ul>' +
            '</div>' +
            '<div class="col-md-6">' +
            '<div class="card bg-light">' +
            '<div class="card-body text-center">' +
            '<h5 class="text-success">Kvalitetsselskap</h5>' +
            '<p class="mb-1">Buffett Score: <strong>85/100</strong></p>' +
            '<span class="badge bg-success">Anbefalt for langsiktige investorer</span>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';
        
        displayDemoResult('Warren Buffett Analyse', content, 'warning');
        showNotification('Kvalitetsanalyse fullført!', 'success');
    }, 1800);
};

window.demoShortAnalysis = function() {
    showNotification('Leter etter short-muligheter...', 'info');
    
    setTimeout(function() {
        var content = '<div class="row">' +
            '<div class="col-md-6">' +
            '<h6><i class="bi bi-graph-down"></i> Short Signaler</h6>' +
            '<div class="alert alert-danger">' +
            '<strong>POTENSIELT SHORT</strong>' +
            '</div>' +
            '<ul class="list-unstyled">' +
            '<li>🔻 Teknisk breakdown</li>' +
            '<li>🔻 Svak fundamental utvikling</li>' +
            '<li>🔻 Insider salg øker</li>' +
            '<li>🔻 Analytiker nedjusteringer</li>' +
            '</ul>' +
            '</div>' +
            '<div class="col-md-6">' +
            '<h6><i class="bi bi-exclamation-triangle"></i> Risiko Analyse</h6>' +
            '<p><strong>Short Interest:</strong> 12.5%</p>' +
            '<p><strong>Borrow Rate:</strong> 3.2%</p>' +
            '<p><strong>Risiko:</strong> Høy volatilitet</p>' +
            '<div class="alert alert-warning">' +
            '<small>⚠️ Short selling er høyrisiko strategi</small>' +
            '</div>' +
            '</div>' +
            '</div>';
        
        displayDemoResult('Short Analyse', content, 'danger');
        showNotification('Short analyse fullført!', 'warning');
    }, 1400);
};

window.demoScreener = function() {
    showNotification('Kjører avansert screener...', 'info');
    
    setTimeout(function() {
        var content = '<h6><i class="bi bi-funnel"></i> Screener Resultater</h6>' +
            '<div class="table-responsive">' +
            '<table class="table table-hover">' +
            '<thead>' +
            '<tr>' +
            '<th>Symbol</th>' +
            '<th>P/E</th>' +
            '<th>ROE</th>' +
            '<th>Debt/Eq</th>' +
            '<th>Score</th>' +
            '</tr>' +
            '</thead>' +
            '<tbody>' +
            '<tr class="table-dark" style="background-color: #198754 !important; color: white;">' +
            '<td><strong>STL.OL</strong></td>' +
            '<td>8.2</td>' +
            '<td>24%</td>' +
            '<td>0.3</td>' +
            '<td><span class="badge bg-success">9.1</span></td>' +
            '</tr>' +
            '<tr class="table-dark" style="background-color: #198754 !important; color: white;">' +
            '<td><strong>MOWI.OL</strong></td>' +
            '<td>11.5</td>' +
            '<td>18%</td>' +
            '<td>0.4</td>' +
            '<td><span class="badge bg-success">8.7</span></td>' +
            '</tr>' +
            '<tr class="table-warning">' +
            '<td><strong>NOR.OL</strong></td>' +
            '<td>14.2</td>' +
            '<td>15%</td>' +
            '<td>0.6</td>' +
            '<td><span class="badge bg-warning">7.3</span></td>' +
            '</tr>' +
            '</tbody>' +
            '</table>' +
            '</div>' +
            '<p class="text-muted">Filtrert ut 847 aksjer basert på dine kriterier</p>';
        
        displayDemoResult('Avansert Screener', content, 'primary');
        showNotification('Screeneren fant 3 topp-kandidater!', 'success');
    }, 2000);
};

window.demoInsiderTrading = function() {
    showNotification('Analyserer insider trading...', 'info');
    
    setTimeout(function() {
        var content = '<h6><i class="bi bi-person-badge"></i> Nyeste Insider Transaksjoner</h6>' +
            '<div class="list-group">' +
            '<div class="list-group-item">' +
            '<div class="d-flex justify-content-between">' +
            '<strong>EQNR.OL - CEO</strong>' +
            '<span class="text-success">+50,000 aksjer</span>' +
            '</div>' +
            '<small class="text-muted">Kjøp • 2 dager siden • 285 NOK</small>' +
            '</div>' +
            '<div class="list-group-item">' +
            '<div class="d-flex justify-content-between">' +
            '<strong>DNB.OL - CFO</strong>' +
            '<span class="text-danger">-25,000 aksjer</span>' +
            '</div>' +
            '<small class="text-muted">Salg • 5 dager siden • 234 NOK</small>' +
            '</div>' +
            '<div class="list-group-item">' +
            '<div class="d-flex justify-content-between">' +
            '<strong>TEL.OL - COO</strong>' +
            '<span class="text-success">+15,000 aksjer</span>' +
            '</div>' +
            '<small class="text-muted">Kjøp • 1 uke siden • 138 NOK</small>' +
            '</div>' +
            '</div>';
        
        displayDemoResult('Insider Trading Analyse', content, 'warning');
        showNotification('Insider trading analyse fullført!', 'success');
    }, 1600);
};

// Additional demo functions
window.demoPortfolioOptimization = function() {
    showNotification('Optimaliserer portefølje...', 'info');
    setTimeout(function() {
        showNotification('Portefølje optimalisering fullført!', 'success');
    }, 2000);
};

window.demoRealTimeAlerts = function() {
    showNotification('Aktiverer sanntids varsler...', 'info');
    setTimeout(function() {
        showNotification('Sanntids varsler aktivert!', 'success');
    }, 1500);
};

window.demoMarketAnalysis = function() {
    showNotification('Analyserer markeder...', 'info');
    setTimeout(function() {
        showNotification('Markedsanalyse fullført!', 'success');
    }, 1800);
};

// Additional demo functions that are called from the HTML template
window.resetDemo = function() {
    var resultContainer = document.getElementById('demo-result-container');
    if (resultContainer) {
        resultContainer.innerHTML = '<p class="text-muted">Velg en funksjon ovenfor for å teste den.</p>';
    }
    demoProgress = 0;
    updateDemoProgress();
    showNotification('Demo tilbakestilt!', 'info');
};

window.demoAnalyze = function(symbol) {
    showNotification('Analyserer ' + symbol + '...', 'info');
    setTimeout(function() {
        showNotification(symbol + ' analyse fullført! Anbefaling: KJØP', 'success');
    }, 1500);
};

window.demoAddToWatchlist = function(symbol) {
    showNotification(symbol + ' lagt til i watchlist!', 'success');
};

window.demoBuyStock = function(symbol) {
    showNotification('Demo kjøp av ' + symbol + ' registrert!', 'info');
};

window.showUpgradeModal = function() {
    // Try to show upgrade modal if it exists, otherwise redirect
    var upgradeModal = document.getElementById('upgradeModal');
    if (upgradeModal && typeof bootstrap !== 'undefined') {
        new bootstrap.Modal(upgradeModal).show();
    } else {
        showNotification('Oppgrader til premium for full tilgang!', 'warning');
        setTimeout(function() {
            window.location.href = '/pricing';
        }, 2000);
    }
};

// Initialize demo when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Ensure functions are available
    console.log('Demo.js loaded successfully');
});

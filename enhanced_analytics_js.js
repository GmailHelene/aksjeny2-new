
// Enhanced JavaScript for Advanced Analytics
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Advanced Analytics JavaScript initialized');
    
    // Comprehensive button check and binding
    const buttonConfigs = [
        { id: 'market-analysis-btn', endpoint: '/advanced-analytics/market-analysis', name: 'Market Analysis' },
        { id: 'batch-predict-btn', endpoint: '/advanced-analytics/batch-predictions', name: 'Batch Predictions' },
        { id: 'efficient-frontier-btn', endpoint: '/advanced-analytics/portfolio-optimization', name: 'Portfolio Optimization' },
        { id: 'var-analysis-btn', endpoint: '/advanced-analytics/risk-analysis', name: 'Risk Analysis' },
        { id: 'stress-test-btn', endpoint: '/advanced-analytics/stress-test', name: 'Stress Test' },
        { id: 'monte-carlo-btn', endpoint: '/advanced-analytics/monte-carlo', name: 'Monte Carlo' }
    ];
    
    // Get CSRF token with validation
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (!csrfMeta) {
        console.error('❌ CSRF token meta tag missing');
        document.getElementById('ml-prediction-results').innerHTML = 
            '<div class="alert alert-danger">❌ Security token missing. Please refresh the page.</div>';
        return;
    }
    
    const csrfToken = csrfMeta.getAttribute('content');
    console.log('✅ CSRF token found and validated');
    
    // Bind events to all buttons
    buttonConfigs.forEach(config => {
        const button = document.getElementById(config.id);
        if (button) {
            console.log(`✅ Binding ${config.name} button`);
            button.addEventListener('click', function() {
                handleButtonClick(config, csrfToken);
            });
            
            // Add visual feedback
            button.addEventListener('mousedown', function() {
                this.style.transform = 'scale(0.95)';
            });
            button.addEventListener('mouseup', function() {
                this.style.transform = 'scale(1)';
            });
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        } else {
            console.warn(`⚠️  Button ${config.id} not found`);
        }
    });
    
    function handleButtonClick(config, csrfToken) {
        console.log(`🔧 ${config.name} button clicked`);
        const results = document.getElementById('ml-prediction-results');
        
        if (!results) {
            console.error('Results container not found');
            return;
        }
        
        results.innerHTML = `<div class="alert alert-info">
            <i class="fas fa-spinner fa-spin"></i> ${config.name} kører...
        </div>`;
        
        fetch(config.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
        .then(response => {
            console.log(`📡 ${config.name} response status:`, response.status);
            return response.json();
        })
        .then(data => {
            console.log(`📊 ${config.name} data received:`, data);
            if (data.success) {
                results.innerHTML = `<div class="alert alert-success">
                    <strong>✅ ${config.name} Successful:</strong><br>
                    ${data.analysis || data.message || 'Operation completed successfully.'}
                </div>`;
            } else {
                results.innerHTML = `<div class="alert alert-warning">
                    <strong>⚠️ ${config.name} Issue:</strong><br>
                    ${data.error || 'Unknown error occurred.'}
                </div>`;
            }
        })
        .catch(error => {
            console.error(`❌ ${config.name} error:`, error);
            results.innerHTML = `<div class="alert alert-danger">
                <strong>❌ ${config.name} Error:</strong><br>
                Network error: ${error.message}
            </div>`;
        });
    }
});

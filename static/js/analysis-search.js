document.addEventListener('DOMContentLoaded', function() {
    const searchForms = document.querySelectorAll('.ticker-search-form');
    
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const tickerInput = form.querySelector('input[name="ticker"], input[name="symbol"]');
            if (tickerInput && tickerInput.value.trim()) {
                const currentPath = window.location.pathname;
                const ticker = tickerInput.value.trim().toUpperCase();
                
                // Redirect based on current page
                if (currentPath.includes('sentiment')) {
                    window.location.href = `/analysis/sentiment?symbol=${ticker}`;
                } else if (currentPath.includes('warren-buffett')) {
                    window.location.href = `/analysis/warren-buffett?ticker=${ticker}`;
                } else if (currentPath.includes('ai-predictions')) {
                    window.location.href = `/analysis/ai-predictions?ticker=${ticker}`;
                } else if (currentPath.includes('technical')) {
                    window.location.href = `/analysis/technical?symbol=${ticker}`;
                }
            }
        });
    });
});

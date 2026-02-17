/**
 * Portfolio functionality for Aksjeradar
 */

// Portfolio management functions
function addStock(ticker, shares, price) {
    // Add stock to portfolio
    console.log(`Adding ${shares} shares of ${ticker} at ${price}`);
    
    const data = {
        ticker: ticker,
        shares: shares,
        purchase_price: price
    };
    
    fetch('/api/portfolio/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Aksje lagt til i portefølje!', 'success');
            updatePortfolio();
        } else {
            showNotification('Feil ved tillegning av aksje: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error adding stock:', error);
        showNotification('Nettverksfeil ved tillegning av aksje', 'error');
    });
}

function removeStock(ticker) {
    // Remove stock from portfolio
    console.log(`Removing ${ticker} from portfolio`);
    
    if (!confirm(`Er du sikker på at du vil fjerne ${ticker} fra porteføljen?`)) {
        return;
    }
    
    fetch(`/api/portfolio/remove/${ticker}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Aksje fjernet fra portefølje!', 'success');
            updatePortfolio();
            // Remove the row from the table
            const row = document.querySelector(`tr[data-ticker="${ticker}"]`);
            if (row) {
                row.remove();
            }
        } else {
            showNotification('Feil ved fjerning av aksje: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error removing stock:', error);
        showNotification('Nettverksfeil ved fjerning av aksje', 'error');
    });
}

function updatePortfolio() {
    // Update portfolio display
    console.log('Updating portfolio...');
    // Implementation would go here
}

// Initialize portfolio functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Portfolio functionality loaded');
    
    // Add event listeners for portfolio actions
    const addButtons = document.querySelectorAll('.add-stock-btn');
    addButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const ticker = this.dataset.ticker;
            // Handle add stock
        });
    });
    
    const removeButtons = document.querySelectorAll('.remove-stock-btn');
    removeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const ticker = this.dataset.ticker;
            removeStock(ticker);
        });
    });
});

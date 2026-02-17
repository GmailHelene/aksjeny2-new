document.addEventListener('DOMContentLoaded', function() {
    // Fix stock detail buttons
    document.querySelectorAll('.stock-detail-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const symbol = this.dataset.symbol;
            window.location.href = `/stocks/details/${symbol}`;
        });
    });
    
    // Fix buy buttons
    document.querySelectorAll('.stock-buy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const symbol = this.dataset.symbol;
            window.location.href = `/portfolio/add?symbol=${symbol}`;
        });
    });
    
    // Currency calculator
    const currencyForm = document.getElementById('currencyCalculator');
    if (currencyForm) {
        currencyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const amount = parseFloat(document.getElementById('amount').value);
            const fromCurrency = document.getElementById('fromCurrency').value;
            const toCurrency = document.getElementById('toCurrency').value;
            const rate = parseFloat(document.getElementById('exchangeRate').value);
            
            if (amount && rate) {
                const result = amount * rate;
                document.getElementById('conversionResult').innerHTML = 
                    `<div class="alert alert-success">
                        ${amount} ${fromCurrency} = ${result.toFixed(2)} ${toCurrency}
                    </div>`;
            }
        });
    }
});

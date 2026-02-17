// Warren Buffett Analysis Search Functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log("Warren Buffett search script loaded");
    
    // Get the search input element
    const tickerSearch = document.getElementById('ticker');
    
    if (!tickerSearch) {
        console.log("Ticker search input not found");
        return;
    }
    
    console.log("Ticker search input found:", tickerSearch);
    
    // Enable stock search autocomplete
    setupTickerAutocomplete(tickerSearch);
    
    // Handle form submission
    const analysisForm = tickerSearch.closest('form');
    if (analysisForm) {
        console.log("Analysis form found:", analysisForm);
        
        analysisForm.addEventListener('submit', function(event) {
            const ticker = tickerSearch.value.trim();
            console.log("Form submitted with ticker:", ticker);
            
            if (!ticker) {
                event.preventDefault();
                showErrorToast('Vennligst skriv inn et aksjesymbol');
                console.log("Form submission prevented - empty ticker");
                return false;
            }
            
            // Let the form submit normally with the ticker value
            return true;
        });
    } else {
        console.log("Analysis form not found");
    }
    
    // Direct button for analysis (fallback)
    const analyzeButton = document.querySelector('button[type="submit"]');
    if (analyzeButton) {
        console.log("Analyze button found");
        analyzeButton.addEventListener('click', function() {
            const ticker = tickerSearch.value.trim();
            if (ticker) {
                console.log("Analyze button clicked with ticker:", ticker);
                window.location.href = `/analysis/warren_buffett?ticker=${encodeURIComponent(ticker)}`;
            } else {
                showErrorToast('Vennligst skriv inn et aksjesymbol');
            }
        });
    }
});

// Setup ticker autocomplete
function setupTickerAutocomplete(inputElement) {
    // Get stock lists from data attributes
    try {
        console.log("Setting up ticker autocomplete");
        
        const osloStocksElement = document.getElementById('oslo-stocks-data');
        const globalStocksElement = document.getElementById('global-stocks-data');
        
        if (!osloStocksElement || !globalStocksElement) {
            console.log("Stock data elements not found");
            return;
        }
        
        const osloStocksData = osloStocksElement.dataset.stocks;
        const globalStocksData = globalStocksElement.dataset.stocks;
        
        if (!osloStocksData || !globalStocksData) {
            console.log("Stock data attributes not found");
            return;
        }
        
        console.log("Oslo stocks data:", osloStocksData);
        console.log("Global stocks data:", globalStocksData);
        
        const osloStocks = JSON.parse(osloStocksData);
        const globalStocks = JSON.parse(globalStocksData);
        
        // Create a combined list of stocks for autocomplete
        const allStocks = { ...osloStocks, ...globalStocks };
        console.log("Combined stocks for autocomplete:", Object.keys(allStocks).length);
        
        // Stock suggestions
        let suggestions = [];
        for (const [symbol, data] of Object.entries(allStocks)) {
            suggestions.push({
                symbol: symbol,
                name: data.name,
                sector: data.sector || 'Ukjent',
                display: `${symbol} - ${data.name} (${data.sector || 'Ukjent'})`
            });
        }
        
        // Add event listener for input
        inputElement.addEventListener('input', function() {
            const query = this.value.trim().toUpperCase();
            console.log("Input event - query:", query);
            
            // Hide any existing dropdown
            const existingDropdown = document.querySelector('.ticker-autocomplete-dropdown');
            if (existingDropdown) {
                existingDropdown.remove();
            }
            
            // If input is empty, don't show dropdown
            if (!query) return;
            
            // Filter suggestions based on input
            const filteredSuggestions = suggestions.filter(item => {
                return item.symbol.includes(query) || 
                       item.name.toUpperCase().includes(query) ||
                       item.sector.toUpperCase().includes(query);
            }).slice(0, 7); // Limit to 7 suggestions
            
            console.log("Filtered suggestions:", filteredSuggestions.length);
            
            // Create dropdown if we have suggestions
            if (filteredSuggestions.length > 0) {
                createSuggestionsDropdown(inputElement, filteredSuggestions);
            }
        });
        
        // Handle click outside to close dropdown
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.ticker-autocomplete-container')) {
                const dropdown = document.querySelector('.ticker-autocomplete-dropdown');
                if (dropdown) dropdown.remove();
            }
        });
    } catch (error) {
        console.error("Error in setupTickerAutocomplete:", error);
    }
}

// Create suggestions dropdown
function createSuggestionsDropdown(inputElement, suggestions) {
    try {
        console.log("Creating suggestions dropdown");
        
        // Create container around input for positioning
        let container = inputElement.closest('.ticker-autocomplete-container');
        if (!container) {
            console.log("Creating new container for autocomplete");
            container = document.createElement('div');
            container.className = 'ticker-autocomplete-container position-relative';
            inputElement.parentNode.insertBefore(container, inputElement);
            container.appendChild(inputElement);
        }
        
        // Create dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'ticker-autocomplete-dropdown position-absolute start-0 end-0 mt-1 bg-white shadow rounded-3';
        dropdown.style.zIndex = 1000;
        dropdown.style.maxHeight = '300px';
        dropdown.style.overflowY = 'auto';
        dropdown.style.border = '1px solid #dee2e6';
        
        // Add suggestions
        suggestions.forEach((item, index) => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'p-2 border-bottom ticker-suggestion';
            suggestionItem.style.cursor = 'pointer';
            
            // Highlight first item
            if (index === 0) {
                suggestionItem.classList.add('bg-light');
            }
            
            // Hover effect
            suggestionItem.addEventListener('mouseover', () => {
                // Remove highlight from all items
                dropdown.querySelectorAll('.ticker-suggestion').forEach(el => {
                    el.classList.remove('bg-light');
                });
                // Add highlight to this item
                suggestionItem.classList.add('bg-light');
            });
            
            // Create inner HTML
            suggestionItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${item.symbol}</strong>
                        <span class="text-muted ms-2">${item.name}</span>
                    </div>
                    <span class="badge bg-secondary">${item.sector}</span>
                </div>
            `;
            
            // Handle click
            suggestionItem.addEventListener('click', () => {
                console.log("Suggestion clicked:", item.symbol);
                inputElement.value = item.symbol;
                dropdown.remove();
                
                // Trigger form submission
                const form = inputElement.closest('form');
                if (form) {
                    console.log("Submitting form with selected ticker");
                    form.submit();
                } else {
                    // Fallback - redirect directly
                    console.log("Form not found, redirecting directly");
                    window.location.href = `/analysis/warren_buffett?ticker=${encodeURIComponent(item.symbol)}`;
                }
            });
            
            dropdown.appendChild(suggestionItem);
        });
        
        // Add to DOM
        container.appendChild(dropdown);
        
        // Add keyboard navigation
        inputElement.addEventListener('keydown', function(e) {
            const items = dropdown.querySelectorAll('.ticker-suggestion');
            const activeItem = dropdown.querySelector('.ticker-suggestion.bg-light');
            let activeIndex = Array.from(items).indexOf(activeItem);
            
            // Down arrow
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (activeIndex < items.length - 1) {
                    if (activeItem) activeItem.classList.remove('bg-light');
                    items[activeIndex + 1].classList.add('bg-light');
                    items[activeIndex + 1].scrollIntoView({ block: 'nearest' });
                }
            }
            // Up arrow
            else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (activeIndex > 0) {
                    if (activeItem) activeItem.classList.remove('bg-light');
                    items[activeIndex - 1].classList.add('bg-light');
                    items[activeIndex - 1].scrollIntoView({ block: 'nearest' });
                }
            }
            // Enter key
            else if (e.key === 'Enter' && activeItem) {
                e.preventDefault();
                activeItem.click();
            }
        });
    } catch (error) {
        console.error("Error in createSuggestionsDropdown:", error);
    }
}

// Show error toast
function showErrorToast(message) {
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toastElement = document.createElement('div');
        toastElement.className = 'toast align-items-center text-white bg-danger border-0';
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');
        
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastElement);
        
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove toast after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    } else {
        // Fallback if Bootstrap is not available
        alert(message);
    }
}

// Basic functionality for Aksjeradar app
document.addEventListener('DOMContentLoaded', function() {
    console.log('Aksjeradar app initialized');
    
    // Initialize Bootstrap components
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (typeof bootstrap !== 'undefined') {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Check if bootstrap is loaded
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        });
    }
    
    // Format number inputs
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.value < 0) {
                this.value = 0;
            }
        });
    });
});

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Utility function to format percentage
function formatPercentage(percentage) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(percentage / 100);
}

// Eksempel på kode som viser en oppdateringsmelding
let newVersionAvailable = false;

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (newVersionAvailable) {
      document.getElementById('update-notification').style.display = 'block';
    }
  });
  
  navigator.serviceWorker.ready.then(reg => {
    reg.addEventListener('updatefound', () => {
      newVersionAvailable = true;
    });
  });
}

// Remove or comment out any connection monitoring code
// Example of what to remove:
/*
// Connection monitoring - REMOVED
function checkConnection() {
    // This function is removed to prevent "Tilkobling tapt" messages
}

// WebSocket status - REMOVED
function updateConnectionStatus(status) {
    // This function is removed
}
*/

// Initialize app without connection monitoring
document.addEventListener('DOMContentLoaded', function() {
    console.log('Aksjeradar initialized');
    
    // Remove any existing connection status elements
    const connectionElements = document.querySelectorAll('.connection-status, .connection-lost, [data-ws-status]');
    connectionElements.forEach(el => el.remove());
});
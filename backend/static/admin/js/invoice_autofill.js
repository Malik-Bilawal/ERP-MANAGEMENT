// Auto-fill invoice amount when client is selected
function fetchClientPendingBalance(clientId) {
    if (!clientId) return;
    
    fetch(`/api/client-management/clients/${clientId}/`)
        .then(response => response.json())
        .then(data => {
            const amountField = document.querySelector('#id_amount');
            if (amountField && data.pending_payments) {
                const pendingAmount = parseFloat(data.pending_payments);
                if (pendingAmount > 0) {
                    amountField.value = pendingAmount;
                    showNotification(`Client pending balance: $${pendingAmount.toLocaleString()} loaded`, 'success');
                } else {
                    showNotification('Client has no pending balance', 'warning');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching client:', error);
            showNotification('Could not fetch client balance. Enter amount manually.', 'error');
        });
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 9999;
        padding: 15px; border-radius: 5px;
        background: ${type === 'success' ? '#d4edda' : type === 'warning' ? '#fff3cd' : '#f8d7da'};
        color: ${type === 'success' ? '#155724' : type === 'warning' ? '#856404' : '#721c24'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : type === 'warning' ? '#ffeeba' : '#f5c6cb'};
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

document.addEventListener('DOMContentLoaded', function() {
    const clientSelect = document.getElementById('id_client');
    if (clientSelect) {
        // For autocomplete_fields (Select2), listen to the change event
        clientSelect.addEventListener('change', function() {
            fetchClientPendingBalance(this.value);
        });
        
        // Also listen to Select2's custom event
        if (typeof $ !== 'undefined') {
            $(clientSelect).on('select2:select', function(e) {
                fetchClientPendingBalance(e.params.data.id);
            });
        }
    }
});

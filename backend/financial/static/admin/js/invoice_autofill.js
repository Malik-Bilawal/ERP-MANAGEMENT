// Auto-fill project cost when project is selected
function fetchProjectCost(projectId) {
    if (!projectId) return;
    
    // Fetch project details via API
    fetch(`/api/client-management/projects/${projectId}/`)
        .then(response => response.json())
        .then(data => {
            // Auto-fill amount field
            const amountField = document.querySelector('#id_amount');
            if (amountField && data.budget) {
                amountField.value = data.budget;
                amountField.readOnly = true;
                
                // Show notification
                showNotification(`Project cost: $${data.budget} loaded automatically`, 'success');
            }
            
            // Auto-fill client if not already set
            const clientField = document.querySelector('#id_client');
            if (clientField && !clientField.value && data.client) {
                clientField.value = data.client;
            }
        })
        .catch(error => {
            console.error('Error fetching project:', error);
            showNotification('Could not fetch project cost. Please enter manually.', 'error');
        });
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `messagelist ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        padding: 15px;
        border-radius: 5px;
        background: ${type === 'success' ? '#d4edda' : '#f8d7da'};
        color: ${type === 'success' ? '#155724' : '#721c24'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'};
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    `;
    notification.innerHTML = message;
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Add event listener when page loads
document.addEventListener('DOMContentLoaded', function() {
    const projectField = document.querySelector('#id_project');
    if (projectField) {
        projectField.addEventListener('change', function() {
            fetchProjectCost(this.value);
        });
    }
});
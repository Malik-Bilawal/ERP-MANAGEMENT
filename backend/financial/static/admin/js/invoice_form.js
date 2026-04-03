// Invoice form - fetch projects and project details
document.addEventListener('DOMContentLoaded', function() {
    console.log('Invoice form JS loaded');
    
    var clientField = document.querySelector('#id_client');
    var projectField = document.querySelector('#id_project');
    var amountField = document.querySelector('#id_amount');
    
    console.log('Client field found:', clientField ? 'yes' : 'no');
    console.log('Project field found:', projectField ? 'yes' : 'no');
    console.log('Amount field found:', amountField ? 'yes' : 'no');

    if (!clientField || !projectField) {
        console.log('Fields not found on this page');
        return;
    }

    // Create budget display element
    function createBudgetDisplay() {
        var wrapper = document.createElement('div');
        wrapper.id = 'project-budget-display';
        wrapper.style.cssText = 'background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 16px; margin-bottom: 16px;';
        wrapper.innerHTML = '<p style="margin: 0; color: #92400e;">Select a project to see budget information</p>';
        return wrapper;
    }
    
    // Insert budget display after project field
    var budgetDisplay = createBudgetDisplay();
    projectField.parentNode.parentNode.insertBefore(budgetDisplay, projectField.parentNode.nextSibling);

    function loadProjects(clientId) {
        if (!clientId) {
            projectField.innerHTML = '<option value="">---------</option>';
            return;
        }
        console.log('Loading projects for client:', clientId);
        
        fetch('/admin/financial/invoice/project-details/?client_id=' + clientId, {
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Projects loaded:', data);
            projectField.innerHTML = '<option value="">---------</option>';
            if (data.length === 0) {
                projectField.innerHTML = '<option value="">No projects with remaining balance</option>';
                return;
            }
            data.forEach(function(project) {
                var option = document.createElement('option');
                option.value = project.id;
                option.textContent = project.project_id + ' - ' + project.name + ' ($' + parseFloat(project.budget).toLocaleString() + ')';
                projectField.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading projects:', error);
            projectField.innerHTML = '<option value="">Error loading projects</option>';
        });
    }

    function loadProjectDetails(projectId) {
        console.log('Loading details for project:', projectId);
        if (!projectId) {
            budgetDisplay.innerHTML = '<p style="margin: 0; color: #92400e;">Select a project to see budget information</p>';
            return;
        }
        
        fetch('/admin/financial/invoice/project-details/' + projectId + '/', {
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Project details:', data);
            if (data.error) {
                console.error(data.error);
                return;
            }

            var budget = parseFloat(data.budget);
            var invoiced = parseFloat(data.total_invoiced);
            var remaining = parseFloat(data.remaining_budget);

            budgetDisplay.innerHTML = 
                '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">' +
                '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Total Budget</p>' +
                '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #0c4a6e;">$' + budget.toLocaleString(undefined, {minimumFractionDigits: 2}) + '</p></div>' +
                '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Already Invoiced</p>' +
                '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #ea580c;">$' + invoiced.toLocaleString(undefined, {minimumFractionDigits: 2}) + '</p></div>' +
                '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Remaining</p>' +
                '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #16a34a;">$' + remaining.toLocaleString(undefined, {minimumFractionDigits: 2}) + '</p></div>' +
                '</div>';
        })
        .catch(error => {
            console.error('Failed to load project details:', error);
            budgetDisplay.innerHTML = '<p style="margin: 0; color: #dc2626;">Error loading project details</p>';
        });
    }

    clientField.addEventListener('change', function() {
        var clientId = this.value;
        loadProjects(clientId);
        projectField.value = '';
        budgetDisplay.innerHTML = '<p style="margin: 0; color: #92400e;">Select a project to see budget information</p>';
    });

    projectField.addEventListener('change', function() {
        var projectId = this.value;
        loadProjectDetails(projectId);
    });

    // If editing an existing invoice and project is already selected
    var existingProject = projectField.value;
    if (existingProject) {
        console.log('Loading existing project:', existingProject);
        loadProjectDetails(existingProject);
    }
});

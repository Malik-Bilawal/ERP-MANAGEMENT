(function($) {
    $(document).ready(function() {
        console.log('Invoice form JS loaded');
        
        var clientField = $('#id_client');
        var projectField = $('#id_project');
        var amountField = $('#id_amount');
        var budgetDisplay = $('#id_remaining_budget_display');
        
        console.log('Client field found:', clientField.length);
        console.log('Project field found:', projectField.length);

        if (!clientField.length) {
            console.log('Client field not found, trying alternative selectors');
            clientField = $('select[name="client"]');
            projectField = $('select[name="project"]');
            amountField = $('input[name="amount"]');
            console.log('Alternative - Client field found:', clientField.length);
            console.log('Alternative - Project field found:', projectField.length);
        }
        
        if (!clientField.length) {
            console.log('Fields not found, aborting');
            return;
        }

        function loadProjects(clientId) {
            if (!clientId) {
                projectField.html('<option value="">---------</option>');
                return;
            }
            console.log('Loading projects for client:', clientId);
            $.ajax({
                url: '/admin/financial/invoice/project-details/',
                data: { client_id: clientId },
                success: function(data) {
                    console.log('Projects loaded:', data);
                    projectField.html('<option value="">---------</option>');
                    if (data.length === 0) {
                        projectField.html('<option value="">No projects with remaining balance</option>');
                        return;
                    }
                    $.each(data, function(i, project) {
                        projectField.append(
                            $('<option></option>').val(project.id).text(project.project_id + ' - ' + project.name + ' ($' + parseFloat(project.budget).toLocaleString() + ')')
                        );
                    });
                },
                error: function(xhr, status, error) {
                    console.error('Error loading projects:', xhr.responseText);
                    projectField.html('<option value="">Error loading projects</option>');
                }
            });
        }

        function loadProjectDetails(projectId) {
            if (!projectId) {
                amountField.val('');
                if (budgetDisplay.length) {
                    budgetDisplay.html('<div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 12px;"><p style="margin: 0; color: #92400e;">Select a project to see budget information</p></div>');
                }
                return;
            }
            $.ajax({
                url: '/admin/financial/invoice/project-details/' + projectId + '/',
                success: function(data) {
                    if (data.error) {
                        console.error(data.error);
                        return;
                    }

                    var budget = parseFloat(data.budget);
                    var invoiced = parseFloat(data.total_invoiced);
                    var remaining = parseFloat(data.remaining_budget);

                    amountField.val(remaining.toFixed(2));

                    if (budgetDisplay.length) {
                        budgetDisplay.html(
                            '<div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 16px;">' +
                            '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">' +
                            '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Total Budget</p>' +
                            '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #0c4a6e;">$' + budget.toLocaleString(undefined, {minimumFractionDigits: 2}) + '</p></div>' +
                            '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Already Invoiced</p>' +
                            '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #ea580c;">$' + invoiced.toLocaleString(undefined, {minimumFractionDigits: 2}) + '</p></div>' +
                            '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Remaining</p>' +
                            '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #16a34a;">$' + remaining.toLocaleString(undefined, {minimumFractionDigits: 2}) + '</p></div>' +
                            '</div></div>'
                        );
                    }
                },
                error: function() {
                    console.error('Failed to load project details');
                }
            });
        }

        clientField.on('change', function() {
            var clientId = $(this).val();
            loadProjects(clientId);
            amountField.val('');
            projectField.val('');
        });

        projectField.on('change', function() {
            var projectId = $(this).val();
            loadProjectDetails(projectId);
        });

        var existingProject = projectField.val();
        if (existingProject) {
            loadProjectDetails(existingProject);
        }
    });
})(django.jQuery);

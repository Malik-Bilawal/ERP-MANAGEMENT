// Payment Auto-fill JavaScript
// When an invoice is selected, auto-fill the amount to remaining balance

(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Get the invoice select element
        var invoiceSelect = $('#id_invoice');
        var amountInput = $('#id_amount');
        
        if (invoiceSelect.length && amountInput.length) {
            // Function to fetch invoice details and auto-fill
            function fetchInvoiceDetails(invoiceId) {
                if (!invoiceId) {
                    return;
                }
                
                $.ajax({
                    url: '/api/financial/invoices/' + invoiceId + '/',
                    type: 'GET',
                    dataType: 'json',
                    success: function(data) {
                        if (data.remaining_amount !== undefined) {
                            // Auto-fill the amount field with remaining balance
                            amountInput.val(data.remaining_amount);
                        }
                    },
                    error: function() {
                        console.log('Could not fetch invoice details');
                    }
                });
            }
            
            // For Django admin with Select2
            if (invoiceSelect.hasClass('select2-hidden-accessible')) {
                invoiceSelect.on('change', function() {
                    var invoiceId = $(this).val();
                    fetchInvoiceDetails(invoiceId);
                });
            } else {
                // Regular select
                invoiceSelect.on('change', function() {
                    var invoiceId = $(this).val();
                    fetchInvoiceDetails(invoiceId);
                });
            }
        }
    });
})(django.jQuery);
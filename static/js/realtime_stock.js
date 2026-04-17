// Jessey Clinic - Real-time Stock Updates
// Polls server for low stock and expiry alerts

$(document).ready(function() {
    // Update stock alerts every 60 seconds
    let alertInterval = setInterval(updateAlerts, 60000);

    function updateAlerts() {
        $.ajax({
            url: '/stock/alerts-data',
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                updateLowStockBadge(data.low_stock_count);
                updateExpiryBadge(data.expiring_count);
                if (data.low_stock_count > 0 && $('#lowStockAlert').length) {
                    $('#lowStockAlert').html(`<i class="fas fa-exclamation-triangle"></i> ${data.low_stock_count} low stock items`).show();
                } else if ($('#lowStockAlert').length) {
                    $('#lowStockAlert').hide();
                }
            },
            error: function() {
                console.log('Failed to fetch stock alerts');
            }
        });
    }

    function updateLowStockBadge(count) {
        const badge = $('#lowStockBadge');
        if (badge.length) {
            if (count > 0) {
                badge.text(count).removeClass('d-none');
            } else {
                badge.addClass('d-none');
            }
        }
    }

    function updateExpiryBadge(count) {
        const badge = $('#expiryBadge');
        if (badge.length) {
            if (count > 0) {
                badge.text(count).removeClass('d-none');
            } else {
                badge.addClass('d-none');
            }
        }
    }

    // For stock list page: live stock quantity updates (optional)
    $('.stock-quantity').each(function() {
        const drugId = $(this).data('id');
        // Could implement WebSocket or long polling for real-time
    });

    // Auto-refresh expiring soon page every 2 minutes
    if ($('#expiringTable').length) {
        setInterval(function() {
            location.reload();
        }, 120000);
    }
});
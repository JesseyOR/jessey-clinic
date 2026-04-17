// Jessey Clinic - Quick Checkout JavaScript
// Handles product search, cart management, and sale completion

$(document).ready(function() {
    let searchTimeout;
    let currentCart = {};

    // Load cart from session via AJAX or from page data
    function loadCart() {
        $.get('/sales/cart-data', function(data) {
            currentCart = data.cart || {};
            updateCartDisplay();
        });
    }

    // Search products with debounce
    $('#searchInput').on('input', function() {
        clearTimeout(searchTimeout);
        const query = $(this).val();
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => searchProducts(query), 500);
        } else if (query.length === 0) {
            $('#productList').html('<div class="text-center p-5">Type to search products</div>');
        }
    });

    function searchProducts(query) {
        $.ajax({
            url: '/api/mobile/search/drugs',
            method: 'GET',
            data: { q: query },
            success: function(response) {
                displayProducts(response.results);
            },
            error: function() {
                $('#productList').html('<div class="alert alert-danger">Search failed</div>');
            }
        });
    }

    function displayProducts(products) {
        if (!products.length) {
            $('#productList').html('<p class="text-muted text-center">No products found</p>');
            return;
        }
        let html = '';
        products.forEach(p => {
            html += `
                <div class="col-md-6 col-lg-4">
                    <div class="card product-card mb-3" data-id="${p.id}">
                        <div class="card-body">
                            <h6 class="card-title">${escapeHtml(p.name)}</h6>
                            <p class="card-text text-primary">$${parseFloat(p.selling_price).toFixed(2)}</p>
                            <small class="text-muted">Stock: ${p.quantity}</small>
                            ${p.requires_prescription ? '<span class="badge bg-warning ms-2">Rx</span>' : ''}
                            <button class="btn btn-sm btn-primary add-to-cart mt-2 w-100" data-id="${p.id}">
                                <i class="fas fa-cart-plus"></i> Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        $('#productList').html(html);
    }

    // Add to cart
    $(document).on('click', '.add-to-cart', function(e) {
        e.stopPropagation();
        const drugId = $(this).data('id');
        const quantity = 1; // Default, could add quantity selector
        $.ajax({
            url: '/sales/add-to-cart',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ drug_id: drugId, quantity: quantity }),
            success: function(response) {
                if (response.success) {
                    location.reload(); // Reload to refresh cart
                }
            },
            error: function(xhr) {
                alert('Error: ' + (xhr.responseJSON?.error || 'Could not add to cart'));
            }
        });
    });

    // Remove from cart
    $(document).on('click', '.remove-item', function() {
        const drugId = $(this).data('id');
        $.ajax({
            url: '/sales/remove-from-cart',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ drug_id: drugId }),
            success: function() {
                location.reload();
            }
        });
    });

    // Complete sale
    $('#completeSaleBtn').click(function() {
        if ($(this).prop('disabled')) return;
        const paymentMethod = $('#paymentMethod').val();
        const patientId = $('#patientId').val();
        $.ajax({
            url: '/sales/complete-sale',
            method: 'POST',
            data: { payment_method: paymentMethod, patient_id: patientId },
            success: function(response) {
                if (response.invoice) {
                    window.location.href = '/sales/receipt/' + response.invoice;
                } else {
                    window.location.href = '/sales/history';
                }
            },
            error: function(xhr) {
                alert('Sale failed: ' + (xhr.responseText || 'Unknown error'));
            }
        });
    });

    // Helper: escape HTML
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    // Auto-refresh low stock warning
    if ($('#lowStockBadge').length) {
        setInterval(function() {
            $.get('/stock/low-stock-count', function(data) {
                if (data.count > 0) {
                    $('#lowStockBadge').text(data.count).show();
                } else {
                    $('#lowStockBadge').hide();
                }
            });
        }, 30000);
    }
});
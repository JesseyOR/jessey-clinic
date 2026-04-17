// Jessey Clinic - Barcode Scanner Integration
// Supports USB barcode scanners (simulates keyboard input)

$(document).ready(function() {
    let barcodeBuffer = '';
    let barcodeTimer = null;
    const SCAN_DELAY = 50; // milliseconds between characters
    const SCAN_TIMEOUT = 100; // timeout to reset buffer

    // Attach event listener to the whole document (or specific input)
    $(document).on('keypress', function(e) {
        // Only capture if focus is not on a text input (to avoid double input)
        const activeTag = document.activeElement.tagName;
        if (activeTag === 'INPUT' || activeTag === 'TEXTAREA' || activeTag === 'SELECT') {
            return;
        }

        // Get character
        const char = String.fromCharCode(e.which);
        barcodeBuffer += char;

        // Clear previous timer
        if (barcodeTimer) clearTimeout(barcodeTimer);

        // Set timer to process barcode after short delay
        barcodeTimer = setTimeout(function() {
            if (barcodeBuffer.length >= 6) { // Minimum barcode length
                processBarcode(barcodeBuffer);
            }
            barcodeBuffer = '';
        }, SCAN_TIMEOUT);
    });

    function processBarcode(barcode) {
        console.log('Scanned barcode:', barcode);
        // Send to server to find drug
        $.ajax({
            url: '/api/mobile/lookup-barcode',
            method: 'GET',
            data: { barcode: barcode },
            success: function(response) {
                if (response.drug) {
                    // Add to cart automatically
                    addToCart(response.drug.id, 1);
                    showToast('Added: ' + response.drug.name, 'success');
                } else {
                    showToast('Product not found for barcode: ' + barcode, 'warning');
                }
            },
            error: function() {
                showToast('Barcode lookup failed', 'danger');
            }
        });
    }

    function addToCart(drugId, quantity) {
        $.ajax({
            url: '/sales/add-to-cart',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ drug_id: drugId, quantity: quantity }),
            success: function() {
                location.reload();
            },
            error: function(xhr) {
                showToast('Error: ' + (xhr.responseJSON?.error || 'Could not add'), 'danger');
            }
        });
    }

    function showToast(message, type) {
        // Simple toast notification
        const toastHtml = `
            <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 1100">
                <div class="toast align-items-center text-bg-${type} border-0" role="alert" data-bs-autohide="true" data-bs-delay="3000">
                    <div class="d-flex">
                        <div class="toast-body">${message}</div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            </div>
        `;
        $('body').append(toastHtml);
        const toast = new bootstrap.Toast($('.toast').last());
        toast.show();
        setTimeout(() => $('.toast').last().remove(), 3500);
    }

    // Optional: manual barcode input field
    $('#manualBarcode').on('keypress', function(e) {
        if (e.which === 13) { // Enter pressed
            const barcode = $(this).val().trim();
            if (barcode) {
                processBarcode(barcode);
                $(this).val('');
            }
        }
    });
});
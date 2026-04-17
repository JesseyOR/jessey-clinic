// Jessey Clinic - Mobile Dashboard Scripts
// Lightweight for mobile devices

$(document).ready(function() {
    // Swipe to toggle sidebar on mobile
    let touchStartX = 0;
    let touchEndX = 0;

    $(document).on('touchstart', function(e) {
        touchStartX = e.originalEvent.touches[0].clientX;
    });

    $(document).on('touchend', function(e) {
        touchEndX = e.originalEvent.changedTouches[0].clientX;
        handleSwipe();
    });

    function handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        if (Math.abs(swipeDistance) > 50) {
            if (swipeDistance > 0 && $('#sidebar').hasClass('active') === false) {
                // Swipe right to open sidebar
                $('#sidebar').addClass('active');
            } else if (swipeDistance < 0 && $('#sidebar').hasClass('active')) {
                // Swipe left to close sidebar
                $('#sidebar').removeClass('active');
            }
        }
    }

    // Click outside sidebar to close (mobile)
    $(document).on('click', function(e) {
        if ($('#sidebar').hasClass('active') && !$(e.target).closest('#sidebar').length && !$(e.target).closest('#sidebarCollapse').length) {
            $('#sidebar').removeClass('active');
        }
    });

    // Refresh data on pull-to-refresh (simple)
    let pullStartY = 0;
    $(document).on('touchstart', function(e) {
        if ($(window).scrollTop() === 0) {
            pullStartY = e.originalEvent.touches[0].clientY;
        }
    });
    $(document).on('touchmove', function(e) {
        const pullEndY = e.originalEvent.touches[0].clientY;
        if (pullStartY && pullEndY - pullStartY > 100 && $(window).scrollTop() === 0) {
            location.reload();
        }
    });

    // Mobile dashboard auto-refresh every 30 seconds
    if ($('.mobile-container').length) {
        setInterval(function() {
            // Refresh only if page is visible
            if (!document.hidden) {
                $.ajax({
                    url: window.location.href,
                    method: 'GET',
                    success: function(html) {
                        const newStats = $(html).find('.mobile-stats').html();
                        if (newStats) {
                            $('.mobile-stats').html(newStats);
                        }
                    }
                });
            }
        }, 30000);
    }
});
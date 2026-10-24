// Staff: live count of pending payments in the sidebar
function updatePendingBadge() {
    fetch('/payments/pending-count/')
        .then(response => response.json())
        .then(data => {
            document.querySelectorAll('.pending-badge').forEach(badge => {
                badge.textContent = data.count > 0 ? data.count : '';
                badge.classList.toggle('d-none', data.count === 0);
            });
        })
        .catch(error => console.log('Badge update failed:', error));
}

if (document.querySelector('.pending-badge')) {
    updatePendingBadge();
    setInterval(updatePendingBadge, 15000);
}

function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[2]) : null;
}

// Wishlist hearts: toggle without reloading the page
document.addEventListener('click', event => {
    const button = event.target.closest('[data-wishlist-url]');
    if (!button) return;
    event.preventDefault();
    if (button.dataset.loginUrl) {
        window.location = button.dataset.loginUrl;
        return;
    }
    fetch(button.dataset.wishlistUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest'},
    })
        .then(response => response.json())
        .then(data => {
            document.querySelectorAll(`[data-wishlist-url="${button.dataset.wishlistUrl}"]`).forEach(btn => {
                btn.classList.toggle('active', data.in_wishlist);
                const icon = btn.querySelector('i');
                if (icon) icon.className = data.in_wishlist ? 'bi bi-heart-fill' : 'bi bi-heart';
                const label = btn.querySelector('.wish-label');
                if (label) label.textContent = data.in_wishlist ? 'In wishlist' : 'Add to wishlist';
            });
            const counter = document.getElementById('wishlist-count');
            if (counter) {
                counter.textContent = data.count;
                counter.classList.toggle('d-none', data.count === 0);
            }
        });
});

// Quantity +/- buttons
document.addEventListener('click', event => {
    const button = event.target.closest('[data-qty-step]');
    if (!button) return;
    const input = button.parentElement.querySelector('input');
    const step = parseInt(button.dataset.qtyStep, 10);
    const max = parseInt(input.max || '9999', 10);
    const value = Math.min(Math.max((parseInt(input.value, 10) || 1) + step, 1), max);
    input.value = value;
    if (button.dataset.autosubmit !== undefined) button.closest('form').submit();
});

// Auto-hide flash messages
setTimeout(() => {
    document.querySelectorAll('.flash-stack .alert').forEach(alert => {
        bootstrap.Alert.getOrCreateInstance(alert).close();
    });
}, 5000);

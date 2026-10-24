function updatePendingBadge() {
    fetch('/payments/pending-count/')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('pending-badge');
            if (badge) {
                badge.textContent = data.count > 0 ? data.count : '';
            }
        })
        .catch(error => console.log('Badge update failed:', error));
}

// Update immediately, then every 10 seconds
if (document.getElementById('pending-badge')) {
    updatePendingBadge();
    setInterval(updatePendingBadge, 10000);
}
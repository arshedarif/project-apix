document.addEventListener('DOMContentLoaded', function () {
    const downloadBtn = document.getElementById('download-btn');
    const selectedCountSpan = document.getElementById('selected-count');
    const selectedCountDisplay = document.getElementById('selectedCount');
    const notification = document.getElementById('notification');

    function updateSelectedCount() {
        const count = document.querySelectorAll('.image-checkbox:checked').length;
        selectedCountSpan.textContent = count;
        selectedCountDisplay.textContent = `${count} selected`;
    }

    document.addEventListener('change', function (e) {
        if (e.target.classList.contains('image-checkbox')) {
            updateSelectedCount();
        }
    });

    function showNotification(message, type) {
        notification.textContent = message;
        notification.className = `notification show ${type}`;
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    downloadBtn.addEventListener('click', async function () {
        const checkboxes = document.querySelectorAll('.image-checkbox:checked');
        if (checkboxes.length === 0) {
            showNotification('Please select at least one image.', 'error');
            return;
        }

        // Show loading spinner
        const originalHTML = downloadBtn.innerHTML;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';
        downloadBtn.disabled = true;

        try {
            const images = Array.from(checkboxes).map(checkbox => ({
                url: checkbox.value,
                title: checkbox.dataset.title
            }));

            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ images: images })
            });

            if (!response.ok) {
                throw new Error('Failed to download images.');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Task.zip';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            showNotification('Download started.', 'success');
        } catch (error) {
            console.error(error);
            showNotification(`Error: ${error.message}`, 'error');
        } finally {
            downloadBtn.innerHTML = originalHTML;
            downloadBtn.disabled = false;
        }
    });

    updateSelectedCount();
});

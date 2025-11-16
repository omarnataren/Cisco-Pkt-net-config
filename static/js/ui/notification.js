// Notificación
export function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = 'notification ' + (type === 'error' ? 'error' : '');
    notification.style.display = 'block';
    
    setTimeout(() => {
notification.style.display = 'none';
    }, 3000);
}
// Funciones de zoom
export function zoomIn() {
    const currentScale = network.getScale();
    if (currentScale < MAX_ZOOM) {
        network.moveTo({
            scale: Math.min(currentScale * 1.2, MAX_ZOOM),
            animation: { duration: 200, easingFunction: 'easeInOutQuad' }
        });
    }
}

export function zoomOut() {
    const currentScale = network.getScale();
    if (currentScale > MIN_ZOOM) {
        network.moveTo({
            scale: Math.max(currentScale / 1.2, MIN_ZOOM),
            animation: { duration: 200, easingFunction: 'easeInOutQuad' }
        });
    }
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.zoomIn = zoomIn;
window.zoomOut = zoomOut;
// ✅ Importaciones optimizadas
import { nodes, selectedNode } from '../core/network-state.js';
import { showNotification } from '../ui/notification.js';

// Actualizar nombre de dispositivo
export function updateDeviceName() {
    if (!selectedNode) return;
    
    const newName = document.getElementById('device-name-input').value.trim();
    
    if (!newName) {
        showNotification('El nombre no puede estar vacío', 'error');
        return;
    }
    
    // Verificar que el nombre no exista
    const existingNode = nodes.get().find(n => n.data.name === newName && n.id !== selectedNode);
    if (existingNode) {
        showNotification('Ya existe un dispositivo con ese nombre', 'error');
        return;
    }
    
    // Actualizar nodo
    nodes.update({
        id: selectedNode,
        label: newName,
        title: newName,
        data: {
            ...nodes.get(selectedNode).data,
            name: newName
        }
    });
    
    showNotification('Nombre actualizado');
    
    // Refrescar propiedades (función global)
    if (typeof window.showDeviceProperties === 'function') {
        window.showDeviceProperties(nodes.get(selectedNode));
    }
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.updateDeviceName = updateDeviceName;
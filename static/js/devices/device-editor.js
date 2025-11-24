// ✅ Importaciones optimizadas
import { showNotification } from '../ui/notification.js';

// Actualizar nombre de dispositivo
export function updateDeviceName() {
    if (!window.selectedNode) return;
    
    const newName = document.getElementById('device-name-input').value.trim();
    
    if (!newName) {
        showNotification('El nombre no puede estar vacío', 'error');
        return;
    }
    
    // Verificar que el nombre no exista
    const existingNode = window.nodes.get().find(n => n.data.name === newName && n.id !== window.selectedNode);
    if (existingNode) {
        showNotification('Ya existe un dispositivo con ese nombre', 'error');
        return;
    }
    
    // Actualizar nodo
    window.nodes.update({
        id: window.selectedNode,
        label: newName,
        title: newName,
        data: {
            ...window.nodes.get(window.selectedNode).data,
            name: newName
        }
    });
    
    showNotification('Nombre actualizado');
    
    // Refrescar propiedades (función global)
    if (typeof window.showDeviceProperties === 'function') {
        window.showDeviceProperties(window.nodes.get(window.selectedNode));
    }
}

// Actualizar VLAN de servidor
export function updateServerVlan() {
    if (!window.selectedNode) return;
    
    const node = window.nodes.get(window.selectedNode);
    if (node.data.type !== 'server') {
        showNotification('Esta función es solo para servidores', 'error');
        return;
    }
    
    const vlanSelect = document.getElementById('server-vlan-select');
    const selectedVlan = vlanSelect.value;
    
    // Actualizar nodo con VLAN
    window.nodes.update({
        id: window.selectedNode,
        data: {
            ...node.data,
            vlan: selectedVlan
        }
    });
    
    if (selectedVlan) {
        showNotification(`VLAN ${selectedVlan} asignada al servidor ${node.data.name}`);
    } else {
        showNotification('VLAN removida del servidor');
    }
    
    // Refrescar propiedades
    if (typeof window.showDeviceProperties === 'function') {
        window.showDeviceProperties(window.nodes.get(window.selectedNode));
    }
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.updateDeviceName = updateDeviceName;
window.updateServerVlan = updateServerVlan;
// ✅ Importaciones optimizadas
import { showNotification } from '../ui/notification.js';
import { releaseInterface } from '../devices/device-interfaces.js';

// Seleccionar nodo
export function selectNode(nodeId) {
    window.selectedNode = nodeId;
    window.selectedEdge = null;
    const node = window.nodes.get(nodeId);
    
    // Llamada a función global (definida en property-panel.js)
    if (typeof window.showDeviceProperties === 'function') {
        window.showDeviceProperties(node);
    }
}

// Seleccionar edge
export function selectEdge(edgeId) {
    window.selectedEdge = edgeId;
    window.selectedNode = null;
    showEdgeProperties(edgeId);
}


// Limpiar selección
export function clearSelection() {
    window.selectedNode = null;
    window.selectedEdge = null;
    const content = document.getElementById('properties-content');
    content.innerHTML = `
    <p style="color: #8b949e; text-align: center; padding: 40px 20px;">
        Selecciona un elemento para ver sus propiedades
    </p>
    `;
}

// Toggle para mostrar/ocultar más dispositivos
export function toggleMoreDevices() {
    const panel = document.getElementById('more-devices-panel');
    const arrow = document.getElementById('toggle-devices-arrow');
    const text = document.getElementById('toggle-devices-text');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        arrow.textContent = '▲';
        text.textContent = 'Ver menos dispositivos';
    } else {
        panel.style.display = 'none';
        arrow.textContent = '▼';
        text.textContent = 'Ver más dispositivos';
    }
}

// Eliminar selección
export function deleteSelected() {
    if (window.selectedNode) {
    const node = window.nodes.get(window.selectedNode);

    // Liberar interfaces de las conexiones antes de eliminarlas
    const connectedEdges = window.edges.get().filter(e => e.from === window.selectedNode || e.to === window.selectedNode);
    connectedEdges.forEach(edge => {
        const fromNode = window.nodes.get(edge.from);
        const toNode = window.nodes.get(edge.to);
        
        if (edge.data && edge.data.fromInterface && fromNode && fromNode.data.type === 'router') {
            releaseInterface(
                fromNode.data.name,
                edge.data.fromInterface.type,
                edge.data.fromInterface.number
            );
        }
        
        if (edge.data && edge.data.toInterface && toNode && toNode.data.type === 'router') {
            releaseInterface(
                toNode.data.name,
                edge.data.toInterface.type,
                edge.data.toInterface.number
            );
        }
        window.edges.remove(edge.id);
    });
        // Limpiar rastreador de interfaces del dispositivo eliminado
        if (window.usedInterfaces[node.data.name]) {
            delete window.usedInterfaces[node.data.name];
        }

        window.nodes.remove(window.selectedNode);
        showNotification(node.data.name + ' eliminado');
        clearSelection();
    } else if (window.selectedEdge) {
        // Llamar a función global
        if (typeof window.deleteConnection === 'function') {
            window.deleteConnection();
        }
    } else {
        showNotification('Selecciona un elemento primero', 'error');
    }
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.selectNode = selectNode;
window.selectEdge = selectEdge;
window.clearSelection = clearSelection;
window.deleteSelected = deleteSelected;
window.toggleMoreDevices = toggleMoreDevices;
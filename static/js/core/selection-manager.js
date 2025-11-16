// ✅ Importaciones optimizadas
import { nodes, edges, selectedNode, selectedEdge, usedInterfaces } from './network-state.js';
import { showNotification } from '../ui/notification.js';
import { releaseInterface } from '../devices/device-interfaces.js';

// Seleccionar nodo
export function selectNode(nodeId) {
    selectedNode = nodeId;
    selectedEdge = null;
    const node = nodes.get(nodeId);
    
    // Llamada a función global (definida en property-panel.js)
    if (typeof window.showDeviceProperties === 'function') {
        window.showDeviceProperties(node);
    }
}

// Seleccionar edge
export function selectEdge(edgeId) {
    selectedEdge = edgeId;
    selectedNode = null;
    showEdgeProperties(edgeId);
}


// Limpiar selección
export function clearSelection() {
    selectedNode = null;
    selectedEdge = null;
    const content = document.getElementById('properties-content');
    content.innerHTML = `
    <p style="color: #8b949e; text-align: center; padding: 40px 20px;">
        Selecciona un elemento para ver sus propiedades
    </p>
    `;
}

// Eliminar selección
export function deleteSelected() {
    if (selectedNode) {
    const node = nodes.get(selectedNode);

    // Liberar interfaces de las conexiones antes de eliminarlas
    const connectedEdges = edges.get().filter(e => e.from === selectedNode || e.to === selectedNode);
    connectedEdges.forEach(edge => {
        const fromNode = nodes.get(edge.from);
        const toNode = nodes.get(edge.to);
        
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
        edges.remove(edge.id);
    });
        // Limpiar rastreador de interfaces del dispositivo eliminado
        if (usedInterfaces[node.data.name]) {
            delete usedInterfaces[node.data.name];
        }

        nodes.remove(selectedNode);
        showNotification(node.data.name + ' eliminado');
        clearSelection();
    } else if (selectedEdge) {
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
// Guardar conexión editada
export function saveEditedConnection() {
    const connectionType = document.getElementById('edit-connection-type').value;
    const edge = edges.get(editingEdge);
    const currentDirection = edge.data.routingDirection || 'bidirectional';
    
    let updatedData = {
        id: editingEdge,
        arrows: getArrowsForDirection(currentDirection)
    };
    
    if (connectionType === 'etherchannel') {
        // Validar campos de EtherChannel
        const protocol = document.getElementById('etherchannel-protocol').value;
        const group = parseInt(document.getElementById('etherchannel-group').value);
        const fromTypeAbbr = document.getElementById('etherchannel-from-type').value;
        const fromType = interfaceTypeNames[fromTypeAbbr] || fromTypeAbbr;
        const fromRange = document.getElementById('etherchannel-from-range').value.trim();
        const toTypeAbbr = document.getElementById('etherchannel-to-type').value;
        const toType = interfaceTypeNames[toTypeAbbr] || toTypeAbbr;
        const toRange = document.getElementById('etherchannel-to-range').value.trim();

        if (!fromRange || !toRange) {
            showNotification('Completa los rangos de interfaces', 'error');
            return;
        }
        
        // Validar formato de rango (ej: 0/1-3)
        const rangePattern = /^\d+\/\d+-\d+$/;
        if (!rangePattern.test(fromRange) || !rangePattern.test(toRange)) {
            showNotification('Formato de rango inválido. Usa formato: 0/1-3', 'error');
            return;
        }

        updatedData.data = {
            etherChannel: {
                protocol: protocol,
                group: group,
                fromType: fromType,
                fromRange: fromRange,
                toType: toType,
                toRange: toRange
            },
            // IMPORTANTE: Mantener las interfaces también para compatibilidad
            fromInterface: { type: fromType, number: fromRange },
            toInterface: { type: toType, number: toRange },
            routingDirection: currentDirection,
            connectionType: 'etherchannel'
        };
        // Estilo visual para EtherChannel (3 líneas gruesas)
        updatedData.width = 6;
        updatedData.dashes = [2, 2];
        updatedData.smooth = { type: 'continuous' };
        updatedData.color = { color: '#58a6ff', highlight: '#79c0ff' };
    } else {
        // Conexión normal
        const fromTypeAbbr = document.getElementById('edit-from-type').value;
        const fromType = interfaceTypeNames[fromTypeAbbr] || fromTypeAbbr;
        const fromNumber = document.getElementById('edit-from-number').value.trim();
        const toTypeAbbr = document.getElementById('edit-to-type').value;
        const toType = interfaceTypeNames[toTypeAbbr] || toTypeAbbr;
        const toNumber = document.getElementById('edit-to-number').value.trim();
        if (!fromNumber || !toNumber) {
            showNotification('Completa todos los campos', 'error');
            return;
        }
        updatedData.data = {
            fromInterface: { type: fromType, number: fromNumber },
            toInterface: { type: toType, number: toNumber },
            routingDirection: currentDirection,
            connectionType: 'normal'
        };
        // Restaurar estilo normal
        updatedData.width = 2;
        updatedData.dashes = false;
        updatedData.color = { color: '#8b949e', highlight: '#58a6ff' };
    }
    
    edges.update(updatedData);
    closeEditConnectionModal();
    showNotification('Conexión actualizada');
    selectEdge(editingEdge);
}


// Eliminar conexión
export function deleteConnection() {
    if (!selectedEdge) return;
    
    // Obtener la conexión antes de eliminarla
    const edge = edges.get(selectedEdge);
    
    // Liberar interfaces si son routers
    const fromNode = nodes.get(edge.from);
    const toNode = nodes.get(edge.to);
    
    if (edge.data && edge.data.fromInterface && fromNode.data.type === 'router') {
releaseInterface(
    fromNode.data.name,
    edge.data.fromInterface.type,
    edge.data.fromInterface.number
);
    }
    
    if (edge.data && edge.data.toInterface && toNode.data.type === 'router') {
releaseInterface(
    toNode.data.name,
    edge.data.toInterface.type,
    edge.data.toInterface.number
);
    }
    
    edges.remove(selectedEdge);
    showNotification('Conexión eliminada');
    clearSelection();
}

function closeEditConnectionModal() {
    document.getElementById('edit-connection-modal').style.display = 'none';
}

// Exportar funciones a window para compatibilidad con onclick en HTML
window.saveEditedConnection = saveEditedConnection;
window.deleteConnection = deleteConnection;
window.closeEditConnectionModal = closeEditConnectionModal;
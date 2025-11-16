
// Guardar conexión
/**
 * Guarda una nueva conexión entre dos dispositivos
 * Puede ser conexión normal o EtherChannel según la selección del usuario
 */
export function saveConnection() {
    const connectionType = document.getElementById('new-connection-type').value;
    
    // Encontrar el ID del nodo destino
    let toNodeId = null;
    const toNameElement = document.getElementById('conn-to-name');
    nodes.forEach(node => {
        if (node.data.name === toNameElement.textContent) {
            toNodeId = node.id;
        }
    });
    
    const fromNode = nodes.get(firstNodeConnection);
    const toNode = nodes.get(toNodeId);
    
    // Determinar si debe tener direcciones de ruteo (solo router o switch_core)
    const isRoutingEdge = (fromNode.data.type === 'router' || fromNode.data.type === 'switch_core') &&
                        (toNode.data.type === 'router' || toNode.data.type === 'switch_core');
    
    const initialDirection = isRoutingEdge ? 'bidirectional' : 'none';
    const edgeId = 'edge_' + Date.now();
    
    let edgeData = {
        id: edgeId,
        from: firstNodeConnection,
        to: toNodeId,
        arrows: getArrowsForDirection(initialDirection)
    };
    
    if (connectionType === 'etherchannel') {
        // Configuración de EtherChannel
        const protocol = document.getElementById('new-etherchannel-protocol').value;
        const group = parseInt(document.getElementById('new-etherchannel-group').value);
        const fromTypeAbbr = document.getElementById('new-etherchannel-from-type').value;
        const fromType = interfaceTypeNames[fromTypeAbbr] || fromTypeAbbr;
        const fromRange = document.getElementById('new-etherchannel-from-range').value.trim();
        const toTypeAbbr = document.getElementById('new-etherchannel-to-type').value;
        const toType = interfaceTypeNames[toTypeAbbr] || toTypeAbbr;
        const toRange = document.getElementById('new-etherchannel-to-range').value.trim();

        if (!fromRange || !toRange) {
            showNotification('Completa los rangos de interfaces de origen y destino', 'error');
            return;
        }
        // Validar formato de rango (ej: 0/1-3)
        const rangePattern = /^\d+\/\d+-\d+$/;
        if (!rangePattern.test(fromRange) || !rangePattern.test(toRange)) {
            showNotification('Formato de rango inválido. Usa formato: 0/1-3', 'error');
            return;
        }
        // Datos de EtherChannel
        edgeData.data = {
            etherChannel: {
                protocol: protocol,
                group: group,
                fromType: fromType,
                fromRange: fromRange,
                toType: toType,
                toRange: toRange
            },
            // Mantener interfaces para compatibilidad
            fromInterface: { type: fromType, number: fromRange },
            toInterface: { type: toType, number: toRange },
            routingDirection: initialDirection,
            connectionType: 'etherchannel'
        };
        // Estilo visual para EtherChannel
        edgeData.width = 6;
        edgeData.dashes = [2, 2];
        edgeData.smooth = { type: 'continuous' };
        edgeData.color = { color: '#58a6ff', highlight: '#79c0ff' };
    } else {
        // Conexión normal
        let fromType, fromNumber, toType, toNumber;

        // Verificar si las interfaces fueron auto-asignadas (total o parcialmente)
        const modal = document.getElementById('connection-modal');
        const autoAssignedMode = modal.dataset.autoAssigned; // 'true', 'partial', o 'false'
        if (autoAssignedMode === 'true' || autoAssignedMode === 'partial') {
            // Hay al menos una interfaz auto-asignada
            const fromIfaceData = modal.dataset.fromInterface;
            const toIfaceData = modal.dataset.toInterface;
            
            // FROM: si está auto-asignada, usar datos guardados; sino, leer del formulario
            if (fromIfaceData) {
                const fromIface = JSON.parse(fromIfaceData);
                fromType = fromIface.type;
                fromNumber = fromIface.number;
            } else {
                const fromTypeAbbr = document.getElementById('conn-from-type').value;
                fromType = interfaceTypeNames[fromTypeAbbr] || fromTypeAbbr;
                fromNumber = document.getElementById('conn-from-number').value.trim();
                if (!fromNumber) {
                    showNotification('Completa la interfaz de origen', 'error');
                    return;
                }
            }
            
            // TO: si está auto-asignada, usar datos guardados; sino, leer del formulario
            if (toIfaceData) {
                const toIface = JSON.parse(toIfaceData);
                toType = toIface.type;
                toNumber = toIface.number;
            } else {
                const toTypeAbbr = document.getElementById('conn-to-type').value;
                toType = interfaceTypeNames[toTypeAbbr] || toTypeAbbr;
                toNumber = document.getElementById('conn-to-number').value.trim();
                if (!toNumber) {
                    showNotification('Completa la interfaz de destino', 'error');
                    return;
                }
            }
        } else {
            // Leer del formulario (conexión manual completa)
            const fromTypeAbbr = document.getElementById('conn-from-type').value;
            fromType = interfaceTypeNames[fromTypeAbbr] || fromTypeAbbr;
            fromNumber = document.getElementById('conn-from-number').value.trim();
            const toTypeAbbr = document.getElementById('conn-to-type').value;
            toType = interfaceTypeNames[toTypeAbbr] || toTypeAbbr;
            toNumber = document.getElementById('conn-to-number').value.trim();
            
            if (!fromNumber || !toNumber) {
                showNotification('Completa todos los campos', 'error');
                return;
            }
        }
        edgeData.data = {
            fromInterface: { type: fromType, number: fromNumber },
            toInterface: { type: toType, number: toNumber },
            routingDirection: initialDirection,
            connectionType: 'normal'
        };
    }
    
    // Agregar la conexión al grafo
    edges.add(edgeData);
    
    closeConnectionModal();
    showNotification('Conexión creada');
    connectionMode = false;
    firstNodeConnection = null;
    document.getElementById('connect-btn').classList.remove('active');
}
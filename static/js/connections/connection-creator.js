
// Guardar conexión
/**
 * Guarda una nueva conexión entre dos dispositivos
 * Puede ser conexión normal o EtherChannel según la selección del usuario
 */
/**
 * Verifica si un puerto ya está en uso en cualquier conexión
 * o computadora conectada en toda la topología.
 */
window.isPortInUseCorrect = function (nodeId, fullPortString) {

    // Si viene vacío, null o undefined → no está en uso
    if (!fullPortString || typeof fullPortString !== "string") {
        return false;
    }

    // Separar el tipo y el número
    // fullPortString = "FastEthernet0/1"
    let type = "";
    let number = "";

    try {
        type = fullPortString.replace(/[0-9\/]+$/, ""); // "FastEthernet"
        number = fullPortString.replace(/^\D+/, "");    // "0/1"
    } catch (e) {
        console.warn("Formato inválido de puerto:", fullPortString);
        return false;
    }

    // 1. Revisar TODAS las conexiones del grafo
    const edges = window.edges.get();

    for (const edge of edges) {

        // Revisar origen
        if (
            edge.from === nodeId &&
            edge.data?.fromInterface &&
            edge.data.fromInterface.type === type &&
            edge.data.fromInterface.number === number
        ) {
            return true;
        }

        // Revisar destino
        if (
            edge.to === nodeId &&
            edge.data?.toInterface &&
            edge.data.toInterface.type === type &&
            edge.data.toInterface.number === number
        ) {
            return true;
        }
    }

    // 2. Revisar PCs conectadas
    const node = window.nodes.get(nodeId);
    if (node?.data?.computers) {
        for (const pc of node.data.computers) {
            if (pc.portNumber === fullPortString) {
                return true;
            }
        }
    }

    return false;
};



export function saveConnection() {
    const connectionType = document.getElementById('new-connection-type').value;
    
    let toNodeId = null;
    const toNameElement = document.getElementById('conn-to-name');
    window.nodes.forEach(node => {
        if (node.data.name === toNameElement.textContent) {
            toNodeId = node.id;
        }
    });
    
    const fromNode = window.nodes.get(window.firstNodeConnection);
    const toNode = window.nodes.get(toNodeId);
    
    // Verificar si el puerto de la conexión de origen está en uso
    const fromPort = document.getElementById('conn-from-number').value.trim();
    if (isPortInUseCorrect(fromPort)) {
        window.showNotification(`El puerto ${fromPort} ya está en uso`, 'error');
        return;
    }

    // Verificar si el puerto de la conexión de destino está en uso
    const toPort = document.getElementById('conn-to-number').value.trim();
    if (isPortInUseCorrect(toPort)) {
        window.showNotification(`El puerto ${toPort} ya está en uso`, 'error');
        return;
    }
    
    const isRoutingEdge = (fromNode.data.type === 'router' || fromNode.data.type === 'switch_core') &&
                        (toNode.data.type === 'router' || toNode.data.type === 'switch_core');
    
    const initialDirection = isRoutingEdge ? 'bidirectional' : 'none';
    const edgeId = 'edge_' + Date.now();
    
    let edgeData = {
        id: edgeId,
        from: window.firstNodeConnection,
        to: toNodeId,
        arrows: window.getArrowsForDirection(initialDirection)
    };
    
    if (connectionType === 'etherchannel') {
        // Configuración de EtherChannel
        const protocol = document.getElementById('new-etherchannel-protocol').value;
        const group = parseInt(document.getElementById('new-etherchannel-group').value);
        const fromTypeAbbr = document.getElementById('new-etherchannel-from-type').value;
        const fromType = window.interfaceTypeNames[fromTypeAbbr] || fromTypeAbbr;
        const fromRange = document.getElementById('new-etherchannel-from-range').value.trim();
        const toTypeAbbr = document.getElementById('new-etherchannel-to-type').value;
        const toType = window.interfaceTypeNames[toTypeAbbr] || toTypeAbbr;
        const toRange = document.getElementById('new-etherchannel-to-range').value.trim();

        if (!fromRange || !toRange) {
            window.showNotification('Completa los rangos de interfaces de origen y destino', 'error');
            return;
        }
        // Validar formato de rango (ej: 0/1-3)
        const rangePattern = /^\d+\/\d+-\d+$/;
        if (!rangePattern.test(fromRange) || !rangePattern.test(toRange)) {
            window.showNotification('Formato de rango inválido. Usa formato: 0/1-3', 'error');
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
            fromInterface: { type: fromType, number: fromRange },
            toInterface: { type: toType, number: toRange },
            routingDirection: initialDirection,
            connectionType: 'etherchannel'
        };
        // Estilo visual para EtherChannel (3 líneas gruesas)
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
            const fromIfaceData = modal.dataset.fromInterface;
            const toIfaceData = modal.dataset.toInterface;
            
            // FROM: si está auto-asignada, usar datos guardados; sino, leer del formulario
            if (fromIfaceData) {
                const fromIface = JSON.parse(fromIfaceData);
                fromType = fromIface.type;
                fromNumber = fromIface.number;
            } else {
                const fromTypeAbbr = document.getElementById('conn-from-type').value;
                fromType = window.interfaceTypeNames[fromTypeAbbr] || fromTypeAbbr;
                fromNumber = document.getElementById('conn-from-number').value.trim();
                if (!fromNumber) {
                    window.showNotification('Completa la interfaz de origen', 'error');
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
                toType = window.interfaceTypeNames[toTypeAbbr] || toTypeAbbr;
                toNumber = document.getElementById('conn-to-number').value.trim();
                if (!toNumber) {
                    window.showNotification('Completa la interfaz de destino', 'error');
                    return;
                }
            }
        } else {
            // Leer del formulario (conexión manual completa)
            const fromTypeAbbr = document.getElementById('conn-from-type').value;
            fromType = window.interfaceTypeNames[fromTypeAbbr] || fromTypeAbbr;
            fromNumber = document.getElementById('conn-from-number').value.trim();
            const toTypeAbbr = document.getElementById('conn-to-type').value;
            toType = window.interfaceTypeNames[toTypeAbbr] || toTypeAbbr;
            toNumber = document.getElementById('conn-to-number').value.trim();
            
            if (!fromNumber || !toNumber) {
                window.showNotification('Completa todos los campos', 'error');
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
    window.edges.add(edgeData);
    
    window.closeConnectionModal();
    window.showNotification('Conexión creada');
    window.connectionMode = false;
    window.firstNodeConnection = null;
    document.getElementById('connect-btn').classList.remove('active');
}


// Exportar funciones a window para compatibilidad con onclick en HTML
window.saveConnection = saveConnection;
// closeConnectionModal está definido en modals.js
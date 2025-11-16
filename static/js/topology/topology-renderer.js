// Inicializar red
export function initNetwork() {
    const container = document.getElementById('network-canvas');
    const data = { nodes: window.nodes, edges: window.edges };
    const options = {
        nodes: {
            shape: 'circle',
            size: 30,
            borderWidth: 2,
            font: { 
                color: '#ffffff', 
                size: 11
            }
        },
        edges: {
            color: { color: '#8b949e', highlight: '#58a6ff' },
            width: 3,
            smooth: { type: 'continuous' },
            arrows: {
                to: {
                    scaleFactor: 1.2
                },
                from: {
                    scaleFactor: 1.2
                }
            }
        },
        physics: {
            enabled: false
        },
        interaction: {
            dragNodes: true,
            dragView: true,
            zoomView: true,
            zoomSpeed: 1.5,
            hover: true
        }
    };
    
    window.network = new vis.Network(container, data, options);
    
    // Eventos
    window.network.on('click', function(params) {
    // Si estamos en modo posicionamiento, posicionar el dispositivo
        if (window.devicePositioningMode) {
            // Las coordenadas ya están en canvas, usar directamente
            const pos = params.pointer.canvas;
            createDeviceAtPosition(pos.x, pos.y);
            return;
        }
        if (window.connectionMode && params.nodes.length > 0) {
            handleConnectionClick(params.nodes[0]);
        } else if (params.nodes.length > 0) {
            selectNode(params.nodes[0]);
        } else if (params.edges.length > 0) {
            selectEdge(params.edges[0]);
        } else {
            clearSelection();
        }
    });
    
    // Doble clic en edge para cambiar dirección
    window.network.on('doubleClick', function(params) {
    if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edge = window.edges.get(edgeId);
    
        // Solo permitir cambio en conexiones entre routers/switch cores
        const fromNode = window.nodes.get(edge.from);
        const toNode = window.nodes.get(edge.to);
        const isRoutingEdge = (fromNode.data.type === 'router' || fromNode.data.type === 'switch_core') &&
                                (toNode.data.type === 'router' || toNode.data.type === 'switch_core');
        
        if (isRoutingEdge) {
            cycleRoutingDirection(edgeId);
        }
    }
    });
    // Evento dragEnd: Se dispara cuando el usuario termina de mover un nodo
    // ACTUALIZA explícitamente las coordenadas en el DataSet de vis.network
    window.network.on('dragEnd', function(params) {
        if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodeData = window.nodes.get(nodeId);
    
        // El nodo ha sido movido, necesitamos actualizar explícitamente sus coordenadas
        // vis.network mueve visualmente el nodo pero NO actualiza automáticamente el DataSet
        const pos = window.network.getPositions(nodeId);
        if (pos[nodeId]) {
            const newX = pos[nodeId].x;
            const newY = pos[nodeId].y;
            
            // ACTUALIZAR el nodo en el DataSet con las nuevas coordenadas
            window.nodes.update({
                id: nodeId,
                x: newX,
                y: newY
            });
            
            console.log(`✓ Dispositivo ${nodeData.label} actualizado a: x=${Math.round(newX)}, y=${Math.round(newY)}`);
        }
    }
    });
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.initNetwork = initNetwork;
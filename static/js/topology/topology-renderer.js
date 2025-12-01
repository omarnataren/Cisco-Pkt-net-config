// Inicializar red
export function initNetwork() {
    const container = document.getElementById('network-canvas');
    const data = { nodes: window.nodes, edges: window.edges };
    const options = {
        nodes: {
            shape: 'circle',
            size: 20,
            borderWidth: 2,
            font: { 
                color: '#000000', 
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
    
    // Dibujar etiquetas de interfaces en los cables
    window.network.on('afterDrawing', function(ctx) {
        drawInterfaceLabels(ctx);
    });
}

/**
 * Dibuja las etiquetas de interfaces cerca de cada dispositivo en los cables
 * @param {CanvasRenderingContext2D} ctx - Contexto del canvas
 */
function drawInterfaceLabels(ctx) {
    const edges = window.edges.get();
    const nodePositions = window.network.getPositions();
    
    edges.forEach(edge => {
        if (!edge.data || !edge.data.fromInterface || !edge.data.toInterface) return;
        
        const fromPos = nodePositions[edge.from];
        const toPos = nodePositions[edge.to];
        
        if (!fromPos || !toPos) return;
        
        // Calcular el ángulo del cable
        const dx = toPos.x - fromPos.x;
        const dy = toPos.y - fromPos.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance === 0) return;
        
        // Normalizar dirección
        const nx = dx / distance;
        const ny = dy / distance;
        
        // Distancia desde el nodo (ajustar según el tamaño del nodo + offset)
        const nodeRadius = 35; // Tamaño aproximado del nodo
        const labelOffset = 5; // Separación adicional
        
        // Posición de la etiqueta "from" (cerca del nodo origen)
        const fromLabelX = fromPos.x + nx * (nodeRadius + labelOffset);
        const fromLabelY = fromPos.y + ny * (nodeRadius + labelOffset);
        
        // Posición de la etiqueta "to" (cerca del nodo destino)
        const toLabelX = toPos.x - nx * (nodeRadius + labelOffset);
        const toLabelY = toPos.y - ny * (nodeRadius + labelOffset);
        
        // Formatear texto de interfaces (abreviado)
        const fromText = formatInterfaceLabel(edge.data.fromInterface);
        const toText = formatInterfaceLabel(edge.data.toInterface);
        
        // Configurar estilo del texto
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Dibujar etiqueta "from" con fondo
        drawLabelWithBackground(ctx, fromText, fromLabelX, fromLabelY);
        
        // Dibujar etiqueta "to" con fondo
        drawLabelWithBackground(ctx, toText, toLabelX, toLabelY);
    });
}

/**
 * Formatea el nombre de la interfaz de forma abreviada
 * @param {Object} iface - Objeto con type y number
 * @returns {string} Interfaz abreviada (ej: "Gi0/0", "Fa0/1")
 */
function formatInterfaceLabel(iface) {
    if (!iface || !iface.type || iface.number === undefined) return '';
    
    // Abreviaturas comunes
    const abbreviations = {
        'GigabitEthernet': 'Gi',
        'FastEthernet': 'Fa',
        'Ethernet': 'Eth',
        'Serial': 'Se',
        'Loopback': 'Lo',
        'Vlan': 'Vl',
        'Port-channel': 'Po'
    };
    
    const abbr = abbreviations[iface.type] || iface.type.substring(0, 2);
    return `${abbr}${iface.number}`;
}

/**
 * Dibuja una etiqueta con fondo semitransparente
 * @param {CanvasRenderingContext2D} ctx - Contexto del canvas
 * @param {string} text - Texto a dibujar
 * @param {number} x - Posición X
 * @param {number} y - Posición Y
 */
function drawLabelWithBackground(ctx, text, x, y) {
    if (!text) return;
    
    const padding = 5;
    const metrics = ctx.measureText(text);
    const width = metrics.width + padding * 2;
    const height = 14;
    
    // Fondo semitransparente
    ctx.fillStyle = 'rgba(225, 225, 225, 0.84)';
    ctx.beginPath();
    ctx.roundRect(x - width / 2, y - height / 2, width, height, 3);
    ctx.fill();
    
    // Borde sutil
    ctx.strokeStyle = 'rgba(72, 72, 72, 0.5)';
    ctx.lineWidth = 1;
    ctx.stroke();
    
    // Texto
    ctx.fillStyle = '#000000ff';
    ctx.fillText(text, x, y);
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.initNetwork = initNetwork;
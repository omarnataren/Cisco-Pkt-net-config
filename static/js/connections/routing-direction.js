
// Convertir dirección de ruteo a configuración de flechas
export function getArrowsForDirection(direction) {
    switch(direction) {
        case 'from-to':
            return { 
                to: { 
                    enabled: true, 
                    scaleFactor: 1.2,
                    type: 'arrow'
                },
                from: {
                    enabled: false
                }
            };
        case 'to-from':
            return { 
                to: {
                    enabled: false
                },
                from: { 
                    enabled: true, 
                    scaleFactor: 1.2,
                    type: 'arrow'
                } 
            };
        case 'bidirectional':
            return { 
                to: { 
                    enabled: true, 
                    scaleFactor: 1.2,
                    type: 'arrow'
                },
                from: { 
                    enabled: true, 
                    scaleFactor: 1.2,
                    type: 'arrow'
                }
            };
        case 'none':
        default:
            return {
                to: { enabled: false },
                from: { enabled: false }
            };
    }
}


// Cambiar dirección de ruteo cíclicamente
export function cycleRoutingDirection(edgeId) {
    if (!edgeId) return;
    
    const edge = window.edges.get(edgeId);
    const currentDirection = edge.data.routingDirection || 'bidirectional';
    
    // Ciclo: bidirectional → from-to → to-from → none → bidirectional
    const cycle = {
        'bidirectional': 'from-to',
        'from-to': 'to-from',
        'to-from': 'none',
        'none': 'bidirectional'
    };
    
    const newDirection = cycle[currentDirection];
    
    // Actualizar edge
    window.edges.update({
        id: edgeId,
        data: {
            ...edge.data,
            routingDirection: newDirection
        },
        arrows: getArrowsForDirection(newDirection)
    });
    
    // Actualizar propiedades si este edge está seleccionado
    if (window.selectedEdge === edgeId) {
        window.showEdgeProperties(edgeId);
    }
    
    const directionNames = {
        'bidirectional': 'Bidireccional',
        'from-to': 'Unidireccional →',
        'to-from': 'Unidireccional ←',
        'none': 'Sin ruteo'
    };
    window.showNotification('Dirección: ' + directionNames[newDirection]);
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.getArrowsForDirection = getArrowsForDirection;
window.cycleRoutingDirection = cycleRoutingDirection;

// ✅ Importaciones optimizadas
import { nodes, edges } from '../core/network-state.js';

// Mostrar propiedades de dispositivo
export function showDeviceProperties(node) {
    const typeNames = {
        'router': 'Router',
        'switch': 'Switch',
        'switch_core': 'Switch Core'
    };
    
    const content = document.getElementById('properties-content');
    
    // Botón de administrar computadoras solo para switches
    const computersButton = (node.data.type === 'switch' || node.data.type === 'switch_core') ? 
        '<button class="btn" onclick="openManageComputersModal()" style="background: #238636; margin-top: 10px;">💻 Administrar Computadoras</button>' : '';
    
    content.innerHTML = `
    <div class="property-group">
        <h4>Nombre del Dispositivo</h4>
        <div class="input-group">
            <input type="text" id="device-name-input" value="${node.data.name}" style="margin-bottom: 10px;">
        </div>
        <button class="btn" onclick="updateDeviceName()">Cambiar Nombre</button>
    </div>
    <div class="property-group">
        <h4>Tipo</h4>
        <div style="color: #8b949e; font-size: 14px;">${typeNames[node.data.type] || node.data.type}</div>
    </div>
    ${computersButton}
    <div class="property-group">
        <h4>Conexiones</h4>
        <div id="device-connections"></div>
    </div>
    `;
    
    // Listar conexiones
    const conns = edges.get().filter(e => e.from === node.id || e.to === node.id);
    const connDiv = document.getElementById('device-connections');
    
    if (conns.length === 0) {
            connDiv.innerHTML = '<p style="color: #8b949e; font-size: 12px;">Sin conexiones</p>';
    } else {
    conns.forEach(edge => {
        const otherNodeId = edge.from === node.id ? edge.to : edge.from;
        const otherNode = nodes.get(otherNodeId);
        const isFrom = edge.from === node.id;
        const myInterface = isFrom ? edge.data.fromInterface : edge.data.toInterface;
        
        const item = document.createElement('div');
        item.style.cssText = 'background: #21262d; padding: 10px; border-radius: 6px; margin-bottom: 8px;';
        item.innerHTML = `
            <div style="color: #c9d1d9; margin-bottom: 5px;">${otherNode.data.name}</div>
            <div style="color: #8b949e; font-size: 11px;">
                ${myInterface.type}${myInterface.number}
            </div>
        `;
        connDiv.appendChild(item);
    });
    }
}

// Mostrar propiedades de conexión
export function showEdgeProperties(edgeId) {
    const edge = edges.get(edgeId);
    const fromNode = nodes.get(edge.from);
    const toNode = nodes.get(edge.to);
    
    const routingDirection = edge.data.routingDirection || 'bidirectional';
    const isEtherChannel = edge.data.etherChannel || edge.data.connectionType === 'etherchannel';
    
    // Determinar símbolo de dirección para la flecha central
    let directionSymbol = '↕'; // bidireccional por defecto
    let directionLabel = 'Bidireccional';
    
    if (routingDirection === 'from-to') {
        directionSymbol = '→';
        directionLabel = 'Unidireccional';
    } else if (routingDirection === 'to-from') {
        directionSymbol = '←';
        directionLabel = 'Unidireccional';
    } else if (routingDirection === 'none') {
        directionSymbol = '—';
        directionLabel = 'Sin ruteo';
    }
    
    const content = document.getElementById('properties-content');
    
    let connectionInfo = '';
    
    if (isEtherChannel) {
        const ec = edge.data.etherChannel;
        const protocolName = ec.protocol === 'lacp' ? 'LACP' : 'PAgP';
        const modeFrom = ec.protocol === 'lacp' ? 'active' : 'desirable';
        const modeTo = ec.protocol === 'lacp' ? 'passive' : 'auto';

        connectionInfo = `
            <div class="property-group">
                <h4>EtherChannel</h4>
                <div style="background: #21262d; padding: 15px; border-radius: 6px;">
                    <div style="margin-bottom: 10px;">
                        <div style="color: #58a6ff; font-weight: bold;">${fromNode.data.name}</div>
                        <div style="color: #8b949e; font-size: 11px;">
                            ${ec.fromType}${ec.fromRange} → Port-channel ${ec.group}
                        </div>
                        <div style="color: #6e7681; font-size: 10px; margin-top: 3px;">
                            Modo: ${modeFrom}
                        </div>
                    </div>
                    <div style="text-align: center; color: #8b949e; margin: 10px 0; font-size: 18px;">⚡ ${protocolName} ⚡</div>
                    <div>
                        <div style="color: #58a6ff; font-weight: bold;">${toNode.data.name}</div>
                        <div style="color: #8b949e; font-size: 11px;">
                            ${ec.toType}${ec.toRange} → Port-channel ${ec.group}
                        </div>
                        <div style="color: #6e7681; font-size: 10px; margin-top: 3px;">
                            Modo: ${modeTo}
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else {
        connectionInfo = `
            <div class="property-group">
                <h4>Conexión</h4>
                <div style="background: #21262d; padding: 15px; border-radius: 6px;">
                    <div style="margin-bottom: 10px;">
                        <div style="color: #58a6ff; font-weight: bold;">${fromNode.data.name}</div>
                        <div style="color: #8b949e; font-size: 11px;">
                            ${edge.data.fromInterface.type}${edge.data.fromInterface.number}
                        </div>
                    </div>
                    <div style="text-align: center; color: #8b949e; margin: 10px 0; font-size: 18px;">${directionSymbol}</div>
                    <div>
                        <div style="color: #58a6ff; font-weight: bold;">${toNode.data.name}</div>
                        <div style="color: #8b949e; font-size: 11px;">
                            ${edge.data.toInterface.type}${edge.data.toInterface.number}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    content.innerHTML = `
        ${connectionInfo}
        ${!isEtherChannel ? `
        <div class="property-group">
            <h4>Dirección de Ruteo</h4>
            <div style="background: #21262d; padding: 12px; border-radius: 6px; color: #8b949e;">
                ${directionLabel}
            </div>
        </div>` : ''}
        <button class="btn" onclick="openEditConnectionModal()">Editar Conexión</button>
        <button class="btn btn-danger" onclick="deleteConnection()" style="margin-top: 10px;">Eliminar Conexión</button>
    `;
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.showDeviceProperties = showDeviceProperties;
window.showEdgeProperties = showEdgeProperties;
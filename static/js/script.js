// Variables globales
let network = null;
let nodes = new vis.DataSet([]);
let edges = new vis.DataSet([]);
let vlans = [];
let routerCounter = 1;
let switchCounter = 1;
let switchCoreCounter = 1;
let computerCounter = 1;
let connectionMode = false;
let firstNodeConnection = null;
let selectedNode = null;
let selectedEdge = null;
let editingEdge = null;
let devicePositioningMode = false;
let pendingDeviceType = null;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3.0;

// Rastreador de interfaces usadas por dispositivo
let usedInterfaces = {};

/**
 * Orden de interfaces para routers:
 *  FastEthernet0/0-1 (2 puertos)
 *  Ethernet0/0-3/0 (4 puertos)
 */
const ROUTER_INTERFACE_ORDER = [
    { type: 'FastEthernet', number: '0/0' },
    { type: 'FastEthernet', number: '0/1' },
    { type: 'Ethernet', number: '0/3/0' },
    { type: 'Ethernet', number: '0/2/0' },
    { type: 'Ethernet', number: '0/1/0' },
    { type: 'Ethernet', number: '0/0/0' }
];

/**
 * Orden de asignación de interfaces para Switches (2960)
 * FastEthernet: 0/1 a 0/24 (24 puertos)
 * GigabitEthernet: 0/1 a 0/2 (2 puertos)
 */
const SWITCH_INTERFACE_ORDER = [
    // FastEthernet 0/1 a 0/24
    ...Array.from({ length: 24 }, (_, i) => ({ 
    type: 'FastEthernet', 
    number: `0/${i + 1}` 
    })),
    // GigabitEthernet 0/1 a 0/2
    { type: 'GigabitEthernet', number: '0/1' },
    { type: 'GigabitEthernet', number: '0/2' }
];

const SWITCH_CORE_INTERFACE_ORDER = [
    // GigabitEthernet 1/0/1 a 1/0/24
    ...Array.from({ length: 24 }, (_, i) => ({ 
    type: 'GigabitEthernet', 
    number: `1/0/${i + 1}` 
    })),
    // GigabitEthernet 1/1/1 a 1/1/4
    ...Array.from({ length: 4 }, (_, i) => ({ 
    type: 'GigabitEthernet', 
    number: `1/1/${i + 1}` 
    })),
];

/**
 * Obtiene la siguiente interfaz disponible para un dispositivo
 * @param {string} deviceName - Nombre del dispositivo
 * @param {string} deviceType - Tipo de dispositivo (router, switch, switch_core, computer)
 * @returns {object|null} - {type, number} o null si no hay disponibles
 */
function getNextAvailableInterface(deviceName, deviceType) {
    // Inicializar rastreador si no existe
    if (!usedInterfaces[deviceName]) {
        usedInterfaces[deviceName] = [];
    }
    
    if (deviceType === 'router') {
// Para routers, seguir el orden estricto
        for (let iface of ROUTER_INTERFACE_ORDER) {
            const key = `${iface.type}${iface.number}`;
            if (!usedInterfaces[deviceName].includes(key)) {
                usedInterfaces[deviceName].push(key);
                return { type: iface.type, number: iface.number };
            }
        }
        console.error(`No hay más interfaces disponibles para el router ${deviceName}`);
        return null;
    }
    
    if (deviceType === 'switch') {
// Para switches, seguir el orden: FastEthernet 0/1-24, luego GigabitEthernet 0/1-2
        for (let iface of SWITCH_INTERFACE_ORDER) {
            const key = `${iface.type}${iface.number}`;
            if (!usedInterfaces[deviceName].includes(key)) {
                usedInterfaces[deviceName].push(key);
                return { type: iface.type, number: iface.number };
            }
        }
        console.error(`No hay más interfaces disponibles para el switch ${deviceName}`);
        return null;
    }

    if (deviceType === 'switch_core') {
// Para switches core, seguir el orden: GigabitEthernet 1/0/1-1/0/24, luego GigabitEthernet 1/1/1-1/1/4
        for (let iface of SWITCH_CORE_INTERFACE_ORDER) {
            const key = `${iface.type}${iface.number}`;
            if (!usedInterfaces[deviceName].includes(key)) {
                usedInterfaces[deviceName].push(key);
                return { type: iface.type, number: iface.number };
            }
        }
        console.error(`No hay más interfaces disponibles para el switch core ${deviceName}`);
        return null;
    }
    
    // Para otros dispositivos, mantener lógica existente
    // ( computer)
    return null; // Se asignarán manualmente por ahora
}

/**
 * Libera una interfaz de un dispositivo (al eliminar conexión)
 * @param {string} deviceName - Nombre del dispositivo
 * @param {string} interfaceType - Tipo de interfaz
 * @param {string} interfaceNumber - Número de interfaz
 */
function releaseInterface(deviceName, interfaceType, interfaceNumber) {
    if (!usedInterfaces[deviceName]) return;
    
    const key = `${interfaceType}${interfaceNumber}`;
    const index = usedInterfaces[deviceName].indexOf(key);
    if (index > -1) {
usedInterfaces[deviceName].splice(index, 1);
    }
}

// Inicializar red
function initNetwork() {
    const container = document.getElementById('network-canvas');
    const data = { nodes: nodes, edges: edges };
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
    
    network = new vis.Network(container, data, options);
    
    // Eventos
    network.on('click', function(params) {
    // Si estamos en modo posicionamiento, posicionar el dispositivo
        if (devicePositioningMode) {
            // Las coordenadas ya están en canvas, usar directamente
            const pos = params.pointer.canvas;
            createDeviceAtPosition(pos.x, pos.y);
            return;
        }

        if (connectionMode && params.nodes.length > 0) {
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
    network.on('doubleClick', function(params) {
    if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edge = edges.get(edgeId);
    
        // Solo permitir cambio en conexiones entre routers/switch cores
        const fromNode = nodes.get(edge.from);
        const toNode = nodes.get(edge.to);
        const isRoutingEdge = (fromNode.data.type === 'router' || fromNode.data.type === 'switch_core') &&
                                (toNode.data.type === 'router' || toNode.data.type === 'switch_core');
        
        if (isRoutingEdge) {
            cycleRoutingDirection(edgeId);
        }
    }
    });

    // Evento dragEnd: Se dispara cuando el usuario termina de mover un nodo
    // ACTUALIZA explícitamente las coordenadas en el DataSet de vis.network
    network.on('dragEnd', function(params) {
        if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodeData = nodes.get(nodeId);
    
        // El nodo ha sido movido, necesitamos actualizar explícitamente sus coordenadas
        // vis.network mueve visualmente el nodo pero NO actualiza automáticamente el DataSet
        const pos = network.getPositions(nodeId);
    
        if (pos[nodeId]) {
            const newX = pos[nodeId].x;
            const newY = pos[nodeId].y;
            
            // ACTUALIZAR el nodo en el DataSet con las nuevas coordenadas
            nodes.update({
                id: nodeId,
                x: newX,
                y: newY
            });
            
            console.log(`✓ Dispositivo ${nodeData.label} actualizado a: x=${Math.round(newX)}, y=${Math.round(newY)}`);
        }
    }
    });
}

// Convertir dirección de ruteo a configuración de flechas
function getArrowsForDirection(direction) {
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

// Agregar dispositivo
function addDevice(type) {
    // Activar modo de posicionamiento
    devicePositioningMode = true;
    pendingDeviceType = type;
    
    // Cambiar cursor y mostrar mensaje
    document.getElementById('network-canvas').style.cursor = 'crosshair';
    showNotification(`Haz click en el área de trabajo para posicionar el dispositivo`, 'info');
    
    // Cambiar estilo del botón para indicar que está activo
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
if (btn.getAttribute('onclick') === `addDevice('${type}')`) {
    btn.classList.add('active');
}
    });
}

function createDeviceAtPosition(x, y) {
    if (!devicePositioningMode || !pendingDeviceType) return;
    
    let name, color, shape, deviceType;
    const type = pendingDeviceType;
    
    switch(type) {
case 'router':
    name = 'R' + routerCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'circle';
    deviceType = 'router';
    break;
case 'switch':
    name = 'SW' + switchCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'box';
    deviceType = 'switch';
    break;
case 'switch_core':
    name = 'SWC' + switchCoreCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'box';
    deviceType = 'switch_core';
    break;
case 'computer':
    name = 'PC' + computerCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'circle';
    deviceType = 'computer';
    break;
    }
    
    const id = deviceType + '_' + Date.now();
    nodes.add({
id: id,
label: name,
title: name,
shape: shape,
size: 30,
x: x,  // Coordenada X exacta posicionada por el usuario
y: y,  // Coordenada Y exacta posicionada por el usuario - Se usarán en PTBuilder
fixed: false,  // Permitir que el nodo sea arrastrable
color: color,
font: {
    color: '#ffffff',
    size: 11
},
data: {
    type: deviceType,
    name: name,
    connections: [],
    vlan: null  // Para computadoras
}
    });
    
    // Desactivar modo de posicionamiento
    devicePositioningMode = false;
    pendingDeviceType = null;
    document.getElementById('network-canvas').style.cursor = 'default';
    
    // Remover clase active de todos los botones
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    showNotification(`${name} agregado exitosamente`, 'success');
}

// Agregar VLAN
function addVLAN() {
    const name = document.getElementById('vlan-name').value.trim();
    const prefix = document.getElementById('vlan-prefix').value;
    
    if (!name) {
showNotification('Ingresa un nombre para la VLAN', 'error');
return;
    }
    
    // Verificar que no exista
    if (vlans.find(v => v.name === name)) {
showNotification('Esta VLAN ya existe', 'error');
return;
    }
    
    vlans.push({ name: name, prefix: prefix });
    document.getElementById('vlan-name').value = '';
    updateVLANList();
    showNotification('VLAN ' + name + ' agregada');
}

// Actualizar lista de VLANs
function updateVLANList() {
    const list = document.getElementById('vlan-list');
    list.innerHTML = '';
    
    vlans.forEach((vlan, index) => {
const item = document.createElement('div');
item.className = 'vlan-item';
item.innerHTML = `
    <div class="vlan-item-info">
        <div class="vlan-item-name">${vlan.name}</div>
        <div class="vlan-item-prefix">Prefijo: /${vlan.prefix}</div>
    </div>
    <button class="vlan-item-delete" onclick="deleteVLAN(${index})">✕</button>
`;
list.appendChild(item);
    });
    
    // Actualizar select de computadoras
    updateComputerVlanSelect();
}

// Eliminar VLAN
function deleteVLAN(index) {
    vlans.splice(index, 1);
    updateVLANList();
    showNotification('VLAN eliminada');
}

// Actualizar select de VLANs para computadoras
function updateComputerVlanSelect() {
    const select = document.getElementById('computer-vlan-select');
    select.innerHTML = '<option value="">-- Selecciona VLAN --</option>';
    vlans.forEach(vlan => {
const option = document.createElement('option');
option.value = vlan.name;
option.textContent = vlan.name + ' (/' + vlan.prefix + ')';
select.appendChild(option);
    });
}

// Modo de conexión con toggle
function toggleConnectionMode() {
    connectionMode = !connectionMode;
    firstNodeConnection = null;
    
    const btn = document.getElementById('connect-btn');
    if (connectionMode) {
btn.classList.add('active');
showNotification('Modo conexión activado. Haz clic en dos dispositivos');
    } else {
btn.classList.remove('active');
showNotification('Modo conexión desactivado');
    }
}

// Mantener compatibilidad
function enableConnectionMode() {
    if (!connectionMode) {
toggleConnectionMode();
    }
}

// Manejar clic para conexión
function handleConnectionClick(nodeId) {
    if (!firstNodeConnection) {
firstNodeConnection = nodeId;
const node = nodes.get(nodeId);
showNotification('Seleccionado: ' + node.data.name + '. Ahora selecciona el destino');
    } else {
if (firstNodeConnection === nodeId) {
    showNotification('No puedes conectar un dispositivo consigo mismo', 'error');
    firstNodeConnection = null;
    return;
}

// Abrir modal para configurar conexión
const fromNode = nodes.get(firstNodeConnection);
const toNode = nodes.get(nodeId);

// Auto-asignar interfaces para routers y switches
let fromInterface = null;
let toInterface = null;

// Asignar interfaz para el nodo origen (router, switch o switch_core)
if (fromNode.data.type === 'router' || fromNode.data.type === 'switch' || fromNode.data.type === 'switch_core') {
    fromInterface = getNextAvailableInterface(fromNode.data.name, fromNode.data.type);
    if (!fromInterface) {
        showNotification(`No hay interfaces disponibles en ${fromNode.data.name}`, 'error');
        firstNodeConnection = null;
        return;
    }
}

// Asignar interfaz para el nodo destino (router, switch o switch_core)
if (toNode.data.type === 'router' || toNode.data.type === 'switch' || toNode.data.type === 'switch_core') {
    toInterface = getNextAvailableInterface(toNode.data.name, toNode.data.type);
    if (!toInterface) {
        // Liberar la interfaz del origen si ya se asignó
        if (fromInterface) {
            releaseInterface(fromNode.data.name, fromInterface.type, fromInterface.number);
        }
        showNotification(`No hay interfaces disponibles en ${toNode.data.name}`, 'error');
        firstNodeConnection = null;
        return;
    }
}

// Resetear el modal a valores por defecto
document.getElementById('new-connection-type').value = 'normal';

// Función helper para mapear tipo de interfaz a valor del select
function getInterfaceTypeSelectValue(interfaceType) {
    if (interfaceType === 'FastEthernet') return 'fa';
    if (interfaceType === 'GigabitEthernet') return 'gi';
    if (interfaceType === 'Ethernet') return 'eth';
    return 'fa'; // default
}

// Si hay al menos un dispositivo con interfaz asignada, configurar el modal
if (fromInterface || toInterface) {
    // Configurar interfaz FROM
    if (fromInterface) {
        document.getElementById('conn-from-type').value = getInterfaceTypeSelectValue(fromInterface.type);
        document.getElementById('conn-from-number').value = fromInterface.number;
        document.getElementById('conn-from-type').disabled = true;
        document.getElementById('conn-from-number').disabled = true;
        document.getElementById('conn-from-auto-notice').style.display = 'block';
    } else {
        document.getElementById('conn-from-type').value = 'fa';
        document.getElementById('conn-from-number').value = '0/0';
        document.getElementById('conn-from-type').disabled = false;
        document.getElementById('conn-from-number').disabled = false;
        document.getElementById('conn-from-auto-notice').style.display = 'none';
    }
    
    // Configurar interfaz TO
    if (toInterface) {
        document.getElementById('conn-to-type').value = getInterfaceTypeSelectValue(toInterface.type);
        document.getElementById('conn-to-number').value = toInterface.number;
        document.getElementById('conn-to-type').disabled = true;
        document.getElementById('conn-to-number').disabled = true;
        document.getElementById('conn-to-auto-notice').style.display = 'block';
    } else {
        document.getElementById('conn-to-type').value = 'fa';
        document.getElementById('conn-to-number').value = '0/0';
        document.getElementById('conn-to-type').disabled = false;
        document.getElementById('conn-to-number').disabled = false;
        document.getElementById('conn-to-auto-notice').style.display = 'none';
    }
    
    // Guardar en el modal para referencia
    document.getElementById('connection-modal').dataset.fromInterface = fromInterface ? JSON.stringify(fromInterface) : '';
    document.getElementById('connection-modal').dataset.toInterface = toInterface ? JSON.stringify(toInterface) : '';
    document.getElementById('connection-modal').dataset.autoAssigned = 'partial';
} else {
    // Conexión manual (ningún router involucrado)
    document.getElementById('conn-from-type').value = 'fa';
    document.getElementById('conn-from-number').value = '0/0';
    document.getElementById('conn-to-type').value = 'fa';
    document.getElementById('conn-to-number').value = '0/0';
    
    // Habilitar selects
    document.getElementById('conn-from-type').disabled = false;
    document.getElementById('conn-from-number').disabled = false;
    document.getElementById('conn-to-type').disabled = false;
    document.getElementById('conn-to-number').disabled = false;
    
    // Ocultar avisos
    document.getElementById('conn-from-auto-notice').style.display = 'none';
    document.getElementById('conn-to-auto-notice').style.display = 'none';
    
    document.getElementById('connection-modal').dataset.autoAssigned = 'false';
}

// Resetear campos de EtherChannel
document.getElementById('new-etherchannel-protocol').value = 'lacp';
document.getElementById('new-etherchannel-group').value = '1';
document.getElementById('new-etherchannel-from-type').value = 'fa';
document.getElementById('new-etherchannel-from-range').value = '0/1-3';
document.getElementById('new-etherchannel-to-type').value = 'fa';
document.getElementById('new-etherchannel-to-range').value = '0/1-3';

// Mostrar campos normales y ocultar EtherChannel
document.getElementById('new-normal-fields').style.display = 'block';
document.getElementById('new-etherchannel-fields').style.display = 'none';

updateFromInterfaceList();
updateToInterfaceList();

document.getElementById('conn-from-name').textContent = fromNode.data.name;
document.getElementById('conn-to-name').textContent = toNode.data.name;
document.getElementById('conn-to-name-ec').textContent = toNode.data.name;
document.getElementById('connection-modal').style.display = 'block';
    }
}

// Guardar conexión
/**
 * Guarda una nueva conexión entre dos dispositivos
 * Puede ser conexión normal o EtherChannel según la selección del usuario
 */
function saveConnection() {
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

// Cerrar modal de conexión
function closeConnectionModal() {
    document.getElementById('connection-modal').style.display = 'none';
    
    // Resetear todos los campos a valores por defecto
    document.getElementById('new-connection-type').value = 'normal';
    document.getElementById('conn-from-type').value = 'fa';
    document.getElementById('conn-from-number').innerHTML = '<option value="">Seleccionar interfaz...</option>';
    document.getElementById('conn-to-type').value = 'fa';
    document.getElementById('conn-to-number').innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    // Resetear campos de EtherChannel
    document.getElementById('new-etherchannel-protocol').value = 'lacp';
    document.getElementById('new-etherchannel-group').value = '1';
    document.getElementById('new-etherchannel-from-type').value = 'fa';
    document.getElementById('new-etherchannel-from-range').value = '0/1-3';
    document.getElementById('new-etherchannel-to-type').value = 'fa';
    document.getElementById('new-etherchannel-to-range').value = '0/1-3';

    // Mostrar campos normales y ocultar EtherChannel
    document.getElementById('new-normal-fields').style.display = 'block';
    document.getElementById('new-etherchannel-fields').style.display = 'none';
    
    firstNodeConnection = null;
    connectionMode = false;
    document.getElementById('connect-btn').classList.remove('active');
}

// Seleccionar nodo
function selectNode(nodeId) {
    selectedNode = nodeId;
    selectedEdge = null;
    const node = nodes.get(nodeId);
    
    if (node.data.type === 'computer') {
showComputerProperties(node);
    } else {
showDeviceProperties(node);
    }
}

// Seleccionar edge
function selectEdge(edgeId) {
    selectedEdge = edgeId;
    selectedNode = null;
    showEdgeProperties(edgeId);
}

// Cambiar dirección de ruteo cíclicamente
function cycleRoutingDirection(edgeId) {
    if (!edgeId) return;
    
    const edge = edges.get(edgeId);
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
    edges.update({
id: edgeId,
data: {
    ...edge.data,
    routingDirection: newDirection
},
arrows: getArrowsForDirection(newDirection)
    });
    
    // Actualizar propiedades si este edge está seleccionado
    if (selectedEdge === edgeId) {
showEdgeProperties(edgeId);
    }
    
    const directionNames = {
'bidirectional': 'Bidireccional',
'from-to': 'Unidireccional →',
'to-from': 'Unidireccional ←',
'none': 'Sin ruteo'
    };
    showNotification('Dirección: ' + directionNames[newDirection]);
}

// Funciones de zoom
function zoomIn() {
    const currentScale = network.getScale();
    if (currentScale < MAX_ZOOM) {
network.moveTo({
    scale: Math.min(currentScale * 1.2, MAX_ZOOM),
    animation: { duration: 200, easingFunction: 'easeInOutQuad' }
});
    }
}

function zoomOut() {
    const currentScale = network.getScale();
    if (currentScale > MIN_ZOOM) {
network.moveTo({
    scale: Math.max(currentScale / 1.2, MIN_ZOOM),
    animation: { duration: 200, easingFunction: 'easeInOutQuad' }
});
    }
}

// Mostrar propiedades de dispositivo
function showDeviceProperties(node) {
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

// Mostrar propiedades de computadora
function showComputerProperties(node) {
    const content = document.getElementById('properties-content');
    const vlanInfo = node.data.vlan ? 
`<div style="color: #238636; font-weight: bold;">${node.data.vlan}</div>` :
`<div style="color: #8b949e;">Sin asignar</div>`;
    
    content.innerHTML = `
<div class="property-group">
    <h4>${node.data.name}</h4>
    <div style="color: #8b949e; font-size: 12px;">Computadora</div>
</div>
<div class="property-group">
    <h4>VLAN Asignada</h4>
    ${vlanInfo}
</div>
<button class="btn" onclick="openComputerVlanModal()">Cambiar VLAN</button>
    `;
}

// Actualizar nombre de dispositivo
function updateDeviceName() {
    if (!selectedNode) return;
    
    const newName = document.getElementById('device-name-input').value.trim();
    
    if (!newName) {
showNotification('El nombre no puede estar vacío', 'error');
return;
    }
    
    // Verificar que el nombre no exista
    const existingNode = nodes.get().find(n => n.data.name === newName && n.id !== selectedNode);
    if (existingNode) {
showNotification('Ya existe un dispositivo con ese nombre', 'error');
return;
    }
    
    // Actualizar nodo
    nodes.update({
id: selectedNode,
label: newName,
title: newName,
data: {
    ...nodes.get(selectedNode).data,
    name: newName
}
    });
    
    showNotification('Nombre actualizado');
    showDeviceProperties(nodes.get(selectedNode));
}

// Mostrar propiedades de conexión
function showEdgeProperties(edgeId) {
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

// Abrir modal para editar conexión
function openEditConnectionModal() {
    if (!selectedEdge) return;
    
    const edge = edges.get(selectedEdge);
    editingEdge = selectedEdge;
    
    const isEtherChannel = edge.data.etherChannel || edge.data.connectionType === 'etherchannel';
    
    document.getElementById('edit-connection-type').value = isEtherChannel ? 'etherchannel' : 'normal';
    
    if (isEtherChannel) {
// Cargar datos de EtherChannel
document.getElementById('etherchannel-protocol').value = edge.data.etherChannel.protocol || 'lacp';
document.getElementById('etherchannel-group').value = edge.data.etherChannel.group || 1;
const ecFromType = edge.data.etherChannel.fromType || 'FastEthernet';
const ecToType = edge.data.etherChannel.toType || 'FastEthernet';
document.getElementById('etherchannel-from-type').value = interfaceTypeAbbr[ecFromType] || 'fa';
document.getElementById('etherchannel-from-range').value = edge.data.etherChannel.fromRange || '';
document.getElementById('etherchannel-to-type').value = interfaceTypeAbbr[ecToType] || 'fa';
document.getElementById('etherchannel-to-range').value = edge.data.etherChannel.toRange || '';
    } else {
// Cargar datos de conexión normal
const fromType = edge.data.fromInterface.type;
const toType = edge.data.toInterface.type;
document.getElementById('edit-from-type').value = interfaceTypeAbbr[fromType] || 'fa';
document.getElementById('edit-from-number').value = edge.data.fromInterface.number;
document.getElementById('edit-to-type').value = interfaceTypeAbbr[toType] || 'fa';
document.getElementById('edit-to-number').value = edge.data.toInterface.number;
    }
    
    toggleEtherChannelFields();
    document.getElementById('edit-connection-modal').style.display = 'block';
}

/**
 * Alterna entre campos de conexión normal y EtherChannel en modal de edición
 * Valida que ambos extremos sean switches antes de permitir EtherChannel
 */
function toggleEtherChannelFields() {
    const connectionType = document.getElementById('edit-connection-type').value;
    const normalFields = document.getElementById('normal-connection-fields');
    const etherChannelFields = document.getElementById('etherchannel-fields');
    
    if (connectionType === 'etherchannel') {
// Validar que ambos extremos sean switches
const edge = edges.get(editingEdge);
const fromNode = nodes.get(edge.from);
const toNode = nodes.get(edge.to);

const fromIsSwitch = fromNode.data.type === 'switch' || fromNode.data.type === 'switch_core';
const toIsSwitch = toNode.data.type === 'switch' || toNode.data.type === 'switch_core';

if (!fromIsSwitch || !toIsSwitch) {
    showNotification('EtherChannel solo puede configurarse entre switches', 'error');
    document.getElementById('edit-connection-type').value = 'normal';
    normalFields.style.display = 'block';
    etherChannelFields.style.display = 'none';
    return;
}

normalFields.style.display = 'none';
etherChannelFields.style.display = 'block';
    } else {
normalFields.style.display = 'block';
etherChannelFields.style.display = 'none';
    }
}

/**
 * Datos de interfaces disponibles por tipo
 * Solo contiene los números, el tipo se maneja por separado
 */
const interfaceData = {
    fa: [
'0/0', '0/1', '0/2', '0/3', '0/4', '0/5', '0/6', '0/7',
'0/8', '0/9', '0/10', '0/11', '0/12', '0/13', '0/14', '0/15',
'0/16', '0/17', '0/18', '0/19', '0/20', '0/21', '0/22', '0/23', '0/24'
    ],
    gi: [
'1/0/1', '1/0/2', '1/0/3', '1/0/4', '1/0/5', '1/0/6', '1/0/7', '1/0/8',
'1/0/9', '1/0/10', '1/0/11', '1/0/12', '1/0/13', '1/0/14', '1/0/15', '1/0/16',
'1/0/17', '1/0/18', '1/0/19', '1/0/20', '1/0/21', '1/0/22', '1/0/23'
    ],
    eth: [
'0/0/0', '0/1/0', '0/2/0', '0/3/0',
'1/0', '1/1', '1/2', '1/3'
    ]
};

/**
 * Mapeo de tipos abreviados a nombres completos para mostrar en UI
 */
const interfaceTypeNames = {
    'fa': 'FastEthernet',
    'gi': 'GigabitEthernet',
    'eth': 'Ethernet'
};

/**
 * Mapeo inverso: nombres completos a abreviaciones
 */
const interfaceTypeAbbr = {
    'FastEthernet': 'fa',
    'GigabitEthernet': 'gi',
    'Ethernet': 'eth'
};

/**
 * Actualiza la lista de interfaces de origen
 */
function updateFromInterfaceList() {
    const typeSelect = document.getElementById('conn-from-type');
    const interfaceSelect = document.getElementById('conn-from-number');
    const selectedType = typeSelect.value;
    
    // Limpiar opciones previas
    interfaceSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    // Agregar interfases del tipo seleccionado
    const interfaces = interfaceData[selectedType] || [];
    const typeName = interfaceTypeNames[selectedType] || '';
    
    interfaces.forEach(ifaceNumber => {
const option = document.createElement('option');
option.value = ifaceNumber;  // ✅ Solo el número (ej: "0/1")
option.textContent = typeName + ifaceNumber;  // Para mostrar (ej: "FastEthernet0/1")
interfaceSelect.appendChild(option);
    });
}

/**
 * Actualiza la lista de interfaces de destino
 */
function updateToInterfaceList() {
    const typeSelect = document.getElementById('conn-to-type');
    const interfaceSelect = document.getElementById('conn-to-number');
    const selectedType = typeSelect.value;
    
    // Limpiar opciones previas
    interfaceSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    // Agregar interfases del tipo seleccionado
    const interfaces = interfaceData[selectedType] || [];
    const typeName = interfaceTypeNames[selectedType] || '';
    
    interfaces.forEach(ifaceNumber => {
const option = document.createElement('option');
option.value = ifaceNumber;  // ✅ Solo el número (ej: "0/1")
option.textContent = typeName + ifaceNumber;  // Para mostrar (ej: "FastEthernet0/1")
interfaceSelect.appendChild(option);
    });
}

/**
 * Actualiza la lista de interfaces de origen para EtherChannel
 */
function updateEtherChannelFromList() {
    const typeSelect = document.getElementById('new-etherchannel-from-type');
    const interfaceSelect = document.getElementById('new-etherchannel-from-range');
    const selectedType = typeSelect.value;
    
    // Limpiar opciones previas
    interfaceSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    // Agregar interfases del tipo seleccionado
    const interfaces = interfaceData[selectedType] || [];
    const typeName = interfaceTypeNames[selectedType] || '';
    
    interfaces.forEach(ifaceNumber => {
const option = document.createElement('option');
option.value = ifaceNumber;  // ✅ Solo el número (ej: "0/1")
option.textContent = typeName + ifaceNumber;  // Para mostrar (ej: "FastEthernet0/1")
interfaceSelect.appendChild(option);
    });
}

/**
 * Actualiza la lista de interfaces de destino para EtherChannel
 */
function updateEtherChannelToList() {
    const typeSelect = document.getElementById('new-etherchannel-to-type');
    const interfaceSelect = document.getElementById('new-etherchannel-to-range');
    const selectedType = typeSelect.value;
    
    // Limpiar opciones previas
    interfaceSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    // Agregar interfases del tipo seleccionado
    const interfaces = interfaceData[selectedType] || [];
    const typeName = interfaceTypeNames[selectedType] || '';
    
    interfaces.forEach(ifaceNumber => {
const option = document.createElement('option');
option.value = ifaceNumber;  // ✅ Solo el número (ej: "0/1")
option.textContent = typeName + ifaceNumber;  // Para mostrar (ej: "FastEthernet0/1")
interfaceSelect.appendChild(option);
    });
}

/**
 * Actualiza la lista de puertos disponibles para agregar PC
 */
function updateNewPcPortList() {
    const typeSelect = document.getElementById('new-pc-port-type');
    const portSelect = document.getElementById('new-pc-port-number');
    const selectedType = typeSelect.value;
    
    // Limpiar opciones previas
    portSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    // Agregar interfaces del tipo seleccionado
    const interfaces = interfaceData[selectedType] || [];
    const typeName = interfaceTypeNames[selectedType] || '';
    
    interfaces.forEach(ifaceNumber => {
const option = document.createElement('option');
option.value = ifaceNumber;  // ✅ Solo el número (ej: "0/1" o "1/0/1")
option.textContent = typeName + ifaceNumber;  // Para mostrar (ej: "FastEthernet0/1" o "GigabitEthernet1/0/1")
portSelect.appendChild(option);
    });
}

/**
 * Alterna entre campos normales y EtherChannel en modal de NUEVA conexión
 * Valida que ambos nodos seleccionados sean switches
 */
function toggleNewConnectionFields() {
    const connectionType = document.getElementById('new-connection-type').value;
    const normalFields = document.getElementById('new-normal-fields');
    const etherChannelFields = document.getElementById('new-etherchannel-fields');
    
    if (connectionType === 'etherchannel') {
// Validar que ambos nodos sean switches
if (firstNodeConnection) {
    const fromNode = nodes.get(firstNodeConnection);
    const fromIsSwitch = fromNode.data.type === 'switch' || fromNode.data.type === 'switch_core';
    
    if (!fromIsSwitch) {
        showNotification('EtherChannel solo funciona entre switches', 'error');
        document.getElementById('new-connection-type').value = 'normal';
        return;
    }
}

normalFields.style.display = 'none';
etherChannelFields.style.display = 'block';
// Copiar nombre del destino también en sección EtherChannel
document.getElementById('conn-to-name-ec').textContent = 
    document.getElementById('conn-to-name').textContent;
// Inicializar listas de interfaces para EtherChannel
updateEtherChannelFromList();
updateEtherChannelToList();
    } else {
normalFields.style.display = 'block';
etherChannelFields.style.display = 'none';
    }
}

// Guardar conexión editada
function saveEditedConnection() {
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

// Cerrar modal de edición
function closeEditConnectionModal() {
    document.getElementById('edit-connection-modal').style.display = 'none';
    editingEdge = null;
}

// Eliminar conexión
function deleteConnection() {
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

// Abrir modal de VLAN para computadora
function openComputerVlanModal() {
    if (!selectedNode) return;
    
    const node = nodes.get(selectedNode);
    if (node.data.type !== 'computer') return;
    
    document.getElementById('computer-name').textContent = node.data.name;
    document.getElementById('computer-vlan-select').value = node.data.vlan || '';
    document.getElementById('computer-vlan-modal').style.display = 'block';
}

// Guardar VLAN de computadora
function saveComputerVlan() {
    const vlanName = document.getElementById('computer-vlan-select').value;
    
    if (!vlanName) {
showNotification('Selecciona una VLAN', 'error');
return;
    }
    
    const node = nodes.get(selectedNode);
    const currentPosition = network.getPositions([selectedNode])[selectedNode];
    
    node.data.vlan = vlanName;
    // Mantener posición al actualizar
    node.x = currentPosition.x;
    node.y = currentPosition.y;
    nodes.update(node);
    
    closeComputerVlanModal();
    showNotification('VLAN asignada a ' + node.data.name);
    selectNode(selectedNode);
}

// Cerrar modal de VLAN
function closeComputerVlanModal() {
    document.getElementById('computer-vlan-modal').style.display = 'none';
}

// Administrar computadoras del switch
let currentSwitchForComputers = null; // Variable para guardar el switch actual

function openManageComputersModal() {
    console.log('openManageComputersModal - selectedNode:', selectedNode);
    
    if (!selectedNode) {
showNotification('Selecciona un switch primero', 'error');
return;
    }
    
    // Obtener el nodo completo desde la colección
    let node;
    if (typeof selectedNode === 'string') {
// Si selectedNode es un ID string, obtener el nodo completo
node = nodes.get(selectedNode);
    } else if (selectedNode.id) {
// Si selectedNode tiene id, obtener el nodo completo
node = nodes.get(selectedNode.id);
    } else {
// Si selectedNode ya es el objeto completo
node = selectedNode;
    }
    
    console.log('node obtenido:', node);
    console.log('node.data:', node ? node.data : 'undefined');
    
    if (!node || !node.data) {
showNotification('Error al obtener información del switch', 'error');
return;
    }
    
    console.log('node.data.type:', node.data.type);
    
    if (node.data.type !== 'switch' && node.data.type !== 'switch_core') {
showNotification('Solo puedes administrar computadoras en switches', 'error');
return;
    }
    
    // Guardar referencia al switch
    currentSwitchForComputers = node;
    
    const switchName = currentSwitchForComputers.data.name;
    document.getElementById('switch-computers-name').textContent = switchName;
    
    // Inicializar si no existe
    if (!currentSwitchForComputers.data.computers) {
currentSwitchForComputers.data.computers = [];
    }
    
    updateComputersList();
    document.getElementById('manage-computers-modal').style.display = 'block';
}

function closeManageComputersModal() {
    document.getElementById('manage-computers-modal').style.display = 'none';
}

function updateComputersList() {
    const listDiv = document.getElementById('computers-list');
    const computers = currentSwitchForComputers.data.computers || [];
    
    if (computers.length === 0) {
listDiv.innerHTML = '<p style="color: #8b949e; font-size: 12px; text-align: center; padding: 20px;">No hay computadoras conectadas</p>';
return;
    }
    
    listDiv.innerHTML = '';
    computers.forEach((pc, index) => {
const item = document.createElement('div');
item.style.cssText = 'background: #21262d; padding: 12px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;';
item.innerHTML = `
    <div>
        <div style="color: #58a6ff; font-weight: bold; margin-bottom: 4px;">${pc.name}</div>
        <div style="color: #8b949e; font-size: 11px;">Puerto: ${pc.portType}${pc.portNumber} • VLAN: ${pc.vlan}</div>
    </div>
    <button onclick="removeComputer(${index})" style="background: #da3633; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">🗑️ Eliminar</button>
`;
listDiv.appendChild(item);
    });
}

function removeComputer(index) {
    if (confirm('¿Eliminar esta computadora?')) {
currentSwitchForComputers.data.computers.splice(index, 1);
nodes.update(currentSwitchForComputers);
updateComputersList();
showNotification('Computadora eliminada');
    }
}

function openAddComputerModal() {
    console.log('openAddComputerModal llamada');
    console.log('currentSwitchForComputers:', currentSwitchForComputers);
    
    // Generar nombre automático
    const existingComputers = currentSwitchForComputers.data.computers || [];
    const pcCount = existingComputers.length + 1;
    document.getElementById('new-pc-name').value = `PC${pcCount}`;
    
    console.log('Nombre generado:', `PC${pcCount}`);
    
    // Llenar select de VLANs - USAR ARRAY VLANS DIRECTAMENTE
    const vlanSelect = document.getElementById('new-pc-vlan');
    vlanSelect.innerHTML = '<option value="">-- Selecciona VLAN --</option>';
    
    if (vlans.length === 0) {
showNotification('No hay VLANs creadas. Crea VLANs primero.', 'error');
return;
    }
    
    console.log('VLANs encontradas:', vlans.length);
    
    // Usar directamente el array vlans, no parsear el HTML
    for (let i = 0; i < vlans.length; i++) {
const vlanName = vlans[i].name; // Solo el nombre, sin el prefijo
const option = document.createElement('option');
option.value = vlanName;
option.textContent = vlanName;
vlanSelect.appendChild(option);
    }
    
    // Inicializar lista de puertos
    updateNewPcPortList();
    
    console.log('Abriendo modal...');
    document.getElementById('add-computer-modal').style.display = 'block';
}

function closeAddComputerModal() {
    document.getElementById('add-computer-modal').style.display = 'none';
}

function saveNewComputer() {
    const name = document.getElementById('new-pc-name').value.trim();
    const portType = document.getElementById('new-pc-port-type').value;
    const portNumber = document.getElementById('new-pc-port-number').value.trim();
    const vlan = document.getElementById('new-pc-vlan').value;
    
    console.log('Datos de nueva PC:', { name, portType, portNumber, vlan });
    
    if (!name) {
showNotification('Ingresa el nombre de la PC', 'error');
return;
    }
    
    if (!portNumber) {
showNotification('Selecciona el puerto del switch', 'error');
return;
    }
    
    if (!vlan) {
showNotification('Selecciona una VLAN', 'error');
return;
    }
    
    // Verificar que el puerto no esté en uso
    const computers = currentSwitchForComputers.data.computers || [];
    const portInUse = computers.some(pc => pc.portType === portType && pc.portNumber === portNumber);
    if (portInUse) {
showNotification('Ese puerto ya está en uso', 'error');
return;
    }
    
    // Agregar computadora
    if (!currentSwitchForComputers.data.computers) {
currentSwitchForComputers.data.computers = [];
    }
    
    currentSwitchForComputers.data.computers.push({
name: name,
portType: portType,
portNumber: portNumber,
vlan: vlan
    });
    
    console.log('Computadora agregada:', currentSwitchForComputers.data.computers);
    
    nodes.update(currentSwitchForComputers);
    updateComputersList();
    closeAddComputerModal();
    showNotification(`Computadora ${name} agregada`);
}

// Limpiar selección
function clearSelection() {
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
function deleteSelected() {
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
deleteConnection();
    } else {
showNotification('Selecciona un elemento primero', 'error');
    }
}

// Generar configuraciones
function generateConfigurations() {
    if (nodes.length === 0) {
showNotification('Agrega dispositivos primero', 'error');
return;
    }
    
    // Obtener el valor del primer octeto de red base
    const baseOctet = document.getElementById('base-network-octet').value || '19';
    
    // Crear formulario y enviar datos a nueva pestaña
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/';
    form.target = '_blank';  // Abrir en nueva pestaña
    
    // Serializar datos
    const data = {
nodes: nodes.get(),
edges: edges.get(),
vlans: vlans,
baseNetworkOctet: parseInt(baseOctet)  // Agregar el primer octeto
    };
    
    // Verificar coordenadas antes de enviar
    console.log('📊 Coordenadas de dispositivos a enviar:');
    data.nodes.forEach(node => {
console.log(`  ${node.data.name}: x=${Math.round(node.x)}, y=${Math.round(node.y)}`);
    });
    console.log(`🌐 Red base: ${baseOctet}.0.0.0/8`);
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'topology_data';
    input.value = JSON.stringify(data);
    
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    
    // Mostrar notificación
    showNotification('Generando configuraciones en nueva pestaña...');
    
    // Remover formulario después de enviar
    setTimeout(() => {
document.body.removeChild(form);
    }, 100);
}

// Notificación
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = 'notification ' + (type === 'error' ? 'error' : '');
    notification.style.display = 'block';
    
    setTimeout(() => {
notification.style.display = 'none';
    }, 3000);
}

// Inicializar al cargar
window.onload = function() {
    initNetwork();
};

// Cerrar modales al hacer clic fuera del contenido
window.onclick = function(event) {
    const modals = ['connection-modal', 'edit-connection-modal', 'computer-vlan-modal'];
    modals.forEach(modalId => {
const modal = document.getElementById(modalId);
if (event.target === modal) {
    modal.style.display = 'none';
    // Limpiar estado si es modal de conexión
    if (modalId === 'connection-modal') {
        firstNodeConnection = null;
        connectionMode = false;
        document.getElementById('connect-btn').classList.remove('active');
    }
}
    });
};


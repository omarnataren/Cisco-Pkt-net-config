/**
 * Escanea todas las conexiones y computadoras, construyendo un mapa de interfaces en uso
 * @param {string} deviceName - Opcional: nombre del dispositivo específico
 * @returns {object|array} - Mapa completo o array de interfaces del dispositivo
 */
function scanUsedInterfaces(deviceName = null) {
    const usedMap = {};
    
    // Escanear conexiones entre dispositivos
    window.edges.forEach(edge => {
        const fromNode = window.nodes.get(edge.from);
        const toNode = window.nodes.get(edge.to);
        
        if (!fromNode || !toNode) return;
        
        const fromName = fromNode.data.name;
        const toName = toNode.data.name;
        
        // Registrar interfaz FROM
        if (!usedMap[fromName]) usedMap[fromName] = [];
        const fromKey = `${edge.data.fromInterface.type}${edge.data.fromInterface.number}`;
        if (!usedMap[fromName].includes(fromKey)) {
            usedMap[fromName].push(fromKey);
        }
        
        // Registrar interfaz TO
        if (!usedMap[toName]) usedMap[toName] = [];
        const toKey = `${edge.data.toInterface.type}${edge.data.toInterface.number}`;
        if (!usedMap[toName].includes(toKey)) {
            usedMap[toName].push(toKey);
        }
    });
    
    // Escanear computadoras conectadas a switches
    window.nodes.forEach(node => {
        if ((node.data.type === 'switch' || node.data.type === 'switch_core') && node.data.computers) {
            const nodeName = node.data.name;
            if (!usedMap[nodeName]) usedMap[nodeName] = [];
            
            node.data.computers.forEach(pc => {
                const pcKey = `${pc.portType}${pc.portNumber}`;
                if (!usedMap[nodeName].includes(pcKey)) {
                    usedMap[nodeName].push(pcKey);
                }
            });
        }
    });
    
    return deviceName ? (usedMap[deviceName] || []) : usedMap;
}

/**
 * Verifica si el cache de interfaces necesita resincronización
 * Considera conexiones Y computadoras
 * @param {string} deviceName - Nombre del dispositivo
 * @returns {boolean} - True si necesita resync
 */
function needsResync(deviceName) {
    const node = window.nodes.get().find(n => n.data.name === deviceName);
    if (!node) return false;
    
    // Contar conexiones reales
    const realConnections = window.edges.get().filter(e => 
        e.data.from === deviceName || e.data.to === deviceName
    ).length;
    
    // Contar computadoras si es switch
    const computerCount = ((node.data.type === 'switch' || node.data.type === 'switch_core') && node.data.computers) 
        ? node.data.computers.length 
        : 0;
    
    const cacheCount = (window.usedInterfaces[deviceName] || []).length;
    
    return (realConnections + computerCount) !== cacheCount;
}

/**
 * Resincroniza el cache de interfaces con las conexiones reales
 * @param {string} deviceName - Nombre del dispositivo
 */
function resyncInterfaces(deviceName) {
    const realUsed = scanUsedInterfaces(deviceName);
    window.usedInterfaces[deviceName] = realUsed;
    console.log(`Resync ${deviceName}: ${realUsed.length} interfaces`);
}

/**
 * Obtiene la siguiente interfaz disponible con validación automática
 * @param {string} deviceName - Nombre del dispositivo
 * @param {string} deviceType - Tipo de dispositivo (router, switch, switch_core, computer)
 * @param {string} model - Modelo del dispositivo (opcional, para modo físico)
 * @returns {object|null} - {type, number} o null si no hay disponibles
 */
export function getNextAvailableInterface(deviceName, deviceType, model = null) {
    if (needsResync(deviceName)) {
        resyncInterfaces(deviceName);
    }
    
    if (!window.usedInterfaces[deviceName]) {
        window.usedInterfaces[deviceName] = [];
    }
    
    let interfaceOrder;
    
    if (window.deviceMode === 'physical' && model) {
        interfaceOrder = window.getDeviceInterfaces(deviceType, model);
    } else {
        if (deviceType === 'router') {
            interfaceOrder = window.ROUTER_INTERFACE_ORDER;
        } else if (deviceType === 'switch') {
            interfaceOrder = window.SWITCH_INTERFACE_ORDER;
        } else if (deviceType === 'switch_core') {
            interfaceOrder = window.SWITCH_CORE_INTERFACE_ORDER;
        } else if (deviceType === 'computer') {
            interfaceOrder = window.COMPUTER_INTERFACE_ORDER;
        } else {
            return null;
        }
    }
    
    for (let iface of interfaceOrder) {
        const key = `${iface.type}${iface.number}`;
        if (!window.usedInterfaces[deviceName].includes(key)) {
            window.usedInterfaces[deviceName].push(key);
            return { type: iface.type, number: iface.number };
        }
    }
    
    console.error(`No hay más interfaces disponibles para ${deviceName} (${deviceType}${model ? ' - ' + model : ''})`);
    return null;
}

/**
 * Libera una interfaz de un dispositivo (al eliminar conexión)
 * @param {string} deviceName - Nombre del dispositivo
 * @param {string} interfaceType - Tipo de interfaz
 * @param {string} interfaceNumber - Número de interfaz
 */
export function releaseInterface(deviceName, interfaceType, interfaceNumber) {
    if (!window.usedInterfaces[deviceName]) return;
    
    const key = `${interfaceType}${interfaceNumber}`;
    const index = window.usedInterfaces[deviceName].indexOf(key);
    if (index > -1) {
        window.usedInterfaces[deviceName].splice(index, 1);
    }
}

/**
 * Reconstruye completamente el cache desde las conexiones existentes
 * Útil al importar topologías o después de operaciones masivas
 */
export function rebuildInterfaceCache() {
    console.log('Rebuilding interface cache from topology...');
    window.usedInterfaces = scanUsedInterfaces();
    console.log('Cache rebuilt:', window.usedInterfaces);
}

/**
 * Actualiza la lista de interfaces de origen en el formulario
 */
export function updateFromInterfaceList() {
    const typeSelect = document.getElementById('conn-from-type');
    const interfaceSelect = document.getElementById('conn-from-number');
    const selectedType = typeSelect.value;
    
    interfaceSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    const interfaces = window.interfaceData[selectedType] || [];
    const typeName = window.interfaceTypeNames[selectedType] || '';
    
    interfaces.forEach(ifaceNumber => {
        const option = document.createElement('option');
        option.value = ifaceNumber;
        option.textContent = typeName + ifaceNumber;
        interfaceSelect.appendChild(option);
    });
}

window.getNextAvailableInterface = getNextAvailableInterface;
window.releaseInterface = releaseInterface;
window.updateFromInterfaceList = updateFromInterfaceList;
window.scanUsedInterfaces = scanUsedInterfaces;
window.rebuildInterfaceCache = rebuildInterfaceCache;

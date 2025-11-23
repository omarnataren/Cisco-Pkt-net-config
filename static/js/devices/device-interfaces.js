// ✅ Importaciones optimizadas - sin importar constantes, se usan desde window

/**
 * Obtiene la siguiente interfaz disponible para un dispositivo
 * @param {string} deviceName - Nombre del dispositivo
 * @param {string} deviceType - Tipo de dispositivo (router, switch, switch_core, computer)
 * @param {string} model - Modelo del dispositivo (opcional, para modo físico)
 * @returns {object|null} - {type, number} o null si no hay disponibles
 */
export function getNextAvailableInterface(deviceName, deviceType, model = null) {
    // Inicializar rastreador si no existe
    if (!window.usedInterfaces[deviceName]) {
        window.usedInterfaces[deviceName] = [];
    }
    
    // Obtener las interfaces según el modo (físico o digital)
    let interfaceOrder;
    
    if (window.deviceMode === 'physical' && model) {
        // Modo físico: usar interfaces del modelo específico
        interfaceOrder = window.getDeviceInterfaces(deviceType, model);
    } else {
        // Modo digital: usar interfaces genéricas
        if (deviceType === 'router') {
            interfaceOrder = window.ROUTER_INTERFACE_ORDER;
        } else if (deviceType === 'switch') {
            interfaceOrder = window.SWITCH_INTERFACE_ORDER;
        } else if (deviceType === 'switch_core') {
            interfaceOrder = window.SWITCH_CORE_INTERFACE_ORDER;
        } else {
            return null;
        }
    }
    
    // Buscar la siguiente interfaz disponible
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
 * Actualiza la lista de interfaces de origen
 */
export function updateFromInterfaceList() {
    const typeSelect = document.getElementById('conn-from-type');
    const interfaceSelect = document.getElementById('conn-from-number');
    const selectedType = typeSelect.value;
    
    // Limpiar opciones previas
    interfaceSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    // Agregar interfases del tipo seleccionado
    const interfaces = window.interfaceData[selectedType] || [];
    const typeName = window.interfaceTypeNames[selectedType] || '';
    
    interfaces.forEach(ifaceNumber => {
        const option = document.createElement('option');
        option.value = ifaceNumber;  // Solo el número (ej: "0/1")
        option.textContent = typeName + ifaceNumber;  // Para mostrar (ej: "FastEthernet0/1")
        interfaceSelect.appendChild(option);
    });
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.getNextAvailableInterface = getNextAvailableInterface;
window.releaseInterface = releaseInterface;
window.updateFromInterfaceList = updateFromInterfaceList;

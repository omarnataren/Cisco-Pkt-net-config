// ✅ Importaciones optimizadas - sin importar constantes, se usan desde window

/**
 * Obtiene la siguiente interfaz disponible para un dispositivo
 * @param {string} deviceName - Nombre del dispositivo
 * @param {string} deviceType - Tipo de dispositivo (router, switch, switch_core, computer)
 * @returns {object|null} - {type, number} o null si no hay disponibles
 */
export function getNextAvailableInterface(deviceName, deviceType) {

    // Buscar el nodo real por nombre
    const nodeList = window.nodes.get({
        filter: n => n.data.name === deviceName
    });

    if (!nodeList.length) {
        console.error("No se encontró el dispositivo:", deviceName);
        return null;
    }

    const node = nodeList[0];

    // Determinar el orden de interfaces según el tipo de dispositivo
    let interfaceOrder;

    if (deviceType === 'router') {
        interfaceOrder = window.ROUTER_INTERFACE_ORDER;
    } 
    else if (deviceType === 'switch') {
        interfaceOrder = window.SWITCH_INTERFACE_ORDER;
    } 
    else if (deviceType === 'switch_core') {
        interfaceOrder = window.SWITCH_CORE_INTERFACE_ORDER;
    } 
    else {
        console.warn("Dispositivo no soportado en auto-asignación:", deviceType);
        return null;
    }

    // Recorrer todas las interfaces posibles en orden
    for (let iface of interfaceOrder) {

        // Crear string completo (ej: "FastEthernet0/1")
        const fullPortString = `${iface.type}${iface.number}`;

        // Usar tu función global NUEVA a prueba de errores
        const inUse = window.isPortInUseCorrect(node.id, fullPortString);

        // Si NO está en uso, devolverlo
        if (!inUse) {
            return {
                type: iface.type,
                number: iface.number
            };
        }
    }

    console.error(`No hay interfaces disponibles para ${deviceType} ${deviceName}`);
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

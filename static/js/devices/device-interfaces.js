// ✅ Importaciones optimizadas - sin importar constantes, se usan desde window

/**
 * Obtiene la siguiente interfaz disponible para un dispositivo
 * @param {string} deviceName - Nombre del dispositivo
 * @param {string} deviceType - Tipo de dispositivo (router, switch, switch_core, computer)
 * @returns {object|null} - {type, number} o null si no hay disponibles
 */
export function getNextAvailableInterface(deviceName, deviceType) {
    // Inicializar rastreador si no existe
    if (!window.usedInterfaces[deviceName]) {
        window.usedInterfaces[deviceName] = [];
    }
    
    if (deviceType === 'router') {
        // Para routers, seguir el orden estricto
        for (let iface of window.ROUTER_INTERFACE_ORDER) {
            const key = `${iface.type}${iface.number}`;
            if (!window.usedInterfaces[deviceName].includes(key)) {
                window.usedInterfaces[deviceName].push(key);
                return { type: iface.type, number: iface.number };
            }
        }
        console.error(`No hay más interfaces disponibles para el router ${deviceName}`);
        return null;
    }
    
    if (deviceType === 'switch') {
        // Para switches, seguir el orden: FastEthernet 0/1-24, luego GigabitEthernet 0/1-2
        for (let iface of window.SWITCH_INTERFACE_ORDER) {
            const key = `${iface.type}${iface.number}`;
            if (!window.usedInterfaces[deviceName].includes(key)) {
                window.usedInterfaces[deviceName].push(key);
                return { type: iface.type, number: iface.number };
            }
        }
        console.error(`No hay más interfaces disponibles para el switch ${deviceName}`);
        return null;
    }

    if (deviceType === 'switch_core') {
        // Para switches core, seguir el orden: GigabitEthernet 1/0/1-1/0/24, luego GigabitEthernet 1/1/1-1/1/4
        for (let iface of window.SWITCH_CORE_INTERFACE_ORDER) {
            const key = `${iface.type}${iface.number}`;
            if (!window.usedInterfaces[deviceName].includes(key)) {
                window.usedInterfaces[deviceName].push(key);
                return { type: iface.type, number: iface.number };
            }
        }
        console.error(`No hay más interfaces disponibles para el switch core ${deviceName}`);
        return null;
    }
    
    // Para otros dispositivos, mantener lógica existente
    return null; // Se asignarán manualmente por ahora
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

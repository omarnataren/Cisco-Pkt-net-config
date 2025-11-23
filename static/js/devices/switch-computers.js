// ✅ Importaciones optimizadas
import { showNotification } from '../ui/notification.js';

// Variable de módulo (no exportada, uso interno del modal)
let currentSwitchForComputers = null;

/**
 * Establece el switch actual para gestión de computadoras
 * @param {object} switchNode - Nodo del switch seleccionado
 */
export function setCurrentSwitchForComputers(switchNode) {
    currentSwitchForComputers = switchNode;
}

/**
 * Obtiene el switch actual
 * @returns {object|null} - Nodo del switch actual o null
 */
export function getCurrentSwitchForComputers() {
    return currentSwitchForComputers;
}

// Actualizar lista de computadoras en el modal
export function updateComputersList() {
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

/**
 * Asigna automáticamente la siguiente interfaz disponible del switch
 * Usa el sistema unificado de detección de interfaces
 * @returns {object} - {portType, portNumber} o null si no hay disponibles
 */
function getNextAvailablePortForComputer() {
    const switchNode = currentSwitchForComputers;
    if (!switchNode) return null;
    
    // Usar el sistema unificado de detección
    const usedInterfaces = window.scanUsedInterfaces(switchNode.data.name);
    
    const switchType = switchNode.data.type;
    let interfaceOrder;
    
    if (switchType === 'switch') {
        interfaceOrder = window.SWITCH_INTERFACE_ORDER;
    } else if (switchType === 'switch_core') {
        interfaceOrder = window.SWITCH_CORE_INTERFACE_ORDER;
    } else {
        return null;
    }
    
    for (let iface of interfaceOrder) {
        const key = `${iface.type}${iface.number}`;
        if (!usedInterfaces.includes(key)) {
            return {
                portType: iface.type,
                portNumber: iface.number
            };
        }
    }
    
    return null;
}

// Guardar nueva computadora desde modal (modificado: auto-asignación de puerto)
export function saveNewComputer() {
    const name = document.getElementById('new-pc-name').value.trim();
    const vlan = document.getElementById('new-pc-vlan').value;
    
    console.log('Datos de nueva PC:', { name, vlan });
    
    if (!name) {
        showNotification('Ingresa el nombre de la PC', 'error');
        return;
    }
    
    if (!vlan) {
        showNotification('Selecciona una VLAN', 'error');
        return;
    }
    
    const availablePort = getNextAvailablePortForComputer();
    if (!availablePort) {
        showNotification('No hay puertos disponibles en el switch', 'error');
        return;
    }
    
    if (!currentSwitchForComputers.data.computers) {
        currentSwitchForComputers.data.computers = [];
    }
    
    currentSwitchForComputers.data.computers.push({
        name: name,
        portType: availablePort.portType,
        portNumber: availablePort.portNumber,
        vlan: vlan
    });
    
    console.log('Computadora agregada:', currentSwitchForComputers.data.computers);
    
    // Actualizar cache de interfaces usado
    if (!window.usedInterfaces[currentSwitchForComputers.data.name]) {
        window.usedInterfaces[currentSwitchForComputers.data.name] = [];
    }
    const portKey = `${availablePort.portType}${availablePort.portNumber}`;
    if (!window.usedInterfaces[currentSwitchForComputers.data.name].includes(portKey)) {
        window.usedInterfaces[currentSwitchForComputers.data.name].push(portKey);
    }
    
    window.nodes.update(currentSwitchForComputers);
    updateComputersList();
    closeAddComputerModal();
    showNotification(`Computadora ${name} agregada en ${availablePort.portType}${availablePort.portNumber}`);
}

// Eliminar computadora (modificado: actualizar cache)
export function removeComputer(index) {
    if (confirm('¿Eliminar esta computadora?')) {
        const removedPc = currentSwitchForComputers.data.computers[index];
        currentSwitchForComputers.data.computers.splice(index, 1);
        
        // Actualizar cache de interfaces
        if (window.usedInterfaces[currentSwitchForComputers.data.name]) {
            const portKey = `${removedPc.portType}${removedPc.portNumber}`;
            const idx = window.usedInterfaces[currentSwitchForComputers.data.name].indexOf(portKey);
            if (idx > -1) {
                window.usedInterfaces[currentSwitchForComputers.data.name].splice(idx, 1);
            }
        }
        
        window.nodes.update(currentSwitchForComputers);
        updateComputersList();
        showNotification('Computadora eliminada');
    }
}

// Exponer funciones globalmente para compatibilidad con HTML onclick
window.updateComputersList = updateComputersList;
window.removeComputer = removeComputer;
window.saveNewComputer = saveNewComputer;
window.setCurrentSwitchForComputers = setCurrentSwitchForComputers;
window.getCurrentSwitchForComputers = getCurrentSwitchForComputers;
// ✅ Importaciones optimizadas
import { nodes } from '../core/network-state.js';
import { interfaceData, interfaceTypeNames } from '../core/network-constants.js';
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

// Guardar nueva computadora desde modal
export function saveNewComputer() {
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

// Eliminar computadora
export function removeComputer(index) {
    if (confirm('¿Eliminar esta computadora?')) {
        currentSwitchForComputers.data.computers.splice(index, 1);
        nodes.update(currentSwitchForComputers);
        updateComputersList();
        showNotification('Computadora eliminada');
    }
}

//Actualiza la lista de puertos disponibles para agregar PCs
export function updateNewPcPortList() {
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

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.updateComputersList = updateComputersList;
window.removeComputer = removeComputer;
window.saveNewComputer = saveNewComputer;
window.updateNewPcPortList = updateNewPcPortList;
window.setCurrentSwitchForComputers = setCurrentSwitchForComputers;
window.getCurrentSwitchForComputers = getCurrentSwitchForComputers;
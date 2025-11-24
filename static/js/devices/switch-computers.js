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


// Actualizar select de VLANs para computadoras
export function updateComputerVlanSelect() {
    const select = document.getElementById('new-pc-vlan');
    select.innerHTML = '<option value="">-- Selecciona VLAN --</option>';

    window.vlans.forEach(vlan => {
        const option = document.createElement('option');
        option.value = vlan.name;
        option.textContent = `${vlan.name} (/${vlan.prefix})`;
        select.appendChild(option);
    });
}

// Asignar automáticamente el puerto al seleccionar una VLAN
window.autoAssignPort = function() {
    const vlanName = document.getElementById('new-pc-vlan').value;
    const portInput = document.getElementById('new-pc-port');

    if (!vlanName) {
        portInput.value = "";
        return;
    }

    const computers = currentSwitchForComputers.data.computers || [];

    // Filtrar las computadoras de la misma VLAN
    const vlanComputers = computers.filter(pc => pc.vlan === vlanName);

    // Asignar el siguiente puerto disponible
    const nextPortNumber = vlanComputers.length + 1;
    portInput.value = `FastEthernet0/${nextPortNumber}`;
};

export function updatePortPreview() {

    const vlan = document.getElementById('new-pc-vlan').value;
    const preview = document.getElementById('new-pc-port-preview');

    if (!vlan) {
        preview.value = "";
        return;
    }

    let index = 1;
    let candidate;

    // Intentar desde FastEthernet0/1, 0/2, 0/3, ...
    while (true) {
        candidate = `FastEthernet0/${index}`;

        const used = window.isPortInUseCorrect(currentSwitchForComputers.id, candidate);

        if (!used) {
            preview.value = candidate;
            break;
        }

        index++;
    }
}


// Guardar nueva computadora desde modal
export function saveNewComputer() {
    const name = document.getElementById('new-pc-name').value.trim();
    const vlan = document.getElementById('new-pc-vlan').value;

    if (!name) {
        showNotification('Ingresa el nombre de la PC', 'error');
        return;
    }

    if (!vlan) {
        showNotification('Selecciona una VLAN', 'error');
        return;
    }

    // 1. Asegurarse de que exista el arreglo de computadoras
    if (!currentSwitchForComputers.data.computers) {
        currentSwitchForComputers.data.computers = [];
    }

    // Antes de guardar
const previewPort = document.getElementById('new-pc-port-preview').value;


    // 2. Buscar el primer puerto FastEthernet disponible (REAL)
    let index = 1;
    let port;

    while (true) {
        const candidate = `FastEthernet0/${index}`;

        // Validar puerto contra TODA la topología
        const used = window.isPortInUseCorrect(currentSwitchForComputers.id, candidate);

        if (!used) {
            port = candidate;
            break;
        }

        index++;
    }

    // 3. Agregar la computadora
    currentSwitchForComputers.data.computers.push({
        name: name,
        portType: "FastEthernet",
        portNumber: previewPort,
        vlan: vlan
    });

    window.nodes.update(currentSwitchForComputers);
    updateComputersList();
    closeAddComputerModal();
    showNotification(`Computadora ${name} agregada con el puerto ${port}`);
}

// Eliminar computadora
export function removeComputer(index) {
    if (confirm('¿Eliminar esta computadora?')) {
        currentSwitchForComputers.data.computers.splice(index, 1);
        window.nodes.update(currentSwitchForComputers);
        updateComputersList();
        showNotification('Computadora eliminada');
    }
}

// //Actualiza la lista de puertos disponibles para agregar PCs
// export function updateNewPcPortList() {
//     const typeSelect = document.getElementById('new-pc-port-type');
//     const portSelect = document.getElementById('new-pc-port-number');
//     const selectedType = typeSelect.value;
    
//     // Limpiar opciones previas
//     portSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
//     // Agregar interfaces del tipo seleccionado
//     const interfaces = window.interfaceData[selectedType] || [];
//     const typeName = window.interfaceTypeNames[selectedType] || '';
    
//     interfaces.forEach(ifaceNumber => {
//         const option = document.createElement('option');
//         option.value = ifaceNumber;  // ✅ Solo el número (ej: "0/1" o "1/0/1")
//         option.textContent = typeName + ifaceNumber;  // Para mostrar (ej: "FastEthernet0/1" o "GigabitEthernet1/0/1")
//         portSelect.appendChild(option);
//     });
// }

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.updateComputersList = updateComputersList;
window.removeComputer = removeComputer;
window.saveNewComputer = saveNewComputer;
window.updateComputerVlanSelect = updateComputerVlanSelect;
window.updatePortPreview = updatePortPreview;
// window.updateNewPcPortList = updateNewPcPortList;
window.setCurrentSwitchForComputers = setCurrentSwitchForComputers;
window.getCurrentSwitchForComputers = getCurrentSwitchForComputers;
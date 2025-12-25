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
    // Fondo gris claro (#f0f0f0) y texto oscuro para contraste
    item.style.cssText = 'background: #f0f0f0; padding: 12px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #d0d7de;';
    item.innerHTML = `
        <div>
            <div style="color: #0969da; font-weight: bold; margin-bottom: 4px;">${pc.name}</div>
            <div style="color: #57606a; font-size: 11px;">Puerto: ${pc.portNumber} • VLAN: ${pc.vlan}</div>
        </div>
        <button onclick="removeComputer(${index})" style="background: #cf222e; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 5px;">
            <img src="/static/assets/icons/eliminar.png" style="width: 14px; height: 14px;"> Eliminar
        </button>
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

/**
 * Actualiza la vista previa del puerto que se asignará
 * Considera modo físico y modelo del switch
 */
export function updatePortPreview() {

    const vlan = document.getElementById('new-pc-vlan').value;
    const preview = document.getElementById('new-pc-port-preview');

    if (!vlan) {
        preview.value = "";
        return;
    }

    if (!currentSwitchForComputers) {
        preview.value = "";
        return;
    }

    // Obtener interfaces disponibles según modo y modelo
    let interfaceOrder;
    const switchType = currentSwitchForComputers.data.type;
    const switchModel = currentSwitchForComputers.data.model;

    if (window.deviceMode === 'physical' && switchModel) {
        // Modo físico: usar interfaces del modelo específico
        interfaceOrder = window.getDeviceInterfaces(switchType, switchModel);
    } else {
        // Modo digital: usar interfaces genéricas
        if (switchType === 'switch') {
            interfaceOrder = window.SWITCH_INTERFACE_ORDER;
        } else if (switchType === 'switch_core') {
            interfaceOrder = window.SWITCH_CORE_INTERFACE_ORDER;
        } else {
            preview.value = "";
            return;
        }
    }

    // Buscar el primer puerto disponible
    for (let iface of interfaceOrder) {
        const candidate = `${iface.type}${iface.number}`;
        const used = window.isPortInUseCorrect(currentSwitchForComputers.id, candidate);

        if (!used) {
            preview.value = candidate;
            return;
        }
    }

    preview.value = "Sin puertos disponibles";
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

    // 2. Obtener el puerto del preview
    const port = document.getElementById('new-pc-port-preview').value;

    if (!port || port === "Sin puertos disponibles") {
        showNotification('No hay puertos disponibles en el switch', 'error');
        return;
    }

    // 3. Agregar la computadora
    currentSwitchForComputers.data.computers.push({
        name: name,
        portNumber: port,  // Solo guardamos el string completo: "FastEthernet0/1"
        vlan: vlan
    });

    window.nodes.update(currentSwitchForComputers);
    updateComputersList();
    closeAddComputerModal();
    showNotification(`Computadora ${name} agregada en ${port}`);
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
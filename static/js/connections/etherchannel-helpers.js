// ✅ Importaciones optimizadas
import { showNotification } from '../ui/notification.js';

/**
 * Alterna entre campos de conexión normal y EtherChannel en modal de edición
 * Valida que ambos extremos sean switches antes de permitir EtherChannel
 */
export function toggleEtherChannelFields() {
    const connectionType = document.getElementById('edit-connection-type').value;
    const normalFields = document.getElementById('normal-connection-fields');
    const etherChannelFields = document.getElementById('etherchannel-fields');
    
    if (connectionType === 'etherchannel') {
        // Validar que ambos extremos sean switches
        const edge = window.edges.get(window.editingEdge);
        const fromNode = window.nodes.get(edge.from);
        const toNode = window.nodes.get(edge.to);
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
 * Actualiza la lista de interfaces de origen para EtherChannel
 */
function updateEtherChannelFromList() {
    const typeSelect = document.getElementById('new-etherchannel-from-type');
    const interfaceSelect = document.getElementById('new-etherchannel-from-range');
    const selectedType = typeSelect.value;
    
    // Limpiar opciones previas
    interfaceSelect.innerHTML = '<option value="">Seleccionar interfaz...</option>';
    
    // Agregar interfases del tipo seleccionado
    const interfaces = window.interfaceData[selectedType] || [];
    const typeName = window.interfaceTypeNames[selectedType] || '';
    
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
    const interfaces = window.interfaceData[selectedType] || [];
    const typeName = window.interfaceTypeNames[selectedType] || '';
    
    interfaces.forEach(ifaceNumber => {
        const option = document.createElement('option');
        option.value = ifaceNumber;  // ✅ Solo el número (ej: "0/1")
        option.textContent = typeName + ifaceNumber;  // Para mostrar (ej: "FastEthernet0/1")
        interfaceSelect.appendChild(option);
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
        if (window.firstNodeConnection) {
            const fromNode = window.nodes.get(window.firstNodeConnection);
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

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.toggleEtherChannelFields = toggleEtherChannelFields;
window.updateEtherChannelFromList = updateEtherChannelFromList;
window.updateEtherChannelToList = updateEtherChannelToList;
window.toggleNewConnectionFields = toggleNewConnectionFields;
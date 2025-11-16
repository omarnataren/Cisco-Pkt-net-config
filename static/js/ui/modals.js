// ✅ Importaciones optimizadas
import { nodes, selectedNode, vlans, edges, selectedEdge, editingEdge, firstNodeConnection } from '../core/network-state.js';
import { interfaceTypeAbbr } from '../core/network-constants.js';
import { showNotification } from './notification.js';
import { 
    setCurrentSwitchForComputers, 
    getCurrentSwitchForComputers,
    updateComputersList,
    updateNewPcPortList
} from '../devices/switch-computers.js';

//---- Manejo de modal Manage Computers Modal ----
export function openManageComputersModal() {
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
    setCurrentSwitchForComputers(node);
    
    const switchName = node.data.name;
    document.getElementById('switch-computers-name').textContent = switchName;
    
    // Inicializar si no existe
    const currentSwitch = getCurrentSwitchForComputers();
    if (!currentSwitch.data.computers) {
        currentSwitch.data.computers = [];
    }
    
    updateComputersList();
    document.getElementById('manage-computers-modal').style.display = 'block';
}

// Cerrar el modal de manejo de computadoras
export function closeManageComputersModal() {
    document.getElementById('manage-computers-modal').style.display = 'none';
}

//--- Manejo del Modal Edit Connection Modal ---
// Abrir modal para editar conexión
export function openEditConnectionModal() {
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

// Cerrar modal de edición
export function closeEditConnectionModal() {
    document.getElementById('edit-connection-modal').style.display = 'none';
    editingEdge = null;
}

//--- Manejo del Modal Add Computer Modal ---
//Abrir modal
export function openAddComputerModal() {
    console.log('openAddComputerModal llamada');
    const currentSwitch = getCurrentSwitchForComputers();
    console.log('currentSwitch:', currentSwitch);
    
    // Generar nombre automático
    const existingComputers = currentSwitch.data.computers || [];
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

//Cerrar modal
export function closeAddComputerModal() {
    document.getElementById('add-computer-modal').style.display = 'none';
}

//---- Manejo del Modal Connection Modal ----

// Cerrar modal de conexión
export function closeConnectionModal() {
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

//--- Cerrar modales al hacer clic fuera del contenido ---
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

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.openManageComputersModal = openManageComputersModal;
window.closeManageComputersModal = closeManageComputersModal;
window.openAddComputerModal = openAddComputerModal;
window.closeAddComputerModal = closeAddComputerModal;

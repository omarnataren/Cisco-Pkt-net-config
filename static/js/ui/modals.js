// ✅ Importaciones optimizadas
import { showNotification } from './notification.js';
import { 
    setCurrentSwitchForComputers, 
    getCurrentSwitchForComputers,
    updateComputersList,
    updatePortPreview,

} from '../devices/switch-computers.js';

//---- Manejo de modal Manage Computers Modal ----
export function openManageComputersModal() {
    console.log('openManageComputersModal - window.selectedNode:', window.selectedNode);
    
    if (!window.selectedNode) {
    showNotification('Selecciona un switch primero', 'error');
    return;
    }
    
    // Obtener el nodo completo desde la colección
    let node;
    if (typeof window.selectedNode === 'string') {
        // Si window.selectedNode es un ID string, obtener el nodo completo
        node = window.nodes.get(window.selectedNode);
    } else if (window.selectedNode.id) {
        // Si window.selectedNode tiene id, obtener el nodo completo
        node = window.nodes.get(window.selectedNode.id);
    } else {
        // Si window.selectedNode ya es el objeto completo
        node = window.selectedNode;
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
    if (!window.selectedEdge) return;
    
    const edge = window.edges.get(window.selectedEdge);
    window.editingEdge = window.selectedEdge;
    
    const isEtherChannel = edge.data.etherChannel || edge.data.connectionType === 'etherchannel';
    
    document.getElementById('edit-connection-type').value = isEtherChannel ? 'etherchannel' : 'normal';
    
            if (isEtherChannel) {
        // Cargar datos de EtherChannel
        document.getElementById('etherchannel-protocol').value = edge.data.etherChannel.protocol || 'lacp';
        document.getElementById('etherchannel-group').value = edge.data.etherChannel.group || 1;
        const ecFromType = edge.data.etherChannel.fromType || 'FastEthernet';
        const ecToType = edge.data.etherChannel.toType || 'FastEthernet';
        document.getElementById('etherchannel-from-type').value = window.interfaceTypeAbbr[ecFromType] || 'fa';
        document.getElementById('etherchannel-from-range').value = edge.data.etherChannel.fromRange || '';
        document.getElementById('etherchannel-to-type').value = window.interfaceTypeAbbr[ecToType] || 'fa';
        document.getElementById('etherchannel-to-range').value = edge.data.etherChannel.toRange || '';
    } else {
    // Cargar datos de conexión normal
        const fromType = edge.data.fromInterface.type;
        const toType = edge.data.toInterface.type;
        document.getElementById('edit-from-type').value = window.interfaceTypeAbbr[fromType] || 'fa';
        document.getElementById('edit-from-number').value = edge.data.fromInterface.number;
        document.getElementById('edit-to-type').value = window.interfaceTypeAbbr[toType] || 'fa';
        document.getElementById('edit-to-number').value = edge.data.toInterface.number;
    }
    
    toggleEtherChannelFields();
    document.getElementById('edit-connection-modal').style.display = 'block';
}

// Cerrar modal de edición
export function closeEditConnectionModal() {
    document.getElementById('edit-connection-modal').style.display = 'none';
    window.editingEdge = null;
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
    
    if (window.vlans.length === 0) {
        showNotification('No hay VLANs creadas. Crea VLANs primero.', 'error');
        return;
    }
    
    console.log('VLANs encontradas:', window.vlans.length);
    
    // Usar directamente el array window.vlans, no parsear el HTML
    for (let i = 0; i < window.vlans.length; i++) {
        const vlanName = window.vlans[i].name; // Solo el nombre, sin el prefijo
        const option = document.createElement('option');
        option.value = vlanName;
        option.textContent = vlanName;
        vlanSelect.appendChild(option);
    }
    
    // // Inicializar lista de puertos
    // updateNewPcPortList();
    updatePortPreview();
    
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
    
    window.firstNodeConnection = null;
    window.connectionMode = false;
    document.getElementById('connect-btn').classList.remove('active');
    
    // Reactivar arrastre cuando se cierra el modal
    if (window.network) {
        window.network.setOptions({
            interaction: { dragNodes: true }
        });
    }
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
            window.firstNodeConnection = null;
            window.connectionMode = false;
            document.getElementById('connect-btn').classList.remove('active');
            // Reactivar arrastre
            if (window.network) {
                window.network.setOptions({
                    interaction: { dragNodes: true }
                });
            }
        }
    }
    });
};

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.openManageComputersModal = openManageComputersModal;
window.closeManageComputersModal = closeManageComputersModal;
window.openAddComputerModal = openAddComputerModal;
window.closeAddComputerModal = closeAddComputerModal;
window.closeConnectionModal = closeConnectionModal;

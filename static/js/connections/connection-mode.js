// Modo de conexión con toggle
export function toggleConnectionMode() {
    window.connectionMode = !window.connectionMode;
    window.firstNodeConnection = null;
    
    // Actualizar opción de arrastre en la red
    if (window.network) {
        window.network.setOptions({
            interaction: { dragNodes: !window.connectionMode }
        });
    }
    
    const btn = document.getElementById('connect-btn');
    if (window.connectionMode) {
        btn.classList.add('active');
        window.showNotification('Modo conexión activado. Haz clic en dos dispositivos');
    } else {
        btn.classList.remove('active');
        window.showNotification('Modo conexión desactivado');
    }
}

// Mantener compatibilidad
export function enableConnectionMode() {
    if (!window.connectionMode) {
        toggleConnectionMode();
    }
}

// Manejar clic para conexión
export function handleConnectionClick(nodeId) {
    if (!window.firstNodeConnection) {
        window.firstNodeConnection = nodeId;
        const node = window.nodes.get(nodeId);
        window.showNotification('Seleccionado: ' + node.data.name + '. Ahora selecciona el destino');
    } else {
        if (window.firstNodeConnection === nodeId) {
            window.showNotification('No puedes conectar un dispositivo consigo mismo', 'error');
            window.firstNodeConnection = null;
            return;
        }
        // Abrir modal para configurar conexión
        const fromNode = window.nodes.get(window.firstNodeConnection);
        const toNode = window.nodes.get(nodeId);

        // Auto-asignar interfaces para routers y switches
        let fromInterface = null;
        let toInterface = null;
        
        // Asignar interfaz para el nodo origen (router, switch o switch_core)
        if (fromNode.data.type === 'router' || fromNode.data.type === 'switch' || fromNode.data.type === 'switch_core') {
            fromInterface = window.getNextAvailableInterface(fromNode.data.name, fromNode.data.type);
            if (!fromInterface) {
                window.showNotification(`No hay interfaces disponibles en ${fromNode.data.name}`, 'error');
                window.firstNodeConnection = null;
                return;
            }
        }
        // Asignar interfaz para el nodo destino (router, switch o switch_core)
        if (toNode.data.type === 'router' || toNode.data.type === 'switch' || toNode.data.type === 'switch_core') {
            toInterface = window.getNextAvailableInterface(toNode.data.name, toNode.data.type);
            if (!toInterface) {
                // Liberar la interfaz del origen si ya se asignó
                if (fromInterface) {
                    window.releaseInterface(fromNode.data.name, fromInterface.type, fromInterface.number);
                }
                window.showNotification(`No hay interfaces disponibles en ${toNode.data.name}`, 'error');
                window.firstNodeConnection = null;
                return;
            }
        }
        // Resetear el modal a valores por defecto
        document.getElementById('new-connection-type').value = 'normal';
        // Función helper para mapear tipo de interfaz a valor del select
        function getInterfaceTypeSelectValue(interfaceType) {
            if (interfaceType === 'FastEthernet') return 'fa';
            if (interfaceType === 'GigabitEthernet') return 'gi';
            if (interfaceType === 'Ethernet') return 'eth';
            return 'fa'; // default
        }
        // Si hay al menos un dispositivo con interfaz asignada, configurar el modal
        if (fromInterface || toInterface) {
            // Configurar interfaz FROM
            if (fromInterface) {
                document.getElementById('conn-from-type').value = getInterfaceTypeSelectValue(fromInterface.type);
                document.getElementById('conn-from-number').value = fromInterface.number;
                document.getElementById('conn-from-type').disabled = true;
                document.getElementById('conn-from-number').disabled = true;
                document.getElementById('conn-from-auto-notice').style.display = 'block';
            } else {
                document.getElementById('conn-from-type').value = 'fa';
                document.getElementById('conn-from-number').value = '0/0';
                document.getElementById('conn-from-type').disabled = false;
                document.getElementById('conn-from-number').disabled = false;
                document.getElementById('conn-from-auto-notice').style.display = 'none';
            }
            
            // Configurar interfaz TO
            if (toInterface) {
                document.getElementById('conn-to-type').value = getInterfaceTypeSelectValue(toInterface.type);
                document.getElementById('conn-to-number').value = toInterface.number;
                document.getElementById('conn-to-type').disabled = true;
                document.getElementById('conn-to-number').disabled = true;
                document.getElementById('conn-to-auto-notice').style.display = 'block';
            } else {
                document.getElementById('conn-to-type').value = 'fa';
                document.getElementById('conn-to-number').value = '0/0';
                document.getElementById('conn-to-type').disabled = false;
                document.getElementById('conn-to-number').disabled = false;
                document.getElementById('conn-to-auto-notice').style.display = 'none';
            }
            
            // Guardar en el modal para referencia
            document.getElementById('connection-modal').dataset.fromInterface = fromInterface ? JSON.stringify(fromInterface) : '';
            document.getElementById('connection-modal').dataset.toInterface = toInterface ? JSON.stringify(toInterface) : '';
            document.getElementById('connection-modal').dataset.autoAssigned = 'partial';
        } else {
            // Conexión manual (ningún router involucrado)
            document.getElementById('conn-from-type').value = 'fa';
            document.getElementById('conn-from-number').value = '0/0';
            document.getElementById('conn-to-type').value = 'fa';
            document.getElementById('conn-to-number').value = '0/0';
            
            // Habilitar selects
            document.getElementById('conn-from-type').disabled = false;
            document.getElementById('conn-from-number').disabled = false;
            document.getElementById('conn-to-type').disabled = false;
            document.getElementById('conn-to-number').disabled = false;
            
            // Ocultar avisos
            document.getElementById('conn-from-auto-notice').style.display = 'none';
            document.getElementById('conn-to-auto-notice').style.display = 'none';
            
            document.getElementById('connection-modal').dataset.autoAssigned = 'false';
        }
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
        window.updateFromInterfaceList();
        document.getElementById('conn-from-name').textContent = fromNode.data.name;
        document.getElementById('conn-to-name').textContent = toNode.data.name;
        document.getElementById('conn-to-name-ec').textContent = toNode.data.name;
        document.getElementById('connection-modal').style.display = 'block';
    }
}

// Exportar funciones a window para compatibilidad con onclick en HTML
window.toggleConnectionMode = toggleConnectionMode;
window.enableConnectionMode = enableConnectionMode;
window.handleConnectionClick = handleConnectionClick;
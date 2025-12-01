// Agregar dispositivo
export function addDevice(type) {
    // Activar modo de posicionamiento
    window.devicePositioningMode = true;
    window.pendingDeviceType = type;
    
    // Deshabilitar arrastre mientras estamos posicionando
    if (window.network) {
        window.network.setOptions({
            interaction: { dragNodes: false }
        });
    }
    
    // Cambiar cursor y mostrar mensaje
    document.getElementById('network-canvas').style.cursor = 'cell';
    window.showNotification(`Haz click en el área de trabajo para posicionar el dispositivo`, 'info');
    
    // Cambiar estilo del botón para indicar que está activo
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
if (btn.getAttribute('onclick') === `addDevice('${type}')`) {
    btn.classList.add('active');
}
    });
}


export function createDeviceAtPosition(x, y) {
    if (!window.devicePositioningMode || !window.pendingDeviceType) return;
    
   let name, shape, deviceType, image, color;
    const type = window.pendingDeviceType;
    
    switch(type) {
case 'router':
    name = 'R' + window.routerCounter++;
    image = '/static/assets/icons/router.png';
    shape = 'image'; 
    deviceType = 'router';
    break;
case 'switch':
    name = 'SW' + window.switchCounter++;
     image = '/static/assets/icons/switch.png';
    shape = 'image'; 
    deviceType = 'switch';
    break;
case 'switch_core':
    name = 'SWC' + window.switchCoreCounter++;
    image = '/static/assets/icons/switch-core.png';
    shape = 'image';
    deviceType = 'switch_core';
    break;
case 'computer':
    name = 'PC' + window.computerCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'circle';
    deviceType = 'computer';
    break;
case 'wlc':
    name = 'WLC' + window.wlcCounter++;
    image = '/static/assets/icons/WLC.png';
    shape = 'image'; 
    deviceType = 'wlc';
    break;
case 'server':
    name = 'S' + window.serverCounter++;
    image = '/static/assets/icons/server.png';
    shape = 'image'; 
    deviceType = 'server';
    break;
case 'ap':
    name = 'AP' + window.apCounter++;
     image = '/static/assets/icons/accespoint.png';
    shape = 'image'; 
    deviceType = 'ap';
    break;
    }
    
    const id = deviceType + '_' + Date.now();
    
    // Crear datos del dispositivo
    const deviceData = {
        type: deviceType,
        name: name,
        connections: [],
        vlan: null  // Para computadoras
    };
    
    // Si estamos en modo físico, necesitamos pedir el modelo
    if (window.deviceMode === 'physical' && (deviceType === 'router' || deviceType === 'switch' || deviceType === 'switch_core')) {
        // Mostrar modal para seleccionar modelo
        showModelSelectionModal(id, name, shape, x, y, image, deviceData);
        return;
    }
    
    // Crear objeto de configuración del nodo
    const nodeConfig = {
        id: id,
        label: name,
        title: name,
        shape: shape,
        size: 30,
        x: x,  // Coordenada X exacta posicionada por el usuario
        y: y,  // Coordenada Y exacta posicionada por el usuario - Se usarán en PTBuilder
        fixed: false,  // Permitir que el nodo sea arrastrable
        font: {
            color: '#000000',
            size: 11
        },
        data: deviceData
    };
    
    // Agregar imagen o color según el tipo
    if (image) {
        nodeConfig.image = image;
    } else if (color) {
        nodeConfig.color = color;
    }
    
    window.nodes.add(nodeConfig);
    
    finishDeviceCreation();
    window.showNotification(`${name} agregado exitosamente`, 'success');
}

/**
 * Muestra modal para seleccionar modelo físico del dispositivo
 */
function showModelSelectionModal(id, name, shape, x, y, image, deviceData) {
    const deviceType = deviceData.type;
    const models = window.getAvailableModels(deviceType);
    
    if (models.length === 0) {
        // No hay modelos, agregar sin modelo
        const nodeConfig = {
            id, label: name, title: name, shape, size: 30,
            x, y, fixed: false,
            font: { color: '#000000', size: 11 },
            data: deviceData
        };
        
        if (image) {
            nodeConfig.image = image;
        }
        
        window.nodes.add(nodeConfig);
        finishDeviceCreation();
        return;
    }
    
    // Crear modal dinámicamente
    const modal = document.createElement('div');
    modal.id = 'model-selection-modal';
    modal.className = 'modal';
    modal.style.display = 'block';
    
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Seleccionar Modelo - ${name}</h2>
            <div class="form-group">
                <label>Modelo:</label>
                <select id="model-select" class="form-control">
                    ${models.map(m => `<option value="${m.model}">${m.displayName}</option>`).join('')}
                </select>
            </div>
            <div class="button-group">
                <button class="btn btn-primary" onclick="window.confirmModelSelection()">Confirmar</button>
                <button class="btn btn-secondary" onclick="window.cancelModelSelection()">Cancelar</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Guardar datos temporales
    window.tempDeviceData = { id, name, shape, x, y, image, deviceData };
}

/**
 * Confirma la selección del modelo
 */
window.confirmModelSelection = function() {
    const modelSelect = document.getElementById('model-select');
    const selectedModel = modelSelect.value;
    
    const { id, name, shape, x, y, image, deviceData } = window.tempDeviceData;
    
    // Agregar modelo a los datos del dispositivo
    deviceData.model = selectedModel;
    
    // Actualizar el label para incluir el modelo
    const displayName = window.getDeviceDisplayName(deviceData.type, selectedModel);
    const label = `${name}\n(${selectedModel})`;
    
    // Crear objeto de configuración del nodo
    const nodeConfig = {
        id, 
        label, 
        title: displayName, 
        shape, 
        size: 30,
        x, y, 
        fixed: false, 
        font: { color: '#000000', size: 11 },
        data: deviceData
    };
    
    // Agregar imagen
    if (image) {
        nodeConfig.image = image;
    }
    
    window.nodes.add(nodeConfig);
    
    // Cerrar modal
    const modal = document.getElementById('model-selection-modal');
    modal.remove();
    
    window.tempDeviceData = null;
    finishDeviceCreation();
};

/**
 * Cancela la creación del dispositivo
 */
window.cancelModelSelection = function() {
    const modal = document.getElementById('model-selection-modal');
    modal.remove();
    window.tempDeviceData = null;
    finishDeviceCreation();
    window.showNotification('Creación de dispositivo cancelada', 'info');
};

/**
 * Finaliza el proceso de creación de dispositivo
 */
function finishDeviceCreation() {
    // Desactivar modo de posicionamiento
    window.devicePositioningMode = false;
    window.pendingDeviceType = null;
    document.getElementById('network-canvas').style.cursor = 'default';
    
    // Reactivar arrastre de nodos
    if (window.network) {
        window.network.setOptions({
            interaction: { dragNodes: true }
        });
    }
    
    // Remover clase active solo de botones de dispositivos (no de botones de modo)
    const buttons = document.querySelectorAll('.btn:not(.mode-btn)');
    buttons.forEach(btn => btn.classList.remove('active'));
}

// Exportar funciones a window para compatibilidad con onclick en HTML
window.addDevice = addDevice;
window.createDeviceAtPosition = createDeviceAtPosition;
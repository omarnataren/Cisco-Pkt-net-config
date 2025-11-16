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
    document.getElementById('network-canvas').style.cursor = 'crosshair';
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
    
    let name, color, shape, deviceType;
    const type = window.pendingDeviceType;
    
    switch(type) {
case 'router':
    name = 'R' + window.routerCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'circle';
    deviceType = 'router';
    break;
case 'switch':
    name = 'SW' + window.switchCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'box';
    deviceType = 'switch';
    break;
case 'switch_core':
    name = 'SWC' + window.switchCoreCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'box';
    deviceType = 'switch_core';
    break;
case 'computer':
    name = 'PC' + window.computerCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'circle';
    deviceType = 'computer';
    break;
    }
    
    const id = deviceType + '_' + Date.now();
    window.nodes.add({
id: id,
label: name,
title: name,
shape: shape,
size: 30,
x: x,  // Coordenada X exacta posicionada por el usuario
y: y,  // Coordenada Y exacta posicionada por el usuario - Se usarán en PTBuilder
fixed: false,  // Permitir que el nodo sea arrastrable
color: color,
font: {
    color: '#ffffff',
    size: 11
},
data: {
    type: deviceType,
    name: name,
    connections: [],
    vlan: null  // Para computadoras
}
    });
    
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
    
    // Remover clase active de todos los botones
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    window.showNotification(`${name} agregado exitosamente`, 'success');
}

// Exportar funciones a window para compatibilidad con onclick en HTML
window.addDevice = addDevice;
window.createDeviceAtPosition = createDeviceAtPosition;
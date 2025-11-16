// Agregar dispositivo
export function addDevice(type) {
    // Activar modo de posicionamiento
    devicePositioningMode = true;
    pendingDeviceType = type;
    
    // Cambiar cursor y mostrar mensaje
    document.getElementById('network-canvas').style.cursor = 'crosshair';
    showNotification(`Haz click en el área de trabajo para posicionar el dispositivo`, 'info');
    
    // Cambiar estilo del botón para indicar que está activo
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
if (btn.getAttribute('onclick') === `addDevice('${type}')`) {
    btn.classList.add('active');
}
    });
}


export function createDeviceAtPosition(x, y) {
    if (!devicePositioningMode || !pendingDeviceType) return;
    
    let name, color, shape, deviceType;
    const type = pendingDeviceType;
    
    switch(type) {
case 'router':
    name = 'R' + routerCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'circle';
    deviceType = 'router';
    break;
case 'switch':
    name = 'SW' + switchCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'box';
    deviceType = 'switch';
    break;
case 'switch_core':
    name = 'SWC' + switchCoreCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'box';
    deviceType = 'switch_core';
    break;
case 'computer':
    name = 'PC' + computerCounter++;
    color = { background: '#6e7681', border: '#8b949e' };
    shape = 'circle';
    deviceType = 'computer';
    break;
    }
    
    const id = deviceType + '_' + Date.now();
    nodes.add({
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
    devicePositioningMode = false;
    pendingDeviceType = null;
    document.getElementById('network-canvas').style.cursor = 'default';
    
    // Remover clase active de todos los botones
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    showNotification(`${name} agregado exitosamente`, 'success');
}
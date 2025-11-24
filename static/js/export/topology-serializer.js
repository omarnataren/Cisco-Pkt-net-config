
// Generar configuraciones
export function generateConfigurations() {
    if (window.nodes.length === 0) {
        window.showNotification('Agrega dispositivos primero', 'error');
        return;
    }
    
    // Verificar modo y ejecutar la función correspondiente
    if (window.deviceMode === 'physical') {
        // Modo físico: NO generar PT Builder
        generatePhysicalConfigurations();
    } else {
        // Modo digital: Generar con PT Builder (comportamiento original)
        generateDigitalConfigurations();
    }
}

/**
 * Genera configuraciones en modo digital (con PT Builder)
 */
function generateDigitalConfigurations() {
    // Obtener el valor del primer octeto de red base
    const baseOctet = document.getElementById('base-network-octet').value || '19';
    
    // Crear formulario y enviar datos a nueva pestaña
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/';
    form.target = '_blank';  // Abrir en nueva pestaña
    
    // Serializar datos
    const data = {
        nodes: window.nodes.get(),
        edges: window.edges.get(),
        vlans: window.vlans,
        baseNetworkOctet: parseInt(baseOctet)  // Agregar el primer octeto
    };
    
    // Verificar coordenadas antes de enviar
    console.log('📊 Coordenadas de dispositivos a enviar:');
    data.nodes.forEach(node => {
        console.log(`  ${node.data.name}: x=${Math.round(node.x)}, y=${Math.round(node.y)}`);
    });
    console.log(`🌐 Red base: ${baseOctet}.0.0.0/8`);
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'topology_data';
    input.value = JSON.stringify(data);
    
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    
    // Mostrar notificación
    window.showNotification('Generando configuraciones en nueva pestaña...');
    
    // Remover formulario después de enviar
    setTimeout(() => {
        document.body.removeChild(form);
    }, 100);
}

/**
 * Genera configuraciones en modo físico (sin PT Builder)
 */
async function generatePhysicalConfigurations() {
    // Validar topología física
    const topology = {
        nodes: window.nodes.get(),
        edges: window.edges.get(),
        vlans: window.vlans,
        baseNetworkOctet: parseInt(document.getElementById('base-network-octet').value || '19'),
        mode: 'physical'  // Indicar al backend que es modo físico
    };
    
    const validation = window.validatePhysicalTopology(topology);
    
    if (!validation.valid) {
        window.showNotification('Faltan modelos en algunos dispositivos', 'error');
        console.error('Errores de validación:', validation.errors);
        
        // Mostrar errores al usuario
        const errorList = validation.errors.join('\n');
        alert(`Errores encontrados:\n\n${errorList}\n\nAsegúrate de que todos los dispositivos tengan un modelo asignado.`);
        return;
    }
    
    // Crear formulario y enviar igual que en digital, pero con flag de modo físico
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/';
    form.target = '_blank';  // Abrir en nueva pestaña
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'topology_data';
    input.value = JSON.stringify(topology);
    
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    
    // Mostrar notificación
    window.showNotification('Generando configuraciones físicas en nueva pestaña...');
    
    // Remover formulario después de enviar
    setTimeout(() => {
        document.body.removeChild(form);
    }, 100);
}

// Exportar función a window para compatibilidad con onclick en HTML
window.generateConfigurations = generateConfigurations;

// Exportar función a window para compatibilidad con onclick en HTML
window.generateConfigurations = generateConfigurations;
// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.generateConfigurations = generateConfigurations;
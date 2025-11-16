
// Generar configuraciones
export function generateConfigurations() {
    if (nodes.length === 0) {
showNotification('Agrega dispositivos primero', 'error');
return;
    }
    
    // Obtener el valor del primer octeto de red base
    const baseOctet = document.getElementById('base-network-octet').value || '19';
    
    // Crear formulario y enviar datos a nueva pestaña
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/';
    form.target = '_blank';  // Abrir en nueva pestaña
    
    // Serializar datos
    const data = {
nodes: nodes.get(),
edges: edges.get(),
vlans: vlans,
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
    showNotification('Generando configuraciones en nueva pestaña...');
    
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
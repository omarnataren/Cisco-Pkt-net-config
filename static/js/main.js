// CAPA 1: CORE (Estado global y constantes - sin dependencias)
import './core/network-constants.js';
import './core/network-state.js';
import './core/physical-models.js';

// CAPA 2: UTILIDADES (Dependencias mínimas)
import './ui/notification.js';
import './devices/device-interfaces.js';
import './ui/zoom-controls.js';

// CAPA 3: LÓGICA DE NEGOCIO (Depende de CAPA 1 + 2)
import './core/selection-manager.js';
import './devices/device-editor.js';
import './devices/switch-computers.js';
import { addDevice, createDeviceAtPosition } from './devices/device-factory.js';
import './connections/etherchannel-helpers.js';
import './connections/routing-direction.js';
import './connections/connection-mode.js';
import './connections/connection-creator.js';
import './connections/connection-editor.js';
import './vlans/vlan-managment.js';

// CAPA 4: UI AVANZADA (Depende de todas las anteriores)
import './ui/property-panel.js';
import './ui/modals.js';

// CAPA 5: TOPOLOGÍA Y EXPORTACIÓN (Depende de todo)
import { initNetwork } from './topology/topology-renderer.js';
import './export/topology-serializer.js';
import './export/physical-config-generator.js';

// ✅ EXPORTAR FUNCIONES CRÍTICAS A WINDOW INMEDIATAMENTE
window.addDevice = addDevice;
window.createDeviceAtPosition = createDeviceAtPosition;
window.initNetwork = initNetwork;

// INICIALIZACIÓN
window.onload = function() {
    console.log('Inicializando aplicación...');
    console.log('window.addDevice disponible:', typeof window.addDevice);
    initNetwork();
    console.log('Aplicación inicializada correctamente');
};

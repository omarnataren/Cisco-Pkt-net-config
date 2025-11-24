// Estado global de la aplicación
// Todas las variables se definen en window para que sean accesibles globalmente
// y mutables desde cualquier módulo
window.network = null;
window.nodes = new vis.DataSet([]);
window.edges = new vis.DataSet([]);
window.vlans = [];
window.routerCounter = 1;
window.switchCounter = 1;
window.switchCoreCounter = 1;
window.computerCounter = 1;
window.wlcCounter = 1;
window.serverCounter = 1;
window.apCounter = 1;
window.connectionMode = false;
window.firstNodeConnection = null;
window.selectedNode = null;
window.selectedEdge = null;
window.editingEdge = null;
window.devicePositioningMode = false;
window.pendingDeviceType = null;
window.usedInterfaces = {};

// Constantes
window.MIN_ZOOM = 0.5;
window.MAX_ZOOM = 3.0;
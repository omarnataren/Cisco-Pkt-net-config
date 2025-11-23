/**
 * MÓDULO: physical-config-generator.js
 * DESCRIPCIÓN: Generador de configuraciones para modelos físicos de Cisco
 * Este módulo NO genera scripts PT Builder, solo configuraciones IOS
 */

/**
 * Genera configuraciones IOS para dispositivos físicos
 * @param {Object} topology - Datos de topología
 * @returns {Promise<Object>} Configuraciones generadas
 */
window.generatePhysicalConfigurations = async function(topology) {
    try {
        // Enviar topología al backend
        const response = await fetch('/generate_physical', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(topology)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error generando configuraciones físicas');
        }

        const result = await response.json();
        
        // Descargar archivos de configuración
        downloadPhysicalConfigurations(result.configs, topology);
        
        window.showNotification('Configuraciones físicas generadas exitosamente', 'success');
        return result;
        
    } catch (error) {
        console.error('Error generando configuraciones físicas:', error);
        window.showNotification(`Error: ${error.message}`, 'error');
        throw error;
    }
};

/**
 * Descarga las configuraciones en archivos separados
 * @param {Array} configs - Array de configuraciones de dispositivos
 * @param {Object} topology - Datos de topología
 */
function downloadPhysicalConfigurations(configs, topology) {
    // Crear un archivo por cada dispositivo
    configs.forEach(config => {
        const deviceName = config.name;
        const configText = config.config.join('\n');
        
        // Agregar comentario con información del modelo
        const device = findDeviceInTopology(topology, deviceName);
        let header = `!\n! Configuración para ${deviceName}\n`;
        
        if (device && device.data.model) {
            const displayName = window.getDeviceDisplayName(device.data.type, device.data.model);
            header += `! Modelo: ${displayName}\n`;
        }
        
        header += `! Generado: ${new Date().toLocaleString()}\n!\n\n`;
        
        const fullConfig = header + configText;
        
        // Descargar archivo
        const blob = new Blob([fullConfig], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${deviceName}_config.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
    
    // También crear un archivo consolidado
    const allConfigs = configs.map(config => {
        const device = findDeviceInTopology(topology, config.name);
        let section = `\n${'='.repeat(60)}\n`;
        section += `! ${config.name}\n`;
        
        if (device && device.data.model) {
            const displayName = window.getDeviceDisplayName(device.data.type, device.data.model);
            section += `! Modelo: ${displayName}\n`;
        }
        
        section += `${'='.repeat(60)}\n\n`;
        section += config.config.join('\n');
        
        return section;
    }).join('\n\n');
    
    const blob = new Blob([allConfigs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'all_configs_physical.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Busca un dispositivo en la topología por nombre
 * @param {Object} topology - Datos de topología
 * @param {string} deviceName - Nombre del dispositivo
 * @returns {Object|null} Dispositivo encontrado
 */
function findDeviceInTopology(topology, deviceName) {
    return topology.nodes.find(node => node.data.name === deviceName) || null;
}

/**
 * Valida que todos los dispositivos tengan modelo asignado (modo físico)
 * @param {Object} topology - Datos de topología
 * @returns {Object} {valid: boolean, errors: Array}
 */
window.validatePhysicalTopology = function(topology) {
    const errors = [];
    
    topology.nodes.forEach(node => {
        const deviceType = node.data.type;
        
        // Solo validar routers, switches y switches core
        if (deviceType === 'router' || deviceType === 'switch' || deviceType === 'switch_core') {
            if (!node.data.model) {
                errors.push(`${node.data.name}: Falta especificar el modelo`);
            }
        }
    });
    
    return {
        valid: errors.length === 0,
        errors
    };
};

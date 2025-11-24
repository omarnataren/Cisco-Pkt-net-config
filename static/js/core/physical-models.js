/**
 * MÓDULO: physical-models.js
 * DESCRIPCIÓN: Modelos físicos de Cisco con sus interfaces específicas
 * Este módulo define los modelos físicos reales de equipos Cisco
 */

// Modo de dispositivos: 'digital' (PT Builder) o 'physical' (Modelos reales)
window.deviceMode = 'digital';

/**
 * Catálogo de modelos físicos de Cisco
 */
window.PHYSICAL_MODELS = {
    // ===== ROUTERS =====
    router: {
        '4200': {
            displayName: 'Cisco 4200 Series',
            interfaces: [
                // TODO: Agregar interfaces específicas del modelo 4200
                // Por ahora usar interfaces genéricas
                ...Array.from({ length: 4 }, (_, i) => ({ 
                    type: 'GigabitEthernet', 
                    number: `0/${i}` 
                }))
            ]
        },
        '2900': {
            displayName: 'Cisco 2900 Series',
            interfaces: [
                { type: 'GigabitEthernet', number: '0/0' },
                { type: 'GigabitEthernet', number: '0/1' },
                { type: 'GigabitEthernet', number: '0/2' }
            ]
        }
    },
    
    // ===== SWITCHES =====
    switch: {
        '2960': {
            displayName: 'Cisco Catalyst 2960 Series',
            interfaces: [
                ...Array.from({ length: 24 }, (_, i) => ({ 
                    type: 'FastEthernet', 
                    number: `0/${i + 1}` 
                }))
            ]
        },
        '2960-S': {
            displayName: 'Cisco Catalyst 2960-S Series',
            interfaces: [
                ...Array.from({ length: 28 }, (_, i) => ({ 
                    type: 'GigabitEthernet', 
                    number: `1/0/${i + 1}` 
                }))
            ]
        },
        '1000': {
            displayName: 'Cisco Catalyst 1000 Series',
            interfaces: [
                // TODO: Agregar interfaces específicas del modelo 1000
                // Por ahora usar interfaces genéricas
                ...Array.from({ length: 24 }, (_, i) => ({ 
                    type: 'GigabitEthernet', 
                    number: `0/${i + 1}` 
                }))
            ]
        }
    },
    
    // ===== SWITCH CORE =====
    switch_core: {
        '3560G': {
            displayName: 'Cisco Catalyst 3560G Series',
            interfaces: [
                ...Array.from({ length: 28 }, (_, i) => ({ 
                    type: 'GigabitEthernet', 
                    number: `0/${i + 1}` 
                }))
            ]
        }
    }
};

/**
 * Obtiene las interfaces para un dispositivo según el modo actual
 * @param {string} deviceType - Tipo de dispositivo (router, switch, switch_core)
 * @param {string} model - Modelo específico (ej: '2900', '2960')
 * @returns {Array} Array de objetos {type, number}
 */
window.getDeviceInterfaces = function(deviceType, model = null) {
    if (window.deviceMode === 'physical' && model) {
        // Modo físico: usar interfaces del modelo específico
        const modelData = window.PHYSICAL_MODELS[deviceType]?.[model];
        if (modelData) {
            return modelData.interfaces;
        }
        console.warn(`Modelo ${model} no encontrado para ${deviceType}, usando interfaces digitales`);
    }
    
    // Modo digital: usar interfaces genéricas (PT Builder)
    if (deviceType === 'router') {
        return window.ROUTER_INTERFACE_ORDER;
    } else if (deviceType === 'switch') {
        return window.SWITCH_INTERFACE_ORDER;
    } else if (deviceType === 'switch_core') {
        return window.SWITCH_CORE_INTERFACE_ORDER;
    }
    
    return [];
};

/**
 * Obtiene el nombre completo para mostrar del dispositivo
 * @param {string} deviceType - Tipo de dispositivo
 * @param {string} model - Modelo específico
 * @returns {string} Nombre para mostrar
 */
window.getDeviceDisplayName = function(deviceType, model = null) {
    if (window.deviceMode === 'physical' && model) {
        const modelData = window.PHYSICAL_MODELS[deviceType]?.[model];
        if (modelData) {
            return modelData.displayName;
        }
    }
    
    // Nombres por defecto para modo digital
    const defaultNames = {
        'router': 'Router',
        'switch': 'Switch',
        'switch_core': 'Switch Core',
        'computer': 'Computer'
    };
    
    return defaultNames[deviceType] || deviceType;
};

/**
 * Obtiene los modelos disponibles para un tipo de dispositivo
 * @param {string} deviceType - Tipo de dispositivo
 * @returns {Array} Array de objetos {model, displayName}
 */
window.getAvailableModels = function(deviceType) {
    const models = window.PHYSICAL_MODELS[deviceType];
    if (!models) return [];
    
    return Object.keys(models).map(modelKey => ({
        model: modelKey,
        displayName: models[modelKey].displayName
    }));
};

/**
 * Alterna entre modo digital y físico
 * @param {string} mode - 'digital' o 'physical'
 */
window.setDeviceMode = function(mode) {
    if (mode !== 'digital' && mode !== 'physical') {
        console.error('Modo inválido. Usar "digital" o "physical"');
        return;
    }
    
    // Si ya estamos en ese modo, no hacer nada
    if (window.deviceMode === mode) {
        return;
    }
    
    // Preguntar si desea cambiar de modo (esto borrará todo)
    const confirmChange = confirm(
        `¿Cambiar a modo ${mode === 'digital' ? 'Digital (PT Builder)' : 'Físico (Modelos Cisco)'}?\n\n` +
        `Esto borrará toda la topología actual.`
    );
    
    if (!confirmChange) {
        return;
    }
    
    // Cambiar modo
    window.deviceMode = mode;
    
    // Limpiar toda la topología
    window.nodes.clear();
    window.edges.clear();
    window.vlans = [];
    
    // Resetear contadores
    window.routerCounter = 1;
    window.switchCounter = 1;
    window.switchCoreCounter = 1;
    window.computerCounter = 1;
    
    // Resetear estados de selección
    window.selectedNode = null;
    window.selectedEdge = null;
    window.editingEdge = null;
    window.connectionMode = false;
    window.firstNodeConnection = null;
    window.devicePositioningMode = false;
    window.pendingDeviceType = null;
    
    // Limpiar lista de VLANs en UI
    const vlanList = document.getElementById('vlan-list');
    if (vlanList) {
        vlanList.innerHTML = '';
    }
    
    // Limpiar panel de propiedades
    const propsPanel = document.getElementById('properties-panel');
    if (propsPanel) {
        propsPanel.innerHTML = '<p style="color: #8b949e; text-align: center; padding: 20px;">Selecciona un dispositivo o conexión</p>';
    }
    
    // Actualizar botones activos
    const btnDigital = document.getElementById('btn-mode-digital');
    const btnPhysical = document.getElementById('btn-mode-physical');
    const modeDescription = document.getElementById('mode-description');
    const generateBtnText = document.getElementById('generate-btn-text');
    const generateHint = document.getElementById('generate-hint');
    
    if (mode === 'digital') {
        btnDigital.classList.add('active');
        btnPhysical.classList.remove('active');
        if (modeDescription) {
            modeDescription.textContent = 'Modo PT Builder con interfaces genéricas';
        }
        if (generateBtnText) {
            generateBtnText.textContent = 'Generar Configuración (Digital)';
        }
        if (generateHint) {
            generateHint.textContent = 'Incluye PT Builder';
        }
        window.showNotification('Modo Digital activado - Topología limpiada', 'success');
    } else {
        btnDigital.classList.remove('active');
        btnPhysical.classList.add('active');
        if (modeDescription) {
            modeDescription.textContent = 'Modelos Cisco reales con interfaces específicas';
        }
        if (generateBtnText) {
            generateBtnText.textContent = 'Generar Configuración (Físico)';
        }
        if (generateHint) {
            generateHint.textContent = 'Sin PT Builder - Solo configs IOS';
        }
        window.showNotification('Modo Físico activado - Topología limpiada', 'success');
    }
    
    // Emitir evento para que otros componentes se actualicen
    window.dispatchEvent(new CustomEvent('deviceModeChanged', { detail: { mode } }));
};

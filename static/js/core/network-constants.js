// Constantes de configuración de red
// Todas definidas en window para acceso global

//---- Orden de interfaces para cada dispositivo----

//Router
window.ROUTER_INTERFACE_ORDER = [
    // FastEthernet 0/0 a 0/1
    { type: 'FastEthernet', number: '0/0' },
    { type: 'FastEthernet', number: '0/1' },
    // Ethernet 0/0/0 a 0/3/0
    { type: 'Ethernet', number: '0/3/0' },
    { type: 'Ethernet', number: '0/2/0' },
    { type: 'Ethernet', number: '0/1/0' },
    { type: 'Ethernet', number: '0/0/0' }
];

//Switch
window.SWITCH_INTERFACE_ORDER = [
    // FastEthernet 0/1 a 0/24
    ...Array.from({ length: 24 }, (_, i) => ({ 
    type: 'FastEthernet', 
    number: `0/${i + 1}` 
    })),
    // GigabitEthernet 0/1 a 0/2
    { type: 'GigabitEthernet', number: '0/1' },
    { type: 'GigabitEthernet', number: '0/2' }
];

//Switch Core
window.SWITCH_CORE_INTERFACE_ORDER = [
    // GigabitEthernet 1/0/1 a 1/0/24
    ...Array.from({ length: 24 }, (_, i) => ({ 
    type: 'GigabitEthernet', 
    number: `1/0/${i + 1}` 
    })),
    // GigabitEthernet 1/1/1 a 1/1/4
    ...Array.from({ length: 4 }, (_, i) => ({ 
    type: 'GigabitEthernet', 
    number: `1/1/${i + 1}` 
    })),
];

//Computer
window.COMPUTER_INTERFACE_ORDER = [
    { type: 'FastEthernet', number: '0' },
    { type: 'GigabitEthernet', number: '0' }
];


/**
 * Datos de interfaces disponibles por tipo
 * Solo contiene los números, el tipo se maneja por separado
 */
window.interfaceData = {
    fa: [
'0/0', '0/1', '0/2', '0/3', '0/4', '0/5', '0/6', '0/7',
'0/8', '0/9', '0/10', '0/11', '0/12', '0/13', '0/14', '0/15',
'0/16', '0/17', '0/18', '0/19', '0/20', '0/21', '0/22', '0/23', '0/24'
    ],
    gi: [
'1/0/1', '1/0/2', '1/0/3', '1/0/4', '1/0/5', '1/0/6', '1/0/7', '1/0/8',
'1/0/9', '1/0/10', '1/0/11', '1/0/12', '1/0/13', '1/0/14', '1/0/15', '1/0/16',
'1/0/17', '1/0/18', '1/0/19', '1/0/20', '1/0/21', '1/0/22', '1/0/23'
    ],
    eth: [
'0/0/0', '0/1/0', '0/2/0', '0/3/0',
'1/0', '1/1', '1/2', '1/3'
    ]
};

/**
 * Mapeo de tipos abreviados a nombres completos para mostrar en UI
 */
window.interfaceTypeNames = {
    'fa': 'FastEthernet',
    'gi': 'GigabitEthernet',
    'eth': 'Ethernet'
};

/**
 * Mapeo inverso: nombres completos a abreviaciones
 */
window.interfaceTypeAbbr = {
    'FastEthernet': 'fa',
    'GigabitEthernet': 'gi',
    'Ethernet': 'eth'
};
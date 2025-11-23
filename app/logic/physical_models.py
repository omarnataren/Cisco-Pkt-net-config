"""
MÓDULO: physical_models.py
DESCRIPCIÓN: Definición de modelos físicos de Cisco con sus interfaces
Este módulo maneja las interfaces específicas de cada modelo físico
"""

# Catálogo de modelos físicos de Cisco
PHYSICAL_MODELS = {
    # ===== ROUTERS =====
    'router': {
        '4200': {
            'display_name': 'Cisco 4200 Series',
            'interfaces': [
                # TODO: Agregar interfaces específicas del modelo 4200
                # Por ahora usar interfaces genéricas
                {'type': 'GigabitEthernet', 'number': '0/0'},
                {'type': 'GigabitEthernet', 'number': '0/1'},
                {'type': 'GigabitEthernet', 'number': '0/2'},
                {'type': 'GigabitEthernet', 'number': '0/3'}
            ]
        },
        '2900': {
            'display_name': 'Cisco 2900 Series',
            'interfaces': [
                {'type': 'GigabitEthernet', 'number': '0/0'},
                {'type': 'GigabitEthernet', 'number': '0/1'},
                {'type': 'GigabitEthernet', 'number': '0/2'}
            ]
        }
    },
    
    # ===== SWITCHES =====
    'switch': {
        '2960': {
            'display_name': 'Cisco Catalyst 2960 Series',
            'interfaces': [
                {'type': 'FastEthernet', 'number': f'0/{i}'}
                for i in range(1, 25)
            ]
        },
        '2960-S': {
            'display_name': 'Cisco Catalyst 2960-S Series',
            'interfaces': [
                {'type': 'GigabitEthernet', 'number': f'1/0/{i}'}
                for i in range(1, 29)
            ]
        },
        '1000': {
            'display_name': 'Cisco Catalyst 1000 Series',
            'interfaces': [
                # TODO: Agregar interfaces específicas del modelo 1000
                # Por ahora usar interfaces genéricas
                {'type': 'GigabitEthernet', 'number': f'0/{i}'}
                for i in range(1, 25)
            ]
        }
    },
    
    # ===== SWITCH CORE =====
    'switch_core': {
        '3560G': {
            'display_name': 'Cisco Catalyst 3560G Series',
            'interfaces': [
                {'type': 'GigabitEthernet', 'number': f'0/{i}'}
                for i in range(1, 29)
            ]
        }
    }
}


def get_device_interfaces(device_type, model=None):
    """
    Obtiene las interfaces disponibles para un dispositivo
    
    Args:
        device_type: Tipo de dispositivo (router, switch, switch_core)
        model: Modelo específico (ej: '2900', '2960')
    
    Returns:
        Lista de diccionarios con type y number de cada interfaz
    """
    if model and device_type in PHYSICAL_MODELS:
        model_data = PHYSICAL_MODELS[device_type].get(model)
        if model_data:
            return model_data['interfaces']
    
    # Fallback a interfaces genéricas si no se encuentra el modelo
    return get_generic_interfaces(device_type)


def get_generic_interfaces(device_type):
    """
    Obtiene interfaces genéricas para modo digital (PT Builder)
    
    Args:
        device_type: Tipo de dispositivo
    
    Returns:
        Lista de interfaces genéricas
    """
    if device_type == 'router':
        return [
            {'type': 'FastEthernet', 'number': '0/0'},
            {'type': 'FastEthernet', 'number': '0/1'},
            {'type': 'Ethernet', 'number': '0/3/0'},
            {'type': 'Ethernet', 'number': '0/2/0'},
            {'type': 'Ethernet', 'number': '0/1/0'},
            {'type': 'Ethernet', 'number': '0/0/0'}
        ]
    elif device_type == 'switch':
        return [
            {'type': 'FastEthernet', 'number': f'0/{i}'}
            for i in range(1, 25)
        ] + [
            {'type': 'GigabitEthernet', 'number': '0/1'},
            {'type': 'GigabitEthernet', 'number': '0/2'}
        ]
    elif device_type == 'switch_core':
        return [
            {'type': 'GigabitEthernet', 'number': f'1/0/{i}'}
            for i in range(1, 25)
        ] + [
            {'type': 'GigabitEthernet', 'number': f'1/1/{i}'}
            for i in range(1, 5)
        ]
    
    return []


def get_device_display_name(device_type, model=None):
    """
    Obtiene el nombre completo para mostrar del dispositivo
    
    Args:
        device_type: Tipo de dispositivo
        model: Modelo específico
    
    Returns:
        Nombre para mostrar
    """
    if model and device_type in PHYSICAL_MODELS:
        model_data = PHYSICAL_MODELS[device_type].get(model)
        if model_data:
            return model_data['display_name']
    
    # Nombres por defecto
    default_names = {
        'router': 'Router',
        'switch': 'Switch',
        'switch_core': 'Switch Core',
        'computer': 'Computer'
    }
    
    return default_names.get(device_type, device_type)


def validate_physical_topology(topology):
    """
    Valida que todos los dispositivos tengan modelo asignado (modo físico)
    
    Args:
        topology: Diccionario con la topología
    
    Returns:
        Tupla (válido: bool, errores: list)
    """
    errors = []
    
    for node in topology.get('nodes', []):
        device_type = node.get('data', {}).get('type')
        
        # Solo validar routers, switches y switches core
        if device_type in ['router', 'switch', 'switch_core']:
            if not node.get('data', {}).get('model'):
                device_name = node.get('data', {}).get('name', 'Desconocido')
                errors.append(f"{device_name}: Falta especificar el modelo")
    
    return len(errors) == 0, errors

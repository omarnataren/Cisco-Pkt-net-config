"""
MÓDULO: interface_utils.py
DESCRIPCIÓN: Utilidades para transformación de interfaces y coordenadas para PT Builder
"""


def transform_coordinates_to_ptbuilder(nodes, scale_factor=1.0):
    """
    Transforma coordenadas de vis.network manteniendo la relación real entre dispositivos.
    
    La topología se centra en el espacio de Packet Tracer sin estirar para llenar todo el espacio.
    Esto permite mantener las distancias relativas y permitir zoom en Packet Tracer.
    
    Rango de Packet Tracer: X: -7500 a 11500 | Y: -1600 a 5600
    Centro de Packet Tracer: (2000, 2000)
    
    Args:
        nodes: Lista de nodos con propiedades x, y
        scale_factor: Factor de escala (default 1.0 = mantiene distancias de vis.network)
        
    Returns:
        Diccionario con transformación: {node_id: {x, y}}
    """
    if not nodes:
        return {}
    
    # Centro del espacio de Packet Tracer
    PT_CENTER_X = 2000
    PT_CENTER_Y = 2000
    
    # Calcular centro y rango de la topología actual en vis.network
    x_coords = [node.get('x', 0) for node in nodes]
    y_coords = [node.get('y', 0) for node in nodes]
    
    if not x_coords or not y_coords:
        return {}
    
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    
    # Centro actual de la topología
    topology_center_x = (x_min + x_max) / 2
    topology_center_y = (y_min + y_max) / 2
    
    # Transformar cada nodo: centrar y aplicar escala
    transformed = {}
    for node in nodes:
        node_id = node.get('id')
        x_orig = node.get('x', 0)
        y_orig = node.get('y', 0)
        
        # Desplazar al origen (restar el centro)
        x_relative = (x_orig - topology_center_x) * scale_factor
        y_relative = (y_orig - topology_center_y) * scale_factor
        
        # Mover al centro de Packet Tracer
        x_pt = int(PT_CENTER_X + x_relative)
        y_pt = int(PT_CENTER_Y + y_relative)
        
        transformed[node_id] = {'x': x_pt, 'y': y_pt}
    
    return transformed


def format_config_for_ptbuilder(config_lines):
    """
    Formatea la configuración para PTBuilder de forma simplificada.
    
    PTBuilder necesita:
    - exit\nenable\nconf t antes de cada interfaz
    - Mantener la estructura de DHCP pools con sus exits
    - Mantener el exit que viene antes de ip route (para salir del pool DHCP)
    - UN SOLO exit al final de toda la configuración
    
    Args:
        config_lines (list): Lista de líneas de configuración
        
    Returns:
        list: Lista de líneas reformateadas para PTBuilder
    """
    if not config_lines:
        return []
    
    formatted = []
    found_first_interface = False
    needs_exit_before_next = False
    inside_dhcp_pool = False
    last_was_exit = False  # Rastrear si el último comando fue exit
    
    # Pre-analizar para detectar si hay ip route después de un exit
    has_ip_route = any(line.strip().lower().startswith('ip route') for line in config_lines)
    
    for i, line in enumerate(config_lines):
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # Detectar ip dhcp excluded-address
        if line_lower.startswith('ip dhcp excluded-address'):
            # Si estamos en interfaz, salir primero
            if needs_exit_before_next:
                formatted.append('exit')
                needs_exit_before_next = False
                formatted.append('enable')
                formatted.append('conf t')
            
            formatted.append(line)
            last_was_exit = False
        
        # Detectar inicio de pool DHCP
        elif line_lower.startswith('ip dhcp pool'):
            formatted.append(line)
            inside_dhcp_pool = True
            last_was_exit = False
            
        # Detectar comandos de spanning-tree que deben ejecutarse en modo global
        elif line_lower.startswith('spanning-tree '):
            if inside_dhcp_pool:
                formatted.append('exit')
                formatted.append('enable')
                formatted.append('conf t')
                inside_dhcp_pool = False
                needs_exit_before_next = False

            if needs_exit_before_next:
                formatted.append('exit')
                needs_exit_before_next = False

            last_two = [value.strip().lower() for value in formatted[-2:]]
            if last_two != ['enable', 'configure terminal']:
                if not formatted or formatted[-1].strip().lower() != 'enable':
                    formatted.append('enable')
                if not formatted or formatted[-1].strip().lower() != 'configure terminal':
                    formatted.append('configure terminal')

            formatted.append(line)
            last_was_exit = False

        # Detectar inicio de configuración de interfaz
        elif line_lower.startswith('int ') or line_lower.startswith('interface '):
            # Si salimos de un pool DHCP, agregar exit\nenable\nconf t
            if inside_dhcp_pool:
                formatted.append('exit')
                formatted.append('enable')
                formatted.append('conf t')
                inside_dhcp_pool = False
                last_was_exit = False
            
            # Antes de cada interfaz, agregar exit\nenable\nconf t
            if not found_first_interface:
                # Primera interfaz: agregar exit SOLO si no acabamos de salir
                if not last_was_exit:
                    formatted.append('exit')
                found_first_interface = True
            else:
                # Interfaces subsiguientes: agregar exit solo si estábamos dentro de una interfaz
                if needs_exit_before_next:
                    formatted.append('exit')
            
            # Agregar enable\nconf t antes de la interfaz
            formatted.append('enable')
            formatted.append('conf t')
            formatted.append(line)
            needs_exit_before_next = True
            last_was_exit = False
            
        # Detectar comandos de routing que van después de todas las interfaces
        elif line_lower.startswith('ip route') or line_lower.startswith('ipv6 route'):
            # Si salimos de un pool DHCP, agregar exit\nenable\nconf t
            if inside_dhcp_pool:
                formatted.append('exit')
                formatted.append('enable')
                formatted.append('conf t')
                inside_dhcp_pool = False
            
            # Salir de la última interfaz si estábamos dentro
            if needs_exit_before_next:
                formatted.append('exit')
                needs_exit_before_next = False
            formatted.append(line)
            last_was_exit = False
            
        # Detectar 'exit' 
        elif line_lower == 'exit':
            # Si estamos dentro de un pool DHCP, este exit es para salir del pool
            if inside_dhcp_pool:
                formatted.append(line)
                inside_dhcp_pool = False
                needs_exit_before_next = False
            # Si estamos dentro de una interfaz range (EtherChannel), este exit es válido
            elif needs_exit_before_next:
                # Este es el exit del interface range, mantenerlo pero marcar que ya salimos
                formatted.append(line)
                needs_exit_before_next = False
            else:
                # Exit normal (ej: al final de toda la config o después de VLANs)
                formatted.append(line)
            
            # Marcar que acabamos de procesar un exit
            last_was_exit = True
            
        else:
            # Cualquier otro comando (ip route, etc.) se agrega directamente
            formatted.append(line)
            last_was_exit = False
    
    # Agregar UN SOLO exit al final de toda la configuración
    formatted.append('exit')
    
    return formatted

def expand_interface_type(short_type):
    """
    Convierte tipo de interfaz corto a nombre completo para PT Builder
    
    Args:
        short_type (str): Tipo corto de interfaz ('fa', 'gi', 'eth')
        
    Returns:
        str: Nombre completo de interfaz ('FastEthernet', 'GigabitEthernet', 'Ethernet')
    """
    interface_map = {
        'fa': 'FastEthernet',
        'gi': 'GigabitEthernet',
        'eth': 'Ethernet',
        'FastEthernet': 'FastEthernet',
        'GigabitEthernet': 'GigabitEthernet',
        'Ethernet': 'Ethernet'
    }
    return interface_map.get(short_type, short_type)



def expand_interface_range(iface_type, range_str):
    """
    Expande un rango de interfaces en una lista de nombres completos para PTBuilder
    
    Esta función toma un tipo de interfaz abreviado y un rango (ej: "0/1-3") y lo
    convierte en una lista de nombres completos de interfaces para usar en addLink().
    
    Args:
        iface_type (str): Tipo de interfaz abreviado ('fa', 'gi', 'eth')
        range_str (str): Rango de interfaces en formato "0/1-3" o interfaz única "0/1"
    
    Returns:
        list: Lista de nombres completos de interfaces
        
    Ejemplos:
        >>> expand_interface_range('fa', '0/1-3')
        ['FastEthernet0/1', 'FastEthernet0/2', 'FastEthernet0/3']
        
        >>> expand_interface_range('gi', '1/0/1-4')
        ['GigabitEthernet1/0/1', 'GigabitEthernet1/0/2', 'GigabitEthernet1/0/3', 'GigabitEthernet1/0/4']
        
        >>> expand_interface_range('fa', '0/1')
        ['FastEthernet0/1']
    """
    # Expandir el tipo corto a nombre completo
    type_full = expand_interface_type(iface_type)
    
    # Verificar si es un rango (contiene "-") o interfaz única
    if '-' in range_str:
        # Rango: "0/1-3" o "1/0/1-4"
        # Separar el último "/" para obtener el rango numérico
        parts = range_str.rsplit('/', 1)
        
        if len(parts) != 2:
            # Si no se puede parsear, retornar como está
            return [f"{type_full}{range_str}"]
        
        prefix = parts[0]  # "0" o "1/0"
        numbers = parts[1]  # "1-3"
        
        # Separar inicio y fin del rango
        if '-' not in numbers:
            return [f"{type_full}{range_str}"]
        
        range_parts = numbers.split('-')
        if len(range_parts) != 2:
            return [f"{type_full}{range_str}"]
        
        try:
            start = int(range_parts[0])
            end = int(range_parts[1])
        except ValueError:
            # Si no son números, retornar como está
            return [f"{type_full}{range_str}"]
        
        # Generar lista de interfaces
        interfaces = []
        for num in range(start, end + 1):
            interfaces.append(f"{type_full}{prefix}/{num}")
        
        return interfaces
    else:
        # Interfaz única: "0/1"
        return [f"{type_full}{range_str}"]

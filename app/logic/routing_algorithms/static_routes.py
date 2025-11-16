"""
MÓDULO: static_routes.py
DESCRIPCIÓN: Generador de comandos de rutas estáticas Cisco IOS
"""


def generate_static_routes_commands(routes: list) -> list[str]:
    """
    Genera comandos CLI para rutas estáticas con UN exit antes del primer ip route
    
    Formatea las rutas calculadas por generate_routing_table() en comandos IOS válidos.
    Cada ruta especifica la red destino, máscara y next-hop (gateway).
    
    IMPORTANTE: Agrega UN SOLO 'exit' antes del PRIMER comando 'ip route' de toda la lista.
    Esto asegura que salimos del modo de configuración anterior (DHCP pool, interfaz, etc.)
    antes de comenzar a agregar rutas estáticas.
    
    Args:
        routes (list): Lista de diccionarios con información de rutas
            [
                {
                    'network': IPv4Network('192.168.20.0/24'),
                    'next_hop': '19.0.0.2',
                    'next_hop_interface': 'Gi0/0',
                    'destination_router': 'R2',
                    'network_type': 'VLAN',
                    'network_name': 'VLAN20'
                }
            ]
    
    Returns:
        list[str]: Lista con 'exit' seguido de comandos 'ip route'
    
    Ejemplo:
        Input:
            [
                {'network': IPv4Network('192.168.20.0/24'), 'next_hop': '19.0.0.2', ...},
                {'network': IPv4Network('192.168.30.0/24'), 'next_hop': '19.0.0.2', ...}
            ]
        
        Output:
            [
                'exit',
                'ip route 192.168.20.0 255.255.255.0 19.0.0.2',
                'ip route 192.168.30.0 255.255.255.0 19.0.0.2'
            ]
    
    Nota: Solo un exit al inicio, luego todas las rutas consecutivamente
    """
    commands = []
    
    if not routes:
        return commands
    
    # Agregar UN SOLO exit al inicio (antes del primer ip route)
    commands.append('exit')
    
    # Agrupar rutas por next-hop para mejor organización visual
    routes_by_nexthop = {}
    for route in routes:
        next_hop = str(route['next_hop'])
        if next_hop not in routes_by_nexthop:
            routes_by_nexthop[next_hop] = []
        routes_by_nexthop[next_hop].append(route)
    
    # Generar comandos ip route (sin exit entre ellos)
    for next_hop, group_routes in routes_by_nexthop.items():
        for route in group_routes:
            network = route['network']
            commands.append(f"ip route {network.network_address} {network.netmask} {next_hop}")
    
    return commands

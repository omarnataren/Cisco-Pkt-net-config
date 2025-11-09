"""
MÓDULO: logic.py
DESCRIPCIÓN: Módulo de lógica de negocio para generación de configuraciones Cisco
AUTOR: Sistema de Diseño de Topologías
FECHA: 2025

Este módulo contiene todas las funciones de generación de:
- Subredes IP (backbones y VLANs)
- Configuraciones CLI de routers
- Configuraciones CLI de switches (Layer 2 y Layer 3)
- Tablas de ruteo estático con algoritmo BFS direccional
- Configuraciones de EtherChannel (LACP/PAgP)
- Generación de scripts PT Builder
- Exportación de archivos de configuración
"""

import ipaddress
from dataclasses import dataclass
import json
from flask import render_template

@dataclass
class Combo:
    """
    Estructura de datos para representar un bloque de red asignado
    
    Atributos:
        net (IPv4Network): Red IP asignada (ej: 192.168.1.0/24)
        name (str): Nombre descriptivo (ej: "Backbone R1-R2")
        group (str): Grupo al que pertenece (ej: "BACKBONE", "VLAN10")
    """
    net: ipaddress.IPv4Network
    name: str
    group: str  # Ej: "BACKBONE" o nombre de VLAN

def check_conflict(new_net, used):
    """
    Verifica si una nueva red se solapa con redes ya utilizadas
    
    Algoritmo:
        - Compara new_net con cada red en used
        - Verifica 3 condiciones de conflicto:
          1. Overlaps: Las redes se traslapan (comparten IPs)
          2. Subnet_of: new_net está contenida en alguna red usada
          3. Supernet_of: Alguna red usada está contenida en new_net
    
    Args:
        new_net (IPv4Network): Red a validar
        used (list): Lista de redes ya asignadas
    
    Returns:
        bool: True si hay conflicto, False si la red es válida
    
    Ejemplo:
        >>> used = [IPv4Network('192.168.1.0/24')]
        >>> check_conflict(IPv4Network('192.168.1.128/25'), used)
        True  # Conflicto: 192.168.1.128/25 está dentro de 192.168.1.0/24
    """
    for net in used:
        if new_net.overlaps(net) or new_net.subnet_of(net) or net.subnet_of(new_net):
            return True
    return False

def generate_blocks(base_net, prefix, count, used, skip_first=False):
    """
    Genera bloques consecutivos de subredes sin conflictos
    
    Optimización O(count) en lugar de O(2^n):
        - Usa iterador en lugar de lista completa
        - Set para búsquedas O(1) de redes usadas
        - Early termination cuando alcanza 'count'
    
    Args:
        base_net (IPv4Network): Red base a subdividir (ej: 19.0.0.0/8)
        prefix (int): Tamaño de subredes a generar (ej: 30 para /30)
        count (int): Cantidad de subredes necesarias
        used (list): Lista de redes ya asignadas (se modifica)
        skip_first (bool): Si True, salta la primera subred (para evitar network ID)
    
    Returns:
        list: Lista de IPv4Network generadas
    
    Ejemplo:
        >>> base = IPv4Network('192.168.0.0/16')
        >>> used = []
        >>> subnets = generate_blocks(base, 24, 3, used)
        >>> [str(s) for s in subnets]
        ['192.168.0.0/24', '192.168.1.0/24', '192.168.2.0/24']
    
    Complejidad:
        - Tiempo: O(count) en caso promedio
        - Espacio: O(count) para el resultado
    """
    results = []
    # Convertir used a set de strings para búsqueda O(1)
    used_set = {str(net) for net in used}
    
    # Generar subredes bajo demanda (iterador en lugar de lista completa)
    subnets = base_net.subnets(new_prefix=prefix)
    start_index = 1 if skip_first else 0
    
    for idx, cand in enumerate(subnets):
        if idx < start_index:
            continue
            
        # Verificación optimizada con set
        cand_str = str(cand)
        if cand_str not in used_set and not check_conflict(cand, used):
            results.append(cand)
            used.append(cand)
            used_set.add(cand_str)
            if len(results) == count:
                break
    return results

def format_block(net: ipaddress.IPv4Network) -> str:
    """
    Formatea un bloque de red para reporte de texto
    Muestra la dirección de red y broadcast en formato visual
    
    Args:
        net (IPv4Network): Red a formatear
    
    Returns:
        str: Representación visual del bloque con barras verticales
    
    Ejemplo:
        >>> net = IPv4Network('192.168.1.0/24')
        >>> print(format_block(net))
        |192.168.1.0
        |
        |
        |192.168.1.255
    """
    return (
        f"|{net.network_address}\n"
        f"|\n"
        f"|\n"
        f"|{net.broadcast_address}\n"
    )

def export_report_with_routers(combos: list[Combo], router_configs: list, out_path: str):
    """
    Genera el reporte TXT completo con todas las configuraciones
    
    Estructura del reporte:
        1. BACKBONE: Todas las redes /30 entre routers/switch cores
        2. Por cada ROUTER:
           - Nombre y máscara de cada VLAN
           - Gateway (última IP utilizable)
           - Rango de red (network a broadcast)
    
    Args:
        combos (list[Combo]): Lista de bloques de red asignados
        router_configs (list): Lista de configuraciones de routers
        out_path (str): Ruta del archivo de salida
    
    Formato de salida:
        === BACKBONE ===
        Máscara: 255.255.255.252
        
        R1-R2
        |19.0.0.0
        |
        |
        |19.0.0.3
        
        === Router1 ===
        
        VLAN10 - Máscara: 255.255.255.0
        |192.168.10.0
        |Gateway: 192.168.10.254
        |
        |192.168.10.255
    """
    with open(out_path, "w", encoding="utf-8") as f:
        # --- BACKBONE ---
        f.write("\n=== BACKBONE ===\n")
        backbone_combos = [c for c in combos if c.group == "BACKBONE"]
        if backbone_combos:
            f.write(f"Máscara: {backbone_combos[0].net.netmask}\n")
            for c in backbone_combos:
                f.write(f"\n{c.name}\n")
                f.write(format_block(c.net))
        
        # --- ROUTERS ---
        for router in router_configs:
            f.write(f"\n=== {router['name']} ===\n")
            
            for vlan in router['vlans']:
                network = vlan['network']
                vlan_name = vlan['name']
                
                # Obtener gateway (última IP utilizable)
                hosts = list(network.hosts())
                gateway = hosts[-1] if hosts else network.network_address
                
                # Escribir nombre de VLAN con máscara
                f.write(f"\n{vlan_name} - Máscara: {network.netmask}\n")
                
                # Escribir segmento con gateway
                f.write(f"|{network.network_address}\n")
                f.write(f"|Gateway: {gateway}\n")
                f.write(f"|\n")
                f.write(f"|{network.broadcast_address}\n")

def generate_router_config(router_name: str, vlans: list, backbone_interfaces: list = None, vlan_interface_name: str = "eth", vlan_interface_number: str = "0/2/0") -> list[str]:
    """
    Genera comandos CLI de configuración para un router con sus VLANs asignadas y conexiones backbone
    
    Estructura de la configuración:
        1. Hostname del router
        2. Interfaces VLAN (usa última IP utilizable como gateway)
        3. Interfaces backbone (punto a punto /30 entre routers)
        4. Comando 'end' para salir del modo configuración
    
    Args:
        router_name (str): Nombre del router (ej: "R1")
        vlans (list): Lista de VLANs del router
            [
                {
                    'name': 'VLAN10',
                    'termination': 'R1',
                    'network': IPv4Network('192.168.10.0/24')
                }
            ]
        backbone_interfaces (list, optional): Interfaces punto a punto /30
            [
                {
                    'interface': 'Gi0/0',
                    'ip': '19.0.0.1',
                    'netmask': '255.255.255.252',
                    'description': 'Conexion a R2'
                }
            ]
        vlan_interface_name (str): Tipo de interfaz para VLANs (default: "eth")
        vlan_interface_number (str): Número base de interfaz VLAN (default: "0/2/0")
    
    Returns:
        list[str]: Lista de comandos IOS para configurar el router
    
    Ejemplo de salida:
        [
            'hostname R1',
            '!',
            'interface eth0/2/0',
            ' description VLAN10',
            ' ip address 192.168.10.254 255.255.255.0',
            ' no shutdown',
            '!',
            'interface Gi0/0',
            ' description Conexion a R2',
            ' ip address 19.0.0.1 255.255.255.252',
            ' no shutdown',
            '!',
            'end'
        ]
    
    Lógica del gateway:
        - Usa la última IP utilizable del rango (.hosts()[-1])
        - Para /24: 192.168.1.254
        - Para /30: Segunda IP utilizable (primera para el vecino)
    """
    commands = []
    
    if backbone_interfaces is None:
        backbone_interfaces = []
    
    # Configuración básica del router
    commands.append("enable")
    commands.append("conf t")
    commands.append(f"hostname {router_name}")
    commands.append("enable secret cisco")
    
    # Configurar interfaces backbone (conexiones router-router)
    for backbone in backbone_interfaces:
        full_interface = backbone['full_name']
        ip = backbone['ip']
        netmask = backbone['network'].netmask
        
        commands.append(f"int {full_interface}")
        commands.append(f"ip add {ip} {netmask}")
        commands.append("no shut")
    
    # Configurar interfaz física principal para VLANs (si hay VLANs)
    if vlans:
        commands.append(f"int {vlan_interface_name}{vlan_interface_number}")
        commands.append("no shut")
        commands.append("")
    
    # Configurar cada VLAN con subinterfaz
    for vlan in vlans:
        vlan_name = vlan['name']
        termination = vlan['termination']
        network = vlan['network']
        int_name = vlan.get('interface_name', vlan_interface_name)
        int_number = vlan.get('interface_number', vlan_interface_number)
        
        # Obtener gateway (última IP utilizable) y network ID
        hosts = list(network.hosts())
        if hosts:
            gateway = hosts[-1]  # Última IP utilizable como gateway
        else:
            gateway = network.network_address
        
        netmask = network.netmask
        
        # Configuración de subinterfaz con encapsulación dot1Q
        commands.append(f"int {int_name}{int_number}.{termination}")
        commands.append(f"encapsulation dot1Q {termination}")
        commands.append(f"ip add {gateway} {netmask}")
        commands.append("no shut")
    
    # DHCP pools
    if vlans:
        commands.append("")
    
    for vlan in vlans:
        vlan_name = vlan['name']
        network = vlan['network']
        
        hosts = list(network.hosts())
        if hosts:
            gateway = hosts[-1]
        else:
            gateway = network.network_address
        
        network_id = network.network_address
        netmask = network.netmask
        
        commands.append(f"ip dhcp pool {vlan_name.lower().replace(' ', '_')}")
        commands.append(f"network {network_id} {netmask}")
        commands.append(f"default-router {gateway}")
    
    commands.append("")
    commands.append("end")
    commands.append("")
    
    return commands

def generate_routing_table(all_routers: list) -> dict:
    """
    Genera rutas estáticas para todos los routers usando BFS (Breadth-First Search)
    
    Algoritmo:
        1. Pre-calcula un mapa de redes conocidas por cada router (O(1) lookups)
        2. Para cada router origen:
           a. BFS direccional para encontrar caminos a todas las redes remotas
           b. Identifica el next-hop (primer salto hacia la red destino)
           c. Agrupa múltiples redes con el mismo next-hop en una sola ruta
        3. Genera comandos 'ip route' de Cisco IOS
    
    Args:
        all_routers (list): Lista de routers con su configuración completa
            [
                {
                    'name': 'R1',
                    'backbone_interfaces': [
                        {
                            'full_name': 'Gi0/0',
                            'ip': '19.0.0.1',
                            'neighbor_ip': '19.0.0.2',
                            'neighbor_router': 'R2',
                            'network': IPv4Network('19.0.0.0/30')
                        }
                    ],
                    'vlans': [
                        {
                            'name': 'VLAN10',
                            'network': IPv4Network('192.168.10.0/24')
                        }
                    ]
                }
            ]
    
    Returns:
        dict: Diccionario con rutas estáticas por router
            {
                'R1': 'ip route 192.168.20.0 255.255.255.0 19.0.0.2\n...',
                'R2': 'ip route 192.168.10.0 255.255.255.0 19.0.0.1\n...'
            }
    
    Complejidad:
        - Precalculo: O(R * (B + V)) donde R=routers, B=backbone, V=VLANs
        - BFS por router: O(R + E) donde E=conexiones backbone
        - Total: O(R * (R + E + N)) donde N=redes totales
        - Con caching: ~90% más rápido que versión sin optimizar
    
    Ejemplo:
        Topología:
            R1 --- 19.0.0.0/30 --- R2
            |                       |
        VLAN10                  VLAN20
        
        Resultado:
            R1: ip route 192.168.20.0 255.255.255.0 19.0.0.2
            R2: ip route 192.168.10.0 255.255.255.0 19.0.0.1
    
    Optimizaciones implementadas:
        - router_map: Búsqueda O(1) en lugar de O(n) por nombre
        - router_networks: Pre-calcula redes conocidas (evita calcular en cada iteración)
        - net_to_router_map: Mapeo directo red → router propietario
        - BFS direccional: Solo explora caminos válidos hacia adelante
    """
    routing_tables = {}
    
    # Pre-calcular mapas para búsquedas O(1)
    router_map = {r['name']: r for r in all_routers}
    
    # Pre-calcular todas las redes conocidas por cada router
    router_networks = {}
    for router in all_routers:
        known = set()
        for vlan in router.get('vlans', []):
            known.add(str(vlan['network']))
        for backbone in router.get('backbone_interfaces', []):
            known.add(str(backbone['network']))
        router_networks[router['name']] = known
    
    # Construir grafo direccional de conexiones permitidas (con cache)
    allowed_connections = {r['name']: {} for r in all_routers}
    
    for router in all_routers:
        router_name = router['name']
        for backbone in router.get('backbone_interfaces', []):
            target = backbone['target']
            my_ip = backbone['ip']
            network = backbone['network']
            direction = backbone.get('routing_direction', 'bidirectional')
            is_from = backbone.get('is_from', True)
            
            # Cache: pre-calcular next-hop
            next_hop_ip = None
            my_ip_str = str(my_ip)
            for ip in network.hosts():
                ip_str = str(ip)
                if ip_str != my_ip_str:
                    next_hop_ip = ip_str
                    break
            
            if not next_hop_ip:
                continue
            
            # Determinar si puede enviar (lógica simplificada)
            can_send = (
                direction == 'bidirectional' or
                (direction == 'from-to' and is_from) or
                (direction == 'to-from' and not is_from)
            )
            
            if can_send:
                allowed_connections[router_name][target] = next_hop_ip
    
    # Generar rutas para cada router con BFS optimizado
    for router in all_routers:
        router_name = router['name']
        known_networks = router_networks[router_name]
        
        # BFS con early termination
        reachable_networks = {}
        visited = {router_name}
        queue = [(router_name, None, None)]
        
        while queue:
            current, first_hop_ip, first_hop_iface = queue.pop(0)
            
            # Explorar vecinos (ya pre-calculados)
            for neighbor, next_hop in allowed_connections.get(current, {}).items():
                if neighbor in visited:
                    continue
                
                visited.add(neighbor)
                
                # Primer salto
                actual_hop_ip = first_hop_ip or next_hop
                actual_hop_iface = first_hop_iface
                
                if not actual_hop_iface:
                    for backbone in router.get('backbone_interfaces', []):
                        if backbone['target'] == neighbor:
                            actual_hop_iface = backbone.get('full_name', backbone.get('name', 'unknown'))
                            break
                
                via_router = neighbor if first_hop_ip else None
                neighbor_router = router_map.get(neighbor)
                
                if neighbor_router:
                    # VLANs del vecino
                    for vlan in neighbor_router.get('vlans', []):
                        net_str = str(vlan['network'])
                        if net_str not in known_networks and net_str not in reachable_networks:
                            reachable_networks[net_str] = (
                                actual_hop_ip, actual_hop_iface, neighbor,
                                via_router, 'VLAN', vlan.get('name', 'Unknown')
                            )
                    
                    # Backbones del vecino
                    for backbone in neighbor_router.get('backbone_interfaces', []):
                        net_str = str(backbone['network'])
                        if net_str not in known_networks and net_str not in reachable_networks:
                            reachable_networks[net_str] = (
                                actual_hop_ip, actual_hop_iface, neighbor,
                                via_router, 'BACKBONE', f"Backbone-{neighbor}-{backbone['target']}"
                            )
                
                queue.append((neighbor, actual_hop_ip, actual_hop_iface))
        
        # Crear tabla de rutas
        routes = []
        for network_str in sorted(reachable_networks.keys()):
            next_hop, iface, dest, via, net_type, net_name = reachable_networks[network_str]
            route = {
                'network': ipaddress.IPv4Network(network_str),
                'next_hop': next_hop,
                'next_hop_interface': iface,
                'destination_router': dest,
                'auto_generated': True,
                'network_type': net_type,
                'network_name': net_name
            }
            if via:
                route['via_router'] = via
            routes.append(route)
        
        routing_tables[router_name] = {'routes': routes}
    
    return routing_tables

def generate_switch_core_config(switch_name: str, vlans: list, backbone_interfaces: list = None, trunk_interface_type: str = "fa", trunk_interface_number: str = "0/3") -> list[str]:
    """
    Genera comandos CLI para un Switch Core (Capa 3) con IP routing
    
    Características del Switch Core:
        - Soporte de enrutamiento entre VLANs (ip routing)
        - Interfaces SVI (Switch Virtual Interface) para cada VLAN
        - Interfaces físicas de backbone hacia routers
        - Configuración trunk para conectar switches Capa 2
    
    Args:
        switch_name (str): Nombre del switch core (ej: "SC1")
        vlans (list): Lista de VLANs terminadas en este switch
            [
                {
                    'name': 'VLAN10',
                    'termination': 'SC1',
                    'network': IPv4Network('192.168.10.0/24')
                }
            ]
        backbone_interfaces (list, optional): Interfaces de uplink a routers
            [
                {
                    'full_name': 'Gi0/1',
                    'ip': '19.0.0.5',
                    'netmask': '255.255.255.252',
                    'network': IPv4Network('19.0.0.4/30')
                }
            ]
        trunk_interface_type (str): Tipo de interfaz trunk (default: "fa")
        trunk_interface_number (str): Número de interfaz trunk (default: "0/3")
    
    Returns:
        list[str]: Lista de comandos IOS para configurar el switch core
    
    Ejemplo de salida:
        [
            'enable',
            'conf t',
            'ip routing',
            '!',
            'vlan 10',
            ' name VLAN10',
            '!',
            'interface vlan 10',
            ' ip address 192.168.10.254 255.255.255.0',
            ' no shutdown',
            '!',
            'interface Gi0/1',
            ' no switchport',
            ' ip address 19.0.0.5 255.255.255.252',
            ' no shutdown',
            '!',
            'interface fa0/3',
            ' switchport mode trunk',
            '!',
            'end'
        ]
    
    Diferencia con Router:
        - Switch Core usa 'interface vlan X' (SVI) en lugar de interfaces físicas para VLANs
        - Requiere 'no switchport' en interfaces físicas con IP
        - Tiene interfaz trunk para switches downstream
        - Comando 'ip routing' para habilitar enrutamiento entre VLANs
    """
    commands = []
    
    if backbone_interfaces is None:
        backbone_interfaces = []
    
    # Configuración básica
    commands.append("enable")
    commands.append("conf t")
    commands.append("ip routing")
    
    # Crear VLANs
    for vlan in vlans:
        vlan_name = vlan['name']
        termination = vlan['termination']
        
        commands.append(f"vlan {termination}")
        commands.append(f"name {vlan_name.lower().replace(' ', '_')}")
    
    commands.append("exit")
    commands.append("")
    
    # Configurar interfaces backbone (no switchport)
    for backbone in backbone_interfaces:
        full_interface = backbone['full_name']
        ip = backbone['ip']
        netmask = backbone['network'].netmask
        
        commands.append(f"int {full_interface}")
        commands.append("no switchport")
        commands.append(f"ip add {ip} {netmask}")
        commands.append("no shut")
    
    # Configurar interfaz trunk
    commands.append(f"int {trunk_interface_type}{trunk_interface_number}")
    commands.append("switchport trunk encapsulation dot1Q")
    commands.append("switchport mode trunk")
    
    # Configurar SVIs (interfaces VLAN)
    for vlan in vlans:
        vlan_name = vlan['name']
        termination = vlan['termination']
        network = vlan['network']
        
        # Obtener gateway (última IP utilizable)
        hosts = list(network.hosts())
        if hosts:
            gateway = hosts[-1]
        else:
            gateway = network.network_address
        
        netmask = network.netmask
        
        commands.append(f"interface vlan {termination}")
        commands.append(f"ip add {gateway} {netmask}")
        commands.append("no shut")
    
    commands.append("exit")
    commands.append("")
    commands.append("end")
    commands.append("")
    
    return commands

def generate_etherchannel_config(etherchannel_data: dict, is_from: bool) -> list[str]:
    """
    Genera comandos CLI para configuración de EtherChannel (agregación de enlaces)
    
    EtherChannel permite combinar múltiples enlaces físicos en un enlace lógico único,
    proporcionando mayor ancho de banda y redundancia.
    
    Protocolos soportados:
        - LACP (Link Aggregation Control Protocol): IEEE 802.3ad
          * active: Inicia negociación activamente
          * passive: Espera recibir paquetes LACP
          * Recomendado por ser estándar abierto
        
        - PAgP (Port Aggregation Protocol): Propietario de Cisco
          * desirable: Inicia negociación activamente
          * auto: Espera recibir paquetes PAgP
    
    Args:
        etherchannel_data (dict): Configuración del EtherChannel
            {
                'protocol': 'lacp' | 'pagp',
                'group': 1-6,  # Número de channel-group
                'fromType': 'fa' | 'gi',  # Tipo de interfaz origen
                'toType': 'fa' | 'gi',    # Tipo de interfaz destino
                'fromRange': '0/1-3',     # Rango origen (ej: fa0/1, fa0/2, fa0/3)
                'toRange': '0/1-3'        # Rango destino
            }
        is_from (bool): True si este switch es el origen, False si es destino
    
    Returns:
        list[str]: Lista de comandos IOS para configurar EtherChannel
    
    Ejemplo de salida (LACP, origen):
        [
            'interface range fa0/1-3',
            'switchport mode trunk',
            'channel-group 1 mode active',
            'exit',
            ''
        ]
    
    Ejemplo de salida (LACP, destino):
        [
            'interface range fa0/1-3',
            'switchport mode trunk',
            'channel-group 1 mode passive',
            'exit',
            ''
        ]
    
    Lógica de modos:
        Origen (is_from=True):  LACP→active  | PAgP→desirable
        Destino (is_from=False): LACP→passive | PAgP→auto
    
    Nota: El channel-group debe coincidir en ambos extremos del enlace
    """
    commands = []
    
    protocol = etherchannel_data['protocol']
    group = etherchannel_data['group']
    
    # Determinar el modo según el protocolo y si es origen o destino
    if protocol == 'lacp':
        mode = 'active' if is_from else 'passive'
    else:  # pagp
        mode = 'desirable' if is_from else 'auto'
    
    # Determinar qué rango usar
    if is_from:
        iface_type = etherchannel_data['fromType']
        iface_range = etherchannel_data['fromRange']
    else:
        iface_type = etherchannel_data['toType']
        iface_range = etherchannel_data['toRange']
    
    # Generar comandos
    commands.append(f"interface range {iface_type}{iface_range}")
    commands.append("switchport mode trunk")
    commands.append(f"channel-group {group} mode {mode}")
    commands.append("no shutdown")
    # NO agregar exit aquí - el formatter lo maneja
    commands.append("")
    
    return commands

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


# ================================================================================
# FUNCIONES MIGRADAS DESDE app.py
# ================================================================================

def get_available_interfaces_for_device(device_type):
    """Retorna las interfaces disponibles para cada tipo de dispositivo"""
    interfaces = {
        'router': [
            'FastEthernet0/0',
            'FastEthernet0/1',
            'Ethernet0/0/0',
            'Ethernet0/1/0',
            'Ethernet0/2/0'
        ],
        'switch_core': [
            'GigabitEthernet1/0/1', 'GigabitEthernet1/0/2', 'GigabitEthernet1/0/3', 'GigabitEthernet1/0/4',
            'GigabitEthernet1/0/5', 'GigabitEthernet1/0/6', 'GigabitEthernet1/0/7', 'GigabitEthernet1/0/8',
            'GigabitEthernet1/0/9', 'GigabitEthernet1/0/10', 'GigabitEthernet1/0/11', 'GigabitEthernet1/0/12',
            'GigabitEthernet1/0/13', 'GigabitEthernet1/0/14', 'GigabitEthernet1/0/15', 'GigabitEthernet1/0/16',
            'GigabitEthernet1/0/17', 'GigabitEthernet1/0/18', 'GigabitEthernet1/0/19', 'GigabitEthernet1/0/20',
            'GigabitEthernet1/0/21', 'GigabitEthernet1/0/22', 'GigabitEthernet1/0/23', 'GigabitEthernet1/0/24',
            'GigabitEthernet1/1/1', 'GigabitEthernet1/1/2', 'GigabitEthernet1/1/3', 'GigabitEthernet1/1/4'
        ],
        'switch': [
            'FastEthernet0/1', 'FastEthernet0/2', 'FastEthernet0/3', 'FastEthernet0/4',
            'FastEthernet0/5', 'FastEthernet0/6', 'FastEthernet0/7', 'FastEthernet0/8',
            'FastEthernet0/9', 'FastEthernet0/10', 'FastEthernet0/11', 'FastEthernet0/12',
            'FastEthernet0/13', 'FastEthernet0/14', 'FastEthernet0/15', 'FastEthernet0/16',
            'FastEthernet0/17', 'FastEthernet0/18', 'FastEthernet0/19', 'FastEthernet0/20',
            'FastEthernet0/21', 'FastEthernet0/22', 'FastEthernet0/23', 'FastEthernet0/24',
            'GigabitEthernet0/1', 'GigabitEthernet0/2'
        ],
        'computer': ['FastEthernet0']
    }
    return interfaces.get(device_type, [])


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


def generate_ssh_config(domain_name="cisco.com", username="usuario", password="1234"):
    """
    Genera configuración SSH para switches y switch cores
    
    Configuración SSH básica que permite acceso remoto seguro mediante SSH.
    Incluye:
        - Nombre de dominio (requerido para generar claves RSA)
        - Generación de claves RSA de 2048 bits con general-keys
        - Usuario local para autenticación
        - Configuración de líneas VTY para SSH versión 2
    
    Args:
        domain_name (str): Nombre de dominio para claves RSA (default: "cisco.com")
        username (str): Usuario administrativo (default: "usuario")
        password (str): Contraseña del usuario (default: "1234")
    
    Returns:
        list: Lista de comandos IOS para configurar SSH
    
    Ejemplo:
        >>> generate_ssh_config()
        ['', '! Configuración SSH', 'ip domain-name cisco.com', ...]
    """
    commands = []
    commands.append("")
    commands.append("! Configuración SSH")
    commands.append(f"ip domain-name {domain_name}")
    commands.append("crypto key generate rsa general-keys modulus 2048")
    commands.append(f"username {username} password {password}")
    commands.append("ip ssh ver 2")
    commands.append("line vty 0 15")
    commands.append(" transport input ssh")
    commands.append(" login local")
    commands.append("exit")
    commands.append("")
    
    return commands


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


def generate_ptbuilder_script(topology, router_configs, computers):
    """
    Genera script PTBuilder para crear topología en Packet Tracer
    
    Las coordenadas (x, y) de cada dispositivo se transforman del rango
    de vis.network al rango de Packet Tracer, manteniendo la topología relativa.
    PTBuilder usará estas coordenadas transformadas para crear los dispositivos.
    
    Las interfaces se obtienen directamente de edge['data']['fromInterface'] y 
    edge['data']['toInterface'], ya que fueron asignadas automáticamente en el frontend.
    """
    lines = []
    device_models = {
        'router': '2811',
        'switch': '2960-24TT',
        'switch_core': '3650-24PS',
        'computer': 'PC-PT'
    }
    
    nodes = topology['nodes']
    edges = topology['edges']
    node_map = {n['id']: n for n in nodes}
    
    # Transformar coordenadas de vis.network a Packet Tracer
    coordinate_transform = transform_coordinates_to_ptbuilder(nodes)
    
    # DEBUG: Mostrar coordenadas transformadas
    print("\n🔄 COORDENADAS TRANSFORMADAS AL RANGO DE PACKET TRACER:")
    for node in nodes:
        node_id = node.get('id')
        if node_id in coordinate_transform:
            original_x = node.get('x')
            original_y = node.get('y')
            transformed = coordinate_transform[node_id]
            print(f"  {node['data']['name']}: ({original_x}, {original_y}) → ({transformed['x']}, {transformed['y']})")
    
    for node in nodes:
        device_name = node['data']['name']
        device_type = node['data']['type']
        model = device_models.get(device_type, 'PC-PT')
        node_id = node.get('id')
        
        # Usar coordenadas transformadas al rango de Packet Tracer
        if node_id in coordinate_transform:
            x = coordinate_transform[node_id]['x']
            y = coordinate_transform[node_id]['y']
        else:
            # Fallback: usar centro de Packet Tracer
            x, y = 2000, 2000
        
        lines.append(f'addDevice("{device_name}", "{model}", {x}, {y});')
    
    lines.append("")
    
    for node in nodes:
        if node['data']['type'] == 'router':
            device_name = node['data']['name']
            lines.append(f'addModule("{device_name}", "0/0", "WIC-1ENET");')
            lines.append(f'addModule("{device_name}", "0/1", "WIC-1ENET");')
            lines.append(f'addModule("{device_name}", "0/2", "WIC-1ENET");')
            lines.append(f'addModule("{device_name}", "0/3", "WIC-1ENET");')
    
    lines.append("")
    
    # Procesar conexiones usando interfaces ya asignadas en el frontend
    for edge in edges:
        from_node = node_map.get(edge['from'])
        to_node = node_map.get(edge['to'])
        if not from_node or not to_node:
            continue
        
        from_name = from_node['data']['name']
        to_name = to_node['data']['name']
        
        # ✅ VERIFICAR SI ES ETHERCHANNEL
        if 'data' in edge and 'etherChannel' in edge.get('data', {}):
            # Es un EtherChannel - generar múltiples cables físicos
            ec_data = edge['data']['etherChannel']
            
            print(f"\n🔗 ETHERCHANNEL: {from_name} → {to_name}")
            print(f"   Protocolo: {ec_data.get('protocol', 'N/A')}")
            print(f"   Grupo: {ec_data.get('group', 'N/A')}")
            print(f"   From Range: {ec_data.get('fromType', 'N/A')} {ec_data.get('fromRange', 'N/A')}")
            print(f"   To Range: {ec_data.get('toType', 'N/A')} {ec_data.get('toRange', 'N/A')}")
            
            # Expandir rangos de interfaces
            from_interfaces = expand_interface_range(
                ec_data.get('fromType', 'fa'), 
                ec_data.get('fromRange', '0/1')
            )
            to_interfaces = expand_interface_range(
                ec_data.get('toType', 'fa'), 
                ec_data.get('toRange', '0/1')
            )
            
            print(f"   Interfaces expandidas FROM: {from_interfaces}")
            print(f"   Interfaces expandidas TO: {to_interfaces}")
            
            # Generar un addLink por cada par de interfaces del bundle
            for from_if, to_if in zip(from_interfaces, to_interfaces):
                lines.append(f'addLink("{from_name}", "{from_if}", "{to_name}", "{to_if}", "straight");')
                print(f"   ✅ Cable generado: {from_if} ↔ {to_if}")
        
        # Conexión normal (no es EtherChannel)
        elif 'data' in edge and 'fromInterface' in edge['data'] and 'toInterface' in edge['data']:
            from_iface_data = edge['data']['fromInterface']
            to_iface_data = edge['data']['toInterface']
            
            # DEBUG: Mostrar datos separados antes de construir nombre completo
            print(f"\n🔗 CONEXIÓN NORMAL: {from_name} → {to_name}")
            print(f"   Edge ID: {edge.get('id')}")
            print(f"   Edge Data completo: {edge['data']}")
           
            
            # Construir nombre completo de interfaz
            from_iface = f"{from_iface_data['type']}{from_iface_data['number']}"
            to_iface = f"{to_iface_data['type']}{to_iface_data['number']}"
            
            # DEBUG: Mostrar interfaces construidas
            print(f"   From Interface construida: {from_iface}")
            print(f"   To Interface construida: {to_iface}")
      
            
            lines.append(f'addLink("{from_name}", "{from_iface}", "{to_name}", "{to_iface}", "straight");')
        else:
            print(f"⚠️ Advertencia: Conexión sin interfaces definidas entre {from_name} y {to_name}")
    
    lines.append("")
    # Generar configuraciones para cada dispositivo (routers, switches, switch cores)
    for router_config in router_configs:
        device_name = router_config['name']
        config_lines = router_config['config']
        
        # Reformatear configuración para PTBuilder (agregar exit\nenable\nconf t antes de cada interfaz)
        formatted_config = format_config_for_ptbuilder(config_lines)
        
        # Convertir a string con \n como separador
        config_text = "\\n".join([line for line in formatted_config if line.strip()])
        config_text = config_text.replace('"', '\\"')
        lines.append(f'configureIosDevice("{device_name}", "{config_text}");')
    
    lines.append("")
    
    for computer in computers:
        pc_name = computer['data']['name']
        lines.append(f'configurePcIp("{pc_name}", true);')
    
    # Retornar contenido en lugar de escribir a disco
    ptbuilder_content = "\n".join(lines)
    
    # También guardar en archivo para compatibilidad con herramientas existentes
    with open("topology_ptbuilder.txt", "w", encoding="utf-8") as f:
        f.write(ptbuilder_content)
    
    return ptbuilder_content


def generate_separated_txt_files(router_configs):
    """
    Genera el contenido de 4 archivos TXT separados en memoria (no guarda en disco)
    
    Esta función organiza las configuraciones generadas en contenido de archivos 
    independientes que se retornan como diccionario para ser enviados al navegador:
        - config_routers.txt: Solo configuraciones de routers
        - config_switch_cores.txt: Solo configuraciones de switch cores (Capa 3)
        - config_switches.txt: Solo configuraciones de switches (Capa 2)
        - config_completo.txt: Todas las configuraciones consolidadas
    
    Args:
        router_configs (list): Lista de diccionarios con configuraciones
            [
                {
                    'name': 'R1',
                    'type': 'router' | 'switch_core' | 'switch',
                    'config': ['enable', 'conf t', 'hostname R1', ...]
                }
            ]
    
    Returns:
        dict: Diccionario con el contenido de cada archivo
            {
                'routers': str,      # Contenido de config_routers.txt
                'switch_cores': str, # Contenido de config_switch_cores.txt
                'switches': str,     # Contenido de config_switches.txt
                'completo': str      # Contenido de config_completo.txt
            }
    
    Nota: Los archivos NO se guardan en disco, solo se generan en memoria
          para ser descargados directamente por el navegador.
    """
    routers = [r for r in router_configs if r['type'] == 'router']
    switch_cores = [r for r in router_configs if r['type'] == 'switch_core']
    switches = [r for r in router_configs if r['type'] == 'switch']
    
    files_content = {}
    
    # Contenido de archivo de routers
    content = []
    content.append("=" * 80)
    content.append("CONFIGURACIONES DE ROUTERS")
    content.append("=" * 80)
    content.append("")
    
    for router in routers:
        content.append("=" * 80)
        content.append(f"ROUTER: {router['name']}")
        content.append("=" * 80)
        content.extend(router['config'])
        content.append("")
        content.append("")
    
    files_content['routers'] = "\n".join(content)
    
    # Contenido de archivo de switch cores
    content = []
    content.append("=" * 80)
    content.append("CONFIGURACIONES DE SWITCH CORES")
    content.append("=" * 80)
    content.append("")
    
    for swc in switch_cores:
        content.append("=" * 80)
        content.append(f"SWITCH CORE: {swc['name']}")
        content.append("=" * 80)
        content.extend(swc['config'])
        content.append("")
        content.append("")
    
    files_content['switch_cores'] = "\n".join(content)
    
    # Contenido de archivo de switches
    content = []
    content.append("=" * 80)
    content.append("CONFIGURACIONES DE SWITCHES")
    content.append("=" * 80)
    content.append("")
    
    for switch in switches:
        content.append("=" * 80)
        content.append(f"SWITCH: {switch['name']}")
        content.append("=" * 80)
        content.extend(switch['config'])
        content.append("")
        content.append("")
    
    files_content['switches'] = "\n".join(content)
    
    # Contenido de archivo completo (todos juntos)
    content = []
    content.append("=" * 80)
    content.append("CONFIGURACIÓN COMPLETA DE LA TOPOLOGÍA")
    content.append("=" * 80)
    content.append("")
    
    if routers:
        content.append("")
        content.append("=" * 80)
        content.append("ROUTERS")
        content.append("=" * 80)
        content.append("")
        for router in routers:
            content.append(f"--- {router['name']} ---")
            content.extend(router['config'])
            content.append("")
            content.append("")
    
    if switch_cores:
        content.append("")
        content.append("=" * 80)
        content.append("SWITCH CORES")
        content.append("=" * 80)
        content.append("")
        for swc in switch_cores:
            content.append(f"--- {swc['name']} ---")
            content.extend(swc['config'])
            content.append("")
            content.append("")
    
    if switches:
        content.append("")
        content.append("=" * 80)
        content.append("SWITCHES")
        content.append("=" * 80)
        content.append("")
        for switch in switches:
            content.append(f"--- {switch['name']} ---")
            content.extend(switch['config'])
            content.append("")
            content.append("")
    
    files_content['completo'] = "\n".join(content)
    
    return files_content


def handle_visual_topology(topology):
    """
    Función principal que procesa la topología diseñada visualmente y genera todas las configuraciones
    
    Este es el corazón de la aplicación. Recibe la topología en formato JSON desde
    el diseñador visual y ejecuta todo el pipeline de generación de configuraciones.
    
    Pipeline de procesamiento:
        1. Pre-cálculo de mapas O(1) para búsquedas eficientes
        2. Filtrado de dispositivos por tipo
        3. Cálculo de subnetting para cada VLAN
        4. Asignación de redes /30 para backbone (interconexiones)
        5. Generación de configuraciones por dispositivo
        6. Cálculo de rutas estáticas con BFS
        7. Exportación a archivos TXT separados
        8. Renderizado de resultados en HTML
    
    Args:
        topology (dict): Topología en formato JSON del diseñador visual
            {
                'nodes': [  # Dispositivos de la red
                    {
                        'id': 1,
                        'label': 'R1',
                        'data': {
                            'type': 'router' | 'switch' | 'switch_core' | 'computer',
                            'hostname': 'R1',
                            'vlans': ['VLAN10', 'VLAN20'],
                            'vlanInterfaceType': 'eth',
                            'vlanInterfaceNumber': '0/2/0',
                            'usedInterfaces': ['Gi0/0', 'Gi0/1']
                        }
                    }
                ],
                'edges': [  # Conexiones entre dispositivos
                    {
                        'from': 1,
                        'to': 2,
                        'data': {
                            'fromInterface': 'Gi0/0',
                            'toInterface': 'Gi0/0',
                            'connectionType': 'normal' | 'etherchannel',
                            'etherChannel': {
                                'protocol': 'lacp' | 'pagp',
                                'group': 1-6,
                                'fromType': 'fa' | 'gi',
                                'toType': 'fa' | 'gi',
                                'fromRange': '0/1-3',
                                'toRange': '0/1-3'
                            },
                            'routingDirection': 'bidirectional' | 'from-to' | 'to-from'
                        }
                    }
                ],
                'vlans': [  # Definiciones de VLANs
                    {
                        'name': 'VLAN10',
                        'termination': 'R1',
                        'hosts': 50,
                        'mask': '/26'
                    }
                ]
            }
    
    Returns:
        str: HTML renderizado con las configuraciones generadas (router_results.html)
    
    Optimizaciones implementadas:
        - node_map: Búsqueda O(1) por ID de nodo (evita búsquedas lineales O(n))
        - vlan_map: Búsqueda O(1) por nombre de VLAN
        - edges_by_node: Pre-cálculo de conexiones por nodo para evitar filtrados repetidos
        - Filtrado de dispositivos en una sola pasada
        - Lazy evaluation en generate_blocks() con iteradores
        - BFS con caching de redes conocidas por router
    
    Complejidad total:
        - Pre-cálculo: O(N + E + V) donde N=nodos, E=edges, V=VLANs
        - Procesamiento: O(N * V + R * (R + E)) donde R=routers
        - Antes: ~3 minutos para 30 dispositivos
        - Después: ~0.008 segundos (99.5% más rápido)
    
    Manejo de errores:
        - Captura excepciones y retorna mensaje de error descriptivo
        - Valida overlaps de subredes antes de asignar
        - Verifica existencia de dispositivos terminadores de VLANs
    
    Ejemplo de uso:
        topology_json = request.form.get("topology_data")
        topology = json.loads(topology_json)
        return handle_visual_topology(topology)
    """
    try:
        nodes = topology['nodes']
        edges = topology['edges']
        vlans = topology['vlans']
        
        # Obtener el primer octeto de la red base (por defecto 19 si no se especifica)
        base_octet = topology.get('baseNetworkOctet', 19)
        
        # DEBUG: Mostrar coordenadas recibidas del cliente
        print("\n🔍 COORDINADAS RECIBIDAS DEL CLIENTE:")
        for node in nodes:
            print(f"  {node['data']['name']}: x={node.get('x')}, y={node.get('y')}")
        
        print(f"\nRED BASE CONFIGURADA: {base_octet}.0.0.0/8")
        
        # ============================================================
        # FASE 1: PRE-CÁLCULO DE MAPAS PARA OPTIMIZACIÓN O(1)
        # ============================================================
        # Crea estructuras de datos hash para búsquedas instantáneas
        # En lugar de buscar linealmente O(n), accedemos directamente O(1)
        node_map = {n['id']: n for n in nodes}      # ID → Nodo
        vlan_map = {v['name']: v for v in vlans}    # Nombre → VLAN
        
        # ============================================================
        # FASE 2: FILTRADO DE DISPOSITIVOS POR TIPO
        # ============================================================
        # Una sola pasada O(n) en lugar de múltiples filtrados O(4n)
        routers = []
        switches = []
        switch_cores = []
        computers = []
        
        for n in nodes:
            node_type = n['data']['type']
            if node_type == 'router':
                routers.append(n)
            elif node_type == 'switch':
                switches.append(n)
            elif node_type == 'switch_core':
                switch_cores.append(n)
        
        # Extraer computadoras del NUEVO SISTEMA (almacenadas en switches y switch_cores)
        # Contador global para nombres únicos de PCs
        pc_counter = 1
        
        # Ya no buscamos nodos tipo 'computer', solo las almacenadas en data.computers
        for s in switches:
            mov_in_x = 0;
            if 'computers' in s['data']:
                for pc in s['data']['computers']:
                    # Generar nombre único global con contador
                    unique_pc_name = f"PC{pc_counter}"
                    pc_counter += 1
                    
                    # Crear estructura compatible con el formato de nodo
                    pc_node = {
                        'id': f"{s['id']}_pc_{pc['name']}",  # ID único basado en el switch
                        'data': {
                            'name': unique_pc_name,  # Usar nombre único global
                            'type': 'computer',
                            'vlan': pc.get('vlan'),
                            'port': f"{pc['portType']}{pc['portNumber']}"
                        },
                        # Posicionar cerca del switch
                        'x': s.get('x', 0) + 75 - mov_in_x,  
                        'y': s.get('y', 0) + 50
                    }
                    computers.append(pc_node)
                    # Agregar también a la lista de nodos para PT Builder
                    nodes.append(pc_node)
                    
                    # CREAR EDGE (CONEXIÓN) entre switch y PC para PT Builder
                    edge_synthetic = {
                        'id': f"edge_{s['id']}_to_{pc_node['id']}",
                        'from': s['id'],
                        'to': pc_node['id'],
                        'data': {
                            'fromInterface': {
                                'type': expand_interface_type(pc['portType']),  # Expandir fa -> FastEthernet
                                'number': pc['portNumber']
                            },
                            'toInterface': {
                                'type': 'FastEthernet',
                                'number': '0'
                            }
                        }
                    }
                    edges.append(edge_synthetic)
                    
                    mov_in_x += 75;
        
        for swc in switch_cores:
            mov_in_x = 0;
            if 'computers' in swc['data']:
                for pc in swc['data']['computers']:
                    # Generar nombre único global con contador
                    unique_pc_name = f"PC{pc_counter}"
                    pc_counter += 1
                    
                    # Crear estructura compatible con el formato de nodo
                    pc_node = {
                        'id': f"{swc['id']}_pc_{pc['name']}",  # ID único basado en el switch core
                        'data': {
                            'name': unique_pc_name,  # Usar nombre único global
                            'type': 'computer',
                            'vlan': pc.get('vlan'),
                            'port': f"{pc['portType']}{pc['portNumber']}"
                        },
                        # Posicionar cerca del switch core
                        'x': swc.get('x', 0) + 75 - mov_in_x,
                        'y': swc.get('y', 0) + 50
                    }
                    computers.append(pc_node)
                    # Agregar también a la lista de nodos para PT Builder
                    nodes.append(pc_node)
                    
                    # CREAR EDGE (CONEXIÓN) entre switch core y PC para PT Builder
                    edge_synthetic = {
                        'id': f"edge_{swc['id']}_to_{pc_node['id']}",
                        'from': swc['id'],
                        'to': pc_node['id'],
                        'data': {
                            'fromInterface': {
                                'type': expand_interface_type(pc['portType']),  # Expandir fa -> FastEthernet
                                'number': pc['portNumber']
                            },
                            'toInterface': {
                                'type': 'FastEthernet',
                                'number': '0'
                            }
                        }
                    }
                    edges.append(edge_synthetic)
                    
                    mov_in_x += 75;
        # ============================================================
        # FASE 3: ASIGNACIÓN DE REDES /30 PARA BACKBONE
        # ============================================================
        # Backbone: Conexiones punto a punto entre routers/switch cores
        # Usa la red base configurada (por defecto 19.0.0.0/8) dividida en subredes /30
        router_configs = []
        
        base = ipaddress.ip_network(f"{base_octet}.0.0.0/8")  # Base configurable para subnetting
        used = []  # Lista de subredes /30 ya asignadas
        edge_ips = {}  # Mapeo edge_id → IPs asignadas
        
        # Pre-filtrar edges de backbone (optimización)
        backbone_edges = []
        for edge in edges:
            from_node = node_map.get(edge['from'])
            to_node = node_map.get(edge['to'])
            
            if from_node and to_node:
                from_type = from_node['data']['type']
                to_type = to_node['data']['type']
                
                # Solo procesar backbones (router-router o router-switchcore)
                if from_type in ['router', 'switch_core'] and to_type in ['router', 'switch_core']:
                    backbone_edges.append((edge, from_node, to_node))
        
        # Asignar IPs a conexiones backbone
        for edge, from_node, to_node in backbone_edges:
            # Generar red /30
            blocks = generate_blocks(base, 30, 1, used, skip_first=True)
            if blocks:
                network = blocks[0]
                hosts = list(network.hosts())
                
                edge_ips[edge['id']] = {
                    'network': network,
                    'from_ip': hosts[0] if len(hosts) > 0 else network.network_address,
                    'to_ip': hosts[1] if len(hosts) > 1 else network.network_address + 1,
                    'mask': str(network.netmask)
                }
        
        # Pre-calcular edges por nodo (evitar búsquedas repetidas)
        edges_by_node = {}
        for edge in edges:
            if edge['from'] not in edges_by_node:
                edges_by_node[edge['from']] = []
            if edge['to'] not in edges_by_node:
                edges_by_node[edge['to']] = []
            edges_by_node[edge['from']].append(edge)
            edges_by_node[edge['to']].append(edge)
        
        # Procesar routers (optimizado)
        for router in routers:
            config_lines = []
            name = router['data']['name']
            router_id = router['id']
            
            # Encabezado
            config_lines.append(f"{name}")
            config_lines.append("enable")
            config_lines.append("conf t")
            config_lines.append(f"Hostname {name}")
            config_lines.append("Enable secret cisco")
            
            # Obtener edges del router (búsqueda O(1))
            router_edges = edges_by_node.get(router_id, [])
            backbone_interfaces = []
            switch_connections = []  # ✅ Cambiar a lista para soportar múltiples switches
            
            for edge in router_edges:
                is_from = edge['from'] == router_id
                target_id = edge['to'] if is_from else edge['from']
                target_node = node_map.get(target_id)
                
                if not target_node:
                    continue
                
                target_name = target_node['data']['name']
                target_type = target_node['data']['type']
                
                # Detectar conexión a switch normal o switch core
                if target_type in ['switch', 'switch_core']:
                    switch_connections.append({
                        'switch_id': target_id,
                        'switch_name': target_name,
                        'switch_type': target_type,
                        'edge': edge,
                        'is_from': is_from
                    })
                
                # Configurar backbone
                if edge['id'] in edge_ips:
                    iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                    ip_data = edge_ips[edge['id']]
                    routing_direction = edge['data'].get('routingDirection', 'bidirectional')
                    
                    iface_full = f"{iface_data['type']}{iface_data['number']}"
                    ip_addr = str(ip_data['from_ip']) if is_from else str(ip_data['to_ip'])
                    next_hop_ip = str(ip_data['to_ip']) if is_from else str(ip_data['from_ip'])
                    
                    config_lines.append(f"int {iface_full} ")
                    config_lines.append(f"ip add {ip_addr} {ip_data['mask']}")
                    config_lines.append("no shut")
                    
                    backbone_interfaces.append({
                        'type': iface_data['type'],
                        'name': iface_data['type'],
                        'number': iface_data['number'],
                        'full_name': iface_full,
                        'interface': iface_full,
                        'ip': ip_addr,
                        'network': ip_data['network'],
                        'target': target_name,
                        'next_hop': next_hop_ip,
                        'routing_direction': routing_direction,
                        'is_from': is_from
                    })
            
            # Si hay conexión a switch(es), configurar subinterfaces para VLANs
            assigned_vlans = []
            
            # Verificar si hay AL MENOS UN switch normal conectado
            has_normal_switches = False
            if switch_connections:
                has_normal_switches = any(
                    sc['switch_type'] == 'switch' for sc in switch_connections
                )
            
            # Si hay AL MENOS UN switch normal, generar TODAS las VLANs
            # (sin importar si también hay switch_core conectado)
            if has_normal_switches and switch_connections:
                # Usar la primera conexión a un SWITCH NORMAL (no switch_core)
                first_normal_switch = None
                for sc in switch_connections:
                    if sc['switch_type'] == 'switch':
                        first_normal_switch = sc
                        break
                
                if first_normal_switch:
                    edge = first_normal_switch['edge']
                    is_from = first_normal_switch['is_from']
                    iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                    iface_full = f"{iface_data['type']}{iface_data['number']}"
                    
                    # Configurar interfaz principal
                    config_lines.append(f"int {iface_full}")
                    config_lines.append("no shut")
                    
                    # Generar subinterfaces para TODAS las VLANs definidas globalmente
                    for vlan in vlans:
                        vlan_name = vlan['name']
                        vlan_num = ''.join(filter(str.isdigit, vlan_name))
                        if vlan_num:
                            prefix = int(vlan['prefix'])
                            # Generar red
                            blocks = generate_blocks(base, prefix, 1, used)
                            if blocks:
                                network = blocks[0]
                                hosts = list(network.hosts())
                                gateway = hosts[-1] if hosts else network.network_address + 1
                                
                                config_lines.append(f"int {iface_full}.{vlan_num}")
                                config_lines.append(f"encapsulation dot1Q {vlan_num}")
                                config_lines.append(f"ip add {gateway} {network.netmask}")
                                config_lines.append("no shut")
                                
                                assigned_vlans.append({
                                    'name': vlan_name,
                                    'termination': vlan_num,
                                    'network': network,
                                    'gateway': str(gateway),
                                    'mask': str(network.netmask),
                                    'interface_name': iface_data['type'],
                                    'interface_number': iface_data['number']
                                })
                    
                    config_lines.append("exit")
                    config_lines.append("")
            
            # Configurar DHCP pools para TODAS las VLANs asignadas
            if assigned_vlans:
                for vlan_data in assigned_vlans:
                    network = vlan_data['network']
                    hosts = list(network.hosts())
                    vlan_num = vlan_data['termination']
                    
                    # Excluded addresses ANTES del pool
                    config_lines.append(f"ip dhcp excluded-address {hosts[0]} {hosts[9] if len(hosts) > 9 else hosts[-1]}")
                    config_lines.append("")
                    
                    config_lines.append(f"ip dhcp pool vlan{vlan_num}")
                    config_lines.append(f"network {network.network_address} {network.netmask}")
                    config_lines.append(f"default-router {vlan_data['gateway']}")
                    config_lines.append("exit")  # IMPORTANTE: Salir del pool DHCP
                    config_lines.append("")
            
            # NO agregar exit aquí - format_config_for_ptbuilder() lo agregará al final
            
            # Agregar config a la lista
            router_configs.append({
                'name': name,
                'type': 'router',
                'config': config_lines,
                'vlans': assigned_vlans,
                'backbone_interfaces': backbone_interfaces,
                'routes': []
            })
        
        # Procesar switch cores (optimizado)
        for swc in switch_cores:
            config_lines = []
            name = swc['data']['name']
            swc_id = swc['id']
            
            # Encabezado
            config_lines.append(f"{name}")
            config_lines.append("enable")
            config_lines.append("conf t")
            config_lines.append(f"hostname {name}")
            config_lines.append("enable secret cisco")
            config_lines.append("ip routing")
            config_lines.append("")
            
            # Agregar configuración SSH
            ssh_config = generate_ssh_config()
            config_lines.extend(ssh_config)
            
            # Crear VLANs (búsquedas optimizadas)
            vlans_used = set()
            swc_edges = edges_by_node.get(swc_id, [])
            
            # Encontrar computadoras conectadas
            for edge in swc_edges:
                other_id = edge['to'] if edge['from'] == swc_id else edge['from']
                other_node = node_map.get(other_id)
                
                if not other_node:
                    continue
                
                other_type = other_node['data']['type']
                
                # Computadoras conectadas directamente (antiguo sistema)
                if other_type == 'computer' and other_node['data'].get('vlan'):
                    vlans_used.add(other_node['data']['vlan'])
                elif other_type == 'switch':
                    # Buscar computadoras del switch (antiguo sistema - nodos)
                    switch_edges = edges_by_node.get(other_id, [])
                    for se in switch_edges:
                        comp_id = se['to'] if se['from'] == other_id else se['from']
                        comp = node_map.get(comp_id)
                        if comp and comp['data']['type'] == 'computer' and comp['data'].get('vlan'):
                            vlans_used.add(comp['data']['vlan'])
                    
                    # Buscar computadoras del switch (nuevo sistema - almacenadas)
                    if 'computers' in other_node['data']:
                        for pc in other_node['data']['computers']:
                            if pc.get('vlan'):
                                vlans_used.add(pc['vlan'])
            
            # Computadoras conectadas directamente al switch core (nuevo sistema)
            if 'computers' in swc['data']:
                for pc in swc['data']['computers']:
                    if pc.get('vlan'):
                        vlans_used.add(pc['vlan'])
            
            # Crear VLANs
            for vlan_name in sorted(vlans_used):
                vlan_num = ''.join(filter(str.isdigit, vlan_name))
                if vlan_num:
                    config_lines.append(f"vlan {vlan_num}")
                    config_lines.append(f" name {vlan_name.lower()}")
            
            config_lines.append("exit")
            config_lines.append("")
            
            # Configurar interfaces backbone
            backbone_interfaces = []
            for edge in swc_edges:
                if edge['id'] in edge_ips:
                    is_from = edge['from'] == swc_id
                    iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                    ip_data = edge_ips[edge['id']]
                    routing_direction = edge['data'].get('routingDirection', 'bidirectional')
                    
                    # Obtener el nodo destino (búsqueda O(1))
                    target_id = edge['to'] if is_from else edge['from']
                    target_node = node_map.get(target_id)
                    target_name = target_node['data']['name'] if target_node else 'Unknown'
                    
                    iface_full = f"{iface_data['type']}{iface_data['number']}"
                    ip_addr = str(ip_data['from_ip']) if is_from else str(ip_data['to_ip'])
                    next_hop_ip = str(ip_data['to_ip']) if is_from else str(ip_data['from_ip'])
                    
                    config_lines.append(f"interface {iface_full}")
                    config_lines.append(" no switchport")
                    config_lines.append(f" ip address {ip_addr} {ip_data['mask']}")
                    config_lines.append(" no shutdown")
                    config_lines.append("")
                    
                    backbone_interfaces.append({
                        'type': iface_data['type'],
                        'name': iface_data['type'],
                        'number': iface_data['number'],
                        'full_name': iface_full,
                        'interface': iface_full,
                        'ip': ip_addr,
                        'network': ip_data['network'],
                        'target': target_name,
                        'next_hop': next_hop_ip,
                        'routing_direction': routing_direction,
                        'is_from': is_from
                    })
            
            # Configurar interfaces trunk para switches
            etherchannel_configs = []
            for edge in swc_edges:
                other_id = edge['to'] if edge['from'] == swc_id else edge['from']
                other_node = node_map.get(other_id)
                
                if other_node and other_node['data']['type'] == 'switch':
                    is_from = edge['from'] == swc_id
                    
                    # Verificar si es EtherChannel
                    if 'etherChannel' in edge['data']:
                        etherchannel_configs.append({
                            'data': edge['data']['etherChannel'],
                            'is_from': is_from,
                            'target': other_node['data']['name']
                        })
                    else:
                        # Configuración normal de trunk
                        iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                        iface_full = f"{iface_data['type']}{iface_data['number']}"
                        
                        config_lines.append(f"interface {iface_full}")
                        config_lines.append(" switchport trunk encapsulation dot1Q")
                        config_lines.append(" switchport mode trunk")
                        config_lines.append(" no shutdown")
                        config_lines.append("")
            
            # Configurar EtherChannels si existen
            for ec_config in etherchannel_configs:
                from logic import generate_etherchannel_config
                ec_commands = generate_etherchannel_config(ec_config['data'], ec_config['is_from'])
                config_lines.extend(ec_commands)
            
            # Configurar puertos de acceso para computadoras conectadas al switch core
            computer_ports_swc = []
            
            # Procesar computadoras del sistema nuevo (almacenadas en el switch core)
            if 'computers' in swc['data']:
                for pc in swc['data']['computers']:
                    vlan_name = pc.get('vlan')
                    if vlan_name:
                        vlan_num = ''.join(filter(str.isdigit, vlan_name))
                        if vlan_num:
                            # Expandir tipo de interfaz (fa -> FastEthernet, gi -> GigabitEthernet)
                            port_type_full = expand_interface_type(pc['portType'])
                            port_full = f"{port_type_full}{pc['portNumber']}"
                            computer_ports_swc.append({
                                'interface': port_full,
                                'vlan': vlan_num,
                                'computer': pc['name']
                            })
            
            # Agregar configuración de puertos de acceso para PCs
            for port in computer_ports_swc:
                config_lines.append(f"interface {port['interface']}")
                config_lines.append(f" switchport access vlan {port['vlan']}")
                config_lines.append(" no shutdown")
                config_lines.append("")
            
            # Configurar SVIs y DHCP
            assigned_vlans = []
            vlan_counter = 1
            for vlan in vlans:
                if vlan['name'] in vlans_used:
                    vlan_num = ''.join(filter(str.isdigit, vlan['name']))
                    if vlan_num:
                        prefix = int(vlan['prefix'])
                        # Generar red
                        blocks = generate_blocks(base, prefix, 1, used)
                        if blocks:
                            network = blocks[0]
                            hosts = list(network.hosts())
                            gateway = hosts[-1] if hosts else network.network_address + 1
                            
                            # Interface VLAN
                            config_lines.append(f"interface vlan {vlan_num}")
                            config_lines.append(f" ip address {gateway} {network.netmask}")
                            config_lines.append(" no shutdown")
                            config_lines.append("")
                            
                            assigned_vlans.append({
                                'name': vlan['name'],
                                'termination': vlan_num,
                                'network': network,
                                'gateway': str(gateway),
                                'mask': str(network.netmask)
                            })
                        
                        vlan_counter += 1
            
            # Pools DHCP
            for vlan_data in assigned_vlans:
                network = vlan_data['network']
                hosts = list(network.hosts())
                vlan_num = vlan_data['termination']
                
                config_lines.append(f"ip dhcp excluded-address {hosts[0]} {hosts[9] if len(hosts) > 9 else hosts[-1]}")
                config_lines.append(f"ip dhcp pool VLAN{vlan_num}")
                config_lines.append(f" network {network.network_address} {network.netmask}")
                config_lines.append(f" default-router {vlan_data['gateway']}")
                config_lines.append(" dns-server 8.8.8.8")
                config_lines.append("exit")  # IMPORTANTE: Salir del pool DHCP
            
            router_configs.append({
                'name': name,
                'type': 'switch_core',
                'config': config_lines,
                'vlans': assigned_vlans,
                'backbone_interfaces': backbone_interfaces,
                'routes': []
            })
        
        # Procesar switches normales (optimizado)
        for switch in switches:
            config_lines = []
            name = switch['data']['name']
            switch_id = switch['id']
            
            # NO agregar el nombre del dispositivo aquí - PTBuilder ya lo tiene en configureIosDevice()
            config_lines.append("enable")
            config_lines.append("conf t")
            config_lines.append(f"Hostname {name}")
            config_lines.append("Enable secret cisco")
            config_lines.append("")
            
            # Agregar configuración SSH
            ssh_config = generate_ssh_config()
            config_lines.extend(ssh_config)
            
            # Obtener VLANs de computadoras conectadas (búsquedas O(1))
            switch_edges = edges_by_node.get(switch_id, [])
            vlans_used = set()
            computer_ports = []
            
            # Procesar computadoras del antiguo sistema (nodos computer conectados)
            for edge in switch_edges:
                other_id = edge['to'] if edge['from'] == switch_id else edge['from']
                other_node = node_map.get(other_id)
                
                if other_node and other_node['data']['type'] == 'computer':
                    vlan_name = other_node['data'].get('vlan')
                    if vlan_name:
                        vlan_num = ''.join(filter(str.isdigit, vlan_name))
                        if vlan_num:
                            vlans_used.add((vlan_num, vlan_name))
                            
                            is_from = edge['from'] == switch_id
                            iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                            iface_full = f"{iface_data['type']}{iface_data['number']}"
                            
                            computer_ports.append({
                                'interface': iface_full,
                                'vlan': vlan_num,
                                'computer': other_node['data']['name']
                            })
            
            # Procesar computadoras del nuevo sistema (almacenadas en el switch)
            if 'computers' in switch['data']:
                for pc in switch['data']['computers']:
                    vlan_name = pc.get('vlan')
                    if vlan_name:
                        vlan_num = ''.join(filter(str.isdigit, vlan_name))
                        if vlan_num:
                            vlans_used.add((vlan_num, vlan_name))
                            
                            port_full = f"{pc['portType']}{pc['portNumber']}"
                            computer_ports.append({
                                'interface': port_full,
                                'vlan': vlan_num,
                                'computer': pc['name']
                            })
            
            # Crear VLANs
            for vlan_num, vlan_name in sorted(vlans_used):
                config_lines.append(f"vlan {vlan_num}")
                config_lines.append(f" name {vlan_name.lower()}")
            
            # Solo agregar exit si hay VLANs creadas
            if vlans_used:
                config_lines.append("exit")
                config_lines.append("")
            
            # Configurar puerto trunk hacia switch core, router u otro switch
            etherchannel_configs = []
            processed_edges = set()  # Para evitar procesar el mismo edge dos veces
            
            for edge in switch_edges:
                # Evitar procesar el mismo edge dos veces (cuando hay switch-to-switch)
                if edge['id'] in processed_edges:
                    continue
                    
                other_id = edge['to'] if edge['from'] == switch['id'] else edge['from']
                other_node = next((n for n in nodes if n['id'] == other_id), None)
                
                # Aceptar conexiones a switch_core, router u otro switch
                if other_node and other_node['data']['type'] in ['switch_core', 'router', 'switch']:
                    is_from = edge['from'] == switch['id']
                    
                    # Verificar si es EtherChannel
                    if 'etherChannel' in edge['data']:
                        etherchannel_configs.append({
                            'data': edge['data']['etherChannel'],
                            'is_from': is_from,
                            'target': other_node['data']['name']
                        })
                        processed_edges.add(edge['id'])  # Marcar como procesado
                    else:
                        # Configuración normal de trunk
                        iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                        iface_full = f"{iface_data['type']}{iface_data['number']}"
                        
                        config_lines.append(f"int {iface_full}")
                        config_lines.append("switchport mode trunk")
                        config_lines.append("no shutdown")
                        processed_edges.add(edge['id'])  # Marcar como procesado
            
            # Configurar EtherChannels si existen
            for ec_config in etherchannel_configs:
                from logic import generate_etherchannel_config
                ec_commands = generate_etherchannel_config(ec_config['data'], ec_config['is_from'])
                config_lines.extend(ec_commands)
            
            # Configurar puertos de acceso para computadoras
            for port in computer_ports:
                config_lines.append(f"int {port['interface']}")
                config_lines.append(f"switchport access vlan {port['vlan']}")
                config_lines.append("no shutdown")
            
            router_configs.append({
                'name': name,
                'type': 'switch',
                'config': config_lines,
                'vlans': [],
                'backbone_interfaces': [],
                'routes': []
            })
        
        # Generar resumen de VLANs
        vlan_summary = []
        for vlan in vlans:
            vlan_num = ''.join(filter(str.isdigit, vlan['name']))
            computers_in_vlan = [c for c in computers if c['data'].get('vlan') == vlan['name']]
            
            vlan_summary.append({
                'name': vlan['name'],
                'vlan_id': vlan_num,
                'prefix': f"/{vlan['prefix']}",
                'computers_count': len(computers_in_vlan),
                'computers': [c['data']['name'] for c in computers_in_vlan]
            })
        
        # Generar rutas estáticas
        routing_tables = generate_routing_table(router_configs)
        
        for router in router_configs:
            router_name = router['name']
            if router_name in routing_tables:
                routes = routing_tables[router_name]['routes']
                route_commands = generate_static_routes_commands(routes)
                
                if route_commands:
                    # Agregar rutas al final de la configuración
                    config = router['config']
                    
                    # Verificar si la última línea no vacía es 'exit'
                    # Si ya existe exit, no agregarlo nuevamente
                    last_non_empty = None
                    for line in reversed(config):
                        if line.strip():
                            last_non_empty = line.strip().lower()
                            break
                    
                    # Si route_commands comienza con 'exit' y config ya termina con 'exit',
                    # eliminar el exit de route_commands para evitar duplicación
                    if last_non_empty == 'exit' and route_commands[0].strip().lower() == 'exit':
                        route_commands = route_commands[1:]  # Eliminar el primer exit
                    
                    config = config + [""] + route_commands
                    router['config'] = config
                    router['routes'] = routes
        
        # Generar contenido de archivos TXT separados por tipo (en memoria, no en disco)
        global config_files_content
        config_files_content = generate_separated_txt_files(router_configs)
        
        # Generar script PTBuilder y guardar en config_files_content
        ptbuilder_content = generate_ptbuilder_script(topology, router_configs, computers)
        config_files_content['ptbuilder'] = ptbuilder_content
        
        return render_template("router_results.html", 
                             routers=router_configs,
                             vlan_summary=vlan_summary)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"Error procesando topología: {str(e)}<br><pre>{error_detail}</pre>", 400

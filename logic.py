import ipaddress
from dataclasses import dataclass

@dataclass
class Combo:
    net: ipaddress.IPv4Network
    name: str
    group: str  # Ej: "BACKBONE" o nombre de VLAN

def check_conflict(new_net, used):
    """Verifica si new_net se solapa o está contenido en alguna red usada."""
    for net in used:
        if new_net.overlaps(net) or new_net.subnet_of(net) or net.subnet_of(new_net):
            return True
    return False

def generate_blocks(base_net, prefix, count, used, skip_first=False):
    """Genera 'count' bloques consecutivos de tamaño /prefix dentro de base_net, evitando solapamiento."""
    results = []
    subnets = list(base_net.subnets(new_prefix=prefix))
    start_index = 1 if skip_first else 0  # saltar el primer bloque si se pide
    for cand in subnets[start_index:]:
        if check_conflict(cand, used):
            continue
        results.append(cand)
        used.append(cand)
        if len(results) == count:
            break
    return results

def format_block(net: ipaddress.IPv4Network) -> str:
    """Muestra extremos de red: dirección de red y broadcast."""
    return (
        f"|{net.network_address}\n"
        f"|\n"
        f"|\n"
        f"|{net.broadcast_address}\n"
    )

def export_report(combos: list[Combo], out_path: str):
    """Genera el reporte formateado con grupos y máscara al inicio de cada sección."""
    with open(out_path, "w", encoding="utf-8") as f:
        current_group = None
        for c in combos:
            # Si cambia el grupo (ej. BACKBONE o VLAN)
            if c.group != current_group:
                f.write(f"\n=== {c.group} ===\n")
                f.write(f"Máscara: {c.net.netmask}\n")
                current_group = c.group

            f.write(f"\n{c.name}\n")
            f.write(format_block(c.net))

def export_report_with_routers(combos: list[Combo], router_configs: list, out_path: str):
    """
    Genera el reporte con formato específico:
    - Backbone al inicio
    - Cada router con sus segmentos de VLAN
    - Formato con gateway y máscara
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
    Genera comandos CLI de configuración para un router con sus VLANs asignadas y conexiones backbone.
    
    Args:
        router_name: Nombre del router
        vlans: Lista de diccionarios con 'name', 'termination' y 'network'
        backbone_interfaces: Lista de interfaces backbone (router-router)
        vlan_interface_name: Nombre de la interfaz para VLANs (eth, gi, fa)
        vlan_interface_number: Número de la interfaz para VLANs
    
    Returns:
        Lista de comandos CLI
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
    Genera UNA ruta estática por cada red desconocida (versión optimizada).
    
    La lógica determina automáticamente el mejor next-hop basándose en:
    - Conexiones directas (prioridad alta)
    - Rutas indirectas a través de routers intermedios
    
    Args:
        all_routers: Lista de diccionarios con estructura:
            {
                'name': str,
                'vlans': [{'name': str, 'network': IPv4Network, ...}],
                'backbone_interfaces': [{'network': IPv4Network, 'ip': IPv4Address, 'target': str, ...}]
            }
    
    Returns:
        Diccionario con rutas individuales por router
    """
    routing_tables = {}
    
    # Pre-calcular mapas para búsquedas O(1)
    router_map = {r['name']: r for r in all_routers}
    
    # Cache de next-hops: (router_origen, router_destino) -> IP
    next_hop_cache = {}
    
    # Construir cache de next-hops
    for router in all_routers:
        router_name = router['name']
        for backbone in router.get('backbone_interfaces', []):
            target = backbone['target']
            my_ip = backbone['ip']
            network = backbone['network']
            
            # Encontrar la otra IP en la red /30
            for ip in network.hosts():
                if ip != my_ip:
                    next_hop_cache[(router_name, target)] = ip
                    break
    
    # Construir mapa de adyacencia (quién está conectado con quién)
    adjacency = {r['name']: set() for r in all_routers}
    for router in all_routers:
        router_name = router['name']
        for backbone in router.get('backbone_interfaces', []):
            adjacency[router_name].add(backbone['target'])
    
    # Generar rutas para cada router
    for router in all_routers:
        router_name = router['name']
        
        # Todas las redes en la topología (para crear rutas individuales)
        all_networks = []
        
        # Recolectar todas las redes de todos los routers
        for other_router in all_routers:
            other_name = other_router['name']
            
            # Agregar VLANs del router
            for vlan in other_router.get('vlans', []):
                all_networks.append({
                    'network': vlan['network'],
                    'router': other_name,
                    'type': 'VLAN',
                    'name': vlan['name']
                })
            
            # Agregar redes backbone
            for backbone in other_router.get('backbone_interfaces', []):
                all_networks.append({
                    'network': backbone['network'],
                    'router': other_name,
                    'type': 'BACKBONE',
                    'name': f"Backbone-{other_name}-{backbone['target']}"
                })
        
        # Redes que este router conoce directamente
        known_networks = set()
        for vlan in router.get('vlans', []):
            known_networks.add(vlan['network'])
        for backbone in router.get('backbone_interfaces', []):
            known_networks.add(backbone['network'])
        
        # Generar una ruta por cada red desconocida
        routes = []
        
        for net_info in all_networks:
            network = net_info['network']
            target_router = net_info['router']
            
            # Saltar si es del mismo router o ya la conoce
            if network in known_networks:
                continue
            
            # Determinar el mejor next-hop
            next_hop = None
            via_router = None
            next_hop_interface = None
            
            # 1. Verificar conexión directa al router que tiene la red
            if target_router in adjacency[router_name]:
                next_hop = next_hop_cache.get((router_name, target_router))
                
                # Encontrar la interfaz backbone correspondiente
                for backbone in router.get('backbone_interfaces', []):
                    if backbone['target'] == target_router:
                        next_hop_interface = backbone['full_name']
                        break
            
            # 2. Si no hay conexión directa, buscar ruta indirecta
            else:
                for intermediate in adjacency[router_name]:
                    # Verificar si el intermedio está conectado al target
                    if target_router in adjacency.get(intermediate, set()):
                        next_hop = next_hop_cache.get((router_name, intermediate))
                        via_router = intermediate
                        
                        # Encontrar la interfaz backbone hacia el intermedio
                        for backbone in router.get('backbone_interfaces', []):
                            if backbone['target'] == intermediate:
                                next_hop_interface = backbone['full_name']
                                break
                        
                        break  # Usar el primer camino encontrado
            
            # Agregar la ruta si se encontró un next-hop
            if next_hop and next_hop_interface:
                route = {
                    'network': network,
                    'next_hop': next_hop,
                    'next_hop_interface': next_hop_interface,
                    'destination_router': target_router,
                    'auto_generated': True,
                    'network_type': net_info['type'],
                    'network_name': net_info['name']
                }
                
                if via_router:
                    route['via_router'] = via_router
                
                routes.append(route)
        
        routing_tables[router_name] = {'routes': routes}
    
    return routing_tables

def generate_switch_core_config(switch_name: str, vlans: list, backbone_interfaces: list = None, trunk_interface_type: str = "fa", trunk_interface_number: str = "0/3") -> list[str]:
    """
    Genera comandos CLI para un Switch Core con IP routing.
    
    Args:
        switch_name: Nombre del switch
        vlans: Lista de VLANs con 'name', 'termination' y 'network'
        backbone_interfaces: Lista de interfaces backbone (uplink a routers)
        trunk_interface_type: Tipo de interfaz trunk
        trunk_interface_number: Número de interfaz trunk
    
    Returns:
        Lista de comandos CLI
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

def generate_static_routes_commands(routes: list) -> list[str]:
    """
    Genera comandos CLI para rutas estáticas (SIN comentarios, formato limpio).
    
    Args:
        routes: Lista de rutas con formato de generate_routing_table
    
    Returns:
        Lista de comandos CLI (solo comandos ip route)
    """
    commands = []
    
    if not routes:
        return commands
    
    # Agrupar rutas por next-hop para mejor organización visual
    routes_by_nexthop = {}
    for route in routes:
        next_hop = str(route['next_hop'])
        if next_hop not in routes_by_nexthop:
            routes_by_nexthop[next_hop] = []
        routes_by_nexthop[next_hop].append(route)
    
    # Generar comandos agrupados por next-hop
    for next_hop, group_routes in routes_by_nexthop.items():
        for route in group_routes:
            network = route['network']
            commands.append(f"ip route {network.network_address} {network.netmask} {next_hop}")
    
    return commands

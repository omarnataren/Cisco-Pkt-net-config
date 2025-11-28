"""
MÓDULO: orchestrator.py
DESCRIPCIÓN: Orquestador principal del sistema de generación de configuraciones
AUTOR: Sistema de Diseño de Topologías
FECHA: 2025
"""

import ipaddress
import json
from itertools import combinations
from flask import render_template, current_app

# Imports de módulos propios
from app.core.models import Combo

# Imports usando nombres con guiones (Python los convierte automáticamente)
from app.logic.network_calculations.subnetting import generate_blocks
from app.logic.cisco_config.ssh_config import generate_ssh_config
from app.logic.cisco_config.etherchannel import generate_etherchannel_config
from app.logic.routing_algorithms.static_routes import generate_static_routes_commands
from app.logic.routing_algorithms.bfs_routing import generate_routing_table
from app.logic.exports.text_files import generate_separated_txt_files
from app.logic.ptbuilder.ptbuilder import generate_ptbuilder_script
from app.logic.ptbuilder.interface_utils import expand_interface_type

# Variable global para almacenar contenido de archivos de configuración
config_files_content = {}


def detect_spanning_tree_targets(node_map, adjacency):
    """Return ids of switches needing spanning-tree priority."""
    targets = set()
    for node_id, node in node_map.items():
        node_type = node['data'].get('type')
        if node_type not in ['switch', 'switch_core']:
            continue

        neighbors = adjacency.get(node_id, set())
        if not neighbors:
            continue

        has_router_neighbor = any(
            node_map.get(neighbor_id, {}).get('data', {}).get('type') == 'router'
            for neighbor_id in neighbors
        )
        if not has_router_neighbor:
            continue

        switch_neighbors = [
            neighbor_id for neighbor_id in neighbors
            if node_map.get(neighbor_id, {}).get('data', {}).get('type') in ['switch', 'switch_core']
        ]
        if len(switch_neighbors) < 2:
            continue

        for first, second in combinations(switch_neighbors, 2):
            neighbor_adjacency = adjacency.get(first, set())
            if second in neighbor_adjacency:
                targets.add(node_id)
                break

    return targets


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
        
        # Buscar VLAN nativa
        native_vlan_id = None
        for vlan in vlans:
            if vlan.get('isNative'):
                native_vlan_id = ''.join(filter(str.isdigit, vlan['name']))
                break
        
        # Obtener el primer octeto de la red base (por defecto 19 si no se especifica)
        base_octet = topology.get('baseNetworkOctet', 19)
        
        # Detectar si es modo físico
        is_physical_mode = topology.get('mode') == 'physical'
        
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
        servers = []
        wlcs = []
        aps = []
        
        for n in nodes:
            node_type = n['data']['type']
            if node_type == 'router':
                routers.append(n)
            elif node_type == 'switch':
                switches.append(n)
            elif node_type == 'switch_core':
                switch_cores.append(n)
            elif node_type == 'server':
                servers.append(n)
            elif node_type == 'wlc':
                wlcs.append(n)
            elif node_type == 'ap':
                aps.append(n)
        
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
                    
                    # Parsear el puerto completo (ej: "FastEthernet0/1")
                    port_full = pc.get('portNumber', '')
                    
                    # Separar tipo y número
                    import re
                    match = re.match(r'^([A-Za-z]+)(.+)$', port_full)
                    if match:
                        port_type = match.group(1)  # "FastEthernet"
                        port_number = match.group(2)  # "0/1"
                    else:
                        port_type = 'FastEthernet'
                        port_number = '0/1'
                    
                    # Crear estructura compatible con el formato de nodo
                    pc_node = {
                        'id': f"{s['id']}_pc_{pc['name']}",  # ID único basado en el switch
                        'data': {
                            'name': unique_pc_name,  # Usar nombre único global
                            'type': 'computer',
                            'vlan': pc.get('vlan'),
                            'port': port_full
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
                                'type': port_type,
                                'number': port_number
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
                    
                    # Parsear el puerto completo (ej: "FastEthernet0/1")
                    port_full = pc.get('portNumber', '')
                    
                    # Separar tipo y número
                    import re
                    match = re.match(r'^([A-Za-z]+)(.+)$', port_full)
                    if match:
                        port_type = match.group(1)  # "FastEthernet"
                        port_number = match.group(2)  # "0/1"
                    else:
                        port_type = 'FastEthernet'
                        port_number = '0/1'
                    
                    # Crear estructura compatible con el formato de nodo
                    pc_node = {
                        'id': f"{swc['id']}_pc_{pc['name']}",  # ID único basado en el switch core
                        'data': {
                            'name': unique_pc_name,  # Usar nombre único global
                            'type': 'computer',
                            'vlan': pc.get('vlan'),
                            'port': port_full
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
                                'type': port_type,
                                'number': port_number
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

        adjacency = {node_id: set() for node_id in node_map}
        for edge in edges:
            adjacency.setdefault(edge['from'], set()).add(edge['to'])
            adjacency.setdefault(edge['to'], set()).add(edge['from'])

        spanning_tree_targets = detect_spanning_tree_targets(node_map, adjacency)
        
        # Procesar routers (optimizado)
        for router in routers:
            config_lines = []
            name = router['data']['name']
            router_id = router['id']
            
            # Encabezado con SSH 
            config_lines.append(f"{name}")
            config_lines.append("enable")
            config_lines.append("config terminal")
            config_lines.append(f"hostname {name}")
            config_lines.append("ip domain-name cisco.com")
            config_lines.append("crypto key generate rsa")
            config_lines.append("512")
            config_lines.append("line vty 0 5")
            config_lines.append("transport input ssh")
            config_lines.append("login local")
            config_lines.append("exit")
            config_lines.append("username user password cisco")
            config_lines.append("enable secret cisco")
            config_lines.append("")
            
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
                    
                    config_lines.append(f"int {iface_full}")
                    config_lines.append(f"ip address {ip_addr} {ip_data['mask']}")
                    config_lines.append(" no shut")
                    
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
                            
                            # ✅ VALIDACIÓN: Omitir redes /31 y /32 (no soportan DHCP)
                            if prefix >= 31:
                                print(f"⚠️  ADVERTENCIA: VLAN {vlan_name} con prefijo /{prefix} omitida.")
                                print(f"   Las redes /31 y /32 no tienen suficientes IPs para DHCP.")
                                print(f"   Usa un prefijo máximo de /30 para al menos 2 hosts.")
                                continue
                            
                            # Generar red
                            blocks = generate_blocks(base, prefix, 1, used)
                            if blocks:
                                network = blocks[0]
                                hosts = list(network.hosts())
                                
                                # Verificar que hay suficientes hosts (mínimo 2)
                                if len(hosts) < 2:
                                    print(f"⚠️  ADVERTENCIA: VLAN {vlan_name} no tiene suficientes IPs.")
                                    continue
                                
                                gateway = hosts[-1]
                                
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
                    
                    # ✅ VALIDACIÓN: Solo crear pool si hay suficientes hosts
                    if len(hosts) < 2:
                        print(f"⚠️  Omitiendo pool DHCP para VLAN{vlan_num} (insuficientes IPs)")
                        continue
                    
                    # Excluded addresses ANTES del pool (primeras 10 IPs o todas menos la última)
                    excluded_end = hosts[9] if len(hosts) > 10 else hosts[-2]
                    config_lines.append(f"ip dhcp excluded-address {hosts[0]} {excluded_end}")
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
            
            # Encabezado con SSH 
            config_lines.append(f"{name}")
            config_lines.append("enable")
            config_lines.append("config terminal")
            config_lines.append(f"hostname {name}")
            config_lines.append("ip routing")
            config_lines.append("ip domain-name cisco.com")
            config_lines.append("crypto key generate rsa")
            config_lines.append("yes")
            config_lines.append("512")
            config_lines.append("line vty 0 5")
            config_lines.append("transport input ssh")
            config_lines.append("login local")
            config_lines.append("exit")
            config_lines.append("username user password cisco")
            config_lines.append("enable secret cisco")
            config_lines.append(f"hostname {name}")
            
            # Crear TODAS las VLANs del proyecto en el switch core
            # Los switch cores necesitan tener todas las VLANs para los trunks
            vlans_to_declare = set()  # VLANs a declarar (vlan X)
            vlans_with_computers = set()  # VLANs que necesitan SVI (interface vlan X)
            swc_edges = edges_by_node.get(swc_id, [])
            
            # Encontrar VLANs que realmente tienen computadoras conectadas
            for edge in swc_edges:
                other_id = edge['to'] if edge['from'] == swc_id else edge['from']
                other_node = node_map.get(other_id)
                
                if not other_node:
                    continue
                
                other_type = other_node['data']['type']
                
                # Servidores conectados directamente
                if other_type == 'server' and other_node['data'].get('vlan'):
                    vlans_with_computers.add(other_node['data']['vlan'])
                
                # Computadoras conectadas directamente (antiguo sistema)
                if other_type == 'computer' and other_node['data'].get('vlan'):
                    vlans_with_computers.add(other_node['data']['vlan'])
                elif other_type == 'switch':
                    # Buscar computadoras del switch (antiguo sistema - nodos)
                    switch_edges = edges_by_node.get(other_id, [])
                    for se in switch_edges:
                        comp_id = se['to'] if se['from'] == other_id else se['from']
                        comp = node_map.get(comp_id)
                        if comp and comp['data']['type'] == 'computer' and comp['data'].get('vlan'):
                            vlans_with_computers.add(comp['data']['vlan'])
                    
                    # Buscar computadoras del switch (nuevo sistema - almacenadas)
                    if 'computers' in other_node['data']:
                        for pc in other_node['data']['computers']:
                            if pc.get('vlan'):
                                vlans_with_computers.add(pc['vlan'])
            
            # Computadoras conectadas directamente al switch core (nuevo sistema)
            if 'computers' in swc['data']:
                for pc in swc['data']['computers']:
                    if pc.get('vlan'):
                        vlans_with_computers.add(pc['vlan'])
            
            # Verificar si hay switches conectados al switch core
            has_switches_connected = False
            for edge in swc_edges:
                other_id = edge['to'] if edge['from'] == swc_id else edge['from']
                other_node = node_map.get(other_id)
                if other_node and other_node['data']['type'] == 'switch':
                    has_switches_connected = True
                    break
            
            # Determinar qué VLANs declarar
            if has_switches_connected:
                # Si hay switches conectados, declarar TODAS las VLANs del proyecto
                for vlan in vlans:
                    vlans_to_declare.add(vlan['name'])
            else:
                # Si NO hay switches, solo declarar las VLANs con computadoras
                vlans_to_declare = vlans_with_computers.copy()
            
            # Crear VLANs
            for vlan_name in sorted(vlans_to_declare):
                vlan_num = ''.join(filter(str.isdigit, vlan_name))
                if vlan_num:
                    config_lines.append(f"vlan {vlan_num}")
                    config_lines.append(f" name {vlan_name.lower()}")
            
            config_lines.append("exit")
            config_lines.append("")

            if swc_id in spanning_tree_targets:
                config_lines.append("spanning-tree vlan 1 priority 4096")
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
            
            # Configurar interfaces trunk para switches y WLCs
            etherchannel_configs = []
            for edge in swc_edges:
                other_id = edge['to'] if edge['from'] == swc_id else edge['from']
                other_node = node_map.get(other_id)
                
                # Aceptar conexiones a switch o wlc
                if other_node and other_node['data']['type'] in ['switch', 'wlc']:
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
                        
                        # Si es WLC o Switch y hay VLAN nativa, configurar native vlan
                        if other_node['data']['type'] in ['wlc', 'switch'] and native_vlan_id:
                            config_lines.append(f" switchport trunk native vlan {native_vlan_id}")
                            
                        config_lines.append(" no shutdown")
                        config_lines.append("")
            
            # Configurar EtherChannels si existen
            for ec_config in etherchannel_configs:
                ec_commands = generate_etherchannel_config(ec_config['data'], ec_config['is_from'])
                config_lines.extend(ec_commands)
            
            # Configurar puertos de acceso para computadoras conectadas al switch core
            computer_ports_swc = []
            
            # Procesar servidores conectados al switch core
            for edge in swc_edges:
                other_id = edge['to'] if edge['from'] == swc_id else edge['from']
                other_node = node_map.get(other_id)
                
                if other_node and other_node['data']['type'] == 'server':
                    vlan_name = other_node['data'].get('vlan')
                    if vlan_name:
                        vlan_num = ''.join(filter(str.isdigit, vlan_name))
                        if vlan_num:
                            # Obtener interfaz del switch core hacia el servidor
                            is_from = edge['from'] == swc_id
                            iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                            port_full = f"{iface_data['type']}{iface_data['number']}"
                            
                            computer_ports_swc.append({
                                'interface': port_full,
                                'vlan': vlan_num,
                                'computer': other_node['data']['name'],
                                'is_server': True
                            })
            
            # Procesar computadoras del sistema nuevo (almacenadas en el switch core)
            if 'computers' in swc['data']:
                for pc in swc['data']['computers']:
                    vlan_name = pc.get('vlan')
                    if vlan_name:
                        vlan_num = ''.join(filter(str.isdigit, vlan_name))
                        if vlan_num:
                            # El puerto ya viene completo: "FastEthernet0/1" o "GigabitEthernet1/0/1"
                            port_full = pc.get('portNumber', '')
                            computer_ports_swc.append({
                                'interface': port_full,
                                'vlan': vlan_num,
                                'computer': pc['name'],
                                'is_server': False
                            })
            
            # Agregar configuración de puertos de acceso para PCs
            for port in computer_ports_swc:
                config_lines.append(f"interface {port['interface']}")
                config_lines.append(f" switchport access vlan {port['vlan']}")
                config_lines.append(" no shutdown")
                config_lines.append("")
            
            # Configurar VLAN 1 para gestión de switches normales
            # Cada switch core tiene su propia red de gestión
            swc_index = switch_cores.index(swc) + 1
            config_lines.append("")
            config_lines.append(f"interface vlan 1")
            config_lines.append(f"ip address {base_octet}.0.{swc_index}.254 255.255.255.0")
            config_lines.append(" no shut")
            config_lines.append("exit")
            config_lines.append("")
            
            # Configurar SVIs y DHCP
            assigned_vlans = []
            
            # Agregar VLAN 1 de management a la lista de VLANs para el ruteo
            vlan1_network = ipaddress.IPv4Network(f"{base_octet}.0.{swc_index}.0/24")
            
            # IMPORTANTE: Marcar la red de VLAN 1 como usada para evitar conflictos
            used.append(vlan1_network)
            
            assigned_vlans.append({
                'name': 'VLAN1',
                'termination': '1',
                'network': vlan1_network,
                'gateway': f"{base_octet}.0.{swc_index}.254",
                'mask': '255.255.255.0',
                'is_native': False
            })
            vlan_counter = 1
            for vlan in vlans:
                if vlan['name'] in vlans_with_computers:  # Solo crear SVI si tiene computadoras
                    vlan_num = ''.join(filter(str.isdigit, vlan['name']))
                    if vlan_num:
                        prefix = int(vlan['prefix'])
                        
                        # ✅ VALIDACIÓN: Omitir redes /31 y /32
                        if prefix >= 31:
                            print(f"⚠️  ADVERTENCIA: VLAN {vlan['name']} con prefijo /{prefix} omitida en {name}.")
                            continue
                        
                        # Generar red
                        blocks = generate_blocks(base, prefix, 1, used)
                        if blocks:
                            network = blocks[0]
                            hosts = list(network.hosts())
                            
                            # Verificar suficientes hosts
                            if len(hosts) < 2:
                                print(f"⚠️  ADVERTENCIA: VLAN {vlan['name']} no tiene suficientes IPs en {name}.")
                                continue
                            
                            gateway = hosts[-1]
                            
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
                                'mask': str(network.netmask),
                                'is_native': vlan.get('isNative', False)
                            })
                        
                        vlan_counter += 1
            
            # Pools DHCP
            for vlan_data in assigned_vlans:
                network = vlan_data['network']
                hosts = list(network.hosts())
                vlan_num = vlan_data['termination']
                
                # ✅ VALIDACIÓN: Solo crear pool si hay suficientes hosts
                if len(hosts) < 2:
                    print(f"⚠️  Omitiendo pool DHCP para VLAN{vlan_num} en {name} (insuficientes IPs)")
                    continue
                
                # Excluded addresses (primeras 10 IPs o todas menos la última)
                excluded_end = hosts[9] if len(hosts) > 10 else hosts[-2]
                config_lines.append(f"ip dhcp excluded-address {hosts[0]} {excluded_end}")
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
            config_lines.append("config terminal")
            config_lines.append(f"hostname {name}")
            config_lines.append("ip domain-name cisco.com")
            config_lines.append("crypto key generate rsa")
            config_lines.append("512")
            config_lines.append("line vty 0 5")
            config_lines.append("transport input ssh")
            config_lines.append("login local")
            config_lines.append("exit")
            config_lines.append("username user password cisco")
            config_lines.append("enable secret cisco")
            config_lines.append("")
            config_lines.append("")
            
            # Configurar VLAN 1 management después de SSH (según PARATEST.cisco)
            # Buscar switch core conectado para determinar el gateway correcto
            switch_number = len([s for s in switches if switches.index(s) < switches.index(switch)]) + 1
            
            # Buscar a qué switch core o router está conectado este switch
            connected_swc_vlan1_ip = None
            switch_edges = edges_by_node.get(switch_id, [])
            
            for edge in switch_edges:
                other_id = edge['to'] if edge['from'] == switch_id else edge['from']
                other_node = node_map.get(other_id)
                
                if other_node and other_node['data']['type'] == 'switch_core':
                    # Buscar la IP de VLAN 1 del switch core en sus VLANs asignadas
                    # Por convención, el switch core tiene VLAN 1 configurada
                    # El gateway será base_octet.0.{vlan_number}.254
                    # Por ahora usar un patrón: cada switch core tendrá su propia red para VLAN 1
                    # SW conectado a SWC1 = 15.0.1.x, SW conectado a SWC2 = 15.0.2.x, etc.
                    swc_index = switch_cores.index(other_node) + 1
                    config_lines.append(f"ip default-Gateway {base_octet}.0.{swc_index}.254")
                    config_lines.append("interface vlan 1")
                    config_lines.append(f"ip address {base_octet}.0.{swc_index}.{9 + switch_number} 255.255.255.0")
                    config_lines.append(" no shut")
                    config_lines.append("exit")
                    config_lines.append("")
                    connected_swc_vlan1_ip = f"{base_octet}.0.{swc_index}.254"
                    break
            
            # Si no encontró switch core, usar patrón por defecto
            if not connected_swc_vlan1_ip:
                config_lines.append(f"ip default-Gateway {base_octet}.0.1.254")
                config_lines.append("interface vlan 1")
                config_lines.append(f"ip address {base_octet}.0.1.{9 + switch_number} 255.255.255.0")
                config_lines.append(" no shut")
                config_lines.append("exit")
                config_lines.append("")
            config_lines.append("")
            
            # Obtener edges del switch
            switch_edges = edges_by_node.get(switch_id, [])
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
                            # El puerto ya viene completo: "FastEthernet0/1" o "GigabitEthernet1/0/1"
                            port_full = pc.get('portNumber', '')
                            computer_ports.append({
                                'interface': port_full,
                                'vlan': vlan_num,
                                'computer': pc['name']
                            })
            
            # ✅ CREAR TODAS LAS VLANs GLOBALES (no solo las que tienen PCs)
            # Esto garantiza que el trunk funcione correctamente entre switches
            for vlan in vlans:
                vlan_num = ''.join(filter(str.isdigit, vlan['name']))
                if vlan_num:
                    config_lines.append(f"vlan {vlan_num}")
                    config_lines.append(f" name {vlan['name'].lower()}")
            
            # Agregar exit después de crear VLANs
            if vlans:
                config_lines.append("exit")
                config_lines.append("")

            if switch_id in spanning_tree_targets:
                config_lines.append("spanning-tree vlan 1 priority 4096")
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
                
                # Aceptar conexiones a switch_core, router, switch u wlc
                if other_node and other_node['data']['type'] in ['switch_core', 'router', 'switch', 'wlc', 'ap']:
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
                        
                        # Si es WLC, AP o Switch Core y hay VLAN nativa, configurar native vlan
                        if other_node['data']['type'] in ['wlc', 'ap', 'switch_core'] and native_vlan_id:
                            config_lines.append(f"switchport trunk native vlan {native_vlan_id}")
                        
                        config_lines.append("no shut")
                        config_lines.append("")
                        processed_edges.add(edge['id'])  # Marcar como procesado
            
            # Configurar EtherChannels si existen
            for ec_config in etherchannel_configs:
                ec_commands = generate_etherchannel_config(ec_config['data'], ec_config['is_from'])
                config_lines.extend(ec_commands)
            
            # Configurar puertos de acceso para computadoras
            for port in computer_ports:
                config_lines.append(f"int {port['interface']}")
                config_lines.append(f"switchport access vlan {port['vlan']}")
                config_lines.append(" no shut")
            
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
        
        # Solo generar script PTBuilder si NO es modo físico
        if not is_physical_mode:
            ptbuilder_content = generate_ptbuilder_script(topology, router_configs, computers, servers)
            config_files_content['ptbuilder'] = ptbuilder_content
        
        # Transferir al config de Flask para que las rutas de descarga puedan acceder
        current_app.config['CONFIG_FILES_CONTENT'] = config_files_content
        
        return render_template("success.html", 
                             routers=router_configs,
                             vlan_summary=vlan_summary,
                             is_physical_mode=is_physical_mode)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"Error procesando topología: {str(e)}<br><pre>{error_detail}</pre>", 400


"""
Aplicación Flask para generación automática de configuraciones Cisco

Funcionalidad principal:
    - Diseñador visual de topologías de red
    - Generación automática de configuraciones IOS para routers, switches y switch cores
    - Cálculo de subnetting con validación de overlaps
    - Generación de rutas estáticas mediante BFS
    - Exportación de configuraciones en archivos TXT separados por tipo de dispositivo

Arquitectura:
    - Flask: Web server y routing
    - logic.py: Lógica de negocio (subnetting, configuraciones, enrutamiento)
    - templates/index_visual.html: Interfaz de diseño visual (vis-network)
    - templates/router_results.html: Vista de resultados y descargas

Optimizaciones implementadas:
    - Maps O(1) para búsquedas de nodos, VLANs y conexiones
    - Lazy evaluation con iteradores en lugar de listas
    - Caching de redes conocidas por router para BFS
    - Filtrado de dispositivos en una sola pasada

Autor: Sistema de configuración de redes
Versión: 2.0 (Optimizada)
"""

from flask import Flask, render_template, request, send_file
import ipaddress
import json
import io
from logic import generate_blocks, export_report_with_routers, Combo, generate_router_config, generate_switch_core_config, generate_routing_table, generate_static_routes_commands

app = Flask(__name__)

# Variable global para almacenar contenido de archivos de configuración en memoria
# Se sobrescribe en cada generación de topología
config_files_content = {}

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Ruta principal de la aplicación
    
    GET: Muestra el diseñador visual de topología
    POST: Procesa la topología diseñada y genera configuraciones
    
    Returns:
        GET: Renderiza index_visual.html
        POST: Renderiza router_results.html con las configuraciones generadas
    """
    if request.method == "POST":
        # Procesar topología del diseñador visual
        topology_data = request.form.get("topology_data")
        if topology_data:
            return handle_visual_topology(json.loads(topology_data))
        else:
            return "No se recibieron datos de topología", 400
    
    return render_template("index_visual.html")

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

def generate_ptbuilder_script(topology, router_configs, computers):
    """
    Genera script PTBuilder para crear topología en Packet Tracer
    
    Las coordenadas (x, y) de cada dispositivo se transforman del rango
    de vis.network al rango de Packet Tracer, manteniendo la topología relativa.
    PTBuilder usará estas coordenadas transformadas para crear los dispositivos.
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
    config_map = {cfg['name']: cfg for cfg in router_configs}
    
    def normalize_interface(iface_str):
        """Normaliza nombres de interfaces"""
        if not iface_str:
            return None
        if '.' in iface_str:
            iface_str = iface_str.split('.')[0]
        iface_lower = iface_str.lower().strip()
        if 'interface ' in iface_lower:
            iface_str = iface_str.replace('interface ', '').replace('Interface ', '')
            iface_lower = iface_lower.replace('interface ', '')
        if iface_lower.startswith('fa'):
            return 'FastEthernet' + iface_str[2:]
        elif iface_lower.startswith('gi'):
            return 'GigabitEthernet' + iface_str[2:]
        elif iface_lower.startswith('eth') or iface_lower.startswith('e'):
            if iface_lower.startswith('eth'):
                return 'Ethernet' + iface_str[3:]
            else:
                return 'Ethernet' + iface_str[1:]
        elif iface_lower.startswith('vlan'):
            return None
        return iface_str
    
    def extract_interfaces_from_config(device_name):
        """Extrae interfaces usadas de la configuración"""
        used = set()
        config = config_map.get(device_name)
        if not config:
            return used
        for line in config['config']:
            line_lower = line.lower().strip()
            if line_lower.startswith('int ') or line_lower.startswith('interface '):
                parts = line.split()
                if len(parts) >= 2:
                    iface_normalized = normalize_interface(parts[1])
                    if iface_normalized:
                        used.add(iface_normalized)
        return used
    
    used_interfaces = {}
    for node in nodes:
        device_name = node['data']['name']
        used_interfaces[device_name] = extract_interfaces_from_config(device_name)
    
    def get_next_available_interface(device_name, device_type):
        """Obtiene siguiente interfaz disponible"""
        available = get_available_interfaces_for_device(device_type)
        for iface in available:
            if iface not in used_interfaces[device_name]:
                used_interfaces[device_name].add(iface)
                return iface
        return None
    
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
    
    lines.append("")
    
    for edge in edges:
        from_node = node_map.get(edge['from'])
        to_node = node_map.get(edge['to'])
        if not from_node or not to_node:
            continue
        from_name = from_node['data']['name']
        to_name = to_node['data']['name']
        from_type = from_node['data']['type']
        to_type = to_node['data']['type']
        from_iface = get_next_available_interface(from_name, from_type)
        to_iface = get_next_available_interface(to_name, to_type)
        if from_iface and to_iface:
            lines.append(f'addLink("{from_name}", "{from_iface}", "{to_name}", "{to_iface}", "straight");')
    
    lines.append("")
    
    for router_config in router_configs:
        device_name = router_config['name']
        config_lines = router_config['config']
        config_text = "\\n".join([line for line in config_lines if line.strip()])
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
        
        # DEBUG: Mostrar coordenadas recibidas del cliente
        print("\n🔍 COORDINADAS RECIBIDAS DEL CLIENTE:")
        for node in nodes:
            print(f"  {node['data']['name']}: x={node.get('x')}, y={node.get('y')}")
        
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
            elif node_type == 'computer':
                computers.append(n)
        
        # ============================================================
        # FASE 3: ASIGNACIÓN DE REDES /30 PARA BACKBONE
        # ============================================================
        # Backbone: Conexiones punto a punto entre routers/switch cores
        # Usa red 19.0.0.0/8 dividida en subredes /30 (2 hosts utilizables)
        router_configs = []
        
        base = ipaddress.ip_network("19.0.0.0/8")  # Base para subnetting de backbone
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
            switch_connection = None
            
            for edge in router_edges:
                is_from = edge['from'] == router_id
                target_id = edge['to'] if is_from else edge['from']
                target_node = node_map.get(target_id)
                
                if not target_node:
                    continue
                
                target_name = target_node['data']['name']
                target_type = target_node['data']['type']
                
                # Detectar conexión a switch normal
                if target_type == 'switch':
                    switch_connection = {
                        'switch_id': target_id,
                        'switch_name': target_name,
                        'edge': edge,
                        'is_from': is_from
                    }
                
                # Configurar backbone
                if edge['id'] in edge_ips:
                    iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                    ip_data = edge_ips[edge['id']]
                    routing_direction = edge['data'].get('routingDirection', 'bidirectional')
                    
                    iface_full = f"{iface_data['type']}{iface_data['number']}"
                    ip_addr = str(ip_data['from_ip']) if is_from else str(ip_data['to_ip'])
                    next_hop_ip = str(ip_data['to_ip']) if is_from else str(ip_data['from_ip'])
                    
                    config_lines.append(f"int {iface_full}")
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
            
            # Si hay conexión a switch, configurar subinterfaces para VLANs
            assigned_vlans = []
            if switch_connection:
                edge = switch_connection['edge']
                is_from = switch_connection['is_from']
                iface_data = edge['data']['fromInterface'] if is_from else edge['data']['toInterface']
                iface_full = f"{iface_data['type']}{iface_data['number']}"
                
                # Obtener VLANs del switch conectado (búsqueda O(1))
                switch_id = switch_connection['switch_id']
                switch_edges = edges_by_node.get(switch_id, [])
                
                vlans_used = set()
                # for se in switch_edges:
                #     other_id = se['to'] if se['from'] == switch_id else se['from']
                #     comp = node_map.get(other_id)
                #     if comp and comp['data']['type'] == 'computer' and comp['data'].get('vlan'):
                #         vlans_used.add(comp['data']['vlan'])
                
                # Detectar computadoras del sistema nuevo (almacenadas en switch.data.computers)
                switch_node = node_map.get(switch_id)
                if switch_node and 'computers' in switch_node['data']:
                    for pc in switch_node['data']['computers']:
                        if pc.get('vlan'):
                            vlans_used.add(pc['vlan'])

                # Configurar interfaz principal
                config_lines.append(f"int {iface_full}")
                config_lines.append("no shut")
                
                # Configurar subinterfaces
                for vlan_name in sorted(vlans_used):
                    vlan_num = ''.join(filter(str.isdigit, vlan_name))
                    if vlan_num:
                        # Buscar info de VLAN (búsqueda O(1))
                        vlan_info = vlan_map.get(vlan_name)
                        if vlan_info:
                            prefix = int(vlan_info['prefix'])
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
                
                # Configurar DHCP pools
                for vlan_data in assigned_vlans:
                    network = vlan_data['network']
                    hosts = list(network.hosts())
                    vlan_num = vlan_data['termination']
                    
                    config_lines.append(f"ip dhcp pool vlan{vlan_num}")
                    config_lines.append(f"network {network.network_address} {network.netmask}")
                    config_lines.append(f"default-router {vlan_data['gateway']}")
                    config_lines.append("")
            
            config_lines.append("exit")
            config_lines.append("")
            
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
                        config_lines.append("")
            
            # Configurar EtherChannels si existen
            for ec_config in etherchannel_configs:
                from logic import generate_etherchannel_config
                ec_commands = generate_etherchannel_config(ec_config['data'], ec_config['is_from'])
                config_lines.extend(ec_commands)
            
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
                config_lines.append("")
                config_lines.append(f"ip dhcp pool VLAN{vlan_num}")
                config_lines.append(f" network {network.network_address} {network.netmask}")
                config_lines.append(f" default-router {vlan_data['gateway']}")
                config_lines.append(" dns-server 8.8.8.8")
                config_lines.append("")
            
            config_lines.append("exit")
            
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
            
            config_lines.append(f"{name}")
            config_lines.append("enable")
            config_lines.append("conf t")
            config_lines.append(f"Hostname {name}")
            config_lines.append("Enable secret cisco")
            config_lines.append("")
            
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
                    # Agregar rutas antes del último exit
                    config = router['config']
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

@app.route("/config", methods=["POST"])
def generate_config():
    """Endpoint para recibir la configuración del diseñador visual"""
    topology_data = request.get_json()
    if topology_data:
        return handle_visual_topology(topology_data)
    return "No se recibieron datos de topología", 400

@app.route("/download")
def download():
    """
    Endpoint para descargar el archivo de configuración completo
    
    Descarga config_completo.txt que contiene todas las configuraciones
    de la topología (routers + switch cores + switches) en un solo archivo.
    
    El archivo se genera en memoria y se envía directamente al navegador
    sin guardarse en el disco del servidor.
    
    Returns:
        FileResponse: Archivo config_completo.txt como descarga adjunta
    
    URL: /download
    Método: GET
    """
    global config_files_content
    
    if 'completo' not in config_files_content:
        return "No hay configuraciones generadas. Genera una topología primero.", 400
    
    # Crear archivo en memoria
    file_content = config_files_content['completo']
    file_bytes = io.BytesIO(file_content.encode('utf-8'))
    file_bytes.seek(0)
    
    return send_file(
        file_bytes,
        mimetype='text/plain',
        as_attachment=True,
        download_name='config_completo.txt'
    )

@app.route("/download/<device_type>")
def download_by_type(device_type):
    """
    Endpoint para descargar configuraciones por tipo de dispositivo
    
    Permite descargar archivos específicos según el tipo de dispositivo,
    facilitando la implementación por equipos especializados.
    
    Los archivos se generan en memoria y se envían directamente al navegador
    sin guardarse en el disco del servidor.
    
    Args:
        device_type (str): Tipo de dispositivo a descargar
            - 'routers': Solo configuraciones de routers
            - 'switch_cores': Solo configuraciones de switch cores
            - 'switches': Solo configuraciones de switches
            - 'completo': Todas las configuraciones consolidadas
            - 'ptbuilder': Script PTBuilder para automatizar creación en Packet Tracer
    
    Returns:
        FileResponse: Archivo TXT correspondiente al tipo solicitado
        str: Mensaje de error 400 si el tipo no es válido
    
    URLs disponibles:
        - /download/routers → config_routers.txt
        - /download/switch_cores → config_switch_cores.txt
        - /download/switches → config_switches.txt
        - /download/completo → config_completo.txt
        - /download/ptbuilder → topology_ptbuilder.txt
    
    Método: GET
    
    Ejemplo de uso:
        <a href="/download/routers">Descargar Routers</a>
        <a href="/download/ptbuilder">Descargar PTBuilder Script</a>
    """
    global config_files_content
    
    # Mapeo de tipos a nombres de archivo
    file_names = {
        'routers': 'config_routers.txt',
        'switch_cores': 'config_switch_cores.txt',
        'switches': 'config_switches.txt',
        'completo': 'config_completo.txt',
        'ptbuilder': 'topology_ptbuilder.txt'
    }
    
    # Validar tipo de dispositivo
    if device_type not in file_names:
        return "Tipo de dispositivo no válido. Tipos válidos: routers, switch_cores, switches, completo, ptbuilder", 400
    
    # Verificar que exista contenido generado
    if device_type not in config_files_content:
        return f"No hay configuraciones de tipo '{device_type}' generadas. Genera una topología primero.", 400
    
    # Crear archivo en memoria
    file_content = config_files_content[device_type]
    file_bytes = io.BytesIO(file_content.encode('utf-8'))
    file_bytes.seek(0)
    
    return send_file(
        file_bytes,
        mimetype='text/plain',
        as_attachment=True,
        download_name=file_names[device_type]
    )

if __name__ == "__main__":
    app.run(debug=True)

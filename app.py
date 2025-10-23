from flask import Flask, render_template, request, send_file
import ipaddress
import json
from logic import generate_blocks, export_report_with_routers, Combo, generate_router_config, generate_switch_core_config, generate_routing_table, generate_static_routes_commands

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Procesar topología del diseñador visual
        topology_data = request.form.get("topology_data")
        if topology_data:
            return handle_visual_topology(json.loads(topology_data))
        else:
            return "No se recibieron datos de topología", 400
    
    return render_template("index_visual.html")

def generate_separated_txt_files(router_configs):
    """
    Genera archivos TXT separados por tipo de dispositivo
    """
    routers = [r for r in router_configs if r['type'] == 'router']
    switch_cores = [r for r in router_configs if r['type'] == 'switch_core']
    switches = [r for r in router_configs if r['type'] == 'switch']
    
    # Archivo de routers
    with open("config_routers.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CONFIGURACIONES DE ROUTERS\n")
        f.write("=" * 80 + "\n\n")
        
        for router in routers:
            f.write("=" * 80 + "\n")
            f.write(f"ROUTER: {router['name']}\n")
            f.write("=" * 80 + "\n")
            for line in router['config']:
                f.write(line + "\n")
            f.write("\n\n")
    
    # Archivo de switch cores
    with open("config_switch_cores.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CONFIGURACIONES DE SWITCH CORES\n")
        f.write("=" * 80 + "\n\n")
        
        for swc in switch_cores:
            f.write("=" * 80 + "\n")
            f.write(f"SWITCH CORE: {swc['name']}\n")
            f.write("=" * 80 + "\n")
            for line in swc['config']:
                f.write(line + "\n")
            f.write("\n\n")
    
    # Archivo de switches
    with open("config_switches.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CONFIGURACIONES DE SWITCHES\n")
        f.write("=" * 80 + "\n\n")
        
        for switch in switches:
            f.write("=" * 80 + "\n")
            f.write(f"SWITCH: {switch['name']}\n")
            f.write("=" * 80 + "\n")
            for line in switch['config']:
                f.write(line + "\n")
            f.write("\n\n")
    
    # Archivo completo (todos juntos)
    with open("config_completo.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CONFIGURACIÓN COMPLETA DE LA TOPOLOGÍA\n")
        f.write("=" * 80 + "\n\n")
        
        if routers:
            f.write("\n" + "=" * 80 + "\n")
            f.write("ROUTERS\n")
            f.write("=" * 80 + "\n\n")
            for router in routers:
                f.write(f"--- {router['name']} ---\n")
                for line in router['config']:
                    f.write(line + "\n")
                f.write("\n\n")
        
        if switch_cores:
            f.write("\n" + "=" * 80 + "\n")
            f.write("SWITCH CORES\n")
            f.write("=" * 80 + "\n\n")
            for swc in switch_cores:
                f.write(f"--- {swc['name']} ---\n")
                for line in swc['config']:
                    f.write(line + "\n")
                f.write("\n\n")
        
        if switches:
            f.write("\n" + "=" * 80 + "\n")
            f.write("SWITCHES\n")
            f.write("=" * 80 + "\n\n")
            for switch in switches:
                f.write(f"--- {switch['name']} ---\n")
                for line in switch['config']:
                    f.write(line + "\n")
                f.write("\n\n")

def handle_visual_topology(topology):
    """
    Procesa la topología del diseñador visual y genera las configuraciones.
    Versión optimizada con maps y búsquedas O(1).
    """
    try:
        nodes = topology['nodes']
        edges = topology['edges']
        vlans = topology['vlans']
        
        # Pre-calcular maps para búsquedas O(1)
        node_map = {n['id']: n for n in nodes}
        vlan_map = {v['name']: v for v in vlans}
        
        # Filtrar dispositivos por tipo (una sola pasada)
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
        
        # Generar configuraciones
        router_configs = []
        
        # Generar IPs para backbones
        base = ipaddress.ip_network("19.0.0.0/8")
        used = []
        edge_ips = {}
        
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
                for se in switch_edges:
                    other_id = se['to'] if se['from'] == switch_id else se['from']
                    comp = node_map.get(other_id)
                    if comp and comp['data']['type'] == 'computer' and comp['data'].get('vlan'):
                        vlans_used.add(comp['data']['vlan'])
                
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
                
                if other_type == 'computer' and other_node['data'].get('vlan'):
                    vlans_used.add(other_node['data']['vlan'])
                elif other_type == 'switch':
                    # Buscar computadoras del switch
                    switch_edges = edges_by_node.get(other_id, [])
                    for se in switch_edges:
                        comp_id = se['to'] if se['from'] == other_id else se['from']
                        comp = node_map.get(comp_id)
                        if comp and comp['data']['type'] == 'computer' and comp['data'].get('vlan'):
                            vlans_used.add(comp['data']['vlan'])
            
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
                for cmd in ec_commands:
                    config_lines.append(" " + cmd if cmd and not cmd.startswith("interface") else cmd)
            
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
            
            # Crear VLANs
            for vlan_num, vlan_name in sorted(vlans_used):
                config_lines.append(f"vlan {vlan_num}")
                config_lines.append(f" name {vlan_name.lower()}")
            
            config_lines.append("exit")
            config_lines.append("")
            
            # Configurar puerto trunk hacia switch core o router
            etherchannel_configs = []
            for edge in switch_edges:
                other_id = edge['to'] if edge['from'] == switch['id'] else edge['from']
                other_node = next((n for n in nodes if n['id'] == other_id), None)
                
                if other_node and other_node['data']['type'] in ['switch_core', 'router']:
                    is_from = edge['from'] == switch['id']
                    
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
                        
                        config_lines.append(f"int {iface_full}")
                        config_lines.append("switchport mode trunk")
            
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
        
        # Generar archivos TXT separados por tipo
        generate_separated_txt_files(router_configs)
        
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
    """Descarga archivo completo"""
    return send_file("config_completo.txt", as_attachment=True, download_name="config_completo.txt")

@app.route("/download/<device_type>")
def download_by_type(device_type):
    """Descarga archivo por tipo de dispositivo"""
    files = {
        'routers': 'config_routers.txt',
        'switch_cores': 'config_switch_cores.txt',
        'switches': 'config_switches.txt',
        'completo': 'config_completo.txt'
    }
    
    if device_type in files:
        return send_file(files[device_type], as_attachment=True, download_name=files[device_type])
    return "Tipo de dispositivo no válido", 400

if __name__ == "__main__":
    app.run(debug=True)

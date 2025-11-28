"""
MÓDULO: ptbuilder.py
DESCRIPCIÓN: Generador de scripts para Packet Tracer Builder
"""

from app.logic.ptbuilder.interface_utils import transform_coordinates_to_ptbuilder, expand_interface_range, format_config_for_ptbuilder


def get_cable_type(from_device_type, to_device_type):
    """
    Determina el tipo de cable según los dispositivos conectados.
    
    Reglas de cableado:
    - Cable directo (straight): Dispositivos de diferente tipo
      (router-switch, switch-pc, router-pc)
    - Cable cruzado (cross): Dispositivos del mismo tipo
      (router-router, switch-switch, pc-pc)
    
    Args:
        from_device_type: Tipo del dispositivo origen ('router', 'switch', 'switch_core', 'computer')
        to_device_type: Tipo del dispositivo destino
    
    Returns:
        str: 'straight' o 'cross'
    """
    # Normalizar tipos: switch y switch_core son equivalentes para cableado
    device_category = {
        'router': 'router',
        'switch': 'switch',
        'switch_core': 'switch',  # Switch core se comporta como switch en capa 2
        'computer': 'computer',
        'wlc': 'switch',  # WLC se comporta como switch en capa 2
        'server': 'computer',  # Server se comporta como computer
        'ap': 'switch'  # AP se comporta como switch en capa 2
    }
    
    from_category = device_category.get(from_device_type, from_device_type)
    to_category = device_category.get(to_device_type, to_device_type)
    
    # Si son del mismo tipo → cable cruzado
    if from_category == to_category:
        return 'cross'
    
    # Si son de diferente tipo → cable directo
    return 'straight'


def generate_ptbuilder_script(topology, router_configs, computers, servers=[]):
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
        'computer': 'PC-PT',
        'wlc': 'WLC-3504',
        'server': 'Server-PT',
        'ap': '3702i'
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
            
            # Determinar tipo de cable según dispositivos
            cable_type = get_cable_type(from_node['data']['type'], to_node['data']['type'])
            
            # Generar un addLink por cada par de interfaces del bundle
            for from_if, to_if in zip(from_interfaces, to_interfaces):
                lines.append(f'addLink("{from_name}", "{from_if}", "{to_name}", "{to_if}", "{cable_type}");')
                print(f"   ✅ Cable generado ({cable_type}): {from_if} ↔ {to_if}")
        
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
            
            # Determinar tipo de cable según dispositivos conectados
            cable_type = get_cable_type(from_node['data']['type'], to_node['data']['type'])
            print(f"   Tipo de cable: {cable_type} ({from_node['data']['type']} → {to_node['data']['type']})")
            
            lines.append(f'addLink("{from_name}", "{from_iface}", "{to_name}", "{to_iface}", "{cable_type}");')
        else:
            print(f"⚠️ Advertencia: Conexión sin interfaces definidas entre {from_name} y {to_name}")
    
    lines.append("")
    # Generar configuraciones para cada dispositivo (routers, switches, switch cores)
    for router_config in router_configs:
        device_name = router_config['name']
        config_lines = router_config['config']
        
        # Reformatear configuración para PTBuilder
        formatted_config = format_config_for_ptbuilder(config_lines)
        
        # Convertir a string con \n como separador
        # IMPORTANTE: NO filtrar con line.strip() - mantener TODAS las líneas con su indentación
        config_text = "\\n".join(formatted_config)
        config_text = config_text.replace('"', '\\"')
        lines.append(f'configureIosDevice("{device_name}", "{config_text}");')
    
    lines.append("")
    
    for computer in computers:
        pc_name = computer['data']['name']
        lines.append(f'configurePcIp("{pc_name}", true);')
        
    for server in servers:
        server_name = server['data']['name']
        lines.append(f'configurePcIp("{server_name}", true);')
    
    # Retornar contenido para descarga
    ptbuilder_content = "\n".join(lines)
    
    return ptbuilder_content


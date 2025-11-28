"""
MÓDULO: text_files.py
DESCRIPCIÓN: Generador de archivos TXT de configuración por tipo de dispositivo
"""


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
    
    # Contenido de archivo WLAN config
    wlan_content = []
    
    # Buscar VLAN nativa y generar configuración WLC
    # Agrupar por dispositivo (Router/Switch Core) para separar bloques
    for device in router_configs:
        if 'vlans' in device:
            # Encabezado del bloque del dispositivo
            wlan_content.append("=" * 40)
            wlan_content.append(f"BLOQUE: {device['name']}")
            wlan_content.append("=" * 40)
            wlan_content.append("")
            
            # Parte 1: Configuración WLC (solo si hay VLAN nativa en este dispositivo)
            wlc_counter = 1
            for vlan in device['vlans']:
                if vlan.get('is_native'):
                    network = vlan['network']
                    hosts = list(network.hosts())
                    # IP Address: una antes del gateway (gateway es hosts[-1])
                    wlan_ip = hosts[-2] if len(hosts) >= 2 else hosts[0]
                    
                    wlan_content.append(f"WLC{wlc_counter}") # Usar contador de WLC, no ID de VLAN
                    wlan_content.append(f"Ip Address: {wlan_ip}")
                    wlan_content.append(f"Subnet MASK: {network.netmask}")
                    wlan_content.append(f"Default Gateway: {vlan['gateway']}")
                    wlan_content.append("")
                    wlc_counter += 1

            # Parte 2: Resumen de todas las VLANs de este dispositivo
            for vlan in device['vlans']:
                network = vlan['network']
                hosts = list(network.hosts())
                first_ip = hosts[0] if hosts else "N/A"
                last_ip = hosts[-2] if len(hosts) > 1 else hosts[0]
                
                wlan_content.append(f"---{vlan['name']}---")
                wlan_content.append("Rango usable:")
                wlan_content.append(f"|{first_ip}")
                wlan_content.append("|")
                wlan_content.append("|")
                wlan_content.append(f"|{last_ip}")
                wlan_content.append(f"Gateway{vlan['gateway']}")
                wlan_content.append(f"Máscara: {network.netmask}")
                wlan_content.append("")
            
            wlan_content.append("") # Espacio entre bloques de dispositivos
    
    files_content['wlan'] = "\n".join(wlan_content)

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

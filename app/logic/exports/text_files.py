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

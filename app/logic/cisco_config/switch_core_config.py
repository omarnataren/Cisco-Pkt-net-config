
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
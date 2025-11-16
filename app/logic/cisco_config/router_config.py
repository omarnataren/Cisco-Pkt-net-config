
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
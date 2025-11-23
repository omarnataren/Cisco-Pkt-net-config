
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
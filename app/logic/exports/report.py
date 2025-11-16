"""
MÓDULO: report.py
DESCRIPCIÓN: Generación de reportes de configuración en formato texto
"""

import ipaddress
from app.core.models import Combo


def export_report_with_routers(combos: list[Combo], router_configs: list, out_path: str):
    """
    Genera el reporte TXT completo con todas las configuraciones
    
    Estructura del reporte:
        1. BACKBONE: Todas las redes /30 entre routers/switch cores
        2. Por cada ROUTER:
           - Nombre y máscara de cada VLAN
           - Gateway (última IP utilizable)
           - Rango de red (network a broadcast)
    
    Args:
        combos (list[Combo]): Lista de bloques de red asignados
        router_configs (list): Lista de configuraciones de routers
        out_path (str): Ruta del archivo de salida
    
    Formato de salida:
        === BACKBONE ===
        Máscara: 255.255.255.252
        
        R1-R2
        |19.0.0.0
        |
        |
        |19.0.0.3
        
        === Router1 ===
        
        VLAN10 - Máscara: 255.255.255.0
        |192.168.10.0
        |Gateway: 192.168.10.254
        |
        |192.168.10.255
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



def format_block(net: ipaddress.IPv4Network) -> str:
    """
    Formatea un bloque de red para reporte de texto
    Muestra la dirección de red y broadcast en formato visual
    
    Args:
        net (IPv4Network): Red a formatear
    
    Returns:
        str: Representación visual del bloque con barras verticales
    
    Ejemplo:
        >>> net = IPv4Network('192.168.1.0/24')
        >>> print(format_block(net))
        |192.168.1.0
        |
        |
        |192.168.1.255
    """
    return (
        f"|{net.network_address}\n"
        f"|\n"
        f"|\n"
        f"|{net.broadcast_address}\n"
    )

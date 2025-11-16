"""
MÓDULO: models.py
DESCRIPCIÓN: Modelos de datos core de la aplicación
AUTOR: Sistema de Diseño de Topologías
FECHA: 2025

Este módulo contiene las estructuras de datos fundamentales
utilizadas en todo el sistema.
"""

import ipaddress
from dataclasses import dataclass


@dataclass
class Combo:
    """
    Estructura de datos para representar un bloque de red asignado
    
    Atributos:
        net (IPv4Network): Red IP asignada (ej: 192.168.1.0/24)
        name (str): Nombre descriptivo (ej: "Backbone R1-R2")
        group (str): Grupo al que pertenece (ej: "BACKBONE", "VLAN10")
    """
    net: ipaddress.IPv4Network
    name: str
    group: str  # Ej: "BACKBONE" o nombre de VLAN

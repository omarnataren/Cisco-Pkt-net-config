"""
MÓDULO: ssh_config.py
DESCRIPCIÓN: Generador de configuración SSH para dispositivos Cisco
"""


def generate_ssh_config(domain_name="cisco.com", username="user", password="cisco"):
    """
    Genera configuración SSH para switches y switch cores según PARATEST.cisco
    
    Configuración SSH básica que permite acceso remoto seguro mediante SSH.
    Incluye:
        - Nombre de dominio (requerido para generar claves RSA)
        - Generación de claves RSA de 512 bits (sin modulus en comando)
        - Usuario local para autenticación
        - Configuración de líneas VTY 0-5 para SSH
    
    Args:
        domain_name (str): Nombre de dominio para claves RSA (default: "cisco.com")
        username (str): Usuario administrativo (default: "user")
        password (str): Contraseña del usuario (default: "cisco")
    
    Returns:
        list: Lista de comandos IOS para configurar SSH
    
    Ejemplo:
        >>> generate_ssh_config()
        ['ip domain-name cisco.com', 'crypto key generate rsa', '512', ...]
    """
    commands = []
    commands.append(f"ip domain-name {domain_name}")
    commands.append("crypto key generate rsa")
    commands.append("512")
    commands.append("line vty 0 5")
    commands.append("transport input ssh")
    commands.append("login local")
    commands.append("exit")
    commands.append(f"username {username} password {password}")
    commands.append("enable secret cisco")
    
    return commands

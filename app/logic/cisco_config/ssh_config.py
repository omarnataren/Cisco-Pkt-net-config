"""
MÓDULO: ssh_config.py
DESCRIPCIÓN: Generador de configuración SSH para dispositivos Cisco
"""


def generate_ssh_config(domain_name="cisco.com", username="usuario", password="1234"):
    """
    Genera configuración SSH para switches y switch cores
    
    Configuración SSH básica que permite acceso remoto seguro mediante SSH.
    Incluye:
        - Nombre de dominio (requerido para generar claves RSA)
        - Generación de claves RSA de 2048 bits con general-keys
        - Usuario local para autenticación
        - Configuración de líneas VTY para SSH versión 2
    
    Args:
        domain_name (str): Nombre de dominio para claves RSA (default: "cisco.com")
        username (str): Usuario administrativo (default: "usuario")
        password (str): Contraseña del usuario (default: "1234")
    
    Returns:
        list: Lista de comandos IOS para configurar SSH
    
    Ejemplo:
        >>> generate_ssh_config()
        ['', '! Configuración SSH', 'ip domain-name cisco.com', ...]
    """
    commands = []
    commands.append("")
    commands.append("! Configuración SSH")
    commands.append(f"ip domain-name {domain_name}")
    commands.append("crypto key generate rsa general-keys modulus 2048")
    commands.append(f"username {username} password {password}")
    commands.append("ip ssh ver 2")
    commands.append("line vty 0 15")
    commands.append(" transport input ssh")
    commands.append(" login local")
    commands.append("exit")
    commands.append("")
    
    return commands

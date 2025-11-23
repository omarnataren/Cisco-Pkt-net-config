"""
MÓDULO: subnetting.py
DESCRIPCIÓN: Algoritmos de subnetting y asignación de redes IP
"""

import ipaddress


def generate_blocks(base_net, prefix, count, used, skip_first=False):
    """
    Genera bloques consecutivos de subredes sin conflictos
    
    Optimización O(count) en lugar de O(2^n):
        - Usa iterador en lugar de lista completa
        - Set para búsquedas O(1) de redes usadas
        - Early termination cuando alcanza 'count'
    
    Args:
        base_net (IPv4Network): Red base a subdividir (ej: 19.0.0.0/8)
        prefix (int): Tamaño de subredes a generar (ej: 30 para /30)
        count (int): Cantidad de subredes necesarias
        used (list): Lista de redes ya asignadas (se modifica)
        skip_first (bool): Si True, salta la primera subred (para evitar network ID)
    
    Returns:
        list: Lista de IPv4Network generadas
    
    Ejemplo:
        >>> base = IPv4Network('192.168.0.0/16')
        >>> used = []
        >>> subnets = generate_blocks(base, 24, 3, used)
        >>> [str(s) for s in subnets]
        ['192.168.0.0/24', '192.168.1.0/24', '192.168.2.0/24']
    
    Complejidad:
        - Tiempo: O(count) en caso promedio
        - Espacio: O(count) para el resultado
    """
    results = []
    # Convertir used a set de strings para búsqueda O(1)
    used_set = {str(net) for net in used}
    
    # Generar subredes bajo demanda (iterador en lugar de lista completa)
    subnets = base_net.subnets(new_prefix=prefix)
    start_index = 1 if skip_first else 0
    
    for idx, cand in enumerate(subnets):
        if idx < start_index:
            continue
            
        # Verificación optimizada con set
        cand_str = str(cand)
        if cand_str not in used_set and not check_conflict(cand, used):
            results.append(cand)
            used.append(cand)
            used_set.add(cand_str)
            if len(results) == count:
                break
    return results


def check_conflict(new_net, used):
    """
    Verifica si una nueva red se solapa con redes ya utilizadas
    
    Algoritmo:
        - Compara new_net con cada red en used
        - Verifica 3 condiciones de conflicto:
          1. Overlaps: Las redes se traslapan (comparten IPs)
          2. Subnet_of: new_net está contenida en alguna red usada
          3. Supernet_of: Alguna red usada está contenida en new_net
    
    Args:
        new_net (IPv4Network): Red a validar
        used (list): Lista de redes ya asignadas
    
    Returns:
        bool: True si hay conflicto, False si la red es válida
    
    Ejemplo:
        >>> used = [IPv4Network('192.168.1.0/24')]
        >>> check_conflict(IPv4Network('192.168.1.128/25'), used)
        True  # Conflicto: 192.168.1.128/25 está dentro de 192.168.1.0/24
    """
    for net in used:
        if new_net.overlaps(net) or new_net.subnet_of(net) or net.subnet_of(new_net):
            return True
    return False
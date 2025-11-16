
def get_available_interfaces_for_device(device_type):
    """Retorna las interfaces disponibles para cada tipo de dispositivo"""
    interfaces = {
        'router': [
            'FastEthernet0/0',
            'FastEthernet0/1',
            'Ethernet0/0/0',
            'Ethernet0/1/0',
            'Ethernet0/2/0'
        ],
        'switch_core': [
            'GigabitEthernet1/0/1', 'GigabitEthernet1/0/2', 'GigabitEthernet1/0/3', 'GigabitEthernet1/0/4',
            'GigabitEthernet1/0/5', 'GigabitEthernet1/0/6', 'GigabitEthernet1/0/7', 'GigabitEthernet1/0/8',
            'GigabitEthernet1/0/9', 'GigabitEthernet1/0/10', 'GigabitEthernet1/0/11', 'GigabitEthernet1/0/12',
            'GigabitEthernet1/0/13', 'GigabitEthernet1/0/14', 'GigabitEthernet1/0/15', 'GigabitEthernet1/0/16',
            'GigabitEthernet1/0/17', 'GigabitEthernet1/0/18', 'GigabitEthernet1/0/19', 'GigabitEthernet1/0/20',
            'GigabitEthernet1/0/21', 'GigabitEthernet1/0/22', 'GigabitEthernet1/0/23', 'GigabitEthernet1/0/24',
            'GigabitEthernet1/1/1', 'GigabitEthernet1/1/2', 'GigabitEthernet1/1/3', 'GigabitEthernet1/1/4'
        ],
        'switch': [
            'FastEthernet0/1', 'FastEthernet0/2', 'FastEthernet0/3', 'FastEthernet0/4',
            'FastEthernet0/5', 'FastEthernet0/6', 'FastEthernet0/7', 'FastEthernet0/8',
            'FastEthernet0/9', 'FastEthernet0/10', 'FastEthernet0/11', 'FastEthernet0/12',
            'FastEthernet0/13', 'FastEthernet0/14', 'FastEthernet0/15', 'FastEthernet0/16',
            'FastEthernet0/17', 'FastEthernet0/18', 'FastEthernet0/19', 'FastEthernet0/20',
            'FastEthernet0/21', 'FastEthernet0/22', 'FastEthernet0/23', 'FastEthernet0/24',
            'GigabitEthernet0/1', 'GigabitEthernet0/2'
        ],
        'computer': ['FastEthernet0']
    }
    return interfaces.get(device_type, [])


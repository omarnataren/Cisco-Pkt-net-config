import time
import ipaddress
from logic import generate_routing_table

# Crear datos de prueba
routers = []
for i in range(5):  # 5 routers
    router = {
        'name': f'Router{i+1}',
        'vlans': [],
        'backbone_interfaces': []
    }
    
    # Agregar VLANs
    for j in range(3):
        router['vlans'].append({
            'name': f'VLAN{j+1}',
            'network': ipaddress.ip_network(f'192.168.{i*10+j}.0/24')
        })
    
    # Agregar conexiones backbone al siguiente router
    if i < 4:
        router['backbone_interfaces'].append({
            'target': f'Router{i+2}',
            'full_name': f'eth0/0/{i}',
            'ip': ipaddress.ip_address(f'10.0.{i}.1'),
            'network': ipaddress.ip_network(f'10.0.{i}.0/30')
        })
    
    routers.append(router)

# Medir tiempo de ejecución
print("Probando generación de rutas...")
print(f"Routers: {len(routers)}")
print(f"VLANs por router: 3")
print()

start = time.time()
routing_tables = generate_routing_table(routers)
end = time.time()

print(f"✓ Tiempo de ejecución: {(end-start)*1000:.2f}ms")
print()

# Mostrar resultados
for router_name, data in routing_tables.items():
    routes = data['routes']
    print(f"{router_name}: {len(routes)} rutas generadas")

print()
print("✓ Test completado exitosamente")

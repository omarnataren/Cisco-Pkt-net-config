"""
Script de prueba de rendimiento para optimizaciones
"""
import time
import json

def test_performance():
    """
    Genera una topología de prueba y mide el tiempo de procesamiento
    """
    print("=" * 60)
    print("🔥 PRUEBA DE RENDIMIENTO - OPTIMIZACIONES")
    print("=" * 60)
    
    # Topología de ejemplo: 3 routers + 3 switch cores + 5 switches
    topology = {
        "nodes": [],
        "edges": [],
        "vlans": [
            {"name": "VLAN10", "prefix": "24"},
            {"name": "VLAN20", "prefix": "24"},
            {"name": "VLAN30", "prefix": "24"}
        ]
    }
    
    # Generar routers
    for i in range(1, 4):
        topology["nodes"].append({
            "id": f"r{i}",
            "data": {"type": "router", "name": f"R{i}"}
        })
    
    # Generar switch cores
    for i in range(1, 4):
        topology["nodes"].append({
            "id": f"swc{i}",
            "data": {"type": "switch_core", "name": f"SWC{i}"}
        })
    
    # Generar switches
    for i in range(1, 6):
        topology["nodes"].append({
            "id": f"sw{i}",
            "data": {"type": "switch", "name": f"SW{i}"}
        })
    
    # Generar computadoras (3 por switch)
    comp_id = 1
    for i in range(1, 6):
        for v in ["VLAN10", "VLAN20", "VLAN30"]:
            topology["nodes"].append({
                "id": f"pc{comp_id}",
                "data": {
                    "type": "computer",
                    "name": f"PC{comp_id}",
                    "vlan": v
                }
            })
            comp_id += 1
    
    # Generar conexiones backbone (routers y switch cores)
    edge_id = 1
    
    # Routers entre sí
    for i in range(1, 3):
        topology["edges"].append({
            "id": f"e{edge_id}",
            "from": f"r{i}",
            "to": f"r{i+1}",
            "data": {
                "routingDirection": "bidirectional",
                "fromInterface": {"type": "gi", "number": f"0/{i}"},
                "toInterface": {"type": "gi", "number": f"0/{i}"}
            }
        })
        edge_id += 1
    
    # Routers a switch cores
    for i in range(1, 4):
        topology["edges"].append({
            "id": f"e{edge_id}",
            "from": f"r{i}",
            "to": f"swc{i}",
            "data": {
                "routingDirection": "bidirectional",
                "fromInterface": {"type": "gi", "number": f"0/10"},
                "toInterface": {"type": "gi", "number": f"0/1"}
            }
        })
        edge_id += 1
    
    # Switch cores a switches
    for i in range(1, 4):
        for j in range(1, 3):
            sw_idx = (i-1)*2 + j
            if sw_idx <= 5:
                topology["edges"].append({
                    "id": f"e{edge_id}",
                    "from": f"swc{i}",
                    "to": f"sw{sw_idx}",
                    "data": {
                        "connectionType": "normal",
                        "fromInterface": {"type": "fa", "number": f"0/{j}"},
                        "toInterface": {"type": "fa", "number": f"0/1"}
                    }
                })
                edge_id += 1
    
    # Switches a computadoras
    comp_id = 1
    for i in range(1, 6):
        for j in range(1, 4):
            topology["edges"].append({
                "id": f"e{edge_id}",
                "from": f"sw{i}",
                "to": f"pc{comp_id}",
                "data": {
                    "fromInterface": {"type": "fa", "number": f"0/{j+1}"},
                    "toInterface": {"type": "eth", "number": "0"}
                }
            })
            edge_id += 1
            comp_id += 1
    
    print(f"\n📊 Topología generada:")
    print(f"   - {len([n for n in topology['nodes'] if n['data']['type'] == 'router'])} Routers")
    print(f"   - {len([n for n in topology['nodes'] if n['data']['type'] == 'switch_core'])} Switch Cores")
    print(f"   - {len([n for n in topology['nodes'] if n['data']['type'] == 'switch'])} Switches")
    print(f"   - {len([n for n in topology['nodes'] if n['data']['type'] == 'computer'])} Computadoras")
    print(f"   - {len(topology['edges'])} Conexiones")
    print(f"   - {len(topology['vlans'])} VLANs")
    
    # Importar función
    from app import handle_visual_topology
    
    print("\n⏱️  Midiendo rendimiento...")
    
    # Ejecutar 3 veces y promediar
    times = []
    for run in range(1, 4):
        start = time.time()
        result = handle_visual_topology(topology)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"   Run {run}: {elapsed:.3f}s")
    
    avg_time = sum(times) / len(times)
    
    print(f"\n✅ Resultados:")
    print(f"   - Tiempo promedio: {avg_time:.3f}s")
    print(f"   - Tiempo mínimo: {min(times):.3f}s")
    print(f"   - Tiempo máximo: {max(times):.3f}s")
    
    # Estimación para topología grande
    scale_factor = 30 / 11  # 30 dispositivos vs 11 en prueba
    estimated_large = avg_time * scale_factor
    
    print(f"\n🚀 Estimación para topología grande (30 dispositivos):")
    print(f"   - Tiempo estimado: {estimated_large:.1f}s")
    print(f"   - Mejora vs 180s original: {((180 - estimated_large) / 180 * 100):.1f}%")
    
    if estimated_large < 30:
        print("\n🎉 ¡EXCELENTE! Optimización exitosa")
    elif estimated_large < 60:
        print("\n✅ BUENO - Mejora significativa")
    else:
        print("\n⚠️  Puede requerir más optimización")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_performance()

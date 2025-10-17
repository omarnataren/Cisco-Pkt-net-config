from flask import Flask, render_template, request, send_file
import ipaddress
from logic import generate_blocks, export_report_with_routers, Combo, generate_router_config, generate_switch_core_config, generate_routing_table, generate_static_routes_commands

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Datos base del formulario
            first_octet = request.form["first_octet"]

            # Obtener dispositivos (routers y switches)
            router_names = request.form.getlist("router_name")
            router_types = request.form.getlist("router_type")
            
            # Si no hay tipos, asumir que todos son routers (compatibilidad)
            if not router_types:
                router_types = ['router'] * len(router_names)
            
            # Obtener VLANs
            vlan_names = request.form.getlist("vlan_name")
            vlan_terminations = request.form.getlist("vlan_term")
            vlan_prefixes = request.form.getlist("vlan_prefix")

            # Construcción de red base
            base = ipaddress.ip_network(f"{first_octet}.0.0.0/8")
            used = []
            combos = []
            backbone_networks = []

            # --- Construir estructura de VLANs ---
            vlans = []
            for i, (name, term, pref) in enumerate(zip(vlan_names, vlan_terminations, vlan_prefixes)):
                vlans.append({
                    'id': i,
                    'name': name,
                    'termination': term,
                    'prefix': int(pref)
                })

            # --- Procesar Routers y Switches con sus interfaces ---
            router_configs = []
            for router_idx, (router_name, device_type) in enumerate(zip(router_names, router_types)):
                # Obtener interfaces de este router
                interface_types = request.form.getlist(f"router_{router_idx}_interface_type")
                interface_names = request.form.getlist(f"router_{router_idx}_interface_name")
                interface_numbers = request.form.getlist(f"router_{router_idx}_interface_number")
                interface_targets = request.form.getlist(f"router_{router_idx}_interface_target")
                
                # Interfaces backbone (router-router)
                backbone_interfaces = []
                for int_type, int_name, int_num, target in zip(interface_types, interface_names, interface_numbers, interface_targets):
                    if target.startswith("router_"):
                        # Es una conexión backbone
                        target_router_idx = int(target.split("_")[1])
                        target_router_name = router_names[target_router_idx] if target_router_idx < len(router_names) else "Unknown"
                        
                        # Generar red /30 para backbone
                        backbone_block = generate_blocks(base, 30, 1, used, skip_first=True)
                        if backbone_block:
                            network = backbone_block[0]
                            hosts = list(network.hosts())
                            ip_local = hosts[0] if len(hosts) > 0 else network.network_address
                            ip_remote = hosts[1] if len(hosts) > 1 else network.broadcast_address
                            
                            backbone_interfaces.append({
                                'type': int_type,
                                'name': int_name,
                                'number': int_num,
                                'full_name': f"{int_name}{int_num}",
                                'ip': ip_local,
                                'network': network,
                                'target': target_router_name
                            })
                            
                            # Guardar para el reporte
                            combos.append(Combo(network, f"Backbone-{router_name}-{target_router_name}", "BACKBONE"))
                            backbone_networks.append(network)
                
                # Interfaces VLAN (router-switch)
                vlan_interfaces = []
                # Buscar la interfaz designada para VLANs
                vlan_interface_type = request.form.get(f"router_{router_idx}_vlan_interface_type", "eth")
                vlan_interface_name = request.form.get(f"router_{router_idx}_vlan_interface_name", "eth")
                vlan_interface_number = request.form.get(f"router_{router_idx}_vlan_interface_number", "0/2/0")
                
                assigned_vlans = []
                for vlan in vlans:
                    checkbox_name = f"router_{router_idx}_vlan_{vlan['id']}"
                    if checkbox_name in request.form:
                        # Generar bloque de IP para esta VLAN en este router
                        blocks = generate_blocks(base, vlan['prefix'], 1, used)
                        if blocks:
                            assigned_vlans.append({
                                'name': vlan['name'],
                                'termination': vlan['termination'],
                                'network': blocks[0],
                                'prefix': vlan['prefix'],
                                'interface_name': vlan_interface_name,
                                'interface_number': vlan_interface_number
                            })
                            # Agregar combo para el reporte
                            combos.append(Combo(blocks[0], f"{router_name}-{vlan['name']}", router_name))
                
                # Generar comandos CLI según el tipo de dispositivo
                if device_type == 'switch_core':
                    # Es un switch core
                    trunk_interface_type = request.form.get(f"router_{router_idx}_trunk_interface_type", "fa")
                    trunk_interface_number = request.form.get(f"router_{router_idx}_trunk_interface_number", "0/3")
                    
                    config = generate_switch_core_config(router_name, assigned_vlans, backbone_interfaces, trunk_interface_type, trunk_interface_number)
                    router_configs.append({
                        'name': router_name,
                        'type': 'switch_core',
                        'config': config,
                        'vlans': assigned_vlans,
                        'backbone_interfaces': backbone_interfaces
                    })
                else:
                    # Es un router normal
                    config = generate_router_config(router_name, assigned_vlans, backbone_interfaces, vlan_interface_name, vlan_interface_number)
                    router_configs.append({
                        'name': router_name,
                        'type': 'router',
                        'config': config,
                        'vlans': assigned_vlans,
                        'backbone_interfaces': backbone_interfaces
                    })

            # --- Generar tabla de ruteo automática ---
            routing_tables = generate_routing_table(router_configs)
            
            # --- Agregar comandos de rutas estáticas a cada router ---
            for router in router_configs:
                router_name = router['name']
                if router_name in routing_tables:
                    routes = routing_tables[router_name]['routes']
                    route_commands = generate_static_routes_commands(routes)
                    
                    # Insertar comandos de rutas antes del "end"
                    if route_commands:
                        config = router['config']
                        
                        # Buscar el índice del "end"
                        end_index = -1
                        for i in range(len(config) - 1, -1, -1):
                            if config[i] == "end":
                                end_index = i
                                break
                        
                        if end_index >= 0:
                            # Insertar línea vacía, rutas, y otra línea vacía antes del "end"
                            new_config = config[:end_index] + [""] + route_commands + [""] + config[end_index:]
                            router['config'] = new_config
                        else:
                            # Si no hay "end", agregar al final
                            router['config'] = config + [""] + route_commands
                        
                        router['routes'] = routes
                    else:
                        router['routes'] = []
                else:
                    router['routes'] = []

            # --- Exportar reporte con routers ---
            export_report_with_routers(combos, router_configs, "reporte.txt")
            return render_template("router_results.html", routers=router_configs)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return render_template("index.html", error=f"{str(e)}\n\n{error_detail}")

    return render_template("index.html")

@app.route("/visual")
def visual():
    return render_template("index_visual.html")

@app.route("/download")
def download():
    return send_file("reporte.txt", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

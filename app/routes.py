"""
Rutas HTTP de la aplicación
"""

from flask import Blueprint, render_template, request, send_file, current_app
import json
import io

# Importar funciones del orquestador
from app.logic.orchestrator import handle_visual_topology

bp = Blueprint('main', __name__)

@bp.route("/", methods=["GET", "POST"])
def index():
    """
    Ruta principal de la aplicación
    
    GET: Muestra el diseñador visual de topología
    POST: Procesa la topología diseñada y genera configuraciones
    """
    if request.method == "POST":
        topology_data = request.form.get("topology_data")
        if topology_data:
            topology = json.loads(topology_data)
            return handle_visual_topology(topology)
        else:
            return "No se recibieron datos de topología", 400
    
    return render_template("index.html")


@bp.route("/config", methods=["POST"])
def generate_config():
    """
    Endpoint alternativo para recibir configuración (API JSON)
    """
    topology_data = request.get_json()
    if topology_data:
        return handle_visual_topology(topology_data)
    return {"error": "No se recibieron datos de topología"}, 400


@bp.route("/download")
def download():
    """
    Descarga el archivo de configuración completo
    """
    config_files = current_app.config.get('CONFIG_FILES_CONTENT', {})
    
    if 'completo' not in config_files:
        return "No hay configuraciones generadas. Genera una topología primero.", 400
    
    file_content = config_files['completo']
    file_bytes = io.BytesIO(file_content.encode('utf-8'))
    file_bytes.seek(0)
    
    return send_file(
        file_bytes,
        mimetype='text/plain',
        as_attachment=True,
        download_name='config_completo.txt'
    )


@bp.route("/download/<device_type>")
def download_by_type(device_type):
    """
    Descarga configuraciones por tipo de dispositivo
    
    Args:
        device_type: routers, switch_cores, switches, completo, ptbuilder
    """
    config_files = current_app.config.get('CONFIG_FILES_CONTENT', {})
    
    file_names = {
        'routers': 'config_routers.txt',
        'switch_cores': 'config_switch_cores.txt',
        'switches': 'config_switches.txt',
        'completo': 'config_completo.txt',
        'ptbuilder': 'topology_ptbuilder.txt',
        'wlan': 'WLAN_config.txt'
    }
    
    if device_type not in file_names:
        return "Tipo de dispositivo no válido.", 400
    
    if device_type not in config_files:
        return f"No hay configuraciones de tipo '{device_type}' generadas.", 400
    
    file_content = config_files[device_type]
    file_bytes = io.BytesIO(file_content.encode('utf-8'))
    file_bytes.seek(0)
    
    return send_file(
        file_bytes,
        mimetype='text/plain',
        as_attachment=True,
        download_name=file_names[device_type]
    )
# Cisco PKT - Diseñador Visual de Topologías

Aplicación web para diseñar topologías de red y generar automáticamente configuraciones CLI para dispositivos Cisco (Routers, Switches, Switch Cores).

## Características

### Diseño Visual Interactivo
- Interfaz gráfica basada en vis-network con drag & drop
- Posicionamiento libre de dispositivos
- Conexiones visuales con flechas direccionales
- Edición inline de nombres y propiedades
- Controles de zoom y navegación

### Dispositivos Soportados
- **Routers** (Layer 3) - Ruteo entre redes
- **Switch Core** (Layer 3) - VLANs + ruteo inter-VLAN
- **Switches** (Layer 2) - Conectividad local
- **Computadoras** - Endpoints de red

### Funcionalidades Avanzadas
- **Asignación automática de interfaces** - Selección inteligente según tipo de dispositivo
- **Ruteo direccional** - Control granular de flujo de tráfico (bidireccional, unidireccional, sin ruteo)
- **EtherChannel** - Agregación de enlaces con LACP/PAgP
- **Generación automática de IPs** - Subnetting para backbones (/30) y VLANs
- **Algoritmo BFS direccional** - Cálculo de rutas estáticas respetando direcciones configuradas
- **Configuración SSH** - Acceso remoto seguro en switches (SSHv2, usuarios locales)
- **Exportación múltiple** - Descarga por dispositivo o archivo consolidado
- **Script PTBuilder** - Generación de script para automatizar creación en Packet Tracer

## Instalación

### Requisitos
- Python 3.8+
- Flask 3.x

### Dependencias
```bash
pip install flask
```

## Uso

### Iniciar la aplicación
```bash
python run.py
```

Abre tu navegador en: `http://127.0.0.1:5000`

### Flujo de trabajo

#### 1. Agregar dispositivos
- Click en los botones de la barra superior (Router, Switch Core, Switch, Computadora)
- Los dispositivos aparecen en el canvas
- Arrastra para posicionarlos
- Doble-click para editar nombre

#### 2. Conectar dispositivos
- Click en "Conectar"
- Selecciona dos dispositivos
- Las interfaces se asignan automáticamente según el tipo de dispositivo
- Configura manualmente si es necesario (tipo de interfaz y número)

#### 3. Configurar direcciones de ruteo
Doble-click en una conexión para cambiar dirección:
- **Bidireccional** (↔) - Rutas estáticas en ambas direcciones
- **From-to** (→) - Solo desde origen a destino
- **To-from** (←) - Solo desde destino a origen
- **Sin ruteo** (—) - Conexión física sin rutas

#### 4. Configurar VLANs
- Panel derecho: "Agregar VLAN"
- Define nombre, ID y prefijo de red (ej: /24)
- Doble-click en router/switch core para asignar VLANs

#### 5. Configurar EtherChannel (opcional)
- Click en conexión entre switches
- Selecciona "EtherChannel" en tipo de conexión
- Configura protocolo (LACP/PAgP), channel group y rangos de interfaces

#### 6. Generar configuraciones
- Click en "Generar Configuración"
- Revisa las configuraciones CLI de cada dispositivo
- Descarga individual o archivo completo
- Descarga script PTBuilder para Packet Tracer

## 📁 Estructura del Proyecto

El proyecto sigue **Screaming Architecture**, donde la estructura refleja claramente el propósito del sistema.

```
Cisco-Pkt-net-config/
│
├── app/                                    # 🐍 BACKEND (Python/Flask)
│   ├── __init__.py                         # Factory de aplicación Flask
│   ├── routes.py                           # Rutas HTTP (/, /download)
│   │
│   ├── core/                               # 🎯 Modelos de datos fundamentales
│   │   ├── __init__.py
│   │   └── models.py                       # Combo (dataclass para redes IP)
│   │
│   ├── logic/                              # 💼 Lógica de negocio del sistema
│   │   ├── orchestrator.py                 # Orquestador principal (handle_visual_topology)
│   │   │
│   │   ├── cisco_config/                   # 🔧 Generadores de configuración Cisco IOS
│   │   │   ├── __init__.py
│   │   │   ├── ssh_config.py              # Configuración SSH (SSHv2, usuarios)
│   │   │   ├── etherchannel.py            # EtherChannel (LACP/PAgP)
│   │   │   ├── router_config.py           # Configuración de routers
│   │   │   └── switch_core_config.py      # Configuración de switch cores (Layer 3)
│   │   │
│   │   ├── network_calculations/          # 📊 Cálculos de subnetting y addressing
│   │   │   ├── __init__.py
│   │   │   └── subnetting.py              # generate_blocks() - VLSM, asignación de IPs
│   │   │
│   │   ├── routing_algorithms/            # 🛤️ Algoritmos de ruteo
│   │   │   ├── __init__.py
│   │   │   ├── bfs_routing.py             # BFS direccional para tablas de ruteo
│   │   │   └── static_routes.py           # Generador de comandos "ip route"
│   │   │
│   │   ├── exports/                       # 📤 Exportadores de configuraciones
│   │   │   ├── __init__.py
│   │   │   ├── text_files.py              # Archivos TXT por tipo de dispositivo
│   │   │   └── report.py                  # Reportes de configuración (format_block)
│   │   │
│   │   ├── ptbuilder/                     # 🎨 Generador de scripts PT Builder
│   │   │   ├── __init__.py
│   │   │   ├── ptbuilder.py               # Script principal para Packet Tracer
│   │   │   └── interface_utils.py         # Utilidades (expand_interface_type, transform_coordinates)
│   │   │
│   │   └── device/                        # 📡 Constantes y utilidades de dispositivos
│   │       ├── __init__.py
│   │       └── device-constants.py        # Constantes de interfaces por tipo
│   │
│   └── templates/                         # 🎨 Plantillas HTML
│       ├── index.html                     # Diseñador visual principal
│       ├── router_results.html            # Página de resultados con configuraciones
│       └── modals/                        # Modales de configuración
│           ├── connection_modal.html
│           ├── device_properties_modal.html
│           ├── edit_connection_modal.html
│           ├── manage_computers_modal.html
│           └── vlan_modal.html
│
├── static/                                # 🎨 FRONTEND (JavaScript/CSS)
│   ├── css/
│   │   ├── styles.css                     # Estilos principales
│   │   └── modals.css                     # Estilos de modales
│   │
│   ├── js/
│   │   ├── lib/
│   │   │   └── vis-network.min.js         # Librería de visualización de grafos
│   │   │
│   │   ├── core/                          # 🎯 Estado global y constantes
│   │   │   ├── network-state.js           # nodes, edges, vlans, counters (DataSet vis-network)
│   │   │   └── network-constants.js       # Constantes de interfaces, colores, tipos
│   │   │
│   │   ├── devices/                       # 🖥️ Gestión de dispositivos
│   │   │   ├── device-factory.js          # Crear/eliminar dispositivos en canvas
│   │   │   └── device-interfaces.js       # Asignar/liberar interfaces automáticamente
│   │   │
│   │   ├── connections/                   # 🔗 Gestión de conexiones
│   │   │   ├── connection-mode.js         # Modo de conexión (activar/desactivar)
│   │   │   ├── connection-creator.js      # Crear conexiones entre dispositivos
│   │   │   ├── connection-editor.js       # Editar conexiones existentes
│   │   │   ├── routing-direction.js       # Direccionalidad de ruteo (bi/uni/sin ruteo)
│   │   │   └── etherchannel-helpers.js    # Helpers para EtherChannel
│   │   │
│   │   ├── vlans/                         # 🏷️ Gestión de VLANs
│   │   │   └── vlan-managment.js          # CRUD de VLANs (agregar, eliminar, actualizar)
│   │   │
│   │   ├── topology/                      # 🌐 Renderizado del canvas
│   │   │   └── topology-renderer.js       # Inicialización de vis-network
│   │   │
│   │   ├── ui/                            # 🎨 Componentes de interfaz
│   │   │   ├── notifications.js           # Sistema de notificaciones
│   │   │   ├── modals.js                  # Gestión de modales (abrir/cerrar)
│   │   │   ├── property-panel.js          # Panel de propiedades de dispositivos
│   │   │   └── zoom-controls.js           # Controles de zoom (in/out/reset)
│   │   │
│   │   ├── export/                        # 📤 Exportación de topología
│   │   │   └── topology-serializer.js     # Serializar topología a JSON para backend
│   │   │
│   │   └── main.js                        # 🚀 Punto de entrada principal
│   │
│   └── assets/                            # Recursos estáticos (iconos, imágenes)
│
├── docs/                                  # 📚 Documentación del proyecto
│   ├── SCREAMING_ARCHITECTURE.md          # Propuesta de arquitectura Screaming
│   ├── FUNCIONES_RESTANTES_UBICACION.md   # Análisis de funciones restantes
│   ├── MAPA_VISUAL_REORGANIZACION.md      # Mapa visual de reorganización
│   ├── SISTEMA_IMPORTACIONES.md           # Sistema de importaciones completo
│   └── CHECKLIST_IMPORTACIONES.md         # Checklist de implementación
│
├── run.py                                 # 🚀 Punto de entrada de la aplicación
├── requirements.txt                       # 📦 Dependencias Python
└── README.md                              # 📖 Esta documentación
```

### 📋 Descripción de Carpetas Principales

#### **Backend (app/)**
- **`core/`**: Modelos de datos fundamentales (Combo para redes IP)
- **`logic/cisco_config/`**: Generación de comandos CLI para Cisco IOS
- **`logic/network_calculations/`**: Algoritmos de subnetting VLSM
- **`logic/routing_algorithms/`**: BFS para tablas de ruteo estático
- **`logic/exports/`**: Exportación a archivos TXT y PT Builder
- **`logic/ptbuilder/`**: Scripts para automatización en Packet Tracer
- **`logic/device/`**: Constantes de dispositivos de red

#### **Frontend (static/js/)**
- **`core/`**: Estado global (vis-network DataSet) y constantes
- **`devices/`**: Creación y gestión de dispositivos en canvas
- **`connections/`**: Creación, edición y configuración de conexiones
- **`vlans/`**: Sistema CRUD de VLANs
- **`topology/`**: Inicialización y renderizado del canvas
- **`ui/`**: Componentes de interfaz (notificaciones, modales, zoom)
- **`export/`**: Serialización de topología para enviar a backend

### 🔄 Flujo de Datos

```
Usuario diseña topología (static/js/)
    ↓
topology-serializer.js → JSON
    ↓
POST a Flask (app/routes.py)
    ↓
orchestrator.py coordina:
    ├─ subnetting.py → Calcula redes IP
    ├─ router_config.py → Genera CLI
    ├─ bfs_routing.py → Calcula rutas
    └─ ptbuilder.py → Genera script PT
    ↓
render_template('router_results.html')
```

## Algoritmo de Ruteo

### BFS Direccional
El algoritmo utiliza Breadth-First Search respetando las direcciones configuradas:

1. Construye grafo dirigido basado en `routingDirection` de cada conexión
2. Para cada router, ejecuta BFS explorando solo vecinos permitidos
3. Genera comandos `ip route` para todas las redes alcanzables
4. Next-hop siempre es el primer salto (vecino directo)

**Ejemplo**: R1 → R2 → R3 (unidireccional)
- **R1**: Genera rutas a R2 y R3
- **R2**: Genera rutas a R3 (no a R1)
- **R3**: No genera rutas (no tiene salidas)

## Configuraciones Generadas

### Routers
- Hostname
- Interfaces (FastEthernet, Ethernet)
- IPs de backbone (/30 entre routers)
- VLANs (sub-interfaces)
- Rutas estáticas (según BFS direccional)

### Switches
- Hostname
- VLANs (database)
- Access ports (asignación a VLANs)
- Trunk ports (hacia routers/otros switches)
- EtherChannel (LACP/PAgP)
- SSH (versión 2, usuarios locales)

### Switch Cores
- Todo lo de switches +
- Interfaces SVI (gateway de VLANs)
- Ruteo IP habilitado
- Rutas estáticas

## Tips de Uso

- Usa nombres descriptivos para dispositivos (R1-Core, SW-Piso1)
- Convención de VLANs: 10, 20, 30 para facilitar organización
- Prefijo /24 es estándar para redes de oficina
- EtherChannel: usa el mismo número de interfaces en ambos extremos
- Direcciones de ruteo: Configura antes de generar para evitar regeneraciones

## Tecnologías

- **Backend**: Python 3.8+, Flask 3.x
- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Visualización**: vis-network.js
- **Algoritmos**: BFS direccional, subnetting automático

## Licencia

MIT License

## Autor

Omar Nataren

- Documenta flujo antes de configurar│   ├── index_visual.html              # Interfaz visual principal

│   └── router_results.html            # Página de resultados

## 🐛 Solución├── reporte.txt                         # Reporte generado (temporal)

- Sin rutas → Verifica direcciones (doble-click)├── .gitignore                          # Archivos ignorados por git

- EtherChannel → Solo switches├── README.md                           # Esta documentación

- VLAN faltante → Doble-click + checkbox├── DIRECTED_ROUTING_IMPLEMENTATION.md  # Docs de ruteo direccional

├── ETHERCHANNEL_IMPLEMENTATION.md      # Docs de EtherChannel
└── CLEANUP_ANALYSIS.md                 # Análisis de limpieza

El reporte generado (`reporte.txt`) incluye:

```
=== BACKBONE ===
Máscara: 255.255.255.252

Backbone-1
|10.0.0.4
|
|
|10.0.0.7

=== Router-Principal ===

Ventas - Máscara: 255.255.255.0
|10.0.1.0
|Gateway: 10.0.1.1
|
|10.0.1.255
```

## 🛠️ Tecnologías

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Librerías**: ipaddress (manejo de redes IP)

## 📝 Notas

- Los segmentos IP se asignan automáticamente sin solapamiento
- Cada VLAN puede asignarse a múltiples routers
- El primer host utilizable se usa como gateway
- Los comandos CLI son compatibles con Cisco IOS

## 👨‍💻 Autor

Proyecto para configuración de redes en entornos educativos.

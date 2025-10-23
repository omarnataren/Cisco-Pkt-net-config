# 🌐 Diseñador Visual de Topología de Redes# 🌐 Diseñador Visual de Topología de Redes



Herramienta web interactiva para diseñar topologías de red y generar automáticamente configuraciones CLI de dispositivos Cisco.Herramienta web interactiva para diseñar topologías de red y generar configuraciones CLI de dispositivos Cisco (Routers, Switches).



## 🚀 Características Principales## 🚀 Características



### Diseño Visual Interactivo### Diseño Visual

- 🎨 Canvas gráfico con drag & drop- 🎨 **Interfaz gráfica interactiva** basada en vis-network

- 🔗 Conexiones visuales con flechas direccionales- 🖱️ **Drag & drop** para posicionar dispositivos

- 📝 Edición en tiempo real- 🔗 **Conexiones visuales** entre dispositivos

- 🔍 Zoom (0.3x - 3.0x)- 📝 **Edición inline** de nombres y propiedades

- 🔍 **Zoom y navegación** con controles intuitivos

### Dispositivos

- 🔀 **Router** - Layer 3 con ruteo IP### Dispositivos Soportados

- 🔄 **Switch Core** - Layer 3 con VLANs y ruteo- 🔀 **Routers** (Layer 3)

- 🔌 **Switch** - Layer 2- 🔄 **Switch Core** (Layer 3 con VLANs)

- 💻 **Computadora** - Endpoints- 🔌 **Switches** (Layer 2)

- 💻 **Computadoras** (endpoints)

### Ruteo Direccional

Control granular de rutas estáticas:### Funcionalidades Avanzadas

- **↔ Bidireccional** (default)- ✅ **Ruteo Direccional**: Control manual de direcciones de ruteo (bidireccional, unidireccional, sin ruteo)

- **→ From-to** (unidireccional)- ⚡ **EtherChannel**: Agregación de enlaces con LACP y PAgP

- **← To-from** (unidireccional)  - 🔄 **Generación automática de rutas estáticas** respetando direcciones configuradas

- **—Sin ruteo** (solo conexión física)- 📊 **Cálculo automático de IPs** para backbones y VLANs

- 📋 **Exportación de configuraciones** por dispositivo

### EtherChannel- 💾 **Descarga de reportes** en formato TXT

Agregación entre switches:

- **LACP** (active/passive)## 📋 Cómo usar

- **PAgP** (desirable/auto)

- Rangos de interfaces### 1. Iniciar la aplicación



### Generación Automática```bash

- ✅ IPs para backbones (/30)python app.py

- ✅ Subredes para VLANs```

- ✅ Algoritmo BFS direccional

- ✅ Comandos Cisco IOSLuego abre tu navegador en: `http://127.0.0.1:5000`

- ✅ Exportación TXT

### 2. Diseñar la Topología

## 📋 Uso Rápido

#### Agregar Dispositivos

### 1. Iniciar1. Haz clic en los botones de la barra superior:

```bash   - 🔀 Router

python app.py   - 🔄 Switch Core

```   - 🔌 Switch

Abre: `http://127.0.0.1:5000`   - 💻 Computadora



### 2. Diseñar2. Haz doble-click en un dispositivo para editarlo:

- Click en **Router/Switch/PC** → Aparece en canvas   - Cambiar nombre

- Arrastra para posicionar   - Asignar VLANs (solo routers/switches core)

- Doble-click para editar nombre

#### Conectar Dispositivos

### 3. Conectar1. Haz clic en "🔗 Conectar"

- Click **"🔗 Conectar"**2. Selecciona dos dispositivos para conectarlos

- Click dispositivo 13. Configura las interfaces (tipo y número)

- Click dispositivo 24. La conexión aparecerá en el canvas

- Configura interfaces (fa/gi 0/0)

#### Configurar Direcciones de Ruteo

### 4. Ruteo1. **Doble-click** en una conexión para ciclar entre:

**Doble-click en conexión** para cambiar dirección   - ↔ **Bidireccional**: Rutas en ambas direcciones

   - → **From-to**: Solo desde origen a destino

### 5. VLANs   - ← **To-from**: Solo desde destino a origen

- Panel derecho: **"➕ Agregar VLAN"**   - — **Sin ruteo**: Conexión física sin rutas

- Nombre, ID, Prefijo (/24)

- Doble-click en dispositivo → Marcar VLANs#### Configurar EtherChannel (solo entre switches)

1. Click en una conexión entre switches

### 6. Generar2. Click en "Editar Conexión"

- **"🚀 Generar Configuración"**3. Selecciona "EtherChannel"

- **"📋 Copiar"** por dispositivo4. Configura:

- **"📥 Descargar"** reporte completo   - Protocolo: LACP o PAgP

   - Channel Group: 1-6

## 🔧 Tecnologías   - Rangos de interfaces (ej: fa0/1-3)

Python Flask, vis-network, BFS direccional

### 3. Configurar VLANs

## 📁 Estructura

```1. Haz clic en "➕ Agregar VLAN" en el panel derecho

├── app.py (520 líneas)2. Define:

├── logic.py (483 líneas)   - Nombre (ej: Ventas, IT)

├── templates/   - Terminación/ID (ej: 10, 20)

│   ├── index_visual.html (1560+ líneas)   - Prefijo de máscara (ej: 24 para /24)

│   └── router_results.html (285 líneas)

└── reporte.txt3. Asigna VLANs a routers/switches core haciendo doble-click en el dispositivo

```

### 4. Generar Configuraciones

## ⚙️ Algoritmo de Ruteo

**BFS Direccional**:1. Haz clic en "🚀 Generar Configuración"

1. Grafo dirigido según `routingDirection`2. Se mostrarán las configuraciones CLI de todos los dispositivos:

2. Explora solo vecinos permitidos   - Comandos de interfaces

3. Genera `ip route` para redes alcanzables   - Configuración de VLANs

4. Next-hop = primer salto   - Rutas estáticas (respetando direcciones)

   - EtherChannels configurados

**Ejemplo**: R1 → R2 → R33. Copia configuraciones individuales o todas juntas

- R1: ✅ Rutas a R2 y R34. Descarga el reporte completo en TXT

- R2: ✅ Rutas a R3, ❌ R1  

- R3: ❌ Sin rutas## � Estructura del Proyecto



## 💡 Tips```

- Nombres descriptivos (R1-Core)Combos y rutas/

- VLANs: 10, 20, 30...├── app.py                              # Servidor Flask (521 líneas)

- /24 para oficinas├── logic.py                            # Lógica de ruteo y configs (500 líneas)

- EtherChannel: mismo # interfaces├── templates/

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

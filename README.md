# 🌐 Generador de Configuración de Redes

Herramienta web para generar configuraciones CLI de routers Cisco y reportes de red con VLANs y segmentos IP.

## 🚀 Características

- ✅ Generación automática de segmentos Backbone (/30)
- ✅ Configuración de múltiples routers
- ✅ Asignación de VLANs a routers
- ✅ Generación de comandos CLI para Cisco IOS
- ✅ Reporte de texto con formato estructurado
- ✅ Cálculo automático de gateways
- ✅ Descarga de configuraciones

## 📋 Cómo usar

### 1. Iniciar la aplicación

```bash
python app.py
```

Luego abre tu navegador en: `http://127.0.0.1:5000`

### 2. Configurar la red

1. **Configuración Base**
   - Ingresa el primer octeto (ej: 10, 172, 192)
   - Define cuántos segmentos backbone (/30) necesitas

2. **Agregar VLANs**
   - Haz clic en "➕ Agregar VLAN"
   - Ingresa:
     - Nombre de la VLAN (ej: Ventas, Administración)
     - Terminación (número de interfaz: 0, 1, 2...)
     - Prefijo de máscara (ej: 24 para /24)

3. **Agregar Routers**
   - Haz clic en "➕ Agregar Router"
   - Ingresa el nombre del router (ej: Router-Principal, R1)
   - Selecciona las VLANs que manejará este router usando los checkboxes

4. **Generar Configuración**
   - Haz clic en "🚀 Generar Configuración"
   - Se mostrarán los comandos CLI para cada router
   - Puedes copiar cada configuración individual o todas juntas
   - Descarga el reporte en formato TXT

## 📄 Formato del Reporte

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

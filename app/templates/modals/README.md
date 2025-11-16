# Modales - Diseñador Visual de Topología

Esta carpeta contiene todos los modales (ventanas emergentes) utilizados en el diseñador visual de topologías de red.

## 📁 Estructura de Archivos

```
modals/
├── README.md                      # Este archivo
├── connection_modal.html          # Modal para crear nueva conexión
├── edit_connection_modal.html     # Modal para editar conexión existente
└── computer_vlan_modal.html       # Modal para asignar VLAN a computadora
```

## 📝 Descripción de Modales

### 1. connection_modal.html
**Propósito:** Configurar una nueva conexión entre dos dispositivos

**Características:**
- Selector de tipo de conexión (Normal / EtherChannel)
- Campos para conexión normal:
  - Tipo de interfaz origen (FastEthernet, GigabitEthernet, Ethernet)
  - Número de interfaz origen
  - Tipo de interfaz destino
  - Número de interfaz destino
- Campos para EtherChannel:
  - Protocolo (LACP / PAgP)
  - Channel Group (1-6)
  - Tipo de interfaz y rango para origen
  - Tipo de interfaz y rango para destino

**Funciones JavaScript asociadas:**
- `closeConnectionModal()` - Cierra el modal
- `saveConnection()` - Guarda la nueva conexión
- `toggleNewConnectionFields()` - Muestra/oculta campos según tipo de conexión

**IDs de elementos importantes:**
- `connection-modal` - Contenedor principal
- `new-connection-type` - Selector de tipo de conexión
- `new-normal-fields` - Campos para conexión normal
- `new-etherchannel-fields` - Campos para EtherChannel
- `conn-from-name`, `conn-to-name` - Nombres de dispositivos

---

### 2. edit_connection_modal.html
**Propósito:** Editar una conexión existente entre dispositivos

**Características:**
- Similar a connection_modal.html pero para edición
- Selector de tipo de conexión (Normal / EtherChannel)
- Campos pre-poblados con valores actuales
- Soporta cambio entre tipos de conexión

**Funciones JavaScript asociadas:**
- `closeEditConnectionModal()` - Cierra el modal de edición
- `saveEditedConnection()` - Guarda los cambios en la conexión
- `toggleEtherChannelFields()` - Muestra/oculta campos según tipo

**IDs de elementos importantes:**
- `edit-connection-modal` - Contenedor principal
- `edit-connection-type` - Selector de tipo de conexión
- `normal-connection-fields` - Campos para conexión normal
- `etherchannel-fields` - Campos para EtherChannel

**Diferencias con connection_modal.html:**
- Usa prefijo `edit-` en los IDs
- No tiene `conn-from-name` (ya se conoce la conexión)
- Función de guardado diferente (`saveEditedConnection`)

---

### 3. computer_vlan_modal.html
**Propósito:** Asignar una VLAN a una computadora

**Características:**
- Muestra el nombre de la computadora
- Dropdown con lista de VLANs disponibles
- Validación de selección de VLAN

**Funciones JavaScript asociadas:**
- `closeComputerVlanModal()` - Cierra el modal
- `saveComputerVlan()` - Asigna la VLAN seleccionada

**IDs de elementos importantes:**
- `computer-vlan-modal` - Contenedor principal
- `computer-name` - Nombre de la computadora
- `computer-vlan-select` - Selector de VLAN

**Nota:** El dropdown de VLANs se llena dinámicamente desde JavaScript con las VLANs creadas en la topología.

---

## 🔧 Uso en index_visual.html

Los modales se incluyen en el archivo principal usando Jinja2:

```html
<!-- Modal para nueva conexión -->
{% include 'modals/connection_modal.html' %}

<!-- Modal para editar conexión -->
{% include 'modals/edit_connection_modal.html' %}

<!-- Modal para asignar VLAN a computadora -->
{% include 'modals/computer_vlan_modal.html' %}
```

## 📋 Convenciones de Código

### Estructura HTML
Todos los modales siguen la misma estructura:

```html
<div id="[modal-id]" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>[Título]</h3>
            <button class="modal-close" onclick="[closeFunction]()">&times;</button>
        </div>
        <div class="modal-body">
            <!-- Contenido del modal -->
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="[closeFunction]()">Cancelar</button>
            <button class="btn" onclick="[saveFunction]()">Guardar</button>
        </div>
    </div>
</div>
```

### Clases CSS
- `.modal` - Contenedor principal (overlay)
- `.modal-content` - Caja del modal
- `.modal-header` - Cabecera con título y botón de cerrar
- `.modal-body` - Cuerpo con formulario
- `.modal-footer` - Pie con botones de acción
- `.input-group` - Grupo de label + input
- `.device-info` - Información de dispositivo
- `.btn` - Botón principal
- `.btn-secondary` - Botón secundario

### IDs importantes
- Modales:
  - `connection-modal`
  - `edit-connection-modal`
  - `computer-vlan-modal`

- Campos de nueva conexión:
  - `new-connection-type`
  - `new-normal-fields`
  - `new-etherchannel-fields`
  - `new-etherchannel-protocol`
  - `new-etherchannel-group`

- Campos de edición:
  - `edit-connection-type`
  - `normal-connection-fields`
  - `etherchannel-fields`
  - `etherchannel-protocol`
  - `etherchannel-group`

## 🎨 Estilos

Los estilos CSS de los modales están definidos en `index_visual.html` en la sección `<style>`.

Clases principales:
```css
.modal { /* Overlay de fondo */ }
.modal-content { /* Caja del modal */ }
.modal-header { /* Cabecera */ }
.modal-body { /* Cuerpo */ }
.modal-footer { /* Pie */ }
.input-group { /* Grupo de formulario */ }
```

## 🔄 Flujo de Interacción

### Crear Nueva Conexión
1. Usuario hace clic en "Nueva Conexión"
2. Se abre `connection_modal.html`
3. Usuario selecciona tipo de conexión
4. `toggleNewConnectionFields()` muestra campos apropiados
5. Usuario llena formulario
6. `saveConnection()` procesa y guarda
7. Modal se cierra

### Editar Conexión
1. Usuario hace clic derecho en conexión → "Editar"
2. Se abre `edit_connection_modal.html`
3. Campos se pre-llenan con valores actuales
4. Usuario modifica valores
5. `saveEditedConnection()` actualiza conexión
6. Modal se cierra

### Asignar VLAN a Computadora
1. Usuario hace clic en computadora
2. Se abre `computer_vlan_modal.html`
3. Dropdown se llena con VLANs disponibles
4. Usuario selecciona VLAN
5. `saveComputerVlan()` asigna VLAN
6. Modal se cierra

## 📚 Mantenimiento

### Agregar nuevo modal
1. Crear archivo en `templates/modals/[nombre]_modal.html`
2. Seguir estructura estándar de modal
3. Incluir en `index_visual.html`:
   ```html
   {% include 'modals/[nombre]_modal.html' %}
   ```
4. Implementar funciones JavaScript asociadas
5. Actualizar este README

### Modificar modal existente
1. Editar archivo correspondiente en `templates/modals/`
2. Verificar que IDs y funciones JavaScript sigan funcionando
3. Probar en navegador
4. Actualizar documentación si es necesario

## ✅ Ventajas de esta Estructura

1. **Modularidad:** Cada modal es independiente y reutilizable
2. **Mantenibilidad:** Fácil encontrar y editar código específico
3. **Legibilidad:** index_visual.html más limpio y organizado
4. **Escalabilidad:** Fácil agregar nuevos modales sin saturar el archivo principal
5. **Colaboración:** Múltiples desarrolladores pueden trabajar en diferentes modales

## 📊 Estadísticas

- **Antes:** index_visual.html con ~1730 líneas (todo junto)
- **Después:** 
  - index_visual.html: ~1100 líneas (reducción de 36%)
  - 3 archivos de modales separados: ~250 líneas totales
  - **Resultado:** Código más organizado y mantenible

---

**Última actualización:** Noviembre 2024
**Versión:** 2.0 (Modular)

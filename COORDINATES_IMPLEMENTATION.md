# Implementación: Preservación de Coordenadas para PTBuilder

## Descripción
Las coordenadas (x, y) de cada dispositivo posicionado en la interfaz visual se guardan y se usan exactamente en la generación del script PTBuilder, garantizando que los dispositivos aparezcan en las mismas posiciones dentro de Packet Tracer.

## Cambios Realizados

### 1. Frontend (`templates/index_visual.html`)

**Línea ~340-359**: Función `createDeviceAtPosition(x, y)`
- Los dispositivos se crean con las coordenadas exactas donde el usuario hace clic
- Se almacenan en las propiedades `x` y `y` del nodo
- Se agregaron comentarios explicativos para documentar su uso posterior en PTBuilder

```javascript
nodes.add({
    id: id,
    label: name,
    title: name,
    shape: shape,
    size: 30,
    x: x,  // Coordenada X exacta posicionada por el usuario
    y: y,  // Coordenada Y exacta posicionada por el usuario - Se usarán en PTBuilder
    color: color,
    // ... otras propiedades
});
```

**Línea ~1408**: Función `generateConfigurations()`
- Cuando se envía la topología al servidor, se incluyen automáticamente las coordenadas
- El JSON enviado contiene: `{ nodes: nodes.get(), edges: edges.get(), vlans: vlans }`
- Cada nodo en `nodes.get()` incluye sus propiedades x e y

### 2. Backend (`app.py`)

**Línea ~93-113**: Función `generate_ptbuilder_script(topology, router_configs, computers)`

#### Cambios:
1. **Documentación mejorada** con DocString explicativo sobre preservación de coordenadas

2. **Procesamiento seguro de coordenadas** (líneas 155-162):
```python
for node in nodes:
    device_name = node['data']['name']
    device_type = node['data']['type']
    model = device_models.get(device_type, 'PC-PT')
    # Usar coordenadas exactas posicionadas en la interfaz
    # Si no existen coordenadas, usar valores por defecto
    x = int(node.get('x', 100)) if node.get('x') is not None else 100
    y = int(node.get('y', 100)) if node.get('y') is not None else 100
    lines.append(f'addDevice("{device_name}", "{model}", {x}, {y});')
```

**Características del procesamiento:**
- Convierte las coordenadas a enteros para PTBuilder
- Validación: Si no existen coordenadas, usa valor por defecto (100, 100)
- Valida explícitamente que el valor no sea `None` antes de convertir
- Las coordenadas se pasan directamente al comando `addDevice()`

## Flujo de Datos

```
1. Usuario coloca dispositivo en la interfaz (click en canvas)
   ↓
2. createDeviceAtPosition(x, y) captura coordenadas exactas
   ↓
3. Dispositivo se añade a nodes con propiedades x, y
   ↓
4. generateConfigurations() serializa toda la topología
   ↓
5. JSON incluye nodos con coordenadas: {id, label, x, y, data, ...}
   ↓
6. Servidor recibe topology['nodes'] con propiedades x, y
   ↓
7. generate_ptbuilder_script() lee x, y de cada nodo
   ↓
8. addDevice() en PTBuilder usa coordenadas exactas: addDevice("R1", "2811", 150, 200)
   ↓
9. Dispositivo aparece en Packet Tracer en posición (150, 200)
```

## Ejemplo de Salida PTBuilder

Con los dispositivos posicionados en la interfaz:
- Router R1 en posición (150, 200)
- Switch SW1 en posición (-100, 300)
- PC1 en posición (250, 50)

El script PTBuilder generado contendrá:
```
addDevice("R1", "2811", 150, 200);
addDevice("SW1", "2960-24TT", -100, 300);
addDevice("PC1", "PC-PT", 250, 50);
...
```

## Prueba Funcional

Para verificar que funciona:
1. Abre la interfaz visual
2. Posiciona varios dispositivos en diferentes ubicaciones
3. Haz clic en "Generar Configuración"
4. Descarga el script PTBuilder
5. Los dispositivos deberían aparecer en Packet Tracer en las mismas posiciones

## Notas Técnicas

- Las coordenadas se conservan en unidades de píxeles del canvas
- vis.network almacena valores float pero PTBuilder los interpreta como enteros
- La conversión a `int()` redondea al entero más cercano (comportamiento estándar)
- Si se necesita más precisión, se puede cambiar el tipado en la línea 162 de app.py

## Archivos Modificados

- `templates/index_visual.html`: Comentarios en createDeviceAtPosition()
- `app.py`: Mejora de generate_ptbuilder_script() con manejo seguro de coordenadas

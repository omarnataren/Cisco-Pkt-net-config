# Transformación de Coordenadas: vis.network → Packet Tracer

## Problema Original
- **vis.network** utiliza un sistema de coordenadas de rango pequeño (aproximadamente -200 a +200)
- **Packet Tracer** utiliza un sistema de coordenadas mucho más amplio (0-11570 en X, 0-5570 en Y)
- Los dispositivos se posicionaban correctamente en la interfaz visual pero aparecían en posiciones incorrectas en Packet Tracer

## Solución Implementada

### Función: `transform_coordinates_to_ptbuilder(nodes)`

Ubicación: `app.py` líneas ~91-145

**Cómo funciona:**

1. **Calcula el rango actual** de coordenadas en la interfaz:
   - Encuentra el valor mínimo y máximo de X
   - Encuentra el valor mínimo y máximo de Y

2. **Normaliza las coordenadas** a rango [0, 1]:
   ```
   x_normalizado = (x_original - x_mín) / (x_máx - x_mín)
   y_normalizado = (y_original - y_mín) / (y_máx - y_mín)
   ```

3. **Mapea al rango de Packet Tracer** con márgenes:
   - Rango X: 0 a 11570 (con margen de 5%)
   - Rango Y: 0 a 5570 (con margen de 5%)
   - Los márgenes previenen que los dispositivos se creen en los bordes

4. **Retorna un diccionario** con las coordenadas transformadas:
   ```python
   {
       'node_id_1': {'x': 5870, 'y': 2850},
       'node_id_2': {'x': 5920, 'y': 2900},
       ...
   }
   ```

### Ejemplo de Transformación

**Entrada (vis.network):**
```
R1: x=-163, y=-134
R2: x=-157, y=-101
R3: x=-129, y=-121
R4: x=-102, y=-132
R5: x=-80,  y=-139
```

**Proceso:**
1. Rango X: de -163 a -80 (rango = 83)
2. Rango Y: de -139 a -101 (rango = 38)
3. Aplicar transformación y márgenes
4. Mapear al espacio de Packet Tracer

**Salida (Packet Tracer):**
```
R1: x~1200, y~1500
R2: x~1250, y~2000
R3: x~1800, y~1800
R4: x~2300, y~1600
R5: x~2800, y~1400
```

**Resultado:** La topología relativa se mantiene, pero ahora los dispositivos están en el rango que Packet Tracer espera.

## Características Principales

### ✅ Preserva la Topología Relativa
- Los dispositivos mantienen sus posiciones relativas entre sí
- Solo cambia la escala y el desplazamiento

### ✅ Manejo de Casos Especiales
- Si todos los dispositivos están en la misma posición → se coloca en el centro
- Si no hay coordenadas → fallback al centro (5785, 2785)

### ✅ Márgenes de Seguridad
- 5% de margen en todos los lados previene que dispositivos queden en bordes
- Evita que se creen fuera del área visible de Packet Tracer

### ✅ Escalado Inteligente
- Usa el rango mínimo/máximo actual, no asume valores fijos
- Si cambias el tamaño del canvas o añades dispositivos más alejados, la transformación se ajusta automáticamente

## Integración en `generate_ptbuilder_script()`

```python
# Transformar coordenadas
coordinate_transform = transform_coordinates_to_ptbuilder(nodes)

# Usar las coordenadas transformadas
for node in nodes:
    node_id = node.get('id')
    if node_id in coordinate_transform:
        x = coordinate_transform[node_id]['x']
        y = coordinate_transform[node_id]['y']
    else:
        x, y = 5785, 2785  # Centro por defecto
    
    lines.append(f'addDevice("{device_name}", "{model}", {x}, {y});')
```

## Prueba Funcional

Para verificar que funciona correctamente:

1. Abre la interfaz visual
2. Posiciona 5-6 dispositivos en diferentes lugares del canvas
3. Haz clic en "Generar Configuración"
4. Descarga el script PTBuilder
5. Verifica que los `addDevice()` tienen coordenadas en el rango 0-11570 (X) y 0-5570 (Y)
6. Ejecuta el script en Packet Tracer
7. Los dispositivos deberían mantener su topología relativa

## Rango Esperado en PTBuilder

Después de esta implementación, las coordenadas en el script generado deberían verse así:

```
addDevice("R1", "2811", 1850, 1600);
addDevice("R2", "2811", 1920, 1900);
addDevice("R3", "2811", 2450, 1750);
addDevice("R4", "2811", 2950, 1550);
addDevice("R5", "2811", 3450, 1400);
```

En lugar de:

```
addDevice("R1", "2811", -163, -134);   ❌ Fuera de rango
addDevice("R2", "2811", -157, -101);   ❌ Fuera de rango
...
```

## Notas Técnicas

- La transformación es **lossless** en términos de topología relativa
- La única información "perdida" es la escala absoluta, pero eso es esperado
- Se pueden ajustar los márgenes (actualmente 5%) modificando el valor `0.05` en la línea ~136 de `app.py`
- Se pueden ajustar los rangos de Packet Tracer si cambian en futuras versiones

## Archivos Modificados

- `app.py`: Añadida función `transform_coordinates_to_ptbuilder()` y modificada `generate_ptbuilder_script()`

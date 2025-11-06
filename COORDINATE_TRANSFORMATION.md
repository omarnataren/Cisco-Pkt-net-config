# Transformación de Coordenadas: vis.network → Packet Tracer

## Problema Original
- vis.network genera coordenadas en rango pequeño (~-200 a +200)
- Packet Tracer usa rango grande: X: -7500 a 11500 | Y: -1600 a 5600
- Necesitábamos mantener la relación real entre dispositivos sin estirar

## Solución Implementada

### Enfoque: Mantener Proporciones + Centrar

**Paso 1: Calcular el centro de la topología actual**
```
topology_center_x = (x_min + x_max) / 2
topology_center_y = (y_min + y_max) / 2
```

**Paso 2: Desplazar cada punto al origen (restar el centro)**
```
x_relative = (x_orig - topology_center_x) * scale_factor
y_relative = (y_orig - topology_center_y) * scale_factor
```

**Paso 3: Mover al centro de Packet Tracer**
```
x_pt = PT_CENTER_X + x_relative  = 2000 + x_relative
y_pt = PT_CENTER_Y + y_relative  = 2000 + y_relative
```

### Rango de Packet Tracer
- **X**: -7500 a 11500 (rango de 19000, centro en 2000)
- **Y**: -1600 a 5600 (rango de 7200, centro en 2000)
- **Centro**: (2000, 2000)

## Ejemplo Práctico

### Coordenadas en vis.network (tu captura):
```
x: -7590, y: -1230  (posición de un dispositivo)
```

### Proceso de transformación:

1. **Con 5 routers en posiciones:**
   - R1: (-163, -134)
   - R2: (-157, -101)
   - R3: (-129, -121)
   - R4: (-102, -132)
   - R5: (-80, -139)

2. **Calcular centro de la topología:**
   - Centro X = (-163 + -157 + -129 + -102 + -80) / 5 ≈ -126.2
   - Centro Y = (-134 + -101 + -121 + -132 + -139) / 5 ≈ -125.4

3. **Desplazar al origen (ejemplo R1):**
   - x_relative = -163 - (-126.2) = -36.8
   - y_relative = -134 - (-125.4) = -8.6

4. **Mover al centro de Packet Tracer:**
   - x_pt = 2000 + (-36.8) ≈ 1963
   - y_pt = 2000 + (-8.6) ≈ 1991

### Resultado en Packet Tracer:
```
addDevice("R1", "2811", 1963, 1991);
```

## Ventajas del Enfoque

✅ **Mantiene la relación real**: Las distancias entre dispositivos se conservan exactamente como en vis.network

✅ **Permite zoom en Packet Tracer**: Al estar centrada en (2000, 2000), hay espacio en todo el perímetro para zoom

✅ **Escalable**: El parámetro `scale_factor` permite ajustar el tamaño de la topología si es necesario

✅ **Flexible**: El usuario puede hacer zoom después de importar para ver mejor

## Parámetro scale_factor

Si necesitas ajustar el tamaño de la topología en Packet Tracer:

```python
# Escalar 2x más grande
coordinate_transform = transform_coordinates_to_ptbuilder(nodes, scale_factor=2.0)

# Escalar 0.5x más pequeño
coordinate_transform = transform_coordinates_to_ptbuilder(nodes, scale_factor=0.5)
```

**Nota**: Actualmente se usa `scale_factor=1.0` (por defecto), que mantiene las proporciones exactas.

## Archivo Modificado

- `app.py`: Función `transform_coordinates_to_ptbuilder()` actualizada (línea 93)

## Validación

Para verificar que funciona correctamente:

1. Posiciona dispositivos en vis.network
2. Genera el PTBuilder
3. Los dispositivos deberían estar centrados en Packet Tracer alrededor de (2000, 2000)
4. La topología mantiene la misma forma y proporciones

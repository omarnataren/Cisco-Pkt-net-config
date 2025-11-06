# Verificación: Flujo de Actualización de Coordenadas

## Checklist de Verificación

### 1️⃣ Frontend - Actualización en tiempo real
- [ ] Coloca un dispositivo en la interfaz
- [ ] Abre la consola (F12)
- [ ] Mueve el dispositivo varias veces
- [ ] **Verifica que ves mensajes como:** `✓ Dispositivo R1 actualizado a: x=-46, y=-190`
- [ ] Cada vez que lo mueves, las coordenadas deben cambiar

### 2️⃣ Frontend - Envío de datos actualizados
- [ ] Mantén abierta la consola
- [ ] Haz clic en "Generar Configuración"
- [ ] **Verifica que ves:**
```
📊 Coordenadas de dispositivos a enviar:
  R1: x=-46, y=-190
```
- [ ] Las coordenadas mostradas deben ser las NUEVAS (después de mover)

### 3️⃣ Backend - Recepción de coordenadas
- [ ] Mira la terminal donde corre el servidor Flask
- [ ] **Verifica que ves:**
```
🔍 COORDINADAS RECIBIDAS DEL CLIENTE:
  R1: x=-46, y=-190
```
- [ ] Deben coincidir exactamente con lo que enviaste desde el navegador

### 4️⃣ Backend - Transformación de coordenadas
- [ ] En la misma terminal del servidor
- [ ] **Verifica que ves:**
```
🔄 COORDENADAS TRANSFORMADAS AL RANGO DE PACKET TRACER:
  R1: (-46, -190) → (1968, 1895)
```
- [ ] Las coordenadas deben estar en el rango de Packet Tracer (aprox. 2000 ± algo)

### 5️⃣ Verificación del archivo descargado
- [ ] Descarga el PTBuilder desde la nueva pestaña
- [ ] Abre el archivo `topology_ptbuilder.txt`
- [ ] **Verifica que contiene:**
```
addDevice("R1", "2811", 1968, 1895);
```
- [ ] Las coordenadas deben coincidir con las transformadas

## Flujo Completo

```
Usuario mueve dispositivo en interfaz
         ↓
dragEnd event se dispara
         ↓
network.getPositions() obtiene posición actual
         ↓
nodes.update() actualiza el DataSet
         ↓
console.log muestra: "✓ Dispositivo R1 actualizado a: x=-46, y=-190"
         ↓
Usuario hace clic en "Generar Configuración"
         ↓
console.log muestra: "📊 Coordenadas de dispositivos a enviar:"
         ↓
Datos se envían al servidor en POST
         ↓
Servidor muestra: "🔍 COORDINADAS RECIBIDAS DEL CLIENTE:"
         ↓
Se transforman las coordenadas
         ↓
Servidor muestra: "🔄 COORDENADAS TRANSFORMADAS"
         ↓
Se genera el archivo PTBuilder
         ↓
Usuario descarga el archivo
         ↓
Archivo contiene: addDevice("R1", "2811", 1968, 1895);
```

## Problemas Posibles y Soluciones

### Problema: Las coordenadas en la consola no cambian después de mover
**Solución:** El evento dragEnd no se está disparando. Verifica que `dragNodes: true` está en las opciones de vis.network.

### Problema: El servidor recibe las coordenadas originales, no las actualizadas
**Solución:** Los datos no se están actualizando en el DataSet. Verifica que `nodes.update()` se llama en el dragEnd.

### Problema: El archivo PTBuilder tiene coordenadas incorrectas
**Solución:** La transformación puede estar mal. Verifica que:
- `transform_coordinates_to_ptbuilder()` calcula correctamente el centro
- Las coordenadas transformadas están dentro del rango esperado (~2000 ± distancia)

## Debugging Commands

En la consola del navegador (F12):
```javascript
// Ver todas las coordenadas actuales
nodes.get().forEach(n => console.log(`${n.data.name}: x=${n.x}, y=${n.y}`))

// Ver posición de un nodo específico
network.getPositions(['router_1234567890'])
```

En la terminal del servidor:
```bash
# Buscar los logs de debug
grep "🔍\|🔄" output.log
```

## Notas Técnicas

- Las coordenadas de vis.network están en píxeles del canvas
- Las coordenadas de Packet Tracer están en una escala de -7500 a 11500 (X) y -1600 a 5600 (Y)
- La transformación mantiene la proporción y centra la topología en (2000, 2000)
- El factor de escala es 1.0 por defecto (no estira la topología)

# Actualización Dinámíca de Coordenadas al Mover Dispositivos

## Descripción
Cuando el usuario mueve un dispositivo en la interfaz visual (arrastrando con el ratón), las nuevas coordenadas se actualizan automáticamente y se usan en la generación del PTBuilder.

## Cómo Funciona

### 1. Evento `dragEnd` en vis.network

**Ubicación**: `templates/index_visual.html` (líneas 240-260 aproximadamente)

```javascript
network.on('dragEnd', function(params) {
    if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodeData = nodes.get(nodeId);
        
        // Las nuevas coordenadas ya están en nodeData.x y nodeData.y
        // vis.network actualiza automáticamente estas propiedades
        console.log(`Dispositivo ${nodeData.label} movido a: x=${nodeData.x}, y=${nodeData.y}`);
        
        // Actualizar el nodo con las nuevas coordenadas
        nodes.update({
            id: nodeId,
            x: nodeData.x,
            y: nodeData.y
        });
    }
});
```

### 2. Cómo se Ejecuta

**Paso a paso:**

1. **Usuario arrastra un dispositivo** en el canvas
   - Hace clic y arrastra el dispositivo a una nueva posición
   - vis.network actualiza automáticamente x, y del nodo

2. **Se dispara el evento `dragEnd`**
   - Se ejecuta cuando el usuario suelta el ratón (fin del arrastre)
   - `params.nodes` contiene el ID del nodo que se movió

3. **Se obtiene el nodeData actualizado**
   - `nodes.get(nodeId)` retorna el nodo con las nuevas coordenadas x, y

4. **Se confirma la actualización**
   - `nodes.update()` se llama para asegurar que las coordenadas se guarden
   - Se imprime un log de debug con la nueva posición

5. **Al generar PTBuilder**
   - Cuando haces clic en "Generar Configuración"
   - `nodes.get()` retorna todos los nodos con sus coordenadas **actualizadas**
   - El servidor recibe las coordenadas finales correctas
   - La transformación de coordenadas se aplica correctamente

## Flujo Completo

```
1. Usuario posiciona dispositivo inicial (click)
   → createDeviceAtPosition(x, y) crea nodo con x, y iniciales
   
2. Usuario arrastra dispositivo a nueva posición
   → vis.network actualiza x, y automáticamente
   → Evento dragEnd se dispara
   → console.log muestra nueva posición
   → nodes.update() confirma el cambio
   
3. Usuario cambia de opinión y arrastra de nuevo
   → Evento dragEnd se dispara nuevamente
   → Coordenadas se actualizan nuevamente
   
4. Usuario hace clic en "Generar Configuración"
   → nodes.get() retorna todos los nodos con coordenadas FINALES
   → JSON incluye: {id, label, x: 150.5, y: -200.3, data, ...}
   
5. Servidor recibe topología con coordenadas actualizadas
   → transform_coordinates() convierte las coordenadas FINALES
   → PTBuilder recibe las coordenadas mapeadas correctas
```

## Ejemplo Práctico

**Escenario:**
1. Posicionas R1 en (100, -50) 
2. Lo arrastras a (200, 100)
3. Lo arrastras nuevamente a (150, 75)
4. Generas la configuración

**Lo que sucede internamente:**
- Primera creación: nodo tiene x=100, y=-50
- Primer dragEnd: nodo tiene x=200, y=100 ✓
- Segundo dragEnd: nodo tiene x=150, y=75 ✓
- Al generar: se usan coordenadas finales (150, 75)

**Output PTBuilder:**
```
addDevice("R1", "2811", COORDENADAS_TRANSFORMADAS_DE_(150,_75));
```

## Consola de Debug

Para verificar que todo funciona, abre la consola del navegador (F12) y verás mensajes como:

```
Dispositivo R1 movido a: x=200, y=100
Dispositivo R1 movido a: x=150, y=75
Dispositivo SW1 movido a: x=-50, y=-200
```

## Notas Técnicas

### ¿Por qué se llama `nodes.update()`?

Aunque vis.network actualiza las coordenadas automáticamente al arrastrar, llamar a `nodes.update()` asegura que:
1. Los cambios se propagan correctamente
2. El estado interno de la DataSet se sincroniza
3. No hay inconsistencias entre lo visual y los datos almacenados

### ¿Se pierden coordenadas al actualizar?

**No.** vis.network mantiene todas las propiedades del nodo cuando se arrastra:
- Se actualiza: x, y
- Se mantienen: id, label, data, color, shape, etc.

### ¿Y si el usuario no mueve el dispositivo?

**Funciona igual:**
- Las coordenadas iniciales se usan
- El evento dragEnd solo se dispara si realmente se mueve

## Cambios Realizados

- Agregado evento `dragEnd` a `network.on()`
- Limpieza de `console.log` de debug en el evento click
- Se mantiene el `console.log` en dragEnd para verificación
- Comentarios actualizados en el código

## Archivos Modificados

- `templates/index_visual.html`: Evento dragEnd agregado

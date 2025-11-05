# 🐛 Error de Descarga de PTBuilder - Explicación y Solución

## ¿Qué pasaba?

Cuando intentabas descargar el script PTBuilder, recibías este error:
```
Tipo de dispositivo no válido. Tipos válidos: routers, switch_cores, switches, completo
```

## ¿Por qué ocurría?

El error venía de la función `download_by_type()` en `app.py` (línea 1117).

### Causa raíz:
1. **`ptbuilder` no estaba en la lista de tipos válidos** - El diccionario `file_names` solo tenía 4 tipos (routers, switch_cores, switches, completo), pero el botón HTML intentaba descargar `/download/ptbuilder`

2. **El contenido de PTBuilder no se guardaba en `config_files_content`** - La función `generate_ptbuilder_script()` solo escribía a un archivo en disco (`topology_ptbuilder.txt`) pero no guardaba el contenido en la estructura de datos global que usa el endpoint `/download`

## Solución Implementada

### 1. **Modificar `generate_ptbuilder_script()` para retornar contenido**

**Antes:**
```python
def generate_ptbuilder_script(topology, router_configs, computers):
    # ... genera líneas ...
    with open("topology_ptbuilder.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
```

**Después:**
```python
def generate_ptbuilder_script(topology, router_configs, computers):
    # ... genera líneas ...
    ptbuilder_content = "\n".join(lines)
    
    # Guardar en archivo para compatibilidad
    with open("topology_ptbuilder.txt", "w", encoding="utf-8") as f:
        f.write(ptbuilder_content)
    
    return ptbuilder_content  # ← NUEVO: Retornar el contenido
```

**Beneficio:** Ahora la función retorna el contenido generado para que pueda ser guardado en memoria.

---

### 2. **Guardar el contenido de PTBuilder en `config_files_content`**

**Ubicación:** Línea ~1024 en `app.py`

**Antes:**
```python
config_files_content = generate_separated_txt_files(router_configs)
generate_ptbuilder_script(topology, router_configs, computers)  # ← Se ignoraba el retorno
```

**Después:**
```python
config_files_content = generate_separated_txt_files(router_configs)
ptbuilder_content = generate_ptbuilder_script(topology, router_configs, computers)
config_files_content['ptbuilder'] = ptbuilder_content  # ← NUEVO: Guardar en dict
```

**Beneficio:** Ahora el contenido de PTBuilder se almacena en la misma estructura que los otros tipos de configuración.

---

### 3. **Agregar `ptbuilder` a los tipos válidos de descarga**

**Ubicación:** Línea ~1119 en `app.py`

**Antes:**
```python
file_names = {
    'routers': 'config_routers.txt',
    'switch_cores': 'config_switch_cores.txt',
    'switches': 'config_switches.txt',
    'completo': 'config_completo.txt'
}
```

**Después:**
```python
file_names = {
    'routers': 'config_routers.txt',
    'switch_cores': 'config_switch_cores.txt',
    'switches': 'config_switches.txt',
    'completo': 'config_completo.txt',
    'ptbuilder': 'topology_ptbuilder.txt'  # ← NUEVO: Agregar ptbuilder
}
```

**Beneficio:** Ahora `/download/ptbuilder` es reconocido como un tipo válido.

---

### 4. **Actualizar mensaje de error**

**Antes:**
```
Tipo de dispositivo no válido. Tipos válidos: routers, switch_cores, switches, completo
```

**Después:**
```
Tipo de dispositivo no válido. Tipos válidos: routers, switch_cores, switches, completo, ptbuilder
```

**Beneficio:** El mensaje ahora es más informativo.

---

### 5. **Actualizar documentación**

Se actualizó el docstring de `download_by_type()` para incluir ptbuilder en:
- Descripción de argumentos
- Lista de URLs disponibles
- Ejemplos de uso

## Flujo Completo Ahora

```
1. Usuario genera topología (click en "Generar Configuración")
   ↓
2. Se llama a generate_separated_txt_files() 
   → Guardado en config_files_content['routers'], ['switches'], etc.
   ↓
3. Se llama a generate_ptbuilder_script()
   → Genera el contenido
   → Lo guarda en archivo (topology_ptbuilder.txt)
   → LO RETORNA
   ↓
4. El contenido retornado se guarda:
   → config_files_content['ptbuilder'] = ptbuilder_content
   ↓
5. Usuario hace clic en "Descargar PTBuilder Script"
   → Browser solicita /download/ptbuilder
   ↓
6. download_by_type('ptbuilder') ejecuta:
   ✓ Valida que 'ptbuilder' esté en file_names ✓
   ✓ Busca config_files_content['ptbuilder'] ✓
   ✓ Lo envía como descarga ✓
```

## Pruebas Realizadas

- ✅ Sintaxis Python validada (`py_compile`)
- ✅ Servidor Flask inicia correctamente
- ✅ Se puede generar topología exitosamente
- ✅ Se pueden descargar otros tipos (routers, completo)
- ✅ Ahora `/download/ptbuilder` es reconocido

## Próximo Paso

Intenta nuevamente:
1. Genera una topología (agrega dispositivos, conexiones, etc.)
2. Haz clic en "Generar Configuración"
3. Haz clic en "📦 Descargar PTBuilder Script"

**Debería funcionar sin errores y descargar `topology_ptbuilder.txt`**

## Archivos Modificados

- `app.py`
  - Línea 93-223: `generate_ptbuilder_script()` ahora retorna contenido
  - Línea 1024-1026: Se guarda el contenido en `config_files_content`
  - Línea 1119-1124: Se agrega 'ptbuilder' al diccionario de tipos válidos
  - Línea 1128: Se actualiza el mensaje de error
  - Línea 1077-1119: Se actualiza la documentación

## Notas Técnicas

- El archivo `topology_ptbuilder.txt` se sigue escribiendo en disco para compatibilidad con herramientas externas
- El contenido también se guarda en memoria para descargas a través del navegador
- Los dos sistemas (disco + memoria) trabajan en paralelo, sin conflictos

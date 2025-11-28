// Agregar VLAN
export function addVLAN() {
    const name = document.getElementById('vlan-name').value.trim();
    const prefix = parseInt(document.getElementById('vlan-prefix').value);
    
    if (!name) {
        showNotification('Ingresa un nombre para la VLAN', 'error');
        return;
    }
    
    // ✅ VALIDACIÓN: Rechazar prefijos /31 y /32 (no soportan DHCP)
    if (prefix >= 31) {
        showNotification('⚠️ Error: Los prefijos /31 y /32 no soportan DHCP. Usa máximo /30 (4 IPs).', 'error');
        return;
    }
    
    // Validar rango de prefijo
    if (prefix < 8 || prefix > 30 || isNaN(prefix)) {
        showNotification('⚠️ El prefijo debe estar entre /8 y /30', 'error');
        return;
    }
    
    // Verificar que no exista
    if (window.vlans.find(v => v.name === name)) {
        showNotification('Esta VLAN ya existe', 'error');
        return;
    }
    
    // Inicializar con isNative: false
    window.vlans.push({ name: name, prefix: prefix, isNative: false });
    document.getElementById('vlan-name').value = '';
    document.getElementById('vlan-prefix').value = '';
    updateVLANList();
    showNotification('✅ VLAN ' + name + ' agregada (/' + prefix + ')');
}

// Establecer VLAN nativa
export function setNativeVLAN(index) {
    // Resetear todas
    window.vlans.forEach(v => v.isNative = false);
    // Establecer la seleccionada
    if (window.vlans[index]) {
        window.vlans[index].isNative = true;
    }
    updateVLANList();
}

// Actualizar lista de VLANs
export function updateVLANList() {
    const list = document.getElementById('vlan-list');
    const hint = document.getElementById('vlan-hint');
    
    list.innerHTML = '';
    
    // Mostrar/ocultar mensaje de ayuda
    if (window.vlans.length > 0) {
        if (hint) hint.style.display = 'block';
    } else {
        if (hint) hint.style.display = 'none';
    }
    
    window.vlans.forEach((vlan, index) => {
        const item = document.createElement('div');
        item.className = 'vlan-item';
        
        // Checkbox/Radio para nativa
        const nativeBadge = vlan.isNative ? 
            '<span style="color: #58a6ff; font-size: 10px; margin-left: 5px; font-weight: bold;">Nativa</span>' : '';
            
        const radioChecked = vlan.isNative ? 'checked' : '';
        
        item.innerHTML = `
            <div class="vlan-item-info" style="display: flex; align-items: center;">
                <input type="radio" name="native_vlan" 
                       onclick="setNativeVLAN(${index})" 
                       ${radioChecked} 
                       style="margin-right: 8px; cursor: pointer;">
                <div>
                    <div class="vlan-item-name">
                        ${vlan.name}
                        ${nativeBadge}
                    </div>
                    <div class="vlan-item-prefix">Prefijo: /${vlan.prefix}</div>
                </div>
            </div>
            <button class="vlan-item-delete" onclick="deleteVLAN(${index})">✕</button>
        `;
        list.appendChild(item);
    });
    
    // Actualizar select de computadoras
    updateComputerVlanSelect();
}

// Eliminar VLAN
export function deleteVLAN(index) {
    window.vlans.splice(index, 1);
    updateVLANList();
    showNotification('VLAN eliminada');
}

// Actualizar select de VLANs para computadoras
export function updateComputerVlanSelect() {
    const select = document.getElementById('computer-vlan-select');
    select.innerHTML = '<option value="">-- Selecciona VLAN --</option>';
    window.vlans.forEach(vlan => {
        const option = document.createElement('option');
        option.value = vlan.name;
        const nativeText = vlan.isNative ? ' (Nativa)' : '';
        option.textContent = vlan.name + ' (/' + vlan.prefix + ')' + nativeText;
        select.appendChild(option);
    });
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.addVLAN = addVLAN;
window.updateVLANList = updateVLANList;
window.deleteVLAN = deleteVLAN;
window.setNativeVLAN = setNativeVLAN;
window.updateComputerVlanSelect = updateComputerVlanSelect;
// Agregar VLAN
export function addVLAN() {
    const name = document.getElementById('vlan-name').value.trim();
    const prefix = document.getElementById('vlan-prefix').value;
    
    if (!name) {
        showNotification('Ingresa un nombre para la VLAN', 'error');
        return;
    }
    // Verificar que no exista
    if (vlans.find(v => v.name === name)) {
        showNotification('Esta VLAN ya existe', 'error');
        return;
    }
    
    vlans.push({ name: name, prefix: prefix });
    document.getElementById('vlan-name').value = '';
    updateVLANList();
    showNotification('VLAN ' + name + ' agregada');
}

// Actualizar lista de VLANs
export function updateVLANList() {
    const list = document.getElementById('vlan-list');
    list.innerHTML = '';
    
    vlans.forEach((vlan, index) => {
const item = document.createElement('div');
item.className = 'vlan-item';
item.innerHTML = `
    <div class="vlan-item-info">
        <div class="vlan-item-name">${vlan.name}</div>
        <div class="vlan-item-prefix">Prefijo: /${vlan.prefix}</div>
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
    vlans.splice(index, 1);
    updateVLANList();
    showNotification('VLAN eliminada');
}

// Actualizar select de VLANs para computadoras
export function updateComputerVlanSelect() {
    const select = document.getElementById('computer-vlan-select');
    select.innerHTML = '<option value="">-- Selecciona VLAN --</option>';
    vlans.forEach(vlan => {
const option = document.createElement('option');
option.value = vlan.name;
option.textContent = vlan.name + ' (/' + vlan.prefix + ')';
select.appendChild(option);
    });
}

// ✅ Exponer funciones globalmente para compatibilidad con HTML onclick
window.addVLAN = addVLAN;
window.updateVLANList = updateVLANList;
window.deleteVLAN = deleteVLAN;
window.updateComputerVlanSelect = updateComputerVlanSelect;
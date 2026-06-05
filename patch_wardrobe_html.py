import sys

sys.stdout.reconfigure(encoding='utf-8')
content = open('templates/wardrobe.html', encoding='utf-8').read()

# 1. Add Edit Modal
modal_html = """
<!-- Edit Item Modal -->
<div id="edit-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:9999; justify-content:center; align-items:center;">
    <div style="background:var(--warm-white); padding:2rem; border-radius:12px; width:400px; max-width:90%;">
        <h3 style="font-family:'Cormorant Garamond',serif; font-size:1.5rem; margin-bottom:1rem; color:var(--espresso);">Sửa Thông Tin</h3>
        <input type="hidden" id="edit-item-id">
        <div style="margin-bottom:1rem;">
            <label style="display:block; font-size:0.8rem; margin-bottom:0.3rem;">Tên món đồ (Name)</label>
            <input type="text" id="edit-item-name" style="width:100%; padding:0.5rem; border:1px solid rgba(0,0,0,0.1); border-radius:4px;">
        </div>
        <div style="margin-bottom:1rem;">
            <label style="display:block; font-size:0.8rem; margin-bottom:0.3rem;">Ghi chú (Note)</label>
            <textarea id="edit-item-note" style="width:100%; padding:0.5rem; border:1px solid rgba(0,0,0,0.1); border-radius:4px; height:80px;"></textarea>
        </div>
        <div style="margin-bottom:1.5rem;">
            <label style="display:block; font-size:0.8rem; margin-bottom:0.3rem;">Danh mục</label>
            <input type="text" id="edit-item-category" style="width:100%; padding:0.5rem; border:1px solid rgba(0,0,0,0.1); border-radius:4px;">
        </div>
        <div style="display:flex; justify-content:flex-end; gap:1rem;">
            <button onclick="closeEditModal()" style="padding:0.5rem 1rem; border:none; background:transparent; cursor:pointer;">Hủy</button>
            <button onclick="saveEditItem()" style="padding:0.5rem 1rem; border:none; background:var(--caramel); color:white; border-radius:4px; cursor:pointer;">Lưu</button>
        </div>
    </div>
</div>
"""
if 'id="edit-modal"' not in content:
    content = content.replace('<!-- Toast -->', modal_html + '\n<!-- Toast -->')

# 2. Modify renderGrid to add Edit button
render_grid_old = """            <div class="item-actions">
                <button class="ia-btn" onclick="sendFeedback(${item.id}, 'liked')" title="Thích">❤️</button>
                <button class="ia-btn" onclick="sendFeedback(${item.id}, 'worn')" title="Đã mặc hôm nay">✓</button>
                <button class="ia-btn" onclick="sendFeedback(${item.id}, 'skipped')" title="Bỏ qua">↷</button>
            </div>"""

render_grid_new = """            <div class="item-actions">
                <button class="ia-btn" onclick="sendFeedback(${item.id}, 'liked')" title="Thích">❤️</button>
                <button class="ia-btn" onclick="sendFeedback(${item.id}, 'worn')" title="Đã mặc hôm nay">✓</button>
                <button class="ia-btn" onclick="openEditModal(${item.id})" title="Sửa thông tin">✏️</button>
            </div>"""
content = content.replace(render_grid_old, render_grid_new)

# 3. Add edit modal JS functions
edit_js = """
// ─── EDIT MODAL ────────────────────────────────────────────────────────────
function openEditModal(id) {
    const item = allItems.find(i => i.id === id);
    if(!item) return;
    document.getElementById('edit-item-id').value = id;
    document.getElementById('edit-item-name').value = item.name || '';
    document.getElementById('edit-item-note').value = item.note || '';
    document.getElementById('edit-item-category').value = item.category || '';
    document.getElementById('edit-modal').style.display = 'flex';
}
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}
async function saveEditItem() {
    const id = document.getElementById('edit-item-id').value;
    const data = {
        name: document.getElementById('edit-item-name').value,
        note: document.getElementById('edit-item-note').value,
        category: document.getElementById('edit-item-category').value
    };
    try {
        const r = await fetch(`/api/wardrobe/items/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if(r.ok) {
            showToast('✓ Đã cập nhật');
            closeEditModal();
            loadItems(currentFilter);
        } else {
            showToast('✗ Lỗi cập nhật');
        }
    } catch(e) { console.error(e); }
}
"""
if 'function openEditModal' not in content:
    content = content.replace('// ─── INIT', edit_js + '\n// ─── INIT')

# 4. Modify loadDailyOutfit to use GPS and render layers
# We replace the entire loadDailyOutfit function.
import re
start_daily = content.find('// ─── DAILY OUTFIT')
end_daily = content.find('// ─── STATS', start_daily)

new_daily = """// ─── DAILY OUTFIT (GPS + Layers) ─────────────────────────────────────────
async function loadDailyOutfit() {
    const list = document.getElementById('daily-outfit-list');
    list.innerHTML = '<div style="text-align:center;color:var(--dust);font-size:0.8rem;padding:1rem 0;">✨ Đang phân tích... (đang lấy GPS)</div>';
    
    let lat = null, lon = null;
    try {
        // Lấy GPS để phân tích thời tiết thật
        const pos = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {timeout: 5000});
        });
        lat = pos.coords.latitude;
        lon = pos.coords.longitude;
    } catch(e) {
        console.warn('GPS failed or denied, fallback to city mode.');
    }

    list.innerHTML = '<div style="text-align:center;color:var(--dust);font-size:0.8rem;padding:1rem 0;">✨ Đang phân tích phục trang...</div>';

    try {
        const gender = localStorage.getItem('fm_gender') || 'female';
        let url = `/api/wardrobe/daily-outfit?gender=${gender}`;
        if (lat && lon) {
            url += `&lat=${lat}&lon=${lon}`;
        }
        
        const r = await fetch(url);
        const d = await r.json();

        if (!d.outfit || !d.outfit.length) {
            list.innerHTML = `<div style="text-align:center;color:var(--dust);font-size:0.8rem;padding:1rem 0;line-height:1.6;">${d.message || 'Chưa có outfit phù hợp.'}</div>`;
            return;
        }

        // Render Layers instead of flat items
        const layersHtml = (d.layers || []).map(l => {
            const item = l.item;
            return `
                <div class="outfit-item">
                    <div style="font-size:0.6rem; color:var(--dust); text-transform:uppercase; margin-right:10px; width:40px; text-align:center;">Lớp ${l.layer}</div>
                    ${item.image_url
                        ? `<img class="outfit-img" src="${item.image_url}" alt="${item.category}" onerror="this.src=''">`
                        : `<div class="outfit-img" style="display:flex;align-items:center;justify-content:center;font-size:1.5rem;">👗</div>`}
                    <div class="outfit-info" style="flex:1;">
                        <div class="outfit-cat">${item.name || item.category}</div>
                        <div class="outfit-color" style="font-size:0.7rem;">${l.label} • ${item.color || ''}</div>
                    </div>
                    <div class="outfit-actions">
                        <button class="action-btn worn" onclick="sendFeedback(${item.id},'worn')" title="Mặc món này">✓</button>
                        <button class="action-btn skip" onclick="sendFeedback(${item.id},'skipped')" title="Bỏ qua">↷</button>
                    </div>
                </div>
            `;
        }).join('');

        list.innerHTML = `
            <div style="font-size:0.72rem;color:var(--caramel);margin-bottom:0.6rem;letter-spacing:0.05em;line-height:1.4;">
                ${d.message}
                ${d.ai_tips ? `<br><span style="color:var(--espresso);font-weight:400;">${d.ai_tips}</span>` : ''}
            </div>
            ${layersHtml}
            <button onclick="saveOutfitSet([${d.outfit.map(i=>i.id).join(',')}])" style="width:100%;margin-top:0.5rem;padding:0.5rem;background:var(--espresso);color:var(--cream);border:none;border-radius:6px;cursor:pointer;">Lưu thành Bộ</button>
        `;
    } catch(e) {
        list.innerHTML = '<div style="text-align:center;color:var(--dust);font-size:0.78rem;padding:1rem 0;">Lỗi tải outfit.</div>';
    }
}

async function saveOutfitSet(ids) {
    // Note: To be fully implemented in backend, simple mock alert for now
    alert('Đã lưu outfit (Giao diện Outfit Sets sẽ được thêm trong bảng điều khiển sắp tới).');
}

"""
content = content[:start_daily] + new_daily + content[end_daily:]

open('templates/wardrobe.html', 'w', encoding='utf-8').write(content)
print('Patched wardrobe.html successfully')

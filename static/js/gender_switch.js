/**
 * Gender Switch — Đổi ảnh theo giới tính (Nam/Nữ)
 * =================================================
 * - Đọc/lưu gender từ localStorage + server session
 * - Swap tất cả ảnh có attribute data-male-src / data-female-src
 * - Inject gender toggle vào nav (nếu chưa có)
 * - Phát sự kiện 'genderchange' cho các component khác
 */

(function() {
    'use strict';

    const GENDER_KEY = 'fm_gender';
    let currentGender = localStorage.getItem(GENDER_KEY) || 'female';

    // ─── GENDER IMAGES MAP ───────────────────────────────────────────────────
    // Default ảnh cho các section chưa có data attribute
    // Sử dụng URL từ Unsplash với param để phân biệt nam/nữ

    const SECTION_IMAGES = {
        // Personal Color section
        'personal_color': {
            male:   'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80',
            female: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&auto=format&fit=crop&q=80',
        },
        // Face Shape section
        'face_shape': {
            male:   'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&auto=format&fit=crop&q=80',
            female: 'https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=400&auto=format&fit=crop&q=80',
        },
        // Body Shape section
        'body_shape': {
            male:   'https://images.unsplash.com/photo-1571945153237-4929e783af4a?w=400&auto=format&fit=crop&q=80',
            female: 'https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=400&auto=format&fit=crop&q=80',
        },
        // AI Chat section
        'chatbot': {
            male:   'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&auto=format&fit=crop&q=80',
            female: 'https://images.unsplash.com/photo-1534751516642-a1af1ef26a56?w=400&auto=format&fit=crop&q=80',
        },
    };

    // ─── APPLY GENDER IMAGES ──────────────────────────────────────────────────

    function applyGenderImages(gender) {
        // 1. Swap tất cả ảnh có data-male-src / data-female-src
        document.querySelectorAll('[data-male-src], [data-female-src]').forEach(img => {
            const src = gender === 'male'
                ? img.getAttribute('data-male-src')
                : img.getAttribute('data-female-src');
            if (src) {
                // Fade effect
                img.style.opacity = '0';
                img.style.transition = 'opacity 0.35s ease';
                setTimeout(() => {
                    img.src = src;
                    img.onload = () => { img.style.opacity = '1'; };
                    img.onerror = () => { img.style.opacity = '1'; };
                }, 180);
            }
        });

        // 2. Swap section images theo data-section attribute
        document.querySelectorAll('[data-section]').forEach(el => {
            const section = el.getAttribute('data-section');
            if (SECTION_IMAGES[section]) {
                const img = el.querySelector('img, .section-img');
                if (img) {
                    const src = SECTION_IMAGES[section][gender];
                    if (src && img.src !== src) {
                        img.style.opacity = '0';
                        img.style.transition = 'opacity 0.35s ease';
                        setTimeout(() => {
                            img.src = src;
                            img.onload = () => { img.style.opacity = '1'; };
                        }, 180);
                    }
                }
            }
        });

        // 3. Cập nhật các text có gender placeholder
        document.querySelectorAll('[data-gender-text]').forEach(el => {
            const texts = el.getAttribute('data-gender-text').split('|');
            el.textContent = gender === 'male' ? (texts[0] || '') : (texts[1] || texts[0] || '');
        });

        // 4. Phát event
        window.dispatchEvent(new CustomEvent('genderchange', { detail: { gender } }));
    }

    // ─── SWITCH GENDER ────────────────────────────────────────────────────────

    function setGender(gender) {
        if (gender !== 'male' && gender !== 'female') return;
        currentGender = gender;
        localStorage.setItem(GENDER_KEY, gender);

        // Cập nhật toggle buttons
        document.querySelectorAll('.gender-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.gender === gender);
        });

        // Apply images
        applyGenderImages(gender);

        // Đồng bộ với server
        fetch('/api/set-gender', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ gender }),
        }).catch(() => {}); // fail silently
    }

    // ─── CREATE TOGGLE UI ────────────────────────────────────────────────────

    function createGenderToggle() {
        // Tránh tạo trùng
        if (document.getElementById('gender-toggle')) return;

        const toggle = document.createElement('div');
        toggle.id = 'gender-toggle';
        toggle.title = 'Chọn giới tính để hiển thị ảnh phù hợp';
        toggle.innerHTML = `
            <button class="gender-btn ${currentGender === 'female' ? 'active' : ''}" data-gender="female" aria-label="Nữ">
                ♀ Nữ
            </button>
            <button class="gender-btn ${currentGender === 'male' ? 'active' : ''}" data-gender="male" aria-label="Nam">
                ♂ Nam
            </button>
        `;

        toggle.addEventListener('click', e => {
            const btn = e.target.closest('.gender-btn');
            if (btn) setGender(btn.dataset.gender);
        });

        // Chèn vào nav nếu tìm thấy
        const nav = document.querySelector('nav');
        if (nav) {
            nav.appendChild(toggle);
        } else {
            // Fallback: fixed position
            toggle.style.cssText = `
                position: fixed;
                top: 16px;
                right: 20px;
                z-index: 9997;
            `;
            document.body.appendChild(toggle);
        }
    }

    // ─── PUBLIC API ──────────────────────────────────────────────────────────

    window.GenderSwitch = {
        getGender:    () => currentGender,
        setGender:    setGender,
        toggle:       () => setGender(currentGender === 'male' ? 'female' : 'male'),
    };

    // ─── INIT ─────────────────────────────────────────────────────────────────

    function init() {
        createGenderToggle();
        applyGenderImages(currentGender);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

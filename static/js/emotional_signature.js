/**
 * Emotional Signature Engine — Frontend
 * =======================================
 * 1. Kết nối camera qua getUserMedia()
 * 2. Dùng MediaPipe FaceMesh để track landmarks khuôn mặt
 * 3. Tính velocity từ delta landmarks theo thời gian thực
 * 4. Gửi seed lên /api/emotional-signature mỗi 5 giây
 * 5. Áp dụng theme CSS và cập nhật badge
 */

(function() {
    'use strict';

    const CONFIG = {
        UPDATE_INTERVAL_MS:  5000,   // Gửi signature mỗi 5 giây
        MIN_LANDMARKS:       5,      // Số landmarks tối thiểu để xử lý
        CAMERA_WIDTH:        320,
        CAMERA_HEIGHT:       240,
        MAX_VELOCITY:        0.5,    // Clamp velocity để tránh outliers
    };

    let videoEl       = null;
    let faceMeshReady = false;
    let faceMesh      = null;
    let lastLandmarks = null;
    let lastTimestamp = Date.now();
    let updateTimer   = null;
    let currentTheme  = localStorage.getItem('em_theme') || 'warm_glow';
    let currentMood   = localStorage.getItem('em_mood')  || 'calm';
    let currentSig    = localStorage.getItem('em_sig')   || '';

    // ─── DOM SETUP ────────────────────────────────────────────────────────────

    function createHiddenVideo() {
        const v = document.createElement('video');
        v.id       = 'em-video-feed';
        v.style.cssText = 'position:fixed;opacity:0;pointer-events:none;width:1px;height:1px;top:-1px;left:-1px;';
        v.autoplay = true;
        v.muted    = true;
        v.playsInline = true;
        document.body.appendChild(v);
        return v;
    }

    function createBadge() {
        if (document.getElementById('em-signature-badge')) return;
        const badge = document.createElement('div');
        badge.id = 'em-signature-badge';
        badge.innerHTML = `
            <span class="badge-emoji">🌊</span>
            <span class="badge-text">Calm</span>
            <span class="badge-code">••••••••</span>
        `;
        badge.title = 'Mã Định Danh Cảm Xúc của bạn';
        document.body.appendChild(badge);
    }

    function createOverlay() {
        if (document.getElementById('theme-transition-overlay')) return;
        const overlay = document.createElement('div');
        overlay.id = 'theme-transition-overlay';
        document.body.appendChild(overlay);
    }

    function updateBadge(data) {
        const badge = document.getElementById('em-signature-badge');
        if (!badge) return;
        badge.querySelector('.badge-emoji').textContent  = data.emoji   || '🌊';
        badge.querySelector('.badge-text').textContent   = data.description || 'Calm';
        badge.querySelector('.badge-code').textContent   = (data.signature || '').slice(0, 8) + '…';
        badge.classList.add('visible');
    }

    // ─── THEME APPLICATION ────────────────────────────────────────────────────

    function applyTheme(theme) {
        if (theme === currentTheme && document.documentElement.getAttribute('data-theme') === theme) return;

        // Flash overlay
        const overlay = document.getElementById('theme-transition-overlay');
        if (overlay) {
            overlay.classList.add('flash');
            setTimeout(() => overlay.classList.remove('flash'), 350);
        }

        document.documentElement.setAttribute('data-theme', theme);
        currentTheme = theme;
        localStorage.setItem('em_theme', theme);

        // Dispatch custom event for other scripts
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
    }

    // ─── MEDIAPIPE VELOCITY CALCULATION ──────────────────────────────────────

    function calcVelocity(currentLMs, prevLMs, dt) {
        /**
         * Tính vận tốc (velocity) của từng landmark.
         * dt = time delta in seconds
         */
        return currentLMs.map((lm, i) => {
            const prev = prevLMs[i] || { x: lm.x, y: lm.y, z: lm.z };
            const vx = (lm.x - prev.x) / Math.max(dt, 0.001);
            const vy = (lm.y - prev.y) / Math.max(dt, 0.001);
            const vz = ((lm.z || 0) - (prev.z || 0)) / Math.max(dt, 0.001);
            return {
                x:  lm.x,
                y:  lm.y,
                z:  lm.z || 0,
                vx: Math.max(-CONFIG.MAX_VELOCITY, Math.min(CONFIG.MAX_VELOCITY, vx)),
                vy: Math.max(-CONFIG.MAX_VELOCITY, Math.min(CONFIG.MAX_VELOCITY, vy)),
                vz: Math.max(-CONFIG.MAX_VELOCITY, Math.min(CONFIG.MAX_VELOCITY, vz)),
            };
        });
    }

    // ─── MEDIAPIPE INTEGRATION ────────────────────────────────────────────────

    async function initMediaPipe() {
        // Kiểm tra xem MediaPipe đã load chưa (từ CDN)
        if (typeof FaceMesh === 'undefined') {
            console.log('[EmSig] MediaPipe FaceMesh not found — using time-based seed');
            startTimerBasedUpdates();
            return;
        }

        try {
            faceMesh = new FaceMesh({
                locateFile: file =>
                    `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
            });

            faceMesh.setOptions({
                maxNumFaces: 1,
                refineLandmarks: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence:  0.5,
            });

            faceMesh.onResults(onFaceMeshResults);
            faceMeshReady = true;
            console.log('[EmSig] MediaPipe FaceMesh initialized');
        } catch (e) {
            console.warn('[EmSig] MediaPipe init failed:', e);
            startTimerBasedUpdates();
        }
    }

    function onFaceMeshResults(results) {
        if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) return;

        const rawLMs    = results.multiFaceLandmarks[0];
        const now       = Date.now();
        const dt        = (now - lastTimestamp) / 1000;
        lastTimestamp   = now;

        // Lấy subset landmarks quan trọng (key points): mắt, mũi, miệng, tai
        const KEY_INDICES = [
            33, 133, 362, 263,  // mắt trái, phải
            1, 4, 5,             // mũi
            61, 291, 17, 0,      // miệng
            234, 454,            // gò má
            10, 152,             // trán, cằm
            70, 300,             // lông mày
        ];

        const keyLMs = KEY_INDICES
            .filter(i => i < rawLMs.length)
            .map(i => rawLMs[i]);

        let landmarksWithVel;
        if (lastLandmarks && lastLandmarks.length === keyLMs.length) {
            landmarksWithVel = calcVelocity(keyLMs, lastLandmarks, dt);
        } else {
            landmarksWithVel = keyLMs.map(lm => ({ ...lm, vx: 0, vy: 0, vz: 0 }));
        }

        lastLandmarks = keyLMs;

        // Throttle: không gửi quá thường xuyên
        if (now - window._emLastSent > CONFIG.UPDATE_INTERVAL_MS) {
            window._emLastSent = now;
            sendSignatureRequest(landmarksWithVel);
        }
    }

    // ─── CAMERA INIT ─────────────────────────────────────────────────────────

    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width:  { ideal: CONFIG.CAMERA_WIDTH },
                    height: { ideal: CONFIG.CAMERA_HEIGHT },
                    facingMode: 'user',
                },
                audio: false,
            });
            videoEl.srcObject = stream;

            if (faceMeshReady && faceMesh) {
                // Gửi frames vào MediaPipe
                const Camera = window.Camera;
                if (Camera) {
                    new Camera(videoEl, {
                        onFrame: async () => {
                            if (faceMesh) await faceMesh.send({ image: videoEl });
                        },
                        width:  CONFIG.CAMERA_WIDTH,
                        height: CONFIG.CAMERA_HEIGHT,
                    });
                }
            }

            console.log('[EmSig] Camera started');
        } catch (err) {
            console.log('[EmSig] Camera access denied or unavailable:', err.message);
            // Fallback graceful: dùng timestamp-based seed
            startTimerBasedUpdates();
        }
    }

    // ─── FALLBACK: Time-based updates (no camera) ─────────────────────────────

    function startTimerBasedUpdates() {
        // Khi không có camera, dùng timestamp + random để tạo seed
        window._emLastSent = 0;

        function doUpdate() {
            const fakeLandmarks = generateTimestampLandmarks();
            sendSignatureRequest(fakeLandmarks);
        }

        doUpdate(); // Lần đầu ngay lập tức
        updateTimer = setInterval(doUpdate, CONFIG.UPDATE_INTERVAL_MS);
    }

    function generateTimestampLandmarks() {
        // Sinh "landmarks" giả dựa trên timestamp + small noise
        const t = Date.now();
        const noise = () => (Math.random() - 0.5) * 0.002;
        return Array.from({ length: 16 }, (_, i) => ({
            x:  0.3 + (i * 0.02) % 0.5 + noise(),
            y:  0.2 + (i * 0.03) % 0.6 + noise(),
            z:  (i * 0.001) + noise(),
            vx: noise() * 0.5,
            vy: noise() * 0.5,
            vz: 0,
        }));
    }

    // ─── API CALL ─────────────────────────────────────────────────────────────

    async function sendSignatureRequest(landmarks) {
        try {
            const resp = await fetch('/api/emotional-signature', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ landmarks }),
            });

            if (!resp.ok) return;
            const data = await resp.json();

            // Cập nhật globals
            currentTheme  = data.ui_theme  || 'warm_glow';
            currentMood   = data.mood      || 'calm';
            currentSig    = data.signature || '';

            localStorage.setItem('em_theme', currentTheme);
            localStorage.setItem('em_mood',  currentMood);
            localStorage.setItem('em_sig',   currentSig);

            // Áp dụng theme
            applyTheme(currentTheme);
            updateBadge(data);

            // Dispatch event cho chatbot widget
            window.dispatchEvent(new CustomEvent('emotionupdate', { detail: data }));

        } catch (e) {
            // Fail silently
        }
    }

    // ─── RESTORE SAVED THEME ─────────────────────────────────────────────────

    function restoreSavedTheme() {
        const saved = localStorage.getItem('em_theme');
        if (saved) {
            document.documentElement.setAttribute('data-theme', saved);
            currentTheme = saved;
        }
    }

    // ─── PUBLIC API ──────────────────────────────────────────────────────────

    window.EmotionalSignature = {
        getCurrentMood:      () => currentMood,
        getCurrentTheme:     () => currentTheme,
        getCurrentSignature: () => currentSig,
        forceTheme:          (t) => applyTheme(t),
        getMoodData: () => ({
            mood:      currentMood,
            theme:     currentTheme,
            signature: currentSig,
        }),
    };

    // ─── INIT ─────────────────────────────────────────────────────────────────

    function init() {
        restoreSavedTheme();
        createBadge();
        createOverlay();
        videoEl = createHiddenVideo();

        window._emLastSent = 0;

        // Load MediaPipe từ CDN (async, không block page)
        const mpScript = document.createElement('script');
        mpScript.src   = 'https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js';
        mpScript.crossOrigin = 'anonymous';
        mpScript.onload = async () => {
            await initMediaPipe();
            await startCamera();
        };
        mpScript.onerror = () => {
            console.log('[EmSig] MediaPipe CDN unavailable, using fallback');
            startTimerBasedUpdates();
        };
        document.head.appendChild(mpScript);

        // Camera helper
        const camScript = document.createElement('script');
        camScript.src   = 'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js';
        camScript.crossOrigin = 'anonymous';
        document.head.appendChild(camScript);
    }

    // Run after DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

/**
 * FashionMentor AI – Floating Chatbot Widget (Luxury Dark Theme)
 * Supports: normal chat/search + in-chat Stylist AI (hair/glasses swap)
 */
(function () {
    'use strict';

    /* ── 1. CSS ── */
    const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Jost:wght@200;300;400;500&display=swap');

:root {
    --fm-dark: #1a120a;
    --fm-dark2: #221509;
    --fm-border: rgba(212,170,95,0.12);
    --fm-border2: rgba(212,170,95,0.2);
    --fm-text: #e8ddd0;
    --fm-text-dim: #b8a99a;
    --fm-text-muted: #7a6558;
    --fm-caramel: #c4843b;
    --fm-gold: #d4aa5f;
}

#fm-fab {
    position: fixed; bottom: 28px; right: 28px; z-index: 9999;
    width: 56px; height: 56px; border-radius: 2px;
    background: rgba(196,132,59,0.15);
    border: 1px solid var(--fm-border2); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    transition: all 0.25s ease;
    font-size: 22px; color: var(--fm-caramel); user-select: none;
    font-family: 'Cormorant Garamond', serif;
}
#fm-fab:hover { 
    transform: translateY(-3px); 
    background: var(--fm-caramel); 
    color: #fff;
    border-color: var(--fm-caramel);
    box-shadow: 0 12px 40px rgba(196,132,59,0.3); 
}
#fm-fab .fm-badge {
    position: absolute; top: -6px; right: -6px;
    background: var(--fm-caramel); color: #fff; font-size: 10px; font-weight: 500;
    width: 20px; height: 20px; border-radius: 2px;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid var(--fm-border2); opacity: 0; transition: opacity 0.2s;
    font-family: 'Jost', sans-serif;
}
#fm-fab .fm-badge.show { opacity: 1; }

#fm-panel {
    position: fixed; bottom: 96px; right: 28px; z-index: 9998;
    width: 390px; height: 560px; border-radius: 2px;
    background: var(--fm-dark);
    border: 1px solid var(--fm-border2);
    box-shadow: 0 20px 60px rgba(0,0,0,0.8);
    display: flex; flex-direction: column;
    font-family: 'Jost', sans-serif; font-weight: 300; overflow: hidden;
    transform: scale(0.9) translateY(20px);
    transform-origin: bottom right; opacity: 0; pointer-events: none;
    transition: transform 0.28s cubic-bezier(0.34,1.56,0.64,1), opacity 0.22s ease;
}
#fm-panel::before {
    content: ''; position: absolute; inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none; z-index: 0;
}
#fm-panel.open { transform: scale(1) translateY(0); opacity: 1; pointer-events: all; }
#fm-panel > * { position: relative; z-index: 1; }

/* Header */
.fm-header {
    padding: 16px 20px 12px; border-bottom: 1px solid var(--fm-border);
    display: flex; align-items: center; justify-content: space-between;
    flex-shrink: 0; background: var(--fm-dark2);
}
.fm-header-left { display: flex; align-items: center; gap: 12px; }
.fm-avatar-hd {
    width: 36px; height: 36px; border-radius: 2px;
    background: rgba(196,132,59,0.1); border: 1px solid var(--fm-border2);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0; color: var(--fm-caramel);
}
.fm-header-info .fm-title { 
    font-family: 'Cormorant Garamond', serif; 
    font-size: 16px; font-weight: 400; color: var(--fm-text); letter-spacing: 0.03em; 
}
.fm-header-info .fm-sub { font-size: 11px; color: var(--fm-text-muted); margin-top: 2px; letter-spacing: 0.05em; }
.fm-header-actions { display: flex; align-items: center; gap: 8px; }

/* Mode toggle */
.fm-mode-toggle {
    display: flex; background: rgba(255,255,255,0.03);
    border: 1px solid var(--fm-border); border-radius: 2px;
    padding: 3px; gap: 2px;
}
.fm-mode-btn {
    padding: 5px 12px; border-radius: 2px; border: none;
    font-size: 10px; font-weight: 400; cursor: pointer;
    transition: all 0.2s ease; background: transparent; color: var(--fm-text-muted);
    font-family: 'Jost', sans-serif; white-space: nowrap;
    letter-spacing: 0.12em; text-transform: uppercase;
}
.fm-mode-btn.active {
    background: var(--fm-caramel);
    color: #fff;
}
.fm-mode-btn:hover:not(.active) { background: rgba(212,170,95,0.08); color: var(--fm-gold); }

.fm-close-btn {
    width: 28px; height: 28px; border-radius: 2px; border: 1px solid transparent;
    background: transparent; color: var(--fm-text-muted); font-size: 14px;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: all 0.2s; font-family: 'Jost', sans-serif;
}
.fm-close-btn:hover { background: rgba(196,132,59,0.1); border-color: var(--fm-border2); color: var(--fm-caramel); }

/* Messages */
.fm-messages {
    flex: 1; overflow-y: auto;
    padding: 20px 20px 10px;
    display: flex; flex-direction: column; gap: 16px;
}
.fm-messages::-webkit-scrollbar { width: 3px; }
.fm-messages::-webkit-scrollbar-thumb { background: var(--fm-border2); border-radius: 3px; }

/* Welcome */
.fm-welcome {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center; gap: 12px; padding: 20px;
    animation: fadeIn 0.6s ease 0.2s forwards; opacity: 0;
}
@keyframes fadeIn { to { opacity: 0.85; } }
.fm-welcome .fw-icon { 
    font-size: 24px; width: 56px; height: 56px; 
    border-radius: 2px; background: rgba(196,132,59,0.1); 
    border: 1px solid var(--fm-border2); 
    display: flex; align-items: center; justify-content: center;
}
.fm-welcome p { font-size: 13px; color: var(--fm-text-muted); line-height: 1.7; }

/* Message bubbles */
.fm-msg { display: flex; gap: 10px; animation: fmSlideUp 0.25s ease; }
.fm-msg.user { flex-direction: row-reverse; }
@keyframes fmSlideUp {
    from { opacity:0; transform:translateY(8px); }
    to   { opacity:1; transform:translateY(0); }
}
.fm-av {
    width: 28px; height: 28px; border-radius: 2px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 11px;
    font-family: 'Cormorant Garamond', serif; letter-spacing: 0.05em;
}
.fm-av.ai   { background: rgba(196,132,59,0.15); border: 1px solid var(--fm-border2); color: var(--fm-caramel); }
.fm-av.user { background: rgba(255,255,255,0.06); border: 1px solid var(--fm-border); color: var(--fm-text-dim); }

.fm-bubble {
    max-width: 80%; padding: 12px 16px;
    border-radius: 2px; font-size: 13.5px; line-height: 1.75;
}
.fm-bubble.ai {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--fm-border);
    color: var(--fm-text);
}
.fm-bubble.ai h1,.fm-bubble.ai h2,.fm-bubble.ai h3 { 
    font-family: 'Cormorant Garamond', serif; color: var(--fm-gold); 
    font-size: 16px; font-weight: 400; margin: 12px 0 6px; 
}
.fm-bubble.ai ul,.fm-bubble.ai ol { padding-left: 20px; margin: 6px 0; }
.fm-bubble.ai li { margin: 4px 0; }
.fm-bubble.ai a  { color: var(--fm-caramel); text-decoration: underline; }
.fm-bubble.ai strong { color: var(--fm-gold); font-weight: 500; }
.fm-bubble.ai em { color: var(--fm-dust); font-style: italic; }
.fm-bubble.ai code { background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 2px; font-size: 12px; font-family: monospace; color: var(--fm-caramel); }
.fm-bubble.user {
    background: rgba(196,132,59,0.12);
    border: 1px solid rgba(196,132,59,0.25);
    color: var(--fm-text);
}
.fm-badge-mode {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 9.5px; padding: 2px 8px; border-radius: 2px;
    margin-bottom: 8px; background: rgba(255,255,255,0.05); color: var(--fm-text-muted);
    letter-spacing: 0.1em; text-transform: uppercase;
}
.fm-badge-mode.search { background: rgba(196,132,59,0.1); color: var(--fm-caramel); }
.fm-badge-mode.stylist { background: rgba(212,170,95,0.1); color: var(--fm-gold); }

/* Loading dots */
.fm-dots { display:flex; gap:5px; padding:4px 0; align-items:center; }
.fm-dots span { width:7px; height:7px; border-radius: 50%; animation:fmBounce 1.3s infinite; background: var(--fm-caramel); }
.fm-dots span:nth-child(2){ opacity: 0.7; animation-delay:.2s; }
.fm-dots span:nth-child(3){ opacity: 0.5; animation-delay:.4s; }
@keyframes fmBounce {
    0%,60%,100%{transform:translateY(0);opacity:.4;}
    30%{transform:translateY(-6px);opacity:1;}
}

/* ── Stylist picker inside bubble ── */
.fm-stylist-section { margin-top: 14px; }
.fm-stylist-label {
    font-size: 10px; font-weight: 500; letter-spacing: 0.2em;
    text-transform: uppercase; color: var(--fm-text-muted); margin-bottom: 8px;
    padding-bottom: 6px; border-bottom: 1px solid var(--fm-border);
}
.fm-sample-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
    gap: 8px;
}
.fm-sample-card {
    border-radius: 2px; overflow: hidden;
    border: 1px solid var(--fm-border);
    cursor: pointer; transition: all 0.18s ease;
    background: rgba(255,255,255,0.02);
    position: relative;
}
.fm-sample-card:hover { border-color: var(--fm-caramel); }
.fm-sample-card.selected {
    border-color: var(--fm-caramel);
    box-shadow: 0 0 0 2px rgba(196,132,59,0.3);
}
.fm-sample-card img { width:100%; aspect-ratio:1/1; object-fit:cover; display:block; }
.fm-sample-card .fsc-name {
    font-size: 10px; color: var(--fm-text-dim);
    padding: 4px 6px; text-align: center; line-height: 1.3;
}
.fm-sample-card .fsc-check {
    position: absolute; top: 4px; right: 4px;
    background: var(--fm-caramel); color: #fff; border-radius: 50%;
    width: 14px; height: 14px; font-size: 9px;
    display: none; align-items: center; justify-content: center;
}
.fm-sample-card.selected .fsc-check { display: flex; }

.fm-gen-btn {
    width: 100%; margin-top: 14px;
    padding: 12px; border-radius: 2px; 
    border: 1px solid var(--fm-caramel);
    background: rgba(196,132,59,0.12);
    color: var(--fm-caramel); font-size: 11px; font-weight: 400;
    letter-spacing: 0.2em; text-transform: uppercase;
    cursor: pointer; transition: all 0.22s ease;
    font-family: 'Jost', sans-serif;
}
.fm-gen-btn:hover:not(:disabled) { background: var(--fm-caramel); color: #fff; }
.fm-gen-btn:disabled { 
    opacity: 0.3; cursor: not-allowed; 
    border-color: var(--fm-border2); color: var(--fm-text-muted); background: transparent; 
}

.fm-no-photo-warn {
    font-size: 12px; color: var(--fm-gold); font-style: italic;
    background: rgba(212,170,95,0.05); border: 1px solid var(--fm-border2); 
    border-radius: 2px; padding: 10px 14px; margin-top: 10px; line-height: 1.6;
}
.fm-no-photo-warn a { color: var(--fm-caramel) !important; font-style: normal; }

.fm-result-img {
    width: 100%; border-radius: 2px; margin-top: 12px;
    border: 1px solid var(--fm-border2);
}
.fm-result-actions {
    display: flex; gap: 8px; margin-top: 8px;
}
.fm-result-actions a {
    flex: 1; padding: 8px; border-radius: 2px; text-align: center;
    font-size: 10px; font-weight: 400; text-decoration: none; text-transform: uppercase; letter-spacing: 0.1em;
    background: rgba(255,255,255,0.03);
    color: var(--fm-text-dim); border: 1px solid var(--fm-border2);
    transition: all 0.18s ease;
}
.fm-result-actions a:hover { border-color: var(--fm-caramel); color: var(--fm-caramel); }

.fm-empty { font-size: 11px; color: var(--fm-text-muted); font-style: italic; padding: 6px 0; }

/* Input area */
.fm-input-area {
    padding: 14px 20px 16px; border-top: 1px solid var(--fm-border);
    flex-shrink: 0; background: rgba(255,255,255,0.01);
}
.fm-input-box {
    display: flex; gap: 10px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--fm-border2);
    border-radius: 2px; padding: 8px 10px 8px 16px;
    transition: border-color 0.2s;
}
.fm-input-box:focus-within {
    border-color: var(--fm-caramel);
}
.fm-input-box textarea {
    flex: 1; background: none; border: none; outline: none;
    font-family: 'Jost', sans-serif; font-weight: 300; font-size: 13.5px;
    color: var(--fm-text); resize: none; max-height: 100px; min-height: 24px; line-height: 1.55;
}
.fm-input-box textarea::placeholder { color: var(--fm-text-muted); }
.fm-send {
    width: 36px; height: 36px; border-radius: 2px; border: 1px solid var(--fm-border2);
    background: rgba(196,132,59,0.15); color: var(--fm-caramel); cursor: pointer; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.2s ease; font-size: 14px;
}
.fm-send:hover:not(:disabled) { background: var(--fm-caramel); color: #fff; border-color: var(--fm-caramel); }
.fm-send:disabled { opacity: 0.3; cursor: not-allowed; }
.fm-hint { font-size: 10px; color: var(--fm-text-muted); text-align: center; margin-top: 8px; letter-spacing: 0.1em; text-transform: uppercase; }
`;

    const styleEl = document.createElement('style');
    styleEl.textContent = CSS;
    document.head.appendChild(styleEl);

    /* ── 2. Detect page context ── */
    const path    = window.location.pathname;
    let pageName  = '';
    let topicName = 'thời trang';
    let faceShape = '';

    const m = path.match(/\/(face_shape|body_shape|personal_color)\/(.+)/);
    if (m) {
        pageName  = m[2].replace(/-/g, '_');
        topicName = pageName.replace(/_/g, ' ');
        if (m[1] === 'face_shape') {
            faceShape = m[2].toLowerCase();
        }
    }

    const VALID_SHAPES = new Set(['heart','oblong','oval','round','square']);
    const isStylistPage = VALID_SHAPES.has(faceShape);

    /* ── 3. Build DOM ── */
    const fab = document.createElement('button');
    fab.id = 'fm-fab';
    fab.title = 'Mở FashionMentor AI';
    fab.innerHTML = '💬<span class="fm-badge" id="fm-badge">1</span>';
    document.body.appendChild(fab);

    const panel = document.createElement('div');
    panel.id = 'fm-panel';
    panel.innerHTML = `
<div class="fm-header">
    <div class="fm-header-left">
        <div class="fm-avatar-hd">AI</div>
        <div class="fm-header-info">
            <div class="fm-title">Deep Style <span>AI</span></div>
            <div class="fm-sub" id="fm-sub">Đang xem: ${topicName || 'trang chính'}</div>
        </div>
    </div>
    <div class="fm-header-actions">
        <div class="fm-mode-toggle">
            <button class="fm-mode-btn active" id="fm-btn-chat" onclick="fmSetMode('chat')">💬 Chat</button>
            <button class="fm-mode-btn" id="fm-btn-search" onclick="fmSetMode('search')">🔍 Search</button>
        </div>
        <button class="fm-close-btn" id="fm-close" title="Đóng">✕</button>
    </div>
</div>
<div class="fm-messages" id="fm-messages">
    <div class="fm-welcome" id="fm-welcome">
        <div class="fw-icon">✨</div>
        <p>${isStylistPage
            ? `Tôi là trợ lý AI của Deep Style.<br>
               Bạn có thể hỏi tôi về thời trang, hoặc nói <strong style="color:var(--fm-gold)">
               "đổi tóc"</strong>, <strong style="color:var(--fm-gold)">"thử kính"</strong> để tôi gợi ý kiểu
               phù hợp với khuôn mặt <strong style="color:var(--fm-gold)">${topicName}</strong> của bạn!`
            : `Xin chào! Tôi là trợ lý AI thời trang.<br>
               ${pageName ? `Tôi sẽ tư vấn dựa trên nội dung trang <strong style="color:var(--fm-gold)">${topicName}</strong> này.` : 'Hãy hỏi tôi về thời trang!'}`
        }</p>
    </div>
</div>
<div class="fm-input-area">
    <div class="fm-input-box">
        <textarea id="fm-input" placeholder="${isStylistPage ? 'Hỏi về thời trang hoặc "đổi tóc", "thử kính"...' : 'Hỏi về thời trang...'}" rows="1"></textarea>
        <button class="fm-send" id="fm-send" title="Gửi">➤</button>
    </div>
    <div class="fm-hint" id="fm-hint">💬 Chat · Gemini 2.5 Flash</div>
</div>`;
    document.body.appendChild(panel);

    /* ── 4. State ── */
    let isOpen    = false;
    let mode      = 'chat';
    let busy      = false;
    let hasUnread = false;

    const stylistState = {};
    let _bubbleCounter = 0;

    /* ── 4b. Chat history (localStorage) ── */
    const HISTORY_KEY = 'fm_chat_' + (pageName || 'general');
    const TS_KEY      = 'fm_upload_ts';
    let   _history    = [];

    function saveHistory() {
        try { localStorage.setItem(HISTORY_KEY, JSON.stringify(_history.slice(-60))); } catch(e) {}
    }

    function restoreHistory() {
        try {
            const saved = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
            if (!saved.length) return;
            removeWelcome();
            saved.forEach(rec => {
                _addMsgDom(rec.role, rec.html, rec.badgeType);
            });
            _history = saved;
            const msgs = document.getElementById('fm-messages');
            if (msgs) msgs.scrollTop = msgs.scrollHeight;
        } catch(e) {}
    }

    async function initHistory() {
        try {
            const r    = await fetch('/api/session-info');
            const info = await r.json();
            const storedTs = localStorage.getItem(TS_KEY);
            const serverTs = String(info.upload_ts || 0);
            if (serverTs !== '0' && storedTs !== serverTs) {
                localStorage.removeItem(HISTORY_KEY);
                localStorage.setItem(TS_KEY, serverTs);
            } else {
                restoreHistory();
            }
        } catch(e) {
            restoreHistory();
        }
    }

    /* ── 5. marked.js ── */
    let markedReady = false;
    function loadMarked(cb) {
        if (markedReady) { cb(); return; }
        const s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        s.onload = () => { markedReady = true; cb(); };
        document.head.appendChild(s);
    }
    function parseMd(text) {
        if (typeof marked !== 'undefined') return marked.parse(text);
        return text.replace(/\n/g,'<br>');
    }

    /* ── 6. Open / Close ── */
    function togglePanel() {
        isOpen = !isOpen;
        panel.classList.toggle('open', isOpen);
        fab.innerHTML = isOpen
            ? '✕<span class="fm-badge" id="fm-badge"></span>'
            : '💬<span class="fm-badge" id="fm-badge"' + (hasUnread ? ' class="show"' : '') + '></span>';
        if (isOpen) {
            hasUnread = false;
            document.getElementById('fm-input').focus();
        }
    }

    // Export toggleChat globally so HTML buttons can call it
    window.toggleChat = togglePanel;

    fab.addEventListener('click', togglePanel);
    document.getElementById('fm-close').addEventListener('click', togglePanel);

    /* ── 7. Mode ── */
    window.fmSetMode = function (m2) {
        mode = m2;
        document.getElementById('fm-btn-chat').classList.toggle('active', m2 === 'chat');
        document.getElementById('fm-btn-search').classList.toggle('active', m2 === 'search');
        var trendBtn = document.getElementById('fm-btn-trend');
        if (trendBtn) trendBtn.classList.toggle('active', m2 === 'trend');
        var hintMap = {
            chat: '💬 Chat · Gemini 2.5 Flash',
            search: '🔍 Web Search · Gemini 2.5 Pro',
            trend: '📈 Trend Alert · Dữ liệu thời gian thực',
        };
        document.getElementById('fm-hint').textContent = hintMap[m2] || hintMap.chat;
        if (m2 === 'trend') {
            var inp = document.getElementById('fm-input');
            if (inp && !inp.value.trim()) {
                inp.value = 'Xu hướng thời trang hot nhất hiện nay là gì?';
                inp.style.height = 'auto';
                inp.style.height = Math.min(inp.scrollHeight, 100) + 'px';
            }
        }
    };

    /* ── 8. Helpers ── */
    function escHtml(t) {
        return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
    }

    function removeWelcome() {
        const el = document.getElementById('fm-welcome');
        if (el) el.remove();
    }

    function _addMsgDom(role, html, badgeType) {
        const msgs = document.getElementById('fm-messages');
        const div  = document.createElement('div');
        div.className = `fm-msg ${role}`;
        if (role === 'ai') {
            const bCls = badgeType === 'search' ? 'search' : badgeType === 'stylist' ? 'stylist' : '';
            const bTxt = badgeType === 'search' ? '🔍 Search' : badgeType === 'stylist' ? '✨ Stylist AI' : '💬 Chat';
            div.innerHTML = `
                <div class="fm-av ai">AI</div>
                <div class="fm-bubble ai">
                    <div class="fm-badge-mode ${bCls}">${bTxt}</div>
                    ${html}
                </div>`;
        } else {
            div.innerHTML = `
                <div class="fm-av user">You</div>
                <div class="fm-bubble user">${escHtml(html)}</div>`;
        }
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
        return div;
    }

    function addMsg(role, html, badgeType) {
        removeWelcome();
        const div = _addMsgDom(role, html, badgeType);
        if (badgeType !== 'stylist') {
            _history.push({ role, html, badgeType });
            saveHistory();
        }
        return div;
    }

    function showLoading() {
        removeWelcome();
        const msgs = document.getElementById('fm-messages');
        const div  = document.createElement('div');
        div.className = 'fm-msg ai'; div.id = 'fm-loading';
        div.innerHTML = `<div class="fm-av ai">AI</div>
            <div class="fm-bubble ai"><div class="fm-dots"><span></span><span></span><span></span></div></div>`;
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
    }
    function hideLoading() {
        const el = document.getElementById('fm-loading');
        if (el) el.remove();
    }

    /* ── 9. Stylist bubble renderer ── */
    function renderStylistBubble(data) {
        const bid    = 'fmst-' + (++_bubbleCounter);
        const shape  = data.face_shape;
        const target = data.target;
        const samples = data.samples;
        const hasPhoto = data.has_photo;

        stylistState[bid] = { faceShape: shape, selectedHair: '', selectedGlasses: '' };

        let html = `<div style="margin-bottom:12px;">
            Tôi sẽ giúp bạn thử <strong style="color:var(--fm-gold)">${
                target === 'hair' ? 'kiểu tóc' : target === 'glasses' ? 'gọng kính' : 'kiểu tóc và kính'
            }</strong> phù hợp với khuôn mặt <strong style="color:var(--fm-gold)">${shape}</strong> của bạn!
        </div>`;

        if (!hasPhoto) {
            html += `<div class="fm-no-photo-warn">
                ⚠️ Chưa có ảnh khuôn mặt trong phiên. Vui lòng quay lại
                <a href="/face_shape">trang Phân tích khuôn mặt</a>
                và tải ảnh lên trước.
            </div>`;
        } else {
            if (target === 'hair' || target === 'both') {
                html += buildSampleSection(bid, 'hair', 'Chọn kiểu tóc', samples.hair, shape);
            }
            if (target === 'glasses' || target === 'both') {
                html += buildSampleSection(bid, 'glasses', 'Chọn gọng kính', samples.glasses, shape);
            }

            html += `<button class="fm-gen-btn" id="${bid}-genbtn" onclick="fmGenerateStylist('${bid}','${shape}')" disabled>
                ✨ Áp dụng lên ảnh của tôi
            </button>`;
        }

        html += `<div id="${bid}-result" style="display:none"></div>`;

        loadMarked(() => {
            addMsg('ai', html, 'stylist');
            const msgs = document.getElementById('fm-messages');
            setTimeout(() => { msgs.scrollTop = msgs.scrollHeight; }, 80);
        });
    }

    function buildSampleSection(bid, type, label, items, shape) {
        if (!items || !items.length) {
            return `<div class="fm-stylist-section"><div class="fm-stylist-label">${label}</div>
                <div class="fm-empty">Chưa có mẫu nào</div></div>`;
        }
        const cards = items.map(it => `
            <div class="fm-sample-card" id="${bid}-${type}-${it.file}"
                 onclick="fmSelectSample('${bid}','${type}','${it.file}')">
                <img src="/face_shape/images/${shape}/${it.file}" alt="${it.name}" loading="lazy">
                <div class="fsc-name">${it.name}</div>
                <div class="fsc-check">✓</div>
            </div>`).join('');
        return `<div class="fm-stylist-section">
            <div class="fm-stylist-label">${label}</div>
            <div class="fm-sample-grid">${cards}</div>
        </div>`;
    }

    /* ── 10. Stylist interaction ── */
    window.fmSelectSample = function (bid, type, file) {
        if (!stylistState[bid]) return;
        document.querySelectorAll(`[id^="${bid}-${type}-"]`).forEach(el => {
            el.classList.remove('selected');
        });
        const card = document.getElementById(`${bid}-${type}-${file}`);
        if (card) card.classList.add('selected');

        if (type === 'hair')    stylistState[bid].selectedHair    = file;
        if (type === 'glasses') stylistState[bid].selectedGlasses = file;

        updateGenBtn(bid);
    };

    function updateGenBtn(bid) {
        const st  = stylistState[bid];
        const btn = document.getElementById(`${bid}-genbtn`);
        if (!btn || !st) return;
        btn.disabled = !(st.selectedHair || st.selectedGlasses);
    }

    window.fmGenerateStylist = async function (bid, shape) {
        const st = stylistState[bid];
        if (!st) return;

        const btn     = document.getElementById(`${bid}-genbtn`);
        const resultEl = document.getElementById(`${bid}-result`);
        if (btn) btn.disabled = true;

        if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.innerHTML = `<div class="fm-dots" style="margin-top:12px">
                <span></span><span></span><span></span></div>
                <div style="font-size:11px;color:var(--fm-text-muted);margin-top:6px;letter-spacing:0.05em;">Đang tạo ảnh với AI…</div>`;
        }

        try {
            const res  = await fetch('/api/stylist/generate-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    face_shape:   shape,
                    hair_file:    st.selectedHair,
                    glasses_file: st.selectedGlasses,
                })
            });
            const data = await res.json();

            if (data.error) throw new Error(data.error);

            const url = data.result_url + '?t=' + Date.now();
            if (resultEl) {
                resultEl.innerHTML = `
                    <img class="fm-result-img" src="${url}" alt="Kết quả">
                    <div class="fm-result-actions">
                        <a href="${url}" target="_blank">🔍 Xem lớn</a>
                        <a href="${url}" download>⬇️ Tải xuống</a>
                    </div>`;
            }

            if (!isOpen) {
                hasUnread = true;
                const badge = document.getElementById('fm-badge');
                if (badge) badge.classList.add('show');
            }

            const msgs = document.getElementById('fm-messages');
            setTimeout(() => { msgs.scrollTop = msgs.scrollHeight; }, 100);

        } catch (e) {
            if (resultEl) {
                resultEl.innerHTML = `<div class="fm-no-photo-warn">❌ ${e.message}</div>`;
            }
            if (btn) btn.disabled = false;
        }
    };

    /* ── 11. Send message ── */
    async function sendMsg() {
        if (busy) return;
        const input = document.getElementById('fm-input');
        const text  = input.value.trim();
        if (!text) return;

        input.value = '';
        input.style.height = 'auto';

        addMsg('user', text);
        showLoading();
        busy = true;
        document.getElementById('fm-send').disabled = true;

        try {
            const emData = window.EmotionalSignature ? window.EmotionalSignature.getMoodData() : {};
            const gender = (window.GenderSwitch ? window.GenderSwitch.getGender() : null)
                           || localStorage.getItem('fm_gender') || 'female';
            const apiMode = (mode === 'trend') ? 'search' : mode;

            const res  = await fetch('/api/stylist/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt:     text,
                    face_shape: faceShape,
                    mode:       apiMode,
                    page:       pageName,
                    gender:     gender,
                    signature:  emData.signature || '',
                    mood:       emData.mood || 'calm',
                })
            });
            const data = await res.json();
            hideLoading();

            loadMarked(() => {
                if (data.error) {
                    addMsg('ai', `❌ ${escHtml(data.error)}`, mode);
                } else if (data.action === 'stylist') {
                    renderStylistBubble(data);
                } else {
                    const badgeType = data.trend_injected ? 'search' : mode;
                    let resultHtml = parseMd(data.result || '');
                    if (data.trend_injected) {
                        resultHtml = `<div class="fm-badge-mode search">📈 Trend Alert — Dữ liệu mới nhất</div>` + resultHtml;
                    }
                    addMsg('ai', resultHtml, badgeType);
                }

                if (!isOpen) {
                    hasUnread = true;
                    const badge = document.getElementById('fm-badge');
                    if (badge) badge.classList.add('show');
                }
            });

        } catch (err) {
            hideLoading();
            loadMarked(() => addMsg('ai', `❌ Lỗi kết nối: ${err.message}`, mode));
        } finally {
            busy = false;
            document.getElementById('fm-send').disabled = false;
            document.getElementById('fm-input').focus();
        }
    }

    document.getElementById('fm-send').addEventListener('click', sendMsg);
    document.getElementById('fm-input').addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
    });
    document.getElementById('fm-input').addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });

    /* ── 12. Load marked eagerly + khởi tạo lịch sử chat ── */
    loadMarked(function () {
        initHistory();
    });

})();
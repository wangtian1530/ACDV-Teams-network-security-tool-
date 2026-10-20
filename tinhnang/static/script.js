// ============== TOAST + LOG SYSTEM ==============
let logHistory = [];
const LOG_LIMIT = 500;

function escapeHtmlText(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}

function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const recent = Array.from(container.children).slice(-3);
    if (recent.some(t => t.dataset.msg === message)) return;

    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌', system: '⚙️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.dataset.msg = message;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
        <span class="toast-msg">${escapeHtmlText(message)}</span>
        <button class="toast-close" type="button">×</button>
    `;
    toast.querySelector('.toast-close').onclick = () => removeToast(toast);
    container.appendChild(toast);

    if (duration > 0) setTimeout(() => removeToast(toast), duration);
    while (container.children.length > 5) container.removeChild(container.firstChild);
}

function removeToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
}

function addLogToHistory(line, type = '') {
    logHistory.push({ line, type, time: new Date().toLocaleTimeString() });
    if (logHistory.length > LOG_LIMIT) logHistory.shift();
}

function renderLogModal() {
    const body = document.getElementById('logModalBody');
    if (!body) return;
    if (logHistory.length === 0) {
        body.innerHTML = '<div style="text-align:center;color:#888;padding:20px;">Chưa có log nào</div>';
        return;
    }
    body.innerHTML = logHistory.map(l => {
        const cls = l.type === 'error-log' ? 'log-error'
                  : l.type === 'system-log' ? 'log-system'
                  : l.type === 'cmd-log' ? 'log-cmd' : '';
        return `<div class="log-line ${cls}">[${l.time}] ${escapeHtmlText(l.line)}</div>`;
    }).join('');
    body.scrollTop = body.scrollHeight;
}

function openLogModal() {
    renderLogModal();
    const modal = document.getElementById('logModal');
    if (modal) modal.style.display = 'flex';
}
function closeLogModal() {
    const modal = document.getElementById('logModal');
    if (modal) modal.style.display = 'none';
}

function updateTicker(message, type = '') {
    const text = document.getElementById('tickerText');
    const ticker = document.getElementById('statusTicker');
    if (!text || !ticker) return;
    text.textContent = message;
    ticker.className = 'status-ticker';
    if (type === 'error-log' || /❌|\[ERROR\]|\[✗\]/.test(message)) ticker.classList.add('ticker-error');
    else if (/⚠️|\[WARNING\]|\[!\]/.test(message)) ticker.classList.add('ticker-warning');
    else if (/✅|\[RESULT\]|✓|Hoàn tất/.test(message)) ticker.classList.add('ticker-success');
    else if (type === 'system-log') ticker.classList.add('ticker-system');
}

// ============== PASSWORD HELPERS ==============
function generateFakePassword(length) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%';
    let result = '';
    for (let i = 0; i < length; i++) result += chars.charAt(Math.floor(Math.random() * chars.length));
    return result;
}

function analyzePasswordStrength(password) {
    let score = 0; let feedback = [];
    if (!password) return { score: 0, strength: 'Không có', feedback: ['Chưa có mật khẩu'] };
    if (password.length >= 8) score += 1;
    if (password.length >= 12) score += 1;
    if (password.length >= 16) score += 1;
    if (/[a-z]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^a-zA-Z0-9]/.test(password)) score += 1;
    if (/(.)\1{2,}/.test(password)) feedback.push('⚠️ Có ký tự lặp lại nhiều lần');
    if (/^[a-zA-Z]+$/.test(password)) feedback.push('⚠️ Chỉ có chữ cái');
    if (/^[0-9]+$/.test(password)) feedback.push('⚠️ Chỉ có số');
    if (password.toLowerCase() === password) feedback.push('⚠️ Không có chữ hoa');
    if (password.toUpperCase() === password) feedback.push('⚠️ Không có chữ thường');
    if (password.length < 8) feedback.push('⚠️ Quá ngắn');
    let strength = 'Yếu';
    if (score >= 6) strength = 'Rất mạnh';
    else if (score >= 5) strength = 'Mạnh';
    else if (score >= 3) strength = 'Trung bình';
    return { score, strength, feedback };
}

function suggestNewPassword(oldPassword, ssid) {
    if (!oldPassword || oldPassword.length < 4) return generateStrongPassword(ssid);
    let suggestions = [];
    const variations = [
        oldPassword + '!@#', oldPassword + '2024',
        oldPassword.charAt(0).toUpperCase() + oldPassword.slice(1) + '!',
        oldPassword.replace(/a/g, '@').replace(/e/g, '3').replace(/i/g, '1').replace(/o/g, '0').replace(/s/g, '$'),
        oldPassword.split('').reverse().join('') + '?!',
        ssid.replace(/\s/g, '') + '@' + oldPassword,
        oldPassword + '@' + ssid.replace(/\s/g, '').substring(0, 6),
        oldPassword.toUpperCase() + '123!',
        oldPassword.toLowerCase() + 'Abc123!'
    ];
    for (let pwd of variations) {
        const analysis = analyzePasswordStrength(pwd);
        if (analysis.strength === 'Mạnh' || analysis.strength === 'Rất mạnh')
            suggestions.push({ password: pwd, strength: analysis.strength, score: analysis.score });
    }
    if (suggestions.length === 0) suggestions.push({ password: generateStrongPassword(ssid), strength: 'Rất mạnh', score: 7 });
    suggestions.sort((a, b) => b.score - a.score);
    return suggestions.slice(0, 3);
}

function generateStrongPassword(ssid) {
    const upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    const lower = 'abcdefghijkmnopqrstuvwxyz';
    const numbers = '23456789';
    const special = '!@#$%&*?';
    let password = '';
    let base = ssid ? ssid.replace(/\s/g, '').substring(0, 6) : 'WiFi';
    if (base.length < 3) base = 'Secure';
    password += base.charAt(0).toUpperCase();
    password += base.slice(1).toLowerCase();
    password += numbers.charAt(Math.floor(Math.random() * numbers.length));
    password += special.charAt(Math.floor(Math.random() * special.length));
    password += upper.charAt(Math.floor(Math.random() * upper.length));
    password += lower.charAt(Math.floor(Math.random() * lower.length));
    password += numbers.charAt(Math.floor(Math.random() * numbers.length));
    return password.split('').sort(() => Math.random() - 0.5).join('');
}

function analyzeVulnerability(attackType, networkInfo, password) {
    const vulnerabilities = []; const recommendations = [];
    const passwordStrength = analyzePasswordStrength(password);

    if (attackType === 'wps') {
        vulnerabilities.push({ name: '🔓 Lỗ hổng WPS', description: 'WPS có lỗ hổng bảo mật nghiêm trọng', details: 'Có thể tấn công bằng Pixie Dust / brute-force PIN', severity: 'Cao' });
        recommendations.push({ title: '🚫 TẮT WPS NGAY', description: 'Vào 192.168.1.1, tìm Wireless Settings và tắt WPS' });
        recommendations.push({ title: '📌 Cập nhật firmware', description: 'Cập nhật router để vá lỗi WPS' });
        recommendations.push({ title: '🔐 Dùng WPA2/WPA3', description: 'Chuyển sang WPA2/WPA3 với mật khẩu mạnh' });
    }

    if (attackType === 'auto_connect' || attackType === 'password') {
        if (passwordStrength.strength === 'Yếu') {
            vulnerabilities.push({ name: '🔓 Mật khẩu yếu', description: `Độ mạnh: ${passwordStrength.strength}`, details: `Điểm: ${passwordStrength.score}/7. ${passwordStrength.feedback.join(' ')}`, severity: passwordStrength.score <= 2 ? 'Rất cao' : 'Trung bình' });
        }
        vulnerabilities.push({ name: '⚠️ Dictionary Attack', description: 'Mật khẩu yếu dễ bị bẻ khóa', details: 'Hacker dùng wordlist để thử', severity: passwordStrength.strength === 'Yếu' ? 'Cao' : 'Thấp' });
        if (password.length < 8) vulnerabilities.push({ name: '⚠️ Mật khẩu ngắn', description: `Chỉ ${password.length} ký tự`, details: 'Brute-force trong vài phút', severity: 'Rất cao' });
        recommendations.push({ title: '🔄 ĐỔI MẬT KHẨU NGAY', description: 'Dùng ít nhất 12 ký tự: hoa + thường + số + ký tự đặc biệt' });
        recommendations.push({ title: '📋 Nguyên tắc', description: 'Dùng câu: "NhaToiO@Hanoi123"' });
        recommendations.push({ title: '🔒 Dùng password manager', description: 'Bitwarden / 1Password' });
    }

    if (attackType === 'pixie_dust') {
        vulnerabilities.push({ name: '💀 Lỗ hổng Pixie Dust', description: 'Cho phép tính PIN chỉ trong vài giây', details: 'Lỗi PRNG của Ralink, MediaTek, Realtek', severity: 'Nghiêm trọng' });
        recommendations.push({ title: '🚨 TẮT WPS KHẨN CẤP', description: 'Router bị ảnh hưởng Pixie Dust' });
        recommendations.push({ title: '🔄 Nâng cấp firmware/router', description: 'Chọn router hỗ trợ WPA3' });
        recommendations.push({ title: '🔐 Guest Network', description: 'Cách ly mạng chính' });
    }

    return { vulnerabilities, recommendations, passwordStrength };
}

// ============== PROGRESS BAR ==============
let _progressTimer = null;

function showProgress(pct, label) {
    const wrap = document.getElementById('moduleProgressWrap');
    const bar = document.getElementById('moduleProgressBar');
    const lab = document.getElementById('moduleProgressLabel');
    if (!wrap || !bar || !lab) return;
    if (pct === null || pct === undefined || pct < 0) {
        wrap.style.display = 'none';
        bar.style.width = '0%';
        lab.textContent = '0%';
        if (_progressTimer) { clearInterval(_progressTimer); _progressTimer = null; }
        return;
    }
    wrap.style.display = 'block';
    pct = Math.max(0, Math.min(100, pct));
    bar.style.width = pct + '%';
    lab.textContent = Math.round(pct) + '%' + (label ? ' — ' + label : '');
}

function startProgress(label) {
    let pct = 0;
    showProgress(0, label || 'Đang khởi tạo...');
    if (_progressTimer) clearInterval(_progressTimer);
    _progressTimer = setInterval(() => {
        if (pct < 90) {
            pct += Math.random() * 3 + 0.6;
            if (pct > 90) pct = 90;
            showProgress(pct, label);
        }
    }, 700);
}

function stopProgress(finalPct) {
    if (_progressTimer) { clearInterval(_progressTimer); _progressTimer = null; }
    if (finalPct !== undefined) {
        showProgress(100, 'Hoàn tất');
        setTimeout(() => showProgress(null), 1500);
    } else {
        showProgress(null);
    }
}

// ============== MODULE PANEL RENDERER ==============
function renderModulePanel(panel) {
    if (!panel) return '';
    let panelHtml = panel.html || '<div style="text-align:center;padding:20px;color:#888;">Không có nội dung</div>';
    let html = '<div class="module-panel">';
    if (panel.title) html += '<h4>' + panel.title + '</h4>';
    html += panelHtml;
    if (panel.actions && panel.actions.length) {
        html += '<div class="module-actions">';
        panel.actions.forEach((a, idx) => {
            const id = 'modact-' + Date.now() + '-' + idx;
            const paramsEnc = encodeURIComponent(JSON.stringify(a.params || {}));
            const promptEnc = encodeURIComponent(JSON.stringify(a.prompt || null));
            html += '<button class="btn btn-' + (a.color || 'secondary') + ' module-action-btn" ' +
                    'data-id="' + id + '" data-command="' + (a.command || '') + '" ' +
                    'data-params="' + paramsEnc + '" data-prompt="' + promptEnc + '">' +
                    (a.icon || '🔧') + ' ' + (a.label || 'Run') + '</button>';
        });
        html += '</div>';
    }
    html += '</div>';
    return html;
}

function bindModuleActionButtons(container) {
    if (!container) return;
    container.querySelectorAll('.module-action-btn').forEach(btn => {
        btn.onclick = () => {
            if (!wsClient || wsClient.isProcessing || !wsClient.isReady) return;
            const command = btn.dataset.command;
            let params = {};
            try { params = JSON.parse(decodeURIComponent(btn.dataset.params || '%7B%7D')); } catch (e) {}
            let promptCfg = null;
            try {
                const raw = decodeURIComponent(btn.dataset.prompt || 'null');
                promptCfg = raw === 'null' ? null : JSON.parse(raw);
            } catch (e) { promptCfg = null; }
            if (promptCfg && promptCfg.field) {
                askModalInput(promptCfg.message || 'Nhập giá trị:', promptCfg.default || '', promptCfg.hint || '').then(val => {
                    if (val === null) return;
                    const trimmed = val.trim();
                    if (!trimmed) return;
                    params[promptCfg.field] = trimmed;
                    wsClient.send(command, params);
                });
            } else {
                wsClient.send(command, params);
            }
        };
    });
}

// ============== MODAL INPUT ==============
function askModalInput(message, defaultValue, hint) {
    return new Promise((resolve) => {
        const modal = document.getElementById('moduleInputModal');
        const titleEl = document.getElementById('modalTitle');
        const labelEl = document.getElementById('modalFieldLabel');
        const inputEl = document.getElementById('modalInputField');
        const hintEl = document.getElementById('modalHint');
        const okBtn = document.getElementById('modalOkBtn');
        const cancelBtn = document.getElementById('modalCancelBtn');
        const closeBtn = document.getElementById('modalCloseBtn');
        if (!modal || !inputEl) { resolve(null); return; }

        titleEl.textContent = '📥 Nhập thông tin';
        labelEl.textContent = message || 'Giá trị:';
        inputEl.value = defaultValue || '';
        hintEl.textContent = hint || '';
        modal.style.display = 'flex';
        setTimeout(() => inputEl.focus(), 120);

        const cleanup = () => {
            modal.style.display = 'none';
            okBtn.onclick = null;
            cancelBtn.onclick = null;
            closeBtn.onclick = null;
            inputEl.onkeydown = null;
        };
        const done = (val) => { cleanup(); resolve(val); };
        okBtn.onclick = () => done(inputEl.value);
        cancelBtn.onclick = () => done(null);
        closeBtn.onclick = () => done(null);
        inputEl.onkeydown = (e) => {
            if (e.key === 'Enter') { e.preventDefault(); done(inputEl.value); }
            if (e.key === 'Escape') { e.preventDefault(); done(null); }
        };
    });
}

// ============== MAIN RESULT SECTION ==============
function clearMainResult() {
    const section = document.getElementById('mainResultSection');
    const contentEl = document.getElementById('resultContent');
    if (contentEl) contentEl.innerHTML = '';
    if (section) section.style.display = 'none';
    showProgress(null);
    // ⭐ v2.1: user đóng panel → không auto-refresh khi reconnect
    if (window.wsClient) {
        window.wsClient._lastPanelCommand = null;
        window.wsClient._lastPanelParams = null;
    }
}

// ⭐ v2: re-execute <script> tags injected via innerHTML
function _execScriptsIn(container) {
    if (!container) return;
    container.querySelectorAll('script').forEach(oldScript => {
        try {
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });
            newScript.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(newScript, oldScript);
        } catch (e) {
            console.warn('[script-exec] error:', e);
        }
    });
}

function setMainResult(titleHtml, contentHtml, opts) {
    const section = document.getElementById('mainResultSection');
    const titleEl = document.getElementById('resultTitle');
    const contentEl = document.getElementById('resultContent');
    if (!section || !titleEl || !contentEl) return;

    contentEl.innerHTML = '';
    titleEl.innerHTML = titleHtml || '📊 KẾT QUẢ MODULE';
    contentEl.innerHTML = (contentHtml !== undefined && contentHtml !== null) ? contentHtml : '';

    // ⭐ v2: chạy lại <script> inline (bị innerHTML block)
    _execScriptsIn(contentEl);

    showProgress(null);
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    bindModuleActionButtons(contentEl);
}

function showVulnerabilityReport(attackType, networkInfo, crackedPassword) {
    const analysis = analyzeVulnerability(attackType, networkInfo, crackedPassword);
    const suggestions = suggestNewPassword(crackedPassword, networkInfo.ssid);
    let html = `
        <div class="vuln-summary">
            <div class="vuln-badge ${attackType === 'wps' ? 'badge-wps' : attackType === 'pixie_dust' ? 'badge-critical' : 'badge-password'}">
                ${attackType === 'wps' ? '⚡ TẤN CÔNG WPS' : attackType === 'pixie_dust' ? '💀 PIXIE DUST' : '🔑 BẺ KHÓA MẬT KHẨU'}
            </div>
            <div class="vuln-network"><strong>📡 Mạng:</strong> ${networkInfo.ssid} (${networkInfo.bssid})</div>
            <div class="vuln-password">
                <strong>🔐 Mật khẩu bị lộ:</strong> <code>${crackedPassword}</code>
                <span class="strength-badge strength-${analysis.passwordStrength.strength.toLowerCase().replace(' ', '-')}">
                    ${analysis.passwordStrength.strength}
                </span>
            </div>
        </div>`;
    if (analysis.vulnerabilities.length > 0) {
        html += `<div class="vuln-list"><h3>🚨 LỖ HỔNG PHÁT HIỆN</h3>`;
        for (let vuln of analysis.vulnerabilities) {
            html += `<div class="vuln-item severity-${vuln.severity.toLowerCase().replace(' ', '-')}">
                <div class="vuln-item-title">${vuln.name}</div>
                <div class="vuln-item-desc">${vuln.description}</div>
                <div class="vuln-item-details">${vuln.details}</div>
                <div class="vuln-severity">Mức độ: ${vuln.severity}</div>
            </div>`;
        }
        html += `</div>`;
    }
    if (analysis.recommendations.length > 0) {
        html += `<div class="recommendations"><h3>🛠️ CÁCH PHÒNG CHỐNG</h3>`;
        for (let rec of analysis.recommendations) {
            html += `<div class="rec-item"><div class="rec-title">${rec.title}</div><div class="rec-desc">${rec.description}</div></div>`;
        }
        html += `</div>`;
    }
    html += `<div class="suggestion-intro" style="margin-top:20px;"><p>Dựa trên mật khẩu <strong>"${crackedPassword}"</strong>, đề xuất:</p></div><div class="suggestion-list">`;
    for (let i = 0; i < suggestions.length; i++) {
        const sug = suggestions[i];
        html += `<div class="suggestion-item">
            <div class="suggestion-number">${i + 1}</div>
            <div class="suggestion-password">
                <code>${sug.password}</code>
                <button class="copy-suggestion-btn" onclick="copyToClipboard('${sug.password.replace(/'/g, "\\'")}')">📋 Sao chép</button>
            </div>
            <div class="suggestion-strength strength-${sug.strength.toLowerCase().replace(' ', '-')}">Độ mạnh: ${sug.strength}</div>
            <div class="suggestion-note">${i === 0 ? '⭐ Khuyến nghị nhất' : '🔄 Thay thế'}</div>
        </div>`;
    }
    html += `</div><div class="suggestion-tips"><h4>💡 Mẹo ghi nhớ:</h4><ul><li>Viết ra giấy, cất an toàn</li><li>Câu thần chú: "Nhà tôi 123" -> "Nt@123"</li><li>Dùng Bitwarden (miễn phí)</li></ul></div>`;
    setMainResult('🚨 PHÂN TÍCH LỖ HỔNG', html);
}

function showDirbResults(result) {
    const found = result.found || [];
    let html = `
        <div class="vuln-summary" style="border-left-color:#17a2b8;">
            <div class="vuln-badge" style="background:#17a2b8;color:white;">🔍 KẾT QUẢ DIRB</div>
            <div class="vuln-network"><strong>🎯 Mục tiêu:</strong> ${result.target || '(không rõ)'}</div>
            <div class="vuln-network"><strong>📊 Tổng số:</strong> ${found.length}</div>
        </div>`;
    if (found.length === 0) {
        html += `<div style="text-align:center;padding:30px;color:#999;">Không tìm thấy thư mục/file ẩn nào</div>`;
    } else {
        const priority = { '200': 1, '201': 1, '301': 2, '302': 3, '307': 3, '401': 4, '403': 5 };
        found.sort((a, b) => (priority[a.status] || 9) - (priority[b.status] || 9));
        for (const item of found) {
            const cls = item.status === '200' || item.status === '201' ? ''
                      : (item.status === '301' || item.status === '302' || item.status === '307') ? 'redirect'
                      : 'forbidden';
            html += `<div class="dirb-result-item">
                <a href="${item.url}" target="_blank" rel="noopener">🔗 ${item.url}</a>
                <span class="dirb-status-badge ${cls}">HTTP ${item.status}</span>
            </div>`;
        }
    }
    setMainResult('🔍 KẾT QUẢ QUÉT THƯ MỤC ẨN', html);
}

function showBlockedResult(moduleName, command, hangCount) {
    let html = `<div class="vuln-summary" style="border-left-color:#dc3545;">
        <div class="vuln-badge" style="background:#dc3545;color:white;">⛔ MODULE BỊ KHÓA</div>
        <div class="vuln-network"><strong>📦 Module:</strong> ${moduleName}</div>
        <div class="vuln-network"><strong>⚙ Lệnh:</strong> ${command}</div>
        <div class="vuln-password"><strong>⚠ Số lần treo:</strong> ${hangCount}</div>
    </div>
    <div class="recommendations"><h3>🛠️ KHẮC PHỤC</h3>
        <div class="rec-item"><div class="rec-title">1. Khởi động lại tool</div><div class="rec-desc">Nhấn "🛑 TẮT TOOL" và chạy lại. Session sẽ tự dọn dẹp.</div></div>
        <div class="rec-item"><div class="rec-title">2. Kiểm tra mạng</div><div class="rec-desc">Đảm bảo WiFi ổn định, không ngắt giữa chừng.</div></div>
        <div class="rec-item"><div class="rec-title">3. Giảm tải module</div><div class="rec-desc">Giảm max_workers trong data/modules/dirb.json.</div></div>
    </div>`;
    setMainResult('⛔ MODULE BỊ KHÓA', html);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        const toast = document.createElement('div');
        toast.className = 'copy-toast';
        toast.textContent = '✅ Đã sao chép!';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    });
}

// ============== WEBSOCKET CLIENT ==============
class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 2000;
        this.isConnecting = false;
        this.isProcessing = false;
        this.isReady = false;
        this.systemStatus = { system: false, scanning: false, connecting: false, wps_attacking: false, lan_scanning: false };
        this.pendingCommands = [];
        this.storedNetworks = new Map();
        this.lastCrackedPassword = null;
        this.currentFakePasswordValue = '';
        this.isFakePasswordActive = false;
        this.currentTask = null;
        this.taskInfo = null;
        this.lastSentCommand = null;
        this.lastSentParams = null;
        this.localProcessing = false;
        this.retryAttempts = {};
        this.pendingRetry = null;
        this.blockedModules = new Set();
        // ⭐ v2.1: track panel đang xem để auto-refresh khi reconnect
        this._lastPanelCommand = null;
        this._lastPanelParams = null;
    }

    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) return;
        this.isConnecting = true;
        const wsPort = window.location.port ? parseInt(window.location.port) + 1 : 81;
        const wsUrl = `ws://${window.location.hostname}:${wsPort}`;

        try {
            this.ws = new WebSocket(wsUrl);
            this.ws.onopen = () => {
                // ⭐ v2.1: detect reconnect (không phải lần connect đầu)
                const wasReconnect = this.reconnectAttempts > 0;
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.isReady = true;
                this.updateWSStatus(true);
                updateTicker('✅ WebSocket đã kết nối');
                this.addLog('[SYSTEM] ✅ Kết nối WebSocket thành công!', 'system-log');
                this.updateUIState();

                // ⭐ v2.1: auto-refresh DOM sau reconnect (vd: sau khi tool restart)
                if (wasReconnect) {
                    setTimeout(() => this._refreshAfterReconnect(), 300);
                }

                if (this.pendingRetry) {
                    const retry = this.pendingRetry;
                    this.pendingRetry = null;
                    this.addLog(`[SYSTEM] 🔄 Thử lại: ${retry.command}...`, 'system-log');
                    setTimeout(() => this.send(retry.command, retry.params || {}), 2000);
                }
                while (this.pendingCommands.length > 0) {
                    const cmd = this.pendingCommands.shift();
                    this.send(cmd.command, cmd.params);
                }
            };
            this.ws.onmessage = (event) => {
                try { this.handleMessage(JSON.parse(event.data)); } catch (e) {}
            };
            this.ws.onclose = () => {
                const wasProcessing = this.isProcessing || this.localProcessing;
                const lastCmd = this.lastSentCommand;
                const lastParams = this.lastSentParams;
                const taskName = this.currentTask;
                this.isReady = false;
                this.isConnecting = false;
                this.isProcessing = false;
                this.localProcessing = false;
                this.updateWSStatus(false);
                if (wasProcessing && lastCmd) this.handleDisconnectRetry(lastCmd, lastParams, taskName);
                this.scheduleReconnect();
            };
            this.ws.onerror = () => { this.isReady = false; this.updateWSStatus(false); };
        } catch (error) {
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }

    // ⭐ v2.1: refresh DOM sau reconnect — load lại nút module + panel đang xem
    _refreshAfterReconnect() {
        // 1) Load lại nút module ở top nav (module mới có thể đã xuất hiện)
        if (typeof loadUIModules === 'function') {
            loadUIModules().then(() => {
                this.addLog('[SYSTEM] 🔄 Đã làm mới danh sách nút module', 'system-log');
            }).catch(() => {});
        }
        // 2) Nếu user đang xem panel module → re-send lệnh đó để lấy data mới
        if (this._lastPanelCommand && this.isReady) {
            const cmd = this._lastPanelCommand;
            const prm = this._lastPanelParams || {};
            this.addLog(`[SYSTEM] 🔄 Đang làm mới panel: ${cmd}...`, 'system-log');
            setTimeout(() => {
                // double check vẫn còn đang xem panel này
                if (this._lastPanelCommand === cmd && this.isReady) {
                    this.send(cmd, prm, /* silent */ true);
                }
            }, 400);
        }
    }

    handleDisconnectRetry(command, params, taskName) {
        // ⭐ v2: không retry cho install_module (tool restart sau install — bình thường)
        if (command === 'install_module' || command === 'restart_tool') {
            this.addLog(`[SYSTEM] ⚠ Mất WS sau "${command}" — tool đang restart, chờ reconnect...`, 'system-log');
            return;
        }
        const retries = this.retryAttempts[command] || 0;
        this.addLog(`[ERROR] ⚠ Mất WS khi chạy "${command}". Server đã kill toàn bộ process.`, 'error-log');
        if (retries >= 2) {
            this.addLog(`[ERROR] ⛔ Lệnh "${command}" liên tục treo. Đã BLOCK.`, 'error-log');
            this.blockedModules.add(command);
            showBlockedResult(command, command, retries + 1);
            return;
        }
        const userConfirm = confirm(
            `⚠ MẤT KẾT NỐI WEBSOCKET\n\nLệnh: ${command}\nTask: ${taskName || 'không rõ'}\n\n` +
            `Server đã tự dừng mọi process. WiFi đã khôi phục.\n\n` +
            `Thử lại lệnh này?\n(Lần: ${retries + 1}/3)`
        );
        if (userConfirm) {
            this.retryAttempts[command] = retries + 1;
            this.pendingRetry = { command, params };
            this.addLog(`[SYSTEM] 📌 Sẽ thử lại "${command}" sau khi kết nối lại...`, 'system-log');
        } else {
            this.retryAttempts[command] = retries + 1;
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            updateTicker('❌ Không thể kết nối WS - tải lại trang');
            this.addLog('[ERROR] Không thể kết nối WS sau nhiều lần thử', 'error-log');
            this.pendingRetry = null;
            return;
        }
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.min(this.reconnectAttempts, 5);
        updateTicker(`🔄 Đang kết nối lại (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        setTimeout(() => this.connect(), delay);
    }

    updateWSStatus(connected) {
        const dot = document.getElementById('wsStatusDot');
        const text = document.getElementById('wsStatusText');
        if (!dot || !text) return;
        if (connected) {
            dot.className = 'status-dot connected';
            text.textContent = 'Đã kết nối';
        } else if (this.isConnecting) {
            dot.className = 'status-dot connecting';
            text.textContent = 'Đang kết nối...';
        } else {
            dot.className = 'status-dot disconnected';
            text.textContent = 'Mất kết nối';
        }
    }

    addLog(line, type = '') {
        addLogToHistory(line, type);
        updateTicker(line, type);
        if (type === 'error-log' || /❌|\[ERROR\]|\[✗\]/.test(line)) {
            showToast(line, 'error', 6000);
        } else if (/\[RESULT\]|✅ Thành công|✓ Hoàn tất/.test(line)) {
            showToast(line, 'success', 4000);
        } else if (/⚠️|\[WARNING\]/.test(line)) {
            showToast(line, 'warning', 4000);
        }
    }

    handleServerLog(line, id) {
        addLogToHistory(line, '');
        updateTicker(line, '');
        if (/❌|\[ERROR\]|\[✗\]|Lỗi:|Thất bại/.test(line)) {
            showToast(line, 'error', 6000);
        } else if (/\[WPS\]|\[INSTALLER\]|✓ Thành công|Hoàn tất/.test(line)) {
            showToast(line, 'success', 3000);
        }
    }

    addLoadingLog(message) { updateTicker(message); }
    removeLoadingLog() { /* no-op */ }

    handleMessage(data) {
        switch (data.type) {
            case 'log':
                this.handleServerLog(data.line, data.id);
                break;
            case 'progress':
                showProgress(data.pct, data.label);
                const sec = document.getElementById('mainResultSection');
                if (sec && data.pct !== null && data.pct !== undefined) sec.style.display = 'block';
                break;
            case 'networks':
                this.updateNetworkList(data.data);
                break;
            case 'lan_devices':
                this.updateLanDevices(data.data);
                break;
            case 'module_panel':
                setMainResult(data.title || '📊 KẾT QUẢ MODULE', renderModulePanel(data.panel));
                break;
            case 'status':
                this.updateSystemStatus(data);
                this.isProcessing = data.is_processing;
                if (data.blocked_modules) this.blockedModules = new Set(data.blocked_modules);
                this.updateUIState();
                break;
            case 'result':
                this.handleCommandResult(data.command, data.result);
                break;
            case 'busy':
                this.handleBusy(data);
                break;
            case 'error':
                this.handleError(data);
                break;
        }
    }

    updateNetworkList(networks) {
        if (!networks || networks.length === 0) {
            document.getElementById('networkContainer').innerHTML =
                '<div style="text-align: center; padding: 40px; color: #999;">Không tìm thấy mạng WiFi</div>';
            return;
        }
        networks.forEach(net => this.storedNetworks.set(net.stt, net));
        let html = `<div class="network-list"><div class="network-header"><div>STT</div><div>Tên WiFi</div><div>BSSID (MAC)</div><div>WPS</div></div>`;
        networks.forEach(net => {
            const wpsBadge = net.wps_enabled ? '<span class="wps-badge">✅ Có</span>' : '<span class="wps-badge" style="background:#dc3545;">❌ Không</span>';
            const savedBadge = net.has_password ? '<span class="saved-badge">💾 Đã lưu</span>' : '';
            const signalIcon = net.signal || '📶';
            const disabledClass = this.isProcessing ? 'disabled-item' : '';
            const selectedClass = window.selectedNetwork && window.selectedNetwork.stt === net.stt ? 'selected' : '';
            html += `<div class="network-item ${disabledClass} ${selectedClass}" onclick="if(window.wsClient && !window.wsClient.isProcessing) selectNetwork(${net.stt})" data-stt="${net.stt}">
                <div><strong>${net.stt}</strong></div>
                <div>${this.escapeHtml(net.ssid)} ${savedBadge}<div style="font-size: 10px; color: #666;">${signalIcon}</div></div>
                <div style="font-size: 11px; font-family: monospace;">${net.bssid}</div>
                <div>${wpsBadge}</div>
            </div>`;
        });
        html += '</div>';
        document.getElementById('networkContainer').innerHTML = html;
        window.networksList = networks;
        const lanC = document.getElementById('lanContainer');
        if (lanC) lanC.style.display = 'none';
    }

    updateLanDevices(devices) {
        if (!devices || Object.keys(devices).length === 0) {
            document.getElementById('lanDevicesContainer').innerHTML =
                '<div style="text-align: center; padding: 40px; color: #999;">Không tìm thấy thiết bị nào trong mạng LAN</div>';
            document.getElementById('lanContainer').style.display = 'block';
            return;
        }
        let html = `<div class="lan-list"><div class="lan-header"><div>Địa chỉ IP</div><div>Thông tin</div><div>Số cổng mở</div></div>`;
        for (const [ip, device] of Object.entries(devices)) {
            const portCount = device.total_open || 0;
            const ports = device.open_ports || [];
            const osGuess = device.os_guess || 'Unknown';
            let portsHtml = ports.length > 0
                ? `<div class="lan-device-ports">🔌 ${ports.slice(0, 5).map(p => `<span class="lan-port-badge">${p}</span>`).join('')} ${ports.length > 5 ? `+${ports.length - 5}` : ''}</div>`
                : `<div class="lan-device-ports">❌ Không có cổng mở</div>`;
            const deviceJson = JSON.stringify(device).replace(/"/g, '&quot;');
            html += `<div class="lan-item clickable" onclick="showLanDetailModal('${ip}', ${deviceJson})">
                <div class="lan-device-ip">🌐 ${ip}</div>
                <div><div class="lan-os-guess">💻 ${osGuess}</div>${portsHtml}</div>
                <div><span class="lan-badge">${portCount} cổng</span></div>
            </div>`;
        }
        html += '</div>';
        document.getElementById('lanDevicesContainer').innerHTML = html;
        document.getElementById('lanContainer').style.display = 'block';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    updateSystemStatus(status) {
        this.systemStatus = status.data || status;
        this.currentTask = status.current_task;
        this.taskInfo = status.task_info;
        this.updateStopButton();
        let statusMessage = '';
        if (status.data?.scanning || status.scanning) statusMessage = '📡 Đang quét mạng WiFi...';
        else if (status.data?.connecting || status.connecting) statusMessage = '🔌 Đang kết nối...';
        else if (status.data?.wps_attacking || status.wps_attacking) statusMessage = '⚡ Đang tấn công WPS...';
        else if (status.data?.lan_scanning || status.lan_scanning) statusMessage = '🌐 Đang quét LAN...';
        else if (status.data?.system || status.system) statusMessage = '⏳ Đang xử lý...';
        else { statusMessage = '✅ Sẵn sàng'; this.hideStopButton(); }
        updateTicker(statusMessage);
        this.updateStatus(statusMessage);
    }

    updateStopButton() {
        const stopContainer = document.getElementById('stopButtonContainer');
        const stopBtn = document.getElementById('stopBtn');
        if (!stopContainer || !stopBtn) return;
        const isKnownStopable = this.taskInfo && this.taskInfo.can_stop;
        const hasCurrentTask = this.currentTask && this.currentTask !== '' &&
                               this.currentTask !== 'stop' && this.currentTask !== 'get_status';
        const shouldShow = this.isProcessing && (isKnownStopable || hasCurrentTask);
        if (shouldShow) {
            stopContainer.style.display = 'block';
            const taskIcon = (this.taskInfo && this.taskInfo.icon) || '⚙️';
            let taskName = 'TÁC VỤ';
            if (this.taskInfo && this.taskInfo.name) taskName = this.taskInfo.name.toUpperCase();
            else if (this.currentTask) taskName = this.currentTask.replace(/_/g, ' ').toUpperCase();
            stopBtn.innerHTML = `${taskIcon} DỪNG ${taskName} NGAY ${taskIcon}`;
            if (!stopBtn.querySelector('.task-indicator')) {
                const indicator = document.createElement('span');
                indicator.className = 'task-indicator';
                stopBtn.insertBefore(indicator, stopBtn.firstChild);
            }
        } else {
            stopContainer.style.display = 'none';
        }
    }

    hideStopButton() {
        const stopContainer = document.getElementById('stopButtonContainer');
        if (stopContainer) stopContainer.style.display = 'none';
    }

    updateUIState() {
        const btns = ['scanBtn', 'clearCardBtn', 'quitBtn', 'shutdownBtn', 'connectBtn', 'wpsBtn', 'autoConnectBtn', 'clearBtn', 'togglePasswordBtn'];
        const inputs = ['passwordInput'];
        const enabled = this.isReady && !this.isProcessing && !this.localProcessing;
        btns.forEach(id => { const btn = document.getElementById(id); if (btn) btn.disabled = !enabled; });
        inputs.forEach(id => { const input = document.getElementById(id); if (input) input.disabled = !enabled; });
        document.querySelectorAll('.module-btn').forEach(btn => {
            const isBlocked = btn.dataset.blocked === '1';
            btn.disabled = !enabled || isBlocked;
            const cmd = btn.dataset.command;
            if (cmd && this.blockedModules.has(cmd)) {
                btn.style.opacity = '0.4';
                btn.title = 'Module bị khóa';
            } else if (isBlocked) {
                btn.style.opacity = '0.55';
            } else {
                btn.style.opacity = '';
                btn.title = '';
            }
        });
        this.updateStopButton();
        if (enabled && window.selectedNetwork && window.selectedNetwork.wps_enabled) {
            document.getElementById('wpsBtn').disabled = false;
        } else if (enabled && window.selectedNetwork && !window.selectedNetwork.wps_enabled) {
            document.getElementById('wpsBtn').disabled = true;
        }
        if (enabled && window.selectedNetwork) {
            document.getElementById('connectBtn').disabled = false;
            document.getElementById('autoConnectBtn').disabled = false;
        } else if (enabled && !window.selectedNetwork) {
            document.getElementById('connectBtn').disabled = true;
            document.getElementById('autoConnectBtn').disabled = true;
        }
    }

    updateStatus(message) {
        const statusDiv = document.getElementById('status');
        const time = new Date().toLocaleTimeString();
        if (statusDiv) statusDiv.innerHTML = `[${time}] ${message}`;
    }

    handleCommandResult(command, result) {
        this.removeLoadingLog();
        this.localProcessing = false;
        this.updateUIState();

        if (result && result.type === 'module_blocked') {
            this.blockedModules.add(result.module);
            showBlockedResult(result.module, command, result.hang_count || 0);
            this.addLog(`[ERROR] ⛔ ${result.message}`, 'error-log');
            stopProgress();
            this.updateUIState();
            return;
        }

        if (result && result.type === 'permission_denied') {
            stopProgress();
            const msg = result.message || 'Yêu cầu quyền ROOT';
            showToast('⛔ ' + msg, 'error', 8000);
            this.addLog(`[ERROR] ⛔ ${msg}`, 'error-log');
            this.updateStatus(`⛔ ${msg}`);
            return;
        }

        if (result && result.type === 'cancelled') {
            stopProgress();
            this.addLog(`[CANCELLED] ${result.message || 'Đã dừng giữa chừng'}`, 'system-log');
            this.updateStatus(`⏹️ ${result.message || 'Đã dừng'}`);
            if (result.hosts && Object.keys(result.hosts).length > 0) {
                this.updateLanDevices(result.hosts);
                const lanC = document.getElementById('lanContainer');
                if (lanC) lanC.style.display = 'block';
            }
            if (result.networks && result.networks.length > 0) {
                this.updateNetworkList(result.networks);
            }
            if (result.found) {
                showDirbResults({ target: result.target || '(không rõ)', found: result.found, total: result.found.length });
            }
            this.updateUIState();
            return;
        }

        if (result.status === 'success' || result.status === 'error') delete this.retryAttempts[command];

        const extractRealPassword = (cmd, res) => {
            if (this.lastCrackedPassword) {
                const pwd = this.lastCrackedPassword;
                this.lastCrackedPassword = null;
                return pwd;
            }
            if (res.message) {
                const extracted = this.extractPasswordFromLog(res.message);
                if (extracted) return extracted;
            }
            if (res.password && res.password !== '********') return res.password;
            return generateFakePassword(12);
        };

        if (command === 'scan' && result.status === 'success') {
            stopProgress();
            if (result.networks) {
                this.updateStatus(`✅ Tìm thấy ${result.networks.length} mạng WiFi`);
                this.addLog(`[RESULT] ✅ Tìm thấy ${result.networks.length} mạng WiFi`, 'system-log');
            }
        } else if (command === 'lan_scan' && result.status === 'success') {
            stopProgress();
            this.updateStatus(`✅ Quét LAN thành công! ${result.total_hosts || 0} thiết bị`);
            this.addLog(`[RESULT] ✅ Quét LAN [${result.scan_mode || 'normal'}] → ${result.total_hosts || 0} thiết bị`, 'system-log');
            if (result.hosts) this.updateLanDevices(result.hosts);
        } else if (command === 'lan_quick_scan' && result.status === 'success') {
            stopProgress();
            this.updateStatus(`✅ Quét nhanh LAN thành công! ${result.total_hosts || 0} thiết bị`);
            this.addLog(`[RESULT] ✅ Quét nhanh LAN → ${result.total_hosts || 0} thiết bị`, 'system-log');
            if (result.hosts) this.updateLanDevices(result.hosts);
        } else if (command === 'scan_specific_host' && result.status === 'success') {
            stopProgress();
            this.updateStatus(`✅ Quét host thành công!`);
            this.addLog(`[RESULT] ✅ ${result.message}`, 'system-log');
        } else if (command === 'dirb' && result.status === 'success') {
            stopProgress();
            this.updateStatus(`✅ Tìm thấy ${result.total || 0} mục ẩn`);
            this.addLog(`[RESULT] ✅ Tìm thấy ${result.total || 0} mục trên ${result.target}`, 'system-log');
            showDirbResults(result);
        } else if (command === 'shutdown') {
            stopProgress();
            this.updateStatus(`🛑 Tool đang tắt...`);
            this.addLog(`[SYSTEM] 🛑 Tool đang tắt.`, 'system-log');
        } else if (command === 'connect_with_password' && result.status === 'success') {
            stopProgress();
            this.updateStatus(`✅ Kết nối thành công!`);
            this.addLog(`[RESULT] ✅ ${result.message}`, 'system-log');
            if (window.selectedNetwork) {
                window.selectedNetwork.has_password = true;
                const passwordInput = document.getElementById('passwordInput');
                let realPassword;
                if (this.isFakePasswordActive && passwordInput.value === this.currentFakePasswordValue) {
                    realPassword = extractRealPassword(command, result);
                } else {
                    realPassword = passwordInput.value;
                }
                showVulnerabilityReport('password', window.selectedNetwork, realPassword);
            }
            const savedHint = document.getElementById('savedHint');
            savedHint.innerHTML = '✅ Đã kết nối thành công! Mật khẩu đã được lưu.';
            savedHint.classList.add('warning');
            setTimeout(() => {
                if (window.selectedNetwork && window.selectedNetwork.has_password) this.updateSavedHintForNetwork(window.selectedNetwork);
                savedHint.classList.remove('warning');
            }, 3000);
        } else if (command === 'wps_attack' && result.status === 'success') {
            stopProgress();
            this.updateStatus(result.connected ? `✅ WPS thành công + đã kết nối!` : `✅ WPS thành công!`);
            this.addLog(`[RESULT] ✅ ${result.message}`, 'system-log');
            if (window.selectedNetwork) {
                window.selectedNetwork.has_password = true;
                const attackType = result.pixie_dust ? 'pixie_dust' : 'wps';
                let realPassword = extractRealPassword(command, result);
                showVulnerabilityReport(attackType, window.selectedNetwork, realPassword);
            }
            const savedHint = document.getElementById('savedHint');
            savedHint.innerHTML = '✅ WPS thành công! Mật khẩu đã được lưu.';
            savedHint.classList.add('warning');
            setTimeout(() => {
                if (window.selectedNetwork && window.selectedNetwork.has_password) this.updateSavedHintForNetwork(window.selectedNetwork);
                savedHint.classList.remove('warning');
            }, 3000);
        } else if (command === 'auto_connect' && result.status === 'success') {
            stopProgress();
            this.updateStatus(`✅ Auto Connect thành công!`);
            this.addLog(`[RESULT] ✅ ${result.message}`, 'system-log');
            if (window.selectedNetwork) {
                window.selectedNetwork.has_password = true;
                let realPassword = extractRealPassword(command, result);
                showVulnerabilityReport('auto_connect', window.selectedNetwork, realPassword);
            }
            const savedHint = document.getElementById('savedHint');
            savedHint.innerHTML = '✅ Auto Connect thành công! Mật khẩu đã được lưu.';
            savedHint.classList.add('warning');
            setTimeout(() => {
                if (window.selectedNetwork && window.selectedNetwork.has_password) this.updateSavedHintForNetwork(window.selectedNetwork);
                savedHint.classList.remove('warning');
            }, 3000);
        } else if (command === 'install_module') {
            stopProgress();
            if (result.status === 'success') {
                const msg = result.message || 'Đã cài module thành công';
                this.updateStatus(`✅ ${msg}`);
                this.addLog(`[RESULT] ✅ ${msg}`, 'system-log');
                showToast('✅ ' + msg, 'success', 6000);
            } else {
                this.updateStatus(`❌ Lỗi cài module: ${result.message}`);
                this.addLog(`[ERROR] ${result.message}`, 'error-log');
            }
        } else if (command === 'restart_tool' && result.status === 'success') {
            stopProgress();
            const msg = result.message || 'Tool đang khởi động lại...';
            this.updateStatus(`🔄 ${msg}`);
            this.addLog(`[SYSTEM] 🔄 ${msg}`, 'system-log');
        } else if (result.status === 'error') {
            stopProgress();
            this.updateStatus(`❌ Lỗi: ${result.message}`);
            this.addLog(`[ERROR] ${result.message}`, 'error-log');
        }
    }

    extractPasswordFromLog(logLine) {
        const patterns = [
            /mật khẩu[:\s]+([^\s]+)/i, /password[:\s]+([^\s]+)/i,
            /psk[:\s]+([^\s]+)/i, /key[:\s]+([^\s]+)/i, /pass[:\s]+([^\s]+)/i,
            /'([^']+)' là mật khẩu/i, /"([^"]+)" là mật khẩu/i
        ];
        for (let pattern of patterns) {
            const match = logLine.match(pattern);
            if (match && match[1] && match[1] !== '********' && match[1].length >= 4) return match[1];
        }
        return null;
    }

    handleBusy(data) {
        this.localProcessing = false;
        this.updateUIState();
        stopProgress();
        this.updateStatus(`⚠️ ${data.message}`);
        this.addLog(`[SYSTEM] ${data.message}`, 'system-log');
    }

    handleError(data) {
        this.localProcessing = false;
        this.updateUIState();
        stopProgress();
        this.updateStatus(`❌ Lỗi: ${data.message}`);
        this.addLog(`[ERROR] ${data.message}`, 'error-log');
    }

    // ⭐ v2.1: thêm tham số `silent` — khi true: không clear panel, không toast,
    //         dùng cho auto-refresh sau reconnect để panel update mượt
    send(command, params = {}, silent = false) {
        this.lastSentCommand = command;
        this.lastSentParams = params;

        // ⭐ v2.1: track lệnh panel để auto-refresh khi reconnect
        const panelCommands = ['list_modules', 'module_detail', 'module_activity', 'get_module_versions'];
        const isPanelCmd = panelCommands.includes(command);

        const nonBlocking = ['get_status', 'clear_terminal', 'shutdown', 'stop', 'stop_task', 'stop_wps', 'reset_blocks'];
        const keepPanelCommands = ['install_module'];

        if (!nonBlocking.includes(command)) {
            this.localProcessing = true;
            if (!keepPanelCommands.includes(command) && !silent) {
                clearMainResult();
            }
            if (!silent) {
                showToast(`🚀 Bắt đầu: ${command}`, 'info', 2000);
            }
            this.updateUIState();
        }

        // ⭐ v2.1: set sau clearMainResult để không bị reset
        if (isPanelCmd) {
            this._lastPanelCommand = command;
            this._lastPanelParams = params;
        }

        const progressCommands = ['scan', 'lan_scan', 'lan_quick_scan', 'scan_specific_host', 'dirb', 'wps_attack', 'auto_connect', 'connect_with_password'];
        if (progressCommands.includes(command)) startProgress(this.getProgressLabel(command, params));

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify({ command, params }));
                this.addLog(`[CMD] $> ${command}`, 'cmd-log');
            } catch (e) {
                this.addLog(`[ERROR] WS send fail: ${e.message}`, 'error-log');
            }
        } else {
            this.pendingCommands.push({ command, params });
            this.addLog(`[SYSTEM] Lệnh "${command}" chờ kết nối...`, 'system-log');
            this.connect();
        }
    }

    getProgressLabel(command, params) {
        if (command === 'scan') return 'Quét WiFi';
        if (command === 'lan_scan') return 'Quét LAN — ' + ((params && params.mode) || 'normal');
        if (command === 'lan_quick_scan') return 'Quét nhanh LAN';
        if (command === 'scan_specific_host') return 'Quét host ' + ((params && params.target_ip) || '');
        if (command === 'dirb') return 'Quét thư mục ẩn';
        if (command === 'wps_attack') return 'Tấn công WPS';
        if (command === 'auto_connect') return 'Auto connect';
        if (command === 'connect_with_password') return 'Kết nối WiFi';
        return command;
    }

    updateSavedHintForNetwork(network) {
        const savedHint = document.getElementById('savedHint');
        const passwordInput = document.getElementById('passwordInput');
        if (network && network.has_password) {
            const fakePassword = generateFakePassword(12);
            passwordInput.value = fakePassword;
            passwordInput.placeholder = '🔒 Đã có mật khẩu lưu - Nhập mới nếu muốn đổi';
            this.markAsFakePassword(fakePassword);
            savedHint.innerHTML = '🔒 Mạng này đã có mật khẩu được lưu.';
            savedHint.style.color = '#ffc107';
        }
    }

    markAsFakePassword(fakePassword) {
        this.isFakePasswordActive = true;
        this.currentFakePasswordValue = fakePassword;
    }
    markAsRealPassword() {
        this.isFakePasswordActive = false;
        this.currentFakePasswordValue = '';
    }
    isInputFakePassword() {
        if (!this.isFakePasswordActive) return false;
        const passwordInput = document.getElementById('passwordInput');
        return passwordInput.value === this.currentFakePasswordValue;
    }
}

// ============== MODULE UI ĐỘNG ==============
let currentCategory = "all";
let allModuleButtons = [];

async function loadUIModules() {
    try {
        const res = await fetch('/api/ui', { cache: 'no-store' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();

        window.APP_CONFIG.isRoot = data.is_root === true;
        window.APP_CONFIG.rootMethod = data.root_method || 'none';
        window.APP_CONFIG.rootRequiredCommands = new Set(data.root_required_commands || []);
        updateRootBanner(data.is_root, data.root_method);

        renderMenuNav(data.categories || []);
        allModuleButtons = data.buttons || [];
        renderModuleButtons();
    } catch (e) {
        const nav = document.getElementById('menuNav');
        if (nav) nav.innerHTML = '<span style="font-size:11px;color:#999;padding:6px;">Không tải được module</span>';
        throw e;
    }
}

function renderMenuNav(categories) {
    const nav = document.getElementById('menuNav');
    if (!nav) return;
    let html = `<button class="menu-tab active" data-cat="all">📦 Tất cả</button>`;
    for (const cat of categories) html += `<button class="menu-tab" data-cat="${cat.id}">${cat.icon || ''} ${cat.label || cat.id}</button>`;
    nav.innerHTML = html;
    nav.querySelectorAll('.menu-tab').forEach(tab => {
        tab.onclick = () => {
            currentCategory = tab.dataset.cat;
            nav.querySelectorAll('.menu-tab').forEach(t => t.classList.toggle('active', t === tab));
            renderModuleButtons();
        };
    });
}

function renderModuleButtons() {
    const container = document.getElementById('moduleButtons');
    if (!container) return;
    const filtered = currentCategory === 'all' ? allModuleButtons : allModuleButtons.filter(b => b.category === currentCategory);
    if (filtered.length === 0) {
        container.innerHTML = '<div class="module-empty">📭 Không có module trong mục này</div>';
        return;
    }
    let html = '';
    for (const btn of filtered) {
        const color = btn.color || 'secondary';
        const icon = btn.icon || '🔧';
        const paramsAttr = encodeURIComponent(JSON.stringify(btn.params || {}));
        const promptAttr = encodeURIComponent(JSON.stringify(btn.prompt || null));
        const canRun = btn.can_run !== false;
        const requiresRoot = btn.requires_root === true;
        const lockIcon = (!canRun && requiresRoot) ? ' 🔒' : '';
        const blockedAttr = canRun ? '' : 'data-blocked="1"';
        const titleAttr = (!canRun && requiresRoot)
            ? 'title="⚠️ Cần quyền ROOT — chạy sudo python main.py"'
            : '';
        html += `<button class="btn btn-${color} module-btn" 
            data-command="${btn.command}" 
            data-params="${paramsAttr}" 
            data-prompt="${promptAttr}"
            ${blockedAttr} ${titleAttr}>${icon} ${btn.label}${lockIcon}</button>`;
    }
    container.innerHTML = html;
    container.querySelectorAll('.module-btn').forEach(el => {
        el.onclick = () => handleModuleButtonClick(el);
    });
    if (wsClient) wsClient.updateUIState();
}

function handleModuleButtonClick(btnEl) {
    if (btnEl.dataset.blocked === '1') {
        showToast('🔒 Lệnh này cần quyền ROOT. Chạy lại tool bằng: sudo python main.py', 'warning', 6000);
        return;
    }
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady) return;
    const command = btnEl.dataset.command;
    let params = {};
    try { params = JSON.parse(decodeURIComponent(btnEl.dataset.params || '%7B%7D')); } catch (e) {}
    let promptCfg = null;
    try {
        const raw = decodeURIComponent(btnEl.dataset.prompt || 'null');
        promptCfg = raw === 'null' ? null : JSON.parse(raw);
    } catch (e) { promptCfg = null; }
    if (promptCfg && promptCfg.field) {
        askModalInput(promptCfg.message || 'Nhập giá trị:', promptCfg.default || '', promptCfg.hint || '').then(val => {
            if (val === null) return;
            const trimmed = val.trim();
            if (!trimmed) return;
            params[promptCfg.field] = trimmed;
            wsClient.send(command, params);
        });
    } else {
        wsClient.send(command, params);
    }
}

// ============== QUẢN LÝ MẠNG ==============
let wsClient = null;
let selectedNetwork = null;

function stopAllTasks() {
    if (!wsClient || !wsClient.isReady) return;
    let taskName = 'tác vụ';
    if (wsClient.taskInfo) taskName = wsClient.taskInfo.name.toLowerCase();
    else if (wsClient.currentTask) taskName = wsClient.currentTask.replace(/_/g, ' ').toLowerCase();
    if (confirm(`⚠️ Dừng ${taskName} đang chạy?\n\nSẽ:\n- Dừng ngay ${taskName}\n- Trả kết quả dở dang nếu có\n- Khôi phục WiFi\n\nTiếp tục?`)) {
        wsClient.addLog(`[SYSTEM] ⏹️ Dừng ${taskName}...`, 'system-log');
        wsClient.send('stop');
        wsClient.isProcessing = false;
        wsClient.localProcessing = false;
        wsClient.systemStatus.scanning = false;
        wsClient.systemStatus.connecting = false;
        wsClient.systemStatus.wps_attacking = false;
        wsClient.systemStatus.lan_scanning = false;
        wsClient.taskInfo = null;
        wsClient.currentTask = null;
        wsClient.updateUIState();
        wsClient.hideStopButton();
        stopProgress();
        wsClient.updateStatus(`✅ Đã dừng ${taskName}`);
    }
}

function selectNetwork(stt) {
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady) return;
    const networks = window.networksList || [];
    const network = networks.find(n => n.stt === stt);
    if (!network) return;
    selectedNetwork = network;
    window.selectedNetwork = network;
    document.querySelectorAll('.network-item').forEach(item => {
        item.classList.remove('selected');
        if (item.getAttribute('data-stt') == stt) item.classList.add('selected');
    });
    const savedHint = document.getElementById('savedHint');
    const passwordInput = document.getElementById('passwordInput');
    if (!wsClient.isProcessing && wsClient.isReady) {
        document.getElementById('connectBtn').disabled = false;
        document.getElementById('autoConnectBtn').disabled = false;
        passwordInput.disabled = false;
        document.getElementById('togglePasswordBtn').disabled = false;
        document.getElementById('wpsBtn').disabled = !network.wps_enabled;
    }
    if (network.has_password) {
        const fakePassword = generateFakePassword(12);
        passwordInput.value = fakePassword;
        passwordInput.placeholder = '🔒 Đã có mật khẩu lưu - Nhập mới nếu muốn đổi';
        wsClient.markAsFakePassword(fakePassword);
        savedHint.innerHTML = '🔒 Mạng này đã có mật khẩu được lưu.';
        savedHint.style.color = '#ffc107';
    } else {
        passwordInput.value = '';
        passwordInput.placeholder = '🔐 Nhập mật khẩu WiFi (bắt buộc)';
        wsClient.markAsRealPassword();
        savedHint.innerHTML = `🔐 Vui lòng nhập mật khẩu cho <strong>${network.ssid}</strong>`;
        savedHint.style.color = '#28a745';
    }
}

function showLanDetailModal(ip, device) {
    const ports = device.port_details || [];
    const portListHtml = ports.length > 0 ? `
        <table style="width:100%; margin-top:15px; border-collapse:collapse;">
            <tr style="background:rgba(0,0,0,0.05);"><th style="padding:8px; text-align:left;">Cổng</th><th style="padding:8px; text-align:left;">Dịch vụ</th><th style="padding:8px; text-align:left;">Trạng thái</th></tr>
            ${ports.map(p => `<tr style="border-bottom:1px solid rgba(0,0,0,0.1);"><td style="padding:8px;">${p.port}</td><td style="padding:8px;">${p.service}</td><td style="padding:8px; color:#28a745;">✓ MỞ</td></tr>`).join('')}
        </table>` : '<p>Không có cổng nào mở</p>';
    const modalHtml = `
        <div id="lanDetailModal" class="modal-overlay">
            <div style="background:white; border-radius:12px; max-width:600px; width:90%; max-height:80%; overflow:auto;">
                <div style="padding:15px 20px; background:linear-gradient(135deg, #2c3e50 0%, #1a1a2e 100%); color:white; display:flex; justify-content:space-between; align-items:center;">
                    <h3>🖧 Chi Tiết Thiết Bị</h3>
                    <button onclick="closeLanDetailModal()" style="background:none; border:none; color:white; font-size:28px; cursor:pointer;">×</button>
                </div>
                <div style="padding:20px;">
                    <p><strong>IP:</strong> ${ip}</p>
                    <p><strong>OS dự đoán:</strong> ${device.os_guess || 'Không rõ'}</p>
                    <p><strong>Số cổng mở:</strong> ${device.total_open || 0}</p>
                    ${portListHtml}
                    <div style="margin-top:20px; text-align:right; gap:10px; display:flex; justify-content:flex-end;">
                        <button onclick="quickDirb('${ip}')" class="btn btn-info">🔍 Quét thư mục</button>
                        <button onclick="closeLanDetailModal()" class="btn btn-secondary">Đóng</button>
                    </div>
                </div>
            </div>
        </div>`;
    const existing = document.getElementById('lanDetailModal');
    if (existing) existing.remove();
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeLanDetailModal() {
    const modal = document.getElementById('lanDetailModal');
    if (modal) modal.remove();
}

function quickDirb(ip) {
    closeLanDetailModal();
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady) return;
    askModalInput(`URL/port để quét (vd: http://${ip} hoặc http://${ip}:8080):`, `http://${ip}`, 'Thêm :port nếu web chạy port khác 80').then(url => {
        if (!url) return;
        wsClient.send('dirb', { url: url.trim() });
    });
}

function scanNetworks() {
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady) return;
    clearMainResult();
    wsClient.send('scan');
}

function shutdownTool() {
    if (!confirm('⚠️ TẮT TOOL?\n\nTool sẽ dừng hoàn toàn. Phải khởi động lại từ Termux.\n\nTiếp tục?')) return;
    if (!wsClient || !wsClient.isReady) return;
    wsClient.addLog('[SYSTEM] 🛑 Đang tắt tool...', 'system-log');
    wsClient.send('shutdown');
    setTimeout(() => {
        document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;background:#1e1e2e;color:#f48771;font-family:monospace;font-size:20px;text-align:center;padding:20px;">🛑 TOOL ĐÃ TẮT<br><br><span style="font-size:14px;color:#a9b7c6;">Đóng tab. Chạy lại tool từ Termux.</span></div>';
    }, 2500);
}

function connectWithPassword() {
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady || !selectedNetwork) return;
    const passwordInput = document.getElementById('passwordInput');
    const inputValue = passwordInput.value.trim();
    if (wsClient.isInputFakePassword()) {
        wsClient.addLog('[INFO] Dùng mật khẩu đã lưu...', 'system-log');
        wsClient.send('connect_with_password', { network: selectedNetwork, password: '' });
    } else if (inputValue === '') {
        wsClient.updateStatus('⚠️ Vui lòng nhập mật khẩu');
        wsClient.addLog('[WARNING] Vui lòng nhập mật khẩu WiFi', 'error-log');
    } else {
        wsClient.addLog('[INFO] Thử mật khẩu từ client...', 'system-log');
        wsClient.send('connect_with_password', { network: selectedNetwork, password: inputValue });
    }
}

function wpsAttack() {
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady || !selectedNetwork) return;
    if (!selectedNetwork.wps_enabled) { wsClient.updateStatus('⚠️ WPS không được bật'); return; }
    wsClient.send('wps_attack', { network: selectedNetwork });
}

function autoConnect() {
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady || !selectedNetwork) return;
    wsClient.send('auto_connect', { network: selectedNetwork });
}

function clearCard() {
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady) return;
    wsClient.send('clear_all');
}

function quit() {
    if (!wsClient || wsClient.isProcessing || !wsClient.isReady) return;
    wsClient.send('quit');
}

function togglePasswordVisibility() {
    const passwordInput = document.getElementById('passwordInput');
    const btn = document.getElementById('togglePasswordBtn');
    if (!passwordInput || !btn) return;
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        btn.textContent = '🙈';
    } else {
        passwordInput.type = 'password';
        btn.textContent = '👁️';
    }
}

// ============== APP CONFIG (root-aware) ==============
window.APP_CONFIG = {
    isRoot: true,
    rootRequiredCommands: new Set(),
    rootMethod: 'none',
};

function updateRootBanner(isRoot, method) {
    let banner = document.getElementById('rootWarningBanner');
    if (!banner) {
        const container = document.querySelector('.container');
        if (!container) return;
        banner = document.createElement('div');
        banner.id = 'rootWarningBanner';
        banner.style.cssText =
            'padding:10px 15px;border-radius:8px;margin-bottom:15px;' +
            'text-align:center;font-size:13px;font-weight:bold;display:none;';
        const header = container.querySelector('.header');
        if (header && header.parentNode) {
            header.parentNode.insertBefore(banner, header.nextSibling);
        } else {
            container.prepend(banner);
        }
    }
    if (isRoot === false) {
        banner.style.background = '#ffc107';
        banner.style.color = '#333';
        banner.innerHTML =
            `⚠️ Đang chạy KHÔNG ROOT (method: <b>${method || 'none'}</b>) — chỉ dùng được module không cần quyền. ` +
            `Chạy lại bằng <code>sudo python main.py</code> để mở khoá toàn bộ.`;
        banner.style.display = 'block';
    } else {
        banner.style.display = 'none';
    }
}

// ============== CONFIG MANAGEMENT (⚙️ Cài đặt) ==============
let currentConfig = null;
let currentConfigMeta = null;

async function loadConfig() {
    try {
        const res = await fetch('/api/config', { cache: 'no-store' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        currentConfig = data.config;
        currentConfigMeta = {
            is_root: data.is_root,
            root_method: data.root_method,
            config_path: data.config_path,
            restart_required_fields: data.restart_required_fields || [],
        };
        return data;
    } catch (e) {
        console.error('loadConfig error:', e);
        return null;
    }
}

function configEsc(val) {
    if (val === null || val === undefined) return '';
    return String(val).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function buildConfigForm(config) {
    const net = config.network || {};
    const env = config.environment || {};
    const perm = config.permissions || {};
    const mod = config.modules || {};
    const srv = config.server || {};

    return `
        <div class="config-section">
            <h4>🌐 Mạng</h4>
            <div class="config-row">
                <label>Card mạng:</label>
                <input id="cfg_interface" class="modal-input" type="text" value="${configEsc(net.interface)}" placeholder="wlan0">
            </div>
            <div class="config-row">
                <label>Host:</label>
                <input id="cfg_host" class="modal-input" type="text" value="${configEsc(net.host)}" placeholder="0.0.0.0">
            </div>
            <div class="config-row">
                <label>Port (HTTP, WS = port+1):</label>
                <input id="cfg_port" class="modal-input" type="number" value="${configEsc(net.port)}" min="1024" max="65535">
            </div>
        </div>

        <div class="config-section">
            <h4>📦 Môi trường</h4>
            <div class="config-row">
                <label>Binaries (mỗi dòng 1 cái):</label>
                <textarea id="cfg_binaries" class="modal-input" rows="3">${(env.binaries || []).join('\n')}</textarea>
            </div>
            <div class="config-row">
                <label>Python libraries:</label>
                <textarea id="cfg_libraries" class="modal-input" rows="2">${(env.libraries || []).join('\n')}</textarea>
            </div>
            <div class="config-row">
                <label>PYTHONPATH:</label>
                <input id="cfg_python_path" class="modal-input" type="text" value="${configEsc(env.python_path)}" placeholder="/data/...">
            </div>
            <div class="config-row">
                <label>LD_LIBRARY_PATH (mỗi dòng 1 path):</label>
                <textarea id="cfg_lib_paths" class="modal-input" rows="2">${(env.lib_paths || []).join('\n')}</textarea>
            </div>
        </div>

        <div class="config-section">
            <h4>🔐 Quyền</h4>
            <div class="config-row">
                <label>Check method:</label>
                <select id="cfg_check_method" class="modal-input">
                    <option value="sudo" ${perm.check_method === 'sudo' ? 'selected' : ''}>sudo (ưu tiên)</option>
                    <option value="auto" ${perm.check_method === 'auto' ? 'selected' : ''}>auto (euid → sudo → su)</option>
                    <option value="su" ${perm.check_method === 'su' ? 'selected' : ''}>su (Termux/Android)</option>
                    <option value="euid" ${perm.check_method === 'euid' ? 'selected' : ''}>euid only</option>
                    <option value="none" ${perm.check_method === 'none' ? 'selected' : ''}>none (bypass — bỏ qua)</option>
                </select>
            </div>
            <div class="config-row">
                <label style="display:flex;align-items:center;gap:8px;">
                    <input id="cfg_strict_mode" type="checkbox" ${perm.strict_mode ? 'checked' : ''}>
                    <span>Strict mode — chặn lệnh cần ROOT nếu không có quyền</span>
                </label>
            </div>
        </div>

        <div class="config-section">
            <h4>🛠️ Commands cần ROOT (mỗi dòng 1 cái)</h4>
            <div class="config-row">
                <textarea id="cfg_root_cmds" class="modal-input" rows="5">${(mod.root_required_commands || []).join('\n')}</textarea>
            </div>
        </div>

        <div class="config-section">
            <h4>🖥️ Server</h4>
            <div class="config-row">
                <label>Max clients:</label>
                <input id="cfg_max_clients" class="modal-input" type="number" value="${configEsc(srv.max_clients)}" min="1">
            </div>
            <div class="config-row">
                <label>WS ping interval (s):</label>
                <input id="cfg_ping_interval" class="modal-input" type="number" value="${configEsc(srv.ws_ping_interval)}" min="5">
            </div>
            <div class="config-row">
                <label>WS ping timeout (s):</label>
                <input id="cfg_ping_timeout" class="modal-input" type="number" value="${configEsc(srv.ws_ping_timeout)}" min="10">
            </div>
        </div>
    `;
}

function linesToArray(id) {
    const el = document.getElementById(id);
    if (!el) return [];
    return el.value.split('\n').map(s => s.trim()).filter(s => s.length > 0);
}

async function showConfigModal() {
    const modal = document.getElementById('configModal');
    const body = document.getElementById('configFormBody');
    if (!modal || !body) return;
    body.innerHTML = '<div style="text-align:center;padding:30px;color:#888;">Đang tải cấu hình...</div>';
    document.getElementById('configRestartNotice').style.display = 'none';
    modal.style.display = 'flex';

    const data = await loadConfig();
    if (!data || !currentConfig) {
        body.innerHTML = '<div style="text-align:center;padding:30px;color:#dc3545;">❌ Không tải được cấu hình</div>';
        return;
    }
    body.innerHTML = buildConfigForm(currentConfig);
}

function hideConfigModal() {
    const modal = document.getElementById('configModal');
    if (modal) modal.style.display = 'none';
}

async function saveConfigFromModal() {
    if (!currentConfig) return;
    const saveBtn = document.getElementById('configSaveBtn');
    saveBtn.disabled = true;
    saveBtn.textContent = '⏳ Đang lưu...';

    const newCfg = {
        network: {
            interface: (document.getElementById('cfg_interface').value || '').trim() || 'wlan0',
            host: (document.getElementById('cfg_host').value || '').trim() || '0.0.0.0',
            port: parseInt(document.getElementById('cfg_port').value) || 8080,
        },
        environment: {
            binaries: linesToArray('cfg_binaries'),
            libraries: linesToArray('cfg_libraries'),
            python_path: (document.getElementById('cfg_python_path').value || '').trim(),
            lib_paths: linesToArray('cfg_lib_paths'),
        },
        permissions: {
            check_method: document.getElementById('cfg_check_method').value,
            strict_mode: document.getElementById('cfg_strict_mode').checked,
        },
        modules: {
            root_required_commands: linesToArray('cfg_root_cmds'),
        },
        server: {
            max_clients: parseInt(document.getElementById('cfg_max_clients').value) || 1,
            ws_ping_interval: parseInt(document.getElementById('cfg_ping_interval').value) || 20,
            ws_ping_timeout: parseInt(document.getElementById('cfg_ping_timeout').value) || 60,
        },
    };

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newCfg),
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast('✅ ' + (data.message || 'Đã lưu config!'), 'success', 4000);

            if (data.is_root !== undefined) {
                window.APP_CONFIG.isRoot = data.is_root;
                window.APP_CONFIG.rootMethod = data.root_method;
                updateRootBanner(data.is_root, data.root_method);
            }

            await loadUIModules();
            await loadConfig();

            if (data.needs_restart) {
                document.getElementById('configRestartNotice').style.display = 'block';
                if (confirm('⚠️ Một số thay đổi cần KHỞI ĐỘNG LẠI tool để áp dụng.\n\nKhởi động lại ngay bây giờ?')) {
                    hideConfigModal();
                    if (wsClient && wsClient.isReady) {
                        wsClient.send('restart_tool');
                    } else {
                        showToast('⚠️ Mất WS, vui lòng restart tool thủ công từ Termux', 'warning', 8000);
                    }
                }
            } else {
                hideConfigModal();
            }
        } else {
            showToast('❌ ' + (data.message || 'Lỗi lưu config'), 'error', 6000);
        }
    } catch (e) {
        showToast('❌ Lỗi: ' + e.message, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Lưu cấu hình';
    }
}

// ============== KHỞI TẠO ==============
document.addEventListener('DOMContentLoaded', () => {
    wsClient = new WebSocketClient();
    window.wsClient = wsClient;
    wsClient.connect();

    document.getElementById('scanBtn').onclick = scanNetworks;
    document.getElementById('connectBtn').onclick = connectWithPassword;
    document.getElementById('wpsBtn').onclick = wpsAttack;
    document.getElementById('autoConnectBtn').onclick = autoConnect;
    document.getElementById('clearCardBtn').onclick = clearCard;
    document.getElementById('quitBtn').onclick = quit;
    document.getElementById('shutdownBtn').onclick = shutdownTool;
    document.getElementById('togglePasswordBtn').onclick = togglePasswordVisibility;

    const logBtn = document.getElementById('logBtn');
    if (logBtn) logBtn.onclick = openLogModal;
    const logCloseBtn = document.getElementById('logCloseBtn');
    if (logCloseBtn) logCloseBtn.onclick = closeLogModal;
    const logCloseBtn2 = document.getElementById('logCloseBtn2');
    if (logCloseBtn2) logCloseBtn2.onclick = closeLogModal;
    const logClearBtn = document.getElementById('logClearBtn');
    if (logClearBtn) logClearBtn.onclick = () => { logHistory = []; renderLogModal(); };

    const configBtn = document.getElementById('configBtn');
    if (configBtn) configBtn.onclick = showConfigModal;
    const configCloseBtn = document.getElementById('configCloseBtn');
    if (configCloseBtn) configCloseBtn.onclick = hideConfigModal;
    const configCancelBtn = document.getElementById('configCancelBtn');
    if (configCancelBtn) configCancelBtn.onclick = hideConfigModal;
    const configSaveBtn = document.getElementById('configSaveBtn');
    if (configSaveBtn) configSaveBtn.onclick = saveConfigFromModal;

    loadUIModules();

    const closeResultBtn = document.getElementById('closeResultBtn');
    if (closeResultBtn) {
        closeResultBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            clearMainResult();
        };
    }

    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const modalCancelBtn = document.getElementById('modalCancelBtn');
    if (modalCloseBtn) modalCloseBtn.onclick = () => { const m = document.getElementById('moduleInputModal'); if (m) m.style.display = 'none'; };
    if (modalCancelBtn) modalCancelBtn.onclick = () => { const m = document.getElementById('moduleInputModal'); if (m) m.style.display = 'none'; };

    const passwordInput = document.getElementById('passwordInput');
    if (passwordInput) {
        passwordInput.addEventListener('input', function () {
            if (wsClient && wsClient.isFakePasswordActive && this.value !== wsClient.currentFakePasswordValue) {
                wsClient.markAsRealPassword();
                const savedHint = document.getElementById('savedHint');
                if (window.selectedNetwork) {
                    savedHint.innerHTML = `🔐 Sẽ thử với mật khẩu bạn nhập cho <strong>${window.selectedNetwork.ssid}</strong>`;
                    savedHint.style.color = '#28a745';
                }
            }
        });
        passwordInput.addEventListener('focus', function () {
            if (wsClient && wsClient.isFakePasswordActive && this.value === wsClient.currentFakePasswordValue) this.select();
            setTimeout(() => {
                const group = document.getElementById('connectGroup');
                if (group) group.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        });
        passwordInput.addEventListener('blur', function () {
            if (window.selectedNetwork && window.selectedNetwork.has_password && this.value.trim() === '') {
                const fakePassword = generateFakePassword(12);
                this.value = fakePassword;
                wsClient.markAsFakePassword(fakePassword);
                const savedHint = document.getElementById('savedHint');
                savedHint.innerHTML = '🔒 Mạng này đã có mật khẩu được lưu.';
                savedHint.style.color = '#ffc107';
            }
        });
        passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && wsClient && !wsClient.isProcessing && wsClient.isReady && selectedNetwork) {
                passwordInput.blur();
                connectWithPassword();
            }
        });
    }

    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', () => {
            const active = document.activeElement;
            if (active && active.id === 'passwordInput') {
                const group = document.getElementById('connectGroup');
                if (group) group.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    const setupStopButton = () => {
        const stopBtn = document.getElementById('stopBtn');
        if (stopBtn) {
            const newStopBtn = stopBtn.cloneNode(true);
            stopBtn.parentNode.replaceChild(newStopBtn, stopBtn);
            newStopBtn.onclick = stopAllTasks;
        }
    };
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                const container = document.getElementById('stopButtonContainer');
                if (container && container.style.display === 'block') setupStopButton();
            }
        });
    });
    const stopContainer = document.getElementById('stopButtonContainer');
    if (stopContainer) observer.observe(stopContainer, { attributes: true });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && wsClient && wsClient.isProcessing && wsClient.isReady) stopAllTasks();
    });
});

// ============== VERSION + BEFOREUNLOAD ==============
let moduleVersions = [];

async function loadModuleVersions() {
    try {
        const res = await fetch('/api/versions', { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();
        moduleVersions = data.modules || [];
    } catch (e) {}
}

window.addEventListener('beforeunload', (e) => {
    if (wsClient && (wsClient.isProcessing || wsClient.localProcessing)) {
        const msg = '⚠ Có task đang chạy!\n\nNếu rời trang:\n- Server sẽ KILL process\n- Module có thể bị block\n\nRời?';
        e.preventDefault();
        e.returnValue = msg;
        return msg;
    }
});

const _origLoadUIModules = loadUIModules;
loadUIModules = async function() {
    await _origLoadUIModules();
    loadModuleVersions();
};

// ⭐ v2: export thêm cổng cho dropzone JS trong module panel gọi
window.sendCommand = function(command, params) {
    if (!wsClient) {
        showToast('⚠ WS chưa sẵn sàng', 'warning', 3000);
        return false;
    }
    try {
        wsClient.send(command, params || {});
        return true;
    } catch (e) {
        showToast('❌ ' + e.message, 'error', 4000);
        return false;
    }
};

// Fallback window.ws — nhận JSON string (tương thích dropzone JS)
window.ws = {
    send: function(jsonStr) {
        try {
            const msg = typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr;
            if (msg && msg.command) {
                return window.sendCommand(msg.command, msg.params || {});
            }
        } catch (e) {
            console.warn('[window.ws.send] parse fail:', e);
        }
        return false;
    }
};

// Export
window.selectNetwork = selectNetwork;
window.scanNetworks = scanNetworks;
window.autoConnect = autoConnect;
window.copyToClipboard = copyToClipboard;
window.showLanDetailModal = showLanDetailModal;
window.closeLanDetailModal = closeLanDetailModal;
window.stopAllTasks = stopAllTasks;
window.quickDirb = quickDirb;
window.togglePasswordVisibility = togglePasswordVisibility;
window.showBlockedResult = showBlockedResult;
window.askModalInput = askModalInput;
window.showProgress = showProgress;
window.startProgress = startProgress;
window.stopProgress = stopProgress;
window.setMainResult = setMainResult;
window.renderModulePanel = renderModulePanel;
window.clearMainResult = clearMainResult;
window.showToast = showToast;
window.openLogModal = openLogModal;
window.showConfigModal = showConfigModal;
window.updateRootBanner = updateRootBanner;
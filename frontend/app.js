// ========================================
// Keitaro Campaign Manager — Frontend App
// ========================================

const API = '/api/campaigns';

// State
let campaigns = [];
let offers = [];
let domains = [];
let groups = [];
let sources = [];
let currentCampaignId = null;
let deleteTarget = { type: null, id: null, offerId: null };

// DOM Elements
const els = {
    // Header
    statusIndicator: document.getElementById('statusIndicator'),
    statusText: document.getElementById('statusText'),

    // Create form
    createForm: document.getElementById('createForm'),
    createBtn: document.getElementById('createBtn'),
    offerSelect: document.getElementById('offerSelect'),
    domainSelect: document.getElementById('domainSelect'),
    groupSelect: document.getElementById('groupSelect'),
    sourceSelect: document.getElementById('sourceSelect'),

    // List
    campaignsBody: document.getElementById('campaignsBody'),
    emptyState: document.getElementById('emptyState'),
    campaignsCount: document.getElementById('campaignsCount'),
    refreshBtn: document.getElementById('refreshBtn'),

    // Detail modal
    detailModal: document.getElementById('detailModal'),
    modalTitle: document.getElementById('modalTitle'),
    modalSubtitle: document.getElementById('modalSubtitle'),
    modalBody: document.getElementById('modalBody'),
    closeModal: document.getElementById('closeModal'),

    // Add offer modal
    addOfferModal: document.getElementById('addOfferModal'),
    addOfferForm: document.getElementById('addOfferForm'),
    addOfferSelect: document.getElementById('addOfferSelect'),
    closeAddOfferModal: document.getElementById('closeAddOfferModal'),
    cancelAddOffer: document.getElementById('cancelAddOffer'),

    // Confirm modal
    confirmModal: document.getElementById('confirmModal'),
    confirmText: document.getElementById('confirmText'),
    closeConfirmModal: document.getElementById('closeConfirmModal'),
    cancelConfirm: document.getElementById('cancelConfirm'),
    confirmDelete: document.getElementById('confirmDelete'),

    // Toast
    toastContainer: document.getElementById('toastContainer'),

    // Alert banner
    alertBanner: document.getElementById('alertBanner'),
};

// ========================================
// Init
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
    await checkHealth();
    await loadResources();
    await loadCampaigns();
    bindEvents();
});

// ========================================
// Health Check
// ========================================

async function checkHealth() {
    try {
        const r = await fetch('/health');
        if (r.ok) {
            setStatus('connected', 'Подключено');
        } else { throw new Error('unhealthy'); }
    } catch {
        setStatus('error', 'Нет связи с API');
        showAlert('Не удаётся подключиться к серверу. Проверьте, запущен ли бэкенд.', 'danger');
    }
}

function setStatus(state, text) {
    els.statusIndicator.className = 'status-indicator';
    if (state === 'connected') els.statusIndicator.classList.add('status-indicator--connected');
    else if (state === 'error') els.statusIndicator.classList.add('status-indicator--error');
    els.statusText.textContent = text;
}

// ========================================
// Resources (dropdowns)
// ========================================

async function loadResources() {
    try {
        const [o, d, g, s] = await Promise.all([
            fetch(`${API}/resources/offers`).then(r => r.json()),
            fetch(`${API}/resources/domains`).then(r => r.json()),
            fetch(`${API}/resources/groups`).then(r => r.json()),
            fetch(`${API}/resources/traffic-sources`).then(r => r.json()),
        ]);
        offers = o; domains = d; groups = g; sources = s;
        fillSelects();
    } catch (e) {
        console.error('Load resources error:', e);
        showAlert('Не удалось загрузить справочники из Keitaro. Проверьте API ключ.', 'danger');
    }
}

function fillSelects() {
    // Offers (create form)
    fillSelect(els.offerSelect, offers, 'Выберите оффер', true);
    // Offers (add offer modal)
    fillSelect(els.addOfferSelect, offers, 'Выберите оффер', true);
    // Domains
    fillSelect(els.domainSelect, domains, 'Авто (первый доступный)', false, d => d.name);
    // Groups
    fillSelect(els.groupSelect, groups, 'Авто (первая доступная)', false, g => g.name);
    // Sources
    fillSelect(els.sourceSelect, sources, 'Авто (первый доступный)', false, s => s.name);
}

function fillSelect(selectEl, items, placeholder, required, labelFn = i => `${i.name} (ID: ${i.id})`) {
    selectEl.innerHTML = '';
    if (!required) {
        const opt = document.createElement('option');
        opt.value = ''; opt.textContent = placeholder;
        selectEl.appendChild(opt);
    } else {
        const opt = document.createElement('option');
        opt.value = ''; opt.textContent = placeholder; opt.disabled = true; opt.selected = true;
        selectEl.appendChild(opt);
    }
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.id;
        opt.textContent = labelFn(item);
        selectEl.appendChild(opt);
    });
}

// ========================================
// Campaigns List
// ========================================

async function loadCampaigns() {
    renderLoading();
    try {
        const r = await fetch(API);
        campaigns = await r.json();
        renderCampaigns();
    } catch (e) {
        console.error('Load campaigns error:', e);
        renderError();
        showToast('Не удалось загрузить кампании', 'danger');
    }
}

function renderLoading() {
    els.campaignsBody.innerHTML = `
        <tr class="table-loading">
            <td colspan="9">
                <div class="loading-state">
                    <svg class="loading-spinner" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>
                    <span>Загрузка кампаний…</span>
                </div>
            </td>
        </tr>
    `;
}

function renderError() {
    els.campaignsBody.innerHTML = `
        <tr class="table-loading">
            <td colspan="9">
                <div class="loading-state" style="color: var(--color-danger-600);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                    <span>Ошибка загрузки. <button class="btn btn--ghost" onclick="loadCampaigns()" style="padding:0;font-size:inherit;text-decoration:underline;">Повторить</button></span>
                </div>
            </td>
        </tr>
    `;
}

function renderCampaigns() {
    if (!campaigns.length) {
        els.campaignsBody.innerHTML = '';
        els.emptyState.hidden = false;
        els.campaignsCount.textContent = 'Кампаний: 0';
        return;
    }
    els.emptyState.hidden = true;
    els.campaignsCount.textContent = `Кампаний: ${campaigns.length}`;

    els.campaignsBody.innerHTML = campaigns.map(c => `
        <tr data-id="${c.id}">
            <td>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span class="mono" style="font-weight:600;">${esc(c.name)}</span>
                    <span class="badge badge--info" style="font-size:10px;padding:2px 6px;">#${c.id}</span>
                </div>
            </td>
            <td><span class="badge badge--success">${esc(c.geo_code)}</span></td>
            <td><span class="mono">#${c.offer_id}</span></td>
            <td><span class="mono">${c.domain_id ? '#'+c.domain_id : '<span style="color:var(--color-text-muted)">—</span>'}</span></td>
            <td><span class="mono">${c.group_id ? '#'+c.group_id : '<span style="color:var(--color-text-muted)">—</span>'}</span></td>
            <td><span class="mono">${c.traffic_source_id ? '#'+c.traffic_source_id : '<span style="color:var(--color-text-muted)">—</span>'}</span></td>
            <td>
                <div style="display:flex;gap:6px;align-items:center;">
                    <span class="badge ${c.stream_1_id ? 'badge--success' : 'badge--danger'}" style="font-size:10px;">${c.stream_1_id ? '✓ Google' : '✗ Google'}</span>
                    <span class="badge ${c.stream_2_id ? 'badge--success' : 'badge--danger'}" style="font-size:10px;">${c.stream_2_id ? '✓ Offer' : '✗ Offer'}</span>
                </div>
            </td>
            <td class="mono">${fmtDate(c.created_at)}</td>
            <td>
                <div class="actions">
                    <button class="btn btn--ghost" data-view="${c.id}" aria-label="Открыть кампанию ${esc(c.name)}" title="Открыть">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                    <button class="btn btn--ghost" data-delete="${c.id}" aria-label="Удалить кампанию ${esc(c.name)}" title="Удалить" style="color:var(--color-danger-600);">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function fmtDate(s) {
    if (!s) return '—';
    try { return new Date(s).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }); } catch { return s; }
}

const ESC_MAP = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ESC_MAP[c]); }

// ========================================
// Create Campaign
// ========================================

els.createForm.addEventListener('submit', async e => {
    e.preventDefault();
    const fd = new FormData(els.createForm);
    const data = {
        name: fd.get('name').trim(),
        geo_code: fd.get('geo_code').trim().toUpperCase(),
        offer_id: +fd.get('offer_id'),
        domain_id: fd.get('domain_id') ? +fd.get('domain_id') : undefined,
        group_id: fd.get('group_id') ? +fd.get('group_id') : undefined,
        traffic_source_id: fd.get('traffic_source_id') ? +fd.get('traffic_source_id') : undefined
    };
    if (!data.name || !data.geo_code || !data.offer_id) return showToast('Заполните обязательные поля', 'danger');

    setLoading(els.createBtn, true);
    try {
        const r = await fetch(API, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) });
        if (!r.ok) throw new Error((await r.json()).detail || 'Ошибка создания');
        showToast('Кампания успешно создана', 'success');
        els.createForm.reset();
        await loadCampaigns();
    } catch (e) { showToast(e.message, 'danger'); }
    finally { setLoading(els.createBtn, false); }
});

// ========================================
// View Campaign Detail
// ========================================

async function openDetail(id) {
    currentCampaignId = id;
    const c = campaigns.find(x => x.id === id);
    if (!c) return;

    els.modalTitle.textContent = c.name;
    els.modalSubtitle.textContent = `Keitaro ID: ${c.keitaro_campaign_id} • Гео: ${c.geo_code}`;
    els.detailModal.showModal();
    renderDetailLoading();

    try {
        const r = await fetch(`${API}/${id}`);
        const d = await r.json();
        renderDetail(d);
    } catch (e) {
        els.modalBody.innerHTML = `
            <div class="loading-state" style="color:var(--color-danger-600);text-align:center;padding:var(--space-8);">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                <p style="margin-top:12px;">Ошибка загрузки: ${esc(e.message)}</p>
                <button class="btn btn--primary" onclick="openDetail(${id})" style="margin-top:16px;">Повторить</button>
            </div>
        `;
    }
}

function renderDetailLoading() {
    els.modalBody.innerHTML = `
        <div class="loading-state loading-state--inline" style="justify-content:center;">
            <svg class="loading-spinner" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>
            <span>Загрузка деталей…</span>
        </div>
    `;
}

function renderDetail(c) {
    const offersHtml = (c.offers?.length || 0) > 0
        ? c.offers.map(o => `
            <div class="offer-row">
                <div class="offer-info">
                    <div class="offer-name">${esc(o.offer_name || 'Оффер #' + o.keitaro_offer_id)}</div>
                    <div class="offer-meta">ID: ${o.keitaro_offer_id} ${o.stream_id ? '• Stream: ' + o.stream_id : ''}</div>
                </div>
                <button class="btn btn--ghost" data-del-offer="${o.keitaro_offer_id}" aria-label="Удалить оффер ${esc(o.offer_name || o.keitaro_offer_id)}" title="Удалить оффер" style="color:var(--color-danger-600);">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                </button>
            </div>
        `).join('')
        : `
            <div style="padding:var(--space-8);text-align:center;color:var(--color-text-muted);">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin:0 auto var(--space-3);opacity:0.5;"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6M9 13h4"/></svg>
                <p>Дополнительных офферов нет</p>
            </div>
        `;

    els.modalBody.innerHTML = `
        <details class="detail-section" open>
            <summary>Информация о кампании</summary>
            <div class="detail-grid">
                <div class="detail-item"><label>Local ID</label><span>${c.id}</span></div>
                <div class="detail-item"><label>Keitaro Campaign ID</label><span>${c.keitaro_campaign_id}</span></div>
                <div class="detail-item"><label>Название</label><span>${esc(c.name)}</span></div>
                <div class="detail-item"><label>Alias</label><span>${esc(c.alias)}</span></div>
                <div class="detail-item"><label>Гео</label><span>${esc(c.geo_code)}</span></div>
                <div class="detail-item"><label>Основной оффер</label><span>#${c.offer_id}</span></div>
                <div class="detail-item"><label>Домен</label><span>${c.domain_id ? '#'+c.domain_id : 'Авто'}</span></div>
                <div class="detail-item"><label>Группа</label><span>${c.group_id ? '#'+c.group_id : 'Авто'}</span></div>
                <div class="detail-item"><label>Источник трафика</label><span>${c.traffic_source_id ? '#'+c.traffic_source_id : 'Авто'}</span></div>
                <div class="detail-item"><label>Стрим 1 (Google)</label><span>${c.stream_1_id ? '#'+c.stream_1_id : 'Не создан'}</span></div>
                <div class="detail-item"><label>Стрим 2 (Offer)</label><span>${c.stream_2_id ? '#'+c.stream_2_id : 'Не создан'}</span></div>
                <div class="detail-item"><label>Создана</label><span>${fmtDate(c.created_at)}</span></div>
                <div class="detail-item"><label>Обновлена</label><span>${c.updated_at ? fmtDate(c.updated_at) : 'Никогда'}</span></div>
            </div>
        </details>

        <details class="detail-section" open>
            <summary>Офферы в кампании <span style="font-weight:400;color:var(--color-text-muted);font-size:var(--text-xs);">(${c.offers?.length || 0})</span></summary>
            <div class="offers-list">${offersHtml}</div>
            <div style="padding:var(--space-4);border-top:1px solid var(--color-border);display:flex;justify-content:flex-end;">
                <button class="btn btn--secondary" id="addOfferBtn" style="font-size:var(--text-sm);">
                    <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                    Добавить оффер
                </button>
            </div>
        </details>
    `;

    // Bind buttons
    els.modalBody.querySelectorAll('[data-del-offer]').forEach(b => b.onclick = () => confirmRemoveOffer(currentCampaignId, +b.dataset.delOffer));
    els.modalBody.querySelector('#addOfferBtn')?.addEventListener('click', () => openAddOfferModal(currentCampaignId));
}

// ========================================
// Delete Campaign
// ========================================

async function deleteCampaign(id) {
    const c = campaigns.find(x => x.id === id);
    if (!c) return;
    openConfirm(
        `Удалить кампанию <strong>${esc(c.name)}</strong>?`,
        'Это действие удалит кампанию и из Keitaro, и из локальной базы. Потоки и статистика в Keitaro будут потеряны.',
        async () => {
            try {
                const r = await fetch(`${API}/${id}`, { method: 'DELETE' });
                if (!r.ok) throw new Error((await r.json()).detail || 'Ошибка удаления');
                showToast('Кампания удалена', 'success');
                await loadCampaigns();
            } catch (e) { showToast(e.message, 'danger'); }
        }
    );
}

// ========================================
// Remove Offer from Campaign
// ========================================

function confirmRemoveOffer(campaignId, offerId) {
    const c = campaigns.find(x => x.id === campaignId);
    const offer = c?.offers?.find(o => o.keitaro_offer_id === offerId);
    const name = offer?.offer_name || `#${offerId}`;
    openConfirm(
        `Удалить оффер <strong>${esc(name)}</strong> из кампании?`,
        'Оффер будет удалён из второго потока в Keitaro. Основной оффер (из формы создания) нельзя удалить — только дополнительные.',
        async () => {
            try {
                const r = await fetch(`${API}/${campaignId}/offers/${offerId}`, { method: 'DELETE' });
                if (!r.ok) throw new Error((await r.json()).detail || 'Ошибка удаления');
                showToast('Оффер удалён', 'success');
                await openDetail(campaignId);
                await loadCampaigns();
            } catch (e) { showToast(e.message, 'danger'); }
        }
    );
}

// ========================================
// Add Offer Modal
// ========================================

function openAddOfferModal(campaignId) {
    currentCampaignId = campaignId;
    els.addOfferForm.reset();
    els.addOfferModal.showModal();
}

els.addOfferForm.addEventListener('submit', async e => {
    e.preventDefault();
    const fd = new FormData(els.addOfferForm);
    const offerId = +fd.get('offer_id');
    if (!offerId) return showToast('Выберите оффер', 'danger');

    const btn = els.addOfferForm.querySelector('button[type="submit"]');
    setLoading(btn, true);
    try {
        const r = await fetch(`${API}/${currentCampaignId}/offers`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ keitaro_offer_id: offerId }) });
        if (!r.ok) throw new Error((await r.json()).detail || 'Ошибка добавления');
        showToast('Оффер добавлен в кампанию', 'success');
        els.addOfferModal.close();
        await openDetail(currentCampaignId);
        await loadCampaigns();
    } catch (e) { showToast(e.message, 'danger'); }
    finally { setLoading(btn, false); }
});

// ========================================
// Confirm Modal
// ========================================

function openConfirm(title, text, onConfirm) {
    deleteTarget.onConfirm = onConfirm;
    els.confirmText.innerHTML = text;
    els.confirmModal.querySelector('.modal-title').textContent = title;
    els.confirmModal.showModal();
}

els.confirmDelete.addEventListener('click', () => {
    if (deleteTarget.onConfirm) {
        deleteTarget.onConfirm();
        deleteTarget.onConfirm = null;
    }
    els.confirmModal.close();
});

// ========================================
// Utils
// ========================================

function setLoading(btn, on) {
    if (!btn) return;
    btn.disabled = on;
    const text = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    if (text) text.style.display = on ? 'none' : 'inline';
    if (loader) loader.style.display = on ? 'flex' : 'none';
}

function showToast(message, type = 'info', title = '') {
    const icons = {
        success: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        danger: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    };

    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    el.innerHTML = `
        ${icons[type] || icons.info}
        <div class="toast-content">
            ${title ? `<div class="toast-title">${esc(title)}</div>` : ''}
            <div class="toast-message">${esc(message)}</div>
        </div>
        <button class="toast-close" aria-label="Закрыть"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        <div class="toast-progress"></div>
    `;
    el.querySelector('.toast-close').onclick = () => removeToast(el);
    els.toastContainer.appendChild(el);
    setTimeout(() => removeToast(el), 4500);
}

function removeToast(el) {
    el.style.animation = 'slideIn 0.2s ease-in reverse';
    setTimeout(() => el.remove(), 200);
}

function showAlert(message, type = 'info') {
    const icons = {
        success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        danger: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    };
    els.alertBanner.className = `alert-banner alert-banner--${type}`;
    els.alertBanner.innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;flex:1;">
            ${icons[type] || icons.info}
            <span>${esc(message)}</span>
        </div>
        <button class="alert-banner__close" aria-label="Закрыть"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    `;
    els.alertBanner.querySelector('.alert-banner__close').onclick = () => { els.alertBanner.hidden = true; };
    els.alertBanner.hidden = false;
}

// ========================================
// Event Binding
// ========================================

function bindEvents() {
    // Modal close handlers
    [els.closeModal, els.closeAddOfferModal, els.cancelAddOffer].forEach(b => b?.addEventListener('click', () => {
        els.detailModal.close();
        els.addOfferModal.close();
    }));

    [els.detailModal, els.addOfferModal, els.confirmModal].forEach(m => {
        m.addEventListener('click', e => { if (e.target === m) m.close(); });
    });

    // Confirm modal
    [els.closeConfirmModal, els.cancelConfirm].forEach(b => b?.addEventListener('click', () => els.confirmModal.close()));
    els.confirmDelete.addEventListener('click', () => {
        if (deleteTarget.onConfirm) {
            deleteTarget.onConfirm();
            deleteTarget.onConfirm = null;
        }
        els.confirmModal.close();
    });

    // Delegated events for table
    els.campaignsBody.addEventListener('click', e => {
        const viewBtn = e.target.closest('[data-view]');
        const delBtn = e.target.closest('[data-delete]');
        if (viewBtn) openDetail(+viewBtn.dataset.view);
        if (delBtn) deleteCampaign(+delBtn.dataset.delete);
    });

    els.refreshBtn.addEventListener('click', loadCampaigns);

    // Keyboard
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            els.detailModal.close();
            els.addOfferModal.close();
            els.confirmModal.close();
        }
    });
}

// Expose for inline onclick
window.loadCampaigns = loadCampaigns;
window.openDetail = openDetail;
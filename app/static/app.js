// ==============================================================================
// Logic & State Management - OKX Singapore API Access Test
// ==============================================================================

const state = {
    stepAPassed: false,
    stepBPassed: false,
    marketData: null,
    pendingAction: null,
    isSubmitting: false,
    lastOrderId: null
};

// DOM Elements
const el = {
    serverIpVal: document.getElementById('val-server-ip'),
    btnRefreshIp: document.getElementById('btn-refresh-ip'),
    credentialsVal: document.getElementById('val-credentials'),
    credentialsBadge: document.getElementById('badge-credentials'),

    // Step A
    cardA: document.getElementById('step-card-a'),
    btnStepA: document.getElementById('btn-run-step-a'),
    spinA: document.getElementById('spin-a'),
    statusA: document.getElementById('status-chip-a'),

    // Step B
    cardB: document.getElementById('step-card-b'),
    btnStepB: document.getElementById('btn-run-step-b'),
    spinB: document.getElementById('spin-b'),
    statusB: document.getElementById('status-chip-b'),

    // Step C
    cardC: document.getElementById('step-card-c'),
    tickerLastPx: document.getElementById('ticker-last-px'),
    btnTradeLong: document.getElementById('btn-trade-long'),
    btnTradeShort: document.getElementById('btn-trade-short'),

    // Report
    pillNet: document.getElementById('pill-net'),
    valPillNet: document.getElementById('val-pill-net'),
    pillAuth: document.getElementById('pill-auth'),
    valPillAuth: document.getElementById('val-pill-auth'),
    pillOrder: document.getElementById('pill-order'),
    valPillOrder: document.getElementById('val-pill-order'),
    pillFill: document.getElementById('pill-fill'),
    valPillFill: document.getElementById('val-pill-fill'),
    resultPlaceholder: document.getElementById('result-placeholder'),
    resultDetails: document.getElementById('result-details'),

    // Modal
    orderModal: document.getElementById('order-modal'),
    modalActionName: document.getElementById('modal-action-name'),
    modalPrice: document.getElementById('modal-price'),
    btnCancelModal: document.getElementById('btn-cancel-modal'),
    btnConfirmModal: document.getElementById('btn-confirm-modal')
};

// ==============================================================================
// Initialisation
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
});

async function initApp() {
    await fetchCredentialsStatus();
    await fetchServerIp();
    await fetchMarketPreview();
}

function setupEventListeners() {
    el.btnRefreshIp.addEventListener('click', fetchServerIp);
    el.btnStepA.addEventListener('click', runStepA);
    el.btnStepB.addEventListener('click', runStepB);

    // Boutons de trading manuels (Step C)
    el.btnTradeLong.addEventListener('click', () => openConfirmModal('BUY_LONG'));
    el.btnTradeShort.addEventListener('click', () => openConfirmModal('SELL_SHORT'));

    // Modal
    el.btnCancelModal.addEventListener('click', closeConfirmModal);
    el.btnConfirmModal.addEventListener('click', executeOrder);

    // Fermeture du modal sur clic overlay
    el.orderModal.addEventListener('click', (e) => {
        if (e.target === el.orderModal) closeConfirmModal();
    });
}

// ==============================================================================
// 1. Diagnostics (IP & Clés)
// ==============================================================================
async function fetchCredentialsStatus() {
    try {
        const res = await fetch('/api/config-status');
        const data = await res.json();
        if (data.configured) {
            el.credentialsVal.textContent = `Clé : ${data.api_key_masked} | Passphrase OK`;
            el.credentialsBadge.textContent = 'Configuré (Démo)';
            el.credentialsBadge.className = 'badge badge-configured';
        } else {
            el.credentialsVal.textContent = 'Variables manquantes dans le .env';
            el.credentialsBadge.textContent = 'Non configuré';
            el.credentialsBadge.className = 'badge badge-missing';
        }
    } catch (err) {
        el.credentialsVal.textContent = 'Erreur lors du contrôle des clés';
    }
}

async function fetchServerIp() {
    el.serverIpVal.textContent = 'Détection en cours...';
    try {
        const res = await fetch('/api/server-ip');
        const data = await res.json();
        if (data.success) {
            el.serverIpVal.textContent = `${data.ip} (${data.duration_ms} ms)`;
        } else {
            el.serverIpVal.textContent = `Échec de détection : ${data.error}`;
        }
    } catch (err) {
        el.serverIpVal.textContent = 'Erreur réseau';
    }
}

async function fetchMarketPreview() {
    try {
        const res = await fetch('/api/market/preview');
        const data = await res.json();
        if (data.success) {
            state.marketData = data;
            const px = parseFloat(data.last_px || 0).toLocaleString('fr-FR', { minimumFractionDigits: 1 });
            el.tickerLastPx.textContent = `${px} USDT`;
        }
    } catch (err) {
        console.warn('Impossible de rafraîchir le ticker', err);
    }
}

// ==============================================================================
// 2. Étape A : Connectivité Réseau
// ==============================================================================
async function runStepA() {
    setLoading(el.btnStepA, el.spinA, true);
    el.statusA.textContent = 'Test en cours...';
    el.statusA.className = 'step-status-chip';

    try {
        const res = await fetch('/api/step-a/connectivity');
        const data = await res.json();
        setLoading(el.btnStepA, el.spinA, false);

        displayResult('Étape A — Connectivité Réseau Publique', data);

        if (data.success) {
            state.stepAPassed = true;
            el.statusA.textContent = `Succès (HTTP ${data.http_status} - ${data.duration_ms} ms)`;
            el.statusA.className = 'step-status-chip status-chip-success';
            el.cardA.classList.add('step-success');

            // Mise à jour de la pilule 1
            el.valPillNet.textContent = `OK (${data.duration_ms} ms)`;
            el.pillNet.className = 'pill pill-ok';

            // Débloquer l'étape B
            unlockStepB();
        } else {
            state.stepAPassed = false;
            el.statusA.textContent = `Échec : ${data.okx_msg}`;
            el.statusA.className = 'step-status-chip status-chip-error';

            el.valPillNet.textContent = `ERREUR (${data.okx_code})`;
            el.pillNet.className = 'pill pill-err';
        }
    } catch (err) {
        setLoading(el.btnStepA, el.spinA, false);
        el.statusA.textContent = `Erreur réseau : ${err.message}`;
        el.statusA.className = 'step-status-chip status-chip-error';
    }
}

function unlockStepB() {
    el.cardB.classList.remove('step-locked');
    el.btnStepB.removeAttribute('disabled');
    el.statusB.textContent = 'Prêt pour validation';
    el.statusB.className = 'step-status-chip';
}

// ==============================================================================
// 3. Étape B : Authentification Démo
// ==============================================================================
async function runStepB() {
    if (!state.stepAPassed) return;

    setLoading(el.btnStepB, el.spinB, true);
    el.statusB.textContent = 'Validation en cours...';
    el.statusB.className = 'step-status-chip';

    try {
        const res = await fetch('/api/step-b/auth');
        const data = await res.json();
        setLoading(el.btnStepB, el.spinB, false);

        displayResult('Étape B — Authentification Démo Privée', data);

        if (data.success) {
            state.stepBPassed = true;
            el.statusB.textContent = `Succès (Mode: ${data.position_mode} | Solde Démo: ${data.demo_usdt_available} USDT)`;
            el.statusB.className = 'step-status-chip status-chip-success';
            el.cardB.classList.add('step-success');

            // Mise à jour de la pilule 2
            el.valPillAuth.textContent = `OK (Code 0 - ${data.duration_ms} ms)`;
            el.pillAuth.className = 'pill pill-ok';

            // Débloquer l'étape C (boutons de trading)
            unlockStepC();
        } else {
            state.stepBPassed = false;
            el.statusB.textContent = `Échec Auth : ${data.okx_msg} (Code: ${data.okx_code})`;
            el.statusB.className = 'step-status-chip status-chip-error';

            el.valPillAuth.textContent = `REJET (${data.okx_code})`;
            el.pillAuth.className = 'pill pill-err';
        }
    } catch (err) {
        setLoading(el.btnStepB, el.spinB, false);
        el.statusB.textContent = `Erreur : ${err.message}`;
        el.statusB.className = 'step-status-chip status-chip-error';
    }
}

function unlockStepC() {
    el.cardC.classList.remove('step-locked');
    el.btnTradeLong.removeAttribute('disabled');
    el.btnTradeShort.removeAttribute('disabled');
}

// ==============================================================================
// 4. Étape C : Modal de confirmation & Placement d'ordre Futures Démo
// ==============================================================================
async function openConfirmModal(action) {
    if (!state.stepBPassed || state.isSubmitting) return;

    state.pendingAction = action;
    await fetchMarketPreview();

    const isLong = action === 'BUY_LONG';
    el.modalActionName.textContent = isLong ? 'ACHETER (LONG)' : 'VENDRE (SHORT)';
    el.modalActionName.className = `highlight-action ${isLong ? 'long' : 'short'}`;

    if (state.marketData && state.marketData.last_px) {
        const lastPx = parseFloat(state.marketData.last_px);
        // Long: ordre limite légèrement en dessous (ex: -0.5%) | Short: légèrement au dessus (+0.5%)
        const estPx = isLong ? (lastPx * 0.995).toFixed(1) : (lastPx * 1.005).toFixed(1);
        el.modalPrice.textContent = `${parseFloat(estPx).toLocaleString('fr-FR')} USDT (Marché actuel : ${lastPx.toLocaleString('fr-FR')} USDT)`;
    } else {
        el.modalPrice.textContent = 'Calcul automatique basé sur le marché';
    }

    el.orderModal.classList.remove('hidden');
}

function closeConfirmModal() {
    el.orderModal.classList.add('hidden');
    state.pendingAction = null;
}

async function executeOrder() {
    if (!state.pendingAction || state.isSubmitting) return;

    const action = state.pendingAction;
    closeConfirmModal();

    // Bloquer les boutons pour éviter le double-clic
    setTradingButtonsState(true);

    try {
        const res = await fetch('/api/step-c/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, confirmed: true })
        });

        const data = await res.json();
        displayResult(`Étape C — Ordre Futures Démo [${action}]`, data);

        if (res.status === 200 && data.success) {
            state.lastOrderId = data.order_id;
            
            // Pilule 3 : Requête acceptée par OKX
            el.valPillOrder.textContent = `ACCEPTÉ (ordId: ${data.order_id})`;
            el.pillOrder.className = 'pill pill-ok';

            // Pilule 4 : Statut de l'ordre
            const orderState = data.order_status || 'live';
            el.valPillFill.textContent = `${orderState.toUpperCase()} (${data.duration_ms} ms)`;
            el.pillFill.className = 'pill pill-ok';
        } else {
            // Requête refusée par OKX
            el.valPillOrder.textContent = `REFUSÉ (Code: ${data.okx_code || res.status})`;
            el.pillOrder.className = 'pill pill-err';

            el.valPillFill.textContent = data.okx_sub_code ? `SubCode: ${data.okx_sub_code}` : 'NON PLACÉ';
            el.pillFill.className = 'pill pill-err';
        }
    } catch (err) {
        displayResult('Étape C — Exception Réseau', {
            success: false,
            http_status: 0,
            okx_code: 'CLIENT_ERROR',
            okx_msg: err.message
        });

        el.valPillOrder.textContent = 'ERREUR RÉSEAU';
        el.pillOrder.className = 'pill pill-err';
    } finally {
        setTradingButtonsState(false);
    }
}

function setTradingButtonsState(disabled) {
    state.isSubmitting = disabled;
    el.btnTradeLong.disabled = disabled;
    el.btnTradeShort.disabled = disabled;

    if (disabled) {
        el.btnTradeLong.style.opacity = '0.5';
        el.btnTradeShort.style.opacity = '0.5';
    } else {
        el.btnTradeLong.style.opacity = '1';
        el.btnTradeShort.style.opacity = '1';
    }
}

// ==============================================================================
// 5. Affichage Détaillé des Résultats
// ==============================================================================
function displayResult(title, data) {
    el.resultPlaceholder.classList.add('hidden');
    el.resultDetails.classList.remove('hidden');

    const isSuccess = data.success === true;
    const httpStatus = data.http_status !== undefined ? data.http_status : 'N/A';
    const okxCode = data.okx_code !== undefined ? data.okx_code : 'N/A';
    const duration = data.duration_ms !== undefined ? `${data.duration_ms} ms` : 'N/A';
    const msg = data.okx_msg || (isSuccess ? 'Opération réussie' : 'Erreur');
    const orderId = data.order_id || 'Aucun';
    const orderState = data.order_status || 'N/A';

    let orderParamsHtml = '';
    if (data.order_params) {
        const p = data.order_params;
        orderParamsHtml = `
            <div class="res-item">
                <span class="res-lbl">Paramètres Envoyés</span>
                <span class="res-val">${p.instId} | side: ${p.side} | posSide: ${p.posSide} | sz: ${p.sz} (${p.contract_value}) | px: ${p.px} | type: ${p.ordType}</span>
            </div>
        `;
    }

    let cancelBtnHtml = '';
    if (orderId && orderId !== 'Aucun') {
        cancelBtnHtml = `
            <button class="btn btn-secondary" style="font-size: 0.78rem; padding: 6px 12px; margin-top: 10px;" onclick="cancelTestOrder('${orderId}')">
                Annuler cet ordre de test (nettoyage)
            </button>
        `;
    }

    const blockHtml = `
        <div class="result-block">
            <div class="result-block-header">
                <span class="result-block-title">${title}</span>
                <span class="badge ${isSuccess ? 'badge-configured' : 'badge-missing'}">
                    ${isSuccess ? 'SUCCÈS' : 'ÉCHEC'}
                </span>
            </div>
            <div class="res-grid">
                <div class="res-item">
                    <span class="res-lbl">Code HTTP</span>
                    <span class="res-val ${httpStatus === 200 ? 'success' : 'error'}">${httpStatus}</span>
                </div>
                <div class="res-item">
                    <span class="res-lbl">Code OKX (code)</span>
                    <span class="res-val ${okxCode === '0' ? 'success' : 'error'}">${okxCode}</span>
                </div>
                <div class="res-item">
                    <span class="res-lbl">Durée de requête</span>
                    <span class="res-val">${duration}</span>
                </div>
                <div class="res-item">
                    <span class="res-lbl">Identifiant Ordre (ordId)</span>
                    <span class="res-val">${orderId}</span>
                </div>
                <div class="res-item">
                    <span class="res-lbl">Statut Moteur (state)</span>
                    <span class="res-val ${orderState === 'live' || orderState === 'filled' ? 'success' : ''}">${orderState}</span>
                </div>
                <div class="res-item">
                    <span class="res-lbl">Message OKX</span>
                    <span class="res-val">${msg}</span>
                </div>
                ${orderParamsHtml}
            </div>
            ${cancelBtnHtml}
            <details style="margin-top: 12px; cursor: pointer;">
                <summary style="font-size: 0.75rem; color: var(--text-muted);">Afficher la réponse JSON brute</summary>
                <pre class="json-box" style="margin-top: 8px;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>
            </details>
        </div>
    `;

    // Ajoute le nouveau résultat en haut de l'historique
    el.resultDetails.innerHTML = blockHtml + el.resultDetails.innerHTML;
}

window.cancelTestOrder = async function(orderId) {
    try {
        const res = await fetch(`/api/order/cancel?ordId=${orderId}`, { method: 'POST' });
        const data = await res.json();
        alert(`Ordre ${orderId} annulé : ${JSON.stringify(data)}`);
    } catch (e) {
        alert(`Erreur d'annulation : ${e.message}`);
    }
};

function setLoading(buttonEl, spinnerEl, isLoading) {
    if (isLoading) {
        spinnerEl.classList.remove('hidden');
        buttonEl.setAttribute('disabled', 'true');
    } else {
        spinnerEl.classList.add('hidden');
        buttonEl.removeAttribute('disabled');
    }
}

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

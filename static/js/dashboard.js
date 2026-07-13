// Dashboard JavaScript
// Handles live polling, charts, and real-time updates for simulated traffic

let trafficChart = null;
let sparklineChart = null;
let trafficVolumeData = [];
const MAX_DATA_POINTS = 12; // 60 seconds / 5-second intervals

function initDashboard(initialStats) {
    initTrafficChart(initialStats);
    initSparklineChart();
    updateBreakdown(initialStats);
    startPolling();
}

// ── Chart helpers ────────────────────────────────────────────

function clampCanvasSize(canvas, maxWidth, maxHeight) {
    canvas.width = Math.min(canvas.width || maxWidth, maxWidth);
    canvas.height = Math.min(canvas.height || maxHeight, maxHeight);
    canvas.style.maxWidth = maxWidth + 'px';
    canvas.style.maxHeight = maxHeight + 'px';
}

function initTrafficChart(stats) {
    const canvas = document.getElementById('trafficChart');
    if (!canvas) return;
    clampCanvasSize(canvas, 1200, 300);
    const ctx = canvas.getContext('2d');

    trafficChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Normal', 'DoS', 'Probing', 'R2L', 'U2R'],
            datasets: [{
                label: 'Connection Count',
                data: [stats.normal, stats.dos, stats.probing, stats.r2l, stats.u2r],
                backgroundColor: ['#28a745', '#dc3545', '#ffc107', '#fd7e14', '#6f42c1'],
                borderWidth: 0,
                borderRadius: 4,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.parsed.x.toLocaleString()} connections`
                    }
                }
            },
            scales: {
                x: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: { grid: { display: false } }
            }
        }
    });
}

function initSparklineChart() {
    const canvas = document.getElementById('sparklineChart');
    if (!canvas) return;
    clampCanvasSize(canvas, 1200, 130);
    const ctx = canvas.getContext('2d');

    for (let i = 0; i < MAX_DATA_POINTS; i++) trafficVolumeData.push(0);

    sparklineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: MAX_DATA_POINTS }, (_, i) => `-${(MAX_DATA_POINTS - i) * 5}s`),
            datasets: [{
                label: 'Packets / 5s',
                data: [...trafficVolumeData],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102,126,234,0.12)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#667eea',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } }
            },
            animation: { duration: 400 }
        }
    });
}

// ── Polling ───────────────────────────────────────────────────

let pollingInterval = null;
let lastTotal = 0;

function startPolling() {
    if (pollingInterval) return;
    pollingInterval = setInterval(updateStats, 5000);
}

function stopPolling() {
    if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; }
}

document.addEventListener('visibilitychange', () => {
    document.hidden ? stopPolling() : startPolling();
});
window.addEventListener('beforeunload', stopPolling);

async function updateStats() {
    try {
        const res = await fetch('/api/stats', {
            headers: { 'X-API-Key': 'dev-api-key-change-in-production' }
        });
        if (!res.ok) return;
        const stats = await res.json();

        updateMetrics(stats);
        updateTrafficChart(stats);
        updateSparkline(stats);
        updateBreakdown(stats);
        updateLiveFeed();
    } catch (err) {
        console.error('[Dashboard] Polling error:', err);
    }
}

// ── Metric updates ────────────────────────────────────────────

function updateMetrics(stats) {
    const totalEl = document.getElementById('total-processed');
    if (totalEl) totalEl.textContent = stats.total_processed.toLocaleString();

    const attackEl = document.querySelector('.metric-attack');
    if (attackEl) {
        const attacks = stats.dos + stats.probing + stats.r2l + stats.u2r;
        attackEl.textContent = attacks.toLocaleString();
    }

    const alertEl = document.getElementById('active-alerts');
    if (alertEl) alertEl.textContent = (stats.active_alerts || 0).toLocaleString();

    const accEl = document.querySelector('.metric-accuracy');
    if (accEl) accEl.textContent = (stats.model_accuracy * 100).toFixed(2) + '%';
}

function updateTrafficChart(stats) {
    if (!trafficChart) return;
    trafficChart.data.datasets[0].data = [
        stats.normal, stats.dos, stats.probing, stats.r2l, stats.u2r
    ];
    trafficChart.update();
}

function updateSparkline(stats) {
    if (!sparklineChart) return;
    const delta = Math.max(0, stats.total_processed - lastTotal);
    lastTotal = stats.total_processed;
    trafficVolumeData.shift();
    trafficVolumeData.push(delta);
    sparklineChart.data.datasets[0].data = [...trafficVolumeData];
    sparklineChart.update();
}

function updateBreakdown(stats) {
    const map = { 'bd-dos': stats.dos, 'bd-probing': stats.probing,
                  'bd-r2l': stats.r2l, 'bd-u2r': stats.u2r };
    Object.entries(map).forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = (val || 0).toLocaleString();
    });
}

// ── Live feed ─────────────────────────────────────────────────

const CLASS_COLORS = {
    normal:  '#28a745',
    dos:     '#dc3545',
    probing: '#ffc107',
    r2l:     '#fd7e14',
    u2r:     '#6f42c1',
};

async function updateLiveFeed() {
    const feed = document.getElementById('liveFeed');
    if (!feed) return;
    try {
        const res = await fetch('/api/events?per_page=15', {
            headers: { 'X-API-Key': 'dev-api-key-change-in-production' }
        });
        if (!res.ok) return;
        const data = await res.json();
        const events = data.events || [];
        if (!events.length) return;

        // Keep header row, rebuild the rest
        const header = feed.querySelector('.feed-header');
        feed.innerHTML = '';
        if (header) feed.appendChild(header);

        events.forEach(ev => {
            const ts  = new Date(ev.timestamp + 'Z').toLocaleTimeString();
            const cls = ev.predicted_class || 'unknown';
            const ip  = (ev.source_ip || '').replace('[SIM]', '');
            const conf = ((ev.confidence || 0) * 100).toFixed(1) + '%';
            const sim = ev.is_simulated ? '<span class="sim-inline-tag">SIM</span>' : '';

            const row = document.createElement('div');
            row.className = `feed-item feed-${cls}`;
            row.innerHTML = `
                <span class="feed-time">${ts}</span>
                <span class="feed-ip">${ip}</span>
                <span class="feed-class ${cls}" style="color:${CLASS_COLORS[cls] || '#666'}">${cls.toUpperCase()} ${sim}</span>
                <span class="feed-confidence">${conf}</span>
            `;
            feed.appendChild(row);
        });
    } catch (err) {
        console.error('[Dashboard] Live feed error:', err);
    }
}

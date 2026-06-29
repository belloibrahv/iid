// Dashboard JavaScript
// Handles live polling, charts, and real-time updates

let trafficChart = null;
let sparklineChart = null;
let trafficVolumeData = [];
const MAX_DATA_POINTS = 12; // 60 seconds / 5 second intervals

function initDashboard(initialStats) {
    initTrafficChart(initialStats);
    initSparklineChart();
    startPolling();
}

function initTrafficChart(stats) {
    const canvas = document.getElementById('trafficChart');
    clampCanvasSize(canvas, 1200, 300);
    const ctx = canvas.getContext('2d');
    
    const data = {
        labels: ['Normal', 'DoS', 'Probing', 'R2L', 'U2R'],
        datasets: [{
            label: 'Traffic Count',
            data: [stats.normal, stats.dos, stats.probing, stats.r2l, stats.u2r],
            backgroundColor: [
                '#28a745',
                '#dc3545',
                '#ffc107',
                '#fd7e14',
                '#6f42c1'
            ],
            borderWidth: 0
        }]
    };
    
    try {
        trafficChart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (e) {
        console.warn('Failed to create traffic chart:', e);
    }
}

function clampCanvasSize(canvas, maxWidth, maxHeight) {
    canvas.width = Math.min(canvas.width || maxWidth, maxWidth);
    canvas.height = Math.min(canvas.height || maxHeight, maxHeight);
    canvas.style.maxWidth = maxWidth + 'px';
    canvas.style.maxHeight = maxHeight + 'px';
}

function initSparklineChart() {
    const canvas = document.getElementById('sparklineChart');
    clampCanvasSize(canvas, 1200, 130);
    const ctx = canvas.getContext('2d');
    
    // Initialize with empty data
    for (let i = 0; i < MAX_DATA_POINTS; i++) {
        trafficVolumeData.push(0);
    }
    
    try {
        sparklineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: MAX_DATA_POINTS}, (_, i) => i * 5),
                datasets: [{
                    label: 'Packets',
                    data: trafficVolumeData,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        beginAtZero: true
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    } catch (e) {
        console.warn('Failed to create sparkline chart:', e);
    }
}

let pollingInterval = null;

function startPolling() {
    if (pollingInterval) return;
    pollingInterval = setInterval(updateStats, 5000);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopPolling();
    } else {
        startPolling();
    }
});

window.addEventListener('beforeunload', stopPolling);

async function updateStats() {
    try {
        const response = await fetch('/api/stats', {
            headers: {
                'X-API-Key': 'dev-api-key-change-in-production'
            }
        });
        
        if (response.ok) {
            const stats = await response.json();
            updateMetrics(stats);
            updateTrafficChart(stats);
            updateSparkline(stats);
            updateLiveFeed(stats);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

function updateMetrics(stats) {
    const totalEl = document.getElementById('total-processed');
    if (totalEl) {
        totalEl.textContent = stats.total_processed;
    }
    
    const attackCount = stats.dos + stats.probing + stats.r2l + stats.u2r;
    const attackElement = document.querySelector('.metric-attack');
    if (attackElement) {
        attackElement.textContent = attackCount;
    }
    
    const accuracyElement = document.querySelector('.metric-accuracy');
    if (accuracyElement) {
        accuracyElement.textContent = (stats.model_accuracy * 100).toFixed(2) + '%';
    }
}

function updateTrafficChart(stats) {
    if (trafficChart) {
        trafficChart.data.datasets[0].data = [
            stats.normal,
            stats.dos,
            stats.probing,
            stats.r2l,
            stats.u2r
        ];
        try {
            trafficChart.update();
        } catch (e) {
            console.warn('Traffic chart update failed:', e);
        }
    }
}

function updateSparkline(stats) {
    if (sparklineChart) {
        // Calculate new volume (difference from previous total)
        const previousTotal = trafficVolumeData.reduce((a, b) => a + b, 0);
        const newVolume = Math.max(0, stats.total_processed - previousTotal);
        
        // Shift data and add new point
        trafficVolumeData.shift();
        trafficVolumeData.push(newVolume);
        
        sparklineChart.data.datasets[0].data = trafficVolumeData;
        try {
            sparklineChart.update();
        } catch (e) {
            console.warn('Sparkline chart update failed:', e);
        }
    }
}

async function updateLiveFeed(stats) {
    const liveFeed = document.getElementById('liveFeed');
    if (!liveFeed) return;
    
    try {
        // Get recent events
        const response = await fetch('/api/events?per_page=10', {
            headers: {
                'X-API-Key': 'dev-api-key-change-in-production'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const events = data.events || [];
            
            liveFeed.innerHTML = '';
            
            if (events.length === 0) {
                liveFeed.innerHTML = `
                    <div class="feed-item">
                        <span class="feed-time">--:--:--</span>
                        <span class="feed-class">No events yet</span>
                    </div>
                `;
                return;
            }
            
            events.forEach(event => {
                const timestamp = new Date(event.timestamp).toLocaleTimeString();
                const feedItem = document.createElement('div');
                feedItem.className = 'feed-item';
                feedItem.innerHTML = `
                    <span class="feed-time">${timestamp}</span>
                    <span class="feed-class ${event.predicted_class}">${event.predicted_class.toUpperCase()}</span>
                    <span class="feed-confidence">${(event.confidence * 100).toFixed(1)}%</span>
                `;
                liveFeed.appendChild(feedItem);
            });
        }
    } catch (error) {
        console.error('Error fetching live feed:', error);
    }
}

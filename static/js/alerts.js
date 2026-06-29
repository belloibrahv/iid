// Alerts JavaScript
// Handles alert filtering, detail view, and resolution

function filterAlerts(attackType) {
    const url = new URL(window.location.href);
    if (attackType) {
        url.searchParams.set('type', attackType);
    } else {
        url.searchParams.delete('type');
    }
    window.location.href = url.toString();
}

async function showAlertDetail(alertId) {
    const detailRow = document.getElementById(`detail-${alertId}`);
    const detailContent = document.getElementById(`detail-content-${alertId}`);
    
    if (detailRow.style.display === 'none') {
        // Show detail
        detailRow.style.display = 'table-row';
        
        if (detailContent.textContent === 'Loading...') {
            try {
                const response = await fetch(`/alerts/${alertId}/detail`);
                if (response.ok) {
                    const data = await response.json();
                    renderAlertDetail(data, detailContent);
                } else {
                    detailContent.textContent = 'Error loading alert details';
                }
            } catch (error) {
                detailContent.textContent = 'Error loading alert details';
            }
        }
    } else {
        // Hide detail
        detailRow.style.display = 'none';
    }
}

function renderAlertDetail(data, container) {
    // Parse raw features if available
    let features = {};
    if (data.raw_features_json) {
        try {
            features = JSON.parse(data.raw_features_json);
        } catch (e) {
            console.error('Error parsing features:', e);
        }
    }
    
    const featureOrder = [
        'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
        'logged_in', 'count', 'srv_count', 'same_srv_rate', 'diff_srv_rate',
        'dst_host_count', 'dst_host_srv_count', 'dst_host_same_srv_rate',
        'dst_host_diff_srv_rate', 'num_compromised', 'root_shell', 'su_attempted',
        'num_root', 'num_failed_logins'
    ];
    
    let featureHtml = '<h4>Feature Values</h4><div class="feature-grid">';
    
    featureOrder.forEach(feature => {
        const value = features[feature] !== undefined ? features[feature] : 'N/A';
        featureHtml += `
            <div class="feature-item">
                <span class="feature-name">${feature}</span>
                <span class="feature-value">${value}</span>
            </div>
        `;
    });
    
    featureHtml += '</div>';
    
    container.innerHTML = `
        <div class="alert-detail-info">
            <p><strong>Attack Type:</strong> ${data.attack_type.toUpperCase()}</p>
            <p><strong>Confidence:</strong> ${(data.confidence * 100).toFixed(2)}%</p>
            <p><strong>Timestamp:</strong> ${data.timestamp}</p>
            <p><strong>Source IP:</strong> ${data.source_ip || 'N/A'}</p>
        </div>
        ${featureHtml}
    `;
}

async function resolveAlert(alertId) {
    if (!confirm('Are you sure you want to mark this alert as resolved?')) {
        return;
    }
    
    try {
        const response = await fetch(`/alerts/${alertId}/resolve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'dev-api-key-change-in-production'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Reload page to show updated status
                window.location.reload();
            } else {
                alert('Failed to resolve alert');
            }
        } else {
            alert('Failed to resolve alert');
        }
    } catch (error) {
        console.error('Error resolving alert:', error);
        alert('Failed to resolve alert');
    }
}

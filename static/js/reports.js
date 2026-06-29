// Reports JavaScript
// Handles model tab switching and report display

document.addEventListener('DOMContentLoaded', function() {
    const modelTabs = document.querySelectorAll('.model-tab');
    
    modelTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const modelName = this.getAttribute('data-model');
            switchModel(modelName);
        });
    });
});

async function switchModel(modelName) {
    // Update active tab
    document.querySelectorAll('.model-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('data-model') === modelName) {
            tab.classList.add('active');
        }
    });
    
    // Fetch model report data
    try {
        const response = await fetch(`/api/reports/${modelName}`);
        
        if (response.ok) {
            const data = await response.json();
            updateReportContent(data, modelName);
        } else {
            console.error('Failed to load model report');
        }
    } catch (error) {
        console.error('Error fetching model report:', error);
    }
}

function updateReportContent(data, modelName) {
    const reportContent = document.getElementById('reportContent');
    
    if (!data || !data.classification_report) {
        reportContent.innerHTML = '<div class="no-data">No evaluation results available for this model.</div>';
        return;
    }
    
    const report = data.classification_report;
    
    const summaryHtml = `
        <div class="metrics-summary">
            <div class="summary-card">
                <div class="summary-label">Accuracy</div>
                <div class="summary-value">${report.accuracy.toFixed(3)}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Precision</div>
                <div class="summary-value">${report.macro_avg.precision.toFixed(3)}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Recall</div>
                <div class="summary-value">${report.macro_avg.recall.toFixed(3)}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">F1-Score</div>
                <div class="summary-value">${report.macro_avg['f1-score'].toFixed(3)}</div>
            </div>
        </div>
    `;
    
    const classes = ['normal', 'dos', 'probing', 'r2l', 'u2r'];
    let tableRows = '';
    
    classes.forEach(className => {
        if (report[className]) {
            tableRows += `
                <tr>
                    <td>${className.toUpperCase()}</td>
                    <td>${report[className].precision.toFixed(3)}</td>
                    <td>${report[className].recall.toFixed(3)}</td>
                    <td>${report[className]['f1-score'].toFixed(3)}</td>
                    <td>${report[className].support}</td>
                </tr>
            `;
        }
    });
    
    const tableHtml = `
        <div class="per-class-table-container">
            <h3>Per-Class Metrics</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Class</th>
                        <th>Precision</th>
                        <th>Recall</th>
                        <th>F1-Score</th>
                        <th>Support</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
    
    // Note: Accuracy comparison is static and shows all models
    reportContent.innerHTML = summaryHtml + tableHtml;
    
    // Re-add accuracy comparison (it's always shown)
    addAccuracyComparison();
}

function addAccuracyComparison() {
    const reportContent = document.getElementById('reportContent');
    
    // Fetch all evaluation results to show comparison
    fetch('/api/reports/random_forest')
        .then(response => response.json())
        .then(rfData => {
            let comparisonHtml = `
                <div class="accuracy-comparison">
                    <h3>Model Accuracy Comparison</h3>
                    <div class="progress-bars">
            `;
            
            if (rfData && rfData.classification_report) {
                comparisonHtml += `
                    <div class="progress-item">
                        <div class="progress-label">Random Forest</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${rfData.classification_report.accuracy * 100}%">
                                ${(rfData.classification_report.accuracy * 100).toFixed(2)}%
                            </div>
                        </div>
                    </div>
                `;
            }
            
            comparisonHtml += `
                    </div>
                </div>
            `;
            
            reportContent.innerHTML += comparisonHtml;
        })
        .catch(error => {
            console.error('Error loading accuracy comparison:', error);
        });
}

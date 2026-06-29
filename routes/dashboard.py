"""
Dashboard Routes Module.
Implements all web interface routes for login, dashboard, alerts, log, and reports.
Implements FR-DASH-01 through FR-REP-05.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from core.auth import login_user, logout_user, is_authenticated, login_required, init_admin_user
from core.database import Database
import json

dashboard_bp = Blueprint('dashboard', __name__)
db = Database()


@dashboard_bp.route('/')
def index():
    """
    Homepage with information about the IDS system and team.
    """
    return render_template('index.html')


@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page.
    Implements FR-AUTH-01.
    """
    if is_authenticated():
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if login_user(username, password):
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


@dashboard_bp.route('/logout')
def logout():
    """
    Logout endpoint.
    Implements FR-AUTH-04.
    """
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('dashboard.login'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Main dashboard page.
    Implements FR-DASH-01 through FR-DASH-05.
    """
    stats = db.get_stats()
    
    # Add model accuracy from evaluation results
    try:
        with open('models/evaluation_results.json', 'r') as f:
            eval_results = json.load(f)
            rf_accuracy = eval_results['random_forest']['classification_report']['accuracy']
            stats['model_accuracy'] = rf_accuracy
    except:
        stats['model_accuracy'] = 0.0
    
    return render_template('dashboard.html', stats=stats)


@dashboard_bp.route('/alerts')
@login_required
def alerts():
    """
    Alerts management page.
    Implements FR-ALERT-01 through FR-ALERT-08.
    """
    attack_type = request.args.get('type')
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    offset = (page - 1) * per_page
    
    alerts_list = db.get_alerts(
        attack_type=attack_type,
        status=status,
        limit=per_page,
        offset=offset
    )
    
    total = db.get_alert_count(attack_type=attack_type, status=status)
    total_pages = (total + per_page - 1) // per_page
    
    # Get active alert count
    active_count = db.get_alert_count(status='unresolved')
    
    return render_template(
        'alerts.html',
        alerts=alerts_list,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        attack_type=attack_type,
        status=status,
        active_count=active_count
    )


@dashboard_bp.route('/alerts/<int:alert_id>/detail')
@login_required
def alert_detail(alert_id):
    """
    Get alert detail with event data via AJAX.
    Implements FR-ALERT-06.
    """
    alert_data = db.get_alert_with_event(alert_id)
    if alert_data:
        return jsonify(alert_data)
    return jsonify({'error': 'Alert not found'}), 404


@dashboard_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert_route(alert_id):
    """
    Resolve an alert.
    Implements FR-ALERT-05.
    """
    success = db.resolve_alert(alert_id)
    if success:
        flash('Alert marked as resolved', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


@dashboard_bp.route('/log')
@login_required
def event_log():
    """
    Event log page.
    Implements FR-LOG-01 through FR-LOG-05.
    """
    class_filter = request.args.get('class')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    source_ip = request.args.get('source_ip')
    page = int(request.args.get('page', 1))
    per_page = 50
    
    offset = (page - 1) * per_page
    
    events = db.get_events(
        class_filter=class_filter,
        from_date=from_date,
        to_date=to_date,
        source_ip=source_ip,
        limit=per_page,
        offset=offset
    )
    
    total = db.get_event_count(
        class_filter=class_filter,
        from_date=from_date,
        to_date=to_date,
        source_ip=source_ip
    )
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template(
        'log.html',
        events=events,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        class_filter=class_filter,
        from_date=from_date,
        to_date=to_date,
        source_ip=source_ip
    )


@dashboard_bp.route('/reports')
@login_required
def reports():
    """
    Classification report page.
    Implements FR-REP-01 through FR-REP-05.
    """
    # Load evaluation results
    try:
        with open('models/evaluation_results.json', 'r') as f:
            eval_results = json.load(f)
    except:
        eval_results = {}
    
    # Get current active model (Random Forest)
    active_model = 'random_forest'
    
    return render_template(
        'reports.html',
        eval_results=eval_results,
        active_model=active_model
    )


@dashboard_bp.route('/api/reports/<model_name>')
@login_required
def get_model_report(model_name):
    """
    Get report data for a specific model via AJAX.
    Implements FR-REP-04.
    """
    try:
        with open('models/evaluation_results.json', 'r') as f:
            eval_results = json.load(f)
        
        if model_name in eval_results:
            return jsonify(eval_results[model_name])
        return jsonify({'error': 'Model not found'}), 404
    except:
        return jsonify({'error': 'Could not load evaluation results'}), 500

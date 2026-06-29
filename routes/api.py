"""
API Routes Module.
Implements all REST API endpoints for classification and data retrieval.
Implements FR-API-01 through FR-API-08.
"""
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError
from functools import wraps

from core.inference import inference_engine, ValidationError as InferenceValidationError
from core.database import Database
from config import API_KEY, BATCH_CLASSIFICATION_LIMIT

api_bp = Blueprint('api', __name__)
db = Database()


# API Key authentication decorator
def require_api_key(f):
    """Decorator to require API key for API endpoints.
    Also allows session-authenticated users to access endpoints.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session authentication first
        from core.auth import is_authenticated
        if is_authenticated():
            return f(*args, **kwargs)
        
        # Fall back to API key authentication
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


# Validation schemas
class ClassificationSchema(Schema):
    """Schema for single classification request."""
    duration = fields.Float(required=True)
    protocol_type = fields.Str(required=True)
    service = fields.Str(required=True)
    flag = fields.Str(required=True)
    src_bytes = fields.Float(required=True)
    dst_bytes = fields.Float(required=True)
    logged_in = fields.Integer(required=True)
    count = fields.Float(required=True)
    srv_count = fields.Float(required=True)
    same_srv_rate = fields.Float(required=True)
    diff_srv_rate = fields.Float(required=True)
    dst_host_count = fields.Float(required=True)
    dst_host_srv_count = fields.Float(required=True)
    dst_host_same_srv_rate = fields.Float(required=True)
    dst_host_diff_srv_rate = fields.Float(required=True)
    num_compromised = fields.Float(required=True)
    root_shell = fields.Integer(required=True)
    su_attempted = fields.Integer(required=True)
    num_root = fields.Float(required=True)
    num_failed_logins = fields.Float(required=True)


class BatchClassificationSchema(Schema):
    """Schema for batch classification request."""
    records = fields.List(fields.Nested(ClassificationSchema()), required=True)


@api_bp.route('/classify', methods=['POST'])
@require_api_key
def classify():
    """
    Classify a single network connection record.
    Implements FR-API-01 and FR-API-02.
    """
    try:
        # Validate request body
        schema = ClassificationSchema()
        data = schema.load(request.get_json())
        
        # Extract source IP if provided
        source_ip = request.get_json().get('source_ip')
        
        # Run inference
        result = inference_engine.predict(data, source_ip=source_ip)
        
        return jsonify(result), 200
    
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'details': str(e.messages)
        }), 422
    
    except InferenceValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'details': str(e)
        }), 422
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/classify/batch', methods=['POST'])
@require_api_key
def classify_batch():
    """
    Classify a batch of network connection records.
    Implements FR-API-03.
    """
    try:
        # Validate request body
        schema = BatchClassificationSchema()
        data = schema.load(request.get_json())
        records = data['records']
        
        # Check batch size limit
        if len(records) > BATCH_CLASSIFICATION_LIMIT:
            return jsonify({
                'error': f'Batch size limit is {BATCH_CLASSIFICATION_LIMIT} records'
            }), 400
        
        # Run batch inference
        results = inference_engine.predict_batch(records)
        
        return jsonify({'results': results}), 200
    
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'details': str(e.messages)
        }), 422
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stats', methods=['GET'])
@require_api_key
def get_stats():
    """
    Get current dashboard statistics.
    Implements FR-API-06.
    """
    try:
        stats = db.get_stats()
        
        # Add model accuracy from evaluation results
        import json
        from config import EVALUATION_RESULTS_PATH
        try:
            with open(EVALUATION_RESULTS_PATH, 'r') as f:
                eval_results = json.load(f)
                rf_accuracy = eval_results['random_forest']['classification_report']['accuracy']
                stats['model_accuracy'] = rf_accuracy
        except:
            stats['model_accuracy'] = 0.0
        
        return jsonify(stats), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/alerts', methods=['GET'])
@require_api_key
def get_alerts():
    """
    Get paginated alert records with optional filters.
    Implements FR-API-07.
    """
    try:
        # Get query parameters
        attack_type = request.args.get('type')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get alerts
        alerts = db.get_alerts(
            attack_type=attack_type,
            status=status,
            limit=per_page,
            offset=offset
        )
        
        # Get total count
        total = db.get_alert_count(attack_type=attack_type, status=status)
        
        return jsonify({
            'alerts': alerts,
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/alerts/<int:alert_id>/resolve', methods=['PATCH'])
@require_api_key
def resolve_alert(alert_id):
    """
    Mark an alert as resolved.
    """
    try:
        success = db.resolve_alert(alert_id)
        
        if success:
            return jsonify({'alert_id': alert_id, 'status': 'resolved'}), 200
        else:
            return jsonify({'error': 'Alert not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/events', methods=['GET'])
@require_api_key
def get_events():
    """
    Get paginated event log records with optional filters.
    Implements FR-API-08.
    """
    try:
        # Get query parameters
        class_filter = request.args.get('class')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        source_ip = request.args.get('source_ip')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get events
        events = db.get_events(
            class_filter=class_filter,
            from_date=from_date,
            to_date=to_date,
            source_ip=source_ip,
            limit=per_page,
            offset=offset
        )
        
        # Get total count
        total = db.get_event_count(
            class_filter=class_filter,
            from_date=from_date,
            to_date=to_date,
            source_ip=source_ip
        )
        
        return jsonify({
            'events': events,
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/events/export', methods=['GET'])
@require_api_key
def export_events():
    """
    Export filtered event log as CSV file.
    Implements FR-LOG-05.
    """
    try:
        import csv
        from io import StringIO
        from flask import Response
        
        # Get query parameters
        class_filter = request.args.get('class')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        source_ip = request.args.get('source_ip')
        
        # Get all matching events (no limit for export)
        events = db.get_events(
            class_filter=class_filter,
            from_date=from_date,
            to_date=to_date,
            source_ip=source_ip,
            limit=10000,
            offset=0
        )
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        if events:
            writer.writerow(events[0].keys())
        
        # Write rows
        for event in events:
            writer.writerow(event.values())
        
        # Create response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=events_export.csv'
            }
        )
        
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

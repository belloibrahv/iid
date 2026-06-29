"""
Unit tests for API endpoints.
"""
import pytest
import json
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_classify_valid_payload(client):
    """Test classification with valid payload."""
    # This test requires model artefacts to be loaded
    # Skip if inference engine fails to load
    try:
        from core.inference import inference_engine
    except:
        pytest.skip("Model artefacts not available")
    
    payload = {
        'duration': 0,
        'protocol_type': 'tcp',
        'service': 'http',
        'flag': 'SF',
        'src_bytes': 181,
        'dst_bytes': 5450,
        'logged_in': 1,
        'count': 8,
        'srv_count': 8,
        'same_srv_rate': 1.0,
        'diff_srv_rate': 0.0,
        'dst_host_count': 9,
        'dst_host_srv_count': 9,
        'dst_host_same_srv_rate': 1.0,
        'dst_host_diff_srv_rate': 0.0,
        'num_compromised': 0,
        'root_shell': 0,
        'su_attempted': 0,
        'num_root': 0,
        'num_failed_logins': 0
    }
    
    response = client.post(
        '/api/classify',
        data=json.dumps(payload),
        content_type='application/json',
        headers={'X-API-Key': 'dev-api-key-change-in-production'}
    )
    
    # Check response
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'predicted_class' in data
    assert 'confidence' in data
    assert 'event_id' in data


def test_classify_missing_field(client):
    """Test classification with missing required field."""
    payload = {
        'duration': 0,
        'protocol_type': 'tcp'
        # Missing many required fields
    }
    
    response = client.post(
        '/api/classify',
        data=json.dumps(payload),
        content_type='application/json',
        headers={'X-API-Key': 'dev-api-key-change-in-production'}
    )
    
    # Should return 422 for validation error
    assert response.status_code == 422


def test_classify_invalid_api_key(client):
    """Test classification with invalid API key."""
    payload = {
        'duration': 0,
        'protocol_type': 'tcp',
        'service': 'http',
        'flag': 'SF',
        'src_bytes': 181,
        'dst_bytes': 5450,
        'logged_in': 1,
        'count': 8,
        'srv_count': 8,
        'same_srv_rate': 1.0,
        'diff_srv_rate': 0.0,
        'dst_host_count': 9,
        'dst_host_srv_count': 9,
        'dst_host_same_srv_rate': 1.0,
        'dst_host_diff_srv_rate': 0.0,
        'num_compromised': 0,
        'root_shell': 0,
        'su_attempted': 0,
        'num_root': 0,
        'num_failed_logins': 0
    }
    
    response = client.post(
        '/api/classify',
        data=json.dumps(payload),
        content_type='application/json',
        headers={'X-API-Key': 'invalid-key'}
    )
    
    # Should return 401 for invalid API key
    assert response.status_code == 401


def test_get_stats(client):
    """Test getting statistics."""
    response = client.get(
        '/api/stats',
        headers={'X-API-Key': 'dev-api-key-change-in-production'}
    )
    
    # Check response
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'total_processed' in data
    assert 'normal' in data
    assert 'dos' in data


def test_get_alerts(client):
    """Test getting alerts."""
    response = client.get(
        '/api/alerts',
        headers={'X-API-Key': 'dev-api-key-change-in-production'}
    )
    
    # Check response
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'alerts' in data
    assert 'total' in data


def test_batch_classification_limit(client):
    """Test that batch classification rejects more than 100 records."""
    # Create payload with 101 records
    records = [
        {
            'duration': 0,
            'protocol_type': 'tcp',
            'service': 'http',
            'flag': 'SF',
            'src_bytes': 181,
            'dst_bytes': 5450,
            'logged_in': 1,
            'count': 8,
            'srv_count': 8,
            'same_srv_rate': 1.0,
            'diff_srv_rate': 0.0,
            'dst_host_count': 9,
            'dst_host_srv_count': 9,
            'dst_host_same_srv_rate': 1.0,
            'dst_host_diff_srv_rate': 0.0,
            'num_compromised': 0,
            'root_shell': 0,
            'su_attempted': 0,
            'num_root': 0,
            'num_failed_logins': 0
        }
    ] * 101
    
    payload = {'records': records}
    
    response = client.post(
        '/api/classify/batch',
        data=json.dumps(payload),
        content_type='application/json',
        headers={'X-API-Key': 'dev-api-key-change-in-production'}
    )
    
    # Should return 400 for batch size limit exceeded
    assert response.status_code == 400

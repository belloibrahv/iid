"""
Unit tests for the inference engine.
"""
import pytest
from core.inference import InferenceEngine, ValidationError


def test_validate_record_missing_feature():
    """Test that validation fails for missing features."""
    # This test will fail if model artefacts don't exist
    # Skip if artefacts not available
    pytest.importorskip("joblib")
    
    try:
        engine = InferenceEngine()
    except:
        pytest.skip("Model artefacts not available")
    
    incomplete_record = {
        'duration': 0,
        'protocol_type': 'tcp'
        # Missing many required features
    }
    
    with pytest.raises(ValidationError):
        engine.validate_record(incomplete_record)


def test_validate_record_none_value():
    """Test that validation fails for None values."""
    try:
        engine = InferenceEngine()
    except:
        pytest.skip("Model artefacts not available")
    
    record_with_none = {
        'duration': None,
        'protocol_type': 'tcp',
        'service': 'http',
        'flag': 'SF',
        'src_bytes': 100,
        'dst_bytes': 200,
        'logged_in': 1,
        'count': 5,
        'srv_count': 5,
        'same_srv_rate': 1.0,
        'diff_srv_rate': 0.0,
        'dst_host_count': 10,
        'dst_host_srv_count': 10,
        'dst_host_same_srv_rate': 1.0,
        'dst_host_diff_srv_rate': 0.0,
        'num_compromised': 0,
        'root_shell': 0,
        'su_attempted': 0,
        'num_root': 0,
        'num_failed_logins': 0
    }
    
    with pytest.raises(ValidationError):
        engine.validate_record(record_with_none)


def test_predict_returns_valid_format():
    """Test that predict returns a dictionary with required keys."""
    try:
        engine = InferenceEngine()
    except:
        pytest.skip("Model artefacts not available")
    
    valid_record = {
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
    
    result = engine.predict(valid_record, source_ip='192.168.1.100')
    
    # Check required keys
    assert 'predicted_class' in result
    assert 'confidence' in result
    assert 'timestamp' in result
    assert 'event_id' in result
    
    # Check predicted_class is valid
    valid_classes = ['normal', 'dos', 'probing', 'r2l', 'u2r']
    assert result['predicted_class'] in valid_classes
    
    # Check confidence is in [0, 1]
    assert 0 <= result['confidence'] <= 1
    
    # Check event_id is a positive integer
    assert isinstance(result['event_id'], int)
    assert result['event_id'] > 0


def test_predict_batch():
    """Test batch prediction."""
    try:
        engine = InferenceEngine()
    except:
        pytest.skip("Model artefacts not available")
    
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
    ] * 3
    
    results = engine.predict_batch(records)
    
    # Check we get results for all records
    assert len(results) == 3
    
    # Check each result has required fields
    for result in results:
        assert 'record_index' in result
        if 'error' not in result:
            assert 'event_id' in result
            assert 'predicted_class' in result

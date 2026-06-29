"""
Unit tests for the database module.
"""
import pytest
import tempfile
import os
from core.database import Database


def test_database_initialization():
    """Test that database initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = Database(db_path)
        
        # Check that database file was created
        assert os.path.exists(db_path)


def test_create_user():
    """Test user creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = Database(db_path)
        
        user_id = db.create_user('testuser', 'hashed_password')
        
        # Check that user ID is a positive integer
        assert isinstance(user_id, int)
        assert user_id > 0


def test_get_user_by_username():
    """Test retrieving user by username."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = Database(db_path)
        
        # Create a user
        db.create_user('testuser', 'hashed_password')
        
        # Retrieve the user
        user = db.get_user_by_username('testuser')
        
        # Check user data
        assert user is not None
        assert user['username'] == 'testuser'
        assert user['password_hash'] == 'hashed_password'


def test_create_event():
    """Test event creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = Database(db_path)
        
        event_data = {
            'predicted_class': 'dos',
            'confidence': 0.98,
            'source_ip': '192.168.1.100',
            'duration': 0,
            'protocol_type': 'tcp',
            'service': 'http',
            'flag': 'SF',
            'src_bytes': 100,
            'dst_bytes': 200,
            'logged_in': 0,
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
        
        event_id = db.create_event(event_data)
        
        # Check that event ID is a positive integer
        assert isinstance(event_id, int)
        assert event_id > 0


def test_create_alert():
    """Test alert creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = Database(db_path)
        
        # First create an event
        event_data = {
            'predicted_class': 'dos',
            'confidence': 0.98,
            'duration': 0,
            'protocol_type': 'tcp',
            'service': 'http',
            'flag': 'SF',
            'src_bytes': 100,
            'dst_bytes': 200,
            'logged_in': 0,
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
        
        event_id = db.create_event(event_data)
        
        # Create alert
        alert_id = db.create_alert(event_id, 'dos', 0.98, '192.168.1.100')
        
        # Check that alert ID is a positive integer
        assert isinstance(alert_id, int)
        assert alert_id > 0


def test_resolve_alert():
    """Test alert resolution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = Database(db_path)
        
        # Create event and alert
        event_data = {
            'predicted_class': 'dos',
            'confidence': 0.98,
            'duration': 0,
            'protocol_type': 'tcp',
            'service': 'http',
            'flag': 'SF',
            'src_bytes': 100,
            'dst_bytes': 200,
            'logged_in': 0,
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
        
        event_id = db.create_event(event_data)
        alert_id = db.create_alert(event_id, 'dos', 0.98)
        
        # Resolve alert
        success = db.resolve_alert(alert_id)
        
        # Check resolution was successful
        assert success is True
        
        # Check alert status
        alerts = db.get_alerts()
        resolved_alert = [a for a in alerts if a['id'] == alert_id][0]
        assert resolved_alert['status'] == 'resolved'


def test_get_stats():
    """Test statistics retrieval."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = Database(db_path)
        
        # Create some events
        for i in range(5):
            event_data = {
                'predicted_class': 'normal' if i < 3 else 'dos',
                'confidence': 0.9,
                'duration': 0,
                'protocol_type': 'tcp',
                'service': 'http',
                'flag': 'SF',
                'src_bytes': 100,
                'dst_bytes': 200,
                'logged_in': 0,
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
            event_id = db.create_event(event_data)
            
            # Create alert for dos events
            if i >= 3:
                db.create_alert(event_id, 'dos', 0.9)
        
        stats = db.get_stats()
        
        # Check stats
        assert stats['total_processed'] == 5
        assert stats['normal'] == 3
        assert stats['dos'] == 2
        assert stats['active_alerts'] == 2

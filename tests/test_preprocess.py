"""
Unit tests for the pre-processing module.
"""
import pytest
import numpy as np
import pandas as pd
from ml.preprocess import Preprocessor


def test_preprocessor_initialization():
    """Test that Preprocessor initializes correctly."""
    preprocessor = Preprocessor()
    assert preprocessor.encoders == {}
    assert preprocessor.scaler is None
    assert preprocessor.feature_selector is None
    assert preprocessor.selected_features is None


def test_encode_categorical():
    """Test categorical encoding."""
    preprocessor = Preprocessor()
    
    # Create sample data
    X_train = pd.DataFrame({
        'protocol_type': ['tcp', 'udp', 'tcp'],
        'service': ['http', 'ftp', 'http'],
        'flag': ['SF', 'SF', 'REJ'],
        'duration': [0, 1, 2]
    })
    
    y_train = ['normal', 'dos', 'normal']
    
    # Fit and transform
    preprocessor.fit(X_train, y_train)
    X_encoded = preprocessor._encode_categorical(X_train)
    
    # Check that categorical columns are now numeric
    assert X_encoded['protocol_type'].dtype in [np.int64, int]
    assert X_encoded['service'].dtype in [np.int64, int]
    assert X_encoded['flag'].dtype in [np.int64, int]


def test_min_max_scaling():
    """Test min-max scaling produces values in [0, 1]."""
    preprocessor = Preprocessor()
    
    # Create sample data
    X_train = pd.DataFrame({
        'protocol_type': ['tcp', 'udp', 'tcp'],
        'service': ['http', 'ftp', 'http'],
        'flag': ['SF', 'SF', 'REJ'],
        'duration': [0, 100, 50]
    })
    
    y_train = ['normal', 'dos', 'normal']
    
    # Fit and transform
    preprocessor.fit(X_train, y_train)
    X_processed = preprocessor.transform(X_train)
    
    # Check all values are in [0, 1]
    assert np.all((X_processed >= 0) & (X_processed <= 1))


def test_feature_selection():
    """Test that feature selection reduces to exactly 20 features."""
    preprocessor = Preprocessor()
    
    # Create sample data with more than 20 features
    feature_names = [f'feature_{i}' for i in range(41)]
    X_train = pd.DataFrame({
        **{f: np.random.rand(100) for f in feature_names[:3]},  # categorical
        **{f: np.random.rand(100) for f in feature_names[3:]}  # numerical
    })
    
    # Rename first 3 to categorical names
    X_train = X_train.rename(columns={
        'feature_0': 'protocol_type',
        'feature_1': 'service',
        'feature_2': 'flag'
    })
    
    # Set categorical values
    X_train['protocol_type'] = ['tcp', 'udp'] * 50
    X_train['service'] = ['http', 'ftp'] * 50
    X_train['flag'] = ['SF', 'REJ'] * 50
    
    y_train = ['normal'] * 50 + ['dos'] * 50
    
    # Fit and transform
    preprocessor.fit(X_train, y_train)
    X_processed = preprocessor.transform(X_train)
    
    # Check output has exactly 20 features
    assert X_processed.shape[1] == 20


def test_save_and_load_artefacts():
    """Test that artefacts can be saved and loaded."""
    import tempfile
    import os
    from ml.config import (
        ENCODER_PROTOCOL_TYPE_PATH,
        ENCODER_SERVICE_PATH,
        ENCODER_FLAG_PATH,
        SCALER_PATH,
        FEATURE_SELECTOR_PATH,
        SELECTED_FEATURES_PATH
    )
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Update paths to use temp directory
        original_paths = [
            ENCODER_PROTOCOL_TYPE_PATH,
            ENCODER_SERVICE_PATH,
            ENCODER_FLAG_PATH,
            SCALER_PATH,
            FEATURE_SELECTOR_PATH,
            SELECTED_FEATURES_PATH
        ]
        
        temp_paths = [
            os.path.join(tmpdir, 'encoder_protocol.joblib'),
            os.path.join(tmpdir, 'encoder_service.joblib'),
            os.path.join(tmpdir, 'encoder_flag.joblib'),
            os.path.join(tmpdir, 'scaler.joblib'),
            os.path.join(tmpdir, 'selector.joblib'),
            os.path.join(tmpdir, 'features.json')
        ]
        
        # Monkey patch the paths
        import ml.preprocess as preprocess_module
        preprocess_module.ENCODER_PROTOCOL_TYPE_PATH = temp_paths[0]
        preprocess_module.ENCODER_SERVICE_PATH = temp_paths[1]
        preprocess_module.ENCODER_FLAG_PATH = temp_paths[2]
        preprocess_module.SCALER_PATH = temp_paths[3]
        preprocess_module.FEATURE_SELECTOR_PATH = temp_paths[4]
        preprocess_module.SELECTED_FEATURES_PATH = temp_paths[5]
        
        # Create and fit preprocessor
        preprocessor = Preprocessor()
        X_train = pd.DataFrame({
            'protocol_type': ['tcp', 'udp'] * 50,
            'service': ['http', 'ftp'] * 50,
            'flag': ['SF', 'REJ'] * 50,
            'duration': np.random.rand(100)
        })
        y_train = ['normal'] * 50 + ['dos'] * 50
        
        preprocessor.fit(X_train, y_train)
        preprocessor.save_artefacts()
        
        # Load artefacts
        loaded_preprocessor = Preprocessor.load_artefacts()
        
        # Check that loaded preprocessor has the same selected features
        assert loaded_preprocessor.selected_features == preprocessor.selected_features
        
        # Restore original paths
        preprocess_module.ENCODER_PROTOCOL_TYPE_PATH = original_paths[0]
        preprocess_module.ENCODER_SERVICE_PATH = original_paths[1]
        preprocess_module.ENCODER_FLAG_PATH = original_paths[2]
        preprocess_module.SCALER_PATH = original_paths[3]
        preprocess_module.FEATURE_SELECTOR_PATH = original_paths[4]
        preprocess_module.SELECTED_FEATURES_PATH = original_paths[5]

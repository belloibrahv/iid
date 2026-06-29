"""
Inference Engine Module.
Loads model artefacts and applies the full pre-processing pipeline for predictions.
Implements the inference pipeline as specified in Section 6.6.
"""
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

from ml.config import (
    CLASS_LABEL_MAP,
    RANDOM_FOREST_MODEL_PATH,
    ENCODER_PROTOCOL_TYPE_PATH,
    ENCODER_SERVICE_PATH,
    ENCODER_FLAG_PATH,
    SCALER_PATH,
    FEATURE_SELECTOR_PATH,
    SELECTED_FEATURES_PATH
)
from core.database import Database


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InferenceEngine:
    """
    Loads model artefacts and performs inference on network connection records.
    Implements the full inference pipeline from Section 6.6.
    """
    
    def __init__(self):
        self.model = None
        self.encoders = {}
        self.scaler = None
        self.feature_selector = None
        self.selected_features = []
        self.db = Database()
        self._load_artefacts()
    
    def _load_artefacts(self):
        """
        Load all model artefacts from disk.
        """
        print("Loading model artefacts...")
        
        # Load Random Forest model (the deployed model)
        self.model = joblib.load(RANDOM_FOREST_MODEL_PATH)
        
        # Load encoders
        self.encoders['protocol_type'] = joblib.load(ENCODER_PROTOCOL_TYPE_PATH)
        self.encoders['service'] = joblib.load(ENCODER_SERVICE_PATH)
        self.encoders['flag'] = joblib.load(ENCODER_FLAG_PATH)
        
        # Load scaler
        self.scaler = joblib.load(SCALER_PATH)
        
        # Load feature selector
        self.feature_selector = joblib.load(FEATURE_SELECTOR_PATH)
        
        # Load selected feature names
        with open(SELECTED_FEATURES_PATH, 'r') as f:
            self.selected_features = json.load(f)
        
        print("Model artefacts loaded successfully.")
    
    def validate_record(self, record: Dict[str, Any]) -> None:
        """
        Validate that all required features are present and within expected bounds.
        
        Args:
            record: Dictionary containing feature values
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for missing required features
        missing_features = set(self.selected_features) - set(record.keys())
        if missing_features:
            raise ValidationError(f"Missing required features: {missing_features}")
        
        # Basic validation for numerical ranges
        for feature in self.selected_features:
            value = record[feature]
            
            # Check for None values
            if value is None:
                raise ValidationError(f"Feature '{feature}' cannot be None")
            
            # Check for numerical features
            if feature not in ['protocol_type', 'service', 'flag']:
                try:
                    float(value)
                except (ValueError, TypeError):
                    raise ValidationError(f"Feature '{feature}' must be numeric")
    
    def preprocess_record(self, record: Dict[str, Any]) -> np.ndarray:
        """
        Apply the full pre-processing pipeline to a single record.
        
        Args:
            record: Dictionary containing feature values
            
        Returns:
            Pre-processed feature vector (1D numpy array)
        """
        # Convert to DataFrame
        df = pd.DataFrame([record])
        
        # Step 1: Encode categorical features
        for feature in ['protocol_type', 'service', 'flag']:
            encoder = self.encoders[feature]
            known_classes = set(encoder.classes_)
            
            def encode_value(val):
                if val in known_classes:
                    return encoder.transform([val])[0]
                else:
                    # Handle unseen categories
                    return 0
            
            df[feature] = df[feature].apply(encode_value)
        
        # Step 2: Select features in correct order
        df_ordered = df[self.selected_features]
        
        # Step 3: Apply MinMax scaling (transform, do not fit)
        df_scaled = self.scaler.transform(df_ordered)
        
        # Step 4: Apply feature selection (transform, do not fit)
        df_selected = self.feature_selector.transform(df_scaled)
        
        return df_selected[0]  # Return as 1D array
    
    def predict(self, record: Dict[str, Any], source_ip: str = None) -> Dict[str, Any]:
        """
        Run the full inference pipeline on a single record.
        
        Args:
            record: Dictionary containing feature values
            source_ip: Optional source IP address
            
        Returns:
            Dictionary with predicted_class, confidence, timestamp, event_id
            
        Raises:
            ValidationError: If input validation fails
        """
        # Step 1: Validate input
        self.validate_record(record)
        
        # Step 2: Preprocess
        features = self.preprocess_record(record)
        
        # Step 3: Predict
        prediction = self.model.predict([features])[0]
        probabilities = self.model.predict_proba([features])[0]
        confidence = float(np.max(probabilities))
        
        # Step 4: Map integer class to string label
        predicted_class = CLASS_LABEL_MAP[prediction]
        
        # Step 5: Create timestamp
        timestamp = datetime.utcnow().isoformat()
        
        # Step 6: Prepare event data for database
        event_data = {
            'timestamp': timestamp,
            'predicted_class': predicted_class,
            'confidence': confidence,
            'source_ip': source_ip,
            **record
        }
        
        # Step 7: Write to database
        event_id = self.db.create_event(event_data)
        
        # Step 8: Create alert if attack detected
        if predicted_class != 'normal':
            self.db.create_alert(event_id, predicted_class, confidence, source_ip)
        
        # Step 9: Return result
        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'timestamp': timestamp,
            'event_id': event_id
        }
    
    def predict_batch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run inference on a batch of records.
        
        Args:
            records: List of record dictionaries
            
        Returns:
            List of prediction results
        """
        results = []
        
        for i, record in enumerate(records):
            try:
                result = self.predict(record)
                results.append({
                    'record_index': i,
                    'event_id': result['event_id'],
                    'predicted_class': result['predicted_class'],
                    'confidence': result['confidence']
                })
            except ValidationError as e:
                results.append({
                    'record_index': i,
                    'error': str(e)
                })
        
        return results


# Global inference engine instance
inference_engine = InferenceEngine()


if __name__ == '__main__':
    # Test the inference engine
    print("Testing inference engine...")
    
    # Sample record (normal traffic)
    test_record = {
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
    
    print("\nTesting single prediction...")
    result = inference_engine.predict(test_record, source_ip='192.168.1.100')
    print(f"Result: {result}")
    
    print("\nTesting batch prediction...")
    batch_records = [test_record, test_record, test_record]
    batch_results = inference_engine.predict_batch(batch_records)
    print(f"Batch results: {batch_results}")
    
    print("\nTesting validation...")
    try:
        incomplete_record = {'duration': 0}
        inference_engine.predict(incomplete_record)
    except ValidationError as e:
        print(f"Validation error (expected): {e}")
    
    print("\nInference engine test complete!")

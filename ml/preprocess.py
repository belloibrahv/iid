"""
Pre-processor Module.
Implements label encoding, min-max scaling, and feature selection.
Saves all fitted artefacts for reuse during inference.
Implements ML-PRE-01 through ML-PRE-06.
"""
import pandas as pd
import numpy as np
import json
import joblib
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.feature_selection import SelectKBest, mutual_info_classif

from ml.config import (
    CATEGORICAL_FEATURES,
    N_FEATURES_TO_SELECT,
    SELECTED_FEATURES,
    ENCODER_PROTOCOL_TYPE_PATH,
    ENCODER_SERVICE_PATH,
    ENCODER_FLAG_PATH,
    SCALER_PATH,
    FEATURE_SELECTOR_PATH,
    SELECTED_FEATURES_PATH
)


class Preprocessor:
    """
    Handles data pre-processing: encoding, scaling, and feature selection.
    Fitted on training data and applied to test/inference data.
    """
    
    def __init__(self):
        self.encoders = {}
        self.scaler = None
        self.feature_selector = None
        self.selected_features = None
    
    def fit(self, X_train, y_train):
        """
        Fit all pre-processing steps on training data.
        
        Args:
            X_train: Training feature DataFrame
            y_train: Training labels
            
        Returns:
            self: Fitted preprocessor
        """
        # Step 1: Fit label encoders for categorical features (ML-PRE-01)
        for feature in CATEGORICAL_FEATURES:
            encoder = LabelEncoder()
            encoder.fit(X_train[feature])
            self.encoders[feature] = encoder
        
        # Step 2: Apply encoding to training data
        X_encoded = self._encode_categorical(X_train)
        
        # Step 3: Fit MinMaxScaler (ML-PRE-02)
        self.scaler = MinMaxScaler()
        X_scaled = self.scaler.fit_transform(X_encoded)
        
        # Step 4: Fit feature selector using mutual information (ML-PRE-03)
        self.feature_selector = SelectKBest(
            score_func=mutual_info_classif,
            k=N_FEATURES_TO_SELECT
        )
        X_selected = self.feature_selector.fit_transform(X_scaled, y_train)
        
        # Step 5: Get selected feature names
        selected_mask = self.feature_selector.get_support()
        self.selected_features = X_encoded.columns[selected_mask].tolist()
        
        print(f"Selected {len(self.selected_features)} features:")
        print(self.selected_features)
        
        return self
    
    def transform(self, X):
        """
        Apply fitted pre-processing to new data.
        
        Args:
            X: Feature DataFrame to transform
            
        Returns:
            Transformed feature matrix (numpy array)
        """
        # Step 1: Encode categorical features
        X_encoded = self._encode_categorical(X)
        
        # Step 2: Apply scaling (do NOT refit)
        X_scaled = self.scaler.transform(X_encoded)
        
        # Step 3: Apply feature selection (do NOT refit)
        X_selected = self.feature_selector.transform(X_scaled)
        
        return X_selected
    
    def fit_transform(self, X_train, y_train):
        """
        Fit on training data and transform it.
        
        Args:
            X_train: Training feature DataFrame
            y_train: Training labels
            
        Returns:
            Transformed training feature matrix
        """
        self.fit(X_train, y_train)
        return self.transform(X_train)
    
    def _encode_categorical(self, X):
        """
        Encode categorical features using fitted encoders.
        Handles unseen categories by assigning them to a default value.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            DataFrame with encoded categorical features
        """
        X_encoded = X.copy()
        
        for feature in CATEGORICAL_FEATURES:
            encoder = self.encoders[feature]
            
            # Handle unseen categories by mapping them to a special value
            # Get the set of known classes
            known_classes = set(encoder.classes_)
            
            # Create a mapping for unseen values
            def encode_value(val):
                if val in known_classes:
                    return encoder.transform([val])[0]
                else:
                    # Assign unseen category to the most frequent class
                    return 0  # or could use len(known_classes)
            
            X_encoded[feature] = X_encoded[feature].apply(encode_value)
        
        return X_encoded
    
    def save_artefacts(self):
        """
        Save all fitted artefacts to disk (ML-PRE-04).
        """
        # Save encoders
        joblib.dump(self.encoders['protocol_type'], ENCODER_PROTOCOL_TYPE_PATH)
        joblib.dump(self.encoders['service'], ENCODER_SERVICE_PATH)
        joblib.dump(self.encoders['flag'], ENCODER_FLAG_PATH)
        
        # Save scaler
        joblib.dump(self.scaler, SCALER_PATH)
        
        # Save feature selector
        joblib.dump(self.feature_selector, FEATURE_SELECTOR_PATH)
        
        # Save selected feature names
        with open(SELECTED_FEATURES_PATH, 'w') as f:
            json.dump(self.selected_features, f, indent=2)
        
        print("Pre-processing artefacts saved successfully.")
    
    @classmethod
    def load_artefacts(cls):
        """
        Load fitted artefacts from disk for inference.
        
        Returns:
            Preprocessor instance with loaded artefacts
        """
        preprocessor = cls()
        
        # Load encoders
        preprocessor.encoders['protocol_type'] = joblib.load(ENCODER_PROTOCOL_TYPE_PATH)
        preprocessor.encoders['service'] = joblib.load(ENCODER_SERVICE_PATH)
        preprocessor.encoders['flag'] = joblib.load(ENCODER_FLAG_PATH)
        
        # Load scaler
        preprocessor.scaler = joblib.load(SCALER_PATH)
        
        # Load feature selector
        preprocessor.feature_selector = joblib.load(FEATURE_SELECTOR_PATH)
        
        # Load selected feature names
        with open(SELECTED_FEATURES_PATH, 'r') as f:
            preprocessor.selected_features = json.load(f)
        
        print("Pre-processing artefacts loaded successfully.")
        
        return preprocessor


def preprocess_for_inference(record_dict, preprocessor):
    """
    Pre-process a single record dictionary for inference.
    
    Args:
        record_dict: Dictionary with feature names as keys
        preprocessor: Fitted Preprocessor instance
        
    Returns:
        Transformed feature vector (numpy array)
    """
    # Convert to DataFrame
    df = pd.DataFrame([record_dict])
    
    # Ensure all required features are present
    for feature in preprocessor.selected_features:
        if feature not in df.columns:
            raise ValueError(f"Missing required feature: {feature}")
    
    # Select only the features in the correct order
    df_ordered = df[preprocessor.selected_features]
    
    # Transform
    transformed = preprocessor.transform(df_ordered)
    
    return transformed[0]  # Return single row as 1D array


if __name__ == '__main__':
    # Test the preprocessor
    from ml.load_data import load_train_data, get_feature_matrix_and_labels
    
    print("Loading training data...")
    train_df = load_train_data()
    X_train, y_train = get_feature_matrix_and_labels(train_df)
    
    print(f"\nOriginal feature shape: {X_train.shape}")
    
    print("\nFitting preprocessor...")
    preprocessor = Preprocessor()
    X_train_processed = preprocessor.fit_transform(X_train, y_train)
    
    print(f"\nProcessed feature shape: {X_train_processed.shape}")
    
    print("\nSaving artefacts...")
    preprocessor.save_artefacts()
    
    print("\nTesting artefact loading...")
    loaded_preprocessor = Preprocessor.load_artefacts()
    
    print("\nTesting transform on sample data...")
    sample = X_train.iloc[:5]
    transformed = loaded_preprocessor.transform(sample)
    print(f"Transformed shape: {transformed.shape}")
    print(f"All values in [0, 1]: {np.all((transformed >= 0) & (transformed <= 1))}")

"""
Model Training Module.
Trains Random Forest, Decision Tree, and SVM classifiers on pre-processed data.
Implements ML-RF-01 through ML-SVM-05.
"""
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.multiclass import OneVsRestClassifier

from ml.config import (
    RF_PARAMS,
    DT_PARAMS,
    SVM_PARAMS,
    RANDOM_FOREST_MODEL_PATH,
    DECISION_TREE_MODEL_PATH,
    SVM_MODEL_PATH
)


class ModelTrainer:
    """
    Trains and saves classification models.
    """
    
    def __init__(self):
        self.rf_model = None
        self.dt_model = None
        self.svm_model = None
    
    def train_random_forest(self, X_train, y_train):
        """
        Train Random Forest classifier with specified hyperparameters.
        
        Args:
            X_train: Pre-processed training features
            y_train: Training labels
            
        Returns:
            Trained RandomForestClassifier
        """
        print("Training Random Forest classifier...")
        self.rf_model = RandomForestClassifier(**RF_PARAMS)
        self.rf_model.fit(X_train, y_train)
        print(f"Random Forest training completed.")
        return self.rf_model
    
    def train_decision_tree(self, X_train, y_train):
        """
        Train Decision Tree classifier with specified hyperparameters.
        
        Args:
            X_train: Pre-processed training features
            y_train: Training labels
            
        Returns:
            Trained DecisionTreeClassifier
        """
        print("Training Decision Tree classifier...")
        self.dt_model = DecisionTreeClassifier(**DT_PARAMS)
        self.dt_model.fit(X_train, y_train)
        print(f"Decision Tree training completed.")
        return self.dt_model
    
    def train_svm(self, X_train, y_train):
        """
        Train SVM classifier with OneVsRest multi-class strategy.
        
        Args:
            X_train: Pre-processed training features
            y_train: Training labels
            
        Returns:
            Trained OneVsRestClassifier with SVM base
        """
        print("Training SVM classifier...")
        svm_base = SVC(**SVM_PARAMS, probability=True)
        self.svm_model = OneVsRestClassifier(svm_base)
        self.svm_model.fit(X_train, y_train)
        print(f"SVM training completed.")
        return self.svm_model
    
    def train_all(self, X_train, y_train):
        """
        Train all three models.
        
        Args:
            X_train: Pre-processed training features
            y_train: Training labels
            
        Returns:
            Dictionary with all trained models
        """
        models = {}
        
        models['random_forest'] = self.train_random_forest(X_train, y_train)
        models['decision_tree'] = self.train_decision_tree(X_train, y_train)
        models['svm'] = self.train_svm(X_train, y_train)
        
        return models
    
    def save_models(self):
        """
        Save all trained models to disk (ML-SER-01 through ML-SER-03).
        """
        if self.rf_model:
            joblib.dump(self.rf_model, RANDOM_FOREST_MODEL_PATH)
            print(f"Random Forest model saved to {RANDOM_FOREST_MODEL_PATH}")
        
        if self.dt_model:
            joblib.dump(self.dt_model, DECISION_TREE_MODEL_PATH)
            print(f"Decision Tree model saved to {DECISION_TREE_MODEL_PATH}")
        
        if self.svm_model:
            joblib.dump(self.svm_model, SVM_MODEL_PATH)
            print(f"SVM model saved to {SVM_MODEL_PATH}")
    
    @classmethod
    def load_model(cls, model_name):
        """
        Load a specific trained model from disk.
        
        Args:
            model_name: One of 'random_forest', 'decision_tree', 'svm'
            
        Returns:
            Loaded model
        """
        if model_name == 'random_forest':
            return joblib.load(RANDOM_FOREST_MODEL_PATH)
        elif model_name == 'decision_tree':
            return joblib.load(DECISION_TREE_MODEL_PATH)
        elif model_name == 'svm':
            return joblib.load(SVM_MODEL_PATH)
        else:
            raise ValueError(f"Unknown model name: {model_name}")


if __name__ == '__main__':
    # Test the trainer
    from ml.load_data import load_train_data, get_feature_matrix_and_labels
    from ml.preprocess import Preprocessor
    
    print("Loading and preprocessing training data...")
    train_df = load_train_data()
    X_train, y_train = get_feature_matrix_and_labels(train_df)
    
    print("Fitting preprocessor...")
    preprocessor = Preprocessor()
    X_train_processed = preprocessor.fit_transform(X_train, y_train)
    
    print("\n" + "="*50)
    print("Training models...")
    trainer = ModelTrainer()
    models = trainer.train_all(X_train_processed, y_train)
    
    print("\n" + "="*50)
    print("Saving models...")
    trainer.save_models()
    
    print("\n" + "="*50)
    print("Testing model loading...")
    rf_loaded = ModelTrainer.load_model('random_forest')
    dt_loaded = ModelTrainer.load_model('decision_tree')
    svm_loaded = ModelTrainer.load_model('svm')
    
    print("All models loaded successfully!")
    
    # Test prediction
    print("\nTesting prediction on sample data...")
    sample = X_train_processed[:5]
    rf_pred = rf_loaded.predict(sample)
    print(f"RF predictions: {rf_pred}")

"""
Model Evaluation Module.
Computes metrics, generates plots, and saves evaluation results.
Implements ML-EVAL-01 through ML-EVAL-07.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    ConfusionMatrixDisplay
)
from sklearn.preprocessing import label_binarize

from ml.config import (
    CLASS_LABELS,
    EVALUATION_RESULTS_PATH
)


class ModelEvaluator:
    """
    Evaluates trained models and generates visualisations.
    """
    
    def __init__(self):
        self.results = {}
    
    def evaluate_model(self, model, X_test, y_test, model_name):
        """
        Evaluate a single model on test data.
        
        Args:
            model: Trained model
            X_test: Pre-processed test features
            y_test: Test labels
            model_name: Name of the model for reporting
            
        Returns:
            Dictionary of evaluation metrics
        """
        print(f"\nEvaluating {model_name}...")
        
        # Get predictions
        y_pred = model.predict(X_test)
        
        # Get prediction probabilities (if available)
        try:
            y_proba = model.predict_proba(X_test)
        except AttributeError:
            # Some models don't have predict_proba
            y_proba = None
        
        # Compute classification report
        report = classification_report(
            y_test, y_pred,
            target_names=CLASS_LABELS,
            output_dict=True
        )
        
        # Compute confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Compute AUC-ROC (if probabilities available)
        auc_roc = None
        if y_proba is not None:
            try:
                # Binarize labels for multi-class ROC
                y_test_bin = label_binarize(y_test, classes=CLASS_LABELS)
                
                # Handle case where y_proba might need reshaping
                if len(y_proba.shape) == 2 and y_proba.shape[1] == len(CLASS_LABELS):
                    auc_roc = roc_auc_score(y_test_bin, y_proba, multi_class='ovr')
                else:
                    auc_roc = roc_auc_score(y_test, y_proba, multi_class='ovr')
            except Exception as e:
                print(f"Could not compute AUC-ROC: {e}")
                auc_roc = None
        
        # Store results
        model_results = {
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'auc_roc': auc_roc,
            'predictions': y_pred.tolist()
        }
        
        self.results[model_name] = model_results
        
        # Print summary
        print(f"\n{model_name} Results:")
        print(f"Overall Accuracy: {report['accuracy']:.4f}")
        if auc_roc:
            print(f"AUC-ROC: {auc_roc:.4f}")
        
        return model_results
    
    def evaluate_all(self, models, X_test, y_test):
        """
        Evaluate all models.
        
        Args:
            models: Dictionary of model_name -> trained_model
            X_test: Pre-processed test features
            y_test: Test labels
            
        Returns:
            Dictionary of all evaluation results
        """
        for model_name, model in models.items():
            self.evaluate_model(model, X_test, y_test, model_name)
        
        return self.results
    
    def plot_confusion_matrix(self, model_name, save_path=None):
        """
        Plot confusion matrix for a model.
        
        Args:
            model_name: Name of the model
            save_path: Optional path to save the plot
        """
        if model_name not in self.results:
            raise ValueError(f"No results for model: {model_name}")
        
        cm = np.array(self.results[model_name]['confusion_matrix'])
        
        fig, ax = plt.subplots(figsize=(8, 6))
        disp = ConfusionMatrixDisplay(
            confusion_matrix=cm,
            display_labels=CLASS_LABELS
        )
        disp.plot(ax=ax, cmap='Blues', values_format='d')
        plt.title(f'Confusion Matrix - {model_name.replace("_", " ").title()}')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Confusion matrix saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_roc_curves(self, models, X_test, y_test, save_path=None):
        """
        Plot ROC curves for all models on a single figure (ML-EVAL-05).
        
        Args:
            models: Dictionary of model_name -> trained_model
            X_test: Pre-processed test features
            y_test: Test labels
            save_path: Optional path to save the plot
        """
        from sklearn.metrics import roc_curve, auc
        from sklearn.preprocessing import label_binarize
        
        # Binarize labels
        y_test_bin = label_binarize(y_test, classes=CLASS_LABELS)
        n_classes = len(CLASS_LABELS)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = ['blue', 'red', 'green', 'orange', 'purple']
        model_colors = {
            'random_forest': 'blue',
            'decision_tree': 'green',
            'svm': 'red'
        }
        
        for model_name, model in models.items():
            try:
                y_proba = model.predict_proba(X_test)
                
                # Compute ROC curve for each class
                fpr = dict()
                tpr = dict()
                roc_auc = dict()
                
                for i in range(n_classes):
                    fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
                    roc_auc[i] = auc(fpr[i], tpr[i])
                
                # Compute micro-average ROC curve
                fpr["micro"], tpr["micro"], _ = roc_curve(
                    y_test_bin.ravel(), y_proba.ravel()
                )
                roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])
                
                # Plot micro-average ROC
                ax.plot(
                    fpr["micro"], tpr["micro"],
                    label=f'{model_name.replace("_", " ").title()} (AUC = {roc_auc["micro"]:.3f})',
                    color=model_colors.get(model_name, 'black'),
                    linewidth=2
                )
            except Exception as e:
                print(f"Could not plot ROC for {model_name}: {e}")
        
        ax.plot([0, 1], [0, 1], 'k--', linewidth=1)
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('ROC Curves - Model Comparison')
        ax.legend(loc="lower right")
        ax.grid(alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"ROC curves saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_accuracy_comparison(self, save_path=None):
        """
        Plot bar chart comparing accuracy across all models (ML-EVAL-06).
        
        Args:
            save_path: Optional path to save the plot
        """
        model_names = []
        accuracies = []
        
        for model_name, results in self.results.items():
            model_names.append(model_name.replace('_', ' ').title())
            accuracies.append(results['classification_report']['accuracy'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(model_names, accuracies, color=['blue', 'green', 'red'])
        
        ax.set_ylabel('Accuracy')
        ax.set_title('Model Accuracy Comparison')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'{acc:.4f}',
                ha='center', va='bottom'
            )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Accuracy comparison saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def save_results(self):
        """
        Save all evaluation results to JSON file (ML-EVAL-07).
        """
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = {}
        for model_name, results in self.results.items():
            serializable_results[model_name] = {
                'classification_report': results['classification_report'],
                'confusion_matrix': results['confusion_matrix'],
                'auc_roc': results['auc_roc']
            }
        
        with open(EVALUATION_RESULTS_PATH, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Evaluation results saved to {EVALUATION_RESULTS_PATH}")


if __name__ == '__main__':
    # Test the evaluator
    from ml.load_data import load_train_data, load_test_data, get_feature_matrix_and_labels
    from ml.preprocess import Preprocessor
    from ml.train import ModelTrainer
    
    print("Loading and preprocessing data...")
    train_df = load_train_data()
    test_df = load_test_data()
    
    X_train, y_train = get_feature_matrix_and_labels(train_df)
    X_test, y_test = get_feature_matrix_and_labels(test_df)
    
    print("Fitting preprocessor...")
    preprocessor = Preprocessor()
    X_train_processed = preprocessor.fit_transform(X_train, y_train)
    X_test_processed = preprocessor.transform(X_test)
    
    print("\nTraining models...")
    trainer = ModelTrainer()
    models = trainer.train_all(X_train_processed, y_train)
    
    print("\nEvaluating models...")
    evaluator = ModelEvaluator()
    evaluator.evaluate_all(models, X_test_processed, y_test)
    
    print("\nGenerating plots...")
    evaluator.plot_confusion_matrix('random_forest', save_path='models/cm_rf.png')
    evaluator.plot_confusion_matrix('decision_tree', save_path='models/cm_dt.png')
    evaluator.plot_confusion_matrix('svm', save_path='models/cm_svm.png')
    
    evaluator.plot_roc_curves(models, X_test_processed, y_test, save_path='models/roc_curves.png')
    evaluator.plot_accuracy_comparison(save_path='models/accuracy_comparison.png')
    
    print("\nSaving results...")
    evaluator.save_results()
    
    print("\nEvaluation complete!")

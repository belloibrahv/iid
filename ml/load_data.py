"""
Dataset Loader Module.
Loads NSL-KDD dataset files, assigns column names, and maps attack labels to 5 categories.
Implements ML-DATA-01, ML-DATA-02, ML-DATA-03.
"""
import pandas as pd
from ml.config import (
    ALL_FEATURE_NAMES,
    ATTACK_MAP,
    TRAIN_DATA_PATH,
    TEST_DATA_PATH
)


def load_dataset(file_path):
    """
    Load NSL-KDD dataset from a text file.
    
    Args:
        file_path: Path to the dataset file (KDDTrain+.txt or KDDTest+.txt)
        
    Returns:
        DataFrame with 41 feature columns and a label column
    """
    # Load data without header (files have no header row)
    df = pd.read_csv(file_path, header=None)
    
    # Assign column names (41 features + label)
    column_names = ALL_FEATURE_NAMES + ['label']
    df.columns = column_names
    
    return df


def map_attack_labels(df):
    """
    Map the 22 raw attack sub-type labels to 5 consolidated categories.
    
    Args:
        df: DataFrame with original 'label' column
        
    Returns:
        DataFrame with new 'category' column containing one of:
        'normal', 'dos', 'probing', 'r2l', 'u2r'
    """
    # Map each attack type to its category
    df['category'] = df['label'].map(ATTACK_MAP)
    
    # Verify no unmapped labels
    unmapped = df[df['category'].isna()]['label'].unique()
    if len(unmapped) > 0:
        raise ValueError(f"Unmapped attack labels found: {unmapped}")
    
    return df


def load_train_data():
    """
    Load and preprocess the training dataset (KDDTrain+.txt).
    
    Returns:
        DataFrame with features and category labels
    """
    df = load_dataset(TRAIN_DATA_PATH)
    df = map_attack_labels(df)
    return df


def load_test_data():
    """
    Load and preprocess the test dataset (KDDTest+.txt).
    
    Returns:
        DataFrame with features and category labels
    """
    df = load_dataset(TEST_DATA_PATH)
    df = map_attack_labels(df)
    return df


def get_feature_matrix_and_labels(df, feature_columns=None):
    """
    Separate features and labels from the dataset.
    
    Args:
        df: DataFrame with features and 'category' column
        feature_columns: List of feature column names to use.
                        If None, uses all 41 features.
                        
    Returns:
        X: Feature matrix (DataFrame)
        y: Label series (Series)
    """
    if feature_columns is None:
        feature_columns = ALL_FEATURE_NAMES
    
    X = df[feature_columns].copy()
    y = df['category'].copy()
    
    return X, y


if __name__ == '__main__':
    # Test the data loader
    print("Loading training data...")
    train_df = load_train_data()
    print(f"Training data shape: {train_df.shape}")
    print(f"\nClass distribution in training data:")
    print(train_df['category'].value_counts())
    
    print("\n" + "="*50)
    print("Loading test data...")
    test_df = load_test_data()
    print(f"Test data shape: {test_df.shape}")
    print(f"\nClass distribution in test data:")
    print(test_df['category'].value_counts())
    
    print("\n" + "="*50)
    print("Sample of training data:")
    print(train_df.head())

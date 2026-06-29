"""
ML Pipeline Configuration Module.
Contains feature names, attack mapping, model hyperparameters, and file paths.
"""
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Dataset paths
DATA_DIR = BASE_DIR / 'data'
TRAIN_DATA_PATH = DATA_DIR / 'KDDTrain+.txt'
TEST_DATA_PATH = DATA_DIR / 'KDDTest+.txt'

# Model artefact paths
MODELS_DIR = BASE_DIR / 'models'
MODELS_DIR.mkdir(exist_ok=True)

RANDOM_FOREST_MODEL_PATH = MODELS_DIR / 'random_forest.joblib'
DECISION_TREE_MODEL_PATH = MODELS_DIR / 'decision_tree.joblib'
SVM_MODEL_PATH = MODELS_DIR / 'svm.joblib'

ENCODER_PROTOCOL_TYPE_PATH = MODELS_DIR / 'encoder_protocol_type.joblib'
ENCODER_SERVICE_PATH = MODELS_DIR / 'encoder_service.joblib'
ENCODER_FLAG_PATH = MODELS_DIR / 'encoder_flag.joblib'
SCALER_PATH = MODELS_DIR / 'scaler.joblib'
FEATURE_SELECTOR_PATH = MODELS_DIR / 'feature_selector.joblib'
SELECTED_FEATURES_PATH = MODELS_DIR / 'selected_features.json'
EVALUATION_RESULTS_PATH = MODELS_DIR / 'evaluation_results.json'

# All 41 NSL-KDD feature names (in order)
ALL_FEATURE_NAMES = [
    'duration', 'protocol_type', 'service', 'flag',
    'src_bytes', 'dst_bytes', 'land', 'wrong_fragment', 'urgent',
    'hot', 'num_failed_logins', 'logged_in', 'num_compromised',
    'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count', 'serror_rate',
    'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate', 'same_srv_rate',
    'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count',
    'dst_host_srv_count', 'dst_host_same_srv_rate',
    'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
    'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
    'dst_host_srv_rerror_rate'
]

# The 20 selected features after information gain ranking (ML-PRE-06)
SELECTED_FEATURES = [
    'src_bytes', 'dst_bytes', 'flag', 'service', 'duration',
    'protocol_type', 'count', 'srv_count', 'same_srv_rate',
    'diff_srv_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root',
    'num_failed_logins'
]

# Categorical features that need label encoding
CATEGORICAL_FEATURES = ['protocol_type', 'service', 'flag']

# Attack type to category mapping (ML-DATA-03)
ATTACK_MAP = {
    'normal': 'normal',
    # DoS attacks
    'back': 'dos', 'land': 'dos', 'neptune': 'dos', 'pod': 'dos',
    'smurf': 'dos', 'teardrop': 'dos', 'mailbomb': 'dos',
    'apache2': 'dos', 'processtable': 'dos', 'udpstorm': 'dos',
    # Probing attacks
    'ipsweep': 'probing', 'nmap': 'probing', 'portsweep': 'probing',
    'satan': 'probing', 'mscan': 'probing', 'saint': 'probing',
    # R2L attacks
    'ftp_write': 'r2l', 'guess_passwd': 'r2l', 'imap': 'r2l',
    'multihop': 'r2l', 'phf': 'r2l', 'spy': 'r2l', 'warezclient': 'r2l',
    'warezmaster': 'r2l', 'snmpgetattack': 'r2l', 'named': 'r2l',
    'xlock': 'r2l', 'xsnoop': 'r2l', 'sendmail': 'r2l',
    # U2R attacks
    'buffer_overflow': 'u2r', 'loadmodule': 'u2r', 'perl': 'u2r',
    'rootkit': 'u2r', 'httptunnel': 'u2r', 'ps': 'u2r',
    'sqlattack': 'u2r', 'xterm': 'u2r',
}

# Class label mapping for prediction output
CLASS_LABELS = ['normal', 'dos', 'probing', 'r2l', 'u2r']
CLASS_LABEL_MAP = {i: label for i, label in enumerate(CLASS_LABELS)}

# Random Forest hyperparameters (ML-RF-01 to ML-RF-07)
RF_PARAMS = {
    'n_estimators': 100,
    'criterion': 'gini',
    'max_features': 'sqrt',
    'max_depth': None,
    'min_samples_leaf': 1,
    'random_state': 42,
    'n_jobs': -1
}

# Decision Tree hyperparameters (ML-DT-01 to ML-DT-04)
DT_PARAMS = {
    'criterion': 'gini',
    'max_depth': 15,
    'min_samples_leaf': 2,
    'random_state': 42
}

# SVM hyperparameters (ML-SVM-01 to ML-SVM-05)
SVM_PARAMS = {
    'kernel': 'rbf',
    'C': 1.0,
    'gamma': 'scale',
    'random_state': 42
}

# Feature selection parameters
N_FEATURES_TO_SELECT = 20

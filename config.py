"""
Application-level configuration for the IDS Flask application.
Centralises all configuration values as per NFR-MAINT-04.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Database Configuration
# Render provides DATABASE_URL automatically for PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # PostgreSQL (Render or other production database)
    DATABASE_PATH = None
else:
    # SQLite (development)
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'ids.db'))

# Model Paths
MODELS_DIR = BASE_DIR / 'models'
RANDOM_FOREST_MODEL_PATH = MODELS_DIR / 'random_forest.joblib'
DECISION_TREE_MODEL_PATH = MODELS_DIR / 'decision_tree.joblib'
SVM_MODEL_PATH = MODELS_DIR / 'svm.joblib'

# Pre-processing Artefact Paths
ENCODER_PROTOCOL_TYPE_PATH = MODELS_DIR / 'encoder_protocol_type.joblib'
ENCODER_SERVICE_PATH = MODELS_DIR / 'encoder_service.joblib'
ENCODER_FLAG_PATH = MODELS_DIR / 'encoder_flag.joblib'
SCALER_PATH = MODELS_DIR / 'scaler.joblib'
FEATURE_SELECTOR_PATH = MODELS_DIR / 'feature_selector.joblib'
SELECTED_FEATURES_PATH = MODELS_DIR / 'selected_features.json'
EVALUATION_RESULTS_PATH = MODELS_DIR / 'evaluation_results.json'

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
API_KEY = os.getenv('API_KEY', 'dev-api-key-change-in-production')

# Session Configuration
SESSION_PERMANENT = False
SESSION_TYPE = 'filesystem'
SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'  # True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
EVENT_LOG_PAGE_SIZE = 50

# API Configuration
BATCH_CLASSIFICATION_LIMIT = 100

# Classification Thresholds
CONFIDENCE_THRESHOLD = 0.5

# Ensure directories exist
MODELS_DIR.mkdir(exist_ok=True)

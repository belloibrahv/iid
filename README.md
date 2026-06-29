# Intelligent Intrusion Detection System (IDS)

A web-based security monitoring application that uses supervised machine learning to classify network traffic connections as normal or as one of four attack categories: Denial of Service (DoS), Probing, Remote to Local (R2L), and User to Root (U2R).

## Project Overview

This system addresses the fundamental shortcomings of traditional signature-based IDS tools by training classification models on the NSL-KDD benchmark dataset and deploying them through a real-time web interface.

**Institution:** Tai Solarin Federal University of Education (TASFUED), Ijebu-Ode, Ogun State  
**Department:** Computer and Information Science  
**Supervisor:** Mrs Ogunbanjo  
**Version:** 1.0.0

## Features

- **ML Pipeline**: Offline data pre-processing, model training, evaluation, and serialisation
- **Web Application**: Flask REST API backend with HTML/CSS/JS frontend dashboard
- **Real-time Classification**: Classify network traffic with 99%+ accuracy using Random Forest
- **Dashboard**: Live traffic monitoring, alert management, event log, and performance reports
- **Authentication**: Secure session-based authentication for administrators

## Tech Stack

### Machine Learning
- Python 3.10+
- scikit-learn 1.3+
- pandas 2.0+
- NumPy 1.24+
- joblib 1.3+
- matplotlib 3.7+
- seaborn 0.12+

### Backend
- Flask 3.0+
- SQLite 3.x
- Flask-Bcrypt 1.0+
- Flask-Session 0.5+
- marshmallow 3.20+

### Frontend
- HTML5, CSS3, Vanilla JavaScript (ES6+)
- Chart.js for visualizations

## Project Structure

```
ids-project/
├── ml/                          # Machine learning pipeline
│   ├── load_data.py             # Dataset loading and label mapping
│   ├── preprocess.py            # Encoding, scaling, feature selection
│   ├── train.py                 # Train RF, DT, SVM models
│   ├── evaluate.py              # Metrics, plots, evaluation
│   ├── config.py                # ML configuration
│   └── notebooks/
│       └── eda.ipynb            # Exploratory data analysis
├── models/                      # Serialised model artefacts
├── core/                        # Shared backend logic
│   ├── inference.py             # Inference engine
│   ├── database.py              # SQLite operations
│   └── auth.py                  # Authentication
├── routes/                      # Flask route handlers
│   ├── api.py                   # API endpoints
│   └── dashboard.py             # Dashboard routes
├── templates/                   # Jinja2 HTML templates
├── static/                      # Static assets
│   ├── css/
│   └── js/
├── data/                        # Dataset files
├── tests/                       # Test suite
├── app.py                       # Flask app factory
├── config.py                    # App configuration
├── requirements.txt             # Dependencies
├── .env                         # Environment variables
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   cd /Users/kudirat/Desktop/iid
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set your SECRET_KEY and API_KEY
   ```

5. **Download NSL-KDD Dataset**
   - Download `KDDTrain+.txt` and `KDDTest+.txt` from the Canadian Institute for Cybersecurity
   - Place them in the `data/` directory

## Usage

### Step 1: Run ML Pipeline

Train and evaluate the classification models:

```bash
python ml/load_data.py      # Test data loading
python ml/preprocess.py     # Pre-process and save artefacts
python ml/train.py          # Train all models
python ml/evaluate.py       # Evaluate and generate reports
```

This will:
- Load and pre-process the NSL-KDD dataset
- Train Random Forest, Decision Tree, and SVM classifiers
- Evaluate models on the test set
- Save model artefacts to `models/` directory
- Generate evaluation reports and plots

### Step 2: Initialize Database and Admin User

```bash
python core/auth.py
```

This will create the SQLite database and initialize the default admin user:
- Username: `admin`
- Password: `admin123` (change this after first login!)

### Step 3: Start the Web Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Run with Docker

The production container pins Python to 3.11 so scientific dependencies install from stable wheels instead of being compiled against a newer Python version.

```bash
docker build -t ids-app .
docker run --env-file .env -p 5000:10000 ids-app
```

The container installs `requirements-prod.txt`, listens on `PORT`, and defaults to `10000`, matching Render's Docker web service behavior.

### Step 4: Access the Dashboard

1. Open `http://localhost:5000` in your browser
2. Log in with the admin credentials
3. Navigate through the dashboard to monitor traffic, view alerts, and review reports

## API Endpoints

### Classification API

All API endpoints require the `X-API-Key` header.

**Classify single record:**
```bash
POST /api/classify
Content-Type: application/json
X-API-Key: your-api-key

{
  "duration": 0,
  "protocol_type": "tcp",
  "service": "http",
  "flag": "SF",
  "src_bytes": 181,
  "dst_bytes": 5450,
  "logged_in": 1,
  "count": 8,
  "srv_count": 8,
  "same_srv_rate": 1.0,
  "diff_srv_rate": 0.0,
  "dst_host_count": 9,
  "dst_host_srv_count": 9,
  "dst_host_same_srv_rate": 1.0,
  "dst_host_diff_srv_rate": 0.0,
  "num_compromised": 0,
  "root_shell": 0,
  "su_attempted": 0,
  "num_root": 0,
  "num_failed_logins": 0
}
```

**Batch classification:**
```bash
POST /api/classify/batch
Content-Type: application/json
X-API-Key: your-api-key

{
  "records": [...]
}
```

**Get statistics:**
```bash
GET /api/stats
X-API-Key: your-api-key
```

**Get alerts:**
```bash
GET /api/alerts?type=dos&status=unresolved&page=1&per_page=20
X-API-Key: your-api-key
```

**Get events:**
```bash
GET /api/events?class=dos&from=2026-01-01&to=2026-12-31
X-API-Key: your-api-key
```

## Model Performance

The deployed Random Forest model achieves:
- **Overall Accuracy**: ≥99% on KDDTest+ test set
- **DoS F1-Score**: ≥0.99
- **U2R Recall**: ≥0.85 (minority class)
- **False Positive Rate**: ≤1.0%

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=. tests/
```

## Development

### Code Formatting

```bash
black .
```

### Linting

```bash
flake8 .
```

## Security Considerations

- Change the default admin password immediately after first login
- Update `SECRET_KEY` and `API_KEY` in `.env` for production
- Enable HTTPS in production by setting `SESSION_COOKIE_SECURE = True`
- The system is designed for single-administrator use
- API endpoints are protected by API key authentication

## Troubleshooting

### Model artefacts not found
Ensure you have run the ML pipeline before starting the web application. The inference engine requires model files in the `models/` directory.

### Database locked errors
SQLite may experience locking under high concurrent write operations. For production deployment with high traffic volume, consider migrating to PostgreSQL.

### Import errors
Ensure all dependencies are installed: `pip install -r requirements.txt`

## License

This project is developed as a final year project for TASFUED Computer and Information Science Department.

## Acknowledgments

- NSL-KDD Dataset: Canadian Institute for Cybersecurity
- scikit-learn: Machine Learning library for Python
- Flask: Python web framework

## Contact

For questions or issues, please contact the project supervisor: Mrs Ogunbanjo

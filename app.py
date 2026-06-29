"""
Flask Application Factory.
Creates and configures the Flask application with all routes and extensions.
"""
from flask import Flask, session
from flask_cors import CORS
from config import SECRET_KEY, SESSION_TYPE, SESSION_PERMANENT
from core.auth import bcrypt, init_admin_user
from core.inference import inference_engine
from routes.api import api_bp
from routes.dashboard import dashboard_bp


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SESSION_TYPE'] = SESSION_TYPE
    app.config['SESSION_PERMANENT'] = SESSION_PERMANENT
    
    # Initialize extensions
    bcrypt.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp)
    
    # Initialize admin user
    with app.app_context():
        init_admin_user()
    
    # Load inference engine (this loads model artefacts)
    try:
        _ = inference_engine
        print("Inference engine loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load inference engine: {e}")
        print("Please run the ML pipeline first to generate model artefacts.")

    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200
    
    # Root route redirects to dashboard
    @app.route('/')
    def index():
        from core.auth import is_authenticated
        if is_authenticated():
            from flask import redirect, url_for
            return redirect(url_for('dashboard.dashboard'))
        from flask import redirect, url_for
        return redirect(url_for('dashboard.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('login.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('login.html'), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

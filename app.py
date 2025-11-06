"""
Admissions Genie - SNF Admission Decision Support Tool
Main Flask application entry point.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, session, request
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config.settings import config
from config.database import init_db

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])
config[env].init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[app.config['RATELIMIT_DEFAULT']],
    storage_uri=app.config['RATELIMIT_STORAGE_URL']
)

# Set up logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Admissions Genie startup')

# Register blueprints (routes)
try:
    from routes.auth import auth_bp
    from routes.admission import admission_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admission_bp, url_prefix='/admission')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    app.logger.info('All blueprints registered successfully')
except ImportError as e:
    app.logger.error(f'Failed to import blueprints: {e}')


# Main routes
@app.route('/')
def index():
    """Home page - redirect to login or dashboard."""
    if 'user_id' in session:
        return render_template('dashboard.html')
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Main dashboard page."""
    if 'user_id' not in session:
        return render_template('login.html', error='Please log in to continue.')

    from models.admission import Admission
    from models.user import User

    user = User.get_by_id(session['user_id'])
    recent_admissions = Admission.get_recent(limit=10)

    return render_template('dashboard.html', user=user, recent_admissions=recent_admissions)


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return {'status': 'healthy', 'version': '1.0.0'}, 200


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    app.logger.warning(f'404 error: {request.url}')
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    app.logger.error(f'500 error: {error}')
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors."""
    app.logger.warning(f'403 error: {request.url}')
    return render_template('errors/403.html'), 403


# Template filters
@app.template_filter('currency')
def currency_filter(value):
    """Format value as currency."""
    if value is None:
        return '$0.00'
    return f'${value:,.2f}'


@app.template_filter('percentage')
def percentage_filter(value):
    """Format value as percentage."""
    if value is None:
        return '0%'
    return f'{value:.1f}%'


# Context processors
@app.context_processor
def inject_user():
    """Inject current user into all templates."""
    if 'user_id' in session:
        from models.user import User
        user = User.get_by_id(session['user_id'])
        return dict(current_user=user)
    return dict(current_user=None)


# Initialize database on first run
with app.app_context():
    try:
        init_db()
        app.logger.info('Database initialized successfully')
    except Exception as e:
        app.logger.error(f'Database initialization failed: {e}')


if __name__ == '__main__':
    # Check for Azure OpenAI configuration (optional for demo mode)
    azure_configured = all([
        os.getenv('AZURE_OPENAI_API_KEY'),
        os.getenv('AZURE_OPENAI_ENDPOINT'),
        os.getenv('AZURE_OPENAI_DEPLOYMENT')
    ])

    if not azure_configured:
        print("\n" + "="*70)
        print("⚠️  DEMO MODE - Azure OpenAI Not Configured")
        print("="*70)
        print("\nRunning in DEMO MODE with pre-loaded sample admissions.")
        print("Document upload feature will be disabled.")
        print("\nTo enable document upload, set these environment variables:")
        print("  - AZURE_OPENAI_API_KEY")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_DEPLOYMENT")
        print("\nSee .env.example for reference.")
        print("="*70 + "\n")

    # Run the application
    port = int(os.getenv('PORT', 5000))
    print("\n" + "="*70)
    print(f"🚀 Starting Admissions Genie (DEMO VERSION)")
    print("="*70)
    print(f"📍 Access at: http://localhost:{port}")
    print(f"📧 Admin login: admin@admissionsgenie.com / admin123")
    print(f"📧 User login: user@admissionsgenie.com / user123")
    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])

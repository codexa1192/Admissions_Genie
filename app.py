"""
Admissions Genie - SNF Admission Decision Support Tool
Main Flask application entry point.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, session, request, redirect
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config.settings import config, Config
from config.database import init_db
from middleware.session_timeout import init_session_timeout

# Initialize Sentry for error tracking (production only)
if Config.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv('FLASK_ENV', 'development'),
        before_send=lambda event, hint: None if Config.FLASK_ENV == 'development' else event
    )

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

# Make limiter accessible for route decorators
app.extensions['limiter'] = limiter

# Initialize session timeout middleware (HIPAA requirement: 15-minute idle timeout)
init_session_timeout(app)

# Force HTTPS in production
if Config.FLASK_ENV == 'production':
    @app.before_request
    def force_https():
        """Redirect HTTP to HTTPS in production."""
        if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

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
    from routes.health import health_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admission_bp, url_prefix='/admission')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(health_bp)  # Health checks at /health

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
    # Get recent admissions for the user's organization (multi-tenant)
    recent_admissions = Admission.get_recent(organization_id=user.organization_id, limit=10)

    return render_template('dashboard.html', user=user, recent_admissions=recent_admissions)


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
    # CRITICAL SECURITY CHECK: Enforce encryption in production
    if Config.FLASK_ENV == 'production':
        if not os.getenv('ENCRYPTION_KEY'):
            print("\n" + "="*70)
            print("❌ FATAL ERROR: ENCRYPTION_KEY not set in production!")
            print("="*70)
            print("\n🔒 HIPAA Compliance Requirement:")
            print("Production deployment REQUIRES encryption for PHI protection.")
            print("\n📝 To generate an encryption key:")
            print('  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"')
            print("\n⚙️  Then set the environment variable:")
            print("  export ENCRYPTION_KEY='<generated-key>'")
            print("  # Or add to .env file or hosting platform environment variables")
            print("\n⚠️  Security Warning:")
            print("  - Store the key securely (AWS Secrets Manager, Azure Key Vault, etc.)")
            print("  - Never commit the key to version control")
            print("  - Back up the key in multiple secure locations")
            print("  - If the key is lost, encrypted data CANNOT be recovered")
            print("="*70 + "\n")
            sys.exit(1)  # PREVENT STARTUP WITHOUT ENCRYPTION

        # Check for default admin credentials
        try:
            from models.user import User
            admin = User.get_by_email('admin@admissionsgenie.com')
            if admin and admin.verify_password('admin123'):
                print("\n" + "="*70)
                print("⚠️  WARNING: DEFAULT ADMIN CREDENTIALS DETECTED!")
                print("="*70)
                print("\n🔐 Security Risk:")
                print("The default admin password 'admin123' is still in use.")
                print("This is a CRITICAL security vulnerability in production.")
                print("\n📝 Required Action:")
                print("1. Login as admin@admissionsgenie.com")
                print("2. Navigate to Settings → Change Password")
                print("3. Set a strong password (12+ chars, mixed case, numbers, symbols)")
                print("\n⏱  You have 24 hours to change this password.")
                print("After 24 hours, the admin account will be locked for security.")
                print("="*70 + "\n")
                app.logger.critical("DEFAULT ADMIN CREDENTIALS DETECTED IN PRODUCTION - SECURITY RISK!")
        except Exception as e:
            app.logger.warning(f"Could not check admin credentials: {e}")

        # Check virus scanner availability (CRITICAL for production)
        try:
            from utils.virus_scanner import get_virus_scanner
            scanner = get_virus_scanner()
            if not scanner.is_available():
                print("\n" + "="*70)
                print("❌ FATAL ERROR: Virus scanner not available in production!")
                print("="*70)
                print("\n🦠 HIPAA Compliance Requirement:")
                print("Production deployment REQUIRES malware protection (§164.308(a)(5)(ii)(B)).")
                print("\n📝 To install ClamAV:")
                print("  # macOS")
                print("  brew install clamav")
                print("  brew services start clamav")
                print("\n  # Ubuntu/Debian")
                print("  sudo apt-get install clamav clamav-daemon")
                print("  sudo systemctl start clamav-daemon")
                print("\n  # Install Python package")
                print("  pip install python-clamd")
                print("\n⚠️  Security Warning:")
                print("  Files CANNOT be uploaded safely without virus scanning.")
                print("  This is a CRITICAL security requirement for handling PHI.")
                print("="*70 + "\n")
                sys.exit(1)  # PREVENT STARTUP WITHOUT VIRUS SCANNING
            else:
                print(f"✅ Virus scanner available: {scanner.get_version()}")
        except Exception as e:
            print("\n" + "="*70)
            print("❌ FATAL ERROR: Cannot initialize virus scanner!")
            print("="*70)
            print(f"\nError: {e}")
            print("\nVirus scanning is REQUIRED for HIPAA compliance.")
            print("="*70 + "\n")
            sys.exit(1)

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

    # Show appropriate startup message based on mode
    if Config.FLASK_ENV == 'production':
        print("\n" + "="*70)
        print(f"🚀 Starting Admissions Genie (PRODUCTION MODE)")
        print("="*70)
        print(f"📍 Access at: https://your-domain.com")
        print(f"🔒 Encryption: ENABLED")
        print(f"🔒 HIPAA Mode: ACTIVE")
        print("="*70 + "\n")
    else:
        # Check virus scanner status in development
        from utils.virus_scanner import get_virus_scanner
        scanner = get_virus_scanner()
        scanner_status = "✅ ENABLED" if scanner.is_available() else "⚠️  DISABLED (install ClamAV for production)"

        print("\n" + "="*70)
        print(f"🚀 Starting Admissions Genie (DEMO VERSION)")
        print("="*70)
        print(f"📍 Access at: http://localhost:{port}")
        print(f"📧 Admin login: admin@admissionsgenie.com / admin123")
        print(f"📧 User login: user@admissionsgenie.com / user123")
        print(f"🦠 Virus Scanning: {scanner_status}")
        print("="*70 + "\n")

    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])

"""
Application configuration settings.
Loads configuration from environment variables with sensible defaults.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///admissions.db')

    # Azure OpenAI settings (HIPAA-compliant)
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4-turbo')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

    # File upload settings
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '50'))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'pdf,docx,doc,jpg,jpeg,png').split(','))
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')

    # AWS S3 settings (production file storage)
    USE_S3 = os.getenv('USE_S3', 'false').lower() == 'true'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'admissions-genie-uploads')
    AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'us-east-1')
    AWS_S3_ENCRYPTION = 'AES256'  # Server-side encryption

    # Celery/Redis settings (background tasks)
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Sentry error tracking
    SENTRY_DSN = os.getenv('SENTRY_DSN')

    # Session timeout (HIPAA requirement: 15 minutes idle)
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '15'))

    # PHI protection
    PHI_STRICT_MODE = os.getenv('PHI_STRICT_MODE', 'false').lower() == 'true'

    # Session settings
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', '3600'))
    )

    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Don't expire CSRF tokens

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per hour')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/admissions-genie.log')

    # Application-specific settings
    DEFAULT_LOS_ESTIMATE = 15  # Default length of stay in days
    SCORE_THRESHOLDS = {
        'accept': 70,  # Score >= 70 → Accept
        'defer': 40,   # Score 40-69 → Defer
        # Score < 40 → Decline
    }

    # Business weights defaults (can be overridden per facility)
    DEFAULT_BUSINESS_WEIGHTS = {
        'margin': 0.6,           # Weight for financial margin
        'census': 0.2,           # Weight for census priority
        'denial_risk': 0.3,      # Penalty weight for denial risk
        'complexity': 0.2,       # Penalty weight for care complexity
        'readmit_risk': 0.1      # Penalty weight for readmission risk
    }

    @staticmethod
    def init_app(app):
        """Initialize application with this config."""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    TESTING = False
    # Override with more secure settings in production
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    DATABASE_URL = 'sqlite:///:memory:'  # In-memory database for tests


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

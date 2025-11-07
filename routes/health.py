"""
Health check endpoints for monitoring and uptime tracking.
"""

from flask import Blueprint, jsonify
from datetime import datetime
from config.database import db
from config.settings import Config
import os

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'admissions-genie'
    }), 200


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with dependency status.
    Checks database, S3, Redis, and other critical services.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'admissions-genie',
        'version': '1.0.0',
        'checks': {}
    }

    # Check database connection
    try:
        db.execute_query("SELECT 1", fetch='one')
        health_status['checks']['database'] = {
            'status': 'healthy',
            'type': 'postgresql' if Config.DATABASE_URL.startswith('postgresql') else 'sqlite'
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'

    # Check S3 configuration
    if Config.USE_S3:
        try:
            # Just check if credentials are configured
            if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
                health_status['checks']['s3'] = {
                    'status': 'configured',
                    'bucket': Config.AWS_S3_BUCKET
                }
            else:
                health_status['checks']['s3'] = {
                    'status': 'misconfigured',
                    'error': 'AWS credentials not set'
                }
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks']['s3'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
    else:
        health_status['checks']['s3'] = {
            'status': 'disabled',
            'message': 'Using local file storage'
        }

    # Check Azure OpenAI configuration
    if Config.AZURE_OPENAI_API_KEY:
        health_status['checks']['azure_openai'] = {
            'status': 'configured',
            'endpoint': Config.AZURE_OPENAI_ENDPOINT,
            'deployment': Config.AZURE_OPENAI_DEPLOYMENT_NAME
        }
    else:
        health_status['checks']['azure_openai'] = {
            'status': 'not_configured',
            'message': 'Running in demo mode'
        }

    # Check Redis/Celery configuration
    if Config.CELERY_BROKER_URL and Config.CELERY_BROKER_URL != 'redis://localhost:6379/0':
        health_status['checks']['redis'] = {
            'status': 'configured',
            'message': 'Background processing enabled'
        }
    else:
        health_status['checks']['redis'] = {
            'status': 'not_configured',
            'message': 'Synchronous processing only'
        }

    # Check Sentry configuration
    if Config.SENTRY_DSN:
        health_status['checks']['sentry'] = {
            'status': 'configured',
            'message': 'Error tracking enabled'
        }
    else:
        health_status['checks']['sentry'] = {
            'status': 'not_configured',
            'message': 'Error tracking disabled'
        }

    # Determine overall status
    if health_status['status'] == 'healthy':
        status_code = 200
    else:
        status_code = 503  # Service Unavailable

    return jsonify(health_status), status_code


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 when service is ready to accept traffic.
    """
    # Check critical dependencies
    try:
        # Must be able to query database
        db.execute_query("SELECT 1", fetch='one')

        return jsonify({
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.
    Returns 200 if the application process is alive.
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat()
    }), 200

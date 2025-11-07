"""
Session timeout middleware for HIPAA compliance.
Automatically logs out users after 15 minutes of inactivity.
"""

from datetime import datetime, timedelta
from flask import session, redirect, url_for, flash, request
from functools import wraps
from config.settings import Config


def check_session_timeout():
    """
    Check if the current session has timed out.

    Returns:
        True if session is valid, False if timed out
    """
    if 'user_id' not in session:
        return True  # Not logged in, no timeout to check

    last_activity = session.get('last_activity')
    if not last_activity:
        # First request, set last activity
        session['last_activity'] = datetime.now().isoformat()
        return True

    # Parse last activity time
    try:
        last_activity_time = datetime.fromisoformat(last_activity)
    except (ValueError, TypeError):
        # Invalid format, reset session
        session.clear()
        return False

    # Check if session has timed out
    timeout_minutes = Config.SESSION_TIMEOUT_MINUTES
    if datetime.now() - last_activity_time > timedelta(minutes=timeout_minutes):
        return False

    # Update last activity time
    session['last_activity'] = datetime.now().isoformat()
    return True


def session_timeout_required(f):
    """
    Decorator to enforce session timeout on protected routes.
    Use this on routes that require authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_session_timeout():
            # Session has timed out
            session.clear()
            flash('Your session has expired due to inactivity. Please log in again.', 'warning')
            return redirect(url_for('auth.login', next=request.url))

        return f(*args, **kwargs)

    return decorated_function


def init_session_timeout(app):
    """
    Initialize session timeout middleware for the Flask app.
    This checks every request for timeout.
    """
    @app.before_request
    def before_request_timeout_check():
        # Skip timeout check for static files and login page
        if request.endpoint in ['static', 'auth.login', 'auth.logout']:
            return

        # Check session timeout for authenticated users
        if 'user_id' in session and not check_session_timeout():
            session.clear()
            flash('Your session has expired due to inactivity. Please log in again.', 'warning')
            return redirect(url_for('auth.login', next=request.url))


def get_session_time_remaining():
    """
    Get remaining time before session timeout in seconds.

    Returns:
        int: Seconds remaining before timeout, or None if not logged in
    """
    if 'user_id' not in session:
        return None

    last_activity = session.get('last_activity')
    if not last_activity:
        return Config.SESSION_TIMEOUT_MINUTES * 60

    try:
        last_activity_time = datetime.fromisoformat(last_activity)
        timeout_minutes = Config.SESSION_TIMEOUT_MINUTES
        timeout_time = last_activity_time + timedelta(minutes=timeout_minutes)
        remaining = (timeout_time - datetime.now()).total_seconds()
        return max(0, int(remaining))
    except (ValueError, TypeError):
        return None

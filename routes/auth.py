"""
Authentication routes for user login, logout, and registration.
Includes HIPAA-compliant account lockout protection.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime

from models.user import User
from utils.audit_logger import log_authentication, log_audit_event
from utils.password_validator import validate_password_strength
from utils.input_sanitizer import sanitize_email, sanitize_string

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        user = User.get_by_id(session['user_id'])
        if not user or not user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page and handler with account lockout protection.

    HIPAA Compliance: §164.308(a)(5)(ii)(D) - Access Control Protection
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('login.html')

        # Get user by email
        user = User.get_by_email(email)

        if not user:
            # HIPAA audit log: failed login attempt (user not found)
            log_authentication(None, False, reason='user_not_found')
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        # Check if account is locked
        if user.is_locked():
            minutes_left = int((user.locked_until - datetime.now()).total_seconds() / 60) + 1
            log_authentication(user.id, False, reason='account_locked')
            flash(f'Account is locked due to multiple failed login attempts. Please try again in {minutes_left} minutes.', 'danger')
            return render_template('login.html')

        # Check if account is active
        if not user.is_active:
            log_authentication(user.id, False, reason='account_inactive')
            flash('This account has been deactivated. Please contact an administrator.', 'danger')
            return render_template('login.html')

        # Verify password
        if user.verify_password(password):
            # Successful login - reset failed attempts
            user.reset_failed_logins()

            # SECURITY: Regenerate session ID to prevent session fixation attacks
            # This is critical for HIPAA compliance (§164.312(a)(1) - Access Control)
            session.clear()  # Clear any pre-existing session data
            session.permanent = True  # Make session permanent (with timeout)

            # Set session with new session ID
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_role'] = user.role
            session['facility_id'] = user.facility_id

            # Update last login
            user.update_last_login()

            # HIPAA audit log: successful login
            log_authentication(user.id, True)

            flash(f'Welcome back, {user.full_name or user.email}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Failed login - record attempt
            user.record_failed_login()

            # HIPAA audit log: failed login attempt
            log_authentication(user.id, False, reason='invalid_password')

            if user.is_locked():
                flash('Too many failed login attempts. Your account has been locked for 30 minutes.', 'danger')
            else:
                remaining_attempts = 5 - user.failed_login_attempts
                if remaining_attempts <= 2:
                    flash(f'Invalid email or password. {remaining_attempts} attempts remaining before lockout.', 'danger')
                else:
                    flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page and handler with input sanitization."""
    if request.method == 'POST':
        # SECURITY: Sanitize all user inputs to prevent XSS attacks
        email = sanitize_email(request.form.get('email', ''))
        password = request.form.get('password', '')  # Don't sanitize passwords - they're hashed
        confirm_password = request.form.get('confirm_password', '')
        full_name = sanitize_string(request.form.get('full_name', ''))
        facility_id = request.form.get('facility_id')

        # Validation
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # HIPAA Compliance: Enforce strong password requirements
        is_valid, password_errors = validate_password_strength(password)
        if not is_valid:
            for error in password_errors:
                flash(error, 'danger')
            return render_template('register.html')

        # Check if user already exists
        existing_user = User.get_by_email(email)
        if existing_user:
            flash('An account with this email already exists.', 'danger')
            return render_template('register.html')

        # Create new user
        try:
            facility_id_int = int(facility_id) if facility_id else None
            user = User.create(
                organization_id=1,  # Default to first organization (demo)
                email=email,
                password=password,
                full_name=full_name,
                facility_id=facility_id_int,
                role=User.USER  # Default to regular user
            )

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')

    # Get facilities for dropdown
    from models.facility import Facility
    # For registration, we need a default organization (will be improved with proper org selection)
    # For now, get facilities from organization_id=1 (default organization)
    facilities = Facility.get_all(organization_id=1)

    return render_template('register.html', facilities=facilities)


@auth_bp.route('/logout')
def logout():
    """User logout handler."""
    # HIPAA audit log: logout (before clearing session)
    if 'user_id' in session:
        log_authentication(session['user_id'], True, reason='logout')

    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with input sanitization."""
    user = User.get_by_id(session['user_id'])

    if request.method == 'POST':
        # SECURITY: Sanitize user inputs
        full_name = sanitize_string(request.form.get('full_name', ''))
        facility_id = request.form.get('facility_id')

        try:
            facility_id_int = int(facility_id) if facility_id else None
            user.update_profile(full_name=full_name, facility_id=facility_id_int)

            session['facility_id'] = facility_id_int
            flash('Profile updated successfully!', 'success')

        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'danger')

        return redirect(url_for('auth.profile'))

    # Get facilities for dropdown
    from models.facility import Facility
    facilities = Facility.get_all(organization_id=user.organization_id)

    return render_template('profile.html', user=user, facilities=facilities)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page."""
    user = User.get_by_id(session['user_id'])

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not current_password or not new_password:
            flash('All fields are required.', 'danger')
            return render_template('change_password.html')

        if not user.verify_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('change_password.html')

        # HIPAA Compliance: Enforce strong password requirements
        is_valid, password_errors = validate_password_strength(new_password)
        if not is_valid:
            for error in password_errors:
                flash(error, 'danger')
            return render_template('change_password.html')

        # Update password
        try:
            user.update_password(new_password)

            # HIPAA audit log: password change
            log_audit_event(
                action='password_changed',
                resource_type='user',
                resource_id=user.id
            )

            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))

        except Exception as e:
            flash(f'Error changing password: {str(e)}', 'danger')

    return render_template('change_password.html')

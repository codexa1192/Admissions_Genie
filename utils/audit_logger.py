"""
HIPAA-compliant audit logging system.
Tracks all PHI access, authentication events, and configuration changes.
"""

import json
from datetime import datetime
from functools import wraps
from flask import request, session, g
from config.database import db


def log_audit_event(action: str, resource_type: str = None, resource_id: int = None,
                    changes: dict = None, user_id: int = None):
    """
    Log an audit event to the database.

    Args:
        action: Action performed (e.g., 'admission_viewed', 'user_login', 'rate_updated')
        resource_type: Type of resource accessed (e.g., 'admission', 'facility', 'rate')
        resource_id: ID of the resource
        changes: Dict of changes made (for update/delete actions)
        user_id: ID of user performing action (defaults to current session user)
    """
    # Get user ID from current session if not provided
    if user_id is None:
        user_id = session.get('user_id')

    # Get request context
    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get('User-Agent') if request else None

    # Serialize changes to JSON
    changes_json = json.dumps(changes) if changes else None

    # Insert audit log
    query = """
    INSERT INTO audit_logs
    (user_id, action, resource_type, resource_id, changes, ip_address, user_agent, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    db.execute_query(
        query,
        (user_id, action, resource_type, resource_id, changes_json, ip_address, user_agent, datetime.now()),
        fetch='none'
    )


def audit_log(action: str, resource_type: str = None):
    """
    Decorator to automatically audit log function calls.

    Usage:
        @audit_log('admission_viewed', 'admission')
        def view_admission(admission_id):
            ...

    Args:
        action: Action being performed
        resource_type: Type of resource being accessed
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function
            result = f(*args, **kwargs)

            # Try to extract resource ID from kwargs or args
            resource_id = kwargs.get('id') or kwargs.get('admission_id') or kwargs.get('facility_id') or kwargs.get('payer_id')
            if not resource_id and args:
                # Try first argument if it's an integer
                try:
                    resource_id = int(args[0])
                except (ValueError, IndexError):
                    resource_id = None

            # Log the audit event
            log_audit_event(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id
            )

            return result
        return decorated_function
    return decorator


def log_authentication(user_id: int, success: bool, reason: str = None):
    """
    Log authentication attempt.

    Args:
        user_id: ID of user attempting authentication
        success: Whether authentication was successful
        reason: Reason for failure (if applicable)
    """
    action = 'user_login_success' if success else 'user_login_failed'
    changes = {'reason': reason} if reason else None

    log_audit_event(
        action=action,
        resource_type='user',
        resource_id=user_id,
        changes=changes
    )


def log_phi_access(resource_type: str, resource_id: int, field_accessed: str = None):
    """
    Log access to Protected Health Information.

    Args:
        resource_type: Type of PHI resource (e.g., 'admission', 'extracted_data')
        resource_id: ID of the resource
        field_accessed: Specific PHI field accessed (optional)
    """
    changes = {'field': field_accessed} if field_accessed else None

    log_audit_event(
        action='phi_accessed',
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes
    )


def log_configuration_change(config_type: str, config_id: int, old_value: dict, new_value: dict):
    """
    Log configuration changes.

    Args:
        config_type: Type of configuration (e.g., 'rate', 'cost_model', 'facility')
        config_id: ID of configuration
        old_value: Old configuration values
        new_value: New configuration values
    """
    changes = {
        'old': old_value,
        'new': new_value
    }

    log_audit_event(
        action=f'{config_type}_updated',
        resource_type=config_type,
        resource_id=config_id,
        changes=changes
    )


def get_audit_logs(filters: dict = None, limit: int = 100, offset: int = 0):
    """
    Retrieve audit logs with optional filtering.

    Args:
        filters: Dict of filters (e.g., {'user_id': 1, 'action': 'admission_viewed'})
        limit: Maximum number of records to return
        offset: Number of records to skip

    Returns:
        List of audit log records
    """
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []

    if filters:
        if 'user_id' in filters:
            query += " AND user_id = ?"
            params.append(filters['user_id'])

        if 'action' in filters:
            query += " AND action = ?"
            params.append(filters['action'])

        if 'resource_type' in filters:
            query += " AND resource_type = ?"
            params.append(filters['resource_type'])

        if 'resource_id' in filters:
            query += " AND resource_id = ?"
            params.append(filters['resource_id'])

        if 'start_date' in filters:
            query += " AND created_at >= ?"
            params.append(filters['start_date'])

        if 'end_date' in filters:
            query += " AND created_at <= ?"
            params.append(filters['end_date'])

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return db.execute_query(query, tuple(params), fetch='all')


def get_audit_summary(user_id: int = None, days: int = 30):
    """
    Get summary statistics of audit events.

    Args:
        user_id: Filter by specific user (optional)
        days: Number of days to look back

    Returns:
        Dict with summary statistics
    """
    query = """
    SELECT
        action,
        COUNT(*) as count
    FROM audit_logs
    WHERE created_at >= datetime('now', '-' || ? || ' days')
    """
    params = [days]

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    query += " GROUP BY action ORDER BY count DESC"

    results = db.execute_query(query, tuple(params), fetch='all')

    return {row['action']: row['count'] for row in results}

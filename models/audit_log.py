"""
Audit Log model for tracking all significant actions in the system.
Provides comprehensive audit trail for compliance and troubleshooting.
"""

from typing import Optional, List, Dict
from datetime import datetime
import json
from config.database import db


class AuditLog:
    """Audit log entry for tracking system actions."""

    # Action types
    ACTION_ADMISSION_CREATED = 'admission_created'
    ACTION_ADMISSION_UPDATED = 'admission_updated'
    ACTION_ADMISSION_DECISION = 'admission_decision'
    ACTION_USER_LOGIN = 'user_login'
    ACTION_USER_LOGOUT = 'user_logout'
    ACTION_RATE_UPDATED = 'rate_updated'
    ACTION_FACILITY_UPDATED = 'facility_updated'
    ACTION_COST_MODEL_UPDATED = 'cost_model_updated'
    ACTION_FILE_UPLOADED = 'file_uploaded'
    ACTION_REPORT_GENERATED = 'report_generated'

    ALL_ACTIONS = [
        ACTION_ADMISSION_CREATED,
        ACTION_ADMISSION_UPDATED,
        ACTION_ADMISSION_DECISION,
        ACTION_USER_LOGIN,
        ACTION_USER_LOGOUT,
        ACTION_RATE_UPDATED,
        ACTION_FACILITY_UPDATED,
        ACTION_COST_MODEL_UPDATED,
        ACTION_FILE_UPLOADED,
        ACTION_REPORT_GENERATED
    ]

    def __init__(self, id: Optional[int] = None, user_id: Optional[int] = None,
                 action: str = '', resource_type: Optional[str] = None,
                 resource_id: Optional[int] = None, changes: Optional[Dict] = None,
                 ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                 created_at: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.changes = changes or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = created_at or datetime.utcnow()

    @classmethod
    def create(cls, user_id: int, action: str, resource_type: Optional[str] = None,
               resource_id: Optional[int] = None, changes: Optional[Dict] = None,
               ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> 'AuditLog':
        """
        Create a new audit log entry.

        Args:
            user_id: ID of the user performing the action
            action: Action type (use ACTION_* constants)
            resource_type: Type of resource being acted upon (e.g., 'admission', 'facility')
            resource_id: ID of the resource
            changes: Dictionary of changes made (for updates)
            ip_address: IP address of the request
            user_agent: User agent string from the request

        Returns:
            AuditLog instance with assigned ID
        """
        if action not in cls.ALL_ACTIONS:
            raise ValueError(f"Invalid action type. Must be one of: {cls.ALL_ACTIONS}")

        changes_json = json.dumps(changes or {})
        created_at = datetime.utcnow()

        query = """
            INSERT INTO audit_logs
            (user_id, action, resource_type, resource_id, changes, ip_address, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        log_id = db.execute_query(
            query,
            (user_id, action, resource_type, resource_id, changes_json, ip_address, user_agent, created_at),
            fetch='none'
        )

        return cls(
            id=log_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=created_at
        )

    @classmethod
    def get_by_id(cls, log_id: int) -> Optional['AuditLog']:
        """Get audit log entry by ID."""
        query = "SELECT * FROM audit_logs WHERE id = ?"
        result = db.execute_query(query, (log_id,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_by_user(cls, user_id: int, limit: int = 100, offset: int = 0) -> List['AuditLog']:
        """Get audit logs for a specific user."""
        query = """
            SELECT * FROM audit_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        results = db.execute_query(query, (user_id, limit, offset))
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def get_by_resource(cls, resource_type: str, resource_id: int, limit: int = 100) -> List['AuditLog']:
        """Get audit logs for a specific resource."""
        query = """
            SELECT * FROM audit_logs
            WHERE resource_type = ? AND resource_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        results = db.execute_query(query, (resource_type, resource_id, limit))
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def get_by_action(cls, action: str, limit: int = 100, offset: int = 0) -> List['AuditLog']:
        """Get audit logs for a specific action type."""
        query = """
            SELECT * FROM audit_logs
            WHERE action = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        results = db.execute_query(query, (action, limit, offset))
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def get_recent(cls, limit: int = 100, offset: int = 0) -> List['AuditLog']:
        """Get recent audit logs."""
        query = """
            SELECT * FROM audit_logs
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        results = db.execute_query(query, (limit, offset))
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def search(cls, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
               user_id: Optional[int] = None, action: Optional[str] = None,
               resource_type: Optional[str] = None, limit: int = 100) -> List['AuditLog']:
        """
        Search audit logs with multiple filters.

        Args:
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            user_id: Filter by user
            action: Filter by action type
            resource_type: Filter by resource type
            limit: Maximum number of results

        Returns:
            List of matching audit logs
        """
        conditions = []
        params = []

        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        if action:
            conditions.append("action = ?")
            params.append(action)

        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM audit_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(limit)

        results = db.execute_query(query, tuple(params))
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def get_statistics(cls, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict:
        """
        Get audit log statistics for a date range.

        Returns:
            Dictionary with statistics (total_events, events_by_action, events_by_user, etc.)
        """
        conditions = []
        params = []

        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Total events
        total_query = f"SELECT COUNT(*) as count FROM audit_logs WHERE {where_clause}"
        total_result = db.execute_query(total_query, tuple(params), fetch='one')
        total_events = total_result['count'] if total_result else 0

        # Events by action
        action_query = f"""
            SELECT action, COUNT(*) as count
            FROM audit_logs
            WHERE {where_clause}
            GROUP BY action
            ORDER BY count DESC
        """
        action_results = db.execute_query(action_query, tuple(params))
        events_by_action = {row['action']: row['count'] for row in action_results}

        # Events by user (top 10)
        user_query = f"""
            SELECT user_id, COUNT(*) as count
            FROM audit_logs
            WHERE {where_clause}
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
        """
        user_results = db.execute_query(user_query, tuple(params))
        events_by_user = {row['user_id']: row['count'] for row in user_results}

        return {
            'total_events': total_events,
            'events_by_action': events_by_action,
            'events_by_user': events_by_user,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }

    @classmethod
    def _from_db_row(cls, row) -> 'AuditLog':
        """Create AuditLog instance from database row."""
        changes = json.loads(row['changes']) if row['changes'] else {}
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            action=row['action'],
            resource_type=row['resource_type'],
            resource_id=row['resource_id'],
            changes=changes,
            ip_address=row['ip_address'],
            user_agent=row['user_agent'],
            created_at=row['created_at']
        )

    def to_dict(self) -> Dict:
        """Convert audit log to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'changes': self.changes,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} by User {self.user_id} at {self.created_at}>"

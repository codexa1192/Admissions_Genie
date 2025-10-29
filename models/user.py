"""
User model for authentication and access control.
"""

import bcrypt
from typing import Optional, List, Dict
from datetime import datetime
from config.database import db


class User:
    """Represents a user of the Admissions Genie system."""

    # Role constants
    USER = 'user'
    ADMIN = 'admin'

    ROLES = [USER, ADMIN]

    def __init__(self, id: Optional[int] = None, email: str = '', password_hash: str = '',
                 full_name: Optional[str] = None, facility_id: Optional[int] = None,
                 role: str = USER, is_active: bool = True, created_at: Optional[datetime] = None,
                 last_login: Optional[datetime] = None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.facility_id = facility_id
        self.role = role
        self.is_active = is_active
        self.created_at = created_at
        self.last_login = last_login

    @classmethod
    def create(cls, email: str, password: str, full_name: Optional[str] = None,
               facility_id: Optional[int] = None, role: str = USER) -> 'User':
        """
        Create a new user.

        Args:
            email: User email (unique)
            password: Plain text password (will be hashed)
            full_name: User's full name
            facility_id: ID of associated facility (optional)
            role: User role (default: 'user')

        Returns:
            User instance with assigned ID
        """
        if role not in cls.ROLES:
            raise ValueError(f"Invalid role. Must be one of: {cls.ROLES}")

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        query = """
            INSERT INTO users (email, password_hash, full_name, facility_id, role)
            VALUES (?, ?, ?, ?, ?)
        """

        user_id = db.execute_query(
            query,
            (email, password_hash, full_name, facility_id, role),
            fetch='none'
        )

        return cls(
            id=user_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            facility_id=facility_id,
            role=role
        )

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = ?"
        result = db.execute_query(query, (user_id,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = ?"
        result = db.execute_query(query, (email,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_all(cls, facility_id: Optional[int] = None, role: Optional[str] = None) -> List['User']:
        """
        Get all users, optionally filtered by facility or role.

        Args:
            facility_id: Optional facility ID to filter by
            role: Optional role to filter by

        Returns:
            List of User instances
        """
        if facility_id and role:
            query = "SELECT * FROM users WHERE facility_id = ? AND role = ? ORDER BY email"
            results = db.execute_query(query, (facility_id, role))
        elif facility_id:
            query = "SELECT * FROM users WHERE facility_id = ? ORDER BY email"
            results = db.execute_query(query, (facility_id,))
        elif role:
            query = "SELECT * FROM users WHERE role = ? ORDER BY email"
            results = db.execute_query(query, (role,))
        else:
            query = "SELECT * FROM users ORDER BY email"
            results = db.execute_query(query)

        return [cls._from_db_row(row) for row in results]

    @classmethod
    def _from_db_row(cls, row) -> 'User':
        """Create User instance from database row."""
        return cls(
            id=row['id'],
            email=row['email'],
            password_hash=row['password_hash'],
            full_name=row['full_name'],
            facility_id=row['facility_id'],
            role=row['role'],
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            last_login=row['last_login']
        )

    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def update_password(self, new_password: str):
        """Update user password."""
        self.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        query = "UPDATE users SET password_hash = ? WHERE id = ?"
        db.execute_query(query, (self.password_hash, self.id), fetch='none')

    def update_profile(self, full_name: Optional[str] = None, facility_id: Optional[int] = None):
        """Update user profile information."""
        if full_name is not None:
            self.full_name = full_name
        if facility_id is not None:
            self.facility_id = facility_id

        query = "UPDATE users SET full_name = ?, facility_id = ? WHERE id = ?"
        db.execute_query(query, (self.full_name, self.facility_id, self.id), fetch='none')

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now()
        query = "UPDATE users SET last_login = ? WHERE id = ?"
        db.execute_query(query, (self.last_login, self.id), fetch='none')

    def deactivate(self):
        """Deactivate user account."""
        self.is_active = False
        query = "UPDATE users SET is_active = 0 WHERE id = ?"
        db.execute_query(query, (self.id,), fetch='none')

    def activate(self):
        """Activate user account."""
        self.is_active = True
        query = "UPDATE users SET is_active = 1 WHERE id = ?"
        db.execute_query(query, (self.id,), fetch='none')

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == self.ADMIN

    def to_dict(self, include_sensitive: bool = False) -> Dict:
        """
        Convert user to dictionary.

        Args:
            include_sensitive: Whether to include sensitive data like password hash

        Returns:
            Dictionary representation of user
        """
        data = {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'facility_id': self.facility_id,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': str(self.created_at) if self.created_at else None,
            'last_login': str(self.last_login) if self.last_login else None
        }

        if include_sensitive:
            data['password_hash'] = self.password_hash

        return data

    def __repr__(self):
        return f"<User {self.id}: {self.email} ({self.role})>"

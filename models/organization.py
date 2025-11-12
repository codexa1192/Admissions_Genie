"""
Organization model for multi-tenant SaaS architecture.
Each SNF customer is an organization with isolated data.
"""

import json
from typing import Optional, List, Dict
from datetime import datetime
from config.database import db


class Organization:
    """Represents a customer organization (SNF or SNF chain)."""

    # Subscription tiers
    TIER_TRIAL = 'trial'
    TIER_STARTER = 'starter'
    TIER_PROFESSIONAL = 'professional'
    TIER_ENTERPRISE = 'enterprise'

    TIERS = [TIER_TRIAL, TIER_STARTER, TIER_PROFESSIONAL, TIER_ENTERPRISE]

    def __init__(self, id: Optional[int] = None, name: Optional[str] = None,
                 subdomain: Optional[str] = None, subscription_tier: str = TIER_TRIAL,
                 settings: Optional[Dict] = None, stripe_customer_id: Optional[str] = None,
                 is_active: bool = True, trial_ends_at: Optional[datetime] = None,
                 created_at: Optional[datetime] = None):
        self.id = id
        self.name = name
        self.subdomain = subdomain
        self.subscription_tier = subscription_tier
        self.settings = settings or {}
        self.stripe_customer_id = stripe_customer_id
        self.is_active = is_active
        self.trial_ends_at = trial_ends_at
        self.created_at = created_at or datetime.now()

    @classmethod
    def create(cls, name: str, subdomain: str, subscription_tier: str = TIER_TRIAL,
               settings: Optional[Dict] = None) -> 'Organization':
        """
        Create a new organization (tenant).

        Args:
            name: Organization name (e.g., "Sunrise Senior Living")
            subdomain: Unique subdomain (e.g., "sunrise" for sunrise.admissionsgenie.com)
            subscription_tier: Subscription level (trial, starter, professional, enterprise)
            settings: JSON settings (feature flags, usage limits, branding)

        Returns:
            Organization instance with assigned ID
        """
        # Validate tier
        if subscription_tier not in cls.TIERS:
            raise ValueError(f"Invalid subscription tier. Must be one of: {cls.TIERS}")

        # Normalize subdomain
        subdomain = subdomain.lower().strip()

        # Check if subdomain already exists
        existing = cls.get_by_subdomain(subdomain)
        if existing:
            raise ValueError(f"Subdomain '{subdomain}' is already taken")

        settings_json = json.dumps(settings or {})

        # Set trial end date (14 days from now)
        from datetime import timedelta
        trial_ends_at = datetime.now() + timedelta(days=14)

        query = """
            INSERT INTO organizations (
                name, subdomain, subscription_tier, settings,
                is_active, trial_ends_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """

        org_id = db.execute_query(
            query,
            (name, subdomain, subscription_tier, settings_json, 1, trial_ends_at),  # Use 1 instead of True for PostgreSQL
            fetch='none'
        )

        return cls(
            id=org_id,
            name=name,
            subdomain=subdomain,
            subscription_tier=subscription_tier,
            settings=settings,
            is_active=True,
            trial_ends_at=trial_ends_at
        )

    @classmethod
    def get_by_id(cls, org_id: int) -> Optional['Organization']:
        """Get organization by ID."""
        query = "SELECT * FROM organizations WHERE id = ?"
        result = db.execute_query(query, (org_id,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_by_subdomain(cls, subdomain: str) -> Optional['Organization']:
        """Get organization by subdomain."""
        query = "SELECT * FROM organizations WHERE subdomain = ?"
        result = db.execute_query(query, (subdomain.lower(),), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_all(cls, active_only: bool = True) -> List['Organization']:
        """Get all organizations."""
        if active_only:
            query = "SELECT * FROM organizations WHERE is_active = ? ORDER BY created_at DESC"
            results = db.execute_query(query, (True,))
        else:
            query = "SELECT * FROM organizations ORDER BY created_at DESC"
            results = db.execute_query(query)

        return [cls._from_db_row(row) for row in results]

    @classmethod
    def _from_db_row(cls, row) -> 'Organization':
        """Create Organization instance from database row."""
        settings = json.loads(row['settings']) if row['settings'] else {}

        # Parse datetime strings
        created_at = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        trial_ends_at = datetime.fromisoformat(row['trial_ends_at']) if row.get('trial_ends_at') else None

        return cls(
            id=row['id'],
            name=row['name'],
            subdomain=row['subdomain'],
            subscription_tier=row['subscription_tier'],
            settings=settings,
            stripe_customer_id=row.get('stripe_customer_id'),
            is_active=bool(row['is_active']),
            trial_ends_at=trial_ends_at,
            created_at=created_at
        )

    def update(self, name: Optional[str] = None, subscription_tier: Optional[str] = None,
               settings: Optional[Dict] = None, stripe_customer_id: Optional[str] = None,
               is_active: Optional[bool] = None):
        """Update organization details."""
        if name is not None:
            self.name = name
        if subscription_tier is not None:
            if subscription_tier not in self.TIERS:
                raise ValueError(f"Invalid subscription tier. Must be one of: {self.TIERS}")
            self.subscription_tier = subscription_tier
        if settings is not None:
            self.settings = settings
        if stripe_customer_id is not None:
            self.stripe_customer_id = stripe_customer_id
        if is_active is not None:
            self.is_active = is_active

        settings_json = json.dumps(self.settings)

        query = """
            UPDATE organizations
            SET name = ?, subscription_tier = ?, settings = ?,
                stripe_customer_id = ?, is_active = ?
            WHERE id = ?
        """

        db.execute_query(
            query,
            (self.name, self.subscription_tier, settings_json,
             self.stripe_customer_id, 1 if self.is_active else 0, self.id),  # Convert bool to int for PostgreSQL
            fetch='none'
        )

    def get_usage_limits(self) -> Dict:
        """Get usage limits based on subscription tier."""
        limits = {
            self.TIER_TRIAL: {
                'max_facilities': 1,
                'max_users': 5,
                'max_admissions_per_month': 20,
                'api_calls_per_hour': 50
            },
            self.TIER_STARTER: {
                'max_facilities': 1,
                'max_users': 10,
                'max_admissions_per_month': 50,
                'api_calls_per_hour': 100
            },
            self.TIER_PROFESSIONAL: {
                'max_facilities': 5,
                'max_users': 50,
                'max_admissions_per_month': 200,
                'api_calls_per_hour': 1000
            },
            self.TIER_ENTERPRISE: {
                'max_facilities': 999999,  # Unlimited
                'max_users': 999999,
                'max_admissions_per_month': 999999,
                'api_calls_per_hour': 5000
            }
        }

        return limits.get(self.subscription_tier, limits[self.TIER_TRIAL])

    def is_trial_expired(self) -> bool:
        """Check if trial period has expired."""
        if self.subscription_tier != self.TIER_TRIAL:
            return False
        if not self.trial_ends_at:
            return False
        return datetime.now() > self.trial_ends_at

    def can_create_facility(self, current_count: int) -> bool:
        """Check if organization can create another facility."""
        limits = self.get_usage_limits()
        return current_count < limits['max_facilities']

    def can_create_user(self, current_count: int) -> bool:
        """Check if organization can create another user."""
        limits = self.get_usage_limits()
        return current_count < limits['max_users']

    def can_process_admission(self, current_month_count: int) -> bool:
        """Check if organization can process another admission this month."""
        limits = self.get_usage_limits()
        return current_month_count < limits['max_admissions_per_month']

    def to_dict(self) -> Dict:
        """Convert organization to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'subdomain': self.subdomain,
            'subscription_tier': self.subscription_tier,
            'settings': self.settings,
            'stripe_customer_id': self.stripe_customer_id,
            'is_active': self.is_active,
            'trial_ends_at': str(self.trial_ends_at) if self.trial_ends_at else None,
            'created_at': str(self.created_at) if self.created_at else None,
            'usage_limits': self.get_usage_limits()
        }

    def __repr__(self):
        return f"<Organization {self.id}: {self.name} ({self.subscription_tier})>"

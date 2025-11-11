"""
Database configuration and connection management.
Supports both SQLite (development) and PostgreSQL (production).
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional
from config.settings import Config

# Only import psycopg if we're actually using PostgreSQL
# Using psycopg v3 (compatible with Python 3.13)
try:
    import psycopg
    from psycopg.rows import dict_row
    HAS_PSYCOPG = True
except ImportError:
    HAS_PSYCOPG = False


class Database:
    """Database connection manager supporting SQLite and PostgreSQL."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection manager.

        Args:
            database_url: Database connection string (defaults to Config.DATABASE_URL)
        """
        self.database_url = database_url or Config.DATABASE_URL
        self.is_postgres = self.database_url.startswith('postgresql://')

    def _convert_placeholders(self, query: str) -> str:
        """
        Convert SQLite-style ? placeholders to PostgreSQL-style %s placeholders.

        Args:
            query: SQL query with ? placeholders

        Returns:
            Query with appropriate placeholders for the database type
        """
        if self.is_postgres:
            return query.replace('?', '%s')
        return query

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Automatically handles commit/rollback and connection cleanup.

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM facilities")
                results = cursor.fetchall()
        """
        if self.is_postgres:
            if not HAS_PSYCOPG:
                raise ImportError("psycopg is required for PostgreSQL connections but is not installed")
            conn = psycopg.connect(self.database_url, row_factory=dict_row)
        else:
            # Extract path from sqlite:///path/to/db
            db_path = self.database_url.replace('sqlite:///', '')
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Return dict-like rows

        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: str = 'all'):
        """
        Execute a query and return results.

        Args:
            query: SQL query string (with ? placeholders, auto-converted for PostgreSQL)
            params: Query parameters (optional)
            fetch: 'all', 'one', or 'none' (default: 'all')

        Returns:
            Query results based on fetch parameter
        """
        # For PostgreSQL INSERTs, add RETURNING id to get the inserted ID
        is_insert = 'INSERT INTO' in query.upper()
        if fetch == 'none' and self.is_postgres and is_insert:
            if 'RETURNING' not in query.upper():
                query = query.rstrip('; \n') + ' RETURNING id'

        query = self._convert_placeholders(query)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if fetch == 'all':
                return cursor.fetchall()
            elif fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'none':
                if self.is_postgres and is_insert:
                    # PostgreSQL INSERT: fetch the RETURNING id result
                    result = cursor.fetchone()
                    return result['id'] if result else None
                elif not self.is_postgres and is_insert:
                    # SQLite INSERT: use lastrowid
                    return cursor.lastrowid
                else:
                    # UPDATE/DELETE or other non-INSERT: return None
                    return None
            else:
                raise ValueError(f"Invalid fetch parameter: {fetch}")

    def execute_many(self, query: str, params_list: list):
        """
        Execute a query multiple times with different parameters.

        Args:
            query: SQL query string (with ? placeholders, auto-converted for PostgreSQL)
            params_list: List of parameter tuples
        """
        query = self._convert_placeholders(query)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)


def init_db(database_url: Optional[str] = None):
    """
    Initialize database schema.
    Creates all necessary tables if they don't exist.

    Args:
        database_url: Database connection string (defaults to Config.DATABASE_URL)
    """
    db = Database(database_url)

    # SQL schema (compatible with both SQLite and PostgreSQL)
    schema = """
    -- Organizations table (MULTI-TENANT: Each SNF customer is an organization)
    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        subdomain TEXT UNIQUE NOT NULL,  -- For subdomain routing (acme.admissionsgenie.com)
        subscription_tier TEXT NOT NULL DEFAULT 'trial',  -- trial, starter, professional, enterprise
        settings TEXT,  -- JSON string: feature flags, usage limits, branding
        stripe_customer_id TEXT UNIQUE,  -- Stripe customer ID for billing
        is_active INTEGER DEFAULT 1,
        trial_ends_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Facilities table (MULTI-TENANT: Add organization_id)
    CREATE TABLE IF NOT EXISTS facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,  -- MULTI-TENANT: Tenant isolation
        name TEXT NOT NULL,
        wage_index REAL,
        vbp_multiplier REAL,
        capabilities TEXT,  -- JSON string
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
    );

    -- Payers table (MULTI-TENANT: Organization-specific payers)
    CREATE TABLE IF NOT EXISTS payers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,  -- MULTI-TENANT: Tenant isolation
        type TEXT NOT NULL,  -- 'Medicare FFS', 'MA', 'Medicaid FFS', 'Family Care', 'Commercial'
        plan_name TEXT,
        network_status TEXT,  -- 'in_network', 'out_of_network', 'single_case'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
    );

    -- Rates table (MULTI-TENANT: Organization-specific rates)
    CREATE TABLE IF NOT EXISTS rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,  -- MULTI-TENANT: Tenant isolation
        facility_id INTEGER,
        payer_id INTEGER,
        payer_type TEXT NOT NULL,  -- 'medicare_ffs', 'ma_commercial', 'medicaid_wi', 'family_care_wi'
        rate_data TEXT NOT NULL,  -- JSON string with rate structure
        effective_date DATE NOT NULL,
        end_date DATE,
        FOREIGN KEY (organization_id) REFERENCES organizations (id),
        FOREIGN KEY (facility_id) REFERENCES facilities (id),
        FOREIGN KEY (payer_id) REFERENCES payers (id)
    );

    -- Cost models table (MULTI-TENANT: Organization-specific cost models)
    CREATE TABLE IF NOT EXISTS cost_models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,  -- MULTI-TENANT: Tenant isolation
        facility_id INTEGER,
        acuity_band TEXT NOT NULL,  -- 'low', 'medium', 'high', 'complex'
        nursing_hours REAL NOT NULL,
        hourly_rate REAL NOT NULL,
        supply_cost REAL NOT NULL,
        pharmacy_addon REAL,
        transport_cost REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations (id),
        FOREIGN KEY (facility_id) REFERENCES facilities (id)
    );

    -- Business weights table (MULTI-TENANT: Organization-specific weights)
    CREATE TABLE IF NOT EXISTS business_weights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,  -- MULTI-TENANT: Tenant isolation
        facility_id INTEGER,
        version INTEGER NOT NULL,
        weights TEXT NOT NULL,  -- JSON string
        effective_date DATE NOT NULL,
        created_by INTEGER,
        UNIQUE (facility_id, version),
        FOREIGN KEY (organization_id) REFERENCES organizations (id),
        FOREIGN KEY (facility_id) REFERENCES facilities (id)
    );

    -- Admissions table (PHI-FREE MODE + MULTI-TENANT)
    CREATE TABLE IF NOT EXISTS admissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,  -- MULTI-TENANT: Tenant isolation
        facility_id INTEGER NOT NULL,
        payer_id INTEGER NOT NULL,
        case_number TEXT UNIQUE,  -- Auto-generated case ID (NO PHI)
        uploaded_files TEXT,  -- JSON string: file paths (DELETED after processing)
        extracted_data TEXT,  -- JSON string: DEPRECATED - PHI not stored
        pdpm_groups TEXT,  -- JSON string: PT, OT, SLP, Nursing groups (DE-IDENTIFIED)
        projected_revenue REAL,
        projected_cost REAL,
        projected_los INTEGER,
        margin_score INTEGER,  -- 0-100
        recommendation TEXT,  -- 'Accept', 'Defer', 'Decline'
        explanation TEXT,  -- JSON string: detailed breakdown
        actual_decision TEXT,  -- Actual decision made by staff
        decided_by INTEGER,
        decided_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (facility_id) REFERENCES facilities (id),
        FOREIGN KEY (payer_id) REFERENCES payers (id)
    );

    -- Users table (MULTI-TENANT: Users belong to organizations)
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,  -- MULTI-TENANT: Tenant isolation
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        facility_id INTEGER,
        role TEXT DEFAULT 'user',  -- 'user', 'admin'
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations (id),
        FOREIGN KEY (facility_id) REFERENCES facilities (id)
    );

    -- Audit logs table (MULTI-TENANT: Organization-scoped audit trail)
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,  -- MULTI-TENANT: Tenant isolation
        user_id INTEGER,
        action TEXT NOT NULL,  -- Action type (admission_created, user_login, etc.)
        resource_type TEXT,  -- Type of resource (admission, facility, rate, etc.)
        resource_id INTEGER,  -- ID of the resource
        changes TEXT,  -- JSON string with detailed changes
        ip_address TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );

    -- Create indexes for common queries (MULTI-TENANT: Organization-scoped)
    -- Organization indexes (CRITICAL for multi-tenant performance)
    CREATE INDEX IF NOT EXISTS idx_facilities_org ON facilities(organization_id);
    CREATE INDEX IF NOT EXISTS idx_payers_org ON payers(organization_id);
    CREATE INDEX IF NOT EXISTS idx_rates_org ON rates(organization_id);
    CREATE INDEX IF NOT EXISTS idx_cost_models_org ON cost_models(organization_id);
    CREATE INDEX IF NOT EXISTS idx_business_weights_org ON business_weights(organization_id);
    CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id);

    -- Admissions indexes (most queried table)
    CREATE INDEX IF NOT EXISTS idx_admissions_org_created ON admissions(organization_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_admissions_facility ON admissions(facility_id);
    CREATE INDEX IF NOT EXISTS idx_admissions_payer ON admissions(payer_id);
    CREATE INDEX IF NOT EXISTS idx_admissions_created ON admissions(created_at);

    -- Other common query indexes
    CREATE INDEX IF NOT EXISTS idx_rates_facility_payer ON rates(facility_id, payer_id);
    CREATE INDEX IF NOT EXISTS idx_rates_effective_date ON rates(effective_date);
    CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
    CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
    CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);
    """

    # PostgreSQL uses SERIAL instead of AUTOINCREMENT
    if db.is_postgres:
        schema = schema.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        schema = schema.replace('INTEGER DEFAULT 1', 'INTEGER DEFAULT 1')

    # Execute schema creation
    with db.get_connection() as conn:
        cursor = conn.cursor()
        for statement in schema.split(';'):
            if statement.strip():
                cursor.execute(statement)

    print("✅ Database initialized successfully")


# Global database instance
db = Database()


if __name__ == '__main__':
    # Allow running this file directly to initialize the database
    init_db()

"""
Migration: Add security columns for HIPAA compliance
Adds: failed_login_attempts, locked_until, last_failed_login to users table
"""

import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db

def upgrade():
    """Add security-related columns to users table."""
    print("Adding security columns to users table...")

    # Check if columns already exist (for idempotency)
    if not db.is_postgres:
        check_query = "PRAGMA table_info(users)"
        existing_columns = db.execute_query(check_query)
        column_names = [col['name'] for col in existing_columns]
    else:
        check_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
        """
        existing_columns = db.execute_query(check_query)
        column_names = [col['column_name'] for col in existing_columns]

    # Add failed_login_attempts column
    if 'failed_login_attempts' not in column_names:
        print("  - Adding failed_login_attempts column...")
        query = "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"
        db.execute_query(query, fetch='none')
    else:
        print("  - Column failed_login_attempts already exists, skipping")

    # Add locked_until column
    if 'locked_until' not in column_names:
        print("  - Adding locked_until column...")
        query = "ALTER TABLE users ADD COLUMN locked_until TIMESTAMP NULL"
        db.execute_query(query, fetch='none')
    else:
        print("  - Column locked_until already exists, skipping")

    # Add last_failed_login column
    if 'last_failed_login' not in column_names:
        print("  - Adding last_failed_login column...")
        query = "ALTER TABLE users ADD COLUMN last_failed_login TIMESTAMP NULL"
        db.execute_query(query, fetch='none')
    else:
        print("  - Column last_failed_login already exists, skipping")

    print("✅ Security columns migration completed successfully!")


def downgrade():
    """Remove security-related columns (for rollback)."""
    print("Rolling back security columns...")

    # SQLite doesn't support DROP COLUMN easily, so we'll just note it
    if db.is_postgres:
        db.execute_query("ALTER TABLE users DROP COLUMN IF EXISTS failed_login_attempts", fetch='none')
        db.execute_query("ALTER TABLE users DROP COLUMN IF EXISTS locked_until", fetch='none')
        db.execute_query("ALTER TABLE users DROP COLUMN IF EXISTS last_failed_login", fetch='none')
        print("✅ Security columns rollback completed!")
    else:
        print("⚠️  SQLite doesn't support DROP COLUMN. Manual rollback required.")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate database for security features')
    parser.add_argument('action', choices=['upgrade', 'downgrade'], help='Migration action')
    args = parser.parse_args()

    if args.action == 'upgrade':
        upgrade()
    elif args.action == 'downgrade':
        downgrade()

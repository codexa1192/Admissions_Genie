#!/usr/bin/env python3
"""
Quick migration to add security columns to users table in production.
Run this in Render shell: python3 migrations/add_security_columns_quick.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db

def add_security_columns():
    """Add missing security columns to users table."""
    print("=" * 80)
    print("ADDING SECURITY COLUMNS TO USERS TABLE")
    print("=" * 80)
    print()

    try:
        # Add failed_login_attempts column
        print("Adding failed_login_attempts column...")
        db.execute_query(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0",
            fetch='none'
        )
        print("✅ Added failed_login_attempts")

        # Add locked_until column
        print("Adding locked_until column...")
        db.execute_query(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP",
            fetch='none'
        )
        print("✅ Added locked_until")

        # Add last_failed_login column
        print("Adding last_failed_login column...")
        db.execute_query(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMP",
            fetch='none'
        )
        print("✅ Added last_failed_login")

        # Update existing users
        print("\nUpdating existing users with default values...")
        db.execute_query(
            "UPDATE users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL",
            fetch='none'
        )
        print("✅ Updated existing users")

        # Verify columns
        print("\nVerifying columns...")
        result = db.execute_query("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
              AND column_name IN ('failed_login_attempts', 'locked_until', 'last_failed_login')
            ORDER BY column_name
        """)

        if result:
            print("\n✅ Columns verified:")
            for row in result:
                print(f"  - {row['column_name']}: {row['data_type']} (default: {row['column_default']})")
        else:
            print("⚠️  Could not verify columns")

        print("\n" + "=" * 80)
        print("✅ SECURITY COLUMNS ADDED SUCCESSFULLY")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Error adding security columns: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = add_security_columns()
    sys.exit(0 if success else 1)

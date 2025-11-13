#!/usr/bin/env python3
"""
Migration: Add password_must_change column to users table
and set it to TRUE for admin accounts.

This enables forced password change on first login.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db

def migrate():
    """Add password_must_change column and update admin accounts."""

    print("=" * 70)
    print("MIGRATION: Add password_must_change column")
    print("=" * 70)
    print()

    try:
        # Check if column already exists
        result = db.execute_query(
            "SELECT password_must_change FROM users LIMIT 1",
            fetch='one'
        )
        print("✅ Column already exists, skipping creation")
    except Exception as e:
        # Column doesn't exist, add it
        print("Adding password_must_change column...")
        db.execute_query(
            "ALTER TABLE users ADD COLUMN password_must_change INTEGER DEFAULT 0",
            fetch='none'
        )
        print("✅ Column added successfully")

    print()

    # Set password_must_change=1 for admin accounts
    print("Setting password_must_change=TRUE for admin accounts...")
    db.execute_query(
        "UPDATE users SET password_must_change = 1 WHERE email IN ('admin@admissionsgenie.com', 'jthayer@verisightanalytics.com')",
        fetch='none'
    )

    # Count how many were updated
    count = db.execute_query(
        "SELECT COUNT(*) as count FROM users WHERE password_must_change = 1",
        fetch='one'
    )

    print(f"✅ Updated {count['count']} admin account(s)")
    print()

    # Verify the migration
    print("Verifying migration...")
    admins = db.execute_query(
        "SELECT email, password_must_change FROM users WHERE email IN ('admin@admissionsgenie.com', 'jthayer@verisightanalytics.com')",
        fetch='all'
    )

    if admins:
        print()
        print("Admin accounts requiring password change:")
        for admin in admins:
            status = "✅ YES" if admin['password_must_change'] else "❌ NO"
            print(f"  - {admin['email']}: {status}")

    print()
    print("=" * 70)
    print("✅ MIGRATION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Test login with admin@admissionsgenie.com / admin123")
    print("2. System will force password change")
    print("3. Create your new secure password")
    print()

if __name__ == '__main__':
    migrate()

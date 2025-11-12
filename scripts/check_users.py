#!/usr/bin/env python3
"""
Check user accounts and diagnose login issues.
Run in Render shell: python3 scripts/check_users.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user import User
from models.organization import Organization

def check_users():
    """Check all user accounts and their status."""
    print("=" * 80)
    print("USER ACCOUNT DIAGNOSTIC")
    print("=" * 80)
    print()

    # Check organization
    print("1. Checking organizations...")
    orgs = Organization.get_all(active_only=False)
    print(f"   Found {len(orgs)} organizations:")
    for org in orgs:
        print(f"   - {org.name} (ID: {org.id}, Active: {org.is_active})")
    print()

    # Check each expected user
    expected_users = [
        'admin@admissionsgenie.com',
        'user@admissionsgenie.com',
        'jthayer@verisightanalytics.com'
    ]

    print("2. Checking user accounts...")
    for email in expected_users:
        print(f"\n   Checking: {email}")
        user = User.get_by_email(email)

        if user:
            print(f"   ✅ FOUND")
            print(f"      ID: {user.id}")
            print(f"      Organization ID: {user.organization_id}")
            print(f"      Full Name: {user.full_name}")
            print(f"      Facility ID: {user.facility_id}")
            print(f"      Role: {user.role}")
            print(f"      Active: {user.is_active}")
            print(f"      Locked: {user.is_locked()}")
            if user.failed_login_attempts > 0:
                print(f"      ⚠️  Failed login attempts: {user.failed_login_attempts}")
            if user.locked_until:
                print(f"      ⚠️  Locked until: {user.locked_until}")

            # Test password
            if email == 'jthayer@verisightanalytics.com':
                test_password = 'admin123'
            elif 'admin' in email:
                test_password = 'admin123'
            else:
                test_password = 'user123'

            password_valid = user.verify_password(test_password)
            if password_valid:
                print(f"      ✅ Password '{test_password}' is CORRECT")
            else:
                print(f"      ❌ Password '{test_password}' is INCORRECT")
        else:
            print(f"   ❌ NOT FOUND - User needs to be created")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print()

    # Print recommendations
    print("RECOMMENDATIONS:")
    print()

    missing_users = [email for email in expected_users if not User.get_by_email(email)]
    if missing_users:
        print("⚠️  Missing users found. Run this command to create them:")
        print("   python3 seed_database.py")
        print()

    locked_users = []
    for email in expected_users:
        user = User.get_by_email(email)
        if user and user.is_locked():
            locked_users.append(email)

    if locked_users:
        print("⚠️  Locked accounts found. To unlock them, run:")
        for email in locked_users:
            user = User.get_by_email(email)
            print(f"   python3 -c \"from models.user import User; u = User.get_by_email('{email}'); u.unlock(); print('Unlocked {email}')\"")
        print()

    inactive_users = []
    for email in expected_users:
        user = User.get_by_email(email)
        if user and not user.is_active:
            inactive_users.append(email)

    if inactive_users:
        print("⚠️  Inactive accounts found. To activate them, run:")
        for email in inactive_users:
            user = User.get_by_email(email)
            print(f"   python3 -c \"from models.user import User; u = User.get_by_email('{email}'); u.activate(); print('Activated {email}')\"")
        print()

    if not missing_users and not locked_users and not inactive_users:
        print("✅ All user accounts are properly configured!")
        print()


if __name__ == '__main__':
    check_users()

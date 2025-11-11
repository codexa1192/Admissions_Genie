#!/usr/bin/env python3
"""
Multi-Tenant Migration Script
Migrates existing single-tenant data to multi-tenant architecture.

This script:
1. Creates a default organization for existing data
2. Assigns all existing records to that organization
3. Validates data integrity after migration

Usage:
    python3 migrations/multi_tenant_migration.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import Database
from models.organization import Organization


def run_migration():
    """Run the multi-tenant migration."""
    print("=" * 80)
    print("MULTI-TENANT MIGRATION")
    print("=" * 80)
    print()

    db = Database()

    # Step 1: Create default organization
    print("📋 Step 1: Creating default organization...")
    try:
        # Check if organization already exists
        existing_org = Organization.get_by_subdomain('default')
        if existing_org:
            print(f"✅ Default organization already exists (ID: {existing_org.id})")
            org_id = existing_org.id
        else:
            # Create default organization for existing data
            org = Organization.create(
                name='Default Organization',
                subdomain='default',
                subscription_tier=Organization.TIER_PROFESSIONAL,  # Start on professional tier
                settings={
                    'migrated_from_single_tenant': True,
                    'migration_date': '2025-01-01'
                }
            )
            print(f"✅ Created default organization (ID: {org.id})")
            org_id = org.id
    except Exception as e:
        print(f"❌ Failed to create organization: {e}")
        return False

    print()

    # Step 2: Migrate facilities
    print("📋 Step 2: Migrating facilities...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Check if migration already done
            cursor.execute("SELECT COUNT(*) as count FROM facilities WHERE organization_id IS NOT NULL")
            result = cursor.fetchone()
            already_migrated = result['count'] if result else 0

            if already_migrated > 0:
                print(f"✅ Facilities already migrated ({already_migrated} records)")
            else:
                cursor.execute("UPDATE facilities SET organization_id = ? WHERE organization_id IS NULL", (org_id,))
                cursor.execute("SELECT COUNT(*) as count FROM facilities")
                count = cursor.fetchone()['count']
                print(f"✅ Migrated {count} facilities")
    except Exception as e:
        print(f"❌ Failed to migrate facilities: {e}")
        return False

    print()

    # Step 3: Migrate payers
    print("📋 Step 3: Migrating payers...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM payers WHERE organization_id IS NOT NULL")
            result = cursor.fetchone()
            already_migrated = result['count'] if result else 0

            if already_migrated > 0:
                print(f"✅ Payers already migrated ({already_migrated} records)")
            else:
                cursor.execute("UPDATE payers SET organization_id = ? WHERE organization_id IS NULL", (org_id,))
                cursor.execute("SELECT COUNT(*) as count FROM payers")
                count = cursor.fetchone()['count']
                print(f"✅ Migrated {count} payers")
    except Exception as e:
        print(f"❌ Failed to migrate payers: {e}")
        return False

    print()

    # Step 4: Migrate rates
    print("📋 Step 4: Migrating rates...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM rates WHERE organization_id IS NOT NULL")
            result = cursor.fetchone()
            already_migrated = result['count'] if result else 0

            if already_migrated > 0:
                print(f"✅ Rates already migrated ({already_migrated} records)")
            else:
                cursor.execute("UPDATE rates SET organization_id = ? WHERE organization_id IS NULL", (org_id,))
                cursor.execute("SELECT COUNT(*) as count FROM rates")
                count = cursor.fetchone()['count']
                print(f"✅ Migrated {count} rates")
    except Exception as e:
        print(f"❌ Failed to migrate rates: {e}")
        return False

    print()

    # Step 5: Migrate cost models
    print("📋 Step 5: Migrating cost models...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM cost_models WHERE organization_id IS NOT NULL")
            result = cursor.fetchone()
            already_migrated = result['count'] if result else 0

            if already_migrated > 0:
                print(f"✅ Cost models already migrated ({already_migrated} records)")
            else:
                cursor.execute("UPDATE cost_models SET organization_id = ? WHERE organization_id IS NULL", (org_id,))
                cursor.execute("SELECT COUNT(*) as count FROM cost_models")
                count = cursor.fetchone()['count']
                print(f"✅ Migrated {count} cost models")
    except Exception as e:
        print(f"❌ Failed to migrate cost models: {e}")
        return False

    print()

    # Step 6: Migrate business weights
    print("📋 Step 6: Migrating business weights...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM business_weights WHERE organization_id IS NOT NULL")
            result = cursor.fetchone()
            already_migrated = result['count'] if result else 0

            if already_migrated > 0:
                print(f"✅ Business weights already migrated ({already_migrated} records)")
            else:
                cursor.execute("UPDATE business_weights SET organization_id = ? WHERE organization_id IS NULL", (org_id,))
                cursor.execute("SELECT COUNT(*) as count FROM business_weights")
                count = cursor.fetchone()['count']
                print(f"✅ Migrated {count} business weights")
    except Exception as e:
        print(f"❌ Failed to migrate business weights: {e}")
        return False

    print()

    # Step 7: Migrate admissions
    print("📋 Step 7: Migrating admissions...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM admissions WHERE organization_id IS NOT NULL")
            result = cursor.fetchone()
            already_migrated = result['count'] if result else 0

            if already_migrated > 0:
                print(f"✅ Admissions already migrated ({already_migrated} records)")
            else:
                cursor.execute("UPDATE admissions SET organization_id = ? WHERE organization_id IS NULL", (org_id,))
                cursor.execute("SELECT COUNT(*) as count FROM admissions")
                count = cursor.fetchone()['count']
                print(f"✅ Migrated {count} admissions")
    except Exception as e:
        print(f"❌ Failed to migrate admissions: {e}")
        return False

    print()

    # Step 8: Migrate users
    print("📋 Step 8: Migrating users...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM users WHERE organization_id IS NOT NULL")
            result = cursor.fetchone()
            already_migrated = result['count'] if result else 0

            if already_migrated > 0:
                print(f"✅ Users already migrated ({already_migrated} records)")
            else:
                cursor.execute("UPDATE users SET organization_id = ? WHERE organization_id IS NULL", (org_id,))
                cursor.execute("SELECT COUNT(*) as count FROM users")
                count = cursor.fetchone()['count']
                print(f"✅ Migrated {count} users")
    except Exception as e:
        print(f"❌ Failed to migrate users: {e}")
        return False

    print()

    # Step 9: Migrate audit logs
    print("📋 Step 9: Migrating audit logs...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM audit_logs WHERE organization_id IS NOT NULL")
            result = cursor.fetchone()
            already_migrated = result['count'] if result else 0

            if already_migrated > 0:
                print(f"✅ Audit logs already migrated ({already_migrated} records)")
            else:
                cursor.execute("UPDATE audit_logs SET organization_id = ? WHERE organization_id IS NULL", (org_id,))
                cursor.execute("SELECT COUNT(*) as count FROM audit_logs")
                count = cursor.fetchone()['count']
                print(f"✅ Migrated {count} audit logs")
    except Exception as e:
        print(f"❌ Failed to migrate audit logs: {e}")
        return False

    print()

    # Step 10: Verify migration
    print("📋 Step 10: Verifying migration...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            tables = ['facilities', 'payers', 'rates', 'cost_models', 'business_weights',
                     'admissions', 'users', 'audit_logs']

            all_verified = True
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table} WHERE organization_id IS NULL")
                result = cursor.fetchone()
                null_count = result['count'] if result else 0

                if null_count > 0:
                    print(f"⚠️  {table}: {null_count} records still have NULL organization_id")
                    all_verified = False
                else:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    total_count = result['count'] if result else 0
                    print(f"✅ {table}: All {total_count} records have organization_id")

            if not all_verified:
                print("\n⚠️  Migration completed with warnings")
                return False
    except Exception as e:
        print(f"❌ Failed to verify migration: {e}")
        return False

    print()
    print("=" * 80)
    print("✅ MULTI-TENANT MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print()
    print(f"Default Organization ID: {org_id}")
    print(f"Subdomain: default")
    print(f"Tier: professional")
    print()
    print("Next steps:")
    print("1. Test the application with existing data")
    print("2. Create additional organizations for new customers")
    print("3. Implement organization signup flow")
    print()

    return True


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

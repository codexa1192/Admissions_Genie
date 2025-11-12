#!/usr/bin/env python3
"""
Seed production database with organization and users.
Run this in Render shell: python3 migrations/seed_production.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Make sure we're using production DATABASE_URL from environment
if 'DATABASE_URL' not in os.environ:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    print("This script must be run in the Render shell where DATABASE_URL is available.")
    sys.exit(1)

print("=" * 80)
print("SEEDING PRODUCTION DATABASE")
print("=" * 80)
print(f"Database URL: {os.environ['DATABASE_URL'][:30]}...")
print()

# Import seed function
from seed_database import seed_database

try:
    seed_database()
    print("\n" + "=" * 80)
    print("✅ PRODUCTION DATABASE SEEDED SUCCESSFULLY")
    print("=" * 80)
    sys.exit(0)
except Exception as e:
    print(f"\n❌ Error seeding production database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

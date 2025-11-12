#!/usr/bin/env python3
"""
Add case_number column to admissions table (PHI-FREE mode).
Run this in Render shell: python3 migrations/add_case_number_column.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db

def add_case_number_column():
    """Add case_number column to admissions table."""
    print("=" * 80)
    print("ADDING CASE_NUMBER COLUMN TO ADMISSIONS TABLE")
    print("=" * 80)
    print()

    try:
        # Check if column already exists
        print("Checking if case_number column exists...")
        result = db.execute_query("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'admissions'
              AND column_name = 'case_number'
        """, fetch='one')

        if result:
            print("✅ case_number column already exists")
            return True

        # Add case_number column
        print("Adding case_number column...")
        db.execute_query(
            "ALTER TABLE admissions ADD COLUMN case_number TEXT",
            fetch='none'
        )
        print("✅ Added case_number column")

        # Create index
        print("Creating index on case_number...")
        db.execute_query(
            "CREATE INDEX idx_admissions_case_number ON admissions(case_number)",
            fetch='none'
        )
        print("✅ Created index")

        # Verify column
        print("\nVerifying column...")
        result = db.execute_query("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'admissions'
              AND column_name = 'case_number'
        """, fetch='one')

        if result:
            print(f"✅ Column verified: {result['column_name']} ({result['data_type']}, nullable: {result['is_nullable']})")
        else:
            print("⚠️  Could not verify column")

        print("\n" + "=" * 80)
        print("✅ CASE_NUMBER COLUMN ADDED SUCCESSFULLY")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Error adding case_number column: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = add_case_number_column()
    sys.exit(0 if success else 1)

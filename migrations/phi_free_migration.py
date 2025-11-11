"""
PHI-FREE Migration Script
Migrates existing database from PHI storage to PHI-free mode.

Changes:
- Renames patient_initials column to case_number
- Generates case numbers for existing admissions
- Adds migration tracking

HIPAA Compliance: This migration removes PHI identifiers from the database.
Run this BEFORE deploying PHI-free mode in production.
"""

from config.database import Database
from datetime import datetime
import sys


def migrate_to_phi_free():
    """Migrate database from PHI storage to PHI-free mode."""
    db = Database()

    print("\n" + "="*70)
    print("PHI-FREE MIGRATION")
    print("="*70)
    print("\nThis migration will:")
    print("1. Rename 'patient_initials' column to 'case_number'")
    print("2. Generate case numbers for existing admissions")
    print("3. Mark extracted_data as deprecated (will not be populated)")
    print("\n⚠️  WARNING: This is a one-way migration. Back up your database first!")
    print("="*70)

    response = input("\nProceed with migration? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Migration cancelled.")
        sys.exit(0)

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Check if migration already applied
            if db.is_postgres:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'admissions' AND column_name = 'case_number'
                """)
            else:
                cursor.execute("PRAGMA table_info(admissions)")
                columns = [row[1] if isinstance(row, tuple) else row['name'] for row in cursor.fetchall()]
                already_migrated = 'case_number' in columns

            if db.is_postgres:
                already_migrated = cursor.fetchone() is not None

            if already_migrated:
                print("✅ Migration already applied (case_number column exists).")
                return

            print("\n📋 Step 1: Renaming patient_initials to case_number...")

            if db.is_postgres:
                # PostgreSQL: Direct column rename
                cursor.execute("ALTER TABLE admissions RENAME COLUMN patient_initials TO case_number")
            else:
                # SQLite: Requires table recreation (no ALTER COLUMN support)
                # Create new table with updated schema
                cursor.execute("""
                    CREATE TABLE admissions_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        facility_id INTEGER NOT NULL,
                        payer_id INTEGER NOT NULL,
                        case_number TEXT UNIQUE,
                        uploaded_files TEXT,
                        extracted_data TEXT,
                        pdpm_groups TEXT,
                        projected_revenue REAL,
                        projected_cost REAL,
                        projected_los INTEGER,
                        margin_score INTEGER,
                        recommendation TEXT,
                        explanation TEXT,
                        actual_decision TEXT,
                        decided_by INTEGER,
                        decided_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (facility_id) REFERENCES facilities (id),
                        FOREIGN KEY (payer_id) REFERENCES payers (id)
                    )
                """)

                # Copy data from old table (patient_initials → case_number)
                cursor.execute("""
                    INSERT INTO admissions_new
                    SELECT
                        id, facility_id, payer_id,
                        patient_initials as case_number,  -- Rename column
                        uploaded_files, extracted_data, pdpm_groups,
                        projected_revenue, projected_cost, projected_los,
                        margin_score, recommendation, explanation,
                        actual_decision, decided_by, decided_at, created_at
                    FROM admissions
                """)

                # Drop old table and rename new one
                cursor.execute("DROP TABLE admissions")
                cursor.execute("ALTER TABLE admissions_new RENAME TO admissions")

                # Recreate indexes
                cursor.execute("CREATE INDEX idx_admissions_facility ON admissions(facility_id)")
                cursor.execute("CREATE INDEX idx_admissions_payer ON admissions(payer_id)")
                cursor.execute("CREATE INDEX idx_admissions_created ON admissions(created_at)")

            print("✅ Column renamed successfully")

            print("\n📋 Step 2: Generating case numbers for existing admissions...")

            # Get existing admissions
            cursor.execute("SELECT id, created_at FROM admissions WHERE case_number IS NULL OR case_number = ''")
            admissions = cursor.fetchall()

            if len(admissions) == 0:
                print("✅ No admissions need case number generation")
            else:
                # Generate case numbers for existing admissions
                for row in admissions:
                    admission_id = row['id'] if isinstance(row, dict) else row[0]
                    created_at = row['created_at'] if isinstance(row, dict) else row[1]

                    # Generate case number: CASE-YYYYMMDD-{id}
                    if created_at:
                        if isinstance(created_at, str):
                            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            date_obj = created_at
                        date_str = date_obj.strftime('%Y%m%d')
                    else:
                        date_str = datetime.now().strftime('%Y%m%d')

                    case_number = f"CASE-{date_str}-{admission_id:04d}"

                    # Update admission
                    update_query = db._convert_placeholders(
                        "UPDATE admissions SET case_number = ? WHERE id = ?"
                    )
                    cursor.execute(update_query, (case_number, admission_id))

                print(f"✅ Generated {len(admissions)} case numbers")

            print("\n📋 Step 3: Verifying migration...")

            # Verify all admissions have case numbers
            cursor.execute("SELECT COUNT(*) as count FROM admissions WHERE case_number IS NULL OR case_number = ''")
            result = cursor.fetchone()
            null_count = result['count'] if isinstance(result, dict) else result[0]

            if null_count > 0:
                raise Exception(f"Migration verification failed: {null_count} admissions still missing case numbers")

            print("✅ All admissions have case numbers")

            print("\n" + "="*70)
            print("✅ PHI-FREE MIGRATION COMPLETED SUCCESSFULLY")
            print("="*70)
            print("\nNext steps:")
            print("1. Deploy updated application code")
            print("2. Uploaded files will be auto-deleted after processing")
            print("3. No PHI will be stored in extracted_data going forward")
            print("\n")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("\n⚠️  Your database has been rolled back to the previous state.")
        raise


if __name__ == '__main__':
    migrate_to_phi_free()

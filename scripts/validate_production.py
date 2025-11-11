#!/usr/bin/env python3
"""
Production Validation Script for Admissions Genie (PHI-FREE MODE)
Pre-flight checks before deployment to ensure all requirements are met.

Usage: python3 scripts/validate_production.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Config
from config.database import Database, init_db
from utils.virus_scanner import get_virus_scanner
from utils.encryption import get_encryption_manager


class ValidationResult:
    """Track validation results."""

    def __init__(self):
        self.passed = []
        self.warnings = []
        self.failed = []

    def add_pass(self, message: str):
        self.passed.append(message)
        print(f"✅ {message}")

    def add_warning(self, message: str):
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def add_fail(self, message: str):
        self.failed.append(message)
        print(f"❌ {message}")

    def print_summary(self):
        print("\n" + "="*70)
        print("  VALIDATION SUMMARY")
        print("="*70)
        print(f"\n✅ Passed:   {len(self.passed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Failed:   {len(self.failed)}\n")

        if self.failed:
            print("CRITICAL FAILURES:")
            for fail in self.failed:
                print(f"  - {fail}")
            print("\n❌ PRODUCTION DEPLOYMENT BLOCKED\n")
            return False

        if self.warnings:
            print("WARNINGS (review recommended):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.warnings and not self.failed:
            print("✅ ALL CHECKS PASSED - READY FOR PRODUCTION\n")
        else:
            print("⚠️  DEPLOYMENT POSSIBLE WITH WARNINGS\n")

        return True


def validate_environment(result: ValidationResult):
    """Validate environment variables."""
    print("\n" + "="*70)
    print("CHECKING ENVIRONMENT CONFIGURATION")
    print("="*70 + "\n")

    # Flask environment
    if Config.FLASK_ENV == 'production':
        result.add_pass("FLASK_ENV set to production")
    else:
        result.add_warning(f"FLASK_ENV is '{Config.FLASK_ENV}' (should be 'production')")

    # Database URL
    if Config.DATABASE_URL:
        if Config.DATABASE_URL.startswith('postgresql://'):
            result.add_pass("PostgreSQL database configured (recommended)")
        elif Config.DATABASE_URL.startswith('sqlite:///'):
            result.add_warning("SQLite database in use (PostgreSQL recommended for production)")
        else:
            result.add_warning(f"Unrecognized database type: {Config.DATABASE_URL[:20]}...")
    else:
        result.add_fail("DATABASE_URL not set")

    # Secret key
    if Config.SECRET_KEY and Config.SECRET_KEY != 'dev-secret-key-change-in-production':
        if len(Config.SECRET_KEY) >= 32:
            result.add_pass("SECRET_KEY configured (strong)")
        else:
            result.add_warning("SECRET_KEY may be too short (recommend 32+ characters)")
    else:
        result.add_fail("SECRET_KEY not set or using default value")

    # Azure OpenAI
    if os.getenv('AZURE_OPENAI_API_KEY'):
        result.add_pass("AZURE_OPENAI_API_KEY configured")
    else:
        result.add_fail("AZURE_OPENAI_API_KEY not set (required for document extraction)")

    if os.getenv('AZURE_OPENAI_ENDPOINT'):
        result.add_pass("AZURE_OPENAI_ENDPOINT configured")
    else:
        result.add_fail("AZURE_OPENAI_ENDPOINT not set")

    if os.getenv('AZURE_OPENAI_DEPLOYMENT'):
        result.add_pass("AZURE_OPENAI_DEPLOYMENT configured")
    else:
        result.add_fail("AZURE_OPENAI_DEPLOYMENT not set")

    # PHI-FREE MODE: Encryption not required (but warn if enabled)
    if os.getenv('ENCRYPTION_KEY'):
        result.add_warning("ENCRYPTION_KEY set (not needed in PHI-FREE mode)")
    else:
        result.add_pass("No ENCRYPTION_KEY (correct for PHI-FREE mode)")


def validate_database(result: ValidationResult):
    """Validate database configuration and schema."""
    print("\n" + "="*70)
    print("CHECKING DATABASE")
    print("="*70 + "\n")

    try:
        db = Database()

        # Test connection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            result.add_pass("Database connection successful")

            # Check if admissions table exists
            if db.is_postgres:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name = 'admissions'
                """)
                table_exists = cursor.fetchone() is not None
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admissions'")
                table_exists = cursor.fetchone() is not None

            if table_exists:
                result.add_pass("Admissions table exists")

                # Check PHI-FREE migration status
                if db.is_postgres:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'admissions' AND column_name = 'case_number'
                    """)
                    has_case_number = cursor.fetchone() is not None
                else:
                    cursor.execute("PRAGMA table_info(admissions)")
                    columns = [row[1] if isinstance(row, tuple) else row['name'] for row in cursor.fetchall()]
                    has_case_number = 'case_number' in columns

                if has_case_number:
                    result.add_pass("PHI-FREE migration applied (case_number column exists)")
                else:
                    result.add_fail("PHI-FREE migration NOT applied (run migrations/phi_free_migration.py)")
            else:
                result.add_warning("Admissions table does not exist (will be created on first run)")

    except Exception as e:
        result.add_fail(f"Database connection failed: {str(e)}")


def validate_virus_scanner(result: ValidationResult):
    """Validate ClamAV virus scanner."""
    print("\n" + "="*70)
    print("CHECKING VIRUS SCANNER")
    print("="*70 + "\n")

    scanner = get_virus_scanner()

    if scanner.is_available():
        result.add_pass("ClamAV virus scanner available")

        # Test scan with EICAR test file
        try:
            # EICAR test string (safe virus signature for testing)
            eicar = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(eicar)
                test_file = f.name

            is_clean, threat = scanner.scan_file(test_file)
            os.unlink(test_file)

            if not is_clean:
                result.add_pass("ClamAV correctly detects test virus")
            else:
                result.add_warning("ClamAV did not detect EICAR test file (may need definition update)")
        except Exception as e:
            result.add_warning(f"ClamAV test scan failed: {str(e)}")
    else:
        if Config.FLASK_ENV == 'production':
            result.add_fail("ClamAV not available (REQUIRED for production)")
        else:
            result.add_warning("ClamAV not available (acceptable for development)")


def validate_file_structure(result: ValidationResult):
    """Validate required directories and files."""
    print("\n" + "="*70)
    print("CHECKING FILE STRUCTURE")
    print("="*70 + "\n")

    required_dirs = ['data', 'logs', 'migrations', 'scripts', 'config', 'models', 'routes', 'services', 'utils']
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            result.add_pass(f"Directory '{dir_name}' exists")
        else:
            result.add_fail(f"Required directory '{dir_name}' missing")

    # Check upload directory
    upload_dir = Config.UPLOAD_FOLDER
    if os.path.exists(upload_dir):
        result.add_pass(f"Upload directory '{upload_dir}' exists")

        # Check permissions (should be restrictive)
        stat_info = os.stat(upload_dir)
        mode = oct(stat_info.st_mode)[-3:]
        if mode in ['700', '770']:
            result.add_pass(f"Upload directory has secure permissions ({mode})")
        else:
            result.add_warning(f"Upload directory permissions are {mode} (recommend 700 or 770)")
    else:
        result.add_warning(f"Upload directory '{upload_dir}' does not exist (will be created)")

    # Check .env exists
    if os.path.exists('.env'):
        result.add_pass(".env file exists")

        # Check .env permissions
        stat_info = os.stat('.env')
        mode = oct(stat_info.st_mode)[-3:]
        if mode == '600':
            result.add_pass(".env has secure permissions (600)")
        else:
            result.add_warning(f".env permissions are {mode} (should be 600)")
    else:
        result.add_fail(".env file not found")


def validate_phi_free_mode(result: ValidationResult):
    """Validate PHI-FREE mode implementation."""
    print("\n" + "="*70)
    print("CHECKING PHI-FREE MODE IMPLEMENTATION")
    print("="*70 + "\n")

    # Check that models/admission.py uses case_number
    try:
        with open('models/admission.py', 'r') as f:
            content = f.read()

            if 'case_number' in content:
                result.add_pass("Admission model uses case_number")
            else:
                result.add_fail("Admission model does not use case_number")

            if '_generate_case_number' in content:
                result.add_pass("Auto-generate case number function present")
            else:
                result.add_fail("Auto-generate case number function missing")

            if 'extracted_data_json = json.dumps({})' in content:
                result.add_pass("extracted_data is not stored (PHI-FREE mode)")
            else:
                result.add_warning("extracted_data storage behavior unclear")

    except Exception as e:
        result.add_fail(f"Could not validate models/admission.py: {str(e)}")

    # Check that routes/admission.py deletes files
    try:
        with open('routes/admission.py', 'r') as f:
            content = f.read()

            if 'file_storage.delete_file' in content:
                result.add_pass("Files are deleted after processing")
            else:
                result.add_fail("File deletion not implemented")

            if 'PHI-FREE' in content:
                result.add_pass("PHI-FREE mode comments present")
            else:
                result.add_warning("PHI-FREE mode not clearly documented in code")

    except Exception as e:
        result.add_fail(f"Could not validate routes/admission.py: {str(e)}")


def main():
    """Run all validation checks."""
    print("="*70)
    print("  ADMISSIONS GENIE - PRODUCTION VALIDATION")
    print("  PHI-FREE MODE")
    print("="*70)

    result = ValidationResult()

    # Run all validation checks
    validate_environment(result)
    validate_database(result)
    validate_virus_scanner(result)
    validate_file_structure(result)
    validate_phi_free_mode(result)

    # Print summary and return exit code
    success = result.print_summary()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

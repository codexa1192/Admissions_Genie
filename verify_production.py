#!/usr/bin/env python3
"""
Production Environment Verification Script
Run this in Render Shell to verify all environment variables and dependencies.
"""

import os
import sys

def mask_sensitive(value, show_chars=4):
    """Mask sensitive values, showing only first few characters."""
    if not value:
        return "❌ NOT SET"
    if len(value) <= show_chars:
        return f"✅ SET (***)"
    return f"✅ SET ({value[:show_chars]}...)"

def check_env_var(name, required=True, sensitive=True):
    """Check if environment variable is set."""
    value = os.getenv(name)
    if value:
        display = mask_sensitive(value) if sensitive else f"✅ SET: {value}"
        print(f"  {name}: {display}")
        return True
    else:
        status = "❌ REQUIRED" if required else "⚠️  OPTIONAL"
        print(f"  {name}: {status} - NOT SET")
        return not required

def check_dependency(module_name, package_name=None):
    """Check if a Python package is installed."""
    if package_name is None:
        package_name = module_name
    try:
        __import__(module_name)
        print(f"  ✅ {package_name}")
        return True
    except ImportError:
        print(f"  ❌ {package_name} - NOT INSTALLED")
        return False

print("=" * 70)
print("🔍 PRODUCTION ENVIRONMENT VERIFICATION")
print("=" * 70)
print()

# Track overall status
all_good = True

# 1. Check Python version
print("1️⃣  PYTHON VERSION")
print(f"  ✅ Python {sys.version.split()[0]}")
print()

# 2. Check critical dependencies
print("2️⃣  CRITICAL DEPENDENCIES")
deps_ok = True
deps_ok &= check_dependency("flask", "Flask")
deps_ok &= check_dependency("psycopg2", "psycopg2-binary (PostgreSQL driver)")
deps_ok &= check_dependency("azure.storage.blob", "azure-storage-blob")
deps_ok &= check_dependency("openai", "openai")
all_good &= deps_ok
print()

# 3. Check database configuration
print("3️⃣  DATABASE CONFIGURATION")
db_url = os.getenv('DATABASE_URL')
if db_url:
    if db_url.startswith('postgresql://'):
        print(f"  ✅ DATABASE_URL: PostgreSQL ({db_url.split('@')[1].split('/')[0] if '@' in db_url else 'configured'})")
    elif db_url.startswith('sqlite://'):
        print(f"  ⚠️  DATABASE_URL: SQLite (development mode)")
        all_good = False
    else:
        print(f"  ❌ DATABASE_URL: Unknown database type")
        all_good = False
else:
    print(f"  ❌ DATABASE_URL: NOT SET - will use SQLite")
    all_good = False
print()

# 4. Check Azure Blob Storage
print("4️⃣  AZURE BLOB STORAGE")
azure_ok = True
azure_ok &= check_env_var('USE_AZURE', sensitive=False)
azure_ok &= check_env_var('AZURE_STORAGE_ACCOUNT_NAME', sensitive=False)
azure_ok &= check_env_var('AZURE_STORAGE_ACCOUNT_KEY', sensitive=True)
azure_ok &= check_env_var('AZURE_STORAGE_CONTAINER_NAME', sensitive=False)
all_good &= azure_ok
print()

# 5. Check Azure OpenAI
print("5️⃣  AZURE OPENAI")
openai_ok = True
openai_ok &= check_env_var('AZURE_OPENAI_API_KEY', sensitive=True)
openai_ok &= check_env_var('AZURE_OPENAI_ENDPOINT', sensitive=False)
openai_ok &= check_env_var('AZURE_OPENAI_DEPLOYMENT', sensitive=False)
all_good &= openai_ok
print()

# 6. Check Security Settings
print("6️⃣  SECURITY SETTINGS")
security_ok = True
security_ok &= check_env_var('SESSION_TIMEOUT_MINUTES', sensitive=False)
security_ok &= check_env_var('SESSION_COOKIE_SECURE', sensitive=False)
security_ok &= check_env_var('PHI_STRICT_MODE', sensitive=False)
security_ok &= check_env_var('SECRET_KEY', sensitive=True)
all_good &= security_ok
print()

# 7. Check Flask Environment
print("7️⃣  FLASK CONFIGURATION")
check_env_var('FLASK_ENV', required=False, sensitive=False)
check_env_var('PORT', required=False, sensitive=False)
print()

# 8. Optional Services
print("8️⃣  OPTIONAL SERVICES")
check_env_var('REDIS_URL', required=False, sensitive=True)
check_env_var('SENTRY_DSN', required=False, sensitive=True)
print()

# Final Summary
print("=" * 70)
if all_good and deps_ok and db_url and azure_ok and openai_ok and security_ok:
    print("✅ ALL CHECKS PASSED - PRODUCTION READY")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Ensure 'Clear build cache & deploy' was run in Render")
    print("2. Test health endpoint: curl https://admissions-genie.onrender.com/health/detailed")
    print("3. Test login at: https://admissions-genie.onrender.com")
    sys.exit(0)
else:
    print("❌ ISSUES FOUND - NOT PRODUCTION READY")
    print("=" * 70)
    print()
    print("Action Required:")

    if not deps_ok:
        print("❌ Missing dependencies - Run 'Clear build cache & deploy' in Render")

    if not db_url or not db_url.startswith('postgresql://'):
        print("❌ DATABASE_URL not configured for PostgreSQL")
        print("   → Add DATABASE_URL in Render Environment tab")
        print("   → Format: postgresql://user:pass@host:5432/dbname?sslmode=require")

    if not azure_ok:
        print("❌ Azure Blob Storage not fully configured")
        print("   → Verify all 4 AZURE_STORAGE_* variables in Render")

    if not openai_ok:
        print("❌ Azure OpenAI not fully configured")
        print("   → Verify all 3 AZURE_OPENAI_* variables in Render")

    if not security_ok:
        print("❌ Security settings incomplete")
        print("   → Add SESSION_TIMEOUT_MINUTES, SESSION_COOKIE_SECURE, PHI_STRICT_MODE")

    print()
    print("After fixing, run 'Clear build cache & deploy' in Render dashboard")
    sys.exit(1)

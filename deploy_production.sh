#!/bin/bash
#
# Production Deployment Script for Admissions Genie (PHI-FREE MODE)
# One-command deployment with all required dependencies and validation
#
# Usage: ./deploy_production.sh
#

set -e  # Exit on any error

echo "============================================================================"
echo "  ADMISSIONS GENIE - PHI-FREE MODE PRODUCTION DEPLOYMENT"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root (needed for ClamAV installation)
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ ERROR: This script must be run as root (for ClamAV installation)${NC}"
    echo "Please run: sudo ./deploy_production.sh"
    exit 1
fi

echo -e "${GREEN}✅ Running as root${NC}"
echo ""

# Step 1: Check Python version
echo "============================================================================"
echo "STEP 1: Checking Python Version"
echo "============================================================================"

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python 3.9+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"
echo ""

# Step 2: Install ClamAV (virus scanner)
echo "============================================================================"
echo "STEP 2: Installing ClamAV Virus Scanner"
echo "============================================================================"

if command -v clamd &> /dev/null; then
    echo -e "${GREEN}✅ ClamAV already installed${NC}"
else
    echo "Installing ClamAV..."

    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y clamav clamav-daemon clamav-freshclam
        # RHEL/CentOS
        elif command -v yum &> /dev/null; then
            yum install -y clamav clamav-update clamd
        else
            echo -e "${RED}❌ Unsupported Linux distribution${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install clamav
        else
            echo -e "${RED}❌ Homebrew not found. Please install Homebrew first.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Unsupported operating system${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ ClamAV installed${NC}"
fi

# Update virus definitions
echo "Updating virus definitions (this may take a few minutes)..."
freshclam 2>/dev/null || echo -e "${YELLOW}⚠️  freshclam update failed (may already be running)${NC}"

# Start ClamAV daemon
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    systemctl start clamav-daemon || service clamav-daemon start
    systemctl enable clamav-daemon || chkconfig clamav-daemon on
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start clamav
fi

echo -e "${GREEN}✅ ClamAV daemon started${NC}"
echo ""

# Step 3: Install Python dependencies
echo "============================================================================"
echo "STEP 3: Installing Python Dependencies"
echo "============================================================================"

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

# Step 4: Run PHI-FREE migration
echo "============================================================================"
echo "STEP 4: Running PHI-FREE Database Migration"
echo "============================================================================"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Please create .env with required configuration.${NC}"
    exit 1
fi

# Check if migration is needed
python3 -c "
from config.database import Database
db = Database()
with db.get_connection() as conn:
    cursor = conn.cursor()
    if db.is_postgres:
        cursor.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'admissions' AND column_name = 'case_number'\")
        exists = cursor.fetchone() is not None
    else:
        cursor.execute('PRAGMA table_info(admissions)')
        columns = [row[1] if isinstance(row, tuple) else row['name'] for row in cursor.fetchall()]
        exists = 'case_number' in columns

    if exists:
        print('✅ Database already migrated to PHI-FREE mode')
    else:
        print('⚠️  Database migration needed')
        exit(1)
" && MIGRATION_NEEDED=$? || MIGRATION_NEEDED=$?

if [ $MIGRATION_NEEDED -eq 1 ]; then
    echo "Running PHI-FREE migration..."
    python3 migrations/phi_free_migration.py
else
    echo -e "${GREEN}✅ Database already in PHI-FREE mode${NC}"
fi

echo ""

# Step 5: Run production validation
echo "============================================================================"
echo "STEP 5: Running Production Validation"
echo "============================================================================"

python3 scripts/validate_production.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Production validation failed. Please fix the issues above.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All validation checks passed${NC}"
echo ""

# Step 6: Set file permissions
echo "============================================================================"
echo "STEP 6: Setting File Permissions"
echo "============================================================================"

# Create necessary directories
mkdir -p data/uploads
mkdir -p logs

# Set permissions
chmod 700 data/uploads
chmod 700 logs
chmod 600 .env

# If using a specific user (e.g., www-data for web server)
if id "www-data" &>/dev/null; then
    chown -R www-data:www-data data logs
    echo -e "${GREEN}✅ Permissions set for www-data user${NC}"
else
    echo -e "${YELLOW}⚠️  www-data user not found. Skipping user ownership.${NC}"
fi

echo ""

# Step 7: Final instructions
echo "============================================================================"
echo "  DEPLOYMENT COMPLETE - FINAL STEPS"
echo "============================================================================"
echo ""
echo -e "${GREEN}✅ PHI-FREE MODE DEPLOYMENT SUCCESSFUL${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Review your .env configuration:"
echo "   - FLASK_ENV=production"
echo "   - DATABASE_URL (PostgreSQL recommended)"
echo "   - AZURE_OPENAI_API_KEY, ENDPOINT, DEPLOYMENT"
echo "   - SECRET_KEY (generate with: python3 -c 'import secrets; print(secrets.token_hex(32))')"
echo ""
echo "2. Start the application:"
echo "   - Development: python3 app.py"
echo "   - Production (Gunicorn): gunicorn -w 4 -b 0.0.0.0:8080 app:app"
echo "   - Production (with SSL): gunicorn -w 4 -b 0.0.0.0:443 --certfile=cert.pem --keyfile=key.pem app:app"
echo ""
echo "3. Verify PHI-FREE mode is working:"
echo "   - Upload a test discharge summary"
echo "   - Verify case number is auto-generated (CASE-YYYYMMDD-XXXX)"
echo "   - Verify files are deleted after processing"
echo "   - Check audit logs show case_number (not patient_initials)"
echo ""
echo "4. Monitor logs:"
echo "   - Application logs: tail -f logs/app.log"
echo "   - ClamAV logs: tail -f /var/log/clamav/clamav.log"
echo ""
echo "HIPAA COMPLIANCE NOTE:"
echo "Even in PHI-FREE mode, you must have a Business Associate Agreement (BAA)"
echo "with Azure OpenAI, as uploaded documents are processed by Azure during"
echo "the extraction phase (files are deleted immediately after)."
echo ""
echo "============================================================================"
echo ""

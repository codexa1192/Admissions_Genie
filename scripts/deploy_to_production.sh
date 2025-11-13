#!/bin/bash
#############################################################
# Admissions Genie - Production Deployment Script
#
# This script deploys Admissions Genie to production
#
# Prerequisites:
# - Production server with Python 3.9+
# - PostgreSQL database (encrypted)
# - Environment variables configured
# - Azure OpenAI access
#
# Usage: ./scripts/deploy_to_production.sh
#############################################################

set -e  # Exit on error

echo "=========================================="
echo "Admissions Genie - Production Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Prerequisites
echo "Step 1: Checking prerequisites..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Check PostgreSQL client
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} PostgreSQL client (psql) not found (optional)"
else
    echo -e "${GREEN}✓${NC} PostgreSQL client found"
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}ERROR: app.py not found. Are you in the Admissions_Genie directory?${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} In correct directory"

# Step 2: Environment Variables Check
echo ""
echo "Step 2: Checking environment variables..."

REQUIRED_VARS=(
    "DATABASE_URL"
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_KEY"
    "AZURE_OPENAI_DEPLOYMENT"
    "ENCRYPTION_KEY"
    "SECRET_KEY"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    else
        echo -e "${GREEN}✓${NC} $var is set"
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}ERROR: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "${RED}  - $var${NC}"
    done
    echo ""
    echo "Please set these environment variables before deploying."
    echo "Example:"
    echo "  export DATABASE_URL='postgresql://user:pass@host:5432/admissions_genie'"
    echo "  export AZURE_OPENAI_ENDPOINT='https://your-endpoint.openai.azure.com/'"
    echo "  export AZURE_OPENAI_KEY='your-key-here'"
    echo "  export AZURE_OPENAI_DEPLOYMENT='your-deployment-name'"
    echo "  export ENCRYPTION_KEY=\$(python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")"
    echo "  export SECRET_KEY=\$(python3 -c \"import secrets; print(secrets.token_hex(32))\")"
    exit 1
fi

# Check FLASK_ENV is set to production
if [ "$FLASK_ENV" != "production" ]; then
    echo -e "${YELLOW}⚠${NC} FLASK_ENV is not set to 'production' (current: ${FLASK_ENV})"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 3: Create virtual environment
echo ""
echo "Step 3: Setting up virtual environment..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Created virtual environment"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate
echo -e "${GREEN}✓${NC} Activated virtual environment"

# Step 4: Install dependencies
echo ""
echo "Step 4: Installing dependencies..."

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Dependencies installed"

# Step 5: Database initialization
echo ""
echo "Step 5: Initializing database..."

# Check if database is accessible
python3 -c "from config.database import db; db.get_connection()" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Database connection successful"
else
    echo -e "${RED}ERROR: Cannot connect to database${NC}"
    echo "Please check your DATABASE_URL environment variable"
    exit 1
fi

# Initialize schema
python3 -c "from config.database import db; db.init_db()" 2>&1
echo -e "${GREEN}✓${NC} Database schema initialized"

# Ask if we should seed demo data
echo ""
read -p "Seed database with demo data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 seed_database.py
    echo -e "${GREEN}✓${NC} Demo data seeded"
    echo -e "${YELLOW}⚠${NC} Default admin login: admin@admissionsgenie.com / admin123"
    echo -e "${YELLOW}⚠${NC} CHANGE THIS PASSWORD IMMEDIATELY AFTER DEPLOYMENT!"
else
    echo -e "${GREEN}✓${NC} Skipped demo data seeding"
fi

# Step 6: Run tests (optional)
echo ""
read -p "Run tests before deployment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running tests..."
    python3 -m pytest tests/test_all_flows.py -v
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All tests passed"
    else
        echo -e "${RED}ERROR: Tests failed${NC}"
        read -p "Continue deployment anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${GREEN}✓${NC} Skipped tests"
fi

# Step 7: Check virus scanner (ClamAV)
echo ""
echo "Step 7: Checking virus scanner..."

if command -v clamdscan &> /dev/null; then
    echo -e "${GREEN}✓${NC} ClamAV daemon found"

    # Check if daemon is running
    if pgrep -x "clamd" > /dev/null; then
        echo -e "${GREEN}✓${NC} ClamAV daemon is running"
    else
        echo -e "${YELLOW}⚠${NC} ClamAV daemon not running"
        echo "  Start with: sudo systemctl start clamav-daemon"
    fi

    # Update virus definitions
    read -p "Update virus definitions? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo freshclam
        echo -e "${GREEN}✓${NC} Virus definitions updated"
    fi
else
    echo -e "${YELLOW}⚠${NC} ClamAV not found (virus scanning disabled)"
    echo "  Install with: sudo apt-get install clamav clamav-daemon (Ubuntu/Debian)"
    echo "             OR: sudo yum install clamav clamd (RHEL/CentOS)"
fi

# Step 8: Deploy application
echo ""
echo "Step 8: Starting application..."

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Gunicorn not found, using Flask development server"
    echo -e "${RED}WARNING: Development server is NOT recommended for production${NC}"
    read -p "Continue with development server? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi

    # Start Flask development server
    echo "Starting Flask development server on http://0.0.0.0:5000"
    python3 app.py
else
    # Start Gunicorn production server
    echo "Starting Gunicorn production server on http://0.0.0.0:8000"
    echo ""
    echo "Gunicorn configuration:"
    echo "  - Workers: 4"
    echo "  - Timeout: 120s"
    echo "  - Bind: 0.0.0.0:8000"
    echo ""

    gunicorn \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        app:app
fi

# Step 9: Post-deployment checklist
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Change default admin password:"
echo "   - Login at https://your-domain.com"
echo "   - Email: admin@admissionsgenie.com"
echo "   - Password: admin123"
echo "   - Click username → Change Password"
echo ""
echo "2. Add your facility data:"
echo "   - Fill out facility_data_template.csv"
echo "   - Admin Panel → Add facility, payers, rates, costs"
echo ""
echo "3. Create staff accounts:"
echo "   - Admin Panel → Users → Add New User"
echo ""
echo "4. Test the workflow:"
echo "   - Upload a sample discharge summary"
echo "   - Verify score calculation"
echo "   - Record a decision"
echo ""
echo "5. Train your staff:"
echo "   - See GO_LIVE_CHECKLIST.md"
echo ""
echo "For troubleshooting, see DEPLOY_NOW.md"
echo ""

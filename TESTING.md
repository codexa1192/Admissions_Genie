# Admissions Genie - Testing Guide

## Quick Start (Automated Installation)

```bash
cd Documents/Admissions-Genie
chmod +x install_and_test.sh
./install_and_test.sh
```

The install script will:
1. Check Python version
2. Create virtual environment
3. Install all dependencies
4. Install Tesseract OCR (if missing)
5. Initialize database
6. Seed with sample data
7. Start the application

## Manual Installation (If Automated Fails)

### 1. Prerequisites

```bash
# Check Python version (need 3.9+)
python3 --version

# Install Tesseract OCR
# macOS:
brew install tesseract

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# Verify Tesseract
tesseract --version
```

### 2. Virtual Environment

```bash
cd Documents/Admissions-Genie

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Azure OpenAI credentials
nano .env  # or use any text editor
```

**Required in .env:**
```
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo
```

### 5. Initialize Database

```bash
python3 -c "from config.database import init_db; init_db()"
```

### 6. Seed Sample Data

```bash
python3 seed_database.py
```

This creates:
- 2 sample facilities
- 4 payer types (Medicare FFS, MA, Medicaid, Family Care)
- Rate configurations for all payer types
- Cost models for all acuity bands
- 2 users (admin and regular user)

### 7. Start Application

```bash
python3 app.py
```

Application runs at: http://localhost:5000

## Login Credentials

**Admin Account:**
- Email: admin@admissionsgenie.com
- Password: admin123

**Regular User:**
- Email: user@admissionsgenie.com
- Password: user123

## Testing Workflow

### 1. Basic Application Test

1. **Access home page**: http://localhost:5000
2. **Login** with admin credentials
3. **Navigate** to Dashboard
4. **Verify** you see the dashboard with quick action cards

### 2. Test New Admission (WITHOUT Documents - Manual Entry)

Since we don't have sample discharge documents yet, you can test the system logic by:

1. Go to **New Admission**
2. Fill out the form:
   - Select Facility: "Sunshine SNF"
   - Select Payer: "Medicare FFS"
   - Patient Initials: "JD"
   - Estimated LOS: 15
   - Auth Status: "granted"
   - Current Census: 85%

3. **Skip file upload for now** (need to modify code to allow manual entry)

### 3. Test with Sample Document

Create a simple text file (`sample_discharge.txt`) with this content:

```
DISCHARGE SUMMARY

Patient: J.D.
DOB: 01/15/1945

PRINCIPAL DIAGNOSIS: M16.11 - Unilateral primary osteoarthritis, right hip

COMORBIDITIES:
- I50.9 - Heart failure, unspecified
- E11.9 - Type 2 diabetes mellitus
- J44.0 - COPD with acute lower respiratory infection

MEDICATIONS:
- Metformin 1000mg BID
- Lisinopril 20mg daily
- Lasix 40mg daily
- Albuterol inhaler PRN

FUNCTIONAL STATUS:
- ADL Score: 12/28
- Requires moderate assistance with transfers
- Can ambulate 10 feet with walker
- Alert and oriented x3

THERAPY RECOMMENDATIONS:
- PT for gait training and strengthening
- OT for ADL retraining

SPECIAL SERVICES:
- Oxygen therapy 2L NC
- Wound care for stage 2 pressure ulcer

ESTIMATED LOS: 14-18 days

AUTHORIZATION: Medicare Part A approved, 25 benefit days remaining
```

Save as PDF or Word document and upload through the New Admission form.

### 4. Test Admin Functions

#### A. Facility Management
1. Go to **Admin → Facilities**
2. Click **New Facility**
3. Add a new facility with:
   - Name: "Test Care Center"
   - Wage Index: 1.0
   - VBP Multiplier: 0.99
   - Check capabilities: IV ABX, Wound Vac
4. **Save** and verify it appears in the list

#### B. Payer Management
1. Go to **Admin → Payers**
2. Add a new payer:
   - Type: Medicare Advantage
   - Plan Name: "Aetna Medicare Advantage"
3. **Save** and verify

#### C. Rate Upload
1. Create a CSV file (`medicare_rates.csv`):
```csv
fiscal_year,pt_component,ot_component,slp_component,nursing_component,nta_component,non_case_mix
2025,64.89,64.38,26.43,105.81,86.72,98.13
```

2. Go to **Admin → Rates → Upload Rates**
3. Select:
   - Facility: Sunshine SNF
   - Payer: Medicare FFS
   - Rate Type: medicare_ffs
   - Upload the CSV
4. **Save** and verify rates are imported

#### D. Cost Model Management
1. Go to **Admin → Cost Models**
2. Select facility: Sunshine SNF
3. Verify all acuity bands have cost models
4. Edit one:
   - Select "high" acuity
   - Change nursing hours to 6.0
   - **Save** and verify

### 5. End-to-End Admission Test

Once you have Azure OpenAI configured:

1. **Upload** a discharge document (PDF or Word)
2. **System should**:
   - Extract ICD-10 codes
   - Classify PDPM groups
   - Calculate projected revenue
   - Estimate costs
   - Generate margin score
   - Provide recommendation
3. **View Results**:
   - Check margin score (0-100)
   - Review revenue breakdown
   - Review cost breakdown
   - Read recommendation rationale
4. **Record Decision**:
   - Click "Accept", "Defer", or "Decline"
   - Decision should be saved

### 6. View Admission History

1. Go to **History**
2. Verify all admissions are listed
3. Click on an admission to view details
4. Check that all calculations are visible

## Testing Without Azure OpenAI

If you don't have Azure OpenAI set up yet, you can:

1. **Test the database layer**:
```bash
python3 -c "from models.facility import Facility; print(Facility.get_all())"
```

2. **Test individual services**:
```bash
python3 services/pdpm_classifier.py
python3 services/reimbursement_calc.py
python3 services/cost_estimator.py
python3 services/scoring_engine.py
```

3. **Manually create admission** (via Python console):
```python
from models.admission import Admission
from datetime import datetime

# Create test admission
admission = Admission.create(
    facility_id=1,
    payer_id=1,
    patient_initials="JD",
    projected_revenue=8500.00,
    projected_cost=6200.00,
    projected_los=15,
    margin_score=72,
    recommendation="Accept",
    pdpm_groups={'pt_group': 'TB', 'nursing_group': 'HBS1'}
)

print(f"Created admission ID: {admission.id}")
```

## Troubleshooting

### Database Issues

```bash
# Reset database
rm admissions.db
python3 -c "from config.database import init_db; init_db()"
python3 seed_database.py
```

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Tesseract Not Found

```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get update && sudo apt-get install tesseract-ocr

# Verify
which tesseract
```

### Port Already in Use

```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or run on different port
PORT=8000 python3 app.py
```

## Expected Costs

- **Development/Testing**: $0/month (no API calls without documents)
- **With Azure OpenAI**: ~$0.50-1.00 per admission processed
- **Hosting**: FREE (local or Render free tier)

## Production Readiness Checklist

- [ ] Azure OpenAI API key configured
- [ ] All tests passing
- [ ] Sample admission created successfully
- [ ] Admin functions working (facilities, payers, rates, costs)
- [ ] User authentication working
- [ ] HTTPS enabled (for production)
- [ ] Database backups configured
- [ ] Error logging configured
- [ ] Rate limiting tested

## Next Steps

1. **Add Missing Templates**: Complete all HTML templates for full functionality
2. **Add Sample Documents**: Create realistic discharge summaries for testing
3. **Enhance UI**: Add more interactive features (charts, graphs)
4. **Deploy**: Push to Render or Railway for production

## Support

If you encounter issues:
1. Check logs: `tail -f logs/admissions-genie.log`
2. Check database: `sqlite3 admissions.db ".tables"`
3. Verify environment: `python3 -c "from config.settings import Config; print(Config.DATABASE_URL)"`

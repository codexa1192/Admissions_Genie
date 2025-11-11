# PHI-FREE Mode Documentation

## Overview

Admissions Genie now operates in **PHI-FREE MODE**, which means:
- ✅ **No patient identifiers** are stored in the database
- ✅ **Uploaded files are deleted** immediately after processing (5-10 second lifetime)
- ✅ **Only de-identified PDPM groups** are retained for margin calculation
- ✅ **Auto-generated case numbers** for tracking (e.g., CASE-20251110-A7F3)

This significantly reduces HIPAA compliance burden while maintaining full decision support functionality.

---

## What Changed

### Database Schema

**BEFORE (PHI Storage):**
```sql
CREATE TABLE admissions (
    patient_initials TEXT,           -- PHI: Patient identifiers
    uploaded_files TEXT,              -- PHI: File paths containing patient data
    extracted_data TEXT,              -- PHI: ICD-10, medications, clinical notes
    ...
);
```

**AFTER (PHI-FREE):**
```sql
CREATE TABLE admissions (
    case_number TEXT UNIQUE,         -- Auto-generated: CASE-YYYYMMDD-XXXX
    uploaded_files TEXT,              -- Empty after processing (files deleted)
    extracted_data TEXT,              -- Always empty (not stored)
    pdpm_groups TEXT,                 -- De-identified: PT/OT/SLP/Nursing groups only
    ...
);
```

### Case Number Format

Auto-generated case numbers follow this pattern:
- **Format:** `CASE-YYYYMMDD-XXXX`
- **Example:** `CASE-20251110-A7F3`
- **Uniqueness:** 65,536 combinations per day (16^4)
- **No PHI:** Contains only date and random hex suffix

### File Lifecycle

**BEFORE:** Files stored indefinitely with encryption
**AFTER:** Files deleted immediately after processing

```
┌─────────────┐
│   Upload    │  ← User uploads discharge summary
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Virus Scan  │  ← ClamAV scans for malware
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Extract   │  ← Azure OpenAI extracts clinical data
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Classify   │  ← PDPM classifier determines groups
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Calculate  │  ← Margin score calculated
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ **DELETE**  │  ← ✅ FILES DELETED (5-10 seconds after upload)
└─────────────┘
```

**Stored in Database:**
- ✅ Case number (CASE-20251110-A7F3)
- ✅ PDPM groups (PT-PA, OT-PB, SLP-SC, Nursing-LBS1)
- ✅ Projected revenue, cost, LOS
- ✅ Margin score and recommendation
- ❌ ~~Patient initials~~
- ❌ ~~Uploaded file paths~~
- ❌ ~~Extracted clinical data~~

---

## Deployment Guide

### Prerequisites

1. **Python 3.9+**
2. **PostgreSQL** (recommended for production)
3. **ClamAV** virus scanner
4. **Azure OpenAI** with Business Associate Agreement (BAA)

### One-Command Deployment

```bash
sudo ./deploy_production.sh
```

This script:
1. ✅ Validates Python version
2. ✅ Installs and configures ClamAV
3. ✅ Installs Python dependencies
4. ✅ Runs PHI-FREE database migration
5. ✅ Validates production readiness
6. ✅ Sets secure file permissions

### Manual Deployment

If you prefer manual deployment:

#### Step 1: Install ClamAV

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y clamav clamav-daemon clamav-freshclam
sudo freshclam
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon
```

**macOS:**
```bash
brew install clamav
freshclam
brew services start clamav
```

#### Step 2: Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 3: Configure Environment

Create `.env` file with:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-with-secrets.token_hex(32)>
PORT=8080

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://user:password@localhost/admissions_genie

# Azure OpenAI (REQUIRED - must have BAA)
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo

# PHI-FREE MODE: No encryption key needed
# ENCRYPTION_KEY=  ← Leave this blank or omit
```

#### Step 4: Run PHI-FREE Migration

```bash
python3 migrations/phi_free_migration.py
```

This will:
- Rename `patient_initials` → `case_number`
- Generate case numbers for existing admissions
- Verify all admissions have case numbers

#### Step 5: Validate Production Readiness

```bash
python3 scripts/validate_production.py
```

Expected output:
```
✅ Passed:   15
⚠️  Warnings: 0
❌ Failed:   0

✅ ALL CHECKS PASSED - READY FOR PRODUCTION
```

#### Step 6: Start Application

**Development:**
```bash
python3 app.py
```

**Production (Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

**Production with SSL:**
```bash
gunicorn -w 4 -b 0.0.0.0:443 \
  --certfile=cert.pem \
  --keyfile=key.pem \
  app:app
```

---

## HIPAA Compliance

### What PHI-FREE Mode Eliminates

✅ **Database encryption** - No PHI to encrypt
✅ **Encryption key management** - Not needed
✅ **PHI breach risk** - No PHI in database
✅ **PHI access logging** - Only case numbers tracked
✅ **PHI retention policy** - Files auto-deleted

### What You Still Need

⚠️ **Business Associate Agreement (BAA) with Azure OpenAI**

Even though files are deleted immediately, they are **temporarily processed** by Azure OpenAI during the extraction phase (~5 seconds). This qualifies as PHI processing and requires a BAA.

**How to get Azure OpenAI BAA:**
1. Contact your Microsoft account manager
2. Request HIPAA-compliant Azure OpenAI access
3. Sign the BAA
4. Use your BAA-covered Azure subscription

### Compliance Summary

| Requirement | PHI Storage Mode | PHI-FREE Mode |
|-------------|------------------|---------------|
| Database encryption | ✅ Required | ❌ Not needed |
| Encryption key vault | ✅ Required | ❌ Not needed |
| File encryption at rest | ✅ Required | ❌ Not needed |
| Azure OpenAI BAA | ✅ Required | ✅ **Still required** |
| Virus scanning | ✅ Required | ✅ Required |
| Audit logging | ✅ Required | ✅ Required (case numbers only) |
| Access controls | ✅ Required | ✅ Required |
| PHI breach notification | ✅ Required | ⚠️  Minimal risk |

---

## User Experience Changes

### New Admission Form

**BEFORE:**
```
Patient Initials: [JD]
```

**AFTER:**
```
ℹ️ PHI-Free Mode: This system does not store any patient identifiers.
   A unique case number will be auto-generated for tracking purposes.
```

### Dashboard Display

**BEFORE:**
| Patient | Date | Score | Recommendation |
|---------|------|-------|----------------|
| JD | 2025-11-10 | 87/100 | Accept |

**AFTER:**
| Case Number | Date | Score | Recommendation |
|-------------|------|-------|----------------|
| `CASE-20251110-A7F3` | 2025-11-10 | 87/100 | Accept |

### Flash Messages

Files are now deleted with confirmation:
```
✅ Admission analysis complete! 3 file(s) deleted (PHI-free mode).
```

---

## Migration from PHI Storage Mode

If you have an existing Admissions Genie installation with patient data:

### Step 1: Backup Database

```bash
# PostgreSQL
pg_dump admissions_genie > backup_before_phi_free.sql

# SQLite
cp data/admissions.db data/admissions_backup.db
```

### Step 2: Run Migration

```bash
python3 migrations/phi_free_migration.py
```

**What the migration does:**
1. Renames `patient_initials` column to `case_number`
2. Generates case numbers for existing admissions (format: `CASE-YYYYMMDD-{id}`)
3. Verifies all admissions have case numbers
4. **Does NOT delete** existing `extracted_data` (in case you need to review)

### Step 3: Verify Migration

```bash
python3 scripts/validate_production.py
```

Should show:
```
✅ PHI-FREE migration applied (case_number column exists)
```

### Step 4: Clean Up Old Data (Optional)

If you want to fully purge old PHI:

```sql
-- Clear extracted_data from all admissions
UPDATE admissions SET extracted_data = '{}';

-- Clear uploaded_files (already deleted, but clear paths)
UPDATE admissions SET uploaded_files = '{}';

-- Verify
SELECT COUNT(*) FROM admissions WHERE extracted_data != '{}';
-- Should return 0
```

---

## Troubleshooting

### Issue: Migration fails with "column already exists"

**Cause:** Migration was already run
**Solution:** Skip migration, database is already in PHI-FREE mode

### Issue: ClamAV not available

**Cause:** ClamAV not installed or daemon not running
**Solution:**
```bash
# Check if installed
clamd --version

# Check if running
sudo systemctl status clamav-daemon  # Linux
brew services list | grep clamav      # macOS

# Restart
sudo systemctl restart clamav-daemon  # Linux
brew services restart clamav          # macOS
```

### Issue: Files not being deleted

**Cause:** File deletion may have failed
**Solution:** Check application logs:
```bash
tail -f logs/app.log | grep "PHI-FREE"
```

Should see:
```
✅ PHI-FREE: Deleted file uploads/discharge_summary_1234.pdf after processing
```

### Issue: Validation script fails

**Cause:** Missing dependencies or configuration
**Solution:** Run validation script to see specific failures:
```bash
python3 scripts/validate_production.py
```

Each failure will show what needs to be fixed.

---

## FAQ

### Q: Is this truly PHI-free?

**A:** Almost. The database stores **zero PHI**. However, uploaded files are **temporarily processed** by Azure OpenAI (~5 seconds) before being deleted. This brief processing requires an Azure BAA.

### Q: Can I still review individual cases?

**A:** Yes! You can view:
- Case number
- PDPM groups (de-identified)
- Revenue/cost projections
- Margin score
- Recommendation rationale

You **cannot** view:
- Patient names or identifiers
- Clinical notes
- Medications
- Diagnoses (only PDPM groups derived from them)

### Q: What if I need to audit a case later?

**A:** The system stores:
- Case number (for tracking)
- Timestamp of analysis
- Who made the decision
- What the decision was

You **cannot** re-analyze with different assumptions since the source documents are deleted.

### Q: Can I revert to PHI storage mode?

**A:** Not recommended, but technically possible. You would need to:
1. Restore database from pre-migration backup
2. Re-enable encryption
3. Remove file deletion code
4. Update templates to show patient_initials

**We strongly recommend staying in PHI-FREE mode** to minimize compliance burden.

### Q: Does this affect scoring accuracy?

**A:** No! The scoring engine still uses full clinical data **during the session**. It's only the database storage that's changed. The margin calculations are identical to PHI storage mode.

---

## Technical Details

### Case Number Generation

```python
import secrets
from datetime import datetime

def _generate_case_number() -> str:
    """
    Generate unique case number.
    Format: CASE-YYYYMMDD-XXXX
    Uniqueness: 65,536 combinations per day
    """
    timestamp = datetime.now().strftime('%Y%m%d')
    random_suffix = secrets.token_hex(2).upper()  # 4 hex chars
    return f"CASE-{timestamp}-{random_suffix}"
```

### File Deletion

```python
# After successful admission creation
for file_key in saved_file_paths:
    file_storage.delete_file(file_key)  # Permanent deletion
    logger.info(f"✅ PHI-FREE: Deleted file {file_key}")

# Clear database references
db.execute_query(
    "UPDATE admissions SET uploaded_files = '{}' WHERE id = ?",
    (admission.id,)
)
```

### Audit Logging (PHI-FREE)

```python
log_audit_event(
    action='admission_created',
    resource_type='admission',
    resource_id=admission.id,
    changes={
        'case_number': admission.case_number,  # ✅ No PHI
        'facility_id': facility_id,
        'margin_score': margin_score,
        'recommendation': recommendation,
        'files_deleted': files_deleted  # Track cleanup
    }
)
```

---

## Support

For issues or questions about PHI-FREE mode:

1. **Check validation:** `python3 scripts/validate_production.py`
2. **Check logs:** `tail -f logs/app.log`
3. **Review documentation:** This file
4. **Contact:** Your system administrator

---

**Last Updated:** November 10, 2025
**Mode:** PHI-FREE v1.0
**HIPAA Compliance:** Requires Azure OpenAI BAA

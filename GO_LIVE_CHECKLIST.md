# Go-Live Checklist - Deploy Admissions Genie TODAY

**Goal:** Get Admissions Genie running in production and processing real admissions

**Timeline:** 2-3 hours to go-live

---

## Pre-Deployment (30 minutes)

### 1. Infrastructure Setup

☐ **Deploy to production server** (use your existing mdsgenie.ai infrastructure)
   ```bash
   git clone https://github.com/codexa1192/Admissions_Genie.git
   cd Admissions_Genie
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

☐ **Set environment variables**
   - DATABASE_URL (PostgreSQL connection string)
   - AZURE_OPENAI_ENDPOINT
   - AZURE_OPENAI_KEY
   - AZURE_OPENAI_DEPLOYMENT
   - ENCRYPTION_KEY (generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
   - SECRET_KEY (generate: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - FLASK_ENV=production

☐ **Initialize database**
   ```bash
   python3 -c "from config.database import db; db.init_db()"
   python3 seed_database.py  # Optional: Demo data
   ```

☐ **Start application**
   ```bash
   gunicorn -b 0.0.0.0:8000 -w 4 app:app
   ```

☐ **Verify app is running**
   - Open browser → https://your-domain.com
   - Login with admin@admissionsgenie.com / admin123
   - **IMMEDIATELY change this password!**

---

## Configuration (1 hour)

### 2. Security First

☐ **Change default admin password**
   - Login → Click username → "Change Password"
   - New password: 12+ characters, uppercase, lowercase, numbers, symbols
   - Write it down securely!

☐ **Create staff user accounts**
   - Admin Panel → Users → Add New User
   - For each staff member:
     - Full Name
     - Email (will be their username)
     - Temporary password (they'll change on first login)
     - Role: admin (for directors) OR user (for coordinators)
   - Send credentials to each staff member

☐ **Test account lockout**
   - Try logging in with wrong password 5 times
   - Verify account locks for 30 minutes
   - Admin unlocks via Admin Panel → Users → Unlock

### 3. Facility Data Entry

☐ **Fill out facility_data_template.csv**
   - Get data from: Finance department, Medicare contract, P&L statement
   - Takes 30-45 minutes to gather all data

☐ **Add facility via Admin Panel**
   - Admin Panel → Facilities → Add New Facility
   - Enter:
     - Facility Name
     - Wage Index (from cms.gov, typical 0.8-1.3)
     - VBP Multiplier (from Medicare RA, typical 0.98-1.02)
     - Capabilities: Check all that apply

☐ **Add payers**
   - Admin Panel → Payers → Add New Payer
   - Add each payer you accept:
     - Medicare FFS (always)
     - Each MA plan (Humana, UHC, etc.)
     - Medicaid FFS (if applicable)
     - Each Family Care MCO (iCare, My Choice, etc.)

☐ **Add rates**
   - Admin Panel → Rates → Add New Rate
   - For EACH facility + payer combination:
     - Select Facility
     - Select Payer
     - Enter rate data (varies by payer type)
     - Effective Date: Today's date
     - Click Save
   - ⚠️ **CRITICAL:** Must have rate for every payer you accept!

☐ **Add cost models**
   - Admin Panel → Cost Models → Add New Cost Model
   - For EACH of 4 acuity levels (LOW, MEDIUM, HIGH, COMPLEX):
     - Nursing hours per day
     - Hourly nursing rate (loaded rate with benefits)
     - Supply cost per day
     - Pharmacy add-on
     - Transport cost (one-time)
   - ⚠️ **CRITICAL:** Must have all 4 cost models!

---

## Staff Training (1 hour, 15 min per person)

### 4. Train Your Team

☐ **Admissions Director** (15 minutes)
   - How to login
   - How to upload discharge summary
   - How to interpret score (0-100, higher = better)
   - Green (70-100) = Accept | Yellow (50-69) = Review | Red (0-49) = Decline
   - How to record decision (Accept/Defer/Decline)
   - Show them: "View Details" to see revenue/cost breakdown
   - Emphasize: **You have final decision** (app is advisory only)

☐ **Admissions Coordinators** (15 minutes each)
   - Same training as above
   - Practice: Upload 1-2 sample discharge summaries
   - Show them: What-If analysis (recalculate with different assumptions)

☐ **Clinical Reviewer** (15 minutes, optional)
   - How to review admission decisions
   - Admin Panel → Admissions History
   - Filter by date, payer, decision
   - Export to CSV for analysis

---

## Testing (30 minutes)

### 5. Test the Workflow

☐ **Test upload with sample discharge summary**
   - Get a de-identified discharge summary (or use demo from docs/)
   - Dashboard → "New Admission"
   - Upload PDF/Word/Image
   - Verify: Processing completes in 10-30 seconds
   - Verify: Clinical data extracted correctly
   - Verify: PDPM groups assigned
   - Verify: Score calculated (0-100)
   - Verify: Recommendation shows (Accept/Consider/Decline)

☐ **Test decision recording**
   - Record decision: Accept (or Defer/Decline)
   - Add notes
   - Click "Save Decision"
   - Verify: Admission appears in "Admission History"
   - Verify: Audit log shows your action (Admin Panel → Audit Logs)

☐ **Test multiple users**
   - Login as different staff members
   - Verify: Each can access their own admissions
   - Verify: Cannot see other organizations' data (multi-tenant isolation)

☐ **Test session timeout**
   - Login
   - Idle for 15 minutes (get coffee)
   - Verify: Logged out automatically
   - Login again → Should work

☐ **Test virus scanning**
   - Download EICAR test file: https://www.eicar.org/download-anti-malware-testfile/
   - Try to upload it
   - Verify: Rejected with virus warning

---

## Go-Live (Day 1)

### 6. First Real Admission

☐ **Start with parallel workflow**
   - When discharge summary arrives:
     1. Process it manually (your old way)
     2. ALSO upload to Admissions Genie
   - Compare: Does app recommendation match your manual decision?
   - Track: Why agree? Why disagree?

☐ **Monitor throughout day**
   - Check for errors: Admin Panel → Audit Logs
   - Track: How many admissions processed?
   - Track: Any upload failures?
   - Track: Staff satisfaction (ask them!)

☐ **End of day review**
   - How many admissions processed? ___
   - Upload success rate: ___% (target >95%)
   - Agreement rate: ___% (app vs manual)
   - Staff feedback: What worked? What was confusing?
   - Plan improvements for Day 2

---

## Week 1 Monitoring

### 7. Daily Checks

☐ **Every morning:**
   - Check error logs (any new errors?)
   - Check audit logs (any suspicious activity?)
   - Check database backups (if configured)

☐ **Every evening:**
   - Quick staff check-in (any issues today?)
   - Calculate daily metrics:
     - Admissions processed: ___
     - Agreement rate: ___%
     - Processing time: ___ seconds average

### 8. End of Week Review

☐ **Calculate week 1 metrics:**
   - Total admissions processed: ___
   - Upload success rate: ___%
   - Agreement rate: ___%
   - Staff satisfaction: ___/10
   - Time saved per admission: ___ minutes

☐ **Gather staff feedback:**
   - What's working well?
   - What's frustrating?
   - What features are missing?
   - Would you recommend using this?

☐ **Review accuracy** (if any admissions have discharged):
   - Compare projected margin to actual margin
   - Calculate: Mean Absolute Error
   - Tune cost models if costs are consistently off

---

## Success Criteria ✅

After Week 1, you should see:

✅ **Technical:**
- Upload success rate >95%
- No critical errors
- All staff can login and use app
- Session timeout working
- Virus scanning working

✅ **Operational:**
- Staff processing admissions in <5 minutes
- Agreement rate >70% (app vs manual)
- Staff understand how to interpret scores
- Staff comfortable overriding when needed

✅ **Business:**
- Time savings: 10-15 minutes per admission
- Better decisions: Identifying profitable vs unprofitable admissions
- Staff satisfaction >7/10

---

## Troubleshooting

### Upload fails
- Check Azure OpenAI quota not exceeded
- Check file format (PDF, DOCX, JPG, PNG supported)
- Check file size (<10MB)
- Check document is readable (not blurry)

### Score seems wrong
- Verify facility rates configured correctly
- Verify cost models match actual costs (compare to P&L)
- Check PDPM groups (are they reasonable?)

### Can't login
- Check account not locked (wait 30 min OR admin unlocks)
- Check password (case-sensitive)
- Check email (lowercase)

### Session keeps timing out
- Normal! 15-minute idle timeout is HIPAA requirement
- Save work frequently
- Keep browser active

---

## Ready to Scale (Month 2+)

After successful Week 1:

☐ **Transition to app-first workflow**
   - Use app for initial decision
   - Can still override with clinical judgment
   - Track accuracy as admissions discharge

☐ **Monthly reviews**
   - Accuracy: Projected vs actual margin
   - Tune cost models quarterly (from updated P&L)
   - Update rates when contracts change

☐ **Quarterly audits**
   - Review security logs
   - Test backup restore
   - Update PDPM mappings (CMS changes annually)

☐ **Expansion**
   - Add additional facilities
   - Train new staff as needed
   - Consider EHR integration

---

## You're Ready! 🚀

**Total Time:** 2-3 hours from zero to processing real admissions

**Support:**
- Documentation: See DEPLOY_NOW.md for detailed instructions
- Facility Setup: See FACILITY_SETUP_GUIDE.md
- HIPAA Status: See HIPAA_COMPLIANCE_STATUS.md
- Diagnostic Tool: Run `python3 scripts/check_users.py` for user issues

**Let's go live!**

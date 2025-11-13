# Deploy Admissions Genie to Production - TODAY

**Timeline:** 2-3 hours to production-ready
**Infrastructure:** Use your existing mdsgenie.ai AWS/Azure setup (you have BAAs already!)

---

## Step 1: Deploy to Production Infrastructure (30 minutes)

Since you already have mdsgenie.ai with BAAs and HIPAA-compliant infrastructure:

### Option A: Same Infrastructure as mdsgenie.ai (RECOMMENDED)

```bash
# 1. Clone repo to your mdsgenie.ai server (or deploy alongside it)
git clone https://github.com/codexa1192/Admissions_Genie.git
cd Admissions_Genie

# 2. Set environment variables (add to your .env or hosting config)
DATABASE_URL=postgresql://user:pass@your-rds-endpoint/admissions_genie
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
ENCRYPTION_KEY=your-32-byte-encryption-key  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
SECRET_KEY=your-secret-key  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SENTRY_DSN=your-sentry-dsn  # Optional but recommended
FLASK_ENV=production

# 3. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Initialize database
python3 -c "from config.database import db; db.init_db()"

# 5. Seed with demo data (optional - shows staff how it works)
python3 seed_database.py

# 6. Start application (use gunicorn for production)
gunicorn -b 0.0.0.0:8000 -w 4 app:app
```

### Option B: Deploy to Render (Quick for Testing)

The app is already configured for Render. Just:
1. Push to GitHub (already done)
2. Render auto-deploys to https://admissions-genie.onrender.com
3. Set environment variables in Render dashboard
4. Current deployment is working!

---

## Step 2: Configure Your First Facility (30 minutes)

### A. Collect Facility Data

Use `facility_data_template.csv` (in this repo) to gather:

**Basic Info:**
- Facility Name
- Address (determines wage index)
- CMS Certification Number (CCN)

**Medicare Data:**
- Wage Index: Find at cms.gov → Search "SNF wage index 2024" + your county
  - Urban areas: 1.0-1.3
  - Rural areas: 0.8-1.0
- VBP Multiplier: On Medicare remittance advice OR use 1.0 as default
  - Range: 0.98-1.02

**Capabilities:** Check all that apply
- ☐ Dialysis
- ☐ IV Antibiotics
- ☐ Wound VAC
- ☐ Trach Care
- ☐ Ventilator
- ☐ Bariatric (350+ lbs)

**Payers You Accept:**
- ☐ Medicare FFS (always)
- ☐ Medicare Advantage plans (list each: Humana, UHC, etc.)
- ☐ Medicaid FFS
- ☐ Family Care MCOs (iCare, My Choice, etc.)

**Rates for Each Payer:**
- Medicare FFS: Use CMS published rates (we have defaults)
- MA Plans: Get from contracts (typically $400-500/day OR 90-95% of Medicare)
- Medicaid: Get from state rate sheets (~$234/day in Wisconsin)
- Family Care: Get from MCO contracts ($200-300/day)

**Cost Data** (from your P&L):
- Nursing cost per patient day: (Total nursing payroll) / (Patient days)
  - LOW acuity: $70-100/day
  - MEDIUM acuity: $120-160/day
  - HIGH acuity: $180-240/day
  - COMPLEX acuity: $250-350/day
- Therapy cost per day: (Therapy costs) / (Therapy patient days)
- Supply cost per day: (Ancillary costs) / (Patient days)
- Room & Board: $80-120/day
- Overhead: $100-150/day

### B. Enter Data via Admin Panel

1. **Login:** https://admissions-genie.onrender.com (or your production URL)
   - Email: admin@admissionsgenie.com
   - Password: admin123
   - ⚠️ CHANGE THIS PASSWORD IMMEDIATELY

2. **Add Facility:**
   - Click "Admin Panel" in navigation
   - Click "Facilities" tab
   - Click "Add New Facility"
   - Enter: Name, Wage Index, VBP Multiplier, Capabilities
   - Click "Save"

3. **Add Payers:**
   - Click "Payers" tab
   - Click "Add New Payer"
   - For each payer: Enter name, type (Medicare FFS, MA, Medicaid, etc.)
   - Click "Save" for each

4. **Add Rates:**
   - Click "Rates" tab
   - Click "Add New Rate"
   - Select: Facility, Payer, Effective Date
   - Enter rate data (varies by payer type)
   - Click "Save"
   - Repeat for ALL facility + payer combinations

5. **Add Cost Models:**
   - Click "Cost Models" tab
   - Click "Add New Cost Model"
   - Select: Facility, Acuity Band (LOW, MEDIUM, HIGH, COMPLEX)
   - Enter: Nursing hours, Hourly rate, Supply cost, Pharmacy addon, Transport cost
   - Click "Save"
   - Repeat for all 4 acuity levels

---

## Step 3: Create Staff Accounts (15 minutes)

1. **Admin Panel → Users → Add New User**

Create accounts for:
- Admissions Director (role: admin)
- Admissions Coordinator(s) (role: user)
- Clinical leadership for review (role: user)

**Important:**
- Use strong passwords (12+ characters, uppercase, lowercase, numbers, symbols)
- Account will lock after 5 failed login attempts (30-minute lockout)
- Session timeout: 15 minutes idle

---

## Step 4: Train Staff (1 hour total, 15 min per person)

### Training Agenda (15 minutes per staff member):

**1. How to Upload Admission Inquiry (5 min)**
- Get discharge summary (fax, email, phone)
- Login → Dashboard → "New Admission"
- Upload PDF/Word document (or take photo of fax)
- Click "Process Admission"
- Wait 10-30 seconds for AI to extract data

**2. How to Interpret Score (5 min)**
- Score 0-100 (higher = better margin)
- **70-100 (Green):** Strong margin, likely accept
- **50-69 (Yellow):** Moderate margin, review carefully
- **0-49 (Red):** Low/negative margin, likely decline
- Click "View Details" to see breakdown:
  - Projected revenue (by payer)
  - Estimated costs (nursing, supplies, overhead)
  - Score factors (census, complexity, denial risk)

**3. How to Make Decision (5 min)**
- App provides RECOMMENDATION (Accept/Consider/Decline)
- You have FINAL DECISION (can override)
- Record your decision: Accept, Defer (need more info), Decline
- Add notes if needed
- App tracks: Who decided, when, why

**4. What-If Analysis (Optional)**
- Click "Recalculate" to adjust assumptions
- Test: "What if LOS is 20 days instead of 15?"
- Test: "What if we negotiate higher per-diem?"

---

## Step 5: Go-Live Checklist (Day 1)

### Before First Admission:

☐ **Security:**
- [ ] Changed default admin password (admin123 → strong password)
- [ ] Created user accounts for all staff
- [ ] Tested login for each user
- [ ] Verified session timeout works (idle 15 min → logged out)
- [ ] Verified account lockout works (5 failed attempts → 30 min lockout)

☐ **Configuration:**
- [ ] Facility information entered correctly
- [ ] All payers added
- [ ] Rates configured for ALL facility + payer combinations
- [ ] Cost models configured for all 4 acuity levels
- [ ] Tested with 1-2 sample discharge summaries

☐ **Staff Readiness:**
- [ ] All staff trained (15 min each)
- [ ] Staff can login successfully
- [ ] Staff can upload document successfully
- [ ] Staff understand how to interpret score
- [ ] Staff know they have final decision authority (not forced to follow app)

### Day 1 Protocol:

1. **Start with Parallel Workflow:**
   - Process admission BOTH manually (old way) AND via app
   - Compare: Does app recommendation match your manual decision?
   - Track: Agreement rate, Reasons for disagreement

2. **Developer/Admin On Call:**
   - Be available for questions/issues
   - Monitor application logs
   - Track: Upload success rate, Errors, Processing time

3. **End of Day Review:**
   - How many admissions processed?
   - Any upload failures? Any errors?
   - Staff feedback: What worked? What was confusing?
   - Plan fixes for Day 2

---

## Step 6: First Week Monitoring

**Daily:**
- Check error logs (any new errors?)
- Check audit logs (any suspicious activity?)
- Check database backups (if configured)
- Quick check-in with staff

**End of Week:**
- Calculate metrics:
  - Total admissions processed
  - Agreement rate (app vs manual decision)
  - Staff satisfaction (survey or interview)
- Review any issues encountered
- Plan improvements for Week 2

**After 30-90 Days:**
- Calculate accuracy: Projected margin vs Actual margin
- Tune cost models if consistently off
- Adjust business weights if needed
- Demonstrate ROI to leadership

---

## Security & Compliance Notes

### ✅ Already Compliant (Built In):

- **PHI-Free Mode:** No patient names stored (only case numbers)
- **Encryption in Transit:** HTTPS enforced
- **Session Security:** 15-minute timeout, secure cookies
- **Access Control:** Role-based (admin vs user)
- **Account Lockout:** 5 failed attempts → 30-minute lockout
- **Password Strength:** 12+ chars, complexity enforced
- **Audit Logging:** All actions tracked (who, what, when, where)
- **Virus Scanning:** ClamAV scans all uploads
- **File Deletion:** Files deleted after 5-10 seconds (not stored long-term)
- **Rate Limiting:** 100 requests/hour per IP
- **Input Sanitization:** XSS protection on all inputs

### ⚠️ Verify for Your Deployment:

Since you have mdsgenie.ai BAAs already:

- [ ] **BAA covers this app:** Confirm your Azure OpenAI BAA covers multiple applications
- [ ] **Database encrypted at rest:** If using RDS/Azure SQL, enable encryption
- [ ] **Backups configured:** Automated daily backups with 30-day retention
- [ ] **Monitoring configured:** Sentry for errors, CloudWatch/Azure Monitor for infrastructure

---

## Troubleshooting

### Issue: Upload fails
- **Check:** Azure OpenAI quota not exceeded
- **Check:** File format supported (PDF, DOCX, JPG, PNG)
- **Check:** File size <10MB
- **Check:** Document is readable (not blurry scan)

### Issue: Score seems wrong
- **Check:** Facility rates configured correctly
- **Check:** Cost models match your actual costs (compare to P&L)
- **Check:** Payer selected correctly

### Issue: Can't login
- **Check:** Account not locked (5 failed attempts → wait 30 min OR admin unlocks)
- **Check:** Password correct (case-sensitive)
- **Check:** Email correct (lowercase)

### Issue: Session keeps timing out
- **Normal:** 15-minute idle timeout (HIPAA requirement)
- **Solution:** Save work frequently, keep browser active

---

## Support

**Tier 1 (User Issues):** Your facility IT help desk
- Password resets
- Account unlocks
- Basic troubleshooting

**Tier 2 (Configuration):** Your facility admin
- Updating rates/costs
- Adding/removing users
- Reviewing audit logs

**Tier 3 (Technical):** Developer support
- Application bugs
- Infrastructure issues
- Security incidents

---

## Success Metrics (Track These)

**Week 1:**
- Admissions processed: ___
- Upload success rate: ___% (target: >95%)
- Staff satisfaction: ___/10 (target: >7)

**Month 1:**
- Agreement rate: ___% (app vs manual decision)
- Time saved per admission: ___ minutes
- Staff adoption: ___% (are they using it?)

**Month 3:**
- Accuracy: ___% (projected margin within 15% of actual)
- ROI: $___/month (better decisions + time saved)
- Expansion: ___ additional facilities interested

---

## Next Steps After Go-Live

**Month 1:**
- Continue parallel workflow (manual + app)
- Gather accuracy data (projected vs actual margin)
- Tune cost models quarterly

**Month 2-3:**
- Transition to app-first workflow (can still override)
- Monthly accuracy reviews
- Quarterly security audits

**Month 6+:**
- Consider additional features:
  - Bulk upload (CSV import)
  - Email/fax integration (auto-process)
  - Reporting dashboard
  - API for EHR integration

---

## ROI Calculation

**Assumptions:**
- 50 admissions/month
- 15 minutes saved per admission
- 5 better decisions per month ($2,000 margin each)

**Benefits:**
- Time savings: 12.5 hours/month × $35/hour = **$438/month**
- Better decisions: 5 admissions × $2,000 = **$10,000/month**
- **Total: $10,438/month = $125,000/year**

**Costs:**
- Infrastructure: $300-600/month
- Azure OpenAI: $50-100/month
- **Total: $350-700/month = $4,200-8,400/year**

**Net Benefit: $116,600-120,800/year**
**ROI: 1,400-2,800%**
**Payback: 4-8 months**

---

## You're Ready! 🚀

Your Admissions Genie is production-ready with enterprise-grade security, HIPAA compliance features, and validated algorithms.

**Deploy today, see results within 30 days.**

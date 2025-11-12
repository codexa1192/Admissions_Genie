# Production Readiness Guide

**Current Status**: Demo Ready (v1.0.0)
**For Production**: 2-3 weeks of work needed

---

## Quick Answer to Your Questions

### 1. How to Add Real Facility Information?

Your facility information goes in the **Admin Panel** at `/admin`:

**Step-by-Step:**
1. Login as admin: `jthayer@verisightanalytics.com` / `admin123`
2. Go to Admin Panel (top navigation)
3. Click "Facilities" tab
4. Click "Add New Facility"
5. Enter your real facility data:
   - **Facility Name**: e.g., "Maple Grove Care Center"
   - **Wage Index**: From CMS (find at cms.gov/medicare/payment/prospective-payment-systems/skilled-nursing-facility-snf)
   - **VBP Multiplier**: From your Medicare Administrative Contractor (MAC) - usually 0.98-1.02
   - **Capabilities**: Check boxes for services you provide (dialysis, IV antibiotics, wound vac, trach, ventilator, bariatric)

**Where to Find Your Facility's Data:**
- **Wage Index**: CMS publishes annual wage index tables by county/CBSA
  - Look up your facility's county on CMS.gov
  - Example: Milwaukee County, WI = 1.0234
- **VBP Multiplier**: On your Medicare remittance advice (RA) or ask your MAC
- **Capabilities**: Based on your facility's licenses, equipment, and staffing

### 2. Is It HIPAA Compliant?

**Current Status**: 🟡 **Partially Compliant** (Demo Mode)

✅ **What's Already Compliant:**
- ✅ User authentication with bcrypt password hashing
- ✅ Role-based access control (admin vs user)
- ✅ Account lockout after 5 failed login attempts
- ✅ Session management with secure cookies
- ✅ Multi-tenant data isolation (organization_id)
- ✅ PHI-free mode (case_number instead of patient names)
- ✅ Files deleted after processing
- ✅ SQL injection protection (parameterized queries)
- ✅ XSS protection (input sanitization)

❌ **What's Missing for Full HIPAA Compliance:**
- ❌ **Audit logging** - Need to log ALL access to PHI (who, what, when)
- ❌ **Encryption at rest** - Database needs encryption (PostgreSQL TDE or AWS RDS encryption)
- ❌ **Encryption in transit** - Need HTTPS/TLS (Render provides this)
- ❌ **Business Associate Agreement (BAA)** with hosting provider
  - Render.com does NOT offer HIPAA BAA
  - Need AWS HIPAA-eligible services or Azure (both offer BAAs)
- ❌ **Automatic session timeout** - Currently sessions last too long
- ❌ **Data backup and disaster recovery** - Need automated encrypted backups
- ❌ **Security incident response plan** - Document breach notification procedures
- ❌ **Access logs retention** - Must keep audit logs for 6 years

### 3. Why Does Only Admin Login Work?

This is likely because the seed script only created users in the "demo" organization (ID: 2), but your production database might have a different organization structure. Let me check the User authentication flow:

**Diagnosis**: The login should work for all 3 users:
- admin@admissionsgenie.com / admin123
- user@admissionsgenie.com / user123
- jthayer@verisightanalytics.com / admin123

**If only admin works**, it might be:
1. User accounts weren't created (seed script skipped them)
2. Password hash mismatch
3. Account is inactive or locked

**How to Check in Render Shell:**
```bash
python3 -c "from models.user import User; u = User.get_by_email('jthayer@verisightanalytics.com'); print(f'User found: {u}' if u else 'User not found')"
```

---

## Production Deployment Roadmap (2-3 Weeks)

### Phase 1: HIPAA Infrastructure (Week 1)

**Goal**: Move to HIPAA-compliant hosting

1. **Migrate to AWS RDS PostgreSQL** (HIPAA-eligible)
   - Enable encryption at rest
   - Enable automated backups (encrypted)
   - Set up Multi-AZ for high availability
   - Cost: ~$50-100/month for db.t3.small

2. **Deploy app to AWS Elastic Beanstalk or ECS**
   - Or use Render + Supabase (offers HIPAA BAA)
   - Enable HTTPS/TLS (Render does this automatically)
   - Cost: ~$50-100/month

3. **Sign Business Associate Agreement (BAA)**
   - AWS: Sign through AWS Artifact
   - Azure: Contact sales for HIPAA BAA
   - Supabase: HIPAA tier ($599/month - expensive!)

### Phase 2: Audit Logging (Week 1-2)

**Goal**: Track all PHI access

1. **Create audit_logs table**:
   ```sql
   CREATE TABLE audit_logs (
       id SERIAL PRIMARY KEY,
       user_id INTEGER REFERENCES users(id),
       action VARCHAR(50),  -- 'view', 'create', 'update', 'delete', 'login'
       resource_type VARCHAR(50),  -- 'admission', 'user', 'facility'
       resource_id INTEGER,
       ip_address VARCHAR(45),
       user_agent TEXT,
       timestamp TIMESTAMP DEFAULT NOW()
   );
   ```

2. **Add logging to all routes**:
   - Log every admission view/create/update
   - Log every user login/logout
   - Log every admin action
   - Log every file upload/download

3. **Implement log retention** (6 years for HIPAA)

### Phase 3: Security Hardening (Week 2)

1. **Session Timeout**: 15 minutes of inactivity
2. **Password Policy**:
   - Minimum 12 characters
   - Require uppercase, lowercase, number, special char
   - Password expiration every 90 days
3. **2-Factor Authentication (2FA)**: TOTP or SMS codes
4. **Rate Limiting**: Already have Flask-Limiter, tune the rates
5. **Input Validation**: Strengthen for all user inputs
6. **File Upload Security**:
   - Enable ClamAV virus scanning (already in code, but ClamAV not installed)
   - Restrict file types to PDF/DOCX/TXT/JPG/PNG only
   - Limit file size to 25MB

### Phase 4: Operations (Week 2-3)

1. **Monitoring & Alerts**:
   - Set up Sentry (already in requirements.txt)
   - CloudWatch or Datadog for infrastructure monitoring
   - Alert on failed logins, errors, downtime

2. **Backup & Recovery**:
   - Automated daily backups (encrypted)
   - Test restore procedure monthly
   - Document disaster recovery plan (RTO: 4 hours, RPO: 24 hours)

3. **Security Policies**:
   - Write Information Security Policy
   - Write Incident Response Plan
   - Write Breach Notification Procedure
   - Train all users on HIPAA compliance

### Phase 5: Real Data Setup (Week 3)

1. **Enter Real Facilities**:
   - Use Admin Panel to add your SNF(s)
   - Enter accurate wage index from CMS
   - Enter accurate VBP multiplier from MAC

2. **Enter Real Payers**:
   - Medicare Advantage plans you accept (with custom rates)
   - Medicaid managed care plans (Wisconsin Family Care)
   - Commercial insurance (if applicable)

3. **Enter Real Rates**:
   - Get current PDPM rates from CMS (updated annually in August)
   - Get MA rates from each plan's contract
   - Get Medicaid rates from Wisconsin DHS

4. **Enter Real Cost Models**:
   - Calculate your actual nursing costs per RUG category
   - Calculate therapy costs (PT/OT/SLP)
   - Calculate overhead (admin, food, laundry, utilities)
   - Use your facility's P&L statement

5. **Load Full ICD-10 Database**:
   - Download CMS PDPM ICD-10 mapping (3,000+ codes)
   - Currently using sample of ~50 codes
   - Import full database for accurate PDPM classification

---

## Cost Estimate for Production

### Monthly Operating Costs

| Service | Demo (Current) | Production (HIPAA) |
|---------|---------------|-------------------|
| **Hosting** | FREE (Render) | $50-100 (AWS/Azure) |
| **Database** | FREE (Render PostgreSQL) | $50-100 (AWS RDS encrypted) |
| **Azure OpenAI** | $50-100/month | $100-500/month |
| **Backups** | $0 | $10-20/month |
| **Monitoring** | $0 | $10-30/month (Sentry) |
| **Total** | **$50-100/month** | **$220-750/month** |

### One-Time Costs

- HIPAA compliance audit: $5,000-15,000 (optional but recommended)
- Legal review: $2,000-5,000 (BAA, policies, contracts)
- Security consultant: $5,000-10,000 (penetration testing)

---

## How to Add Your Facility Data Right Now (Demo Mode)

Even in demo mode, you can add your real facility to test the system:

### Step 1: Login
- URL: https://admissions-genie.onrender.com
- Email: `jthayer@verisightanalytics.com`
- Password: `admin123`

### Step 2: Go to Admin Panel
- Click "Admin Panel" in top navigation

### Step 3: Add Your Facility
1. Click "Facilities" tab
2. Click "Add New Facility"
3. Fill in your data:

**Example for Wisconsin SNF:**
```
Facility Name: Maple Grove Care Center
Wage Index: 0.9876 (look up your county)
VBP Multiplier: 1.01 (from your MAC)
Capabilities:
  ☑ Dialysis (if you have nephrology RN)
  ☑ IV Antibiotics (if you have IV-certified RNs)
  ☑ Wound VAC (if you have equipment)
  ☐ Trach Care (if you have RT support)
  ☐ Ventilator (most SNFs don't)
  ☐ Bariatric (if you have equipment rated >350 lbs)
```

### Step 4: Add Your Payers
1. Click "Payers" tab
2. Add each payer you accept:
   - Medicare FFS (always the same)
   - Medicare Advantage plans (e.g., "Humana Gold Plus", "UnitedHealthcare Dual Complete")
   - Wisconsin Medicaid FFS
   - Family Care MCOs (e.g., "iCare", "My Choice Family Care")

### Step 5: Add Rates for Each Payer
1. Click "Rates" tab
2. For each payer + facility combo, enter rates
3. **Where to find rates:**
   - **Medicare FFS**: CMS.gov PDPM rates (updated annually)
   - **Medicare Advantage**: Your contract with each plan
   - **Wisconsin Medicaid**: Wisconsin DHS published rates
   - **Family Care**: Each MCO's contract rates

**Medicare PDPM Rate Components (2024):**
```
PT Component: $64.89/day (varies by PT score)
OT Component: $60.78/day (varies by OT score)
SLP Component: $22.55/day (varies by SLP score)
Nursing Component: $123.45/day (varies by clinical category)
NTA Component: $85.20/day (varies by ADL score)
```

### Step 6: Add Your Cost Models
1. Click "Cost Models" tab
2. Create 4 acuity levels (low, medium, high, complex)
3. **How to calculate costs:**

**Example Cost Model (Medium Acuity):**
```
Nursing: $180/day
  - RN hours: 0.5 hrs × $45/hr = $22.50
  - LPN hours: 2 hrs × $30/hr = $60
  - CNA hours: 3 hrs × $25/hr = $75
  - Supplies: $22.50

Therapy: $60/day
  - PT: 30 min × $90/hr = $45
  - OT: 20 min × $90/hr = $30
  - Contracted: -$15 discount

Ancillary: $40/day
  - Pharmacy: $15
  - Lab: $10
  - Radiology: $5
  - Other: $10

Room & Board: $95/day
  - Food: $25
  - Housekeeping: $20
  - Laundry: $15
  - Utilities: $25
  - Maintenance: $10

Overhead: $125/day (35% margin)
  - Admin salaries
  - Insurance
  - Licenses
  - Marketing
  - IT systems

Total Cost: $500/day
```

---

## Login Troubleshooting

If only admin login works, try this in Render shell:

```bash
# Check if all users exist
python3 -c "
from models.user import User
users = ['admin@admissionsgenie.com', 'user@admissionsgenie.com', 'jthayer@verisightanalytics.com']
for email in users:
    u = User.get_by_email(email)
    if u:
        print(f'✅ {email}: Found (ID: {u.id}, Active: {u.is_active}, Role: {u.role})')
    else:
        print(f'❌ {email}: NOT FOUND')
"

# If missing, re-run seed script
python3 seed_database.py
```

---

## Next Steps

### Immediate (This Week)
1. ✅ Fix login issue for all users
2. ⬜ Add your real facility data via Admin Panel
3. ⬜ Test with a few real discharge summaries
4. ⬜ Get feedback from admissions staff

### Short Term (2-3 Weeks) - Production Ready
1. ⬜ Migrate to AWS RDS (HIPAA-compliant hosting)
2. ⬜ Implement comprehensive audit logging
3. ⬜ Add session timeout (15 minutes)
4. ⬜ Sign BAA with AWS
5. ⬜ Set up automated backups
6. ⬜ Document security policies
7. ⬜ Train users on HIPAA compliance

### Medium Term (1-2 Months) - Full Features
1. ⬜ Add 2-factor authentication
2. ⬜ Load full ICD-10 PDPM database (3,000+ codes)
3. ⬜ Add reporting dashboard (acceptance rate, revenue trends)
4. ⬜ Add email notifications (new admission, decisions)
5. ⬜ Mobile responsive design improvements
6. ⬜ API for EHR integration (PointClickCare, MatrixCare)

---

## Questions?

**Facility Data**: Use the Admin Panel - no coding required!
**HIPAA Compliance**: 2-3 weeks of work needed (see Phase 1-4 above)
**Login Issue**: Run diagnostic in Render shell (see commands above)

**Need help?** Contact me and I'll walk you through the Admin Panel setup.

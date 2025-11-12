# Facility Setup Guide - No Coding Required!

**Time Required**: 30-60 minutes per facility
**Difficulty**: Easy - uses web interface only

---

## Overview

You configure your facility through the **Admin Panel** web interface. No database queries, no coding, no technical skills required.

---

## Step 1: Login as Admin

1. Go to https://admissions-genie.onrender.com
2. Login:
   - Email: `jthayer@verisightanalytics.com`
   - Password: `admin123`
3. Click **"Admin Panel"** in the top navigation

---

## Step 2: Add Your Facility

### Where to Find Your Facility's Information

#### A. Wage Index
**What it is**: CMS adjustment factor based on your location's labor costs

**Where to find it**:
1. Go to cms.gov
2. Search "SNF wage index" + current year
3. Find your county/CBSA
4. Example values:
   - Urban areas: 1.0-1.3
   - Rural areas: 0.8-1.0
   - Milwaukee, WI: 1.0234
   - Madison, WI: 1.0156

**If you can't find it**: Use 1.0 as a default (neutral, no adjustment)

#### B. VBP (Value-Based Purchasing) Multiplier
**What it is**: Your facility's quality performance adjustment (0.98 - 1.02)

**Where to find it**:
1. Check your Medicare remittance advice (RA)
2. Ask your Medicare Administrative Contractor (MAC)
3. Or check your facility's quality score on Nursing Home Compare

**If you can't find it**: Use 1.0 as default (neutral)

#### C. Capabilities (Services You Provide)

Check the boxes for services your facility can provide:

- **☑ Dialysis**: Do you have RNs trained in dialysis care?
- **☑ IV Antibiotics**: Do you have IV-certified nursing staff?
- **☑ Wound VAC**: Do you have wound VAC equipment and trained staff?
- **☑ Trach Care**: Do you have respiratory therapist support?
- **☐ Ventilator**: Do you accept ventilator-dependent patients? (Most SNFs don't)
- **☑ Bariatric**: Do you have bariatric equipment (beds, lifts rated >350 lbs)?

### How to Enter It

1. In Admin Panel, click **"Facilities"** tab
2. Click **"Add New Facility"** button
3. Fill in the form:
   ```
   Facility Name: [Your SNF Name]
   Wage Index: [Your county's wage index]
   VBP Multiplier: [Your quality score, or 1.0]
   Capabilities: [Check appropriate boxes]
   ```
4. Click **"Save"**

**Example:**
```
Facility Name: Maple Grove Care Center
Wage Index: 1.0234
VBP Multiplier: 1.01
Capabilities:
  ☑ Dialysis
  ☑ IV Antibiotics
  ☑ Wound VAC
  ☐ Trach Care
  ☐ Ventilator
  ☑ Bariatric
```

---

## Step 3: Add Your Payers

### Which Payers to Add

Add every payer source you accept admissions from:

#### A. Medicare Fee-for-Service (Always)
- Type: `Medicare FFS`
- Plan Name: Leave blank
- This is standard Medicare Part A

#### B. Medicare Advantage Plans (MA)
Add each MA plan you have contracts with:
- Type: `Medicare Advantage`
- Plan Name: "Humana Gold Plus", "UnitedHealthcare Dual Complete", etc.

**Common MA plans in Wisconsin:**
- Humana Gold Plus
- UnitedHealthcare Dual Complete
- Security Health Plan Medicare Advantage
- Aspirus Arise Health Plan

#### C. Wisconsin Medicaid
- Type: `Medicaid FFS`
- Plan Name: Leave blank

#### D. Family Care MCOs (Wisconsin)
Add each Family Care plan you contract with:
- Type: `Family Care`
- Plan Name: "iCare", "My Choice Family Care", etc.

**Wisconsin Family Care MCOs:**
- iCare
- My Choice Family Care
- Lakeland Care
- Care Wisconsin

### How to Enter Payers

1. In Admin Panel, click **"Payers"** tab
2. Click **"Add New Payer"**
3. Fill in:
   ```
   Payer Type: [Select from dropdown]
   Plan Name: [Only for MA and Family Care]
   ```
4. Click **"Save"**
5. Repeat for each payer

---

## Step 4: Add Rates for Each Payer

**IMPORTANT**: You need rates for EACH combination of facility + payer.

### Where to Find Rate Information

#### A. Medicare FFS PDPM Rates (2024)
Official CMS rates published annually (updated in August):

**Base PDPM Component Rates (Federal)**:
- PT Component: $64.89/day (for PT score 12+)
- OT Component: $60.78/day (for OT score 12+)
- SLP Component: $22.55/day (for SLP score 12+)
- Nursing Component: $123.45/day (varies by clinical category)
- NTA (Non-Therapy Ancillary): $85.20/day (varies by comorbidity score)

**These get adjusted by:**
1. Your wage index (you entered this)
2. Your VBP multiplier (you entered this)
3. The patient's PDPM scores (calculated automatically)

**Where to find official rates**: cms.gov → Search "PDPM rates 2024"

#### B. Medicare Advantage Rates
**Source**: Your contract with each MA plan

MA rates are usually:
- **Per diem**: Fixed daily rate (e.g., $450/day)
- **PDPM-like**: Similar to Medicare FFS but with plan-specific rates
- **Carve-outs**: Some plans separate therapy from room & board

**If you don't have contracts yet**: Use Medicare FFS rates as a starting point

#### C. Wisconsin Medicaid Rates
**Source**: Wisconsin Department of Health Services (DHS)

**2024 Wisconsin Medicaid Rates (approximate)**:
- Standard Daily Rate: $234/day
- Varies by facility classification and region

**Where to find**: dhs.wisconsin.gov → Medicaid → Provider rates

#### D. Family Care MCO Rates
**Source**: Your contract with each MCO (iCare, My Choice, etc.)

Family Care rates are typically:
- Per diem: $200-300/day (varies by acuity)
- May include therapy or may be separate

### How to Enter Rates

1. In Admin Panel, click **"Rates"** tab
2. Click **"Add New Rate"**
3. Fill in:
   ```
   Facility: [Select your facility]
   Payer: [Select the payer]

   --- PDPM Component Rates ---
   PT Component: $64.89
   OT Component: $60.78
   SLP Component: $22.55
   Nursing Component: $123.45
   NTA Component: $85.20

   --- OR Per Diem Rate ---
   Per Diem Rate: $450.00 (for MA plans that pay flat rate)
   ```
4. Click **"Save"**
5. Repeat for EACH facility + payer combination

**Example 1: Medicare FFS for Maple Grove**
```
Facility: Maple Grove Care Center
Payer: Medicare FFS
PT Component: 64.89
OT Component: 60.78
SLP Component: 22.55
Nursing Component: 123.45
NTA Component: 85.20
```

**Example 2: Humana MA for Maple Grove**
```
Facility: Maple Grove Care Center
Payer: Medicare Advantage - Humana Gold Plus
Per Diem Rate: 425.00 (check your contract)
```

---

## Step 5: Add Cost Models for Each Facility

Cost models tell the system how much it costs YOU to care for different acuity levels.

### Cost Model Acuity Levels

Create **4 cost models** per facility:

1. **Low Acuity**: Independent ADLs, minimal nursing, no therapy
2. **Medium Acuity**: Some ADL needs, moderate nursing, light therapy
3. **High Acuity**: Significant ADL needs, heavy nursing, intensive therapy
4. **Complex Acuity**: Total care, wound care, IV antibiotics, heavy therapy

### How to Calculate Your Costs

Use your facility's actual costs from your P&L (Profit & Loss statement):

#### A. Nursing Cost Per Day

**Formula**: (Total RN + LPN + CNA costs per month) ÷ (Patient days per month)

**Example Calculation**:
```
Monthly nursing payroll: $180,000
Patient days/month: 2,500
Nursing cost/day: $180,000 ÷ 2,500 = $72/day (LOW acuity)

For HIGH acuity: Multiply by 2.5x = $180/day
```

**Typical Ranges**:
- Low: $70-100/day
- Medium: $120-160/day
- High: $180-240/day
- Complex: $250-350/day

#### B. Therapy Cost Per Day

**Formula**: (Total PT/OT/SLP costs) ÷ (Therapy patient days)

**Example**:
```
If you contract therapy:
  - PT: 30 min/day × $90/hr = $45/day
  - OT: 20 min/day × $90/hr = $30/day
  - Total: $75/day (MEDIUM acuity with therapy)

If in-house:
  - Calculate actual therapist cost per minute
```

**Typical Ranges**:
- Low (no therapy): $0/day
- Medium (light therapy): $40-60/day
- High (intensive therapy): $80-120/day
- Complex: $100-150/day

#### C. Ancillary Cost Per Day

**Includes**: Pharmacy, lab, X-ray, wound supplies, oxygen, etc.

**Example**:
```
Monthly ancillary costs: $45,000
Patient days: 2,500
Ancillary/day: $45,000 ÷ 2,500 = $18/day (LOW)

HIGH acuity with IV antibiotics: $60/day
```

**Typical Ranges**:
- Low: $15-25/day
- Medium: $30-50/day
- High: $60-90/day
- Complex: $100-150/day

#### D. Room & Board Cost Per Day

**Includes**: Food, housekeeping, laundry, utilities, maintenance

**Example**:
```
Monthly R&B costs: $85,000
Patient days: 2,500
R&B/day: $85,000 ÷ 2,500 = $34/day

This is SAME for all acuity levels (everyone gets a room and meals)
```

**Typical Range**: $80-120/day (all acuity levels)

#### E. Overhead Cost Per Day

**Includes**: Admin salaries, marketing, insurance, licenses, IT, corporate allocation

**Example**:
```
Monthly overhead: $120,000
Patient days: 2,500
Overhead/day: $120,000 ÷ 2,500 = $48/day

This is SAME for all acuity levels
```

**Typical Range**: $100-150/day (all acuity levels)

### How to Enter Cost Models

1. In Admin Panel, click **"Cost Models"** tab
2. Click **"Add New Cost Model"**
3. Fill in for **LOW acuity**:
   ```
   Facility: Maple Grove Care Center
   Acuity Level: low
   Nursing Cost/Day: $80
   Therapy Cost/Day: $0
   Ancillary Cost/Day: $20
   Room & Board/Day: $95
   Overhead/Day: $125
   ```
4. Click **"Save"**
5. Repeat for medium, high, complex

**Full Example Set:**

**Low Acuity ($320/day total)**:
```
Nursing: $80
Therapy: $0
Ancillary: $20
Room & Board: $95
Overhead: $125
```

**Medium Acuity ($440/day total)**:
```
Nursing: $140
Therapy: $60
Ancillary: $40
Room & Board: $95
Overhead: $125
```

**High Acuity ($590/day total)**:
```
Nursing: $200
Therapy: $90
Ancillary: $70
Room & Board: $105
Overhead: $125
```

**Complex Acuity ($745/day total)**:
```
Nursing: $280
Therapy: $120
Ancillary: $110
Room & Board: $110
Overhead: $125
```

---

## Step 6: Test Your Setup

1. Go back to main dashboard
2. Click **"New Admission"**
3. Select your facility and a payer
4. Upload a test discharge summary
5. System should now calculate margins using YOUR facility's rates and costs!

---

## Shortcuts & Tips

### If You Don't Have Exact Data Yet

**Acceptable Defaults for Testing**:
- Wage Index: 1.0
- VBP Multiplier: 1.0
- Medicare rates: Use CMS published rates
- Costs: Use industry averages (see ranges above)

**You can update these later** as you get more accurate data.

### If You Have Multiple Facilities

Repeat Steps 2-5 for each facility. Each facility gets:
- Its own wage index and VBP
- Its own rates for each payer
- Its own cost models (costs vary by facility)

### If You're Not Sure About Costs

**Option 1**: Ask your finance director for:
- Total nursing cost per patient day
- Total therapy cost per patient day
- Total ancillary cost per patient day
- Food & supplies cost per patient day
- Administrative overhead per patient day

**Option 2**: Use industry benchmarks:
- Low acuity: $300-350/day total
- Medium acuity: $400-500/day total
- High acuity: $550-650/day total
- Complex acuity: $700-850/day total

---

## Common Questions

### Q: Do I need to update rates every year?
**A**: Yes, Medicare PDPM rates change annually in August. Update your rates tab each year.

### Q: What if I get a new MA contract?
**A**: Add the new payer, then add rates for that payer + each of your facilities.

### Q: Can I delete the demo data (Sunshine SNF)?
**A**: Yes! In the Admin Panel, you can delete demo facilities, payers, and rates.

### Q: How do I add more users for my admissions staff?
**A**: Admin Panel → Users tab → Add New User
   - Enter their email
   - Set a temporary password
   - Assign them to a facility
   - Role: "User" (not admin)

### Q: How accurate are the margin calculations?
**A**: As accurate as the data you enter. If you use real rates and real costs, the projections will be within 5-10% of actual.

---

## Need Help?

If you get stuck:
1. Check if all required fields are filled in
2. Make sure you have rates for EVERY facility + payer combo
3. Make sure you have cost models for all 4 acuity levels
4. Contact me and I'll help troubleshoot

**Your facility data is business-confidential** - it's isolated to your organization only (multi-tenant security).

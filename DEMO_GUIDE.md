# Admissions Genie - Demo Guide

## Quick Start (5 Minutes to Demo-Ready)

### 1. Setup
```bash
cd Documents/Admissions-Genie

# Initialize and seed database
python3 -c "from config.database import init_db; init_db()"
python3 seed_database.py

# Start application
PORT=8080 python3 app.py
```

### 2. Access
- **URL:** http://localhost:8080
- **Admin:** admin@admissionsgenie.com / admin123
- **User:** user@admissionsgenie.com / user123

---

## Demo Flow (15-20 minutes)

### Part 1: Overview (2 min)
"Admissions Genie helps SNF admissions staff make data-driven decisions by analyzing discharge packets and calculating projected margins."

**Show:**
- Login page → Dashboard
- Point out demo banner (transparency about demo mode)
- Quick tour of navigation

### Part 2: Sample Admissions Review (5 min)
"Let's look at three different admission scenarios our system has already analyzed."

**Navigate to:** Dashboard → Admission History

**Walk through each sample:**

1. **JD - Score 87 (Accept)** ✅
   - Medicare hip fracture patient
   - High therapy potential
   - Strong projected margin ($75,576)
   - "This is exactly the kind of admission you want - good revenue, manageable costs"

2. **MS - Score 62 (Defer)** ⚠️
   - MA patient with multiple comorbidities
   - Moderate complexity
   - Decent margin ($40,410) but requires monitoring
   - "Acceptable admission, but watch for clinical decline"

3. **RT - Score 38 (Decline)** ❌
   - Medicaid dementia patient
   - High care needs, minimal rehab potential
   - **Negative margin** (-$12,037)
   - "Financial loss likely - only consider for strategic census needs"

**Key Point:** "The system shows you the full breakdown - revenue, costs, risks - so you can make informed decisions, not just gut feelings."

### Part 3: Live Upload Demo (8 min)
"Now let's process a new admission in real-time."

**Navigate to:** New Admission

**Use:** `demo_documents/discharge_summary_hip_fracture.txt`

**Walk through form:**
1. Select Facility: "Sunshine SNF"
2. Select Payer: "Medicare FFS"
3. Patient Initials: "JD" (demonstrate PHI protection - initials only)
4. Estimated LOS: 25 days
5. Authorization Status: "Approved"
6. Current Census: 85%
7. Upload discharge summary

**Click "Analyze Admission"**

**While Processing (30-60 seconds):**
"The system is now:
1. Extracting diagnoses, medications, and functional status using AI
2. Classifying the patient into PDPM groups
3. Calculating Medicare reimbursement based on your facility's rates
4. Estimating care costs based on your cost models
5. Computing a margin score from 0-100"

**Show Results:**
- PDPM classification (PT/OT/SLP/Nursing/NTA groups)
- Revenue breakdown by component
- Cost estimation with denial risk
- **Margin Score** (should be 85-90)
- **Recommendation** with detailed explanation
- "The system caught that we have IV antibiotic capability - important for this patient!"

### Part 4: Admin Panel Tour (3 min)
"Everything is configurable for your facility."

**Navigate to:** Admin dropdown

**Show briefly:**
- **Facilities:** Multiple facilities supported
- **Payers:** 4 payer types (Medicare FFS, MA, Medicaid, Family Care)
- **Rates:** Facility-specific reimbursement rates
- **Cost Models:** Acuity-based cost estimation
- **Users:** Role-based access (admin vs. user)

**Key Point:** "You can update your rates quarterly, adjust cost models, add new payers - it adapts to your business."

### Part 5: Q&A (3 min)
**Common Questions:**

**Q: How accurate is the PDPM classification?**
A: Currently uses ~30 common ICD-10 codes. For production, we'd load the full CMS mapping database (thousands of codes). Accuracy for common diagnoses is very good.

**Q: Where does the revenue/cost data come from?**
A: You configure your actual contracted rates and facility-specific cost models in the admin panel. The system uses YOUR numbers.

**Q: What about HIPAA compliance?**
A: Demo version uses synthetic data only. Production version would include:
- Encryption of uploaded files
- Comprehensive audit logging
- Automatic file cleanup
- Full HIPAA compliance measures

**Q: Can we customize the margin scoring?**
A: Yes, business weights are configurable per facility to match your strategic priorities.

**Q: How much does it cost?**
A: Azure OpenAI: ~$0.50-1.00 per admission analyzed. Hosting can be free or very low cost. Total: $50-100/month for most facilities.

---

## Demo Tips

### Do's ✅
- Start with high-margin case (builds confidence)
- Show the full calculation transparency
- Emphasize data-driven vs. gut decisions
- Highlight time savings (vs. manual calculation)
- Demonstrate PHI protection (initials only)

### Don'ts ❌
- Don't claim 100% accuracy (say "decision support, not replacement")
- Don't promise features not yet built
- Don't skip the disclaimer about demo data
- Don't oversell - let the product speak for itself

### Power Phrases
- "Data-driven admission decisions"
- "Projected margin visibility before you commit"
- "Transparency in every calculation"
- "Adapts to YOUR facility's rates and costs"
- "Catches risky admissions before they become problems"

---

## Troubleshooting

### App won't start
- Check `.env` file has Azure OpenAI credentials
- Verify database initialized: `python3 -c "from config.database import init_db; init_db()"`
- Port 8080 already in use? Try PORT=5000 or PORT=3000

### Upload fails
- Check file format (PDF, Word, or image)
- Verify Azure OpenAI API key is valid
- Check logs/admissions-genie.log for errors

### Wrong calculations
- Verify rates are configured for facility+payer combination
- Check cost models exist for all acuity bands
- Ensure facility has correct wage index

---

## Post-Demo Follow-Up

### Immediate Actions
1. Send sample admission reports via email
2. Provide pricing breakdown
3. Schedule implementation timeline discussion

### Next Steps
1. Facility-specific rate configuration
2. Historical data import (optional)
3. User training session
4. Production deployment planning

---

## Demo Success Metrics

**Great Demo If:**
- ✅ They ask about implementation timeline
- ✅ They want to see their actual rates in the system
- ✅ They ask about user training
- ✅ They mention specific problem admissions from their history

**Need More Work If:**
- ⚠️ Focus on edge cases not core value
- ⚠️ Skeptical about AI accuracy (address with CMS data)
- ⚠️ Concerned about learning curve (emphasize simplicity)
- ⚠️ Price sensitivity (emphasize cost per admission vs. lost revenue)

---

## Emergency Fallback

If live demo fails for any reason, fall back to:
1. Walk through the 3 pre-loaded sample admissions
2. Show the admin configuration panels
3. Explain the calculation methodology manually
4. Schedule follow-up demo when issue resolved

**Remember:** A smooth walkthrough of existing samples is better than a broken live demo!

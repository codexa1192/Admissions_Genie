# Demo Discharge Summaries

This directory contains **synthetic patient data** for demonstration purposes only. All patient information is fictional.

## Available Documents

### 1. discharge_summary_hip_fracture.txt
**Patient:** John D. (fictional)
**Scenario:** High-margin Medicare admission
**Key Features:**
- Hip fracture with total hip replacement
- Good rehabilitation potential
- IV antibiotic requirement
- Expected Score: 85-90 (ACCEPT)
- Estimated LOS: 25 days

**Use this to demonstrate:**
- Best-case admission scenario
- High therapy potential
- Medicare PDPM reimbursement
- Facility capability matching (IV antibiotics)

---

### 2. discharge_summary_chf_copd.txt
**Patient:** Mary S. (fictional)
**Scenario:** Medium-margin Medicare Advantage admission
**Key Features:**
- Multiple comorbidities (CHF, COPD, CKD)
- Moderate care complexity
- Deconditioning from hospital stay
- Expected Score: 55-70 (DEFER/CONSIDER)
- Estimated LOS: 18 days

**Use this to demonstrate:**
- Moderate-risk admission
- MA per diem contract calculation
- Multiple comorbidity management
- Clinical complexity assessment

---

### 3. discharge_summary_dementia.txt
**Patient:** Robert T. (fictional)
**Scenario:** Low-margin Medicaid admission
**Key Features:**
- Advanced Alzheimer's dementia
- High care needs, minimal rehab potential
- Behavioral management required
- Expected Score: 30-45 (DECLINE)
- Estimated LOS: 45+ days (long-term)

**Use this to demonstrate:**
- High-risk/low-margin scenario
- Medicaid reimbursement challenges
- Strategic decision-making (census vs. margin)
- Long-term care vs. rehab

---

## Demo Tips

1. **Start with Hip Fracture** - Shows the system at its best, builds confidence
2. **Follow with CHF/COPD** - Shows nuanced decision-making
3. **End with Dementia** - Shows system catching problematic admissions

## File Formats

All documents are plain text (.txt) for reliability during demo. The system also supports:
- PDF files (.pdf)
- Word documents (.doc, .docx)
- Images (.png, .jpg, .jpeg)

For production demos, convert these to PDFs for more realistic presentation.

## Important Reminders

- These are 100% fictional patients
- All PHI has been redacted or fabricated
- For demonstration and training purposes only
- Do NOT use with real patient information

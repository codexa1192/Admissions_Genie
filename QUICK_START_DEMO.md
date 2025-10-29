# Quick Start - SNF Demo (2 Minutes)

## Start Demo
```bash
cd Documents/Admissions-Genie
PORT=8080 python3 app.py
```

## Access
**URL:** http://localhost:8080
**Login:** admin@admissionsgenie.com / admin123

## Demo Script (15 min)

### 1. Dashboard (2 min)
"See 3 pre-analyzed admissions - Accept, Defer, Decline"

### 2. Review Samples (5 min)
- **JD (87)** - "High-margin Medicare hip fracture - clear accept"
- **MS (62)** - "Moderate MA case - acceptable with monitoring"
- **RT (38)** - "Medicaid dementia - negative margin, decline"

### 3. Live Upload (8 min)
**New Admission → Upload:** `demo_documents/discharge_summary_hip_fracture.txt`
- Facility: Sunshine SNF
- Payer: Medicare FFS
- Patient: JD
- LOS: 25 days
- **Analyze** → Wait 30-60s → Show full breakdown

## Key Messages
✅ "Data-driven decisions in minutes, not hours"
✅ "See projected margin BEFORE you commit beds"
✅ "Uses YOUR facility's actual rates and costs"
✅ "~$0.50-1.00 per admission analyzed"

## Close
"This MVP is demo-ready. For production with real PHI, we'd add HIPAA compliance and audit logging. Timeline: 2-3 weeks."

## If Something Breaks
Fall back to walking through the 3 pre-loaded samples only.

---

## That's It. You're Ready to Demo. 🚀

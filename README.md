# Admissions Genie - SNF Admission Decision Support Tool

A HIPAA-compliant web application that helps Skilled Nursing Facility (SNF) admissions staff make data-driven decisions by analyzing discharge packets, calculating projected margins based on facility-specific reimbursement rates, and providing transparent recommendations.

## Features

- **Document Processing**: Upload discharge summaries, therapy evaluations, and nursing notes (PDF, Word, images)
- **Intelligent Extraction**: Azure OpenAI extracts clinical features (ICD-10 codes, medications, functional status)
- **PDPM Classification**: Automatic classification of PT, OT, SLP, and Nursing groups based on CMS guidelines
- **Multi-Payer Support**:
  - Medicare Fee-for-Service (PDPM with VPD schedule, wage index, VBP multipliers)
  - Medicare Advantage plans (per-diem and PDPM-mapped contracts)
  - Wisconsin Medicaid (rate structure with high-acuity add-ons)
  - Wisconsin Family Care MCOs (nursing/NTA matrices)
- **Cost Estimation**: Detailed cost projections including nursing, supplies, pharmacy, overhead, and denial risk
- **Margin Scoring**: Transparent 0-100 score with clear explanations and business factor adjustments
- **Admin Management**: Full CRUD for facilities, payers, rates, cost models, and users
- **Audit Logging**: Comprehensive audit trail for all system actions and admission decisions
- **Input Validation**: Frontend and backend validation for data integrity and security
- **Enhanced UX**: Loading states, file previews, tooltips, and real-time form validation

## Cost Structure

- **Azure OpenAI API**: $50-100/month (only recurring cost, ~$0.50-1.00 per admission)
- **Hosting**: FREE (Render free tier or localhost)
- **Database**: FREE (SQLite or Render PostgreSQL free tier)
- **Total**: **$50-100/month**

## Technology Stack

- **Backend**: Flask 2.3.3 (Python 3.13)
- **Database**: SQLite (dev) / PostgreSQL (production)
- **AI**: Azure OpenAI (HIPAA-compliant)
- **Document Processing**: PyPDF2, python-docx, pytesseract (local OCR)
- **Frontend**: Vanilla HTML/CSS/JavaScript (no framework overhead)
- **Deployment**: Render free tier (or local)

## Installation

### Prerequisites

- Python 3.13+
- Tesseract OCR (for image processing)
- Azure OpenAI API access (HIPAA BAA required)

### Setup Steps

1. **Clone the repository** (or create project directory)
   ```bash
   cd Documents/Admissions-Genie
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR**
   - macOS: `brew install tesseract`
   - Ubuntu: `sudo apt-get install tesseract-ocr`
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure OpenAI credentials
   ```

6. **Initialize database and seed data**
   ```bash
   python3 -c "from config.database import init_db; init_db()"
   python3 seed_database.py
   ```

7. **Run the application**
   ```bash
   # The app will use port 8080 (or set PORT environment variable)
   PORT=8080 python3 app.py
   ```

8. **Access the application**
   - Open browser to http://localhost:8080
   - Default admin login: admin@admissionsgenie.com / admin123
   - Regular user: user@admissionsgenie.com / user123

## Usage

### For Admissions Staff

1. **Upload Documents**: Navigate to the admission form and upload discharge documents
2. **Fill in Details**: Select facility, payer type, and provide basic information
3. **Review Results**: Get instant margin score and recommendation with detailed breakdown
4. **Sensitivity Analysis**: Use sliders to adjust assumptions (LOS, census priority, etc.)
5. **Make Decision**: Accept, defer, or decline with full audit trail

### For Administrators

1. **Manage Facilities**: Add facilities with wage indexes, VBP multipliers, and capabilities
2. **Import Rates**: Upload CSV files for Medicare, MA, Medicaid, and Family Care rates
3. **Configure Costs**: Set nursing hours, wages, and supply costs by acuity band
4. **Adjust Weights**: Tune business weights (margin vs census vs risk tolerance)
5. **Audit Trail**: Review all decisions and system calculations

## Rate CSV Formats

### Medicare FFS Rates
```csv
fiscal_year,pt_component,ot_component,slp_component,nursing_component,nta_component,non_case_mix,wage_index,vbp_multiplier
2025,64.89,64.38,26.43,105.81,86.72,98.13,1.0234,0.98
```

### MA/Commercial Contracts
```csv
plan_name,contract_type,day_range,rate
Plan X,per_diem,1-30,450.00
Plan X,per_diem,31-60,400.00
Plan X,per_diem,61-100,375.00
```

### Wisconsin Medicaid
```csv
effective_date,per_diem_rate,component_nursing,component_therapy,component_room
2025-01-01,325.00,185.00,95.00,45.00
```

### Family Care MCO
```csv
mco_name,pdpm_nursing_group,pdpm_nta_score,rate
MCO A,ES1,0-5,275.00
MCO A,ES1,6-11,285.00
MCO A,ES2,0-5,295.00
```

## Security & HIPAA Compliance

- **PHI Protection**: Automatic PHI redaction in logs and audit trails
- **Encryption**: TLS 1.3 in transit, database encryption at rest
- **Access Control**: Role-based authentication (user, admin)
- **Audit Logging**: Every decision tracked with rate versions used
- **Document Storage**: Secure temporary storage with automatic cleanup
- **Azure BAA**: Required for Azure OpenAI (HIPAA-compliant)

## Development

### Project Structure
```
Admissions-Genie/
├── app.py                    # Main Flask application
├── config/                   # Configuration modules
│   ├── settings.py           # Environment-based config
│   └── database.py           # Database connection & schema
├── models/                   # Database models (ORM-style)
│   ├── facility.py           # SNF facilities with wage index
│   ├── payer.py              # Insurance payers
│   ├── rates.py              # Facility-specific reimbursement rates
│   ├── cost_model.py         # Acuity-based cost estimates
│   ├── admission.py          # Admission assessments
│   ├── user.py               # User authentication
│   └── audit_log.py          # Comprehensive audit trail
├── routes/                   # Route handlers (Blueprints)
│   ├── auth.py               # Login, logout, registration
│   ├── admission.py          # Document upload & analysis
│   └── admin.py              # Admin panel for CRUD operations
├── services/                 # Business logic layer
│   ├── document_parser.py    # Azure OpenAI document extraction
│   ├── pdpm_classifier.py    # PDPM classification engine
│   ├── reimbursement_calc.py # Multi-payer revenue calculations
│   ├── cost_estimator.py     # Cost projections with risk
│   └── scoring_engine.py     # Margin scoring (0-100)
├── utils/                    # Utility modules
│   └── validators.py         # Input validation (forms & files)
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── admission/           # Admission workflow pages
│   ├── admin/               # Admin panel pages
│   └── errors/              # Error pages (404, 500, 403)
├── static/                   # Frontend assets
│   ├── css/style.css        # Custom styles
│   └── js/app.js            # Enhanced UX (validation, loading)
├── seed_database.py          # Database seeding script
├── test_all_flows.py         # Comprehensive test suite (29 tests)
└── admissions.db             # SQLite database (dev)
```

### Running Tests
```bash
# Run comprehensive test suite (29 tests - 100% pass rate)
python3 test_all_flows.py

# Test coverage includes:
# - Database operations (facilities, payers, rates, users)
# - PDPM classification with ICD-10 mapping
# - Multi-payer reimbursement calculations (Medicare FFS, MA, Medicaid, Family Care)
# - Cost estimation with denial risk
# - Margin scoring engine
# - Admission workflow (create, retrieve, update)
# - Edge cases and error handling
```

## Deployment to Render

1. **Create render.yaml** (already included)
2. **Push to GitHub**
3. **Connect to Render**:
   - Go to https://render.com
   - New Web Service → Connect GitHub repo
   - Render auto-detects configuration
4. **Set environment variables** in Render dashboard
5. **Deploy**: Automatic on push to main branch

## Roadmap

### Phase 1 (MVP - ✅ COMPLETE)
- ✅ Document upload and parsing (PDF, Word, images)
- ✅ Azure OpenAI extraction with local OCR fallback
- ✅ PDPM classification engine (PT, OT, SLP, Nursing, NTA)
- ✅ Multi-payer reimbursement calculations (4 payer types)
- ✅ Cost estimation with denial risk and overhead
- ✅ Margin scoring (0-100) with transparent explanations
- ✅ Admin panel for facility/payer/rate/cost management
- ✅ User authentication with role-based access control
- ✅ Comprehensive audit logging for all actions
- ✅ Input validation (frontend + backend)
- ✅ Enhanced UX (loading states, tooltips, file previews)
- ✅ Comprehensive test suite (29 tests, 100% pass rate)
- ✅ Database indexing for performance
- ✅ Security hardening (CSRF, rate limiting, password hashing)

### Phase 2 (Future Enhancements)
- [ ] Pre-authorization tracking and workflow
- [ ] EHR integration (PointClickCare, MatrixCare)
- [ ] Auto-fetch CMS rate updates via API
- [ ] Advanced ML for LOS prediction
- [ ] Mobile app for on-the-go decisions
- [ ] Multi-facility dashboard with analytics
- [ ] Historical performance analytics and reporting
- [ ] Real-time census integration
- [ ] Export to CSV/Excel for reporting

## License

Proprietary - All rights reserved

## Support

For questions or issues, contact: [your-email@example.com]

---

**Note**: This application handles Protected Health Information (PHI). Ensure proper Business Associate Agreements (BAAs) are in place with all service providers (Azure, hosting provider, etc.) before processing real patient data.

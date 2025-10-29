# Changelog

All notable changes to Admissions Genie will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2025-10-22

### 🎉 Initial Production Release

**Admissions Genie v1.0** is now production-ready with comprehensive SNF admission decision support capabilities.

### Added

#### Core Features
- **Document Processing System**
  - Upload discharge summaries, therapy evaluations, and nursing notes
  - Support for PDF, Word (doc/docx), and image files (jpg, png)
  - Azure OpenAI GPT-4 Turbo extraction of clinical features
  - Local OCR fallback using Tesseract for image processing
  - ICD-10 code extraction and validation
  - Medication list extraction
  - Functional status assessment

- **PDPM Classification Engine** ([services/pdpm_classifier.py](services/pdpm_classifier.py))
  - Automatic PT/OT group classification (TA-TG)
  - SLP group classification (SA-SE)
  - Nursing case-mix group classification (ES1/ES2, HBS1/HBS2, LBS1/LBS2, etc.)
  - Non-Therapy Ancillary (NTA) scoring (0-12+)
  - ICD-10 code mapping to PDPM categories
  - Cognitive and functional assessment integration

- **Multi-Payer Reimbursement Calculations** ([services/reimbursement_calc.py](services/reimbursement_calc.py))
  - **Medicare Fee-for-Service**: Full PDPM implementation with VPD schedule, wage index adjustment, and VBP multipliers
  - **Medicare Advantage**: Per-diem and PDPM-mapped contract support with day tiers
  - **Wisconsin Medicaid**: Basic rate structure with high-acuity add-ons
  - **Wisconsin Family Care**: MCO-specific nursing/NTA matrices

- **Cost Estimation Engine** ([services/cost_estimator.py](services/cost_estimator.py))
  - Acuity-based nursing cost projection (hours × hourly rate)
  - Supply cost estimation (low/medium/high/complex acuity bands)
  - Pharmacy cost estimation with IV therapy add-ons
  - Transport cost calculations
  - Overhead cost allocation (% of direct costs)
  - Denial risk calculation with expected loss projection
  - Authorization status impact on denial probability

- **Margin Scoring System** ([services/scoring_engine.py](services/scoring_engine.py))
  - Transparent 0-100 scoring algorithm
  - Base margin score from projected profit per diem
  - Business factor adjustments (census impact, denial risk, complexity)
  - Configurable business weights per facility
  - Detailed scoring explanation with component breakdowns
  - Recommendation engine (Accept/Defer/Decline)

#### Database & Models
- **Comprehensive Data Models** ([models/](models/))
  - `Facility`: SNF facilities with wage index, VBP multipliers, capabilities
  - `Payer`: Insurance payers (Medicare FFS, MA, Medicaid, Family Care)
  - `Rate`: Facility-specific reimbursement rates with versioning and date ranges
  - `CostModel`: Acuity-based cost estimates per facility
  - `Admission`: Complete admission assessments with PDPM groups, scores, decisions
  - `User`: Authentication with bcrypt password hashing and role-based access
  - `AuditLog`: Comprehensive audit trail for compliance (NEW)

- **Database Schema** ([config/database.py](config/database.py))
  - SQLite support for development
  - PostgreSQL support for production
  - Automatic schema migration
  - Comprehensive indexing for performance
  - Foreign key constraints for data integrity

#### User Interface
- **Admission Workflow** ([templates/admission/](templates/admission/))
  - Intuitive document upload with drag-drop support
  - Facility and payer selection
  - Projected LOS slider with visual feedback
  - Authorization status tracking
  - Real-time file validation and preview
  - Loading states during analysis (30-60 seconds for document processing)
  - Results dashboard with margin score gauge
  - Detailed revenue/cost breakdowns
  - PDPM group display
  - Admission history with filtering

- **Admin Panel** ([templates/admin/](templates/admin/))
  - Facility management (CRUD operations)
  - Payer management with plan names and network status
  - Rate management with effective date tracking
  - Cost model configuration by acuity band
  - User management with role assignment
  - CSV rate import system (planned)

- **Enhanced User Experience** ([static/js/app.js](static/js/app.js))
  - Client-side form validation with real-time feedback
  - File upload preview with type icons and size display
  - Loading overlays with progress messages
  - Toast notifications for user feedback
  - Contextual tooltips for complex fields
  - Range slider enhancements showing current values
  - Bootstrap 5 responsive design

#### Security & Compliance
- **Security Features**
  - CSRF protection on all forms
  - Rate limiting to prevent abuse
  - Bcrypt password hashing (cost factor 12)
  - SQL injection prevention via parameterized queries
  - XSS protection via template escaping
  - File upload validation (type, size, MIME type)
  - 10MB per file limit, 50MB total upload limit
  - Secure session management

- **HIPAA Compliance**
  - PHI protection: Only patient initials stored (no full names)
  - Audit logging for all admission decisions
  - Secure document storage with automatic cleanup
  - Azure BAA support for AI processing
  - Encrypted connections (TLS 1.3 in production)

- **Comprehensive Input Validation** ([utils/validators.py](utils/validators.py))
  - Frontend validation (JavaScript)
  - Backend validation (Python)
  - AdmissionValidator: Validates facility, payer, LOS (1-100 days), patient initials
  - FileValidator: Validates file extensions, sizes, MIME types
  - BusinessLogicValidator: Validates margin scores, revenue, costs, denial risk

#### Audit & Compliance
- **Audit Logging System** ([models/audit_log.py](models/audit_log.py))
  - Tracks all system actions (admission decisions, rate updates, user logins, etc.)
  - Stores user ID, action type, resource type/ID, changes (JSON), IP address, user agent
  - Search and filter by date range, user, action type, resource
  - Statistics dashboard with event counts by action and user
  - Database indexes for fast querying

#### Testing & Quality
- **Comprehensive Test Suite** ([test_all_flows.py](test_all_flows.py))
  - 29 automated tests covering all core functionality
  - 100% test pass rate
  - Tests include:
    - Database operations (facilities, payers, rates, users)
    - PDPM classification with ICD-10 mapping
    - Multi-payer reimbursement calculations
    - Cost estimation with denial risk
    - Margin scoring engine
    - Admission workflow (create, retrieve, update)
    - Edge cases and error handling
  - Color-coded test output with pass/fail statistics

#### Performance
- **Database Optimization**
  - Indexes on frequently queried columns (facility_id, payer_id, created_at, etc.)
  - Compound indexes for complex queries
  - Efficient query patterns in all models
  - Connection pooling support

#### Deployment
- **Production-Ready Configuration**
  - Environment-based configuration (development, production, testing)
  - Configurable secrets via .env file
  - Logging to file and console
  - Error handling with custom error pages (404, 500, 403)
  - Health check endpoint
  - Port configuration via environment variable
  - Render.com deployment support (planned)

### Database Seeding
- **Sample Data** ([seed_database.py](seed_database.py))
  - 2 sample SNF facilities (Sunshine SNF, Green Valley Care Center)
  - 4 payer configurations (Medicare FFS, MA, Medicaid WI, Family Care WI)
  - 8 rate configurations (4 per facility for all payer types)
  - 8 cost models (4 acuity bands per facility)
  - 2 sample users (admin and regular user)
  - Realistic rate and cost data for Wisconsin SNFs

### Technical Details

#### Technology Stack
- **Backend**: Flask 2.3.3, Python 3.13
- **Database**: SQLite (dev), PostgreSQL (production)
- **AI**: Azure OpenAI GPT-4 Turbo
- **Document Processing**: PyPDF2, python-docx, pytesseract
- **Frontend**: Bootstrap 5, vanilla JavaScript
- **Authentication**: Flask-Login, bcrypt
- **Security**: Flask-Limiter, CSRF protection

#### System Requirements
- Python 3.13+
- Tesseract OCR (for image processing)
- Azure OpenAI API access (HIPAA BAA required)
- 256MB RAM minimum
- 100MB disk space

#### Cost Structure
- Azure OpenAI API: $50-100/month (~$0.50-1.00 per admission)
- Hosting: FREE (Render free tier or localhost)
- Database: FREE (SQLite or Render PostgreSQL)
- **Total monthly cost: $50-100**

### Access Information
- **Default Admin Login**: admin@admissionsgenie.com / admin123
- **Default User Login**: user@admissionsgenie.com / user123
- **Application URL (local)**: http://localhost:8080

### Known Limitations
- Azure OpenAI API key required for document extraction (system works without it but only for manual data entry)
- Single-facility view (multi-facility dashboard planned for Phase 2)
- CSV rate import UI not yet implemented (manual database insertion required)
- No mobile app (web responsive only)
- No EHR integration (manual document upload only)

### Documentation
- [README.md](README.md): Installation and usage guide
- [TESTING.md](TESTING.md): Testing documentation
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md): Technical summary
- [CHANGELOG.md](CHANGELOG.md): This file

---

## Future Releases

### [1.1.0] - Planned
- CSV rate import UI
- Export admissions to CSV/Excel
- Advanced search and filtering in admission history
- Bulk operations for rate updates
- Email notifications for admission decisions

### [1.2.0] - Planned
- Multi-facility dashboard with analytics
- Historical performance reporting
- Real-time census integration
- Pre-authorization tracking workflow

### [2.0.0] - Future
- EHR integration (PointClickCare, MatrixCare)
- Mobile app for iOS and Android
- Advanced ML for LOS prediction
- Auto-fetch CMS rate updates
- Multi-tenant architecture

---

**For questions or support, please contact the development team.**

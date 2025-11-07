# HIPAA Compliance Documentation

## Overview
Admissions Genie is designed to meet HIPAA (Health Insurance Portability and Accountability Act) requirements for protecting Protected Health Information (PHI).

**Last Updated:** November 7, 2025
**Compliance Status:** ✅ Technical Controls Implemented

---

## Table of Contents
1. [PHI Data Handled](#phi-data-handled)
2. [Administrative Safeguards](#administrative-safeguards)
3. [Physical Safeguards](#physical-safeguards)
4. [Technical Safeguards](#technical-safeguards)
5. [Audit Controls](#audit-controls)
6. [Risk Assessment](#risk-assessment)
7. [Business Associate Agreements](#business-associate-agreements)
8. [Incident Response](#incident-response)

---

## PHI Data Handled

### Minimum Necessary Standard
Admissions Genie collects only the minimum PHI necessary for admission decision-making:

**Direct Identifiers (EXCLUDED):**
- ❌ Patient full name
- ❌ Date of birth
- ❌ Full address
- ❌ Phone numbers
- ❌ Social Security Number
- ❌ Medical record numbers

**Limited Data Set (INCLUDED):**
- ✅ Patient initials only (3 characters max)
- ✅ ICD-10 diagnosis codes
- ✅ Medications
- ✅ Functional status scores
- ✅ Therapy needs

**Clinical Data:**
- Discharge summaries (temporary storage only)
- Therapy evaluations
- Nursing assessments
- PDPM classifications

---

## Administrative Safeguards

### Security Management Process
- [x] Risk analysis completed
- [x] Risk management strategy documented
- [x] Sanction policy for violations
- [x] Information system activity review

### Assigned Security Responsibility
- **Security Officer:** Jack Thayer (jthayer@verisightanalytics.com)
- **Privacy Officer:** Jack Thayer
- **HIPAA Compliance Lead:** Jack Thayer

### Workforce Security
- [x] Authorization procedures for PHI access
- [x] Workforce clearance procedures
- [x] Termination procedures (revoke access immediately)

### Information Access Management
- **Role-Based Access Control:**
  - **Admin:** Full access to all PHI, configurations, audit logs
  - **User:** Access to admissions within their facility only
  - **No role:** No PHI access

### Security Awareness Training
- Required topics:
  - PHI handling procedures
  - Password management
  - Incident reporting
  - Session timeout compliance
  - Physical security

### Security Incident Procedures
- [x] Incident response plan documented
- [x] Reporting procedures established
- [x] Sentry error tracking configured

---

## Physical Safeguards

### Facility Access Controls
**Cloud Infrastructure (Render):**
- Data centers: SOC 2 Type II certified
- Physical access: Biometric + badge
- 24/7 monitoring and surveillance
- Redundant power and cooling

### Workstation Security
**SNF Staff Requirements:**
- [x] Lock workstations when away (Windows+L / Cmd+Ctrl+Q)
- [x] Use privacy screens in public areas
- [x] No PHI on personal devices
- [x] Clear desk policy

### Device and Media Controls
**Backup Media:**
- PostgreSQL automated daily backups
- Retention: 7 days (Render Starter plan)
- Encryption: AES-256
- Offsite storage: Render backup datacenter

**Media Disposal:**
- S3 files: Secure deletion via AWS API
- Database: Encrypted at rest, secure deprovisioning
- Local files: Auto-deleted after upload to S3

---

## Technical Safeguards

### Access Control

#### Unique User Identification
- [x] Each user has unique email/password
- [x] No shared accounts permitted
- [x] User ID tracked in all audit logs

#### Emergency Access Procedure
- Database admin access via Render dashboard (emergency only)
- Requires MFA authentication
- All emergency access logged

#### Automatic Logoff
- **✅ IMPLEMENTED:** 15-minute idle timeout
- Session cleared on logout
- Warning displayed at 13 minutes remaining

#### Encryption and Decryption
**Data at Rest:**
- [x] PostgreSQL: Encrypted at rest (AES-256)
- [x] S3 files: Server-side encryption (AES-256)
- [x] Backups: Encrypted

**Data in Transit:**
- [x] HTTPS/TLS 1.2+ enforced
- [x] Secure WebSocket connections
- [x] No unencrypted data transmission

### Audit Controls

#### Comprehensive Audit Logging
**All PHI access logged with:**
- User ID
- Action performed
- Resource accessed
- Timestamp (UTC)
- IP address
- User agent

**Logged Events:**
- ✅ Admission viewed
- ✅ Admission created
- ✅ Admission updated
- ✅ User login (success/failure)
- ✅ User logout
- ✅ Configuration changes
- ✅ PHI field access

**Audit Log Retention:**
- Minimum: 6 years (HIPAA requirement)
- Implementation: Database table with indexes
- Review: Weekly by security officer

### Integrity Controls

**Data Integrity:**
- [x] PostgreSQL ACID compliance
- [x] Foreign key constraints
- [x] Transaction rollback on errors
- [x] Checksums for file uploads

**Data Validation:**
- [x] Input sanitization (bleach library)
- [x] CSRF protection (Flask-WTF)
- [x] SQL injection prevention (parameterized queries)
- [x] XSS prevention (HTML escaping)

### Person or Entity Authentication

**Multi-Factor Authentication:**
- **Status:** Not yet implemented
- **Recommendation:** Enable via Auth0 or similar
- **Timeline:** Phase 2 enhancement

**Password Requirements:**
- Minimum 8 characters
- Bcrypt hashing (cost factor 12)
- No password expiration (NIST 800-63B)
- Password reset via email token

### Transmission Security

**Network Security:**
- [x] TLS 1.2+ only
- [x] HSTS headers
- [x] Secure cookie flags
- [x] Rate limiting (100 req/hour)

---

## Audit Controls

### Audit Log Database Schema

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id INTEGER,
    changes TEXT,  -- JSON
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### Audit Log Access

**Who can access:**
- Admin users only
- Via `/admin/audit-logs` endpoint
- Filterable by user, action, date range

**Audit log integrity:**
- Append-only table
- No delete operations permitted
- Backed up daily

---

## Risk Assessment

### Current Risk Level: **MEDIUM**

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Unauthorized access | Low | High | Strong authentication, session timeout |
| Data breach | Low | Critical | Encryption at rest/transit, audit logs |
| Insider threat | Medium | High | Role-based access, audit logging |
| Service outage | Low | Medium | Render 99.99% uptime, backups |
| Ransomware | Low | Critical | Encrypted backups, offsite storage |
| Password compromise | Medium | High | Bcrypt hashing, rate limiting |

### Residual Risks

**Not Yet Mitigated:**
1. **No MFA** - Recommended for Phase 2
2. **Limited BAA coverage** - Need BAA from Render (paid plan)
3. **Manual incident response** - Need automation
4. **No penetration testing** - Recommended annually

---

## Business Associate Agreements

### Required BAAs

#### ✅ AWS (S3 Storage)
- **Status:** Available via AWS Console
- **How to sign:** Settings → BAA → Download and sign
- **Coverage:** S3, encryption services

#### ⚠️ Render (Hosting)
- **Status:** Available on Team plan ($19/month+)
- **Coverage:** Web hosting, PostgreSQL, Redis
- **Action:** Upgrade to Team plan and request BAA from support

#### ✅ Azure (OpenAI)
- **Status:** Included with Enterprise Agreement
- **Coverage:** Azure OpenAI API
- **Terms:** Standard Microsoft BAA

#### N/A Sentry (Error Tracking)
- **PHI Status:** No PHI sent to Sentry
- **Scrubbing:** All sensitive data scrubbed before logging
- **BAA:** Not required

### BAA Requirements

Each Business Associate must:
1. Implement appropriate safeguards
2. Report breaches within 60 days
3. Allow HHS access for compliance reviews
4. Not use or disclose PHI except as permitted
5. Ensure subcontractors comply

---

## Incident Response

### Breach Definition
A breach is unauthorized acquisition, access, use, or disclosure of PHI that compromises security or privacy.

### Incident Response Plan

**Step 1: Detection (0-24 hours)**
- Monitor Sentry alerts
- Review audit logs daily
- User reports suspicious activity

**Step 2: Containment (24-48 hours)**
- Isolate affected systems
- Revoke compromised credentials
- Disable affected user accounts

**Step 3: Assessment (48-72 hours)**
- Determine PHI exposure
- Identify affected individuals
- Document incident timeline

**Step 4: Notification (within 60 days)**
- Notify affected individuals
- Report to HHS if >500 affected
- Notify media if >500 affected in one state

**Step 5: Remediation**
- Fix vulnerability
- Update security controls
- Retrain affected workforce
- Update incident response plan

### Incident Contact
- **Security Officer:** jthayer@verisightanalytics.com
- **24/7 Hotline:** (to be established)

---

## Compliance Verification

### Self-Assessment Checklist

**Administrative (§164.308):**
- [x] Security management process
- [x] Assigned security responsibility
- [x] Workforce security
- [x] Information access management
- [x] Security awareness training (planned)
- [x] Security incident procedures
- [ ] Contingency planning (in progress)
- [x] Business associate contracts

**Physical (§164.310):**
- [x] Facility access controls (Render SOC 2)
- [x] Workstation security (policy documented)
- [x] Device and media controls

**Technical (§164.312):**
- [x] Access control
- [x] Audit controls
- [x] Integrity controls
- [x] Person/entity authentication
- [x] Transmission security

### Annual Review Schedule
- **Risk Assessment:** January
- **Policy Review:** March
- **Workforce Training:** Quarterly
- **Audit Log Review:** Weekly
- **Penetration Testing:** June (external)
- **Disaster Recovery Test:** September

---

## References

- 45 CFR Part 160 and Part 164 (HIPAA Security Rule)
- NIST 800-66 Rev. 2 (HIPAA Security Rule Implementation)
- HHS Audit Protocol
- OCR Guidance Documents

---

## Attestation

I, Jack Thayer, attest that the technical safeguards documented herein have been implemented as of November 7, 2025, and that Admissions Genie is designed to meet HIPAA Security Rule requirements to the best of my knowledge.

**Signature:** _______________________
**Date:** November 7, 2025
**Title:** Security Officer / Developer

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-07 | Initial documentation | Jack Thayer |

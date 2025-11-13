# HIPAA POLICY TEMPLATES
## Admissions Genie - SNF Management System

**⚠️ DISCLAIMER:** These are templates only. Have your legal/compliance team review before using in production.

---

## 1. INFORMATION SECURITY POLICY

### Purpose
This Information Security Policy establishes requirements for protecting electronic Protected Health Information (ePHI) in compliance with the Health Insurance Portability and Accountability Act (HIPAA).

### Scope
This policy applies to all employees, contractors, and third parties who access the Admissions Genie system.

### Policy

#### 1.1 Access Control
- User accounts must be unique (no shared accounts)
- Passwords must meet complexity requirements (12+ characters, uppercase, lowercase, numbers, symbols)
- Accounts must lock after 5 failed login attempts
- Sessions must timeout after 15 minutes of inactivity
- Multi-factor authentication is required for administrator accounts
- Access must be granted based on minimum necessary principle

#### 1.2 Encryption
- All ePHI must be encrypted at rest using AES-256 or equivalent
- All ePHI must be encrypted in transit using TLS 1.2 or higher
- Encryption keys must be stored separately from encrypted data
- Encryption keys must be rotated annually

#### 1.3 Audit Controls
- All access to ePHI must be logged
- Audit logs must include: user ID, timestamp, action taken, IP address
- Audit logs must be retained for 6 years
- Audit logs must be reviewed monthly for suspicious activity

#### 1.4 Data Integrity
- Database backups must be performed daily
- Backups must be encrypted
- Backup restoration must be tested quarterly
- Data modification must be logged in audit trails

#### 1.5 Transmission Security
- ePHI may only be transmitted using encrypted channels (HTTPS, SFTP, encrypted email)
- Email containing ePHI must be encrypted
- Fax transmission of ePHI must use secure fax services

### Enforcement
Violations of this policy may result in disciplinary action up to and including termination.

### Review
This policy will be reviewed annually and updated as needed.

---

## 2. INCIDENT RESPONSE AND BREACH NOTIFICATION PLAN

### Purpose
This plan establishes procedures for responding to security incidents and data breaches involving ePHI.

### Definitions
- **Security Incident:** Any unauthorized access, use, disclosure, modification, or destruction of ePHI
- **Breach:** Unauthorized acquisition, access, use, or disclosure of ePHI that compromises security or privacy

### Incident Response Team
- **Incident Commander:** [Name, Title]
- **Technical Lead:** [Name, Title]
- **Legal Counsel:** [Name, Firm]
- **Compliance Officer:** [Name, Title]
- **Communications Lead:** [Name, Title]

### Incident Response Procedures

#### Phase 1: Detection and Assessment (0-4 hours)
1. **Detect:** Incident identified via:
   - Security monitoring alerts
   - User reports
   - Audit log review
   - Third-party notification

2. **Assess:**
   - Scope of incident (# of records, type of data)
   - How incident occurred
   - Systems/users affected
   - Ongoing threat assessment

3. **Notify Incident Commander** immediately

#### Phase 2: Containment (4-24 hours)
1. **Isolate** affected systems
2. **Preserve** evidence (do not delete logs)
3. **Document** all actions taken
4. **Assess** whether breach is reportable under HIPAA

#### Phase 3: Investigation (24-72 hours)
1. **Determine:**
   - Who had unauthorized access
   - What data was accessed/disclosed
   - When incident occurred
   - How incident occurred
   - Why controls failed

2. **Document** findings in incident report

#### Phase 4: Remediation (72 hours - 30 days)
1. **Fix** vulnerabilities that allowed incident
2. **Reset** compromised credentials
3. **Update** security controls
4. **Test** remediation effectiveness

#### Phase 5: Notification (Per HIPAA requirements)

**If Breach Affects < 500 Individuals:**
- Notify affected individuals within 60 days
- Notify HHS annually (within 60 days of calendar year end)
- Document notifications

**If Breach Affects ≥ 500 Individuals:**
- Notify affected individuals within 60 days
- Notify HHS within 60 days
- Notify prominent media outlets if ≥ 500 in same state/jurisdiction
- Document all notifications

**Notification Content Must Include:**
- Brief description of what happened
- Types of information involved
- Steps individuals should take to protect themselves
- What organization is doing to investigate/mitigate
- Contact information for questions

#### Phase 6: Post-Incident Review (30-60 days)
1. **Review** incident response effectiveness
2. **Update** policies/procedures as needed
3. **Train** staff on lessons learned
4. **Implement** additional safeguards

### Breach Determination Flowchart

```
Unauthorized access to ePHI occurred?
├─ NO → Not a breach. Document incident and close.
└─ YES → Proceed to risk assessment

Risk assessment: Is there significant risk of harm?
├─ NO → Not a breach. Document risk assessment.
└─ YES → Breach confirmed

Number of individuals affected?
├─ < 500 → Follow notification procedures (60-day timeline)
└─ ≥ 500 → Follow notification procedures + media notification (60-day timeline)
```

### Contact Information

**HHS Breach Reporting:**
- Portal: https://ocrportal.hhs.gov/ocr/breach/wizard_breach.jsf
- Phone: 1-800-368-1019
- Email: OCRComplaint@hhs.gov

**State Attorney General (Wisconsin):**
- Phone: (608) 266-1221
- Website: https://www.doj.state.wi.us/

### Documentation Requirements
All incidents must be documented with:
- Date/time discovered
- Description of incident
- ePHI involved
- Individuals affected
- Actions taken
- Resolution
- Lessons learned

---

## 3. ACCESS CONTROL POLICY

### Purpose
To ensure that only authorized individuals have access to ePHI in the Admissions Genie system.

### Access Levels

| Role | Permissions |
|------|-------------|
| **System Administrator** | Full access to all features, user management, configuration |
| **Facility Administrator** | Access to own facility's data, admission management, reporting |
| **Regular User** | View admissions, create new admissions (own facility only) |

### Access Request Procedure
1. New user requests access via supervisor
2. Supervisor submits access request form
3. IT reviews and verifies business need
4. Compliance officer approves
5. IT provisions account with appropriate role
6. User receives temporary password, must change on first login
7. Access logged in audit trail

### Access Review
- Access rights reviewed quarterly
- Terminated employees removed immediately
- Inactive accounts (90+ days) disabled automatically

### Emergency Access
- Break-glass access available for true emergencies
- All emergency access logged and reviewed
- Emergency access requires two-person authorization

---

## 4. PASSWORD POLICY

### Requirements
All passwords must meet the following requirements:
- Minimum 12 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (!@#$%^&*)
- No common words (password, admin, 123456, etc.)
- No sequential characters (abc, 123)
- No repeated characters (aaa, 111)

### Password Management
- Passwords must be changed every 90 days (recommended)
- Cannot reuse last 5 passwords
- Account locks after 5 failed login attempts
- Lockout duration: 30 minutes
- Passwords never stored in plain text (bcrypt hashing)

### Default Passwords
- Default passwords prohibited in production
- Temporary passwords must be changed on first login
- System enforces password change for new accounts

---

## 5. RISK ANALYSIS

### Identified Threats
| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|------------|
| Unauthorized access to database | Medium | High | Encryption at rest, access controls, audit logging |
| Data breach via stolen credentials | Medium | High | Password complexity, MFA, account lockout |
| Ransomware attack | Medium | High | Encrypted backups, disaster recovery plan |
| Insider threat | Low | High | Audit logging, access reviews, principle of least privilege |
| DDoS attack | Low | Medium | Rate limiting, CloudFlare/WAF |
| Vendor breach (AWS/Azure) | Low | High | BAA with vendor, vendor security assessment |
| Unencrypted data in transit | Low | High | TLS 1.2+ enforced, HTTPS only |
| Accidental disclosure via email | Medium | Medium | User training, email encryption |

### Vulnerabilities
| Vulnerability | Severity | Status |
|---------------|----------|--------|
| Render.com lacks BAA | Critical | RESOLVED (migrated to AWS) |
| Database not encrypted at rest | High | RESOLVED (RDS encryption enabled) |
| Some audit logs incomplete | Medium | IN PROGRESS |
| No MFA for admin accounts | Medium | PENDING |
| Backup restore not tested | Medium | PENDING |

### Residual Risks
After implementing all safeguards, the following residual risks remain:
- Sophisticated nation-state attack (Accepted - low likelihood)
- Natural disaster affecting AWS data center (Accepted - multi-AZ mitigates)
- Social engineering attack on staff (Accepted - training mitigates)

---

## 6. BACKUP AND DISASTER RECOVERY PLAN

### Backup Strategy

**Daily Backups:**
- Database: Full backup daily at 2 AM UTC
- Files: Incremental backup daily at 3 AM UTC
- Retention: 7 days of daily backups

**Weekly Backups:**
- Full system backup every Sunday at 1 AM UTC
- Retention: 4 weeks of weekly backups

**Monthly Backups:**
- Full system backup first Sunday of month
- Retention: 6 years (HIPAA requirement)

**Backup Encryption:**
- All backups encrypted with AES-256
- Encryption keys stored in AWS KMS/Azure Key Vault
- Separate key from production encryption key

### Recovery Time Objective (RTO)
- **Target RTO:** 4 hours
- Maximum acceptable downtime: 4 hours

### Recovery Point Objective (RPO)
- **Target RPO:** 24 hours
- Maximum acceptable data loss: 24 hours of transactions

### Disaster Scenarios

#### Scenario 1: Database Corruption
1. Identify corruption scope
2. Restore from most recent clean backup
3. Replay transaction logs if available
4. Verify data integrity
5. Resume operations
**Estimated Recovery Time:** 2 hours

#### Scenario 2: Ransomware Attack
1. Isolate affected systems immediately
2. Assess extent of encryption
3. Do NOT pay ransom
4. Restore from encrypted backups
5. Rebuild affected systems
6. Investigate attack vector
**Estimated Recovery Time:** 4-8 hours

#### Scenario 3: AWS Region Outage
1. Activate multi-region failover (if configured)
2. If not configured, restore to different region
3. Update DNS to point to new region
4. Verify application functionality
**Estimated Recovery Time:** 6-12 hours

#### Scenario 4: Accidental Data Deletion
1. Identify deleted data
2. Restore from point-in-time backup
3. Merge with current data if needed
4. Verify restoration
**Estimated Recovery Time:** 1-2 hours

### Testing Schedule
- **Backup Verification:** Weekly (automated)
- **Restore Test:** Monthly (sample restore)
- **Full DR Test:** Quarterly (complete failover)
- **Tabletop Exercise:** Annually

### Emergency Contacts
- **AWS Support:** 1-877-209-1146 (Enterprise Support)
- **Database Administrator:** [Name, Phone]
- **System Administrator:** [Name, Phone]
- **Incident Commander:** [Name, Phone]

---

## 7. BUSINESS CONTINUITY PLAN

### Critical Functions
1. Admission decision-making (Priority 1 - restore in 4 hours)
2. Admission tracking (Priority 1 - restore in 4 hours)
3. Reporting (Priority 2 - restore in 24 hours)
4. User management (Priority 3 - restore in 72 hours)

### Alternate Processing Site
- **Primary:** AWS us-east-1 (N. Virginia)
- **Failover:** AWS us-west-2 (Oregon)

### Communication Plan
In the event of system outage:
1. Status page updated within 30 minutes
2. Email notification to all users within 1 hour
3. Phone tree activated for critical users
4. Hourly updates until resolution

### Manual Workarounds
If system unavailable for > 4 hours:
- Admission decisions: Use spreadsheet template
- Data collection: Use paper forms
- Data entry when system restored

---

## POLICY APPROVAL

These policies have been reviewed and approved by:

| Name | Title | Signature | Date |
|------|-------|-----------|------|
| [Name] | CEO/Owner | __________ | _____ |
| [Name] | HIPAA Compliance Officer | __________ | _____ |
| [Name] | Legal Counsel | __________ | _____ |

**Next Review Date:** [One year from approval]

---

## REVISION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-13 | System | Initial creation |
|  |  |  |  |


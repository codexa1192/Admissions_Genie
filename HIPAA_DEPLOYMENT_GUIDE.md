# HIPAA Deployment Guide
## Admissions Genie v1.1.0 - Production Deployment

**Last Updated:** November 10, 2025
**Target Environment:** Production with Real PHI

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Generate Encryption Key

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Output Example:** `Hs9bH9os6dhS7SME9WdEr-x4stzk0JwUmI3PmfGlPGY=`

⚠️ **CRITICAL:** Store this key securely! If lost, encrypted data cannot be recovered.

### Step 2: Update Production Environment Variables

```bash
# Add to your .env or production environment
ENCRYPTION_KEY=<paste-generated-key-here>
FLASK_ENV=production
```

### Step 3: Run Database Migration

```bash
python3 migrations/add_security_columns.py upgrade
```

**Expected Output:**
```
Adding security columns to users table...
  - Adding failed_login_attempts column...
  - Adding locked_until column...
  - Adding last_failed_login column...
✅ Security columns migration completed successfully!
```

### Step 4: Update Admin Passwords

All existing passwords must meet new complexity requirements:
- Minimum 12 characters
- Uppercase + lowercase + number + special character

```bash
# Login as admin and change password via UI:
# http://your-domain.com/auth/change-password
```

### Step 5: Verify Deployment

```bash
python3 test_hipaa_features.py
```

---

## 📋 Detailed Deployment Checklist

### Pre-Deployment (1-2 hours)

- [ ] **Backup current database**
  ```bash
  # SQLite
  cp admissions.db admissions.db.backup.$(date +%Y%m%d)

  # PostgreSQL
  pg_dump admissions > admissions_backup_$(date +%Y%m%d).sql
  ```

- [ ] **Review current environment variables**
  ```bash
  cat .env
  # Ensure no sensitive data in logs or version control
  ```

- [ ] **Test in staging environment first**
  - Deploy to staging
  - Run migration
  - Test login/registration
  - Test admission creation
  - Verify encryption

### Deployment Steps (30-60 minutes)

#### 1. Update Application Code

```bash
cd /path/to/Admissions-Genie
git pull origin main  # Or deploy latest code
```

#### 2. Install/Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

**Key Dependencies:**
- `cryptography>=41.0.0` - Encryption library
- `Flask==2.3.3` - Web framework
- `bcrypt==4.0.1` - Password hashing

#### 3. Generate and Set Encryption Key

```bash
# Generate key
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Set in environment (choose one method)

# Method 1: .env file (for single server)
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env

# Method 2: Render/Heroku (for PaaS)
# Add via web interface: Settings → Environment Variables

# Method 3: AWS/Azure (for cloud)
# Store in AWS Secrets Manager or Azure Key Vault
```

#### 4. Run Database Migration

```bash
python3 migrations/add_security_columns.py upgrade
```

**Verification:**
```bash
# Check if columns were added
sqlite3 admissions.db "PRAGMA table_info(users);"
# Should show: failed_login_attempts, locked_until, last_failed_login
```

#### 5. Restart Application

```bash
# Local/VM
sudo systemctl restart admissions-genie

# Render
# Auto-restarts on git push

# Docker
docker-compose restart
```

### Post-Deployment Verification (15-30 minutes)

#### Test 1: Encryption Verification

```bash
python3 -c "
import os
os.environ['ENCRYPTION_KEY'] = 'YOUR_KEY_HERE'

from utils.encryption import encrypt_value, decrypt_value

original = 'Test PHI Data'
encrypted = encrypt_value(original)
decrypted = decrypt_value(encrypted)

assert original == decrypted, 'Encryption/decryption failed'
print('✅ Encryption working correctly')
"
```

#### Test 2: Account Lockout

1. Navigate to login page
2. Enter valid email, wrong password 5 times
3. Verify account locked message appears
4. Wait 30 minutes OR unlock via admin panel
5. Verify login works after unlock

#### Test 3: Password Complexity

1. Navigate to registration page
2. Try password: `weak` → Should be rejected
3. Try password: `WeakPass1!` → Should be rejected (too short)
4. Try password: `MySecureP@ssw0rd2024` → Should be accepted

#### Test 4: Audit Logging

```bash
python3 -c "
from models.audit_log import AuditLog

# Get recent audit logs
logs = AuditLog.get_recent(limit=10)
print(f'Found {len(logs)} audit log entries')

# Verify login events are logged
for log in logs:
    print(f'{log.action}: {log.created_at}')
"
```

#### Test 5: Create Test Admission

1. Login with valid credentials
2. Create new admission
3. Check database to verify data is encrypted:
   ```bash
   sqlite3 admissions.db "SELECT patient_initials FROM admissions LIMIT 1;"
   ```
4. Should see encrypted gibberish, not plain text

---

## 🔐 Security Configuration

### Required Environment Variables

```bash
# Encryption (REQUIRED)
ENCRYPTION_KEY=<generated-key>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db  # Production PostgreSQL

# Session Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
SESSION_TIMEOUT_MINUTES=15

# Account Lockout
MAX_FAILED_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# Password Policy
MIN_PASSWORD_LENGTH=12
REQUIRE_PASSWORD_COMPLEXITY=true

# Azure OpenAI
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo
```

### Optional Security Enhancements

```bash
# Rate Limiting (Production)
RATELIMIT_STORAGE_URL=redis://localhost:6379
RATELIMIT_DEFAULT=100 per hour

# Error Tracking
SENTRY_DSN=<your-sentry-dsn>

# File Storage (Cloud)
USE_S3=true
AWS_S3_BUCKET=<bucket-name>
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_S3_ENCRYPTION=AES256
```

---

## 📊 Monitoring & Maintenance

### Daily Checks

1. **Audit Log Review**
   ```bash
   python3 -c "
   from models.audit_log import AuditLog
   from datetime import datetime, timedelta

   # Get last 24 hours
   yesterday = datetime.now() - timedelta(days=1)
   logs = AuditLog.search(start_date=yesterday)

   # Check for suspicious activity
   failed_logins = [l for l in logs if l.action == 'login_failed']
   lockouts = [l for l in logs if l.action == 'login_blocked']

   print(f'Failed logins: {len(failed_logins)}')
   print(f'Account lockouts: {len(lockouts)}')
   "
   ```

2. **Backup Verification**
   - Automated backups running
   - Backup encryption enabled
   - Test restore procedure monthly

### Weekly Tasks

1. **Security Updates**
   ```bash
   pip list --outdated
   # Update security-critical packages
   pip install --upgrade cryptography bcrypt
   ```

2. **Audit Log Rotation**
   - Audit logs are stored indefinitely by default
   - Archive old logs (>1 year) to cold storage
   - Maintain 6 years for HIPAA compliance

### Monthly Tasks

1. **Access Review**
   - Review all user accounts
   - Disable inactive accounts (90+ days)
   - Verify admin account list

2. **Password Expiration** (Optional)
   - NIST no longer recommends forced rotation
   - Only force change if breach suspected

### Quarterly Tasks

1. **Penetration Testing**
   - Run OWASP ZAP or similar tool
   - Test common vulnerabilities
   - Document findings

2. **Backup Restore Test**
   - Restore backup to staging
   - Verify data integrity
   - Test encryption key recovery

---

## 🚨 Incident Response

### If Encryption Key is Lost

⚠️ **WARNING:** If encryption key is lost, encrypted data CANNOT be recovered.

**Prevention:**
1. Store key in multiple secure locations
2. Use cloud key management (AWS KMS, Azure Key Vault)
3. Implement key rotation procedure

**If lost:**
1. All new data will use new key
2. Old encrypted data is permanently inaccessible
3. May need to re-enter historical data if critical

### If Account is Locked Out

**User Self-Service:**
- Wait 30 minutes for auto-unlock
- Contact administrator

**Admin Unlock:**
```python
from models.user import User

user = User.get_by_email('locked@example.com')
user.unlock()
print(f'User {user.email} has been unlocked')
```

### If Suspicious Activity Detected

1. **Review Audit Logs**
   ```python
   from models.audit_log import AuditLog

   # Get all failed logins in last hour
   logs = AuditLog.search(action='login_failed')
   for log in logs[-20:]:
       print(f'{log.created_at}: {log.ip_address} - {log.changes}')
   ```

2. **Block IP Address** (if needed)
   - Update rate limiting rules
   - Add to firewall blacklist

3. **Force Password Reset** (if compromised)
   ```python
   from models.user import User

   user = User.get_by_email('compromised@example.com')
   user.deactivate()
   # Send password reset email
   ```

---

## 📞 Support & Troubleshooting

### Common Issues

#### Issue: "ENCRYPTION_KEY not set" error

**Solution:**
```bash
# Check if key is set
echo $ENCRYPTION_KEY

# If not set, add to .env
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output to .env file
```

#### Issue: Cannot decrypt existing data

**Cause:** Encryption key changed or lost

**Solution:**
1. Restore original encryption key
2. If lost, data cannot be recovered
3. For new deployments, use development mode (no ENCRYPTION_KEY) for testing

#### Issue: Password rejected despite meeting requirements

**Solution:**
```bash
# Test password manually
python3 -c "
from utils.password_validator import validate_password_strength

password = 'YourPasswordHere'
is_valid, errors = validate_password_strength(password)

if not is_valid:
    for error in errors:
        print(f'- {error}')
"
```

#### Issue: Migration fails "column already exists"

**Solution:**
Migration is idempotent - safe to run multiple times. If error occurs:
```bash
# Check current schema
sqlite3 admissions.db "PRAGMA table_info(users);"

# If columns exist, migration is already complete
```

---

## 📚 Additional Resources

- **HIPAA Compliance Guide:** `/HIPAA_COMPLIANCE.md`
- **Implementation Status:** `/HIPAA_IMPLEMENTATION_STATUS.md`
- **Testing Documentation:** `/TESTING.md`
- **API Documentation:** `/API_DOCUMENTATION.md`

---

## 🎓 Training Materials

### For Administrators

1. **Encryption Key Management**
   - Never commit keys to version control
   - Store in secure key management system
   - Rotate keys annually (advanced)

2. **User Account Management**
   - Unlock locked accounts
   - Reset passwords if needed
   - Review audit logs for suspicious activity

3. **Monitoring & Alerts**
   - Set up automated alerts for failed logins
   - Monitor audit logs daily
   - Review access logs weekly

### For End Users

1. **Password Requirements**
   - Minimum 12 characters
   - Mix of upper/lower/numbers/symbols
   - No common patterns

2. **Account Lockout**
   - 5 failed attempts = 30-minute lockout
   - Contact admin if locked out
   - Wait 30 minutes for auto-unlock

3. **Session Timeout**
   - 15 minutes of inactivity
   - Save work frequently
   - Log out when done

---

## ✅ Post-Deployment Checklist

### Immediate (Day 1)

- [ ] Encryption key generated and stored securely
- [ ] Database migration completed successfully
- [ ] All admin passwords updated to meet requirements
- [ ] Test login/registration with new password requirements
- [ ] Test account lockout mechanism
- [ ] Test admission creation with encryption enabled
- [ ] Verify audit logging is working
- [ ] Document encryption key location

### First Week

- [ ] Monitor audit logs daily for issues
- [ ] Train administrators on new security features
- [ ] Create backup of encryption key (separate location)
- [ ] Update incident response plan
- [ ] Test backup/restore procedure
- [ ] Review all active user accounts
- [ ] Send communication to all users about new password requirements

### First Month

- [ ] Review audit logs for anomalies
- [ ] Conduct security testing
- [ ] Verify all BAAs are signed
- [ ] Complete HIPAA self-assessment
- [ ] Document lessons learned
- [ ] Plan for future enhancements (MFA, etc.)

---

**Document Version:** 1.0
**Maintained By:** Development Team
**Next Review:** After first production deployment

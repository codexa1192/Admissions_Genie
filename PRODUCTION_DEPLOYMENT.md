# Production Deployment Guide

## Overview
This guide walks you through deploying Admissions Genie to production with full HIPAA compliance, data persistence, and performance optimizations.

**Estimated Time:** 2-3 hours
**Cost:** ~$70-120/month

---

## Phase 1: PostgreSQL Database Setup (15 minutes)

### Step 1: Add PostgreSQL to Render

1. Go to https://dashboard.render.com
2. Click your `Admissions_Genie` web service
3. Go to "Environment" tab
4. Scroll down to "Add-ons"
5. Click "Add PostgreSQL"
6. Select "Starter" plan ($7/month)
7. Wait for provisioning (2-3 minutes)

### Step 2: Configure Database URL

Render automatically adds `DATABASE_URL` environment variable. Verify it exists:
- Go to "Environment" tab
- Look for `DATABASE_URL` (starts with `postgresql://`)
- ✅ Already configured!

### Step 3: Initialize Database

The database schema will auto-initialize on first deploy. To manually initialize:

```bash
# SSH into your Render shell (optional)
python3 -c "from config.database import init_db; init_db()"
```

---

## Phase 2: AWS S3 File Storage (20 minutes)

### Step 1: Create S3 Bucket

1. Go to https://console.aws.com/s3
2. Click "Create bucket"
3. **Bucket name:** `admissions-genie-uploads-prod` (must be globally unique)
4. **Region:** us-east-1
5. **Block Public Access:** Keep ALL boxes checked (✅ Private bucket)
6. **Encryption:** Enable "Server-side encryption" with AES-256
7. Click "Create bucket"

### Step 2: Create IAM User

1. Go to https://console.aws.com/iam/
2. Click "Users" → "Create user"
3. **User name:** `admissions-genie-s3-user`
4. Click "Next"
5. **Permissions:** Select "Attach policies directly"
6. Search for and attach: `AmazonS3FullAccess` (or create custom policy below)
7. Click "Create user"

**Recommended Custom Policy (More Secure):**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::admissions-genie-uploads-prod/*"
        }
    ]
}
```

### Step 3: Get Access Keys

1. Click on the user you just created
2. Go to "Security credentials" tab
3. Click "Create access key"
4. Select "Application running outside AWS"
5. Click "Next" → "Create access key"
6. **Save these keys securely:**
   - Access Key ID: `AKIA...`
   - Secret Access Key: `abc123...`

### Step 4: Add S3 Config to Render

Go to your Render dashboard → Environment → Add these variables:

```
USE_S3=true
AWS_ACCESS_KEY_ID=<your access key>
AWS_SECRET_ACCESS_KEY=<your secret key>
AWS_S3_BUCKET=admissions-genie-uploads-prod
AWS_S3_REGION=us-east-1
```

---

## Phase 3: Redis for Background Tasks (10 minutes)

### Option A: Upstash Redis (Recommended - Easiest)

1. Go to your Render dashboard
2. Click your web service
3. Go to "Environment" tab
4. Scroll to "Add-ons"
5. Click "Add Redis"
6. Select "Upstash" ($10/month)
7. Render automatically adds `REDIS_URL` environment variable

### Option B: Render Redis (Alternative)

1. In Render dashboard, click "New +"
2. Select "Redis"
3. Choose "Starter" plan ($10/month)
4. Note the "Internal Redis URL"
5. Add to your web service environment:
   ```
   REDIS_URL=<your redis internal URL>
   ```

---

## Phase 4: Celery Worker Service (15 minutes)

### Step 1: Create Worker Service

1. In Render dashboard, click "New +"
2. Select "Background Worker"
3. Connect your GitHub repository: `codexa1192/Admissions_Genie`
4. **Name:** `admissions-genie-worker`
5. **Environment:** Python 3
6. **Build Command:** `pip install -r requirements.txt`
7. **Start Command:** `celery -A celery_worker worker --loglevel=info`

### Step 2: Copy Environment Variables

Copy ALL environment variables from your web service to the worker:
- SECRET_KEY
- FLASK_ENV
- DATABASE_URL (already linked if using Render PostgreSQL)
- REDIS_URL (already linked if using Render add-on)
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_DEPLOYMENT
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_S3_BUCKET
- USE_S3=true

### Step 3: Deploy Worker

Click "Create Background Worker" - it will auto-deploy.

---

## Phase 5: Sentry Error Tracking (10 minutes)

### Step 1: Create Sentry Account

1. Go to https://sentry.io/signup/
2. Sign up (FREE plan available)
3. Create new project
4. Select "Flask" as platform
5. Copy your DSN (looks like: `https://abc@xyz.ingest.sentry.io/123`)

### Step 2: Add to Render

```
SENTRY_DSN=<your sentry DSN>
```

---

## Phase 6: Security Configuration (5 minutes)

Add these environment variables to Render:

```
# HIPAA session timeout (15 minutes)
SESSION_TIMEOUT_MINUTES=15

# Force HTTPS in production
SESSION_COOKIE_SECURE=true

# Enable PHI strict mode
PHI_STRICT_MODE=true
```

---

## Phase 7: Seed Production Database (10 minutes)

### Option A: Via Render Shell

1. Go to your Render web service
2. Click "Shell" tab
3. Run:
   ```bash
   python3 seed_database.py
   ```

### Option B: Via Local Script

```bash
# Set production DATABASE_URL locally
export DATABASE_URL="<your production postgres url>"
python3 seed_database.py
```

---

## Phase 8: Verification Checklist

### Database ✅
- [ ] PostgreSQL connected
- [ ] Tables created
- [ ] Sample data loaded
- [ ] Can create new admissions

### File Storage ✅
- [ ] S3 bucket accessible
- [ ] Can upload files
- [ ] Files are encrypted (AES-256)
- [ ] Can retrieve files

### Background Processing ✅
- [ ] Redis connected
- [ ] Celery worker running
- [ ] Tasks process asynchronously
- [ ] No 60-second page hangs

### Security ✅
- [ ] HTTPS enforced
- [ ] Session timeout active (15 min)
- [ ] Audit logs recording
- [ ] PHI encryption enabled

### Monitoring ✅
- [ ] Sentry receiving errors
- [ ] Application starts without errors
- [ ] Health check endpoint responding

---

## Environment Variables Summary

**Required for Production:**
```
# Core
SECRET_KEY=<generated 64-char hex>
FLASK_ENV=production

# Database (auto-added by Render)
DATABASE_URL=postgresql://...

# Azure OpenAI
AZURE_OPENAI_API_KEY=<your key>
AZURE_OPENAI_ENDPOINT=https://eastus.api.cognitive.microsoft.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# AWS S3
USE_S3=true
AWS_ACCESS_KEY_ID=<your key>
AWS_SECRET_ACCESS_KEY=<your secret>
AWS_S3_BUCKET=admissions-genie-uploads-prod
AWS_S3_REGION=us-east-1

# Redis (auto-added by Render addon)
REDIS_URL=redis://...

# Sentry
SENTRY_DSN=https://...

# Security
SESSION_TIMEOUT_MINUTES=15
SESSION_COOKIE_SECURE=true
PHI_STRICT_MODE=true
```

---

## Monthly Cost Breakdown

- **Render Web Service:** FREE (Starter tier)
- **Render PostgreSQL:** $7/month
- **Render Redis:** $10/month
- **Render Worker:** FREE (Starter tier)
- **AWS S3:** $1-5/month (storage + transfers)
- **Azure OpenAI:** $50-100/month (~$0.25-0.50 per admission)
- **Sentry:** FREE (Developer plan)

**Total: ~$70-120/month**

---

## Post-Deployment Tasks

### 1. Update Demo Banner

The app still shows "DEMO MODE" banner. To update:

Edit `templates/base.html`:
```html
<!-- Change from: -->
<div class="alert alert-info">EVALUATION MODE</div>

<!-- To: -->
<div class="alert alert-success">PRODUCTION - HIPAA Compliant</div>
```

### 2. Configure Backups

Render PostgreSQL includes daily backups. To configure:
1. Go to PostgreSQL add-on
2. Click "Backups" tab
3. Verify daily backups are enabled
4. Retention: 7 days (Starter plan)

### 3. Set Up Monitoring

**Uptime Monitoring (FREE):**
1. Go to https://uptimerobot.com
2. Add monitor for your Render URL
3. Set check interval: 5 minutes
4. Email alerts for downtime

### 4. BAA Requirements

For HIPAA compliance, you need Business Associate Agreements (BAA) with:

- **Render:** Contact support for BAA (available on paid plans)
- **AWS:** Sign BAA in AWS Console (Settings → BAA)
- **Azure:** BAA included with Enterprise Agreement

---

## Troubleshooting

### Database Connection Errors
```
Error: could not connect to server
```
**Fix:** Verify `DATABASE_URL` is set and PostgreSQL add-on is active.

### S3 Upload Failures
```
Error: Failed to upload to S3
```
**Fix:** Verify AWS credentials and bucket name are correct. Check IAM permissions.

### Celery Tasks Not Processing
```
Tasks stuck in PENDING state
```
**Fix:** Verify worker service is running and `REDIS_URL` is set on both web and worker.

### Session Timeout Not Working
```
Users not logged out after 15 minutes
```
**Fix:** Verify `SESSION_TIMEOUT_MINUTES=15` is set. Check middleware is initialized in app.py.

---

## Support

For issues:
1. Check Render logs (Logs tab)
2. Check Sentry for errors
3. Review this guide
4. Contact: jthayer@verisightanalytics.com

---

## Next Steps

After production deployment:
1. ✅ Test with real discharge summaries
2. ✅ Train SNF staff
3. ✅ Monitor error rates in Sentry
4. ✅ Review audit logs weekly
5. ✅ Schedule HIPAA compliance audit

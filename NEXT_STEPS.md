# Next Steps - Production Setup

**Status:** PostgreSQL ✅ Already configured
**Remaining Time:** ~1-1.5 hours

---

## Quick Status Check

✅ **Code Integration:** 100% Complete
✅ **PostgreSQL Database:** Already configured
⏳ **AWS S3:** Need to create bucket (~20 min)
⏳ **Redis:** Need to add addon (~10 min)
⏳ **Celery Worker:** Need to create service (~15 min)
⏳ **Sentry:** Need to configure (~10 min)
⏳ **Environment Variables:** Need to verify/add (~10 min)

---

## Remaining Setup Tasks

### 1. AWS S3 File Storage (20 minutes) - REQUIRED

**Why:** Files need persistent storage that survives Render redeployments.

**Steps:**

#### Create S3 Bucket
1. Go to https://console.aws.com/s3
2. Click "Create bucket"
3. **Bucket name:** `admissions-genie-uploads-prod` (must be globally unique - try variations if taken)
4. **Region:** us-east-1
5. **Block Public Access:** Keep ALL boxes checked ✅
6. **Encryption:** Enable "Server-side encryption with Amazon S3 managed keys (SSE-S3)"
7. Click "Create bucket"

#### Create IAM User for S3 Access
1. Go to https://console.aws.com/iam/
2. Click "Users" → "Create user"
3. **User name:** `admissions-genie-s3-user`
4. Click "Next"
5. **Permissions:** Select "Attach policies directly"
6. Create custom inline policy with this JSON:

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

7. Click "Create user"

#### Get Access Keys
1. Click on the user you just created
2. Go to "Security credentials" tab
3. Click "Create access key"
4. Select "Application running outside AWS"
5. Click "Create access key"
6. **SAVE THESE SECURELY:**
   - Access Key ID: `AKIA...`
   - Secret Access Key: `abc123...`

**Cost:** $1-5/month (storage + transfers)

---

### 2. Redis for Background Tasks (10 minutes) - OPTIONAL

**Why:** Enables async document processing (eliminates 60-second UI hangs).

**Note:** This is optional for initial production launch. The app works without it but processes documents synchronously.

**Steps:**
1. Go to Render dashboard → Your web service
2. Click "Environment" tab
3. Scroll to "Add-ons"
4. Click "Add Redis"
5. Select "Upstash" ($10/month)
6. Wait for provisioning
7. Verify `REDIS_URL` environment variable appears

**Cost:** $10/month

---

### 3. Celery Worker Service (15 minutes) - OPTIONAL

**Why:** Background worker for async document processing (only needed if you added Redis).

**Skip this if you didn't add Redis above.**

**Steps:**
1. In Render dashboard, click "New +" → "Background Worker"
2. Connect GitHub repo: `codexa1192/Admissions_Genie`
3. **Name:** `admissions-genie-worker`
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `celery -A celery_worker worker --loglevel=info`
6. Copy ALL environment variables from your web service:
   - DATABASE_URL (linked automatically if same account)
   - REDIS_URL (linked automatically if same account)
   - AZURE_OPENAI_API_KEY
   - AZURE_OPENAI_ENDPOINT
   - AZURE_OPENAI_DEPLOYMENT
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_S3_BUCKET
   - USE_S3
7. Click "Create Background Worker"

**Cost:** FREE (Starter tier)

---

### 4. Sentry Error Tracking (10 minutes) - OPTIONAL

**Why:** Production error monitoring and alerting.

**Steps:**
1. Go to https://sentry.io/signup/
2. Sign up with your email
3. Create new project
4. Select "Flask" as platform
5. Copy your DSN (looks like: `https://abc123@o123.ingest.sentry.io/456`)
6. Add to Render environment variables (see Step 5 below)

**Cost:** FREE (Developer plan, up to 5K errors/month)

---

### 5. Configure Environment Variables (10 minutes) - REQUIRED

Go to Render dashboard → Your web service → "Environment" tab.

**Verify these exist (from previous setup):**
```bash
✅ SECRET_KEY
✅ FLASK_ENV=production
✅ DATABASE_URL (auto-added by PostgreSQL)
✅ AZURE_OPENAI_API_KEY
✅ AZURE_OPENAI_ENDPOINT
✅ AZURE_OPENAI_DEPLOYMENT
```

**Add these NEW variables:**

```bash
# AWS S3 (from Step 1)
USE_S3=true
AWS_ACCESS_KEY_ID=<your access key from Step 1>
AWS_SECRET_ACCESS_KEY=<your secret key from Step 1>
AWS_S3_BUCKET=admissions-genie-uploads-prod
AWS_S3_REGION=us-east-1

# Security (REQUIRED)
SESSION_TIMEOUT_MINUTES=15
SESSION_COOKIE_SECURE=true
PHI_STRICT_MODE=true

# Sentry (OPTIONAL - only if you completed Step 4)
SENTRY_DSN=<your sentry DSN from Step 4>
```

**Notes:**
- `REDIS_URL` is auto-added if you added the Redis addon
- `DATABASE_URL` is already set from your PostgreSQL database
- After adding variables, Render will automatically redeploy

---

### 6. Seed Production Database (5 minutes) - OPTIONAL

**Why:** Load sample facilities, payers, rates, and cost models for testing.

**Via Render Shell:**
1. Go to your web service → "Shell" tab
2. Wait for shell to connect
3. Run:
```bash
python3 seed_database.py
```

**Or via Local Script:**
```bash
# Get DATABASE_URL from Render environment variables
export DATABASE_URL="<your production postgres url>"
python3 seed_database.py
```

**What this loads:**
- 2 sample facilities (Sunrise SNF, Evergreen Care Center)
- 5 payers (Medicare FFS, Medicare Advantage, Medicaid, Family Care, Commercial)
- Active rates for all facility/payer combinations
- Cost models for all acuity levels
- 2 admin and user accounts (you already have these)
- 3 sample admissions (demo data)

---

## Verification Checklist

After completing the setup, verify everything works:

### ✅ Database Connection
```bash
# Visit health check endpoint
curl https://your-app.onrender.com/health/detailed
```
Look for: `"database": {"status": "healthy"}`

### ✅ S3 File Storage
1. Log in to the application
2. Go to "New Admission"
3. Upload a test document
4. Check your S3 bucket - file should appear with AES-256 encryption
5. View the admission - document should be accessible

### ✅ Session Timeout (HIPAA)
1. Log in to the application
2. Wait 15 minutes without clicking anything
3. Try to navigate to any page
4. Should be logged out with message: "Your session has expired"

### ✅ Audit Logging
1. Log in as admin
2. Check PostgreSQL `audit_logs` table:
```sql
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
```
3. Should see your login event with user_id, IP address, timestamp

### ✅ HTTPS Enforcement
```bash
# Try to access via HTTP (should redirect to HTTPS)
curl -I http://your-app.onrender.com
# Look for: Location: https://your-app.onrender.com
```

### ✅ Error Tracking (if Sentry configured)
1. Go to Sentry dashboard
2. Check for test events
3. Application errors should appear in Sentry

---

## Monthly Cost Summary

With PostgreSQL already configured:

| Service | Cost | Status |
|---------|------|--------|
| Render Web Service | FREE | ✅ Running |
| Render PostgreSQL | $7/month | ✅ Already configured |
| AWS S3 | $1-5/month | ⏳ Need to create |
| Render Redis | $10/month | ⏳ Optional |
| Render Worker | FREE | ⏳ Optional (needs Redis) |
| Azure OpenAI | $50-100/month | ✅ Already configured |
| Sentry | FREE | ⏳ Optional |
| **Total** | **$58-112/month** | |

---

## What Happens When You Redeploy?

After adding environment variables, Render will automatically redeploy. Here's what will happen:

1. **Build:** Installs dependencies (boto3, celery, sentry-sdk, etc.)
2. **Deploy:** Starts application with new configuration
3. **Initialization:** Database tables created/verified
4. **Features Activated:**
   - ✅ S3 file storage (encrypted)
   - ✅ 15-minute session timeout
   - ✅ Audit logging to database
   - ✅ HTTPS enforcement
   - ✅ Health check endpoints
   - ✅ Sentry error tracking (if configured)

---

## Troubleshooting

### S3 Upload Fails
```
Error: Failed to upload to S3
```
**Check:**
- AWS credentials are correct
- Bucket name matches exactly
- IAM user has PutObject permission
- Bucket is in the correct region (us-east-1)

### Database Connection Error
```
Error: could not connect to server
```
**Check:**
- `DATABASE_URL` environment variable is set
- PostgreSQL addon is active in Render

### Session Timeout Not Working
**Check:**
- `SESSION_TIMEOUT_MINUTES=15` is set
- Application redeployed after adding variable
- Using a new browser session (clear cookies)

### Import Error for psycopg2
**This is expected** if not using PostgreSQL yet. The app automatically falls back to SQLite.

---

## Need Help?

- **Documentation:** See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for detailed steps
- **HIPAA Compliance:** See [HIPAA_COMPLIANCE.md](HIPAA_COMPLIANCE.md)
- **Support:** jthayer@verisightanalytics.com

---

## After Production Launch

Once everything is working:

1. ✅ Test with real discharge summaries
2. ✅ Train SNF staff
3. ✅ Monitor error rates in Sentry
4. ✅ Review audit logs weekly
5. ✅ Sign Business Associate Agreements:
   - AWS S3 (Settings → BAA in AWS Console)
   - Render (Contact support for BAA - requires Team plan $19/month)
   - Azure OpenAI (Included with Enterprise Agreement)

---

**Ready to go?** Start with Step 1 (AWS S3 setup) - it's the only critical remaining piece!

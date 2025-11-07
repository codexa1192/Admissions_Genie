# Copy-Paste Production Setup

**Time Required:** 30-40 minutes (mostly waiting for AWS/Render)
**Difficulty:** Just copy-paste commands

---

## Part 1: AWS S3 Setup (20 minutes)

### Step 1.1: Create S3 Bucket via AWS CLI

**Option A: If you have AWS CLI installed**

Open your terminal and run these commands exactly:

```bash
# Set your desired bucket name (must be globally unique)
BUCKET_NAME="admissions-genie-uploads-prod-$(date +%s)"

# Create bucket with encryption
aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region us-east-1 \
  --acl private

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Save bucket name for later
echo "Your bucket name: $BUCKET_NAME"
echo $BUCKET_NAME > bucket_name.txt
```

**SAVE THIS OUTPUT** - you'll need the bucket name!

---

**Option B: If you don't have AWS CLI**

1. Go to: https://console.aws.com/s3
2. Click **"Create bucket"**
3. **Bucket name:** `admissions-genie-uploads-prod-YOUR-INITIALS` (e.g., `admissions-genie-uploads-prod-jt`)
4. **Region:** us-east-1
5. **Block Public Access:** Keep all 4 checkboxes CHECKED ✅
6. Scroll down to **"Default encryption"**
7. Select **"Server-side encryption with Amazon S3 managed keys (SSE-S3)"**
8. Click **"Create bucket"**
9. **SAVE THE BUCKET NAME** - write it down!

---

### Step 1.2: Create IAM User and Get Keys

**Option A: Via AWS CLI**

```bash
# Get bucket name from previous step
BUCKET_NAME=$(cat bucket_name.txt)

# Create IAM user
aws iam create-user --user-name admissions-genie-s3-user

# Create inline policy
cat > s3-policy.json <<EOF
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
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

# Attach policy to user
aws iam put-user-policy \
  --user-name admissions-genie-s3-user \
  --policy-name S3UploadPolicy \
  --policy-document file://s3-policy.json

# Create access key
aws iam create-access-key --user-name admissions-genie-s3-user > aws-keys.json

# Display keys
echo "=== SAVE THESE KEYS ==="
cat aws-keys.json | grep -E 'AccessKeyId|SecretAccessKey'
echo "======================="
```

**SAVE THE ACCESS KEY AND SECRET KEY** - you'll need these for Render!

---

**Option B: Via AWS Console**

1. Go to: https://console.aws.com/iam/
2. Click **"Users"** → **"Create user"**
3. **User name:** `admissions-genie-s3-user`
4. Click **"Next"**
5. Click **"Attach policies directly"**
6. Click **"Create policy"** (opens new tab)
7. Click **"JSON"** tab
8. **DELETE EVERYTHING** and paste this (replace `YOUR-BUCKET-NAME`):

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
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

9. Click **"Next"**
10. **Policy name:** `AdmissionsGenieS3Policy`
11. Click **"Create policy"**
12. Go back to the user creation tab, click refresh ↻
13. Search for `AdmissionsGenieS3Policy` and check the box
14. Click **"Next"** → **"Create user"**
15. Click on the user you just created
16. Click **"Security credentials"** tab
17. Click **"Create access key"**
18. Select **"Application running outside AWS"**
19. Click **"Next"** → **"Create access key"**
20. **SAVE THESE KEYS:**
    - Access Key ID: `AKIA...`
    - Secret Access Key: `abc123...`

---

## Part 2: Configure Render (10 minutes)

### Step 2.1: Add Environment Variables

1. Go to: https://dashboard.render.com
2. Click on your **Admissions Genie** web service
3. Click **"Environment"** tab
4. Click **"Add Environment Variable"** for each of these:

**Copy-paste these exactly:**

```bash
# S3 Configuration
USE_S3=true
AWS_S3_REGION=us-east-1
```

Now add these with YOUR values:

```bash
AWS_S3_BUCKET=<paste your bucket name from Step 1.1>
AWS_ACCESS_KEY_ID=<paste your access key from Step 1.2>
AWS_SECRET_ACCESS_KEY=<paste your secret key from Step 1.2>
```

**Security Configuration** (copy-paste exactly):

```bash
SESSION_TIMEOUT_MINUTES=15
SESSION_COOKIE_SECURE=true
PHI_STRICT_MODE=true
```

### Step 2.2: Trigger Deployment

Click **"Save Changes"** at the bottom.

Render will automatically redeploy. This takes 5-10 minutes.

Watch the **"Logs"** tab - you should see:
- ✅ `Installing dependencies...`
- ✅ `Starting application...`
- ✅ `All blueprints registered successfully`

---

## Part 3: Verify Everything Works (5 minutes)

### Step 3.1: Check Health Endpoint

Once deployment completes, run this command (replace YOUR-APP-URL):

```bash
curl https://YOUR-APP-URL.onrender.com/health/detailed
```

You should see JSON with:
- `"database": {"status": "healthy"}`
- `"s3": {"status": "configured"}`

### Step 3.2: Test File Upload

1. Go to your app: `https://YOUR-APP-URL.onrender.com`
2. Log in: `admin@admissionsgenie.com` / `admin123`
3. Click **"New Admission"**
4. Upload a test document
5. Check your S3 bucket - file should appear!

### Step 3.3: Test Session Timeout

1. Log in to the app
2. Wait 15 minutes (or change `SESSION_TIMEOUT_MINUTES=1` for testing)
3. Try to click anything
4. Should be logged out with: "Your session has expired"

---

## That's It! ✅

Your production setup is complete with:
- ✅ PostgreSQL database (you already had this)
- ✅ S3 file storage with encryption
- ✅ 15-minute session timeout
- ✅ Audit logging
- ✅ HTTPS enforcement
- ✅ Health checks

---

## Optional: Add Redis + Celery (25 minutes)

Only do this if you want async document processing.

### Redis Addon (5 minutes)

1. Go to Render dashboard → Your web service
2. Click **"Environment"** tab
3. Scroll to **"Add-ons"**
4. Click **"Add Redis"**
5. Select **"Upstash"** ($10/month)
6. Click **"Provision"**
7. Wait 2 minutes
8. Verify `REDIS_URL` appears in environment variables

### Celery Worker (20 minutes)

1. In Render dashboard, click **"New +"** → **"Background Worker"**
2. **Connect GitHub:** Select `codexa1192/Admissions_Genie`
3. **Name:** `admissions-genie-worker`
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `celery -A celery_worker worker --loglevel=info`
6. **Environment:** Copy ALL variables from your web service:
   - Click your web service → Environment tab
   - Copy each variable to the worker
7. Click **"Create Background Worker"**
8. Wait 5-10 minutes for first deployment

---

## Optional: Add Sentry (10 minutes)

Only do this if you want error tracking.

1. Go to: https://sentry.io/signup/
2. Sign up with your email
3. **Organization name:** Your company name
4. **Project name:** `admissions-genie`
5. **Platform:** Select **"Flask"**
6. Copy the DSN (looks like: `https://abc123@o123.ingest.sentry.io/456`)
7. Go to Render → Your web service → Environment
8. Add: `SENTRY_DSN=<paste your DSN>`
9. Click **"Save Changes"** (triggers redeploy)

---

## Troubleshooting

### S3 Upload Fails
```
Error: Failed to upload to S3
```
**Fix:**
- Check AWS credentials are correct in Render
- Verify bucket name matches exactly
- Check bucket region is `us-east-1`

### Can't Create Bucket (Name Taken)
**Fix:** Bucket names must be globally unique. Try:
- `admissions-genie-uploads-YOUR-INITIALS`
- `admissions-genie-uploads-$(date +%s)` (adds timestamp)

### Session Timeout Not Working
**Fix:**
- Verify `SESSION_TIMEOUT_MINUTES=15` in Render
- Clear browser cookies
- Wait for redeploy to complete

---

## Summary

**Minimum Required (30 min):**
- ✅ AWS S3 bucket with keys
- ✅ 6 environment variables in Render
- ✅ Wait for redeploy

**Optional Enhancements (+35 min):**
- Redis addon ($10/month)
- Celery worker (FREE)
- Sentry error tracking (FREE)

**Total Cost:** $58-112/month (mostly Azure OpenAI)

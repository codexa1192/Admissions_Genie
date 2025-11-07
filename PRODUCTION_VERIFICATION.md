# Production Verification Checklist

**Date:** November 6, 2025
**Status:** Ready for verification after Render deployment completes

---

## Prerequisites

Before starting verification:

- ✅ PostgreSQL database configured on Render
- ✅ Azure Blob Storage container created: `admissions-genie-uploads`
- ✅ All 7 environment variables added to Render
- ⏳ Render deployment completed (check for "Live" status)

---

## Step 1: Verify Deployment Status (2 minutes)

### 1.1 Check Render Dashboard

1. Go to: https://dashboard.render.com
2. Click your **Admissions Genie** web service
3. Verify status shows **"Live"** (green)
4. Check **Logs** tab for these messages:

**Expected Success Messages:**
```
✅ Successfully installed azure-storage-blob-12.19.0
✅ All blueprints registered successfully
✅ Starting Admissions Genie
```

**Deployment Issues (if you see these):**

| Error | Fix |
|-------|-----|
| `ImportError: azure-storage-blob` | Dependencies failed - click "Manual Deploy" → "Clear build cache & deploy" |
| `ValueError: Cannot use both S3 and Azure` | Remove `USE_S3=true` environment variable |
| `AuthenticationError` from Azure | Check `AZURE_STORAGE_ACCOUNT_KEY` is copied correctly |

### 1.2 Get Your App URL

Your Render app URL will be something like:
```
https://admissions-genie-XXXXX.onrender.com
```

**Save this URL** - you'll need it for all tests below.

---

## Step 2: Test Health Endpoint (1 minute)

This verifies Azure Blob Storage is properly configured.

### 2.1 Run Health Check

Replace `YOUR-APP-URL` with your actual Render URL:

```bash
curl https://YOUR-APP-URL.onrender.com/health/detailed
```

### 2.2 Expected Response

You should see JSON like this:

```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T12:34:56",
  "checks": {
    "database": {
      "status": "healthy",
      "type": "postgresql"
    },
    "azure_blob": {
      "status": "configured",
      "account": "admissionsgenie80834",
      "container": "admissions-genie-uploads"
    },
    "openai": {
      "status": "configured",
      "deployment": "gpt-4-turbo"
    },
    "security": {
      "session_timeout_minutes": 15,
      "https_only": true,
      "phi_strict_mode": true
    }
  }
}
```

**What to check:**
- ✅ `"status": "healthy"`
- ✅ `"azure_blob": {"status": "configured"}`
- ✅ `"session_timeout_minutes": 15`

**If health check fails:**
- ❌ 502 Bad Gateway → App is still deploying, wait 2 more minutes
- ❌ 500 Internal Server Error → Check Render logs for error details
- ❌ `"azure_blob": {"status": "not_configured"}` → Environment variables not set correctly

---

## Step 3: Test File Upload to Azure (5 minutes)

This verifies end-to-end file storage functionality.

### 3.1 Log In to Production App

1. Go to: `https://YOUR-APP-URL.onrender.com`
2. Log in with: `admin@admissionsgenie.com` / `admin123`

### 3.2 Create Test Admission

1. Click **"New Admission"** button
2. Fill in form:
   - **Facility:** Select any facility
   - **Payer:** Select any payer (Medicare FFS recommended)
   - **Patient Initials:** `TST` (for test)
   - **Estimated LOS:** `20`
   - **Current Census:** `85%`

### 3.3 Upload Test Document

1. Under **"Discharge Summary"**, click **"Choose File"**
2. Upload one of these test documents from your local machine:
   - `demo_documents/discharge_summary_hip_fracture.txt`
   - Or any PDF/Word document you have

3. Click **"Analyze Admission"**

### 3.4 Verify Upload Success

**Expected behavior:**
- ✅ Processing spinner appears (may take 30-60 seconds for Azure OpenAI extraction)
- ✅ Redirects to admission details page
- ✅ Shows margin score and recommendation
- ✅ Green success message: "Admission analysis complete!"

**If upload fails:**
- ❌ "Failed to upload to Azure Blob Storage" → Check Azure credentials
- ❌ "Failed to extract clinical data" → Check `AZURE_OPENAI_API_KEY`
- ❌ Timeout after 30 seconds → Normal for first request, try again

### 3.5 Verify File in Azure Portal

1. Go to: https://portal.azure.com
2. Navigate to: **Storage accounts** → **admissionsgenie80834**
3. Click: **Containers** → **admissions-genie-uploads**
4. You should see uploaded file with timestamp: `20251106_HHMMSS_filename.ext`

**What this proves:**
- ✅ File upload to Azure Blob Storage works
- ✅ AES-256 encryption is applied (automatic)
- ✅ File naming and timestamping works
- ✅ Database stores `azure://` URI correctly

---

## Step 4: Test Session Timeout (15 minutes)

This verifies HIPAA-compliant session security.

### 4.1 Set Up Test (Optional: Speed Up)

**To test faster (1 minute timeout instead of 15):**

1. Go to Render dashboard → Environment
2. Temporarily change: `SESSION_TIMEOUT_MINUTES=1`
3. Click "Save Changes" (triggers 5-min redeploy)
4. Wait for "Live" status

### 4.2 Test Session Expiration

1. Log in to your app
2. Navigate around (view admissions, dashboard, etc.)
3. **Stop clicking** and wait:
   - With 1-minute timeout: Wait 61 seconds
   - With 15-minute timeout: Wait 16 minutes
4. Try to click any link or button

**Expected behavior:**
- ✅ Redirected to login page
- ✅ Flash message: "Your session has expired. Please log in again."
- ✅ Cannot access protected pages without re-login

**If session timeout doesn't work:**
- Clear browser cookies and try again
- Check Render logs for session middleware errors
- Verify `SESSION_COOKIE_SECURE=true` is set

### 4.3 Restore Production Timeout

If you changed it to 1 minute for testing:

1. Go to Render → Environment
2. Change back to: `SESSION_TIMEOUT_MINUTES=15`
3. Click "Save Changes"

---

## Step 5: Test Database Persistence (2 minutes)

This verifies PostgreSQL is storing data correctly.

### 5.1 Create Multiple Admissions

1. Create 2-3 test admissions with different:
   - Facilities
   - Payers
   - Patient initials

2. Log out and log back in

### 5.2 Verify Data Persists

1. Go to **Dashboard** → Should show recent admissions
2. Click **"Admission History"** → All test admissions should appear
3. Click on each admission → Details should load correctly

**What this proves:**
- ✅ PostgreSQL database is working
- ✅ Data persists across sessions
- ✅ Relationships between tables work (admissions, facilities, payers)

---

## Step 6: Test Error Handling (3 minutes)

This verifies the app handles errors gracefully.

### 6.1 Test Invalid File Upload

1. Try to create admission without uploading any files
2. **Expected:** Red error message about required documents

### 6.2 Test Invalid Patient Data

1. Try to create admission with empty patient initials
2. **Expected:** Form validation error

### 6.3 Test 404 Handling

1. Navigate to: `https://YOUR-APP-URL.onrender.com/nonexistent-page`
2. **Expected:** Custom 404 error page (not ugly default error)

---

## Step 7: Production Checklist

Mark each item as complete:

### Security ✅
- [ ] HTTPS enforced (check URL starts with `https://`)
- [ ] Session timeout working (15 minutes)
- [ ] PHI strict mode enabled (`PHI_STRICT_MODE=true`)
- [ ] Secure cookies enabled (`SESSION_COOKIE_SECURE=true`)
- [ ] Azure Blob Storage encryption (automatic AES-256)

### Infrastructure ✅
- [ ] PostgreSQL database connected and working
- [ ] Azure Blob Storage configured and tested
- [ ] Azure OpenAI document extraction working
- [ ] Health endpoint returns "healthy"
- [ ] Audit logging working (check database `audit_log` table)

### Functionality ✅
- [ ] User login/logout works
- [ ] Create admission with file upload works
- [ ] View admission details works
- [ ] Record decision on admission works
- [ ] Dashboard shows recent admissions
- [ ] Admin panel accessible (for admin users)

### Performance ✅
- [ ] Page loads in < 3 seconds
- [ ] File upload completes in < 60 seconds
- [ ] Azure OpenAI extraction completes in < 30 seconds
- [ ] No console errors in browser dev tools

### Monitoring ✅
- [ ] Render logs show application startup messages
- [ ] Health endpoint accessible for monitoring
- [ ] No error spikes in Render logs
- [ ] Database connections not maxing out

---

## Common Issues and Solutions

### Issue: "502 Bad Gateway"
**Cause:** App is still deploying or crashed
**Fix:**
1. Check Render logs for startup errors
2. Wait 2-3 minutes for full deployment
3. Check database connection string is correct

### Issue: "Failed to upload to Azure Blob Storage"
**Cause:** Azure credentials incorrect
**Fix:**
1. Verify `AZURE_STORAGE_ACCOUNT_NAME=admissionsgenie80834`
2. Verify `AZURE_STORAGE_ACCOUNT_KEY` has no extra spaces
3. Try regenerating key in Azure Portal → Storage account → Access keys

### Issue: "Failed to extract clinical data from documents"
**Cause:** Azure OpenAI not configured
**Fix:**
1. Check `AZURE_OPENAI_API_KEY` is set
2. Check `AZURE_OPENAI_ENDPOINT` is correct
3. Check `AZURE_OPENAI_DEPLOYMENT` matches your deployment name
4. Verify OpenAI deployment is active in Azure Portal

### Issue: Session timeout not working
**Cause:** Cookie settings or browser cache
**Fix:**
1. Clear browser cookies completely
2. Verify `SESSION_COOKIE_SECURE=true` is set
3. Check Render logs for session middleware errors
4. Try in incognito/private browsing mode

### Issue: Files uploading but OpenAI extraction timing out
**Cause:** Cold start or OpenAI quota
**Fix:**
1. First request after deploy can take 30-60 seconds (normal)
2. Check Azure OpenAI quota hasn't been exceeded
3. Try uploading simpler text file first
4. Check Render logs for detailed error messages

---

## Production Ready Criteria

Your app is **production-ready** when all of these are true:

✅ **All environment variables set** (7 total)
✅ **Health endpoint returns "healthy"**
✅ **File upload to Azure works**
✅ **Files visible in Azure Portal**
✅ **Session timeout works (15 minutes)**
✅ **Database persists data across sessions**
✅ **No errors in Render logs**
✅ **HTTPS enforced**

---

## Optional Enhancements

These are **NOT required** for production, but nice to have:

### Redis + Celery (Async Processing)
- **Time:** 25 minutes
- **Cost:** $10/month
- **Benefit:** Background document processing, better UX
- **Guide:** See `COPY_PASTE_SETUP.md` section "Optional: Add Redis + Celery"

### Sentry (Error Tracking)
- **Time:** 10 minutes
- **Cost:** FREE
- **Benefit:** Real-time error notifications and debugging
- **Guide:** See `COPY_PASTE_SETUP.md` section "Optional: Add Sentry"

### Backups
- **Time:** 5 minutes
- **Cost:** FREE (Render includes daily backups)
- **Setup:**
  1. Render dashboard → Your PostgreSQL database
  2. Click "Backups" tab
  3. Verify daily backups are enabled (default)

---

## Next Steps After Verification

Once all tests pass:

1. **Document your production URL** for your team
2. **Change default admin password** in production:
   - Log in as `admin@admissionsgenie.com`
   - Go to Profile → Change Password
   - Use strong password (16+ characters)
3. **Create real user accounts** for your staff
4. **Load real facility/payer/rate data** via admin panel
5. **Train staff** on how to use the system
6. **Monitor Render logs** for first few days

---

## Cost Summary

**Current production costs:**

| Service | Cost/Month | Required |
|---------|------------|----------|
| Render (Starter plan) | $7 | ✅ Yes |
| PostgreSQL (Render) | $7 | ✅ Yes |
| Azure OpenAI | $50-100 | ✅ Yes |
| Azure Blob Storage | $1-2 | ✅ Yes |
| **Total** | **$65-116** | - |

**Optional add-ons:**

| Service | Cost/Month | Benefit |
|---------|------------|---------|
| Redis (Upstash via Render) | $10 | Async processing |
| Celery Worker (Render) | FREE | Background tasks |
| Sentry Error Tracking | FREE | Real-time error alerts |

---

## Support and Troubleshooting

- **Render Docs:** https://render.com/docs
- **Azure Docs:** https://docs.microsoft.com/azure/storage/blobs/
- **Project Documentation:** See `README.md`, `AZURE_SETUP.md`, `COPY_PASTE_SETUP.md`

**For help:**
- Check Render logs first (most errors show here)
- Review this verification checklist
- Check Azure Portal for storage/OpenAI status

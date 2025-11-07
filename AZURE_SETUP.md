# Azure Blob Storage Setup (10 minutes)

**Why Azure Instead of AWS:**
Since you already have Azure credentials for OpenAI, using Azure Blob Storage is faster and keeps everything in one cloud provider!

**Time:** 10 minutes
**Cost:** ~$1-2/month

---

## Quick Setup

### Option A: Azure CLI (Fastest - 5 minutes)

If you have Azure CLI installed, run these commands:

```bash
# Login to Azure
az login

# Create storage account
STORAGE_ACCOUNT="admsgen$(date +%s)"  # Must be globally unique, lowercase only
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group YOUR_RESOURCE_GROUP \
  --location eastus \
  --sku Standard_LRS \
  --encryption-services blob \
  --https-only true

# Create container
az storage container create \
  --name admissions-genie-uploads \
  --account-name $STORAGE_ACCOUNT \
  --public-access off

# Get access key
ACCESS_KEY=$(az storage account keys list \
  --resource-group YOUR_RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query '[0].value' -o tsv)

# Print configuration
echo "=== ADD THESE TO RENDER ==="
echo "USE_AZURE=true"
echo "AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT"
echo "AZURE_STORAGE_ACCOUNT_KEY=$ACCESS_KEY"
echo "AZURE_STORAGE_CONTAINER_NAME=admissions-genie-uploads"
echo "==========================="
```

Replace `YOUR_RESOURCE_GROUP` with your existing Azure resource group name (same one you use for OpenAI).

---

### Option B: Azure Portal (10 minutes)

#### Step 1: Create Storage Account (5 min)

1. Go to: https://portal.azure.com
2. Click **"Create a resource"** → Search for **"Storage account"**
3. Click **"Create"**
4. Fill in:
   - **Resource group:** Use your existing one (same as Azure OpenAI)
   - **Storage account name:** `admissionsgenie` + random numbers (e.g., `admissionsgenie12345`)
     - Must be globally unique
     - Only lowercase letters and numbers
     - 3-24 characters
   - **Region:** East US (or same as your OpenAI)
   - **Performance:** Standard
   - **Redundancy:** Locally-redundant storage (LRS)
5. Click **"Review + create"** → **"Create"**
6. Wait 1-2 minutes for deployment

#### Step 2: Create Container (2 min)

1. Once deployed, click **"Go to resource"**
2. In left menu, click **"Containers"**
3. Click **"+ Container"**
4. **Name:** `admissions-genie-uploads`
5. **Public access level:** Private (no anonymous access)
6. Click **"Create"**

#### Step 3: Get Access Key (3 min)

1. In left menu, click **"Access keys"**
2. Under **key1**, click **"Show"** next to **Key**
3. **Copy these values:**
   - **Storage account name:** (at the top of the page)
   - **Key:** (the long string under key1)

---

## Configure Render

Go to Render dashboard → Your web service → Environment tab → Add these:

```bash
# Azure Blob Storage (instead of AWS S3)
USE_AZURE=true
AZURE_STORAGE_ACCOUNT_NAME=<your storage account name>
AZURE_STORAGE_ACCOUNT_KEY=<your key from step 3>
AZURE_STORAGE_CONTAINER_NAME=admissions-genie-uploads

# Security (still required)
SESSION_TIMEOUT_MINUTES=15
SESSION_COOKIE_SECURE=true
PHI_STRICT_MODE=true
```

**Important:** DO NOT set `USE_S3=true` - use either Azure OR S3, not both!

Click **"Save Changes"** - Render will redeploy automatically (5-10 minutes).

---

## Verify It Works

### 1. Check Health Endpoint

```bash
curl https://YOUR-APP.onrender.com/health/detailed
```

Look for:
```json
{
  "azure_blob": {
    "status": "configured",
    "account": "your-storage-account"
  }
}
```

### 2. Test File Upload

1. Log in to your app
2. Create new admission
3. Upload a test document
4. Go to Azure Portal → Your storage account → Containers → admissions-genie-uploads
5. You should see the uploaded file!

---

## Cost Breakdown

### Azure Blob Storage

| Item | Cost |
|------|------|
| Storage | $0.018/GB/month |
| Transactions | $0.05 per 10,000 operations |
| **Typical usage** | **$1-2/month** |

For 1GB of documents and 1,000 uploads/month = ~$1.50/month

### vs AWS S3

Azure is actually **slightly cheaper** than S3:
- Azure: $0.018/GB/month
- S3: $0.023/GB/month

---

## Advantages of Azure

✅ **Single Cloud Provider** - Everything in Azure (OpenAI + Storage)
✅ **Same Credentials** - Use existing Azure subscription
✅ **Same Region** - Co-locate storage with OpenAI for faster processing
✅ **Automatic Encryption** - AES-256 enabled by default
✅ **Slightly Cheaper** - $0.005/GB less than S3

---

## What Gets Encrypted

Azure automatically encrypts everything:
- ✅ Data at rest (AES-256)
- ✅ Data in transit (HTTPS/TLS 1.2+)
- ✅ Automatic key rotation
- ✅ HIPAA compliant

No extra configuration needed!

---

## Troubleshooting

### "Storage account name is not available"
- Try adding random numbers: `admissionsgenie12345`
- Must be globally unique
- Only lowercase letters and numbers

### "Upload failed: Authentication error"
- Verify storage account name is correct
- Verify access key was copied completely (very long string)
- Try regenerating key in Azure Portal

### "Container not found"
- Verify container name is exactly: `admissions-genie-uploads`
- Check container was created in the storage account

---

## Next Steps

After Azure Blob Storage is working:

1. ✅ Test file upload and retrieval
2. ✅ Verify files appear in Azure Portal
3. ✅ Check encryption is enabled (it is by default)
4. Optional: Add Redis for async processing
5. Optional: Add Sentry for error tracking

---

## Support

- **Azure Docs:** https://docs.microsoft.com/en-us/azure/storage/blobs/
- **Troubleshooting:** Check Render logs for detailed error messages
- **Contact:** jthayer@verisightanalytics.com

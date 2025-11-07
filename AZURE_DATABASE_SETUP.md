# Azure Database for PostgreSQL Setup

**Time:** 10-15 minutes
**Cost:** ~$5-15/month (Basic tier)
**Why:** Keep everything in Azure (OpenAI + Blob Storage + Database)

---

## Quick Setup via Azure CLI (Fastest)

Copy and paste this entire block into Azure Cloud Shell:

```bash
# Set variables
RESOURCE_GROUP="<YOUR_RESOURCE_GROUP>"  # Same one you used for storage
DB_SERVER_NAME="admissionsgenie-db-$(date +%s)"  # Unique name
ADMIN_USER="admissionsgenie_admin"
ADMIN_PASSWORD="$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)"  # Random secure password
DB_NAME="admissions_genie"

# Create PostgreSQL server (Basic tier, cost-effective)
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --location eastus \
  --admin-user $ADMIN_USER \
  --admin-password $ADMIN_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 14 \
  --public-access 0.0.0.0-255.255.255.255

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --database-name $DB_NAME

# Print connection details
echo ""
echo "=================================="
echo "Azure PostgreSQL Created!"
echo "=================================="
echo "Server: ${DB_SERVER_NAME}.postgres.database.azure.com"
echo "Database: $DB_NAME"
echo "Admin User: $ADMIN_USER"
echo "Admin Password: $ADMIN_PASSWORD"
echo ""
echo "=== DATABASE_URL FOR RENDER ==="
echo "postgresql://${ADMIN_USER}:${ADMIN_PASSWORD}@${DB_SERVER_NAME}.postgres.database.azure.com:5432/${DB_NAME}?sslmode=require"
echo "=================================="
echo ""
echo "IMPORTANT: Save the password above - you won't see it again!"
```

**IMPORTANT:** Replace `<YOUR_RESOURCE_GROUP>` with your actual resource group name (same one used for storage).

---

## Alternative: Azure Portal (15 minutes)

If you prefer using the portal:

### Step 1: Create PostgreSQL Server (7 min)

1. Go to: https://portal.azure.com
2. Click **"Create a resource"** → Search **"Azure Database for PostgreSQL"**
3. Select **"Flexible server"** → Click **"Create"**
4. Fill in:
   - **Resource group:** Use existing (same as storage)
   - **Server name:** `admissionsgenie-db-12345` (must be globally unique)
   - **Region:** East US (same as OpenAI and storage)
   - **PostgreSQL version:** 14
   - **Workload type:** Development
   - **Compute + storage:** Click "Configure server"
     - Tier: **Burstable**
     - Compute: **Standard_B1ms** (1 vCore, 2GB RAM) - $12/month
     - Storage: **32 GB**
     - Click **"Save"**
   - **Admin username:** `admissionsgenie_admin`
   - **Password:** Create strong password (save it!)
   - **Confirm password:** Re-enter password

5. Click **"Next: Networking"**
6. **Firewall rules:**
   - Check: **"Allow public access from any Azure service within Azure to this server"**
   - Click **"Add 0.0.0.0 - 255.255.255.255"** (allows Render to connect)

7. Click **"Review + create"** → **"Create"**
8. Wait 5-10 minutes for deployment

### Step 2: Create Database (2 min)

1. Once deployed, click **"Go to resource"**
2. In left menu, click **"Databases"**
3. Click **"+ Add"**
4. **Name:** `admissions_genie`
5. Click **"Save"**

### Step 3: Get Connection String (1 min)

1. In left menu, click **"Connect"**
2. Under **"Connection strings"**, select **"Python (psycopg2)"**
3. You'll see something like:
   ```
   host=admissionsgenie-db-12345.postgres.database.azure.com
   port=5432
   dbname=admissions_genie
   user=admissionsgenie_admin
   password={your_password}
   sslmode=require
   ```

4. **Convert to DATABASE_URL format:**
   ```
   postgresql://admissionsgenie_admin:{your_password}@admissionsgenie-db-12345.postgres.database.azure.com:5432/admissions_genie?sslmode=require
   ```

   Replace `{your_password}` with your actual password.

---

## Add to Render

Once you have your Azure PostgreSQL connection string:

1. Go to Render dashboard → Your web service
2. Click **"Environment"** tab
3. Add (or update if exists):
   - **Key:** `DATABASE_URL`
   - **Value:** `postgresql://admissionsgenie_admin:PASSWORD@admissionsgenie-db-XXXXX.postgres.database.azure.com:5432/admissions_genie?sslmode=require`

4. Verify these 7 variables are also there:
   ```
   USE_AZURE=true
   AZURE_STORAGE_ACCOUNT_NAME=admissionsgenie80834
   AZURE_STORAGE_ACCOUNT_KEY=zAN/HBHKKv1l...
   AZURE_STORAGE_CONTAINER_NAME=admissions-genie-uploads
   SESSION_TIMEOUT_MINUTES=15
   SESSION_COOKIE_SECURE=true
   PHI_STRICT_MODE=true
   ```

5. Click **"Save Changes"**

6. Click **"Manual Deploy"** → **"Clear build cache & deploy"**

7. Wait 8-10 minutes

---

## Verify It Works

Once deployment completes:

```bash
curl https://admissions-genie.onrender.com/health/detailed | grep "postgresql"
```

**Expected:**
```json
"database": {
  "status": "healthy",
  "type": "postgresql"
}
```

---

## Cost Comparison

### Azure PostgreSQL Flexible Server
| Tier | vCores | RAM | Storage | Cost/Month |
|------|--------|-----|---------|------------|
| Burstable B1ms | 1 | 2 GB | 32 GB | ~$12 |
| General Purpose D2s_v3 | 2 | 8 GB | 128 GB | ~$140 |

**Recommended for production:** Burstable B1ms ($12/month)

### Render PostgreSQL
| Plan | Storage | Cost/Month |
|------|---------|------------|
| Starter | 1 GB | $7 |
| Standard | 10 GB | $20 |

**Key Difference:**
- **Azure:** More storage (32GB vs 1GB), better for growth
- **Render:** Cheaper for minimal storage needs
- **Azure:** Better if you want everything in one cloud provider

---

## Total Azure Stack Cost

If you use Azure for everything:

| Service | Cost/Month |
|---------|------------|
| Azure OpenAI | $50-100 |
| Azure Blob Storage | $1-2 |
| Azure PostgreSQL (B1ms) | $12 |
| Render Web Service | $7 |
| **Total** | **$70-121** |

vs. Render PostgreSQL:

| Service | Cost/Month |
|---------|------------|
| Azure OpenAI | $50-100 |
| Azure Blob Storage | $1-2 |
| Render PostgreSQL | $7 |
| Render Web Service | $7 |
| **Total** | **$65-116** |

**Azure is ~$5 more/month but gives you:**
- ✅ Everything in one cloud provider (easier management)
- ✅ More storage (32GB vs 1GB)
- ✅ Better performance (2GB RAM vs 256MB)
- ✅ Co-located with OpenAI and Blob Storage (faster)

---

## Security Features

Azure PostgreSQL Flexible Server includes:

- ✅ SSL/TLS encryption in transit (required)
- ✅ Encryption at rest (automatic AES-256)
- ✅ Private networking support (optional)
- ✅ Firewall rules
- ✅ Automated backups (7-35 days retention)
- ✅ Point-in-time restore

---

## Troubleshooting

### "Cannot connect to database"
**Fix:**
1. Verify firewall rules allow 0.0.0.0-255.255.255.255
2. Check connection string includes `?sslmode=require`
3. Verify admin password is correct

### "SSL connection required"
**Fix:** Add `?sslmode=require` to end of DATABASE_URL

### "Database does not exist"
**Fix:**
1. Go to Azure Portal → Your PostgreSQL server
2. Click "Databases" → Verify `admissions_genie` exists
3. If not, create it

---

## Next Steps

After Azure PostgreSQL is connected:

1. ✅ Verify health endpoint shows PostgreSQL
2. ✅ Test login and user creation
3. ✅ Test file upload to Azure Blob Storage
4. ✅ Create test admission
5. ✅ Verify data persists in Azure database

---

## Recommendation

**For you, I recommend Azure PostgreSQL because:**

1. You already have Azure Cloud Shell set up
2. You're using Azure OpenAI and Blob Storage
3. Single cloud provider = simpler management
4. Better performance and storage for only $5/month more
5. Co-location = faster database queries

**Run the Azure CLI commands above and you'll have everything in Azure!**

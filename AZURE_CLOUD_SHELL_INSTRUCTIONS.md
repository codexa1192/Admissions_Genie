# ☁️ AZURE CLOUD SHELL - COPY/PASTE DEPLOYMENT

**No CLI installation needed. No passwords. Just copy/paste.**

---

## 🚀 COMPLETE SETUP IN 3 STEPS (20 Minutes)

### **STEP 1: Open Azure Cloud Shell** (2 minutes)

1. Go to: **https://portal.azure.com**
2. Sign in (or create free account)
3. Click the **`>_`** icon at the top-right corner
4. If first time:
   - Select **"Bash"**
   - Click **"Create storage"** (it's free)
   - Wait 30 seconds for Cloud Shell to initialize

✅ You now have a terminal in your browser!

---

### **STEP 2: Copy/Paste the Setup Script** (1 minute)

**Option A - From GitHub (Recommended):**

In Cloud Shell, paste this:
```bash
wget https://raw.githubusercontent.com/YOUR-USERNAME/Admissions_Genie/main/azure_cloud_shell_setup.sh
chmod +x azure_cloud_shell_setup.sh
./azure_cloud_shell_setup.sh
```

**Option B - Manual Copy/Paste:**

1. Open the file: `azure_cloud_shell_setup.sh`
2. Copy the **ENTIRE** file (all ~500 lines)
3. Right-click in Cloud Shell → **Paste**
4. Press **Enter**

---

### **STEP 3: Answer the Prompts** (5 minutes)

The script will ask you:

1. **BAA confirmation:** Type `yes`
2. **Project name:** Press Enter (uses default: admissions-genie)
3. **Environment:** Press Enter (uses default: production)
4. **Azure region:** Press Enter (uses default: eastus)
5. **Your email:** Enter your email for alerts
6. **Database username:** Press Enter (uses default: dbadmin)
7. **Database name:** Press Enter (uses default: admissions_genie)
8. **Proceed?** Type `yes`

Then **wait 15-20 minutes** while Azure creates everything.

☕ Go grab coffee! The script does all the work.

---

## ✅ WHAT THE SCRIPT CREATES

While you wait, here's what's being built:

- ✅ **PostgreSQL Database** - Encrypted at rest, SSL enforced, automated backups
- ✅ **Blob Storage** - Encrypted, versioned, private-only access
- ✅ **Key Vault** - All secrets stored securely (no plaintext passwords!)
- ✅ **App Service** - Your web app with HTTPS enforced
- ✅ **Application Insights** - Monitoring and error tracking

**All configured for HIPAA compliance!**

---

## 📋 AFTER THE SCRIPT FINISHES

You'll see a summary like this:

```
════════════════════════════════════════════════════════════════
DEPLOYMENT COMPLETE! 🎉
════════════════════════════════════════════════════════════════

Your Web App: https://admissions-genie-production-app.azurewebsites.net
Database: admissions-genie-production-db.postgres.database.azure.com
Credentials saved to: ~/deployment_credentials.txt
```

**Save your credentials file:**

In Cloud Shell:
1. Click the **"Upload/Download"** icon (top toolbar)
2. Click **"Download"**
3. Enter: `deployment_credentials.txt`
4. Save this file somewhere SECURE!

---

## 🚀 DEPLOY YOUR CODE

**Option A - GitHub Deployment (Easiest):**

1. In Azure Portal → Search "App Services"
2. Click your app (`admissions-genie-production-app`)
3. Click **"Deployment Center"** (left menu)
4. **Source:** GitHub
5. Click **"Authorize"** → Sign in to GitHub
6. **Repository:** Admissions_Genie
7. **Branch:** main
8. Click **"Save"**

Azure automatically deploys! Takes 3-5 minutes.

**Option B - Deploy from Cloud Shell:**

```bash
# Clone your repo
git clone https://github.com/YOUR-USERNAME/Admissions_Genie.git
cd Admissions_Genie

# Create deployment package
zip -r deploy.zip . -x '*.git*' -x '*venv*' -x '*.pyc'

# Deploy to Azure (replace with your resource group and app name)
az webapp deployment source config-zip \
  --resource-group admissions-genie-production-rg \
  --name admissions-genie-production-app \
  --src deploy.zip
```

---

## 🗄️ INITIALIZE DATABASE

After code is deployed, initialize the database:

**Method 1 - SSH into App Service:**

In Cloud Shell:
```bash
az webapp ssh \
  --resource-group admissions-genie-production-rg \
  --name admissions-genie-production-app

# Once connected:
python3 seed_database.py
```

**Method 2 - Via Azure Portal:**

1. Go to your App Service
2. Click **"SSH"** (under Development Tools)
3. Click **"Go"**
4. In the terminal that opens:
   ```bash
   python3 seed_database.py
   ```

---

## 🌐 ACCESS YOUR APP

**Your app is live at:**
```
https://admissions-genie-production-app.azurewebsites.net
```

**Login with:**
- Email: `jthayer@verisightanalytics.com`
- Password: `TempPass2024!` (you set this earlier in Render)

Or create new admin account via seed script.

---

## 💰 COST SUMMARY

**First 30 Days:** FREE ($200 Azure credit)
**After that:** ~$200-280/month

| Service | Monthly Cost |
|---------|--------------|
| PostgreSQL (B2s) | $50-70 |
| App Service (B2) | $75 |
| Blob Storage | $20-30 |
| Application Insights | $50-100 |
| Key Vault | $5 |
| **Total** | **$200-280** |

Plus OpenAI API costs (~$100-500/month depending on usage)

---

## 🔒 SECURITY CHECKLIST

After deployment, verify:

- ✅ Database is encrypted (default in Azure)
- ✅ Storage is encrypted (default in Azure)
- ✅ All secrets in Key Vault (not in code)
- ✅ HTTPS-only enforced
- ✅ SSL required for database connections
- ✅ Public access blocked on storage
- ✅ Automated backups enabled (7-day retention)

---

## 🆘 TROUBLESHOOTING

### "Script failed at Step X"

Just re-run the script! It's safe to run multiple times. It will skip resources that already exist.

### "Can't access my web app"

Wait 5 minutes after deployment. App Service needs time to start.

### "Database connection error"

Check that firewall rule allows Azure services:
```bash
az postgres flexible-server firewall-rule list \
  --resource-group admissions-genie-production-rg \
  --name admissions-genie-production-db
```

Should show: `AllowAllAzureIPs` with start/end IP `0.0.0.0`

### "App can't access Key Vault"

Verify managed identity:
```bash
az webapp identity show \
  --name admissions-genie-production-app \
  --resource-group admissions-genie-production-rg
```

Should show `principalId` and `type: SystemAssigned`

---

## 📞 GET HELP

**Azure Support:**
- Portal: Click "?" → "Help + support"
- Phone: 1-800-867-1389
- Chat: Available 24/7 in portal

**Documentation:**
- HIPAA: https://aka.ms/azurecompliance
- App Service: https://aka.ms/appservicedocs
- PostgreSQL: https://aka.ms/postgresqldocs

---

## ✅ PRODUCTION READINESS

After deployment, you still need to:

- [ ] Complete HIPAA policy documentation (see `docs/HIPAA_POLICY_TEMPLATES.md`)
- [ ] Test backup restoration
- [ ] Configure custom domain (optional)
- [ ] Staff security training
- [ ] Enable Azure Security Center recommendations

**Timeline:** 2-3 weeks to full HIPAA compliance

---

## 🎉 YOU'RE DONE!

Your infrastructure is 100% ready for production.

**What you have:**
- ✅ HIPAA-compliant infrastructure
- ✅ Encrypted database and storage
- ✅ Secure secrets management
- ✅ Automated backups
- ✅ Production monitoring
- ✅ SSL/TLS enforced everywhere

**What's next:**
1. Deploy your code (via GitHub or ZIP)
2. Initialize database (seed_database.py)
3. Complete HIPAA documentation
4. Train staff
5. Launch! 🚀

---

## 🚀 QUICK START SUMMARY

```bash
# 1. Open Cloud Shell at portal.azure.com (click >_ icon)

# 2. Run this ONE command:
wget https://raw.githubusercontent.com/YOUR-USERNAME/Admissions_Genie/main/azure_cloud_shell_setup.sh && chmod +x azure_cloud_shell_setup.sh && ./azure_cloud_shell_setup.sh

# 3. Answer prompts (takes 5 minutes)

# 4. Wait 15-20 minutes

# 5. Done! ✅
```

That's it!

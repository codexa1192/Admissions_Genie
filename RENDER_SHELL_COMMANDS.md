# Render Shell Diagnostic Commands

## Quick Environment Check

Run this single command in your Render Shell to verify everything:

```bash
python3 verify_production.py
```

This will check:
- ✅ Python dependencies installed
- ✅ PostgreSQL driver (psycopg2)
- ✅ Azure Blob Storage SDK
- ✅ All environment variables
- ✅ Database configuration
- ✅ Security settings

---

## Manual Check (if verify_production.py doesn't exist)

Run these commands one by one:

### 1. Check Python Dependencies

```bash
python3 -c "
try:
    import psycopg2
    print('✅ psycopg2: INSTALLED')
except ImportError:
    print('❌ psycopg2: NOT INSTALLED')

try:
    from azure.storage.blob import BlobServiceClient
    print('✅ azure-storage-blob: INSTALLED')
except ImportError:
    print('❌ azure-storage-blob: NOT INSTALLED')

try:
    import openai
    print('✅ openai: INSTALLED')
except ImportError:
    print('❌ openai: NOT INSTALLED')
"
```

### 2. Check Environment Variables (Safe - No Secrets Shown)

```bash
python3 -c "
import os

def check(name):
    val = os.getenv(name)
    if val:
        if len(val) > 10:
            print(f'✅ {name}: SET ({val[:4]}...)')
        else:
            print(f'✅ {name}: SET')
    else:
        print(f'❌ {name}: NOT SET')

print('DATABASE:')
check('DATABASE_URL')

print('\nAZURE STORAGE:')
check('USE_AZURE')
check('AZURE_STORAGE_ACCOUNT_NAME')
check('AZURE_STORAGE_ACCOUNT_KEY')
check('AZURE_STORAGE_CONTAINER_NAME')

print('\nAZURE OPENAI:')
check('AZURE_OPENAI_API_KEY')
check('AZURE_OPENAI_ENDPOINT')
check('AZURE_OPENAI_DEPLOYMENT')

print('\nSECURITY:')
check('SESSION_TIMEOUT_MINUTES')
check('SESSION_COOKIE_SECURE')
check('PHI_STRICT_MODE')
"
```

### 3. Test Database Connection

```bash
python3 -c "
import os
db_url = os.getenv('DATABASE_URL', '')

if not db_url:
    print('❌ DATABASE_URL not set')
elif db_url.startswith('sqlite://'):
    print('⚠️  Using SQLite (development mode)')
elif db_url.startswith('postgresql://'):
    print('✅ PostgreSQL configured')
    # Try to connect
    try:
        import psycopg2
        # Extract connection parts
        parts = db_url.split('://', 1)[1]
        print(f'   Server: {parts.split(\"@\")[1].split(\"/\")[0]}')
        print('   Attempting connection...')

        conn = psycopg2.connect(db_url)
        print('   ✅ Connection successful!')
        conn.close()
    except ImportError:
        print('   ❌ psycopg2 not installed')
    except Exception as e:
        print(f'   ❌ Connection failed: {str(e)[:100]}')
else:
    print(f'❌ Unknown database type: {db_url[:20]}...')
"
```

### 4. Test Azure Blob Storage Connection

```bash
python3 -c "
import os

use_azure = os.getenv('USE_AZURE', 'false').lower() == 'true'
account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
container = os.getenv('AZURE_STORAGE_CONTAINER_NAME')

if not use_azure:
    print('⚠️  Azure Blob Storage not enabled (USE_AZURE=false)')
elif not all([account_name, account_key, container]):
    print('❌ Azure Blob Storage: Missing configuration')
    if not account_name:
        print('   - AZURE_STORAGE_ACCOUNT_NAME not set')
    if not account_key:
        print('   - AZURE_STORAGE_ACCOUNT_KEY not set')
    if not container:
        print('   - AZURE_STORAGE_CONTAINER_NAME not set')
else:
    print(f'✅ Azure Blob Storage configured')
    print(f'   Account: {account_name}')
    print(f'   Container: {container}')

    try:
        from azure.storage.blob import BlobServiceClient
        print('   Testing connection...')

        blob_service_client = BlobServiceClient(
            account_url=f'https://{account_name}.blob.core.windows.net',
            credential=account_key
        )

        container_client = blob_service_client.get_container_client(container)
        container_client.get_container_properties()

        print('   ✅ Connection successful!')
    except ImportError:
        print('   ❌ azure-storage-blob not installed')
    except Exception as e:
        error_msg = str(e)[:100]
        print(f'   ❌ Connection failed: {error_msg}')
"
```

---

## Expected Output (Production Ready)

If everything is configured correctly, you should see:

```
✅ psycopg2: INSTALLED
✅ azure-storage-blob: INSTALLED
✅ openai: INSTALLED

DATABASE:
✅ DATABASE_URL: SET (post...)

AZURE STORAGE:
✅ USE_AZURE: SET
✅ AZURE_STORAGE_ACCOUNT_NAME: SET (admi...)
✅ AZURE_STORAGE_ACCOUNT_KEY: SET (zAN/...)
✅ AZURE_STORAGE_CONTAINER_NAME: SET (admi...)

AZURE OPENAI:
✅ AZURE_OPENAI_API_KEY: SET (sk-p...)
✅ AZURE_OPENAI_ENDPOINT: SET (http...)
✅ AZURE_OPENAI_DEPLOYMENT: SET (gpt-...)

SECURITY:
✅ SESSION_TIMEOUT_MINUTES: SET (15)
✅ SESSION_COOKIE_SECURE: SET (true)
✅ PHI_STRICT_MODE: SET (true)

PostgreSQL configured
   Server: admissionsgenie-db-XXXXX.postgres.database.azure.com:5432
   Attempting connection...
   ✅ Connection successful!

✅ Azure Blob Storage configured
   Account: admissionsgenie80834
   Container: admissions-genie-uploads
   Testing connection...
   ✅ Connection successful!
```

---

## Common Issues and Fixes

### Issue 1: psycopg2 not installed

**Cause:** Build cache using old requirements.txt

**Fix:**
1. Render dashboard → Your web service
2. Click "Manual Deploy" → "Clear build cache & deploy"
3. Wait 8-10 minutes

### Issue 2: Environment variables not set

**Cause:** Variables weren't saved in Render

**Fix:**
1. Render dashboard → Environment tab
2. Verify all variables are listed
3. If missing, add them
4. Click "Save Changes"

### Issue 3: Database connection fails

**Possible causes:**
- DATABASE_URL has wrong format
- PostgreSQL server not allowing connections
- Firewall rules in Azure

**Fix:**
1. Check DATABASE_URL format: `postgresql://user:pass@host:5432/dbname?sslmode=require`
2. Verify Azure PostgreSQL firewall allows 0.0.0.0-255.255.255.255
3. Test connection from Azure Portal

### Issue 4: Azure Blob Storage connection fails

**Possible causes:**
- Wrong account key
- Container doesn't exist
- Typo in account name

**Fix:**
1. Go to Azure Portal → Storage account
2. Click "Access keys" → Copy key1 again
3. Update AZURE_STORAGE_ACCOUNT_KEY in Render
4. Verify container "admissions-genie-uploads" exists

---

## After Running Diagnostics

1. **If all ✅ green checks:** Your app is production ready!

2. **If you see ❌ red errors:**
   - Fix the issues listed
   - Run "Clear build cache & deploy" in Render
   - Wait 8-10 minutes
   - Run diagnostics again

3. **Contact me with:**
   - Copy the full output (it's safe - no secrets shown)
   - I'll tell you exactly what to fix

# Multi-Tenant Deployment Instructions

## Overview
This guide provides exact commands to deploy the multi-tenant version of Admissions Genie to production (Render or Azure).

---

## Prerequisites

1. **Database Location:** Your PostgreSQL database is on:
   - **Render:** If you're using Render's managed PostgreSQL
   - **Azure:** If you're using Azure Database for PostgreSQL

2. **Required Environment Variables:**
   ```bash
   DATABASE_URL=postgresql://user:password@host:port/database
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo
   SECRET_KEY=your-secret-key
   FLASK_ENV=production
   PORT=8080
   ```

---

## Deployment Steps

### Step 1: Connect to Your Database

#### If using Render PostgreSQL:
```bash
# In Render Dashboard:
# 1. Go to your PostgreSQL database
# 2. Click "Connect" → "External Connection"
# 3. Copy the PSQL Command, it looks like:
psql postgresql://username:password@hostname.region.render.com/database_name
```

#### If using Azure PostgreSQL:
```bash
# In Azure Portal:
# 1. Go to your PostgreSQL server
# 2. Click "Connection strings"
# 3. Copy the psql command, it looks like:
psql "host=yourserver.postgres.database.azure.com port=5432 dbname=admissions_genie user=yourusername password=yourpassword sslmode=require"
```

### Step 2: Backup Your Database (CRITICAL)

```sql
-- In psql, run:
\! pg_dump $DATABASE_URL > backup_before_multitenant_$(date +%Y%m%d).sql

-- OR from your local terminal:
pg_dump postgresql://user:pass@host:port/db > backup_before_multitenant_$(date +%Y%m%d).sql
```

### Step 3: Run Database Schema Updates

```sql
-- Connect to your database first using the command from Step 1
-- Then run these SQL commands:

-- 1. Add organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    subdomain TEXT UNIQUE NOT NULL,
    subscription_tier TEXT NOT NULL DEFAULT 'trial',
    settings TEXT,
    stripe_customer_id TEXT UNIQUE,
    is_active INTEGER DEFAULT 1,
    trial_ends_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Add organization_id columns to all tables
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE payers ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE rates ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE cost_models ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE business_weights ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE admissions ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id INTEGER;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS organization_id INTEGER;

-- 3. Create indexes for multi-tenant performance
CREATE INDEX IF NOT EXISTS idx_facilities_org ON facilities(organization_id);
CREATE INDEX IF NOT EXISTS idx_payers_org ON payers(organization_id);
CREATE INDEX IF NOT EXISTS idx_rates_org ON rates(organization_id);
CREATE INDEX IF NOT EXISTS idx_cost_models_org ON cost_models(organization_id);
CREATE INDEX IF NOT EXISTS idx_business_weights_org ON business_weights(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_admissions_org_created ON admissions(organization_id, created_at DESC);

-- 4. Create default organization
INSERT INTO organizations (name, subdomain, subscription_tier, settings, is_active, trial_ends_at)
VALUES (
    'Default Organization',
    'default',
    'professional',
    '{"migrated_from_single_tenant": true, "migration_date": "2025-01-01"}',
    1,
    NOW() + INTERVAL '90 days'
) ON CONFLICT (subdomain) DO NOTHING
RETURNING id;

-- NOTE THE ID RETURNED - you'll need it for the next step!
-- Let's say it returns: 1

-- 5. Migrate existing data (replace 1 with your org ID)
UPDATE facilities SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE payers SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE rates SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE cost_models SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE business_weights SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE admissions SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE users SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE audit_logs SET organization_id = 1 WHERE organization_id IS NULL;

-- 6. Verify migration
SELECT 'facilities' as table_name, COUNT(*) as migrated FROM facilities WHERE organization_id IS NOT NULL
UNION ALL
SELECT 'payers', COUNT(*) FROM payers WHERE organization_id IS NOT NULL
UNION ALL
SELECT 'rates', COUNT(*) FROM rates WHERE organization_id IS NOT NULL
UNION ALL
SELECT 'cost_models', COUNT(*) FROM cost_models WHERE organization_id IS NOT NULL
UNION ALL
SELECT 'business_weights', COUNT(*) FROM business_weights WHERE organization_id IS NOT NULL
UNION ALL
SELECT 'admissions', COUNT(*) FROM admissions WHERE organization_id IS NOT NULL
UNION ALL
SELECT 'users', COUNT(*) FROM users WHERE organization_id IS NOT NULL
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs WHERE organization_id IS NOT NULL;

-- 7. Make organization_id NOT NULL (after verifying all data is migrated)
ALTER TABLE facilities ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE payers ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE rates ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE cost_models ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE business_weights ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE admissions ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE audit_logs ALTER COLUMN organization_id SET NOT NULL;

-- 8. Add foreign key constraints
ALTER TABLE facilities ADD CONSTRAINT fk_facilities_org FOREIGN KEY (organization_id) REFERENCES organizations (id);
ALTER TABLE payers ADD CONSTRAINT fk_payers_org FOREIGN KEY (organization_id) REFERENCES organizations (id);
ALTER TABLE rates ADD CONSTRAINT fk_rates_org FOREIGN KEY (organization_id) REFERENCES organizations (id);
ALTER TABLE cost_models ADD CONSTRAINT fk_cost_models_org FOREIGN KEY (organization_id) REFERENCES organizations (id);
ALTER TABLE business_weights ADD CONSTRAINT fk_business_weights_org FOREIGN KEY (organization_id) REFERENCES organizations (id);
ALTER TABLE admissions ADD CONSTRAINT fk_admissions_org FOREIGN KEY (organization_id) REFERENCES organizations (id);
ALTER TABLE users ADD CONSTRAINT fk_users_org FOREIGN KEY (organization_id) REFERENCES organizations (id);
ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_org FOREIGN KEY (organization_id) REFERENCES organizations (id);
```

### Step 4: Deploy Application Code

#### If using Render:
```bash
# Push your code to GitHub (all changes are committed)
git push origin main

# Render will auto-deploy from GitHub
# Monitor deployment in Render Dashboard
```

#### If using Azure App Service:
```bash
# From your local machine, in the project directory:
az login

# Deploy to Azure App Service
az webapp up --name your-app-name --resource-group your-resource-group

# OR if using GitHub Actions, push to main:
git push origin main
```

### Step 5: Verify Deployment

```bash
# Test the application
curl https://your-app-url.onrender.com/health
# OR
curl https://your-app-name.azurewebsites.net/health

# Check logs
# Render: Dashboard → Your Service → Logs
# Azure: Portal → App Service → Log stream
```

### Step 6: Test Multi-Tenant Functionality

```bash
# Login to your application
# Visit: https://your-app-url.com

# Verify:
# 1. Existing users can still login
# 2. Dashboard shows existing admissions
# 3. New admissions can be created
# 4. All data is scoped to organization_id = 1
```

---

## Alternative: Python Migration Script

If you prefer to run the migration from Python rather than SQL:

```bash
# SSH into your Render shell or Azure shell
# Render: Dashboard → Your Service → Shell
# Azure: Use SSH or Kudu console

# Run the migration script
cd /path/to/app
python3 migrations/multi_tenant_migration.py
```

---

## Rollback Plan

If something goes wrong:

```bash
# Connect to database
psql $DATABASE_URL

# Restore from backup
\! psql $DATABASE_URL < backup_before_multitenant_YYYYMMDD.sql

# OR drop the organization_id columns
ALTER TABLE facilities DROP COLUMN IF EXISTS organization_id;
ALTER TABLE payers DROP COLUMN IF EXISTS organization_id;
ALTER TABLE rates DROP COLUMN IF EXISTS organization_id;
ALTER TABLE cost_models DROP COLUMN IF EXISTS organization_id;
ALTER TABLE business_weights DROP COLUMN IF EXISTS organization_id;
ALTER TABLE admissions DROP COLUMN IF EXISTS organization_id;
ALTER TABLE users DROP COLUMN IF EXISTS organization_id;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS organization_id;
DROP TABLE IF EXISTS organizations;
```

---

## Post-Deployment Checklist

- [ ] Verify database migration completed successfully
- [ ] Test user login
- [ ] Test creating new admission
- [ ] Test viewing existing admissions
- [ ] Check application logs for errors
- [ ] Verify all API endpoints work
- [ ] Test with 2-3 real admission workflows
- [ ] Monitor database query performance
- [ ] Check organization_id is present in all queries

---

## Next Steps

After successful deployment:

1. **Create additional organizations** for new SNF customers
2. **Implement organization signup flow** (WP2 from V1 plan)
3. **Add Stripe billing integration** (WP3 from V1 plan)
4. **Monitor usage limits** per organization

---

## Support

If you encounter issues:

1. **Check logs first:**
   - Render: Dashboard → Logs
   - Azure: Portal → Log stream

2. **Verify environment variables:**
   ```bash
   # In Render/Azure shell
   echo $DATABASE_URL
   echo $AZURE_OPENAI_API_KEY
   ```

3. **Test database connection:**
   ```bash
   python3 -c "from config.database import db; print(db.execute_query('SELECT COUNT(*) FROM organizations', fetch='one'))"
   ```

4. **Check migration status:**
   ```sql
   SELECT table_name, COUNT(*) as records_with_org_id
   FROM information_schema.tables
   WHERE table_schema = 'public'
   GROUP BY table_name;
   ```

---

**Estimated Time:** 30-45 minutes
**Risk Level:** Medium (backup created, rollback available)
**Downtime:** 5-10 minutes during migration

#!/bin/bash

#############################################################################
# AZURE PRODUCTION DEPLOYMENT SCRIPT
# Admissions Genie - HIPAA-Compliant SNF Management System
#############################################################################
#
# This script deploys Admissions Genie to Azure with HIPAA-compliant settings:
# - Azure Database for PostgreSQL with encryption at rest
# - Azure Blob Storage with encryption
# - Azure App Service with SSL/TLS
# - Automated encrypted backups
# - Application Insights monitoring
# - Azure Key Vault for secrets
#
# PREREQUISITES:
# 1. Azure CLI installed: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
# 2. Azure subscription created
# 3. BAA signed with Microsoft (via Azure portal or contact sales)
# 4. Azure CLI logged in: az login
#
# USAGE:
#   ./deploy_azure.sh
#
#############################################################################

set -e  # Exit on any error

echo "============================================================================"
echo "  ADMISSIONS GENIE - AZURE HIPAA-COMPLIANT DEPLOYMENT"
echo "============================================================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    echo "❌ ERROR: Azure CLI not found. Install from:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

if ! az account show &> /dev/null; then
    echo "❌ ERROR: Not logged into Azure. Run: az login"
    exit 1
fi

echo "✅ Azure CLI installed and authenticated"
echo ""

# Get Azure account info
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
SUBSCRIPTION_NAME=$(az account show --query name --output tsv)
TENANT_ID=$(az account show --query tenantId --output tsv)

echo "Azure Subscription: $SUBSCRIPTION_NAME"
echo "Subscription ID: $SUBSCRIPTION_ID"
echo "Tenant ID: $TENANT_ID"
echo ""

# Confirm BAA
echo "============================================================================"
echo "  HIPAA BUSINESS ASSOCIATE AGREEMENT (BAA)"
echo "============================================================================"
echo ""
echo "⚠️  CRITICAL: You MUST sign a BAA with Microsoft before storing PHI."
echo ""
echo "To sign BAA with Microsoft Azure:"
echo ""
echo "Option 1 - Enterprise Agreement (EA) customers:"
echo "  1. Contact your Microsoft Account Manager"
echo "  2. Request HIPAA Business Associate Amendment"
echo "  3. Sign via DocuSign (usually 1-2 business days)"
echo ""
echo "Option 2 - Online Services (Pay-as-you-go):"
echo "  1. Go to https://www.microsoft.com/licensing/terms"
echo "  2. Download 'Microsoft Online Services Terms'"
echo "  3. HIPAA BAA is included in Section 4(b)"
echo "  4. By using Azure for HIPAA workloads, you accept the BAA"
echo ""
echo "Option 3 - Azure Portal:"
echo "  1. Log into Azure Portal"
echo "  2. Go to Azure Service Health > Compliance"
echo "  3. Review HIPAA/HITECH compliance documentation"
echo "  4. Contact support to request signed BAA copy"
echo ""
echo "Documentation:"
echo "  https://aka.ms/azurecompliance"
echo "  https://docs.microsoft.com/en-us/azure/compliance/offerings/offering-hipaa-us"
echo ""

read -p "Have you signed the BAA with Microsoft? (yes/no): " BAA_SIGNED

if [ "$BAA_SIGNED" != "yes" ]; then
    echo "❌ Please sign BAA before deploying. Exiting."
    exit 1
fi

echo "✅ BAA confirmed"
echo ""

# Configuration
echo "============================================================================"
echo "  DEPLOYMENT CONFIGURATION"
echo "============================================================================"
echo ""

read -p "Project name [admissions-genie]: " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-admissions-genie}

read -p "Environment [production]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-production}

read -p "Azure region [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "Domain name (e.g., app.yourdomain.com): " DOMAIN_NAME

read -p "Database admin username [dbadmin]: " DB_ADMIN_USER
DB_ADMIN_USER=${DB_ADMIN_USER:-dbadmin}

read -sp "Database admin password (12+ chars): " DB_ADMIN_PASSWORD
echo ""

read -p "Database name [admissions_genie]: " DB_NAME
DB_NAME=${DB_NAME:-admissions_genie}

# Generate encryption key
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Generate Flask secret key
FLASK_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo ""
echo "Configuration:"
echo "  Project: $PROJECT_NAME"
echo "  Environment: $ENVIRONMENT"
echo "  Location: $LOCATION"
echo "  Domain: $DOMAIN_NAME"
echo ""

read -p "Proceed with deployment? (yes/no): " PROCEED
if [ "$PROCEED" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Resource naming
RESOURCE_GROUP="${PROJECT_NAME}-${ENVIRONMENT}-rg"
POSTGRES_SERVER="${PROJECT_NAME}-${ENVIRONMENT}-db"
STORAGE_ACCOUNT="${PROJECT_NAME}${ENVIRONMENT}storage"
APP_SERVICE_PLAN="${PROJECT_NAME}-${ENVIRONMENT}-plan"
WEB_APP="${PROJECT_NAME}-${ENVIRONMENT}-app"
KEY_VAULT="${PROJECT_NAME}-${ENVIRONMENT}-kv"
APP_INSIGHTS="${PROJECT_NAME}-${ENVIRONMENT}-insights"

echo ""
echo "============================================================================"
echo "  STEP 1: CREATE RESOURCE GROUP"
echo "============================================================================"
echo ""

echo "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --tags Environment=$ENVIRONMENT HIPAA=true Project=$PROJECT_NAME

echo "✅ Resource group created"

echo ""
echo "============================================================================"
echo "  STEP 2: CREATE AZURE KEY VAULT FOR SECRETS"
echo "============================================================================"
echo ""

echo "Creating Key Vault: $KEY_VAULT"
az keyvault create \
    --name $KEY_VAULT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --enable-rbac-authorization false \
    --enabled-for-deployment true \
    --enabled-for-template-deployment true \
    --tags Environment=$ENVIRONMENT HIPAA=true

# Get current user object ID for Key Vault permissions
CURRENT_USER_ID=$(az ad signed-in-user show --query id --output tsv)

# Set Key Vault access policy
az keyvault set-policy \
    --name $KEY_VAULT \
    --resource-group $RESOURCE_GROUP \
    --object-id $CURRENT_USER_ID \
    --secret-permissions get list set delete

echo "✅ Key Vault created"

echo ""
echo "============================================================================"
echo "  STEP 3: CREATE AZURE DATABASE FOR POSTGRESQL"
echo "============================================================================"
echo ""

echo "Creating PostgreSQL server: $POSTGRES_SERVER (this may take 5-10 minutes)..."

az postgres flexible-server create \
    --name $POSTGRES_SERVER \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $DB_ADMIN_USER \
    --admin-password "$DB_ADMIN_PASSWORD" \
    --sku-name Standard_B2s \
    --tier Burstable \
    --storage-size 128 \
    --version 15 \
    --high-availability Disabled \
    --zone 1 \
    --backup-retention 7 \
    --geo-redundant-backup Disabled \
    --public-access 0.0.0.0-255.255.255.255 \
    --tags Environment=$ENVIRONMENT HIPAA=true

# Enable encryption at rest (enabled by default in Azure)
echo "✅ PostgreSQL encryption at rest is enabled by default in Azure"

# Create database
echo "Creating database: $DB_NAME"
az postgres flexible-server db create \
    --resource-group $RESOURCE_GROUP \
    --server-name $POSTGRES_SERVER \
    --database-name $DB_NAME

# Configure firewall to allow Azure services
az postgres flexible-server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --name $POSTGRES_SERVER \
    --rule-name AllowAllAzureIPs \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

# Enable SSL enforcement
az postgres flexible-server parameter set \
    --resource-group $RESOURCE_GROUP \
    --server-name $POSTGRES_SERVER \
    --name require_secure_transport \
    --value ON

# Get connection string
DB_HOST="${POSTGRES_SERVER}.postgres.database.azure.com"
DATABASE_URL="postgresql://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

echo "✅ PostgreSQL server created: $DB_HOST"

echo ""
echo "============================================================================"
echo "  STEP 4: CREATE AZURE BLOB STORAGE WITH ENCRYPTION"
echo "============================================================================"
echo ""

echo "Creating Storage Account: $STORAGE_ACCOUNT"

# Storage account names must be lowercase and no hyphens
STORAGE_ACCOUNT=$(echo $STORAGE_ACCOUNT | tr '[:upper:]' '[:lower:]' | tr -d '-')

az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2 \
    --encryption-services blob \
    --https-only true \
    --min-tls-version TLS1_2 \
    --allow-blob-public-access false \
    --tags Environment=$ENVIRONMENT HIPAA=true

# Create container for PHI storage
STORAGE_KEY=$(az storage account keys list \
    --resource-group $RESOURCE_GROUP \
    --account-name $STORAGE_ACCOUNT \
    --query '[0].value' \
    --output tsv)

az storage container create \
    --name phi-storage \
    --account-name $STORAGE_ACCOUNT \
    --account-key $STORAGE_KEY \
    --public-access off

# Enable blob versioning
az storage account blob-service-properties update \
    --account-name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --enable-versioning true

echo "✅ Storage account created with encryption enabled"

echo ""
echo "============================================================================"
echo "  STEP 5: CREATE APPLICATION INSIGHTS"
echo "============================================================================"
echo ""

echo "Creating Application Insights: $APP_INSIGHTS"

az monitor app-insights component create \
    --app $APP_INSIGHTS \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --tags Environment=$ENVIRONMENT HIPAA=true

APP_INSIGHTS_KEY=$(az monitor app-insights component show \
    --app $APP_INSIGHTS \
    --resource-group $RESOURCE_GROUP \
    --query instrumentationKey \
    --output tsv)

echo "✅ Application Insights created"

echo ""
echo "============================================================================"
echo "  STEP 6: STORE SECRETS IN KEY VAULT"
echo "============================================================================"
echo ""

echo "Storing secrets in Key Vault..."

# Wait for Key Vault to be fully ready
sleep 10

az keyvault secret set \
    --vault-name $KEY_VAULT \
    --name "DATABASE-URL" \
    --value "$DATABASE_URL"

az keyvault secret set \
    --vault-name $KEY_VAULT \
    --name "ENCRYPTION-KEY" \
    --value "$ENCRYPTION_KEY"

az keyvault secret set \
    --vault-name $KEY_VAULT \
    --name "FLASK-SECRET-KEY" \
    --value "$FLASK_SECRET"

az keyvault secret set \
    --vault-name $KEY_VAULT \
    --name "STORAGE-CONNECTION-STRING" \
    --value "DefaultEndpointsProtocol=https;AccountName=${STORAGE_ACCOUNT};AccountKey=${STORAGE_KEY};EndpointSuffix=core.windows.net"

az keyvault secret set \
    --vault-name $KEY_VAULT \
    --name "APPINSIGHTS-INSTRUMENTATIONKEY" \
    --value "$APP_INSIGHTS_KEY"

echo "✅ Secrets stored in Key Vault"

echo ""
echo "============================================================================"
echo "  STEP 7: CREATE APP SERVICE PLAN"
echo "============================================================================"
echo ""

echo "Creating App Service Plan: $APP_SERVICE_PLAN"

az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B2 \
    --is-linux \
    --tags Environment=$ENVIRONMENT HIPAA=true

echo "✅ App Service Plan created"

echo ""
echo "============================================================================"
echo "  STEP 8: CREATE WEB APP"
echo "============================================================================"
echo ""

echo "Creating Web App: $WEB_APP"

az webapp create \
    --name $WEB_APP \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON:3.11" \
    --tags Environment=$ENVIRONMENT HIPAA=true

# Enable HTTPS only
az webapp update \
    --name $WEB_APP \
    --resource-group $RESOURCE_GROUP \
    --https-only true \
    --min-tls-version 1.2

# Get Web App principal ID for Key Vault access
WEBAPP_IDENTITY=$(az webapp identity assign \
    --name $WEB_APP \
    --resource-group $RESOURCE_GROUP \
    --query principalId \
    --output tsv)

# Grant Web App access to Key Vault
az keyvault set-policy \
    --name $KEY_VAULT \
    --resource-group $RESOURCE_GROUP \
    --object-id $WEBAPP_IDENTITY \
    --secret-permissions get list

# Configure app settings to use Key Vault references
az webapp config appsettings set \
    --name $WEB_APP \
    --resource-group $RESOURCE_GROUP \
    --settings \
        DATABASE_URL="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=DATABASE-URL)" \
        ENCRYPTION_KEY="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=ENCRYPTION-KEY)" \
        SECRET_KEY="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=FLASK-SECRET-KEY)" \
        AZURE_STORAGE_CONNECTION_STRING="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=STORAGE-CONNECTION-STRING)" \
        APPINSIGHTS_INSTRUMENTATIONKEY="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=APPINSIGHTS-INSTRUMENTATIONKEY)" \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        ENABLE_ORYX_BUILD=true \
        WEBSITES_ENABLE_APP_SERVICE_STORAGE=true

# Configure deployment source (you'll need to set up your repo)
echo "✅ Web App created: https://${WEB_APP}.azurewebsites.net"

echo ""
echo "============================================================================"
echo "  STEP 9: CONFIGURE CUSTOM DOMAIN AND SSL (Optional)"
echo "============================================================================"
echo ""

if [ ! -z "$DOMAIN_NAME" ]; then
    echo "To configure custom domain $DOMAIN_NAME:"
    echo ""
    echo "1. Add DNS record:"
    echo "   Type: CNAME"
    echo "   Name: ${DOMAIN_NAME}"
    echo "   Value: ${WEB_APP}.azurewebsites.net"
    echo ""
    echo "2. Run these commands after DNS propagates:"
    echo "   az webapp config hostname add --webapp-name $WEB_APP --resource-group $RESOURCE_GROUP --hostname $DOMAIN_NAME"
    echo "   az webapp config ssl bind --certificate-thumbprint auto --ssl-type SNI --name $WEB_APP --resource-group $RESOURCE_GROUP"
    echo ""
fi

echo ""
echo "============================================================================"
echo "  DEPLOYMENT SUMMARY"
echo "============================================================================"
echo ""
echo "✅ HIPAA-compliant infrastructure deployed successfully on Azure!"
echo ""
echo "Resources Created:"
echo "  • Resource Group: $RESOURCE_GROUP"
echo "  • PostgreSQL: $DB_HOST (encrypted at rest, SSL enforced)"
echo "  • Storage Account: $STORAGE_ACCOUNT (encrypted, versioning enabled)"
echo "  • Key Vault: $KEY_VAULT (secrets stored securely)"
echo "  • App Service: https://${WEB_APP}.azurewebsites.net"
echo "  • Application Insights: $APP_INSIGHTS (monitoring enabled)"
echo ""
echo "Secrets stored in Key Vault:"
echo "  • DATABASE-URL"
echo "  • ENCRYPTION-KEY"
echo "  • FLASK-SECRET-KEY"
echo "  • STORAGE-CONNECTION-STRING"
echo "  • APPINSIGHTS-INSTRUMENTATIONKEY"
echo ""
echo "============================================================================"
echo "  NEXT STEPS"
echo "============================================================================"
echo ""
echo "1. Deploy your application code:"
echo ""
echo "   Option A - Deploy from local Git:"
echo "   git remote add azure https://${WEB_APP}.scm.azurewebsites.net/${WEB_APP}.git"
echo "   git push azure main"
echo ""
echo "   Option B - Deploy from GitHub:"
echo "   az webapp deployment source config --name $WEB_APP --resource-group $RESOURCE_GROUP \\"
echo "     --repo-url https://github.com/<your-username>/Admissions_Genie \\"
echo "     --branch main --manual-integration"
echo ""
echo "   Option C - Deploy via ZIP:"
echo "   az webapp deployment source config-zip --name $WEB_APP --resource-group $RESOURCE_GROUP \\"
echo "     --src admissions_genie.zip"
echo ""
echo "2. Initialize database:"
echo "   # SSH into Web App or use Azure Cloud Shell"
echo "   python3 seed_database.py"
echo ""
echo "3. Configure custom domain and SSL certificate:"
echo "   # Follow instructions above in Step 9"
echo ""
echo "4. Set up monitoring alerts:"
echo "   # Configure alerts in Application Insights for errors, performance"
echo ""
echo "5. Test backup restoration:"
echo "   # Verify PostgreSQL automated backups work"
echo ""
echo "============================================================================"
echo ""
echo "⚠️  IMPORTANT REMINDERS:"
echo "  1. Configure DNS to point $DOMAIN_NAME to ${WEB_APP}.azurewebsites.net"
echo "  2. Enable automatic backups verification in Azure Backup"
echo "  3. Set up Azure Monitor alerts for security events"
echo "  4. Complete HIPAA policy documentation"
echo "  5. Train staff on security procedures"
echo "  6. Review Azure Security Center recommendations"
echo ""
echo "💰 ESTIMATED MONTHLY COST:"
echo "  • PostgreSQL (B2s): ~\$50-70/month"
echo "  • App Service (B2): ~\$75/month"
echo "  • Storage: ~\$20-30/month"
echo "  • Application Insights: ~\$50-100/month"
echo "  • Key Vault: ~\$5/month"
echo "  • Total: ~\$200-280/month (plus data transfer and OpenAI API)"
echo ""
echo "📚 HELPFUL LINKS:"
echo "  • Azure Portal: https://portal.azure.com"
echo "  • HIPAA Compliance: https://aka.ms/azurecompliance"
echo "  • PostgreSQL Docs: https://docs.microsoft.com/azure/postgresql/"
echo "  • App Service Docs: https://docs.microsoft.com/azure/app-service/"
echo ""
echo "Deployment complete! 🎉"
echo "============================================================================"

# Save deployment info
cat > deployment_info.txt <<EOF
AZURE DEPLOYMENT INFORMATION
============================

Deployment Date: $(date)
Subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)

Resources:
- Resource Group: $RESOURCE_GROUP
- PostgreSQL Server: $DB_HOST
- Database: $DB_NAME
- Storage Account: $STORAGE_ACCOUNT
- Key Vault: $KEY_VAULT
- Web App: https://${WEB_APP}.azurewebsites.net
- Application Insights: $APP_INSIGHTS

Location: $LOCATION
Environment: $ENVIRONMENT
Project: $PROJECT_NAME

Next Steps:
1. Deploy application code
2. Initialize database
3. Configure custom domain: $DOMAIN_NAME
4. Test backup restoration
5. Complete HIPAA documentation

Key Vault Secrets:
- DATABASE-URL
- ENCRYPTION-KEY
- FLASK-SECRET-KEY
- STORAGE-CONNECTION-STRING
- APPINSIGHTS-INSTRUMENTATIONKEY

IMPORTANT: Keep this file secure. It contains sensitive resource names.
EOF

echo ""
echo "✅ Deployment information saved to: deployment_info.txt"
echo ""

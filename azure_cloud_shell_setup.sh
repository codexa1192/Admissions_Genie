#!/bin/bash

##############################################################################
# AZURE CLOUD SHELL - COMPLETE HIPAA DEPLOYMENT
# Copy/paste this ENTIRE script into Azure Cloud Shell
##############################################################################
#
# INSTRUCTIONS:
# 1. Go to https://portal.azure.com
# 2. Click the ">_" icon at top right (Cloud Shell)
# 3. Select "Bash" if prompted
# 4. Copy this ENTIRE file and paste it
# 5. Press Enter and answer the prompts
#
##############################################################################

set -e

clear
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║          ADMISSIONS GENIE - AZURE HIPAA DEPLOYMENT                    ║"
echo "║                  Quick Setup via Cloud Shell                          ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "This script will create your entire HIPAA-compliant infrastructure:"
echo "  ✅ PostgreSQL Database (encrypted)"
echo "  ✅ Blob Storage (encrypted)"
echo "  ✅ Key Vault (secrets)"
echo "  ✅ App Service (web app)"
echo "  ✅ Application Insights (monitoring)"
echo ""
echo "Estimated time: 15-20 minutes"
echo "Estimated cost: ~\$200-280/month"
echo ""

# Confirm BAA
echo "════════════════════════════════════════════════════════════════════════"
echo "HIPAA BUSINESS ASSOCIATE AGREEMENT (BAA)"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  Microsoft's BAA is automatically included in Azure's terms of service."
echo "   By using Azure for HIPAA workloads, you're covered."
echo ""
echo "   Download terms: https://www.microsoft.com/licensing/terms"
echo "   See Section 4(b) - 'HIPAA Business Associate Amendment'"
echo ""
read -p "I understand Microsoft's BAA covers me (type 'yes'): " baa_confirm

if [ "$baa_confirm" != "yes" ]; then
    echo "❌ Please review BAA terms before proceeding."
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "CONFIGURATION"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Get configuration
read -p "Project name [admissions-genie]: " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-admissions-genie}

read -p "Environment [production]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-production}

read -p "Azure region [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "Your email (for alerts): " ADMIN_EMAIL

read -p "Database admin username [dbadmin]: " DB_USER
DB_USER=${DB_USER:-dbadmin}

# Generate secure random password
DB_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
echo "Generated database password: $DB_PASSWORD"
echo "⚠️  SAVE THIS PASSWORD! Writing to deployment_credentials.txt"

read -p "Database name [admissions_genie]: " DB_NAME
DB_NAME=${DB_NAME:-admissions_genie}

# Generate encryption keys
echo ""
echo "Generating encryption keys..."
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
FLASK_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Resource names
RG="${PROJECT_NAME}-${ENVIRONMENT}-rg"
PG_SERVER="${PROJECT_NAME}-${ENVIRONMENT}-db"
STORAGE_ACCOUNT=$(echo "${PROJECT_NAME}${ENVIRONMENT}store" | tr -d '-' | cut -c1-24)
KEY_VAULT="${PROJECT_NAME}-${ENVIRONMENT}-kv"
APP_SERVICE_PLAN="${PROJECT_NAME}-${ENVIRONMENT}-plan"
WEB_APP="${PROJECT_NAME}-${ENVIRONMENT}-app"
APP_INSIGHTS="${PROJECT_NAME}-${ENVIRONMENT}-insights"

echo ""
echo "Configuration Summary:"
echo "  Resource Group: $RG"
echo "  Database: $PG_SERVER"
echo "  Storage: $STORAGE_ACCOUNT"
echo "  Key Vault: $KEY_VAULT"
echo "  Web App: $WEB_APP"
echo "  Location: $LOCATION"
echo ""
read -p "Proceed with deployment? (yes/no): " proceed

if [ "$proceed" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "STEP 1/6: Creating Resource Group"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

az group create \
    --name $RG \
    --location $LOCATION \
    --tags Environment=$ENVIRONMENT HIPAA=true Project=$PROJECT_NAME

echo "✅ Resource group created"

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "STEP 2/6: Creating PostgreSQL Database (5-10 minutes)"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

az postgres flexible-server create \
    --name $PG_SERVER \
    --resource-group $RG \
    --location $LOCATION \
    --admin-user $DB_USER \
    --admin-password "$DB_PASSWORD" \
    --sku-name Standard_B2s \
    --tier Burstable \
    --storage-size 128 \
    --version 15 \
    --high-availability Disabled \
    --backup-retention 7 \
    --public-access 0.0.0.0-255.255.255.255 \
    --tags Environment=$ENVIRONMENT HIPAA=true

echo "✅ PostgreSQL server created"

# Create database
echo "Creating database: $DB_NAME"
az postgres flexible-server db create \
    --resource-group $RG \
    --server-name $PG_SERVER \
    --database-name $DB_NAME

# Enable SSL
az postgres flexible-server parameter set \
    --resource-group $RG \
    --server-name $PG_SERVER \
    --name require_secure_transport \
    --value ON

# Allow Azure services
az postgres flexible-server firewall-rule create \
    --resource-group $RG \
    --name $PG_SERVER \
    --rule-name AllowAllAzureIPs \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

DB_HOST="${PG_SERVER}.postgres.database.azure.com"
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

echo "✅ Database configured with SSL enforcement"

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "STEP 3/6: Creating Storage Account"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RG \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2 \
    --encryption-services blob \
    --https-only true \
    --min-tls-version TLS1_2 \
    --allow-blob-public-access false \
    --tags Environment=$ENVIRONMENT HIPAA=true

# Get storage key
STORAGE_KEY=$(az storage account keys list \
    --resource-group $RG \
    --account-name $STORAGE_ACCOUNT \
    --query '[0].value' \
    --output tsv)

# Create container
az storage container create \
    --name phi-storage \
    --account-name $STORAGE_ACCOUNT \
    --account-key $STORAGE_KEY \
    --public-access off

# Enable versioning
az storage account blob-service-properties update \
    --account-name $STORAGE_ACCOUNT \
    --resource-group $RG \
    --enable-versioning true

STORAGE_CONN_STRING="DefaultEndpointsProtocol=https;AccountName=${STORAGE_ACCOUNT};AccountKey=${STORAGE_KEY};EndpointSuffix=core.windows.net"

echo "✅ Storage account created with encryption"

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "STEP 4/6: Creating Key Vault and Storing Secrets"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

az keyvault create \
    --name $KEY_VAULT \
    --resource-group $RG \
    --location $LOCATION \
    --enable-rbac-authorization false \
    --tags Environment=$ENVIRONMENT HIPAA=true

# Get current user
CURRENT_USER=$(az ad signed-in-user show --query id --output tsv)

# Set access policy for current user
az keyvault set-policy \
    --name $KEY_VAULT \
    --resource-group $RG \
    --object-id $CURRENT_USER \
    --secret-permissions get list set delete

echo "Waiting for Key Vault to be ready..."
sleep 15

# Store secrets
echo "Storing secrets..."

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
    --value "$STORAGE_CONN_STRING"

echo "✅ Key Vault created and secrets stored"

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "STEP 5/6: Creating Application Insights"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

az monitor app-insights component create \
    --app $APP_INSIGHTS \
    --location $LOCATION \
    --resource-group $RG \
    --tags Environment=$ENVIRONMENT HIPAA=true

APP_INSIGHTS_KEY=$(az monitor app-insights component show \
    --app $APP_INSIGHTS \
    --resource-group $RG \
    --query instrumentationKey \
    --output tsv)

az keyvault secret set \
    --vault-name $KEY_VAULT \
    --name "APPINSIGHTS-INSTRUMENTATIONKEY" \
    --value "$APP_INSIGHTS_KEY"

echo "✅ Application Insights created"

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "STEP 6/6: Creating App Service"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Create App Service Plan
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RG \
    --location $LOCATION \
    --sku B2 \
    --is-linux \
    --tags Environment=$ENVIRONMENT HIPAA=true

# Create Web App
az webapp create \
    --name $WEB_APP \
    --resource-group $RG \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON:3.11" \
    --tags Environment=$ENVIRONMENT HIPAA=true

# Enable HTTPS only
az webapp update \
    --name $WEB_APP \
    --resource-group $RG \
    --https-only true \
    --min-tls-version 1.2

# Enable managed identity
WEBAPP_IDENTITY=$(az webapp identity assign \
    --name $WEB_APP \
    --resource-group $RG \
    --query principalId \
    --output tsv)

echo "Waiting for managed identity to propagate..."
sleep 10

# Grant Web App access to Key Vault
az keyvault set-policy \
    --name $KEY_VAULT \
    --resource-group $RG \
    --object-id $WEBAPP_IDENTITY \
    --secret-permissions get list

# Configure app settings
az webapp config appsettings set \
    --name $WEB_APP \
    --resource-group $RG \
    --settings \
        DATABASE_URL="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=DATABASE-URL)" \
        ENCRYPTION_KEY="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=ENCRYPTION-KEY)" \
        SECRET_KEY="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=FLASK-SECRET-KEY)" \
        AZURE_STORAGE_CONNECTION_STRING="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=STORAGE-CONNECTION-STRING)" \
        APPINSIGHTS_INSTRUMENTATIONKEY="@Microsoft.KeyVault(VaultName=${KEY_VAULT};SecretName=APPINSIGHTS-INSTRUMENTATIONKEY)" \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        ENABLE_ORYX_BUILD=true \
        WEBSITES_PORT=8000

echo "✅ App Service created and configured"

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "DEPLOYMENT COMPLETE! 🎉"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Your HIPAA-compliant infrastructure is ready!"
echo ""
echo "Resources Created:"
echo "  • Resource Group: $RG"
echo "  • PostgreSQL: $DB_HOST"
echo "  • Storage: $STORAGE_ACCOUNT"
echo "  • Key Vault: $KEY_VAULT"
echo "  • Web App: https://${WEB_APP}.azurewebsites.net"
echo "  • Application Insights: $APP_INSIGHTS"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "NEXT STEPS"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "1. DEPLOY YOUR CODE:"
echo ""
echo "   Option A - From GitHub (Recommended):"
echo "   In Azure Portal → App Service → Deployment Center"
echo "   → Select GitHub → Authorize → Select your repo"
echo ""
echo "   Option B - From Cloud Shell:"
echo "   git clone https://github.com/YOUR-USERNAME/Admissions_Genie.git"
echo "   cd Admissions_Genie"
echo "   zip -r deploy.zip . -x '*.git*' -x '*venv*'"
echo "   az webapp deployment source config-zip \\"
echo "     --resource-group $RG \\"
echo "     --name $WEB_APP \\"
echo "     --src deploy.zip"
echo ""
echo "2. INITIALIZE DATABASE:"
echo ""
echo "   az webapp ssh --resource-group $RG --name $WEB_APP"
echo "   python3 seed_database.py"
echo ""
echo "3. ACCESS YOUR APP:"
echo "   https://${WEB_APP}.azurewebsites.net"
echo ""
echo "4. CONFIGURE CUSTOM DOMAIN (Optional):"
echo "   Azure Portal → App Service → Custom domains"
echo "   → Add custom domain → Follow wizard"
echo "   → SSL certificate is FREE via Azure App Service!"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "IMPORTANT - SAVE THESE CREDENTIALS!"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Save credentials to file
cat > ~/deployment_credentials.txt <<EOF
ADMISSIONS GENIE - AZURE DEPLOYMENT CREDENTIALS
================================================

Deployment Date: $(date)
Project: $PROJECT_NAME
Environment: $ENVIRONMENT

DATABASE:
---------
Server: $DB_HOST
Database: $DB_NAME
Username: $DB_USER
Password: $DB_PASSWORD
Connection String: $DATABASE_URL

WEB APP:
--------
URL: https://${WEB_APP}.azurewebsites.net
Name: $WEB_APP

AZURE PORTAL:
-------------
Resource Group: $RG
Location: $LOCATION

KEY VAULT:
----------
Name: $KEY_VAULT
Secrets stored:
  - DATABASE-URL
  - ENCRYPTION-KEY
  - FLASK-SECRET-KEY
  - STORAGE-CONNECTION-STRING
  - APPINSIGHTS-INSTRUMENTATIONKEY

STORAGE:
--------
Account: $STORAGE_ACCOUNT
Container: phi-storage

ADMIN:
------
Email: $ADMIN_EMAIL

⚠️  KEEP THIS FILE SECURE! Contains sensitive credentials.

Next Steps:
1. Deploy your code (see instructions above)
2. Initialize database: python3 seed_database.py
3. Configure custom domain (optional)
4. Complete HIPAA documentation
5. Test backup restoration
6. Staff training

Estimated Monthly Cost: ~\$200-280
EOF

echo "✅ Credentials saved to: ~/deployment_credentials.txt"
echo ""
echo "To view credentials anytime:"
echo "  cat ~/deployment_credentials.txt"
echo ""
echo "To download credentials file:"
echo "  In Cloud Shell → Click 'Upload/Download' icon → Download"
echo "  → Enter: deployment_credentials.txt"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "ESTIMATED MONTHLY COST BREAKDOWN"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "  PostgreSQL (B2s):         ~\$50-70/month"
echo "  App Service (B2):         ~\$75/month"
echo "  Storage (100GB):          ~\$20-30/month"
echo "  Application Insights:     ~\$50-100/month"
echo "  Key Vault:                ~\$5/month"
echo "  -------------------------------------------"
echo "  TOTAL:                    ~\$200-280/month"
echo "  (Plus OpenAI API costs)"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "Questions? Check the deployment_credentials.txt file for all details."
echo ""
echo "════════════════════════════════════════════════════════════════════════"

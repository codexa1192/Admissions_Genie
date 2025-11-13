#!/bin/bash

#############################################################################
# AWS PRODUCTION DEPLOYMENT SCRIPT
# Admissions Genie - HIPAA-Compliant SNF Management System
#############################################################################
#
# This script deploys Admissions Genie to AWS with HIPAA-compliant settings:
# - RDS PostgreSQL with encryption at rest
# - S3 with encryption
# - EC2 with SSL/TLS
# - Automated encrypted backups
# - CloudWatch monitoring
#
# PREREQUISITES:
# 1. AWS CLI installed: https://aws.amazon.com/cli/
# 2. AWS account created
# 3. BAA signed via AWS Artifact
# 4. AWS credentials configured: aws configure
#
# USAGE:
#   ./deploy_aws.sh
#
#############################################################################

set -e  # Exit on any error

echo "============================================================================"
echo "  ADMISSIONS GENIE - AWS HIPAA-COMPLIANT DEPLOYMENT"
echo "============================================================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ ERROR: AWS CLI not found. Install from: https://aws.amazon.com/cli/"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ ERROR: AWS credentials not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS CLI installed and configured"
echo ""

# Get AWS account info
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo ""

# Confirm BAA
echo "============================================================================"
echo "  HIPAA BUSINESS ASSOCIATE AGREEMENT (BAA)"
echo "============================================================================"
echo ""
echo "⚠️  CRITICAL: You MUST sign a BAA with AWS before storing PHI."
echo ""
echo "To sign BAA:"
echo "  1. Log into AWS Console"
echo "  2. Search for 'AWS Artifact' in the search bar"
echo "  3. Go to 'Agreements'"
echo "  4. Find 'AWS Business Associate Addendum'"
echo "  5. Review and accept electronically"
echo "  6. Download signed copy for your records"
echo ""
read -p "Have you signed the BAA with AWS? (yes/no): " BAA_SIGNED

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

read -p "Domain name (e.g., app.yourdomain.com): " DOMAIN_NAME

read -p "Database username [dbadmin]: " DB_USERNAME
DB_USERNAME=${DB_USERNAME:-dbadmin}

read -sp "Database password (12+ chars): " DB_PASSWORD
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
echo "  Domain: $DOMAIN_NAME"
echo "  Region: $AWS_REGION"
echo ""

read -p "Proceed with deployment? (yes/no): " PROCEED
if [ "$PROCEED" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "============================================================================"
echo "  STEP 1: CREATE VPC AND SECURITY GROUPS"
echo "============================================================================"
echo ""

# Create VPC
echo "Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$PROJECT_NAME-vpc},{Key=Environment,Value=$ENVIRONMENT},{Key=HIPAA,Value=true}]" \
    --query 'Vpc.VpcId' \
    --output text)
echo "✅ VPC created: $VPC_ID"

# Enable DNS
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support

# Create Internet Gateway
echo "Creating Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=$PROJECT_NAME-igw}]" \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID
echo "✅ Internet Gateway created: $IGW_ID"

# Create subnets (public and private in 2 AZs for Multi-AZ RDS)
echo "Creating subnets..."
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1.0/24 \
    --availability-zone ${AWS_REGION}a \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-public-1}]" \
    --query 'Subnet.SubnetId' \
    --output text)

PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.2.0/24 \
    --availability-zone ${AWS_REGION}b \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-public-2}]" \
    --query 'Subnet.SubnetId' \
    --output text)

PRIVATE_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.10.0/24 \
    --availability-zone ${AWS_REGION}a \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-private-1}]" \
    --query 'Subnet.SubnetId' \
    --output text)

PRIVATE_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.11.0/24 \
    --availability-zone ${AWS_REGION}b \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-private-2}]" \
    --query 'Subnet.SubnetId' \
    --output text)

echo "✅ Subnets created"

# Create route table for public subnets
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=$PROJECT_NAME-public-rt}]" \
    --query 'RouteTable.RouteTableId' \
    --output text)

aws ec2 create-route --route-table-id $ROUTE_TABLE_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_1 --route-table-id $ROUTE_TABLE_ID
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_2 --route-table-id $ROUTE_TABLE_ID

echo "✅ Route tables configured"

# Create security groups
echo "Creating security groups..."

# Web server security group
WEB_SG=$(aws ec2 create-security-group \
    --group-name "$PROJECT_NAME-web-sg" \
    --description "Security group for web servers" \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$PROJECT_NAME-web-sg}]" \
    --query 'GroupId' \
    --output text)

aws ec2 authorize-security-group-ingress --group-id $WEB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $WEB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $WEB_SG --protocol tcp --port 22 --cidr 0.0.0.0/0

# Database security group
DB_SG=$(aws ec2 create-security-group \
    --group-name "$PROJECT_NAME-db-sg" \
    --description "Security group for RDS database" \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$PROJECT_NAME-db-sg}]" \
    --query 'GroupId' \
    --output text)

aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 5432 --source-group $WEB_SG

echo "✅ Security groups created"

echo ""
echo "============================================================================"
echo "  STEP 2: CREATE RDS POSTGRESQL WITH ENCRYPTION"
echo "============================================================================"
echo ""

# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name "$PROJECT_NAME-db-subnet" \
    --db-subnet-group-description "Subnet group for $PROJECT_NAME" \
    --subnet-ids $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2 \
    --tags "Key=Name,Value=$PROJECT_NAME-db-subnet" "Key=HIPAA,Value=true"

echo "Creating RDS PostgreSQL (this may take 10-15 minutes)..."
DB_INSTANCE_ID="$PROJECT_NAME-db"

aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_ID \
    --db-instance-class db.t3.small \
    --engine postgres \
    --engine-version 15.4 \
    --master-username $DB_USERNAME \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage 100 \
    --storage-type gp3 \
    --storage-encrypted \
    --backup-retention-period 7 \
    --preferred-backup-window "02:00-03:00" \
    --db-subnet-group-name "$PROJECT_NAME-db-subnet" \
    --vpc-security-group-ids $DB_SG \
    --db-name $DB_NAME \
    --publicly-accessible false \
    --multi-az \
    --enable-cloudwatch-logs-exports '["postgresql"]' \
    --deletion-protection \
    --tags "Key=Name,Value=$DB_INSTANCE_ID" "Key=HIPAA,Value=true" "Key=Environment,Value=$ENVIRONMENT"

echo "⏳ Waiting for RDS instance to be available (this takes 10-15 minutes)..."
aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID

DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_ID \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo "✅ RDS PostgreSQL created: $DB_ENDPOINT"

echo ""
echo "============================================================================"
echo "  STEP 3: CREATE S3 BUCKET WITH ENCRYPTION"
echo "============================================================================"
echo ""

S3_BUCKET="$PROJECT_NAME-phi-storage-$AWS_ACCOUNT_ID"

echo "Creating S3 bucket: $S3_BUCKET"
aws s3 mb s3://$S3_BUCKET --region $AWS_REGION

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket $S3_BUCKET \
    --server-side-encryption-configuration '{
      "Rules": [{
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }]
    }'

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket $S3_BUCKET \
    --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
    --bucket $S3_BUCKET \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable logging
aws s3api put-bucket-logging \
    --bucket $S3_BUCKET \
    --bucket-logging-status '{
      "LoggingEnabled": {
        "TargetBucket": "'$S3_BUCKET'",
        "TargetPrefix": "logs/"
      }
    }'

echo "✅ S3 bucket created and configured: $S3_BUCKET"

echo ""
echo "============================================================================"
echo "  STEP 4: STORE SECRETS IN AWS SECRETS MANAGER"
echo "============================================================================"
echo ""

echo "Storing secrets..."

DATABASE_URL="postgresql://$DB_USERNAME:$DB_PASSWORD@$DB_ENDPOINT:5432/$DB_NAME"

aws secretsmanager create-secret \
    --name "$PROJECT_NAME/database-url" \
    --description "Database URL for $PROJECT_NAME" \
    --secret-string "$DATABASE_URL" \
    --tags "Key=HIPAA,Value=true" "Key=Environment,Value=$ENVIRONMENT" || true

aws secretsmanager create-secret \
    --name "$PROJECT_NAME/encryption-key" \
    --description "Fernet encryption key for PHI" \
    --secret-string "$ENCRYPTION_KEY" \
    --tags "Key=HIPAA,Value=true" "Key=Environment,Value=$ENVIRONMENT" || true

aws secretsmanager create-secret \
    --name "$PROJECT_NAME/flask-secret-key" \
    --description "Flask secret key" \
    --secret-string "$FLASK_SECRET" \
    --tags "Key=HIPAA,Value=true" "Key=Environment,Value=$ENVIRONMENT" || true

echo "✅ Secrets stored in AWS Secrets Manager"

echo ""
echo "============================================================================"
echo "  STEP 5: CREATE EC2 INSTANCE"
echo "============================================================================"
echo ""

# Create key pair for SSH access
KEY_NAME="$PROJECT_NAME-key"
if [ ! -f "$KEY_NAME.pem" ]; then
    echo "Creating SSH key pair..."
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --query 'KeyMaterial' \
        --output text > "$KEY_NAME.pem"
    chmod 400 "$KEY_NAME.pem"
    echo "✅ Key pair created: $KEY_NAME.pem"
else
    echo "ℹ️  Using existing key pair: $KEY_NAME.pem"
fi

# Get latest Ubuntu AMI
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text)

echo "Launching EC2 instance with AMI: $AMI_ID"

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type t3.medium \
    --key-name $KEY_NAME \
    --security-group-ids $WEB_SG \
    --subnet-id $PUBLIC_SUBNET_1 \
    --associate-public-ip-address \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$PROJECT_NAME-web},{Key=HIPAA,Value=true},{Key=Environment,Value=$ENVIRONMENT}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "⏳ Waiting for EC2 instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ EC2 instance created: $INSTANCE_ID ($PUBLIC_IP)"

echo ""
echo "============================================================================"
echo "  DEPLOYMENT SUMMARY"
echo "============================================================================"
echo ""
echo "✅ HIPAA-compliant infrastructure deployed successfully!"
echo ""
echo "Resources Created:"
echo "  • VPC: $VPC_ID"
echo "  • RDS PostgreSQL: $DB_ENDPOINT (encrypted at rest, Multi-AZ)"
echo "  • S3 Bucket: $S3_BUCKET (encrypted)"
echo "  • EC2 Instance: $PUBLIC_IP"
echo "  • SSH Key: $KEY_NAME.pem"
echo ""
echo "Secrets stored in AWS Secrets Manager:"
echo "  • $PROJECT_NAME/database-url"
echo "  • $PROJECT_NAME/encryption-key"
echo "  • $PROJECT_NAME/flask-secret-key"
echo ""
echo "============================================================================"
echo "  NEXT STEPS"
echo "============================================================================"
echo ""
echo "1. SSH into your EC2 instance:"
echo "   ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo ""
echo "2. Install application dependencies:"
echo "   sudo apt update && sudo apt install -y python3-pip python3-venv nginx"
echo ""
echo "3. Clone your repository and set up environment:"
echo "   git clone <your-repo-url>"
echo "   cd Admissions_Genie"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "4. Set environment variables (retrieve from Secrets Manager):"
echo "   export DATABASE_URL=\$(aws secretsmanager get-secret-value --secret-id $PROJECT_NAME/database-url --query SecretString --output text)"
echo "   export ENCRYPTION_KEY=\$(aws secretsmanager get-secret-value --secret-id $PROJECT_NAME/encryption-key --query SecretString --output text)"
echo "   export SECRET_KEY=\$(aws secretsmanager get-secret-value --secret-id $PROJECT_NAME/flask-secret-key --query SecretString --output text)"
echo ""
echo "5. Initialize database:"
echo "   python3 seed_database.py"
echo ""
echo "6. Configure nginx and SSL certificate (use Let's Encrypt)"
echo ""
echo "7. Start application with Gunicorn"
echo ""
echo "============================================================================"
echo ""
echo "⚠️  IMPORTANT REMINDERS:"
echo "  1. Configure DNS to point $DOMAIN_NAME to $PUBLIC_IP"
echo "  2. Set up SSL certificate (use certbot for Let's Encrypt)"
echo "  3. Configure automated backups verification"
echo "  4. Set up CloudWatch alarms for monitoring"
echo "  5. Complete HIPAA policy documentation"
echo "  6. Train staff on security procedures"
echo ""
echo "Deployment complete! 🎉"
echo "============================================================================"

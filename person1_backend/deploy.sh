#!/bin/bash

# DocuProcess Lambda Deployment Script
# This script automates AWS setup for Person 1's backend

set -e  # Exit on error

echo "=========================================="
echo "DocuProcess Lambda Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FUNCTION_NAME="DocuProcessDocumentExtractor"
RUNTIME="python3.9"
ROLE_NAME="DocuProcess-Lambda-Role"
S3_BUCKET="justicearch-inbox"
DYNAMODB_TABLE="DocumentRecords"
REGION="us-east-1"
TIMEOUT="300"
MEMORY="512"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}AWS CLI not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v zip &> /dev/null; then
        echo -e "${RED}zip not found. Please install it first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Prerequisites OK${NC}"
    echo ""
}

# Get AWS Account ID
get_account_id() {
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [ -z "$ACCOUNT_ID" ]; then
        echo -e "${RED}Failed to get AWS Account ID. Check your AWS credentials.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS Account ID: $ACCOUNT_ID${NC}"
}

# Create S3 bucket
create_s3_bucket() {
    echo -e "${YELLOW}Creating S3 bucket...${NC}"
    
    if aws s3 ls "s3://$S3_BUCKET" 2>/dev/null; then
        echo -e "${GREEN}✓ S3 bucket already exists${NC}"
    else
        aws s3api create-bucket \
            --bucket "$S3_BUCKET" \
            --region "$REGION"
        echo -e "${GREEN}✓ S3 bucket created${NC}"
    fi
    
    # Block public access
    aws s3api put-public-access-block \
        --bucket "$S3_BUCKET" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    
    echo ""
}

# Create IAM role
create_iam_role() {
    echo -e "${YELLOW}Setting up IAM role...${NC}"
    
    # Check if role exists
    if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
        echo -e "${GREEN}✓ IAM role already exists${NC}"
    else
        # Create trust policy
        cat > /tmp/trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
        
        aws iam create-role \
            --role-name "$ROLE_NAME" \
            --assume-role-policy-document file:///tmp/trust-policy.json
        
        echo -e "${GREEN}✓ IAM role created${NC}"
        
        # Wait for role to be available
        sleep 2
    fi
    
    # Create and attach policies
    attach_policies
    
    echo ""
}

# Attach IAM policies
attach_policies() {
    echo -e "${YELLOW}Attaching policies to role...${NC}"
    
    # S3 policy
    cat > /tmp/s3-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::$S3_BUCKET/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::$S3_BUCKET"
    }
  ]
}
EOF
    
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name S3Access \
        --policy-document file:///tmp/s3-policy.json
    
    # Textract policy
    cat > /tmp/textract-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument"
      ],
      "Resource": "*"
    }
  ]
}
EOF
    
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name TextractAccess \
        --policy-document file:///tmp/textract-policy.json
    
    # DynamoDB policy
    cat > /tmp/dynamodb-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:$REGION:*:table/$DYNAMODB_TABLE"
    }
  ]
}
EOF
    
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name DynamoDBAccess \
        --policy-document file:///tmp/dynamodb-policy.json
    
    # CloudWatch Logs policy
    cat > /tmp/logs-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF
    
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name CloudWatchLogs \
        --policy-document file:///tmp/logs-policy.json
    
    echo -e "${GREEN}✓ Policies attached${NC}"
}

# Create deployment package
create_deployment_package() {
    echo -e "${YELLOW}Creating Lambda deployment package...${NC}"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT
    
    # Copy Lambda files
    cp lambda_function/*.py "$TEMP_DIR/"
    
    # Install dependencies
    pip install -q -r requirements.txt -t "$TEMP_DIR/"
    
    # Create ZIP file
    cd "$TEMP_DIR"
    zip -q -r "$OLDPWD/lambda_function.zip" .
    cd "$OLDPWD"
    
    echo -e "${GREEN}✓ Deployment package created: lambda_function.zip${NC}"
    echo ""
}

# Deploy Lambda function
deploy_lambda() {
    echo -e "${YELLOW}Deploying Lambda function...${NC}"
    
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
    
    # Check if function exists
    if aws lambda get-function --function-name "$FUNCTION_NAME" 2>/dev/null; then
        echo -e "${YELLOW}Updating existing Lambda function...${NC}"
        
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file fileb://lambda_function.zip
    else
        echo -e "${YELLOW}Creating new Lambda function...${NC}"
        
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime "$RUNTIME" \
            --role "$ROLE_ARN" \
            --handler lambda_handler.lambda_handler \
            --zip-file fileb://lambda_function.zip \
            --timeout "$TIMEOUT" \
            --memory-size "$MEMORY" \
            --environment "Variables={
                S3_BUCKET_NAME=$S3_BUCKET,
                DYNAMODB_TABLE_NAME=$DYNAMODB_TABLE,
                CONFIDENCE_THRESHOLD=80,
                AWS_REGION=$REGION,
                LOG_LEVEL=INFO
            }"
    fi
    
    echo -e "${GREEN}✓ Lambda function deployed${NC}"
    echo ""
}

# Configure S3 event trigger
configure_s3_trigger() {
    echo -e "${YELLOW}Configuring S3 event trigger...${NC}"
    
    LAMBDA_ARN="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME"
    
    # Add Lambda permission for S3
    aws lambda add-permission \
        --function-name "$FUNCTION_NAME" \
        --statement-id AllowS3Invoke \
        --action lambda:InvokeFunction \
        --principal s3.amazonaws.com \
        --source-arn "arn:aws:s3:::$S3_BUCKET" 2>/dev/null || true
    
    # Configure S3 bucket notification
    cat > /tmp/notification-config.json << EOF
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "prefix", "Value": "invoices/"},
            {"Name": "suffix", "Value": ".pdf"}
          ]
        }
      }
    }
  ]
}
EOF
    
    aws s3api put-bucket-notification-configuration \
        --bucket "$S3_BUCKET" \
        --notification-configuration file:///tmp/notification-config.json
    
    echo -e "${GREEN}✓ S3 event trigger configured${NC}"
    echo ""
}

# Main execution
main() {
    check_prerequisites
    get_account_id
    create_s3_bucket
    create_iam_role
    create_deployment_package
    deploy_lambda
    configure_s3_trigger
    
    echo -e "${GREEN}=========================================="
    echo "✓ Deployment Complete!"
    echo "==========================================${NC}"
    echo ""
    echo "Lambda Function: $FUNCTION_NAME"
    echo "S3 Bucket: $S3_BUCKET"
    echo "DynamoDB Table: $DYNAMODB_TABLE"
    echo "Region: $REGION"
    echo ""
    echo "Next steps:"
    echo "1. Upload a test PDF to s3://$S3_BUCKET/invoices/"
    echo "2. Check Lambda logs: aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
    echo "3. Verify data in DynamoDB: aws dynamodb scan --table-name $DYNAMODB_TABLE"
    echo ""
}

# Run main function
main "$@"

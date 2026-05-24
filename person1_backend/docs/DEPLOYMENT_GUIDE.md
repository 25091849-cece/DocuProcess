# DocuProcess Lambda Deployment Guide

## Step-by-Step Deployment Instructions

### Prerequisites Checklist
- [ ] AWS Academy Learner Lab access active
- [ ] AWS CLI v2+ installed (`aws --version`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Python 3.9+ installed
- [ ] All source code committed to GitHub
- [ ] Environment variables defined

### Phase 1: Environment Setup (5-10 minutes)

#### 1.1 Verify AWS CLI Configuration
```bash
aws sts get-caller-identity
```
**Expected Output:**
```json
{
    "UserId": "YOUR_USER_ID",
    "Account": "YOUR_ACCOUNT_ID",
    "Arn": "arn:aws:iam::YOUR_ACCOUNT_ID:root"
}
```

#### 1.2 Set Environment Variables
```bash
# Set region
export AWS_REGION=us-east-1

# Set bucket name
export S3_BUCKET_NAME=justicearch-inbox

# Set DynamoDB table name
export DYNAMODB_TABLE_NAME=DocumentRecords

# Set confidence threshold
export CONFIDENCE_THRESHOLD=80

# Get your account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

#### 1.3 Verify Region Support
```bash
aws textract get-document-analysis --region $AWS_REGION 2>&1 | grep -q "Unknown parameter" && echo "Region OK" || echo "Check region support"
```

---

### Phase 2: AWS Service Setup (15-20 minutes)

#### 2.1 Create S3 Bucket
```bash
# Create bucket
aws s3api create-bucket \
  --bucket $S3_BUCKET_NAME \
  --region $AWS_REGION

# Verify bucket creation
aws s3api head-bucket --bucket $S3_BUCKET_NAME
echo "✓ S3 bucket created successfully"
```

#### 2.2 Configure S3 Bucket Settings
```bash
# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $S3_BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket $S3_BUCKET_NAME \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Create prefix directories
aws s3api put-object --bucket $S3_BUCKET_NAME --key invoices/
aws s3api put-object --bucket $S3_BUCKET_NAME --key processed/
aws s3api put-object --bucket $S3_BUCKET_NAME --key archived/

echo "✓ S3 bucket configured"
```

#### 2.3 Create DynamoDB Table
```bash
aws dynamodb create-table \
  --table-name $DYNAMODB_TABLE_NAME \
  --attribute-definitions \
    AttributeName=document_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=document_id,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION

# Wait for table to be active (may take 1-2 minutes)
aws dynamodb wait table-exists --table-name $DYNAMODB_TABLE_NAME --region $AWS_REGION

# Add Global Secondary Index for status queries
aws dynamodb update-table \
  --table-name $DYNAMODB_TABLE_NAME \
  --attribute-definitions \
    AttributeName=status,AttributeType=S \
  --global-secondary-index-updates '[
    {
      "Create": {
        "IndexName": "status-timestamp-index",
        "Keys": [
          {"AttributeName": "status", "KeyType": "HASH"},
          {"AttributeName": "timestamp", "KeyType": "RANGE"}
        ],
        "Projection": {"ProjectionType": "ALL"},
        "ProvisionedThroughput": {
          "ReadCapacityUnits": 5,
          "WriteCapacityUnits": 5
        }
      }
    }
  ]' \
  --region $AWS_REGION 2>/dev/null || true

echo "✓ DynamoDB table created"
```

---

### Phase 3: IAM Role Setup (10-15 minutes)

#### 3.1 Create Lambda Execution Role
```bash
# Create trust policy
cat > /tmp/trust-policy.json << 'EOF'
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

# Create role
aws iam create-role \
  --role-name DocuProcess-Lambda-Role \
  --assume-role-policy-document file:///tmp/trust-policy.json \
  --region $AWS_REGION

echo "✓ IAM role created"
```

#### 3.2 Attach IAM Policies
```bash
# S3 Access
cat > /tmp/s3-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::BUCKET_NAME/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::BUCKET_NAME"
    }
  ]
}
EOF

sed -i "s/BUCKET_NAME/$S3_BUCKET_NAME/g" /tmp/s3-policy.json

aws iam put-role-policy \
  --role-name DocuProcess-Lambda-Role \
  --policy-name S3Access \
  --policy-document file:///tmp/s3-policy.json

# Textract Access
cat > /tmp/textract-policy.json << 'EOF'
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
  --role-name DocuProcess-Lambda-Role \
  --policy-name TextractAccess \
  --policy-document file:///tmp/textract-policy.json

# DynamoDB Access
cat > /tmp/dynamodb-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name DocuProcess-Lambda-Role \
  --policy-name DynamoDBAccess \
  --policy-document file:///tmp/dynamodb-policy.json

# CloudWatch Logs
cat > /tmp/logs-policy.json << 'EOF'
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
  --role-name DocuProcess-Lambda-Role \
  --policy-name CloudWatchLogs \
  --policy-document file:///tmp/logs-policy.json

echo "✓ IAM policies attached"

# Get role ARN for next steps
ROLE_ARN=$(aws iam get-role --role-name DocuProcess-Lambda-Role --query 'Role.Arn' --output text)
echo "Role ARN: $ROLE_ARN"
```

---

### Phase 4: Lambda Function Deployment (15-20 minutes)

#### 4.1 Prepare Deployment Package
```bash
cd person1_backend

# Create deployment directory
mkdir -p lambda_deployment
cd lambda_deployment

# Copy source files
cp ../lambda_function/*.py .
cp ../config/*.py .

# Install dependencies
pip install -r ../requirements.txt -t . --quiet

# Verify key files
ls -la lambda_handler.py textract_processor.py dynamodb_handler.py config.py

echo "✓ Deployment package prepared"
```

#### 4.2 Create Deployment ZIP
```bash
# Create ZIP file
zip -r ../lambda_function.zip . -q

# Verify ZIP
unzip -l ../lambda_function.zip | head -20

# Check ZIP size (must be < 50MB for direct upload)
ZIP_SIZE=$(ls -lh ../lambda_function.zip | awk '{print $5}')
echo "ZIP file size: $ZIP_SIZE"
```

#### 4.3 Deploy Lambda Function
```bash
cd ..

# Deploy function
aws lambda create-function \
  --function-name DocuProcessDocumentExtractor \
  --runtime python3.9 \
  --role $ROLE_ARN \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment "Variables={
    S3_BUCKET_NAME=$S3_BUCKET_NAME,
    DYNAMODB_TABLE_NAME=$DYNAMODB_TABLE_NAME,
    CONFIDENCE_THRESHOLD=$CONFIDENCE_THRESHOLD,
    AWS_REGION=$AWS_REGION,
    LOG_LEVEL=INFO
  }" \
  --region $AWS_REGION

echo "✓ Lambda function deployed"

# Get function details
aws lambda get-function \
  --function-name DocuProcessDocumentExtractor \
  --region $AWS_REGION \
  --query 'Configuration.[FunctionArn,Runtime,MemorySize,Timeout]' \
  --output table
```

---

### Phase 5: S3 Event Trigger Configuration (10-15 minutes)

#### 5.1 Get Lambda Function ARN
```bash
LAMBDA_ARN=$(aws lambda get-function \
  --function-name DocuProcessDocumentExtractor \
  --region $AWS_REGION \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "Lambda ARN: $LAMBDA_ARN"
```

#### 5.2 Grant S3 Permission to Invoke Lambda
```bash
aws lambda add-permission \
  --function-name DocuProcessDocumentExtractor \
  --statement-id AllowS3Invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::$S3_BUCKET_NAME \
  --region $AWS_REGION

echo "✓ S3 permission granted"
```

#### 5.3 Configure S3 Event Notification
```bash
# Create notification configuration
cat > /tmp/s3-notification.json << 'EOF'
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "LAMBDA_ARN",
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

sed -i "s|LAMBDA_ARN|$LAMBDA_ARN|g" /tmp/s3-notification.json

# Apply configuration
aws s3api put-bucket-notification-configuration \
  --bucket $S3_BUCKET_NAME \
  --notification-configuration file:///tmp/s3-notification.json \
  --region $AWS_REGION

echo "✓ S3 event trigger configured"
```

---

### Phase 6: Testing & Verification (20-30 minutes)

#### 6.1 Test Lambda Function Directly
```bash
# Create test event
cat > /tmp/test-event.json << 'EOF'
{
  "Records": [
    {
      "s3": {
        "bucket": {"name": "BUCKET_NAME"},
        "object": {"key": "invoices/test-001.pdf"}
      }
    }
  ]
}
EOF

sed -i "s/BUCKET_NAME/$S3_BUCKET_NAME/g" /tmp/test-event.json

# Test Lambda
aws lambda invoke \
  --function-name DocuProcessDocumentExtractor \
  --invocation-type RequestResponse \
  --payload file:///tmp/test-event.json \
  /tmp/lambda_response.json \
  --region $AWS_REGION

echo "Lambda test response:"
cat /tmp/lambda_response.json | jq .

echo "✓ Lambda function tested"
```

#### 6.2 Check CloudWatch Logs
```bash
# Get recent logs
aws logs tail /aws/lambda/DocuProcessDocumentExtractor \
  --follow \
  --region $AWS_REGION \
  --max-items 20
```

#### 6.3 Verify DynamoDB Table
```bash
# Scan table for test records
aws dynamodb scan \
  --table-name $DYNAMODB_TABLE_NAME \
  --region $AWS_REGION \
  --output table
```

#### 6.4 Test S3 Upload Trigger (Using Sample PDF)
```bash
# Create a simple test PDF (if available)
# aws s3 cp sample_invoice.pdf s3://$S3_BUCKET_NAME/invoices/test-invoice-001.pdf

# Monitor Lambda execution
echo "Waiting for Lambda to execute..."
sleep 5

# Check DynamoDB for new records
aws dynamodb scan \
  --table-name $DYNAMODB_TABLE_NAME \
  --region $AWS_REGION \
  --filter-expression "begins_with(#id, :val)" \
  --expression-attribute-names '{"#id":"document_id"}' \
  --expression-attribute-values '{":val":{"S":"test"}}' \
  --output table
```

---

### Phase 7: Deployment Verification Checklist

- [ ] S3 bucket created and configured
- [ ] DynamoDB table created with GSI
- [ ] IAM role created with correct policies
- [ ] Lambda function deployed and active
- [ ] S3 event trigger configured
- [ ] Lambda can read from S3
- [ ] Lambda can write to DynamoDB
- [ ] CloudWatch logs are working
- [ ] Test event executes successfully
- [ ] S3 file upload triggers Lambda
- [ ] Extracted data appears in DynamoDB

---

### Cleanup (If needed)
```bash
# Delete Lambda function
aws lambda delete-function --function-name DocuProcessDocumentExtractor --region $AWS_REGION

# Delete IAM role
aws iam delete-role-policy --role-name DocuProcess-Lambda-Role --policy-name S3Access
aws iam delete-role --role-name DocuProcess-Lambda-Role

# Delete DynamoDB table
aws dynamodb delete-table --table-name $DYNAMODB_TABLE_NAME --region $AWS_REGION

# Delete S3 bucket (must be empty first)
aws s3 rm s3://$S3_BUCKET_NAME --recursive
aws s3api delete-bucket --bucket $S3_BUCKET_NAME --region $AWS_REGION
```

---

## Troubleshooting

### Lambda Timeout
- **Problem**: Lambda function times out
- **Solution**: Increase timeout in Lambda configuration (max 900 seconds)
```bash
aws lambda update-function-configuration \
  --function-name DocuProcessDocumentExtractor \
  --timeout 300
```

### S3 Event Not Triggering Lambda
- **Problem**: File uploaded to S3 but Lambda doesn't execute
- **Solution**: Verify S3 notification configuration and Lambda permissions
```bash
# Check current notification
aws s3api get-bucket-notification-configuration --bucket $S3_BUCKET_NAME

# Check Lambda permissions
aws lambda get-policy --function-name DocuProcessDocumentExtractor
```

### DynamoDB Access Denied
- **Problem**: Lambda cannot write to DynamoDB
- **Solution**: Verify IAM policy includes DynamoDB permissions
```bash
# List attached policies
aws iam list-role-policies --role-name DocuProcess-Lambda-Role

# Get policy details
aws iam get-role-policy --role-name DocuProcess-Lambda-Role --policy-name DynamoDBAccess
```

### Textract API Error
- **Problem**: `InvalidParameterException` or `UnsupportedDocumentException`
- **Solution**: Ensure document is a valid PDF/image and in supported region
```bash
# Verify Textract availability
aws textract describe-document-classification-job --region $AWS_REGION
```

---

## Next Steps

1. **Integrate with Person 2's Database**: Connect DynamoDB with Person 2's queries
2. **Implement Person 4's SNS**: Add SNS notifications for NEED_REVIEW documents
3. **Setup CloudFront**: Distribute processed documents via CDN
4. **Monitor Costs**: Set up AWS Cost Explorer alerts
5. **Auto-scaling**: Configure DynamoDB auto-scaling for production


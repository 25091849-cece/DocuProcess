# Person 1 Backend - AWS Setup Guide

## Overview
This guide covers the AWS configuration needed for Person 1's backend implementation of the DocuProcess document pipeline.

## Prerequisites
- AWS Academy Learner Lab access
- AWS CLI installed and configured
- Python 3.9+
- Appropriate IAM permissions in your AWS account

## 1. S3 Setup

### Create S3 Bucket for Document Inbox

```bash
aws s3api create-bucket \
  --bucket justicearch-inbox \
  --region us-east-1
```

### Enable Versioning (Optional but recommended)
```bash
aws s3api put-bucket-versioning \
  --bucket justicearch-inbox \
  --versioning-configuration Status=Enabled
```

### Block Public Access
```bash
aws s3api put-public-access-block \
  --bucket justicearch-inbox \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### Configure S3 Event Notifications for Lambda
This configuration will be done in the Lambda setup section.

**S3 Bucket Event Structure:**
- Event Type: `s3:ObjectCreated:*`
- Destination: Lambda Function
- Prefix Filter: `invoices/` (optional)
- Suffix Filter: `.pdf` (optional)

---

## 2. Lambda Function Setup

### Create IAM Role for Lambda

**Create Trust Policy** (`lambda-trust-policy.json`):
```json
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
```

**Create the role:**
```bash
aws iam create-role \
  --role-name DocuProcess-Lambda-Role \
  --assume-role-policy-document file://lambda-trust-policy.json
```

### Attach Policies to Lambda Role

**S3 Access Policy** (`s3-policy.json`):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::justicearch-inbox/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::justicearch-inbox"
    }
  ]
}
```

**Textract Access Policy** (`textract-policy.json`):
```json
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
```

**DynamoDB Access Policy** (`dynamodb-policy.json`):
```json
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
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/DocumentRecords"
    }
  ]
}
```

**CloudWatch Logs Policy** (`logs-policy.json`):
```json
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
```

**Attach policies:**
```bash
# Create and attach inline policies
aws iam put-role-policy \
  --role-name DocuProcess-Lambda-Role \
  --policy-name S3Access \
  --policy-document file://s3-policy.json

aws iam put-role-policy \
  --role-name DocuProcess-Lambda-Role \
  --policy-name TextractAccess \
  --policy-document file://textract-policy.json

aws iam put-role-policy \
  --role-name DocuProcess-Lambda-Role \
  --policy-name DynamoDBAccess \
  --policy-document file://dynamodb-policy.json

aws iam put-role-policy \
  --role-name DocuProcess-Lambda-Role \
  --policy-name CloudWatchLogs \
  --policy-document file://logs-policy.json
```

### Create Lambda Function Deployment Package

1. **Prepare files:**
```bash
cd person1_backend/lambda_function
mkdir lambda_deployment
cp *.py lambda_deployment/
cd lambda_deployment
```

2. **Install dependencies:**
```bash
pip install -r ../requirements.txt -t .
```

3. **Create ZIP:**
```bash
zip -r lambda_function.zip .
```

### Deploy Lambda Function

```bash
aws lambda create-function \
  --function-name DocuProcessDocumentExtractor \
  --runtime python3.9 \
  --role arn:aws:iam::<YOUR_ACCOUNT_ID>:role/DocuProcess-Lambda-Role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables='{
    "S3_BUCKET_NAME=justicearch-inbox",
    "DYNAMODB_TABLE_NAME=DocumentRecords",
    "CONFIDENCE_THRESHOLD=80",
    "AWS_REGION=us-east-1"
  }'
```

### Configure S3 Event Trigger

```bash
aws s3api put-bucket-notification-configuration \
  --bucket justicearch-inbox \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "LambdaFunctionArn": "arn:aws:lambda:us-east-1:<YOUR_ACCOUNT_ID>:function:DocuProcessDocumentExtractor",
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
  }'
```

**Grant S3 permission to invoke Lambda:**
```bash
aws lambda add-permission \
  --function-name DocuProcessDocumentExtractor \
  --statement-id AllowS3Invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::justicearch-inbox
```

---

## 3. Amazon Textract Configuration

### Enable Textract for Your Account
Textract is available in most regions. Verify it's available:

```bash
aws textract describe-document-classification-job --region us-east-1
```

### Textract API Usage
The Lambda function uses:
- `detect_document_text`: Extract raw text (asynchronous calls not needed for small documents)
- `analyze_document`: For more advanced extraction with Forms and Tables

---

## 4. Environment Variables

Create `.env` file for local testing:
```
AWS_REGION=us-east-1
S3_BUCKET_NAME=justicearch-inbox
DYNAMODB_TABLE_NAME=DocumentRecords
CONFIDENCE_THRESHOLD=80
TEXTRACT_MAX_RESULTS=100
LOG_LEVEL=INFO
```

---

## 5. Testing Locally

### Install Dependencies
```bash
cd person1_backend
pip install -r requirements.txt
```

### Run Unit Tests
```bash
python -m pytest tests/
```

### Test Lambda Locally with SAM CLI (Optional)
```bash
pip install aws-sam-cli
sam local invoke DocuProcessDocumentExtractor -e test_event.json
```

**Sample test event** (`test_event.json`):
```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "justicearch-inbox",
          "arn": "arn:aws:s3:::justicearch-inbox"
        },
        "object": {
          "key": "invoices/test-invoice-001.pdf",
          "size": 5242880,
          "sequencer": "0A47r5by"
        }
      }
    }
  ]
}
```

---

## 6. Monitoring & Logging

### View Lambda Logs
```bash
aws logs tail /aws/lambda/DocuProcessDocumentExtractor --follow
```

### CloudWatch Metrics
Monitor in AWS Console:
- Invocations
- Errors
- Duration
- Throttles

---

## Important Notes

1. **Account ID**: Replace `<YOUR_ACCOUNT_ID>` with your actual AWS account ID
   ```bash
   aws sts get-caller-identity --query Account --output text
   ```

2. **Textract Pricing**: Each API call incurs charges. Monitor usage in AWS Billing.

3. **Lambda Timeout**: Set to 300 seconds (5 minutes) for processing large PDFs.

4. **Memory**: Allocate at least 512 MB for processing large documents.

5. **Integration with Person 2**: Lambda saves results to DynamoDB table (created by Person 2).

6. **Integration with Person 4**: 
   - Low confidence documents marked as `NEED_REVIEW`
   - Person 4 implements SNS notifications for these records

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Lambda timeout | Increase timeout and/or memory size |
| Permission denied errors | Check IAM role policies are correctly attached |
| Textract API errors | Ensure Textract is available in your region |
| S3 event not triggering | Verify S3 bucket notification configuration |
| DynamoDB errors | Ensure table exists with correct name and schema |

---

## Next Steps

1. ✅ Set up S3 bucket
2. ✅ Configure Lambda with IAM role
3. ✅ Deploy Lambda function
4. ✅ Connect S3 event trigger
5. ⏳ Wait for Person 2 to create DynamoDB table
6. ⏳ Test full pipeline with sample PDF

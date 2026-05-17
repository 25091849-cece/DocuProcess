# Person 2 - DynamoDB Setup Guide

## Overview

This guide covers setting up Amazon DynamoDB for the DocuProcess document processing system.

## Prerequisites

- AWS Academy Learner Lab access
- AWS CLI installed and configured
- Python 3.9+
- Basic understanding of databases

## 1. Create DynamoDB Table

### Using AWS Console (Easiest)

1. Go to AWS Console → DynamoDB
2. Click "Create table"
3. Fill in the following:
   - **Table name**: `DocumentRecords`
   - **Primary key**: `document_id` (String)
   - **Sort key**: Leave empty (or use `timestamp` for time-series)
4. Click "Create"

### Using AWS CLI

```bash
aws dynamodb create-table \
  --table-name DocumentRecords \
  --attribute-definitions \
    AttributeName=document_id,AttributeType=S \
  --key-schema \
    AttributeName=document_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Explanation**:
- `PAY_PER_REQUEST`: Pay per operation (good for variable traffic)
- Alternative: `--provisioned-throughput` for fixed capacity

## 2. Table Schema

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| document_id | String | ✅ Yes | Unique identifier (PK) |
| vendor | String | ✅ Yes | Vendor/Company name |
| date | String | ✅ Yes | Document date |
| amount | Number | ✅ Yes | Document amount |
| status | String | ✅ Yes | APPROVED or NEED_REVIEW |
| confidence_score | Number | ❌ No | Confidence 0-100 |
| s3_location | String | ❌ No | S3 file location |
| raw_text | String | ❌ No | Full extracted text |
| timestamp | String | ✅ Yes | Creation timestamp |
| last_updated | String | ❌ No | Last modification time |

## 3. Create Global Secondary Indexes (GSI)

### For Status Queries

Create GSI to query by status efficiently:

**Using AWS CLI**:
```bash
aws dynamodb update-table \
  --table-name DocumentRecords \
  --attribute-definitions \
    AttributeName=status,AttributeType=S \
  --global-secondary-indexes \
    IndexName=status-timestamp-index,\
KeySchema=[{AttributeName=status,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}],\
Projection={ProjectionType=ALL},\
ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}
```

### Supported Queries with Indexes

After creating GSI:
```python
# Fast query by status
db.get_documents_by_status('APPROVED')

# Alternative: Query by status and date
response = table.query(
    IndexName='status-timestamp-index',
    KeyConditionExpression='#s = :status',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':status': 'NEED_REVIEW'}
)
```

## 4. Enable Point-in-Time Recovery (Recommended)

```bash
aws dynamodb update-continuous-backups \
  --table-name DocumentRecords \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

## 5. Set Up IAM Permissions

### For Application Access

**Policy for Person 1 (Lambda)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/DocumentRecords"
    }
  ]
}
```

**Policy for Person 3 (Web App)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/DocumentRecords"
    }
  ]
}
```

## 6. Test DynamoDB Setup

### Using AWS CLI

**Put an item**:
```bash
aws dynamodb put-item \
  --table-name DocumentRecords \
  --item '{
    "document_id": {"S": "DOC001"},
    "vendor": {"S": "Test Vendor"},
    "date": {"S": "2026-05-17"},
    "amount": {"N": "1000"},
    "status": {"S": "APPROVED"},
    "timestamp": {"S": "2026-05-17T10:30:00Z"}
  }'
```

**Get an item**:
```bash
aws dynamodb get-item \
  --table-name DocumentRecords \
  --key '{"document_id": {"S": "DOC001"}}'
```

**Scan table**:
```bash
aws dynamodb scan --table-name DocumentRecords
```

### Using Python

```python
from db_operations.db_handler import DynamoDBHandler

db = DynamoDBHandler('DocumentRecords', 'us-east-1')

# Insert test document
doc = {
    'document_id': 'TEST-001',
    'vendor': 'Test Corporation',
    'date': '2026-05-17',
    'amount': 5000,
    'status': 'APPROVED'
}
result = db.insert_document(doc)
print(result)

# Retrieve it
result = db.get_document('TEST-001')
print(result)
```

## 7. Backup & Recovery

### Manual Backup

```bash
aws dynamodb create-backup \
  --table-name DocumentRecords \
  --backup-name DocumentRecords-backup-$(date +%s)
```

### Restore from Backup

```bash
aws dynamodb restore-table-from-backup \
  --target-table-name DocumentRecords-restored \
  --backup-arn <backup-arn>
```

## 8. Monitoring

### CloudWatch Metrics

Monitor in AWS Console:
- **ConsumedWriteCapacityUnits** - Write usage
- **ConsumedReadCapacityUnits** - Read usage
- **UserErrors** - Application errors
- **SystemErrors** - Service errors

### Enable CloudWatch Logging

```bash
aws dynamodb update-table \
  --table-name DocumentRecords \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

## 9. Scaling Considerations

### For Development
- Use `PAY_PER_REQUEST` billing mode
- Start with basic schema
- Create GSI as needed

### For Production
- Use provisioned capacity
- Create multiple GSIs for common queries
- Enable backups
- Enable point-in-time recovery
- Monitor and scale as needed

## 10. Cleanup

### Delete Table

```bash
aws dynamodb delete-table --table-name DocumentRecords
```

### Delete Backups

```bash
aws dynamodb delete-backup --backup-arn <backup-arn>
```

## Environment Variables

```bash
export AWS_REGION=us-east-1
export DYNAMODB_TABLE_NAME=DocumentRecords
export LOG_LEVEL=INFO
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ResourceNotFoundException` | Table doesn't exist - create it first |
| `ValidationException` | Schema mismatch - verify attribute types |
| `ProvisionedThroughputExceededException` | Increase capacity or use PAY_PER_REQUEST |
| `AccessDenied` | Check IAM permissions |

## Next Steps

1. ✅ Create DynamoDB table
2. ✅ Set up GSI for status queries
3. ✅ Configure IAM permissions
4. ✅ Test with sample data
5. ⏳ Integrate with Person 1 (Lambda)
6. ⏳ Integrate with Person 3 (Web App)

---

**Deadline**: Week 9  
**Duration**: Max 1 Week

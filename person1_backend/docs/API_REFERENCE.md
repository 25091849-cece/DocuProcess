# Person 1 API Reference

## Lambda Handler API

### Function: `lambda_handler(event, context)`

**Description**: Main entry point for AWS Lambda triggered by S3 events.

**Parameters**:
- `event` (dict): AWS Lambda event from S3
- `context` (object): AWS Lambda context object

**Returns**:
```json
{
  "statusCode": 200,
  "body": "Document processing completed successfully"
}
```

**S3 Event Structure**:
```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "justicearch-inbox"
        },
        "object": {
          "key": "invoices/document-001.pdf"
        }
      }
    }
  ]
}
```

---

## Textract Processor API

### Class: `TextractProcessor`

#### Method: `extract_document_data(bucket_name, object_key)`

**Description**: Extract key information from document using Amazon Textract.

**Parameters**:
- `bucket_name` (str): S3 bucket name
- `object_key` (str): S3 object key/path

**Returns**:
```json
{
  "success": true,
  "data": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "vendor": "ACME Corporation",
    "date": "01/15/2024",
    "amount": "$1,234.56",
    "confidence_score": 92,
    "extraction_timestamp": "2024-01-15T10:30:00.000Z",
    "raw_text": "Full document text extracted by Textract"
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Error description"
}
```

---

## DynamoDB Handler API

### Class: `DynamoDBHandler`

#### Method: `save_document(document_record)`

**Description**: Save document record to DynamoDB.

**Parameters**:
- `document_record` (dict): Document data to save

```json
{
  "document_id": "uuid",
  "vendor": "string",
  "date": "string",
  "amount": "string",
  "confidence_score": 92,
  "status": "APPROVED",
  "s3_location": "s3://bucket/key",
  "raw_text": "string"
}
```

**Returns**:
```json
{
  "success": true,
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Method: `get_document(document_id)`

**Description**: Retrieve a single document by ID.

**Parameters**:
- `document_id` (str): Document ID

**Returns**:
```json
{
  "success": true,
  "data": { ... }  // Full document record
}
```

#### Method: `update_document(document_id, updates)`

**Description**: Update document fields.

**Parameters**:
- `document_id` (str): Document ID
- `updates` (dict): Fields to update

**Returns**:
```json
{
  "success": true,
  "data": { ... }  // Updated document
}
```

#### Method: `query_by_status(status)`

**Description**: Query all documents with specific status.

**Parameters**:
- `status` (str): Document status ('APPROVED' or 'NEED_REVIEW')

**Returns**:
```json
{
  "success": true,
  "data": [ ... ],  // Array of documents
  "count": 5
}
```

#### Method: `scan_all_documents()`

**Description**: Retrieve all documents from table.

**Returns**:
```json
{
  "success": true,
  "data": [ ... ],  // Array of all documents
  "count": 100
}
```

---

## Configuration API

### Class: `Config`

**Properties**:
- `AWS_REGION` (str): AWS region
- `S3_BUCKET_NAME` (str): S3 bucket name
- `DYNAMODB_TABLE_NAME` (str): DynamoDB table name
- `CONFIDENCE_THRESHOLD` (int): Confidence percentage (0-100)
- `TEXTRACT_MAX_RESULTS` (int): Max results from Textract
- `LOG_LEVEL` (str): Logging level

**Methods**:
- `validate()` → bool: Validate configuration
- `to_dict()` → dict: Convert to dictionary

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| AWS_REGION | us-east-1 | AWS region |
| S3_BUCKET_NAME | justicearch-inbox | S3 bucket for documents |
| DYNAMODB_TABLE_NAME | DocumentRecords | DynamoDB table name |
| CONFIDENCE_THRESHOLD | 80 | Confidence threshold (%) |
| TEXTRACT_MAX_RESULTS | 100 | Max results per request |
| LOG_LEVEL | INFO | Logging level |
| LAMBDA_TIMEOUT | 300 | Lambda timeout (seconds) |
| LAMBDA_MEMORY_SIZE | 512 | Lambda memory (MB) |

---

## Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| APPROVED | High confidence extraction | Auto-approved, skip review |
| NEED_REVIEW | Low confidence extraction | Requires manual review |

---

## Error Codes

| Code | Description | Resolution |
|------|-------------|-----------|
| InvalidParameterException | Invalid Textract parameters | Check document format and S3 location |
| UnsupportedDocumentException | Document format not supported | Use supported image/PDF formats |
| AccessDenied | IAM permission denied | Check role policies |
| ValidationException | Invalid input data | Verify input schema |
| ProvisionedThroughputExceededException | DynamoDB capacity exceeded | Increase write capacity |

---

## Example: Full Document Processing Flow

```python
# Initialize
textract_processor = TextractProcessor(textract_client)
dynamodb_handler = DynamoDBHandler()
config = Config()

# Extract from S3
extract_result = textract_processor.extract_document_data(
    'justicearch-inbox',
    'invoices/document-001.pdf'
)

if extract_result['success']:
    data = extract_result['data']
    
    # Determine status
    if data['confidence_score'] >= config.CONFIDENCE_THRESHOLD:
        data['status'] = 'APPROVED'
    else:
        data['status'] = 'NEED_REVIEW'
    
    # Save to DynamoDB
    save_result = dynamodb_handler.save_document(data)
    
    if save_result['success']:
        print(f"Document saved: {save_result['document_id']}")
```

---

## Integration Examples

### With Person 2 (Database Team)
```python
# Person 2 retrieves documents
documents = dynamodb_handler.query_by_status('APPROVED')

# Person 2 updates document status after user approval
dynamodb_handler.update_document(
    doc_id,
    {'status': 'APPROVED', 'reviewed_by': 'user123'}
)
```

### With Person 3 (Frontend Team)
```python
# Person 3 fetches documents for display
all_docs = dynamodb_handler.scan_all_documents()
review_items = dynamodb_handler.query_by_status('NEED_REVIEW')

# Person 3 displays in web portal
for doc in review_items['data']:
    print(f"{doc['vendor']} - {doc['amount']}")
```

### With Person 4 (DevOps Team)
```python
# Person 4 checks for low-confidence documents
low_conf = dynamodb_handler.query_by_status('NEED_REVIEW')

# Person 4 sends SNS notification
for doc in low_conf['data']:
    sns_client.publish(
        TopicArn=config.SNS_TOPIC_ARN,
        Subject=f"Document Review Required: {doc['document_id']}",
        Message=f"Vendor: {doc['vendor']}, Amount: {doc['amount']}"
    )
```

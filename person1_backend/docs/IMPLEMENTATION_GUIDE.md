# Person 1 Backend Implementation Guide

## Overview
This document provides technical details for implementing the backend document extraction pipeline using AWS Lambda, Textract, and DynamoDB.

## Project Structure

```
person1_backend/
├── lambda_function/
│   ├── lambda_handler.py          # Main Lambda entry point
│   ├── textract_processor.py      # Textract extraction logic
│   ├── dynamodb_handler.py        # DynamoDB operations
│   └── __init__.py
├── config/
│   ├── config.py                  # Configuration management
│   └── __init__.py
├── tests/
│   ├── test_lambda_handler.py     # Lambda tests
│   ├── test_textract_processor.py # Textract tests
│   └── __init__.py
├── docs/
│   ├── AWS_SETUP_GUIDE.md         # AWS setup instructions
│   ├── IMPLEMENTATION_GUIDE.md    # This file
│   └── API_REFERENCE.md           # (To be created)
└── requirements.txt               # Python dependencies
```

## Core Components

### 1. Lambda Handler (`lambda_handler.py`)

**Purpose**: Entry point for document processing pipeline

**Key Functions**:
- `lambda_handler(event, context)` - Main handler function triggered by S3 event
- `process_document(bucket_name, object_key)` - Process individual document

**Event Flow**:
```
S3 Upload Event
    ↓
Lambda Handler receives event
    ↓
Extract bucket and object key
    ↓
Call Textract processor
    ↓
Extract vendor, date, amount, confidence
    ↓
Determine status based on confidence threshold
    ↓
Save to DynamoDB
    ↓
Return success/error response
```

**Configuration**:
- Confidence Threshold: 80% (configurable)
- If confidence ≥ 80% → Status: `APPROVED`
- If confidence < 80% → Status: `NEED_REVIEW`

### 2. Textract Processor (`textract_processor.py`)

**Purpose**: Extract and parse document data using AWS Textract

**Key Functions**:
- `extract_document_data(bucket_name, object_key)` - Main extraction method
- `_extract_text_blocks(response)` - Extract raw text from Textract response
- `_parse_document_fields(raw_text, key_values)` - Parse structured fields
- `_extract_vendor(text, key_values)` - Extract vendor name
- `_extract_date(text, key_values)` - Extract document date
- `_extract_amount(text, key_values)` - Extract monetary amount
- `_calculate_confidence_score(response)` - Calculate overall confidence

**Extraction Logic**:

1. **Vendor Extraction**:
   - Check key-value pairs first (if using FORMS feature)
   - Look for keywords: 'vendor', 'company', 'supplier', 'from', 'bill from'
   - Fallback: Take first non-empty line in document

2. **Date Extraction**:
   - Check key-value pairs
   - Use regex patterns to find dates:
     - MM/DD/YYYY
     - YYYY-MM-DD
     - DD-MM-YYYY
   - Take first match found

3. **Amount Extraction**:
   - Check key-value pairs
   - Use regex patterns:
     - $1,234.56 format
     - 1234.56 format
   - Take last match (usually the total)

4. **Confidence Score**:
   - Collect confidence values from all LINE blocks
   - Return average confidence (0-100)

### 3. DynamoDB Handler (`dynamodb_handler.py`)

**Purpose**: Manage database operations for document records

**Key Functions**:
- `save_document(document_record)` - Save extracted document to DB
- `get_document(document_id)` - Retrieve single document
- `update_document(document_id, updates)` - Update document record
- `query_by_status(status)` - Query documents by status
- `scan_all_documents()` - Get all documents

**Document Schema**:
```json
{
  "document_id": "uuid",
  "vendor": "string",
  "date": "string (ISO 8601)",
  "amount": "string",
  "confidence_score": "number (0-100)",
  "status": "APPROVED | NEED_REVIEW",
  "s3_location": "s3://bucket/key",
  "raw_text": "string",
  "timestamp": "ISO 8601",
  "last_updated": "ISO 8601"
}
```

### 4. Configuration (`config.py`)

**Purpose**: Centralized configuration management

**Environment Variables**:
```
AWS_REGION                 # Default: us-east-1
S3_BUCKET_NAME            # Default: justicearch-inbox
DYNAMODB_TABLE_NAME       # Default: DocumentRecords
CONFIDENCE_THRESHOLD      # Default: 80
TEXTRACT_MAX_RESULTS      # Default: 100
LOG_LEVEL                 # Default: INFO
```

**Configuration Classes**:
- `Config` - Base configuration
- `DevelopmentConfig` - Development settings (confidence: 60%)
- `ProductionConfig` - Production settings (confidence: 80%)
- `TestingConfig` - Testing settings (confidence: 50%)

---

## Integration Points

### With Person 2 (Database)
- Person 1 writes documents to Person 2's DynamoDB table
- Requires table name: `DocumentRecords`
- Expected schema: document_id (PK), status, timestamp

### With Person 4 (DevOps/Integration)
- Documents with `status = NEED_REVIEW` are flagged for Person 4
- Person 4 sends SNS notifications for review items
- Person 4 implements S3 lifecycle rules for archiving

---

## Error Handling

**Error Types**:
1. **S3 Errors**: File not found, access denied, bucket missing
2. **Textract Errors**: Unsupported format, API rate limit, invalid parameters
3. **DynamoDB Errors**: Table not found, write capacity exceeded
4. **Processing Errors**: Regex failures, data parsing errors

**Response Format**:
```json
{
  "statusCode": 200 | 500,
  "body": "Success message or error details"
}
```

---

## Testing

### Unit Tests

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/test_textract_processor.py -v
```

### Integration Testing

Test with real S3 and Textract:
```bash
# Upload test PDF to S3
aws s3 cp sample-invoice.pdf s3://justicearch-inbox/invoices/

# Monitor Lambda logs
aws logs tail /aws/lambda/DocuProcessDocumentExtractor --follow

# Check DynamoDB for results
aws dynamodb scan --table-name DocumentRecords
```

---

## Performance Optimization

### Lambda Optimization
- **Memory**: 512 MB minimum (increase for large PDFs)
- **Timeout**: 300 seconds (5 minutes)
- **Concurrency**: Set reserved concurrency to avoid throttling

### Textract Optimization
- Process PDFs in batches if possible
- Use `AnalyzeDocument` for forms/tables (more expensive)
- Use `DetectDocumentText` for simple text extraction (cheaper)

### DynamoDB Optimization
- Create GSI on `status` and `timestamp` for queries
- Batch writes for multiple documents
- Use projection expressions to reduce data transfer

---

## Debugging Tips

### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

1. **Lambda not triggered by S3**
   - Check S3 event notification configuration
   - Verify Lambda permission allows S3 invocation
   - Check bucket name and object key filters

2. **Textract extraction errors**
   - Ensure PDF is readable and not corrupted
   - Check document is in supported format
   - Verify IAM role has Textract permissions

3. **DynamoDB write failures**
   - Verify table exists and name matches config
   - Check write capacity is sufficient
   - Ensure IAM role has DynamoDB:PutItem permission

4. **Confidence score too low**
   - Pre-process PDF quality (improve resolution)
   - Adjust regex patterns for field extraction
   - Lower confidence threshold in config

---

## Deliverables Checklist

- [x] Lambda function implementation
- [x] Textract integration
- [x] DynamoDB integration
- [x] Configuration management
- [x] Error handling
- [x] Unit tests
- [ ] AWS setup (see AWS_SETUP_GUIDE.md)
- [ ] GitHub code commit
- [ ] Slide appendix with setup steps
- [ ] Documentation review

---

## Next Phase: Integration with Other Teams

Once Person 2 (DynamoDB) is complete:
1. Test full document → Textract → DynamoDB pipeline
2. Verify data schema compatibility
3. Test confidence-based routing

Once Person 3 (EC2 Web App) is complete:
1. Test if Person 3 can retrieve and display documents
2. Verify approved documents appear in web UI
3. Test NEED_REVIEW filtering

Once Person 4 (DevOps) is complete:
1. Test SNS notifications for low-confidence documents
2. Test S3 lifecycle archiving
3. Full end-to-end pipeline testing

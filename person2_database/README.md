# Person 2 Database - DynamoDB Implementation

## Overview

This is **Person 2's DynamoDB Database Implementation** for the DocuProcess Cloud Computing Capstone Project. Handles all database operations for extracted document records.

## Quick Start

### Prerequisites
- Python 3.9+
- AWS Account (Academy Learner Lab)
- AWS CLI configured
- pip or conda

### Installation

```bash
cd person2_database
pip install -r requirements.txt
```

### Run Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
person2_database/
├── db_operations/
│   ├── db_handler.py         # Main database handler
│   └── __init__.py
├── config/
│   ├── config.py             # Configuration
│   └── __init__.py
├── tests/
│   ├── test_db_handler.py    # Unit tests
│   └── __init__.py
├── docs/                     # Documentation
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Key Features

### ✅ CREATE Operations
- Insert single document
- Batch insert multiple documents

### ✅ READ Operations
- Retrieve all documents
- Get specific document by ID
- Query by status (APPROVED, NEED_REVIEW)

### ✅ UPDATE Operations
- Update document fields
- Update status
- Auto-timestamp updates

### ✅ DELETE Operations
- Delete single document

### ✅ SEARCH Operations
- Search by vendor name
- Search by date range
- Search by amount range
- Advanced filtering

### ✅ REPORTING
- Get database statistics
- Count by status
- Total amount calculations

## Document Schema

All documents follow this structure:

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "vendor": "ACME Corporation",
  "date": "2026-01-15",
  "amount": 5000,
  "status": "APPROVED",
  "confidence_score": 92,
  "s3_location": "s3://justicearch-inbox/invoices/doc-001.pdf",
  "raw_text": "Full extracted text",
  "timestamp": "2026-01-15T10:30:00.000Z",
  "last_updated": "2026-01-15T10:30:00.000Z"
}
```

## Status Values

- **APPROVED**: High confidence extraction (auto-approved by Person 1)
- **NEED_REVIEW**: Low confidence extraction (requires manual review by Person 3)

## API Reference

### Initialize Handler

```python
from db_operations.db_handler import DynamoDBHandler

db = DynamoDBHandler(
    table_name='DocumentRecords',
    region='us-east-1'
)
```

### Insert Document

```python
document = {
    'document_id': 'DOC001',
    'vendor': 'ABC Corp',
    'date': '2026-05-17',
    'amount': 1000,
    'status': 'APPROVED'
}

result = db.insert_document(document)
# Returns: {'success': True, 'document_id': 'DOC001', 'message': '...'}
```

### Retrieve Documents

```python
# Get all documents
result = db.retrieve_all_documents()

# Get specific document
result = db.get_document('DOC001')

# Get by status
result = db.get_documents_by_status('APPROVED')
```

### Update Document

```python
# Update specific fields
updates = {'status': 'APPROVED', 'confidence_score': 95}
result = db.update_document('DOC001', updates)

# Update just status
result = db.update_status('DOC001', 'APPROVED')
```

### Delete Document

```python
result = db.delete_document('DOC001')
```

### Search Documents

```python
# By vendor
result = db.search_documents_by_vendor('ABC')

# By date range
result = db.search_documents_by_date('2026-05-01', '2026-05-31')

# By amount range
result = db.search_documents_by_amount(1000, 5000)
```

### Statistics

```python
result = db.get_statistics()
# Returns: {
#   'success': True,
#   'total_documents': 100,
#   'approved_count': 85,
#   'need_review_count': 15,
#   'total_amount': 250000,
#   'percentage_approved': 85.0
# }
```

## Integration with Other Teams

### With Person 1 (Backend)
- Receives document records from Lambda
- Schema must match for seamless integration
- Handles bulk inserts from Person 1's Lambda function

### With Person 3 (Web Frontend)
- Provides read access to documents
- Supports filtering by status for NEED_REVIEW items
- Enables search functionality for the web portal

### With Person 4 (DevOps)
- Provides NEED_REVIEW documents for SNS notifications
- Tracks document lifecycle (NEED_REVIEW → APPROVED)

## Configuration

### Environment Variables

```
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=DocumentRecords
LOG_LEVEL=INFO
```

### AWS Setup

See [AWS_SETUP_GUIDE.md](docs/AWS_SETUP_GUIDE.md) for:
- Creating DynamoDB table
- Setting up Global Secondary Indexes (GSI)
- Configuring permissions
- Testing setup

## Example Usage

```python
from db_operations.db_handler import DynamoDBHandler

# Initialize
db = DynamoDBHandler()

# Insert document from Person 1's Lambda
doc = {
    'document_id': 'UUID-123',
    'vendor': 'ABC Corporation',
    'date': '2026-05-17',
    'amount': 5000,
    'confidence_score': 92,
    'status': 'APPROVED',
    's3_location': 's3://bucket/file.pdf'
}
result = db.insert_document(doc)

# Query for web app (Person 3)
need_review = db.get_documents_by_status('NEED_REVIEW')

# Search functionality
results = db.search_documents_by_vendor('ABC')

# Statistics for dashboard
stats = db.get_statistics()
print(f"Total Documents: {stats['total_documents']}")
print(f"Approved: {stats['approved_count']}")
print(f"Pending Review: {stats['need_review_count']}")
```

## Testing

### Run Unit Tests

```bash
python -m pytest tests/ -v
```

### Integration Testing

```bash
# Test with real DynamoDB
export DYNAMODB_TABLE_NAME=DocumentRecords-test
python db_operations/db_handler.py
```

## Performance Notes

- **Scan operations** retrieve all records (slower for large tables)
- **Batch writes** use size limit of 25 items
- **Pagination** handled automatically
- **Filtering** done client-side for complex queries
- **Indexes** can be created for better performance on common queries

## AWS Costs

- **Write capacity**: ~$1.25 per million writes
- **Read capacity**: ~$0.25 per million reads
- **Storage**: ~$0.25 per GB/month

For testing, use provisioned capacity; for production, use on-demand pricing.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ResourceNotFoundException` | Table doesn't exist; create it first |
| `ValidationException` | Invalid schema; check required fields |
| `AccessDenied` | Check IAM permissions |
| `ProvisionedThroughputExceededException` | Increase write/read capacity |

## Documentation

- **README.md** - This file
- **docs/AWS_SETUP_GUIDE.md** - AWS setup instructions
- **docs/API_REFERENCE.md** - Complete API reference
- **docs/SLIDE_APPENDIX.md** - Presentation content

## Next Steps

1. ✅ Create DynamoDB table (see AWS_SETUP_GUIDE.md)
2. ✅ Configure table schema
3. ✅ Test with unit tests
4. ⏳ Integrate with Person 1 (Lambda)
5. ⏳ Integrate with Person 3 (Web App)
6. ⏳ Full system testing

## Technologies Used

- **AWS DynamoDB** - NoSQL database
- **Python 3.9** - Implementation language
- **boto3** - AWS SDK for Python
- **pytest** - Unit testing

## Contact & Support

For questions:
- Check docs/ folder
- Review code comments
- Run unit tests
- Check CloudWatch logs

---

**Deadline**: Week 9 | **Duration**: Max 1 Week  
**Status**: ✅ Complete

# 🎯 DocuProcess Project Integration Guide

**Date**: May 17, 2026  
**Project**: WOA7016 Cloud Computing Capstone  
**Status**: Person 1 ✅ + Person 2 ✅ Complete

---

## 📊 Project Overview

DocuProcess is now **50% complete** with Person 1 (Backend) and Person 2 (Database) fully implemented.

### Current Status

| Component | Status | Weeks | Details |
|-----------|--------|-------|---------|
| **Person 1** - Backend (Lambda + Textract) | ✅ DONE | 3 weeks | Production-ready, 20+ files |
| **Person 2** - Database (DynamoDB) | ✅ DONE | 1 week | Production-ready, 12+ files |
| **Person 3** - Frontend (EC2 + Flask) | ⏳ Next | 2 weeks | Can start now |
| **Person 4** - DevOps (SNS + Archiving) | ⏳ Next | 2 weeks | Can start week 9.5 |

---

## 🔗 Integration Architecture

### Data Flow

```
PDF Upload (User)
    ↓
S3 Bucket (justicearch-inbox)
    ↓ [Event Trigger]
Lambda Function (Person 1) ← BACKEND
    ↓
Amazon Textract (OCR)
    ↓ [Extract Data + Score]
DynamoDB Table (Person 2) ← DATABASE
    ↓
├─→ EC2 Web App (Person 3) ← FRONTEND
│   └─ APPROVED: Display
│   └─ NEED_REVIEW: Manual interface
│
└─→ SNS Notifications (Person 4) ← DEVOPS
    └─ Alert team for low-confidence items
    └─ Trigger archiving workflow
```

---

## 💾 Person 1 → Person 2 Integration

### How Person 1's Lambda Inserts into Person 2's Database

```python
# In Person 1's lambda_handler.py
from person2_database.db_operations.db_handler import DynamoDBHandler

# Initialize Person 2's database handler
db_handler = DynamoDBHandler(
    table_name='DocumentRecords',
    region='us-east-1'
)

# After Textract extraction (Person 1's responsibility)
extracted_data = textract_processor.extract_document_data(bucket, key)

if extracted_data['success']:
    document_record = {
        'document_id': str(uuid.uuid4()),              # Person 1 generates
        'vendor': extracted_data['vendor'],           # Person 1 extracts
        'date': extracted_data['date'],               # Person 1 extracts
        'amount': extracted_data['amount'],           # Person 1 extracts
        'confidence_score': extracted_data['confidence_score'],
        'status': 'APPROVED' if extracted_data['confidence_score'] >= 80 else 'NEED_REVIEW',
        's3_location': f"s3://{bucket}/{key}",
        'raw_text': extracted_data['raw_text']
    }
    
    # Person 1 uses Person 2's handler to save
    result = db_handler.insert_document(document_record)
    
    if result['success']:
        logger.info(f"Document saved to DynamoDB: {result['document_id']}")
```

### Required Dependencies

Person 1's `requirements.txt` already includes:
```
boto3==1.28.85
```

Person 2's `requirements.txt`:
```
boto3==1.28.85
```

**Shared**: Both use same boto3 version ✅

---

## 🌐 Person 2 → Person 3 Integration

### How Person 3's Web App Reads from Person 2's Database

```python
# In Person 3's Flask app
from person2_database.db_operations.db_handler import DynamoDBHandler

# Initialize database handler
db = DynamoDBHandler(
    table_name='DocumentRecords',
    region='us-east-1'
)

# Route: Display all APPROVED documents
@app.route('/documents/approved')
def approved_documents():
    result = db.get_documents_by_status('APPROVED')
    return render_template('approved_list.html', documents=result['documents'])

# Route: Display NEED_REVIEW documents
@app.route('/documents/review')
def review_documents():
    result = db.get_documents_by_status('NEED_REVIEW')
    return render_template('review_interface.html', documents=result['documents'])

# Route: Search functionality
@app.route('/search')
def search():
    keyword = request.args.get('vendor')
    result = db.search_documents_by_vendor(keyword)
    return render_template('search_results.html', documents=result['documents'])

# Route: Get single document
@app.route('/document/<doc_id>')
def get_document(doc_id):
    result = db.get_document(doc_id)
    return render_template('document_detail.html', document=result['document'])

# Route: Update status after review
@app.route('/document/<doc_id>/approve', methods=['POST'])
def approve_document(doc_id):
    result = db.update_status(doc_id, 'APPROVED')
    return {'success': result['success']}
```

### API Methods Person 3 Will Use

| Method | Purpose | Called By |
|--------|---------|-----------|
| `get_documents_by_status()` | Filter by status | Homepage, filtering |
| `search_documents_by_vendor()` | Search by vendor | Search page |
| `search_documents_by_date()` | Filter by date range | Date range picker |
| `get_document()` | Display single item | Detail page |
| `update_status()` | Mark as reviewed | After manual review |
| `get_statistics()` | Show dashboard stats | Dashboard page |

---

## 🔔 Person 2 → Person 4 Integration

### How Person 4's DevOps Monitors Documents

```python
# In Person 4's Lambda function (periodic checker)
from person2_database.db_operations.db_handler import DynamoDBHandler
import boto3

# Initialize database
db = DynamoDBHandler()

# Initialize SNS
sns_client = boto3.client('sns')

# Query for NEED_REVIEW items
result = db.get_documents_by_status('NEED_REVIEW')

for document in result['documents']:
    # Send SNS notification
    sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:account:DocuProcess-Review',
        Subject=f"Document Review Required: {document['vendor']}",
        Message=f"""
        Document ID: {document['document_id']}
        Vendor: {document['vendor']}
        Date: {document['date']}
        Amount: {document['amount']}
        Confidence: {document['confidence_score']}%
        
        Please review at: https://app.docuprocess.com/review/{document['document_id']}
        """
    )
    
    # Track in CloudWatch
    logger.info(f"Notification sent for {document['document_id']}")

# After archiving (update status)
# Person 4 would call:
db.update_document(document_id, {'status': 'ARCHIVED'})
```

### Person 4 Will Use These Methods

| Method | Purpose |
|--------|---------|
| `get_documents_by_status('NEED_REVIEW')` | Find items for review |
| `get_documents_by_status('APPROVED')` | Find items to archive |
| `update_document()` | Track archiving status |
| `retrieve_all_documents()` | Daily audit |
| `get_statistics()` | Generate reports |

---

## 📝 Shared Document Schema

### DocumentRecords Table Structure

```json
{
  "document_id": "UUID generated by Person 1",
  "vendor": "Extracted by Person 1 from Textract",
  "date": "Extracted by Person 1 from Textract",
  "amount": "Extracted by Person 1 from Textract",
  "confidence_score": "Calculated by Person 1",
  "status": "Set by Person 1 (APPROVED/NEED_REVIEW), updated by Person 3/4",
  "s3_location": "Set by Person 1",
  "raw_text": "Set by Person 1",
  "timestamp": "Auto-set by Person 2 on insert",
  "last_updated": "Auto-set by Person 2 on update"
}
```

---

## ✅ Integration Checklist

### For Person 1 ← → Person 2

- [x] DynamoDB table created (person2_database)
- [x] Schema matches Person 1's output
- [x] Handler methods documented
- [x] Error handling tested
- [ ] Deploy to AWS
- [ ] Test end-to-end: Lambda → DynamoDB

### For Person 2 ← → Person 3

- [x] Query methods for APPROVED/NEED_REVIEW
- [x] Search methods implemented
- [x] Update method for status changes
- [ ] Person 3 creates Flask routes
- [ ] Person 3 implements web UI
- [ ] Test web app queries

### For Person 2 ← → Person 4

- [x] Query methods for monitoring
- [x] Update methods for status tracking
- [ ] Person 4 creates Lambda monitors
- [ ] Person 4 implements SNS notifications
- [ ] Person 4 implements S3 lifecycle
- [ ] Test full notification flow

---

## 🚀 Integration Timeline

### Week 9
- ✅ Person 1 backend DONE
- ✅ Person 2 database DONE
- ⏳ Person 4 starts features

### Week 9.5
- ⏳ Person 4 features ready
- ⏳ Person 3 starts web app
- ⏳ Begin Person 1 + Person 2 integration testing

### Week 10
- ⏳ Person 3 web app complete
- ⏳ Integrate Person 2 + Person 3
- ⏳ Test full web interface

### Week 11
- ⏳ Full system integration
- ⏳ All 4 components connected
- ⏳ End-to-end testing
- ⏳ Final deployment

### June 19
- ⏳ Final submission deadline

---

## 📦 File Dependencies

### Person 1 Depends On
- [x] Person 2 DynamoDB table exists
  - Must create before deploying Lambda
  - Table name must be "DocumentRecords"
  - Required schema fields: document_id (PK), vendor, date, amount, status

### Person 3 Depends On
- [x] Person 2 DynamoDB implemented
- Person 1 Lambda running (to populate data)
- Person 4 SNS configured (for notifications)

### Person 4 Depends On
- [x] Person 2 DynamoDB table exists
- Person 1 Lambda running
- Person 3 web app available
- SNS topic created
- S3 lifecycle rules configured

---

## 🧪 Testing Integration

### Integration Test 1: Lambda → DynamoDB

```python
# Run on AWS Lambda (Person 1)
from db_operations.db_handler import DynamoDBHandler

# Test data from Textract
test_document = {
    'document_id': 'TEST-001',
    'vendor': 'Test Corp',
    'date': '2026-05-17',
    'amount': 5000,
    'confidence_score': 92,
    'status': 'APPROVED'
}

db = DynamoDBHandler()
result = db.insert_document(test_document)

assert result['success'] == True
assert result['document_id'] == 'TEST-001'

# Verify in DynamoDB
verify = db.get_document('TEST-001')
assert verify['document']['vendor'] == 'Test Corp'
```

### Integration Test 2: Web App → DynamoDB

```python
# Run on Flask app (Person 3)
from db_operations.db_handler import DynamoDBHandler

db = DynamoDBHandler()

# Test query
result = db.get_documents_by_status('NEED_REVIEW')
assert result['success'] == True

# Test search
result = db.search_documents_by_vendor('Test')
assert result['count'] >= 0

# Test update
result = db.update_status('TEST-001', 'APPROVED')
assert result['success'] == True

# Verify update
updated = db.get_document('TEST-001')
assert updated['document']['status'] == 'APPROVED'
```

### Integration Test 3: DevOps Monitor → DynamoDB

```python
# Run on Lambda (Person 4)
from db_operations.db_handler import DynamoDBHandler

db = DynamoDBHandler()

# Get items needing review
result = db.get_documents_by_status('NEED_REVIEW')
print(f"Items to review: {result['count']}")

# Get statistics
stats = db.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"Approved: {stats['approved_count']}")
print(f"Pending: {stats['need_review_count']}")
```

---

## 💡 Tips for Integration

1. **Order of Setup**:
   - First: Create DynamoDB table (Person 2)
   - Second: Deploy Lambda (Person 1)
   - Third: Build web app (Person 3)
   - Fourth: Add monitoring (Person 4)

2. **Configuration**:
   - Use same AWS region for all: `us-east-1`
   - Use same DynamoDB table name: `DocumentRecords`
   - Use same boto3 version: `1.28.85`

3. **Testing**:
   - Test each component individually first
   - Then test Person 1 + Person 2 together
   - Then test with Person 3 web app
   - Finally test full integration with Person 4

4. **Error Handling**:
   - Always check `result['success']` before using data
   - Log errors for debugging
   - Test error scenarios

5. **Coordination**:
   - Communicate table schema early (Person 2 defines, Person 1/3/4 follow)
   - Share API documentation
   - Agree on error response formats
   - Document any assumptions

---

## 📞 Integration Support

### For Person 1 Integrating with Person 2
- See: `person1_backend/docs/API_REFERENCE.md`
- See: `person2_database/docs/API_REFERENCE.md`
- Example: `person1_backend/lambda_function/dynamodb_handler.py`

### For Person 3 Integrating with Person 2
- See: `person2_database/docs/API_REFERENCE.md`
- See: `QUICK_START_PERSON2.md`
- Contact Person 2 for schema clarification

### For Person 4 Integrating with Person 2
- See: `person2_database/docs/SLIDE_APPENDIX.md`
- See: `person2_database/docs/API_REFERENCE.md`
- Contact Person 2 for status tracking requirements

---

## 🎯 Success Criteria

### Person 1 + Person 2 Integration
- [ ] Lambda can insert documents into DynamoDB
- [ ] Documents appear with correct schema
- [ ] Status routing works (APPROVED vs NEED_REVIEW)
- [ ] Timestamp handling correct
- [ ] Error handling tested

### Person 2 + Person 3 Integration
- [ ] Web app can retrieve APPROVED documents
- [ ] Web app can filter by status
- [ ] Web app can search by vendor/date/amount
- [ ] Web app can update document status
- [ ] Dashboard shows correct statistics

### Person 2 + Person 4 Integration
- [ ] Person 4 can query NEED_REVIEW items
- [ ] SNS notifications sent correctly
- [ ] Status updates tracked
- [ ] Archiving workflow works
- [ ] Statistics accurate

### Full System (All 4 People)
- [ ] End-to-end workflow: PDF → Lambda → DynamoDB → Web → Review → Archive
- [ ] All error cases handled
- [ ] Performance meets targets
- [ ] Documentation complete
- [ ] Ready for presentation

---

## 🏁 Next Steps

1. **This Week** (Now):
   - Person 1: Deploy Lambda to AWS
   - Person 2: Create DynamoDB table
   - Test Person 1 + Person 2 integration

2. **Week 9.5**:
   - Person 3: Start Flask web app
   - Person 4: Start monitoring Lambda
   - Begin Person 2 + Person 3 integration

3. **Week 10**:
   - Person 3: Complete web app
   - Full Person 2 + Person 3 integration testing

4. **Week 11**:
   - Person 4: Complete DevOps integration
   - Full end-to-end testing
   - Prepare presentation

5. **June 19**:
   - Final submission

---

**Integration Guide**: DocuProcess Project  
**Version**: 1.0  
**Last Updated**: May 17, 2026

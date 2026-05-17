# Person 2 Database - Quick Start

## 🚀 5-Minute Quick Start

### 1. Install Dependencies
```bash
cd person2_database
pip install -r requirements.txt
```

### 2. Run Unit Tests
```bash
python -m pytest tests/ -v
```

### 3. Create DynamoDB Table

**Automated (Recommended)**:
```bash
# Follow docs/AWS_SETUP_GUIDE.md
aws dynamodb create-table \
  --table-name DocumentRecords \
  --attribute-definitions AttributeName=document_id,AttributeType=S \
  --key-schema AttributeName=document_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 4. Test Database Locally

```bash
# Run demo script
python db_operations/db_handler.py
```

Output:
```
==================================================
DocuProcess DynamoDB Handler Demo
==================================================

1. Inserting sample document...
   Result: {'success': True, 'document_id': 'DOC001', ...}
   
2. Retrieving all documents (before update)...
   {'document_id': 'DOC001', 'vendor': 'ABC Sdn Bhd', ...}
   
...
```

## 📚 Documentation

Start with these in order:

1. **README.md** - Overview
2. **docs/AWS_SETUP_GUIDE.md** - AWS configuration
3. **docs/API_REFERENCE.md** - API documentation
4. **docs/IMPLEMENTATION_GUIDE.md** - Technical details

## 🔧 Common Tasks

### Insert Document
```python
from db_operations.db_handler import DynamoDBHandler

db = DynamoDBHandler()

result = db.insert_document({
    'document_id': 'DOC-001',
    'vendor': 'ACME Corp',
    'date': '2026-05-17',
    'amount': 5000,
    'status': 'APPROVED'
})
```

### Query Documents
```python
# Get by status
approved = db.get_documents_by_status('APPROVED')

# Get all
all_docs = db.retrieve_all_documents()

# Search
results = db.search_documents_by_vendor('ACME')
```

### Update Status
```python
db.update_status('DOC-001', 'APPROVED')
```

### Get Statistics
```python
stats = db.get_statistics()
print(f"Total: {stats['total_documents']}")
print(f"Approved: {stats['approved_count']}")
print(f"Pending: {stats['need_review_count']}")
```

## ⚙️ Configuration

### Environment Variables
```bash
export AWS_REGION=us-east-1
export DYNAMODB_TABLE_NAME=DocumentRecords
export LOG_LEVEL=INFO
```

### Table Schema
```
document_id (PK)    ← Unique identifier
vendor              ← Company name
date                ← Document date (YYYY-MM-DD)
amount              ← Document amount
status              ← APPROVED | NEED_REVIEW
confidence_score    ← 0-100
timestamp           ← Creation time (ISO 8601)
last_updated        ← Last modification time
```

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test
```bash
python -m pytest tests/test_db_handler.py::TestDynamoDBHandler::test_insert_document_success -v
```

## 📁 File Structure

```
person2_database/
├── db_operations/
│   ├── db_handler.py         ← Main implementation
│   └── __init__.py
├── config/
│   ├── config.py
│   └── __init__.py
├── tests/
│   ├── test_db_handler.py
│   └── __init__.py
├── docs/
│   ├── AWS_SETUP_GUIDE.md
│   ├── API_REFERENCE.md
│   ├── IMPLEMENTATION_GUIDE.md
│   └── SLIDE_APPENDIX.md
├── requirements.txt
└── README.md
```

## 🔗 Next Steps

1. ✅ Install dependencies
2. ✅ Run tests
3. ✅ Create DynamoDB table
4. ✅ Test with sample data
5. ⏳ Integrate with Person 1 (Lambda)
6. ⏳ Integrate with Person 3 (Web App)
7. ⏳ Coordinate with Person 4 (DevOps)

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'boto3'` | Run `pip install -r requirements.txt` |
| `ResourceNotFoundException` | Create DynamoDB table first |
| `ValidationException` | Check required fields are present |
| Permission denied | Check AWS credentials and IAM role |

## 💡 Pro Tips

1. **Start with pay-per-request** billing for testing
2. **Use batch operations** for bulk inserts from Person 1
3. **Enable PITR backup** for data protection
4. **Monitor CloudWatch metrics** for performance
5. **Test before deploying** to production

## 📞 Support

- Check docs/ for detailed guides
- Review code comments in db_operations/
- Run tests to validate functionality
- Check AWS CloudWatch for errors

---

**Duration**: Max 1 Week | **Deadline**: Week 9

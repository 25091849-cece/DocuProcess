# Person 2 - DynamoDB API Reference

## DynamoDBHandler Class

### Initialization

```python
from db_operations.db_handler import DynamoDBHandler

db = DynamoDBHandler(
    table_name='DocumentRecords',  # Default: DocumentRecords
    region='us-east-1'              # Default: us-east-1
)
```

## CREATE Operations

### `insert_document(document: Dict[str, Any]) → Dict[str, Any]`

Insert a single document.

**Parameters**:
- `document` (dict): Document data
  - **Required**: `document_id`, `vendor`, `date`, `amount`, `status`

**Example**:
```python
result = db.insert_document({
    'document_id': 'DOC-001',
    'vendor': 'ACME Corp',
    'date': '2026-05-17',
    'amount': 5000,
    'status': 'APPROVED',
    'confidence_score': 92
})

# Returns:
# {
#   'success': True,
#   'message': 'Document DOC-001 inserted',
#   'document_id': 'DOC-001'
# }
```

### `insert_multiple_documents(documents: List[Dict[str, Any]]) → Dict[str, Any]`

Insert multiple documents in batch (max 25 per batch).

**Parameters**:
- `documents` (list): List of document dictionaries

**Example**:
```python
docs = [
    {
        'document_id': 'DOC-001',
        'vendor': 'Vendor A',
        'date': '2026-05-17',
        'amount': 1000,
        'status': 'APPROVED'
    },
    {
        'document_id': 'DOC-002',
        'vendor': 'Vendor B',
        'date': '2026-05-17',
        'amount': 2000,
        'status': 'NEED_REVIEW'
    }
]

result = db.insert_multiple_documents(docs)

# Returns:
# {
#   'success': True,
#   'count': 2,
#   'message': '2 documents inserted'
# }
```

## READ Operations

### `retrieve_all_documents() → Dict[str, Any]`

Get all documents from table.

**Returns**:
```python
{
    'success': True,
    'count': 100,
    'documents': [
        {
            'document_id': 'DOC-001',
            'vendor': 'ACME',
            'date': '2026-05-17',
            'amount': 5000,
            'status': 'APPROVED',
            'timestamp': '2026-05-17T10:30:00Z'
        },
        ...
    ]
}
```

### `get_document(document_id: str) → Dict[str, Any]`

Get a specific document by ID.

**Parameters**:
- `document_id` (str): Document ID

**Example**:
```python
result = db.get_document('DOC-001')

# Success:
# {
#   'success': True,
#   'document': {...}
# }

# Not found:
# {
#   'success': False,
#   'error': 'Document not found'
# }
```

### `get_documents_by_status(status: str) → Dict[str, Any]`

Get all documents with specific status.

**Parameters**:
- `status` (str): 'APPROVED' or 'NEED_REVIEW'

**Example**:
```python
result = db.get_documents_by_status('NEED_REVIEW')

# Returns:
# {
#   'success': True,
#   'status': 'NEED_REVIEW',
#   'count': 15,
#   'documents': [...]
# }
```

## UPDATE Operations

### `update_document(document_id: str, updates: Dict[str, Any]) → Dict[str, Any]`

Update specific fields in a document.

**Parameters**:
- `document_id` (str): Document ID
- `updates` (dict): Fields to update

**Example**:
```python
result = db.update_document('DOC-001', {
    'status': 'APPROVED',
    'confidence_score': 95,
    'reviewed_by': 'user123'
})

# Returns:
# {
#   'success': True,
#   'message': 'Document DOC-001 updated',
#   'document': {...updated document...}
# }
```

### `update_status(document_id: str, new_status: str) → Dict[str, Any]`

Update only the status field (convenience method).

**Parameters**:
- `document_id` (str): Document ID
- `new_status` (str): 'APPROVED' or 'NEED_REVIEW'

**Example**:
```python
result = db.update_status('DOC-001', 'APPROVED')
```

## DELETE Operations

### `delete_document(document_id: str) → Dict[str, Any]`

Delete a document.

**Parameters**:
- `document_id` (str): Document ID

**Example**:
```python
result = db.delete_document('DOC-001')

# Returns:
# {
#   'success': True,
#   'message': 'Document DOC-001 deleted'
# }
```

## SEARCH Operations

### `search_documents_by_vendor(keyword: str) → Dict[str, Any]`

Search documents by vendor name (case-insensitive).

**Parameters**:
- `keyword` (str): Vendor name to search for

**Example**:
```python
result = db.search_documents_by_vendor('ABC')

# Returns:
# {
#   'success': True,
#   'keyword': 'ABC',
#   'count': 5,
#   'documents': [...]
# }
```

### `search_documents_by_date(start_date: str, end_date: str) → Dict[str, Any]`

Search documents by date range.

**Parameters**:
- `start_date` (str): Start date (YYYY-MM-DD)
- `end_date` (str): End date (YYYY-MM-DD)

**Example**:
```python
result = db.search_documents_by_date('2026-05-01', '2026-05-31')

# Returns:
# {
#   'success': True,
#   'start_date': '2026-05-01',
#   'end_date': '2026-05-31',
#   'count': 50,
#   'documents': [...]
# }
```

### `search_documents_by_amount(min_amount: float, max_amount: float) → Dict[str, Any]`

Search documents by amount range.

**Parameters**:
- `min_amount` (float): Minimum amount
- `max_amount` (float): Maximum amount

**Example**:
```python
result = db.search_documents_by_amount(1000, 5000)

# Returns:
# {
#   'success': True,
#   'min_amount': 1000,
#   'max_amount': 5000,
#   'count': 25,
#   'documents': [...]
# }
```

## STATISTICS & REPORTING

### `get_statistics() → Dict[str, Any]`

Get overall database statistics.

**Returns**:
```python
{
    'success': True,
    'total_documents': 100,
    'approved_count': 85,
    'need_review_count': 15,
    'total_amount': 250000,
    'percentage_approved': 85.0
}
```

## Response Format

All methods return a consistent response structure:

### Success Response
```json
{
    "success": true,
    "message": "Operation description",
    "data": {...}  // Optional, operation-specific
}
```

### Error Response
```json
{
    "success": false,
    "error": "Error description"
}
```

## Complete Example

```python
from db_operations.db_handler import DynamoDBHandler

# Initialize
db = DynamoDBHandler('DocumentRecords', 'us-east-1')

# 1. Insert document from Person 1 Lambda
document = {
    'document_id': 'DOC-12345',
    'vendor': 'ABC Corporation',
    'date': '2026-05-17',
    'amount': 5000,
    'confidence_score': 92,
    'status': 'APPROVED',
    's3_location': 's3://bucket/doc.pdf',
    'raw_text': 'Full extracted text...'
}
result = db.insert_document(document)
print(f"Inserted: {result['document_id']}")

# 2. Query for Person 3 (Web App)
need_review = db.get_documents_by_status('NEED_REVIEW')
print(f"Documents needing review: {need_review['count']}")

# 3. Search functionality for web portal
results = db.search_documents_by_vendor('ABC')
print(f"Found {results['count']} documents")

# 4. Person 3 updates after manual review
db.update_status('DOC-12345', 'APPROVED')

# 5. Get statistics for dashboard
stats = db.get_statistics()
print(f"Total: {stats['total_documents']}")
print(f"Approved: {stats['approved_count']}")
print(f"Pending: {stats['need_review_count']}")
```

## Error Handling

```python
result = db.insert_document(invalid_doc)

if not result['success']:
    print(f"Error: {result['error']}")
    # Handle error
else:
    print(f"Success: {result['message']}")
```

## Pagination

Large result sets are handled automatically with pagination:

```python
# Automatically handles pagination
result = db.retrieve_all_documents()

# Access all items
for doc in result['documents']:
    print(doc)
```

## Performance Tips

1. **Batch operations** for multiple inserts
2. **Use GSI** for frequent queries by status
3. **Limit scan results** when possible
4. **Client-side filtering** for complex searches
5. **Index optimization** for production

---

**Document**: DynamoDB API Reference  
**Version**: 1.0  
**Deadline**: Week 9

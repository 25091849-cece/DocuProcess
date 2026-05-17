# Person 2 - Slide Appendix Content

## Slide 1: Database Architecture

**Title**: DynamoDB Design for Document Processing

### Content:

**Why DynamoDB?**
- Fully managed (no server management)
- Automatically scales
- Pay-per-request or provisioned capacity
- Built-in security
- Global Tables for multi-region

**Table Design**:
- **Table Name**: `DocumentRecords`
- **Primary Key**: `document_id` (String)
- **Billing**: Pay-per-request (flexible)

**Key Attributes**:
```
document_id (PK)    → Unique identifier
vendor              → Company name
date                → Document date
amount              → Document amount
status              → APPROVED / NEED_REVIEW
confidence_score    → AI confidence (0-100)
timestamp           → Record creation time
```

---

## Slide 2: Table Schema

**Title**: Document Record Structure in DynamoDB

### Schema Diagram:

```
DocumentRecords Table
├── Attributes:
│   ├── document_id (String, PK)
│   ├── vendor (String)
│   ├── date (String)
│   ├── amount (Number)
│   ├── status (String)
│   ├── confidence_score (Number)
│   ├── s3_location (String)
│   ├── raw_text (String)
│   ├── timestamp (String)
│   └── last_updated (String)
│
├── Global Secondary Indexes:
│   └── status-timestamp-index
│       ├── Partition Key: status
│       └── Sort Key: timestamp
│
└── Billing Mode:
    └── PAY_PER_REQUEST
```

**Data Types**:
- String (S)
- Number (N)
- Binary (B)
- List
- Map

---

## Slide 3: CRUD Operations

**Title**: Create, Read, Update, Delete Operations

### Operations Overview:

**CREATE** (Insert):
```python
db.insert_document({...})
db.insert_multiple_documents([...])
```

**READ** (Retrieve):
```python
db.get_document('DOC-001')
db.retrieve_all_documents()
db.get_documents_by_status('APPROVED')
```

**UPDATE** (Modify):
```python
db.update_document('DOC-001', {...})
db.update_status('DOC-001', 'APPROVED')
```

**DELETE** (Remove):
```python
db.delete_document('DOC-001')
```

---

## Slide 4: Search & Query Capabilities

**Title**: Advanced Search and Filtering

### Search Features:

**1. By Vendor Name**
```python
db.search_documents_by_vendor('ABC Corporation')
```
- Case-insensitive matching
- Partial name matching supported

**2. By Date Range**
```python
db.search_documents_by_date('2026-05-01', '2026-05-31')
```
- Useful for monthly reports
- Financial period analysis

**3. By Amount Range**
```python
db.search_documents_by_amount(1000, 5000)
```
- Find high-value invoices
- Budget tracking

**4. By Status**
```python
db.get_documents_by_status('NEED_REVIEW')
```
- Separate review items
- Track approval progress

---

## Slide 5: Database Indexing Strategy

**Title**: Global Secondary Indexes (GSI)

### GSI for Status Queries:

```
Primary Index (Scan):
- Scan entire table O(n)
- Slow for large datasets
- Expensive read operations

Global Secondary Index (Query):
- Query by status instantly O(1)
- Fast filtered results
- Efficient for common queries
```

**GSI Configuration**:
- **Index Name**: `status-timestamp-index`
- **Partition Key**: `status`
- **Sort Key**: `timestamp`
- **Projection**: ALL (copy all attributes)

**Benefits**:
- Fast status filtering
- Enable time-series queries
- Support Person 3's web app queries

---

## Slide 6: Data Flow & Integration

**Title**: Database Integration with Other Components

### Data Flow:

```
Person 1 (Lambda)
    ↓
Insert Document
    ↓
DynamoDB DocumentRecords Table
    ↓
├─→ Person 3 (Web App)
│   └─ Retrieve & Display
│
├─→ Person 4 (DevOps)
│   └─ Monitor NEED_REVIEW
│
└─→ Analytics/Reporting
    └─ Statistics & Insights
```

**Integration Points**:

| Component | Operation | Frequency |
|-----------|-----------|-----------|
| Person 1 | INSERT | Per PDF uploaded |
| Person 3 | QUERY/SCAN | Per web request |
| Person 4 | SCAN | Periodic check |
| Analytics | STATISTICS | Daily/Weekly |

---

## Slide 7: Performance & Scalability

**Title**: Scaling the Database

### Capacity Options:

**Development (Pay-per-Request)**
- $0.25 per million reads
- $1.25 per million writes
- Good for variable traffic
- No capacity planning needed

**Production (Provisioned)**
- Reserve read/write capacity units
- Predictable costs
- Faster performance
- Requires scaling planning

### Performance Metrics:

| Metric | Target | Method |
|--------|--------|--------|
| Read latency | < 10ms | Query with index |
| Write latency | < 10ms | Batch writes |
| Scan speed | < 1s | Full table |
| Search speed | < 100ms | Indexed query |

---

## Slide 8: Security & Compliance

**Title**: DynamoDB Security Best Practices

### Security Layers:

**1. Network Security**
- VPC endpoint for private access
- No internet exposure
- Encrypted in transit

**2. Encryption**
- At-rest: AWS KMS
- In-transit: TLS/SSL
- Key management: Automatic

**3. Authentication & Authorization**
- IAM roles for access
- Fine-grained permissions
- Audit logging enabled

**4. Backup & Recovery**
- Point-in-time recovery (PITR)
- Automated backups
- Manual snapshots available

**5. Data Protection**
- Item-level security
- Attribute encryption option
- Compliance: HIPAA, PCI-DSS ready

---

## Slide 9: Cost Analysis

**Title**: DynamoDB Cost Breakdown

### Pricing Model:

**Pay-Per-Request (Development)**
```
Reads:  $0.25 per million
Writes: $1.25 per million
Storage: $0.25 per GB/month
```

**Example (1000 documents/day)**:
- Inserts: 1,000/day
- Reads: 5,000/day
- Storage: 1 GB

**Monthly Cost**:
```
Writes: (1,000 × 30) / 1M × $1.25 = $0.04
Reads: (5,000 × 30) / 1M × $0.25 = $0.04
Storage: 1 GB × $0.25 = $0.25
Total: ~$0.33/month
```

---

## Slide 10: Architecture Justification

**Title**: Why DynamoDB for DocuProcess?

### Key Advantages:

**1. Serverless**
- No infrastructure to manage
- Auto-scaling built-in
- Pay only for what you use

**2. Scalability**
- Handles millions of requests
- Linear scaling
- Global distribution option

**3. Performance**
- Single-digit millisecond latency
- Consistent performance
- No query timeouts

**4. Integration**
- Seamless with Lambda
- Works with EC2
- Easy with SNS

**5. Cost Effectiveness**
- ~$0.33/month for typical usage
- No server costs
- Efficient for spiky traffic

**6. Reliability**
- 99.99% uptime SLA
- Multi-AZ redundancy
- Automatic failover

---

## Slide 11: Challenges & Solutions

**Title**: Addressing DynamoDB Challenges

| Challenge | DynamoDB Solution | Impact |
|-----------|-------------------|--------|
| Complex queries | Use GSI + client-side filtering | Excellent for DocuProcess |
| Strong consistency | Eventually consistent (tunable) | Not critical for review workflow |
| Item size limit | 400 KB max item | More than enough for documents |
| Partition key design | Use document_id (UUID) | Distributes load evenly |
| Cost at scale | Use provisioned capacity | Can scale to millions |

---

## Configuration Summary

**For Presentation**:
```
Table: DocumentRecords
Region: us-east-1
Billing: Pay-per-Request
Primary Key: document_id (String)
Status Index: status-timestamp-index
Backup: Point-in-time recovery enabled
```

**Statistics to Show**:
- Setup time: < 5 minutes
- Schema flexibility: JSON-like documents
- Query speed: < 10ms
- Monthly cost: < $1 for typical usage
- Reliability: 99.99% uptime

---

## Key Takeaways

1. ✅ **DynamoDB is ideal** for document processing pipelines
2. ✅ **Fully managed** (no ops overhead)
3. ✅ **Cost-effective** (pay-per-request)
4. ✅ **Scalable** (handles millions of documents)
5. ✅ **Integrates seamlessly** with Lambda and EC2
6. ✅ **Highly available** (multi-AZ, 99.99% SLA)

---

## References & Links

- [AWS DynamoDB Docs](https://docs.aws.amazon.com/dynamodb/)
- [Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Pricing Calculator](https://aws.amazon.com/dynamodb/pricing/)
- [boto3 DynamoDB](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html)

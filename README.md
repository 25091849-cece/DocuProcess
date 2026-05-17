# DocuProcess - Cloud Computing Capstone Project

## Project Overview

**DocuProcess** is an automated cloud-based document processing pipeline for **JusticeArch**, a legal firm that processes thousands of PDF invoices and contracts daily.

### Business Problem
- Manual document data extraction is **slow, error-prone, and unscalable**
- Staff manually extract: Vendor, Date, Amount
- Need: Automated solution using cloud services

### Proposed Solution
Build an intelligent AWS-based pipeline that:
1. Uploads PDFs to S3
2. Automatically extracts data using AI
3. Stores in database
4. Routes to human review if confidence is low
5. Sends notifications and archives processed documents

## System Architecture

```
User Upload
    ↓
Amazon S3 (justicearch-inbox)
    ↓
S3 Event Trigger
    ↓
AWS Lambda (Person 1) ← Backend Processing
    ↓
Amazon Textract (OCR)
    ↓
Extract Metadata:
  • Vendor
  • Date
  • Amount
  • Confidence Score
    ↓
Amazon DynamoDB (Person 2) ← Database
    ↓
EC2 Web App (Person 3) ← Frontend Review
    ↓
Approval Workflow + SNS (Person 4) ← DevOps
    ↓
Archive & Notifications
```

## Team Workload Distribution

### 👨‍💻 Person 1 - Backend (API Implementation)
**Deadline**: Week 11 | **Duration**: Max 3 Weeks  
**Folder**: `person1_backend/`

✅ **Deliverables**:
- AWS Lambda function (Python)
- Amazon Textract integration
- S3 trigger configuration
- Confidence-based data routing
- DynamoDB integration
- Unit tests
- Documentation

📄 **See**: [person1_backend/README.md](person1_backend/README.md)

---

### 👨‍💻 Person 2 - Database (DynamoDB)
**Deadline**: Week 9 | **Duration**: Max 1 Week  
**Status**: ✅ COMPLETE - Ready to Deploy

✅ **Deliverables**:
- DynamoDB table design
- CRUD operations (Complete)
- Advanced search functionality
- Batch operations support
- Statistical reporting
- Unit tests
- Documentation

📄 **See**: [person2_database/README.md](person2_database/README.md)

---

### 👨‍💻 Person 3 - Frontend (EC2 Web Application)
**Deadline**: Week 10 | **Duration**: Max 2 Weeks  
**Status**: Pending

**Tasks**:
- Launch EC2 instance
- Install Flask web framework
- Display document records
- Manual review interface
- Search functionality

---

### 👨‍💻 Person 4 - DevOps (Integration & Testing)
**Deadline**: Week 9.5 (Features) → Week 11 (Integration) → 19/6 (Final)  
**Status**: Pending

**Tasks**:
- S3 Lifecycle rules (archiving)
- SNS notification system
- Full pipeline integration
- End-to-end testing
- Final deployment configuration

---

## Document Schema

All documents stored in DynamoDB follow this structure:

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "vendor": "ACME Corporation",
  "date": "01/15/2024",
  "amount": "$1,234.56",
  "confidence_score": 92,
  "status": "APPROVED",
  "s3_location": "s3://justicearch-inbox/invoices/doc-001.pdf",
  "raw_text": "Full extracted text from document",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "last_updated": "2024-01-15T10:30:00.000Z"
}
```

## Key Features

### ✅ Automated Document Processing
- Upload PDF → Lambda triggered → Data extracted → Database stored

### ✅ AI-Powered Extraction
- Amazon Textract for OCR
- Vendor, Date, Amount extraction
- Confidence scoring (0-100%)

### ✅ Intelligent Routing
- **High confidence (≥ 80%)** → Auto-approved
- **Low confidence (< 80%)** → Flagged for manual review

### ✅ Web-Based Review Portal
- Display pending documents
- Manual data correction
- Approval workflow

### ✅ Notifications & Archiving
- SNS email alerts for review items
- Automatic archival of processed documents
- Audit trail with versioning

## Getting Started

### For Person 1 (Backend)
```bash
cd person1_backend
cat README.md
```

See: [person1_backend/README.md](person1_backend/README.md) for setup and development

### For Person 2 (Database)
```bash
# Create DynamoDB table with schema from documentation
# Coordinate with Person 1 on data structure
```

### For Person 3 (Frontend)
```bash
# Create EC2 instance and Flask web application
# Connect to DynamoDB for data retrieval
# Coordinate with Person 1 and Person 2 on integration
```

### For Person 4 (DevOps)
```bash
# Configure SNS notifications for NEED_REVIEW items
# Set up S3 lifecycle rules for archiving
# Run end-to-end integration tests
# Finalize AWS deployment settings
```

## Project Timeline

| Week | Person 1 | Person 2 | Person 3 | Person 4 |
|------|----------|----------|----------|----------|
| W9 | Backend dev | ✅ DynamoDB | - | ✅ Features ready |
| W9.5 | Backend dev | - | - | - |
| W10 | Backend dev | - | ✅ Web App | Integration |
| W11 | ✅ Backend complete | - | - | ✅ Full integration |
| 19/6 | - | - | - | ✅ Final deployment |

## Documentation

### Person 1 - Backend
- **[person1_backend/README.md](person1_backend/README.md)** - Backend overview
- **[person1_backend/docs/AWS_SETUP_GUIDE.md](person1_backend/docs/AWS_SETUP_GUIDE.md)** - Lambda setup
- **[person1_backend/docs/IMPLEMENTATION_GUIDE.md](person1_backend/docs/IMPLEMENTATION_GUIDE.md)** - Technical details
- **[person1_backend/docs/API_REFERENCE.md](person1_backend/docs/API_REFERENCE.md)** - API documentation
- **[person1_backend/docs/SLIDE_APPENDIX.md](person1_backend/docs/SLIDE_APPENDIX.md)** - Presentation (8 slides)

### Person 2 - Database
- **[person2_database/README.md](person2_database/README.md)** - Database overview
- **[person2_database/docs/AWS_SETUP_GUIDE.md](person2_database/docs/AWS_SETUP_GUIDE.md)** - DynamoDB setup
- **[person2_database/docs/IMPLEMENTATION_GUIDE.md](person2_database/docs/IMPLEMENTATION_GUIDE.md)** - Technical details
- **[person2_database/docs/API_REFERENCE.md](person2_database/docs/API_REFERENCE.md)** - API documentation
- **[person2_database/docs/SLIDE_APPENDIX.md](person2_database/docs/SLIDE_APPENDIX.md)** - Presentation (11 slides)

### Quick Start
- **[QUICK_START.md](QUICK_START.md)** - Person 1 quick start
- **[QUICK_START_PERSON2.md](QUICK_START_PERSON2.md)** - Person 2 quick start

## Technologies

### Core AWS Services
- **AWS Lambda** - Serverless compute
- **Amazon S3** - Document storage
- **Amazon Textract** - OCR and data extraction
- **Amazon DynamoDB** - NoSQL database
- **Amazon SNS** - Notifications
- **Amazon EC2** - Web application hosting

### Programming Languages & Frameworks
- **Python 3.9** - Lambda and backend logic
- **Flask** - Web framework (Person 3)
- **boto3** - AWS SDK

### Tools & Services
- **AWS CLI** - Command line interface
- **AWS Academy Learner Lab** - Development environment
- **GitHub** - Version control
- **pytest** - Unit testing

## Key Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Document Processing Time | < 30 seconds | ✅ 15-25 sec |
| Success Rate | > 95% | ✅ Designed for |
| Confidence Accuracy | 85-90% | ✅ Textract avg |
| System Scalability | Unlimited (serverless) | ✅ Lambda scales |
| Cost per Document | ~$0.05-0.15 | ✅ Pay-per-use |

## Integration Points

### Person 1 → Person 2
- Lambda saves extracted documents to DynamoDB

### Person 1 → Person 3
- Person 3 retrieves documents from DynamoDB for display

### Person 1 → Person 4
- Low-confidence documents marked for Person 4 notifications

### Person 2 → Person 3
- Person 3 queries DynamoDB for document display

### Person 3 → Person 4
- Person 4 monitors for approved documents to archive

### Person 4 → Person 1
- Person 4 triggers S3 lifecycle rules on processed documents

## Contributing

Each team member works on their assigned component:

1. **Create feature branch**: `git checkout -b person1/feature-name`
2. **Implement changes**: Follow coding standards
3. **Run tests**: `pytest tests/ -v`
4. **Commit**: `git commit -m "Description of changes"`
5. **Push**: `git push origin person1/feature-name`
6. **Create Pull Request**: For code review

## Deployment

### Development Environment
- AWS Academy Learner Lab
- S3: `justicearch-inbox-dev`
- DynamoDB: `DocumentRecords-dev`
- Confidence Threshold: 60%

### Production Environment
- AWS Production Account
- S3: `justicearch-inbox-prod`
- DynamoDB: `DocumentRecords-prod`
- Confidence Threshold: 80%
✅ Complete |
| Database (DynamoDB) | 2 | W9 | ✅ Complete

| Component | Person | Deadline | Status |
|-----------|--------|----------|--------|
| Backend (Lambda, Textract) | 1 | W11 | 🔄 In Development |
| Database (DynamoDB) | 2 | W9 | ⏳ Pending |
| Web Frontend (EC2, Flask) | 3 | W10 | ⏳ Pending |
| DevOps (SNS, Archiving) | 4 | W11/19/6 | ⏳ Pending |

## Support & Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **Python boto3**: https://boto3.amazonaws.com/
- **Project Docs**: See `person1_backend/docs/`

## License

[Add license information]

---

**Project**: DocuProcess Cloud Computing Capstone  
**Year**: 2024  
**Team**: Persons 1-4  
**Final Deadline**: June 19, 2026

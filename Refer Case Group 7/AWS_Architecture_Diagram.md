# JusticeArch Document Processing - AWS Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        User["👤 Users"]
    end
    
    subgraph "Web Application Layer"
        Flask["🐍 Flask Web App<br/>FlaskCode_v6.py<br/>- Review Portal UI<br/>- Dashboard & Stats<br/>- Document Search"]
    end
    
    subgraph "AWS Services"
        subgraph "Storage & Database"
            S3["🪣 AWS S3<br/>justicearch-inbox-group7<br/>- Document Storage<br/>- Presigned URLs"]
            DynamoDB["📊 DynamoDB<br/>JusticeArchDocuments<br/>- Metadata Storage<br/>- Document Records"]
        end
        
        subgraph "Document Processing"
            Lambda["⚡ AWS Lambda<br/>LambdaCodev1.py<br/>- Triggered by S3 events<br/>- OCR & Form Analysis<br/>- Key-Value Extraction"]
            Textract["📄 AWS Textract<br/>- Document Analysis<br/>- Form Recognition<br/>- Text Extraction"]
        end
        
        subgraph "Notifications & Events"
            S3Events["🔔 S3 Events<br/>Document Upload Trigger"]
        end
    end
    
    User -->|Browse & Review| Flask
    Flask -->|Read Data| DynamoDB
    Flask -->|Get Documents| S3
    Flask -->|Generate Presigned URLs| S3
    
    S3 -->|Upload Event| S3Events
    S3Events -->|Triggers| Lambda
    Lambda -->|Analyze Document| Textract
    Textract -->|Returns Results| Lambda
    Lambda -->|Extract: Vendor, Date,<br/>Key-Value Pairs| Lambda
    Lambda -->|Store Results| DynamoDB
    
    style Flask fill:#ff9f40
    style Lambda fill:#4dd0e1
    style S3 fill:#90caf9
    style DynamoDB fill:#a5d6a7
    style Textract fill:#ce93d8
    style User fill:#ffcc80
```

## Architecture Components

### 1. **Web Application Layer**
- **Flask Web App** (FlaskCode_v6.py)
  - Dashboard with statistics (documents by status)
  - Search functionality
  - Document review interface
  - Admin controls for document management
  - Displays presigned URLs for secure document access

### 2. **Storage Layer**
- **AWS S3** (justicearch-inbox-group7 bucket)
  - Stores uploaded documents (PDFs, images, etc.)
  - Generates time-limited presigned URLs (5-minute expiration)
  - Triggers events on document upload

- **DynamoDB** (JusticeArchDocuments table)
  - Stores document metadata
  - Persists extracted information (vendor, date, key-value pairs)
  - Tracks document status and review state

### 3. **Processing Layer**
- **AWS Lambda** (LambdaCodev1.py)
  - Event-driven trigger on S3 uploads
  - Orchestrates document processing workflow
  - Extracts vendor information (from key-value pairs or regex)
  - Extracts date information (date patterns)
  - Stores results in DynamoDB

- **AWS Textract**
  - Performs OCR on uploaded documents
  - Analyzes forms and tables
  - Extracts key-value pairs from structured documents
  - Returns confidence scores

### 4. **Data Flow**
1. User uploads document → S3
2. S3 event triggers Lambda
3. Lambda calls Textract for analysis
4. Textract returns structured data
5. Lambda extracts key information (vendor, date, forms data)
6. Results stored in DynamoDB
7. Flask app retrieves and displays results to users

## Key Features
- ✅ Serverless processing (Lambda + Textract)
- ✅ Secure document access (presigned URLs)
- ✅ Form field extraction
- ✅ Vendor and date recognition
- ✅ Real-time dashboard updates

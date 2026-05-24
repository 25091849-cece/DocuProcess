# Person 1 Backend - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies
```bash
cd person1_backend
pip install -r requirements.txt
```

### 1.2 Set Environment Variables

**On Windows (PowerShell)**:
```powershell
$env:AWS_REGION = "us-east-1"
$env:S3_BUCKET_NAME = "justicearch-inbox"
$env:DYNAMODB_TABLE_NAME = "DocumentRecords"
$env:CONFIDENCE_THRESHOLD = "80"
```

**On macOS/Linux (Bash)**:
```bash
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=justicearch-inbox
export DYNAMODB_TABLE_NAME=DocumentRecords
export CONFIDENCE_THRESHOLD=80
```

### 2. Run Unit Tests
```bash
python -m pytest tests/ -v
```

### 3. Deploy to AWS (Automated)

**On macOS/Linux**:
```bash
chmod +x deploy.sh
./deploy.sh
```

**On Windows**:
```bash
deploy.bat
```

The script will:
- ✅ Create S3 bucket
- ✅ Set up IAM roles and policies
- ✅ Deploy Lambda function
- ✅ Configure S3 event trigger

### 4. Test the Pipeline
```bash
# Upload a test PDF
aws s3 cp sample-invoice.pdf s3://justicearch-inbox/invoices/test.pdf

# Monitor Lambda execution
aws logs tail /aws/lambda/DocuProcessDocumentExtractor --follow

# Check results in DynamoDB
aws dynamodb scan --table-name DocumentRecords
```

---

## 📚 Documentation

Start with these files in this order:

1. **README.md** - Overview and project structure
2. **docs/IMPLEMENTATION_GUIDE.md** - Technical details
3. **docs/AWS_SETUP_GUIDE.md** - AWS configuration steps
4. **docs/API_REFERENCE.md** - Complete API documentation

---

## 🔧 Manual AWS Setup

If you prefer manual setup instead of using the deployment script:

1. **Create S3 bucket**:
   ```bash
   aws s3api create-bucket --bucket justicearch-inbox --region us-east-1
   ```

2. **Create IAM role** (see AWS_SETUP_GUIDE.md for policies)

3. **Deploy Lambda**:
   ```bash
   python -m pytest tests/
   zip -r lambda_function.zip lambda_function/ config/
   aws lambda create-function ... (see AWS_SETUP_GUIDE.md)
   ```

---

## ⚙️ Configuration

Set environment variables before deploying:

```bash
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=justicearch-inbox
export DYNAMODB_TABLE_NAME=DocumentRecords
export CONFIDENCE_THRESHOLD=80
```

---

## 🧪 Testing

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run specific test
```bash
python -m pytest tests/test_textract_processor.py::TestTextractProcessor::test_extract_vendor_from_text -v
```

### Test locally with SAM CLI
```bash
sam local invoke DocuProcessDocumentExtractor -e test_event.json
```

---

## 📝 Project Files

```
person1_backend/
├── lambda_function/          # Main Lambda code
│   ├── lambda_handler.py     # Entry point
│   ├── textract_processor.py # Textract integration
│   └── dynamodb_handler.py   # Database operations
├── config/
│   └── config.py             # Environment config
├── tests/                    # Unit tests
├── docs/                     # Complete documentation
├── requirements.txt          # Python dependencies
├── test_event.json          # Sample S3 event
├── deploy.sh                # Linux/Mac deployment
├── deploy.bat               # Windows deployment
└── README.md                # Full README
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'boto3'` | Run `pip install -r requirements.txt` |
| Lambda not triggered | Check S3 event notification config |
| DynamoDB write errors | Ensure table exists with correct name |
| Permission denied | Check IAM role policies |
| Textract extraction fails | Verify document is a valid PDF |

---

## 🔗 Next Steps

1. ✅ Deploy Lambda function
2. ✅ Test with sample PDF
3. ⏳ Wait for Person 2 to create DynamoDB table
4. ⏳ Integrate with Person 3 (web app)
5. ⏳ Work with Person 4 on SNS/archiving

---

## 📞 Support

- Check docs/ folder for detailed guides
- Review code comments in lambda_function/
- Run tests to validate functionality
- Check CloudWatch logs for runtime errors

---

**Duration**: Max 3 Weeks | **Deadline**: Week 11

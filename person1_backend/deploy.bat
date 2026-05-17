@echo off
REM DocuProcess Lambda Deployment Script (Windows)
REM This script automates AWS setup for Person 1's backend

setlocal enabledelayedexpansion

echo ==========================================
echo DocuProcess Lambda Deployment Script
echo ==========================================
echo.

REM Configuration
set FUNCTION_NAME=DocuProcessDocumentExtractor
set RUNTIME=python3.9
set ROLE_NAME=DocuProcess-Lambda-Role
set S3_BUCKET=justicearch-inbox
set DYNAMODB_TABLE=DocumentRecords
set REGION=us-east-1
set TIMEOUT=300
set MEMORY=512

REM Check prerequisites
echo Checking prerequisites...

where aws >nul 2>nul
if errorlevel 1 (
    echo ERROR: AWS CLI not found. Please install it first.
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Please install it first.
    exit /b 1
)

echo [OK] Prerequisites installed

REM Get AWS Account ID
for /f "delims=" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i

if "!ACCOUNT_ID!"=="" (
    echo ERROR: Failed to get AWS Account ID. Check your AWS credentials.
    exit /b 1
)

echo [OK] AWS Account ID: !ACCOUNT_ID!
echo.

REM Step 1: Create S3 bucket
echo Creating S3 bucket...
aws s3 ls s3://!S3_BUCKET! >nul 2>nul
if errorlevel 1 (
    aws s3api create-bucket --bucket !S3_BUCKET! --region !REGION!
    echo [OK] S3 bucket created
) else (
    echo [OK] S3 bucket already exists
)

aws s3api put-public-access-block --bucket !S3_BUCKET! --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
echo.

REM Step 2: Create IAM role
echo Setting up IAM role...
aws iam get-role --role-name !ROLE_NAME! >nul 2>nul
if errorlevel 1 (
    (
        echo {
        echo   "Version": "2012-10-17",
        echo   "Statement": [
        echo     {
        echo       "Effect": "Allow",
        echo       "Principal": {"Service": "lambda.amazonaws.com"},
        echo       "Action": "sts:AssumeRole"
        echo     }
        echo   ]
        echo }
    ) > trust-policy.json
    
    aws iam create-role --role-name !ROLE_NAME! --assume-role-policy-document file://trust-policy.json
    echo [OK] IAM role created
    timeout /t 2 /nobreak
) else (
    echo [OK] IAM role already exists
)

echo.

REM Step 3: Attach policies
echo Attaching IAM policies...

(
    echo {
    echo   "Version": "2012-10-17",
    echo   "Statement": [
    echo     {
    echo       "Effect": "Allow",
    echo       "Action": ["s3:GetObject", "s3:GetObjectVersion"],
    echo       "Resource": "arn:aws:s3:::!S3_BUCKET!/*"
    echo     },
    echo     {
    echo       "Effect": "Allow",
    echo       "Action": ["s3:ListBucket"],
    echo       "Resource": "arn:aws:s3:::!S3_BUCKET!"
    echo     }
    echo   ]
    echo }
) > s3-policy.json

aws iam put-role-policy --role-name !ROLE_NAME! --policy-name S3Access --policy-document file://s3-policy.json

(
    echo {
    echo   "Version": "2012-10-17",
    echo   "Statement": [
    echo     {
    echo       "Effect": "Allow",
    echo       "Action": ["textract:DetectDocumentText", "textract:AnalyzeDocument"],
    echo       "Resource": "*"
    echo     }
    echo   ]
    echo }
) > textract-policy.json

aws iam put-role-policy --role-name !ROLE_NAME! --policy-name TextractAccess --policy-document file://textract-policy.json

(
    echo {
    echo   "Version": "2012-10-17",
    echo   "Statement": [
    echo     {
    echo       "Effect": "Allow",
    echo       "Action": ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:Query"],
    echo       "Resource": "arn:aws:dynamodb:!REGION!:*:table/!DYNAMODB_TABLE!"
    echo     }
    echo   ]
    echo }
) > dynamodb-policy.json

aws iam put-role-policy --role-name !ROLE_NAME! --policy-name DynamoDBAccess --policy-document file://dynamodb-policy.json

(
    echo {
    echo   "Version": "2012-10-17",
    echo   "Statement": [
    echo     {
    echo       "Effect": "Allow",
    echo       "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
    echo       "Resource": "arn:aws:logs:*:*:*"
    echo     }
    echo   ]
    echo }
) > logs-policy.json

aws iam put-role-policy --role-name !ROLE_NAME! --policy-name CloudWatchLogs --policy-document file://logs-policy.json

echo [OK] Policies attached
echo.

REM Step 4: Create deployment package
echo Creating Lambda deployment package...
REM Note: Requires PowerShell or alternative on Windows

if exist lambda_function.zip del lambda_function.zip

REM Create temporary directory for packaging
md temp_lambda 2>nul

REM Copy files
copy lambda_function\*.py temp_lambda\ >nul
copy config\*.py temp_lambda\ >nul

REM Install dependencies
pip install -q -r requirements.txt -t temp_lambda\

REM Create ZIP
powershell -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('temp_lambda', 'lambda_function.zip')"

echo [OK] Deployment package created
echo.

REM Step 5: Deploy Lambda
echo Deploying Lambda function...
set ROLE_ARN=arn:aws:iam::!ACCOUNT_ID!:role/!ROLE_NAME!

aws lambda get-function --function-name !FUNCTION_NAME! >nul 2>nul
if errorlevel 1 (
    aws lambda create-function ^
        --function-name !FUNCTION_NAME! ^
        --runtime !RUNTIME! ^
        --role !ROLE_ARN! ^
        --handler lambda_handler.lambda_handler ^
        --zip-file fileb://lambda_function.zip ^
        --timeout !TIMEOUT! ^
        --memory-size !MEMORY! ^
        --environment "Variables={S3_BUCKET_NAME=!S3_BUCKET!,DYNAMODB_TABLE_NAME=!DYNAMODB_TABLE!,CONFIDENCE_THRESHOLD=80,AWS_REGION=!REGION!,LOG_LEVEL=INFO}"
    
    echo [OK] Lambda function created
) else (
    aws lambda update-function-code ^
        --function-name !FUNCTION_NAME! ^
        --zip-file fileb://lambda_function.zip
    
    echo [OK] Lambda function updated
)
echo.

REM Step 6: Configure S3 trigger
echo Configuring S3 event trigger...
set LAMBDA_ARN=arn:aws:lambda:!REGION!:!ACCOUNT_ID!:function:!FUNCTION_NAME!

aws lambda add-permission --function-name !FUNCTION_NAME! --statement-id AllowS3Invoke --action lambda:InvokeFunction --principal s3.amazonaws.com --source-arn arn:aws:s3:::!S3_BUCKET! >nul 2>nul

(
    echo {
    echo   "LambdaFunctionConfigurations": [
    echo     {
    echo       "LambdaFunctionArn": "!LAMBDA_ARN!",
    echo       "Events": ["s3:ObjectCreated:*"],
    echo       "Filter": {
    echo         "Key": {
    echo           "FilterRules": [
    echo             {"Name": "prefix", "Value": "invoices/"},
    echo             {"Name": "suffix", "Value": ".pdf"}
    echo           ]
    echo         }
    echo       }
    echo     }
    echo   ]
    echo }
) > notification-config.json

aws s3api put-bucket-notification-configuration --bucket !S3_BUCKET! --notification-configuration file://notification-config.json

echo [OK] S3 event trigger configured
echo.

REM Cleanup
rmdir /s /q temp_lambda 2>nul
del trust-policy.json s3-policy.json textract-policy.json dynamodb-policy.json logs-policy.json notification-config.json 2>nul

echo ==========================================
echo [SUCCESS] Deployment Complete!
echo ==========================================
echo.
echo Lambda Function: !FUNCTION_NAME!
echo S3 Bucket: !S3_BUCKET!
echo DynamoDB Table: !DYNAMODB_TABLE!
echo Region: !REGION!
echo.
echo Next steps:
echo 1. Upload a test PDF to s3://!S3_BUCKET!/invoices/
echo 2. Check Lambda logs: aws logs tail /aws/lambda/!FUNCTION_NAME! --follow
echo 3. Verify data in DynamoDB: aws dynamodb scan --table-name !DYNAMODB_TABLE!
echo.

endlocal

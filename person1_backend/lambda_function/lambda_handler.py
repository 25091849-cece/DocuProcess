"""
DocuProcess Lambda Handler
Triggered by S3 upload event to extract document data using Amazon Textract
"""

import json
import boto3
import logging
from textract_processor import TextractProcessor
from dynamodb_handler import DynamoDBHandler
from config import Config

# Initialize AWS clients
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize handlers
config = Config()
textract_processor = TextractProcessor(textract_client)
dynamodb_handler = DynamoDBHandler()


def lambda_handler(event, context):
    """
    Main Lambda handler for document processing pipeline
    
    Event structure:
    {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "bucket-name"},
                    "object": {"key": "file-path"}
                }
            }
        ]
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract S3 bucket and key from event
        for record in event.get('Records', []):
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            logger.info(f"Processing: s3://{bucket_name}/{object_key}")
            
            # Process document
            result = process_document(bucket_name, object_key)
            
            if not result['success']:
                logger.error(f"Error processing document: {result['error']}")
                continue
                
            logger.info(f"Successfully processed: {object_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Document processing completed successfully')
        }
        
    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }


def process_document(bucket_name, object_key):
    """
    Process a single document through the pipeline
    
    Args:
        bucket_name (str): S3 bucket name
        object_key (str): S3 object key (file path)
        
    Returns:
        dict: Processing result with success status and data
    """
    try:
        # Step 1: Extract text using Textract
        logger.info(f"Extracting text from {object_key} using Textract...")
        textract_result = textract_processor.extract_document_data(
            bucket_name, 
            object_key
        )
        
        if not textract_result['success']:
            return {
                'success': False,
                'error': f"Textract extraction failed: {textract_result['error']}"
            }
        
        extracted_data = textract_result['data']
        logger.info(f"Extracted data: {json.dumps(extracted_data)}")
        
        # Step 2: Calculate confidence score
        confidence_score = extracted_data.get('confidence_score', 0)
        logger.info(f"Confidence score: {confidence_score}%")
        
        # Step 3: Determine status based on confidence
        if confidence_score >= config.CONFIDENCE_THRESHOLD:
            status = 'APPROVED'
            logger.info("High confidence: Auto-approved")
        else:
            status = 'NEED_REVIEW'
            logger.info("Low confidence: Marked for manual review")
        
        # Step 4: Prepare document record
        document_record = {
            'document_id': extracted_data.get('document_id'),
            'vendor': extracted_data.get('vendor', ''),
            'date': extracted_data.get('date', ''),
            'amount': extracted_data.get('amount', ''),
            'confidence_score': confidence_score,
            'status': status,
            's3_location': f"s3://{bucket_name}/{object_key}",
            'raw_text': extracted_data.get('raw_text', '')
        }
        
        # Step 5: Save to DynamoDB
        logger.info("Saving to DynamoDB...")
        db_result = dynamodb_handler.save_document(document_record)
        
        if not db_result['success']:
            return {
                'success': False,
                'error': f"DynamoDB save failed: {db_result['error']}"
            }
        
        logger.info(f"Document saved to DynamoDB with ID: {document_record['document_id']}")
        
        return {
            'success': True,
            'data': document_record
        }
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

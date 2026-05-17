"""
DynamoDB Handler Module
Handles database operations for document records
"""

import boto3
import logging
from datetime import datetime
from typing import Dict, Any, List
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DynamoDBHandler:
    """
    Wrapper class for DynamoDB operations
    """
    
    def __init__(self, table_name: str = 'DocumentRecords'):
        """
        Initialize DynamoDBHandler
        
        Args:
            table_name (str): DynamoDB table name
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name
        self.table = self.dynamodb.Table(table_name)
        self.logger = logging.getLogger(__name__)
    
    def save_document(self, document_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save document record to DynamoDB
        
        Args:
            document_record (dict): Document data to save
            
        Returns:
            dict: Result of save operation
        """
        try:
            self.logger.info(f"Saving document {document_record.get('document_id')} to DynamoDB")
            
            # Add timestamp if not present
            if 'timestamp' not in document_record:
                document_record['timestamp'] = datetime.now().isoformat()
            
            # Put item in table
            self.table.put_item(Item=document_record)
            
            self.logger.info(f"Successfully saved document: {document_record.get('document_id')}")
            
            return {
                'success': True,
                'document_id': document_record.get('document_id')
            }
            
        except ClientError as e:
            self.logger.error(f"DynamoDB client error: {e.response['Error']['Code']}")
            return {
                'success': False,
                'error': f"DynamoDB error: {e.response['Error']['Code']}"
            }
        except Exception as e:
            self.logger.error(f"Error saving document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve a single document by ID
        
        Args:
            document_id (str): Document ID
            
        Returns:
            dict: Retrieved document or error
        """
        try:
            self.logger.info(f"Retrieving document {document_id}")
            
            response = self.table.get_item(Key={'document_id': document_id})
            
            if 'Item' in response:
                self.logger.info(f"Document found: {document_id}")
                return {
                    'success': True,
                    'data': response['Item']
                }
            else:
                self.logger.info(f"Document not found: {document_id}")
                return {
                    'success': False,
                    'error': 'Document not found'
                }
                
        except ClientError as e:
            self.logger.error(f"DynamoDB error retrieving document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_document(self, document_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update document record
        
        Args:
            document_id (str): Document ID
            updates (dict): Fields to update
            
        Returns:
            dict: Result of update operation
        """
        try:
            self.logger.info(f"Updating document {document_id}")
            
            # Build update expression
            update_parts = []
            expression_values = {}
            
            for key, value in updates.items():
                update_parts.append(f"{key} = :{key}")
                expression_values[f":{key}"] = value
            
            if not update_parts:
                return {'success': False, 'error': 'No fields to update'}
            
            update_expression = "SET " + ", ".join(update_parts)
            update_expression += ", last_updated = :timestamp"
            expression_values[':timestamp'] = datetime.now().isoformat()
            
            response = self.table.update_item(
                Key={'document_id': document_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            self.logger.info(f"Document updated: {document_id}")
            
            return {
                'success': True,
                'data': response['Attributes']
            }
            
        except ClientError as e:
            self.logger.error(f"DynamoDB error updating document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_by_status(self, status: str) -> Dict[str, Any]:
        """
        Query documents by status (APPROVED, NEED_REVIEW)
        Note: Requires status as GSI
        
        Args:
            status (str): Document status
            
        Returns:
            dict: Query results
        """
        try:
            self.logger.info(f"Querying documents with status: {status}")
            
            response = self.table.query(
                IndexName='status-timestamp-index',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': status
                }
            )
            
            items = response.get('Items', [])
            self.logger.info(f"Found {len(items)} documents with status {status}")
            
            return {
                'success': True,
                'data': items,
                'count': len(items)
            }
            
        except ClientError as e:
            self.logger.error(f"DynamoDB query error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def scan_all_documents(self) -> Dict[str, Any]:
        """
        Scan all documents from table
        
        Returns:
            dict: All documents or error
        """
        try:
            self.logger.info("Scanning all documents")
            
            response = self.table.scan()
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            self.logger.info(f"Scanned {len(items)} total documents")
            
            return {
                'success': True,
                'data': items,
                'count': len(items)
            }
            
        except ClientError as e:
            self.logger.error(f"DynamoDB scan error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

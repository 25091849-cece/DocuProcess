"""
DynamoDB Database Handler for DocuProcess
Handles all database operations: Create, Read, Update, Delete, Search
"""

import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DynamoDBHandler:
    """
    Handler for DynamoDB operations
    Manages document records in DocumentRecords table
    """
    
    def __init__(self, table_name: str = 'DocumentRecords', region: str = 'us-east-1'):
        """
        Initialize DynamoDB handler
        
        Args:
            table_name (str): DynamoDB table name
            region (str): AWS region
        """
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table_name = table_name
        self.table = self.dynamodb.Table(table_name)
        self.logger = logging.getLogger(__name__)
    
    # ==================== CREATE OPERATIONS ====================
    
    def insert_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new document record
        
        Args:
            document (dict): Document data to insert
                Required keys: document_id, vendor, date, amount, status
                
        Returns:
            dict: Result with success status
        """
        try:
            self.logger.info(f"Inserting document: {document.get('document_id')}")
            
            # Add timestamp if not present
            if 'timestamp' not in document:
                document['timestamp'] = datetime.now().isoformat()
            
            # Validate required fields
            required_fields = ['document_id', 'vendor', 'date', 'amount', 'status']
            for field in required_fields:
                if field not in document:
                    return {
                        'success': False,
                        'error': f"Missing required field: {field}"
                    }
            
            self.table.put_item(Item=document)
            
            self.logger.info(f"Document inserted successfully: {document['document_id']}")
            return {
                'success': True,
                'message': f"Document {document['document_id']} inserted",
                'document_id': document['document_id']
            }
            
        except ClientError as e:
            self.logger.error(f"DynamoDB error: {e.response['Error']['Code']}")
            return {
                'success': False,
                'error': f"DynamoDB error: {e.response['Error']['Code']}"
            }
        except Exception as e:
            self.logger.error(f"Error inserting document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def insert_multiple_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Insert multiple documents in batch
        
        Args:
            documents (list): List of document records
            
        Returns:
            dict: Result with success count
        """
        try:
            self.logger.info(f"Inserting {len(documents)} documents in batch")
            
            with self.table.batch_writer(
                batch_size=25  # DynamoDB batch size limit
            ) as batch:
                for document in documents:
                    if 'timestamp' not in document:
                        document['timestamp'] = datetime.now().isoformat()
                    batch.put_item(Item=document)
            
            self.logger.info(f"Batch insert completed: {len(documents)} documents")
            return {
                'success': True,
                'count': len(documents),
                'message': f"{len(documents)} documents inserted"
            }
            
        except Exception as e:
            self.logger.error(f"Error batch inserting documents: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== READ OPERATIONS ====================
    
    def retrieve_all_documents(self) -> Dict[str, Any]:
        """
        Retrieve all documents from table
        
        Returns:
            dict: All documents with count
        """
        try:
            self.logger.info("Retrieving all documents")
            
            response = self.table.scan()
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            self.logger.info(f"Retrieved {len(items)} documents")
            return {
                'success': True,
                'count': len(items),
                'documents': items
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get a specific document by ID
        
        Args:
            document_id (str): Document ID to retrieve
            
        Returns:
            dict: Document data or error
        """
        try:
            self.logger.info(f"Retrieving document: {document_id}")
            
            response = self.table.get_item(Key={'document_id': document_id})
            
            if 'Item' in response:
                self.logger.info(f"Document found: {document_id}")
                return {
                    'success': True,
                    'document': response['Item']
                }
            else:
                self.logger.info(f"Document not found: {document_id}")
                return {
                    'success': False,
                    'error': 'Document not found'
                }
                
        except Exception as e:
            self.logger.error(f"Error retrieving document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_documents_by_status(self, status: str) -> Dict[str, Any]:
        """
        Query documents by status (APPROVED, NEED_REVIEW)
        
        Args:
            status (str): Document status
            
        Returns:
            dict: Documents with matching status
        """
        try:
            self.logger.info(f"Querying documents with status: {status}")
            
            response = self.table.scan(
                FilterExpression='#s = :status',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':status': status}
            )
            
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    FilterExpression='#s = :status',
                    ExpressionAttributeNames={'#s': 'status'},
                    ExpressionAttributeValues={':status': status},
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            self.logger.info(f"Found {len(items)} documents with status {status}")
            return {
                'success': True,
                'count': len(items),
                'status': status,
                'documents': items
            }
            
        except Exception as e:
            self.logger.error(f"Error querying by status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update_document(self, document_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific fields in a document
        
        Args:
            document_id (str): Document ID to update
            updates (dict): Fields to update
            
        Returns:
            dict: Updated document or error
        """
        try:
            self.logger.info(f"Updating document: {document_id}")
            
            if not updates:
                return {
                    'success': False,
                    'error': 'No fields to update'
                }
            
            # Build update expression
            update_parts = []
            expression_values = {}
            
            for key, value in updates.items():
                update_parts.append(f"{key} = :{key}")
                expression_values[f":{key}"] = value
            
            # Always update the last_updated timestamp
            update_parts.append("last_updated = :timestamp")
            expression_values[':timestamp'] = datetime.now().isoformat()
            
            update_expression = "SET " + ", ".join(update_parts)
            
            response = self.table.update_item(
                Key={'document_id': document_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            self.logger.info(f"Document updated successfully: {document_id}")
            return {
                'success': True,
                'message': f"Document {document_id} updated",
                'document': response.get('Attributes', {})
            }
            
        except ClientError as e:
            self.logger.error(f"DynamoDB error: {e.response['Error']['Code']}")
            return {
                'success': False,
                'error': f"DynamoDB error: {e.response['Error']['Code']}"
            }
        except Exception as e:
            self.logger.error(f"Error updating document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_status(self, document_id: str, new_status: str) -> Dict[str, Any]:
        """
        Update document status
        
        Args:
            document_id (str): Document ID
            new_status (str): New status (APPROVED, NEED_REVIEW)
            
        Returns:
            dict: Result of update
        """
        return self.update_document(document_id, {'status': new_status})
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document
        
        Args:
            document_id (str): Document ID to delete
            
        Returns:
            dict: Result of deletion
        """
        try:
            self.logger.info(f"Deleting document: {document_id}")
            
            self.table.delete_item(Key={'document_id': document_id})
            
            self.logger.info(f"Document deleted successfully: {document_id}")
            return {
                'success': True,
                'message': f"Document {document_id} deleted"
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== SEARCH OPERATIONS ====================
    
    def search_documents_by_vendor(self, keyword: str) -> Dict[str, Any]:
        """
        Search documents by vendor name
        
        Args:
            keyword (str): Vendor name to search for
            
        Returns:
            dict: Matching documents
        """
        try:
            self.logger.info(f"Searching documents for vendor: {keyword}")
            
            response = self.table.scan()
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            # Client-side filtering by vendor
            results = [
                item for item in items
                if keyword.lower() in item.get('vendor', '').lower()
            ]
            
            self.logger.info(f"Found {len(results)} documents matching vendor: {keyword}")
            return {
                'success': True,
                'keyword': keyword,
                'count': len(results),
                'documents': results
            }
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_documents_by_date(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Search documents by date range
        
        Args:
            start_date (str): Start date (ISO format: YYYY-MM-DD)
            end_date (str): End date (ISO format: YYYY-MM-DD)
            
        Returns:
            dict: Documents in date range
        """
        try:
            self.logger.info(f"Searching documents between {start_date} and {end_date}")
            
            response = self.table.scan()
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            # Filter by date range
            results = [
                item for item in items
                if start_date <= item.get('date', '') <= end_date
            ]
            
            self.logger.info(f"Found {len(results)} documents in date range")
            return {
                'success': True,
                'start_date': start_date,
                'end_date': end_date,
                'count': len(results),
                'documents': results
            }
            
        except Exception as e:
            self.logger.error(f"Error searching by date: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_documents_by_amount(self, min_amount: float, max_amount: float) -> Dict[str, Any]:
        """
        Search documents by amount range
        
        Args:
            min_amount (float): Minimum amount
            max_amount (float): Maximum amount
            
        Returns:
            dict: Documents in amount range
        """
        try:
            self.logger.info(f"Searching documents with amount between {min_amount} and {max_amount}")
            
            response = self.table.scan()
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            # Filter by amount range
            results = [
                item for item in items
                if min_amount <= float(item.get('amount', 0)) <= max_amount
            ]
            
            self.logger.info(f"Found {len(results)} documents in amount range")
            return {
                'success': True,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'count': len(results),
                'documents': results
            }
            
        except Exception as e:
            self.logger.error(f"Error searching by amount: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== STATS AND REPORTING ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            dict: Statistics about documents
        """
        try:
            self.logger.info("Generating statistics")
            
            result = self.retrieve_all_documents()
            
            if not result['success']:
                return result
            
            documents = result['documents']
            
            if not documents:
                return {
                    'success': True,
                    'total_documents': 0,
                    'approved_count': 0,
                    'need_review_count': 0,
                    'total_amount': 0
                }
            
            approved = [d for d in documents if d.get('status') == 'APPROVED']
            need_review = [d for d in documents if d.get('status') == 'NEED_REVIEW']
            total_amount = sum(float(d.get('amount', 0)) for d in documents)
            
            return {
                'success': True,
                'total_documents': len(documents),
                'approved_count': len(approved),
                'need_review_count': len(need_review),
                'total_amount': total_amount,
                'percentage_approved': (len(approved) / len(documents) * 100) if documents else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error generating statistics: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# ==================== MAIN PROGRAM ====================

if __name__ == "__main__":
    
    # Initialize handler
    db_handler = DynamoDBHandler()
    
    print("\n" + "="*50)
    print("DocuProcess DynamoDB Handler Demo")
    print("="*50 + "\n")
    
    # 1. Insert sample document
    print("1. Inserting sample document...")
    sample_doc = {
        'document_id': 'DOC001',
        'vendor': 'ABC Sdn Bhd',
        'date': '2026-05-14',
        'amount': 5000,
        'status': 'NEED_REVIEW'
    }
    result = db_handler.insert_document(sample_doc)
    print(f"   Result: {result}\n")
    
    # 2. Retrieve all documents before update
    print("2. Retrieving all documents (before update)...")
    result = db_handler.retrieve_all_documents()
    if result['success']:
        for doc in result['documents']:
            print(f"   {doc}\n")
    
    # 3. Update document status
    print("3. Updating document status...")
    result = db_handler.update_status('DOC001', 'APPROVED')
    print(f"   Result: {result}\n")
    
    # 4. Retrieve documents after update
    print("4. Retrieving all documents (after update)...")
    result = db_handler.retrieve_all_documents()
    if result['success']:
        for doc in result['documents']:
            print(f"   {doc}\n")
    
    # 5. Search by vendor
    print("5. Searching documents by vendor 'ABC'...")
    result = db_handler.search_documents_by_vendor('ABC')
    print(f"   Count: {result.get('count', 0)}\n")
    
    # 6. Get statistics
    print("6. Getting database statistics...")
    result = db_handler.get_statistics()
    print(f"   {result}\n")

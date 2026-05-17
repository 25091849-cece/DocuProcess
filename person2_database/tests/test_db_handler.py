"""
Unit tests for DynamoDB handler
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add db_operations to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'db_operations'))

from db_handler import DynamoDBHandler


class TestDynamoDBHandler(unittest.TestCase):
    """Test cases for DynamoDBHandler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_dynamodb = Mock()
        self.mock_table = Mock()
    
    @patch('db_handler.boto3.resource')
    def test_insert_document_success(self, mock_resource):
        """Test successful document insertion"""
        mock_resource.return_value.Table.return_value = self.mock_table
        
        handler = DynamoDBHandler('DocumentRecords', 'us-east-1')
        
        document = {
            'document_id': 'DOC001',
            'vendor': 'Test Vendor',
            'date': '2026-05-17',
            'amount': 1000,
            'status': 'APPROVED'
        }
        
        result = handler.insert_document(document)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['document_id'], 'DOC001')
    
    def test_insert_document_missing_field(self):
        """Test document insertion with missing required field"""
        handler = DynamoDBHandler()
        
        document = {
            'document_id': 'DOC001',
            'vendor': 'Test Vendor'
            # Missing required fields
        }
        
        result = handler.insert_document(document)
        
        self.assertFalse(result['success'])
        self.assertIn('Missing required field', result['error'])
    
    @patch('db_handler.boto3.resource')
    def test_update_document(self, mock_resource):
        """Test document update"""
        mock_table = Mock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_table.update_item.return_value = {
            'Attributes': {
                'document_id': 'DOC001',
                'status': 'APPROVED'
            }
        }
        
        handler = DynamoDBHandler()
        result = handler.update_status('DOC001', 'APPROVED')
        
        self.assertTrue(result['success'])
    
    @patch('db_handler.boto3.resource')
    def test_search_by_vendor(self, mock_resource):
        """Test vendor search"""
        mock_table = Mock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_table.scan.return_value = {
            'Items': [
                {
                    'document_id': 'DOC001',
                    'vendor': 'ABC Company',
                    'date': '2026-05-17',
                    'amount': 1000,
                    'status': 'APPROVED'
                }
            ]
        }
        
        handler = DynamoDBHandler()
        result = handler.search_documents_by_vendor('ABC')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)


if __name__ == '__main__':
    unittest.main()

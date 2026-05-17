"""
Unit tests for TextractProcessor module
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add lambda_function to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_function'))

from textract_processor import TextractProcessor


class TestTextractProcessor(unittest.TestCase):
    """Test cases for TextractProcessor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_textract_client = Mock()
        self.processor = TextractProcessor(self.mock_textract_client)
    
    def test_extract_vendor_from_text(self):
        """Test vendor extraction"""
        text = """
        ACME Corporation
        123 Business Street
        Invoice #12345
        """
        result = self.processor._extract_vendor(text, {})
        self.assertIsNotNone(result)
        self.assertIn('ACME', result)
    
    def test_extract_date_from_text(self):
        """Test date extraction"""
        text = "Invoice Date: 01/15/2024"
        result = self.processor._extract_date(text, {})
        self.assertEqual(result, "01/15/2024")
    
    def test_extract_amount_from_text(self):
        """Test amount extraction"""
        text = "Total Amount: $1,234.56"
        result = self.processor._extract_amount(text, {})
        self.assertEqual(result, "$1,234.56")
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        mock_response = {
            'Blocks': [
                {'BlockType': 'LINE', 'Confidence': 95},
                {'BlockType': 'LINE', 'Confidence': 85},
                {'BlockType': 'LINE', 'Confidence': 90},
            ]
        }
        result = self.processor._calculate_confidence_score(mock_response)
        self.assertEqual(result, 90)  # Average of 95, 85, 90
    
    def test_empty_confidence_score(self):
        """Test confidence score with no blocks"""
        mock_response = {'Blocks': []}
        result = self.processor._calculate_confidence_score(mock_response)
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()

"""
Amazon Textract Integration Module
Handles document text extraction and data processing
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TextractProcessor:
    """
    Wrapper class for Amazon Textract operations
    """
    
    def __init__(self, textract_client):
        """
        Initialize TextractProcessor
        
        Args:
            textract_client: boto3 textract client
        """
        self.textract_client = textract_client
        self.logger = logging.getLogger(__name__)
    
    def extract_document_data(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """
        Extract key information from document using Textract
        
        Args:
            bucket_name (str): S3 bucket name
            object_key (str): S3 object key
            
        Returns:
            dict: Extraction result with extracted data and confidence scores
        """
        try:
            self.logger.info(f"Starting Textract extraction for {object_key}")
            
            # Call Textract API
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': object_key
                    }
                }
            )
            
            self.logger.info(f"Textract response status: {response['ResponseMetadata']['HTTPStatusCode']}")
            
            # Extract raw text blocks
            raw_text = self._extract_text_blocks(response)
            self.logger.info(f"Extracted raw text length: {len(raw_text)} characters")
            
            # Parse key-value pairs (if using FORMS feature)
            key_value_pairs = self._extract_key_value_pairs(response)
            
            # Extract structured data
            extracted_data = self._parse_document_fields(raw_text, key_value_pairs)
            
            # Add metadata
            extracted_data['document_id'] = str(uuid.uuid4())
            extracted_data['extraction_timestamp'] = datetime.now().isoformat()
            extracted_data['raw_text'] = raw_text
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(response)
            extracted_data['confidence_score'] = confidence_score
            
            self.logger.info(f"Extraction completed. Confidence: {confidence_score}%")
            
            return {
                'success': True,
                'data': extracted_data
            }
            
        except self.textract_client.exceptions.InvalidParameterException as e:
            self.logger.error(f"Invalid parameter in Textract request: {str(e)}")
            return {'success': False, 'error': f"Invalid parameter: {str(e)}"}
        except self.textract_client.exceptions.UnsupportedDocumentException as e:
            self.logger.error(f"Unsupported document type: {str(e)}")
            return {'success': False, 'error': f"Unsupported document: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Textract extraction error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_text_blocks(self, response: Dict) -> str:
        """
        Extract all text from Textract response
        
        Args:
            response (dict): Textract API response
            
        Returns:
            str: Combined text from all blocks
        """
        text_blocks = []
        
        for block in response.get('Blocks', []):
            if block.get('BlockType') == 'LINE':
                text = block.get('Text', '')
                if text:
                    text_blocks.append(text)
        
        return '\n'.join(text_blocks)
    
    def _extract_key_value_pairs(self, response: Dict) -> Dict[str, str]:
        """
        Extract key-value pairs from document (if FORMS feature is enabled)
        
        Args:
            response (dict): Textract API response
            
        Returns:
            dict: Key-value pairs found in document
        """
        key_values = {}
        
        # This is a placeholder for FORMS extraction
        # Full implementation would map FORM blocks to key-value pairs
        for block in response.get('Blocks', []):
            if block.get('BlockType') == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    # Store for later processing
                    pass
        
        return key_values
    
    def _parse_document_fields(self, raw_text: str, key_values: Dict) -> Dict[str, Any]:
        """
        Parse document to extract vendor, date, and amount fields
        
        Args:
            raw_text (str): Full document text
            key_values (dict): Key-value pairs from document
            
        Returns:
            dict: Parsed fields with extracted data
        """
        parsed_data = {
            'vendor': self._extract_vendor(raw_text, key_values),
            'date': self._extract_date(raw_text, key_values),
            'amount': self._extract_amount(raw_text, key_values)
        }
        
        return parsed_data
    
    def _extract_vendor(self, text: str, key_values: Dict) -> str:
        """
        Extract vendor/company name from document
        
        Args:
            text (str): Document text
            key_values (dict): Key-value pairs
            
        Returns:
            str: Extracted vendor name or empty string
        """
        # Check key-values first
        vendor_keywords = ['vendor', 'company', 'supplier', 'from', 'bill from', 'invoice from']
        
        for key in vendor_keywords:
            if key in key_values:
                return key_values[key]
        
        # Try to extract from text (simple heuristic)
        lines = text.split('\n')
        if lines:
            # Often first non-empty line after header is vendor
            for line in lines[:5]:
                if line.strip() and len(line.strip()) > 3:
                    return line.strip()
        
        return ''
    
    def _extract_date(self, text: str, key_values: Dict) -> str:
        """
        Extract date from document
        
        Args:
            text (str): Document text
            key_values (dict): Key-value pairs
            
        Returns:
            str: Extracted date or empty string
        """
        import re
        
        # Check key-values first
        date_keywords = ['date', 'invoice date', 'date of invoice', 'issued date']
        
        for key in date_keywords:
            if key in key_values:
                return key_values[key]
        
        # Date pattern: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return ''
    
    def _extract_amount(self, text: str, key_values: Dict) -> str:
        """
        Extract monetary amount from document
        
        Args:
            text (str): Document text
            key_values (dict): Key-value pairs
            
        Returns:
            str: Extracted amount or empty string
        """
        import re
        
        # Check key-values first
        amount_keywords = ['amount', 'total', 'total amount', 'invoice total', 'grand total']
        
        for key in amount_keywords:
            if key in key_values:
                return key_values[key]
        
        # Amount pattern: $1,234.56 or 1234.56
        amount_patterns = [
            r'\$[\d,]+\.?\d*',  # $1,234.56
            r'[\d,]+\.\d{2}',   # 1234.56
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Return the last match (usually the total)
                return matches[-1]
        
        return ''
    
    def _calculate_confidence_score(self, response: Dict) -> int:
        """
        Calculate overall confidence score based on Textract confidence values
        
        Args:
            response (dict): Textract API response
            
        Returns:
            int: Confidence score (0-100)
        """
        confidences = []
        
        for block in response.get('Blocks', []):
            if block.get('BlockType') == 'LINE':
                confidence = block.get('Confidence', 0)
                if confidence:
                    confidences.append(confidence)
        
        if not confidences:
            return 0
        
        # Return average confidence
        avg_confidence = sum(confidences) / len(confidences)
        return int(avg_confidence)

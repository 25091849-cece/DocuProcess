"""
DynamoDB Configuration
"""

import os
from typing import Optional


class Config:
    """Configuration for DynamoDB operations"""
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
    
    # DynamoDB Configuration
    DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'DocumentRecords')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = ['DYNAMODB_TABLE_NAME']
        for var in required:
            if not getattr(cls, var, None):
                raise ValueError(f"Missing required configuration: {var}")
        return True
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert configuration to dictionary"""
        return {
            'AWS_REGION': cls.AWS_REGION,
            'DYNAMODB_TABLE_NAME': cls.DYNAMODB_TABLE_NAME,
            'LOG_LEVEL': cls.LOG_LEVEL
        }

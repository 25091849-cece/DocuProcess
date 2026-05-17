"""
Configuration Module
Central place for all environment variables and settings
"""

import os
from typing import Optional


class Config:
    """
    Configuration class for DocuProcess backend
    """
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
    
    # S3 Configuration
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'justicearch-inbox')
    S3_PROCESSED_PREFIX = os.getenv('S3_PROCESSED_PREFIX', 'processed/')
    S3_ARCHIVED_PREFIX = os.getenv('S3_ARCHIVED_PREFIX', 'archived/')
    
    # DynamoDB Configuration
    DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'DocumentRecords')
    
    # Textract Configuration
    TEXTRACT_MAX_RESULTS = int(os.getenv('TEXTRACT_MAX_RESULTS', '100'))
    
    # Confidence Threshold
    # Documents with confidence >= this threshold are auto-approved
    CONFIDENCE_THRESHOLD = int(os.getenv('CONFIDENCE_THRESHOLD', '80'))
    
    # SNS Configuration (for Person 4)
    SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')
    
    # Lambda Configuration
    LAMBDA_TIMEOUT = int(os.getenv('LAMBDA_TIMEOUT', '300'))
    LAMBDA_MEMORY_SIZE = int(os.getenv('LAMBDA_MEMORY_SIZE', '512'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration
        
        Returns:
            bool: True if valid, raises Exception otherwise
        """
        required_vars = [
            'S3_BUCKET_NAME',
            'DYNAMODB_TABLE_NAME'
        ]
        
        for var in required_vars:
            if not getattr(cls, var, None):
                raise ValueError(f"Missing required configuration: {var}")
        
        return True
    
    @classmethod
    def to_dict(cls) -> dict:
        """
        Convert configuration to dictionary
        
        Returns:
            dict: Configuration as dictionary
        """
        return {
            'AWS_REGION': cls.AWS_REGION,
            'S3_BUCKET_NAME': cls.S3_BUCKET_NAME,
            'DYNAMODB_TABLE_NAME': cls.DYNAMODB_TABLE_NAME,
            'CONFIDENCE_THRESHOLD': cls.CONFIDENCE_THRESHOLD,
            'TEXTRACT_MAX_RESULTS': cls.TEXTRACT_MAX_RESULTS,
            'LOG_LEVEL': cls.LOG_LEVEL
        }


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    CONFIDENCE_THRESHOLD = 60  # Lower threshold for testing
    S3_BUCKET_NAME = 'justicearch-inbox-dev'


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    CONFIDENCE_THRESHOLD = 80  # Higher threshold for production
    S3_BUCKET_NAME = 'justicearch-inbox-prod'


class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    CONFIDENCE_THRESHOLD = 50  # Lower for testing
    S3_BUCKET_NAME = 'justicearch-inbox-test'
    DYNAMODB_TABLE_NAME = 'DocumentRecords-test'


# Configuration factory
def get_config(env: Optional[str] = None) -> Config:
    """
    Get configuration based on environment
    
    Args:
        env (str): Environment name (development, production, testing)
        
    Returns:
        Config: Configuration object
    """
    env = env or os.getenv('ENVIRONMENT', 'development')
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return configs.get(env, DevelopmentConfig)

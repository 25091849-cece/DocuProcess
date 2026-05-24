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
    AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID', '767397810758')
    
    # S3 Configuration
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'justicearch-inbox')
    S3_INVOICES_PREFIX = os.getenv('S3_INVOICES_PREFIX', 'invoices/')
    S3_PROCESSED_PREFIX = os.getenv('S3_PROCESSED_PREFIX', 'processed/')
    S3_ARCHIVED_PREFIX = os.getenv('S3_ARCHIVED_PREFIX', 'archived/')
    S3_FAILED_PREFIX = os.getenv('S3_FAILED_PREFIX', 'failed/')
    S3_MAX_FILE_SIZE = int(os.getenv('S3_MAX_FILE_SIZE', '10485760'))  # 10MB in bytes
    S3_ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'tiff']
    S3_ENABLE_VERSIONING = os.getenv('S3_ENABLE_VERSIONING', 'true').lower() == 'true'
    
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
        
        # Validate AWS Account ID
        if not cls.AWS_ACCOUNT_ID:
            raise ValueError("Missing required configuration: AWS_ACCOUNT_ID")
        
        return True
    
    @classmethod
    def get_s3_path(cls, prefix: str, filename: str) -> str:
        """
        Generate full S3 path for a file
        
        Args:
            prefix: S3 prefix (e.g., 'invoices/')
            filename: Original filename
            
        Returns:
            str: Full S3 path
        """
        return f"{prefix}{filename}" if prefix else filename
    
    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """
        Validate if file extension is allowed
        
        Args:
            filename: Filename to validate
            
        Returns:
            bool: True if allowed, False otherwise
        """
        ext = filename.split('.')[-1].lower()
        return ext in cls.S3_ALLOWED_EXTENSIONS
    
    @classmethod
    def to_dict(cls) -> dict:
        """
        Convert configuration to dictionary
        
        Returns:
            dict: Configuration as dictionary
        """
        return {
            'AWS_REGION': cls.AWS_REGION,
            'AWS_ACCOUNT_ID': cls.AWS_ACCOUNT_ID,
            'S3_BUCKET_NAME': cls.S3_BUCKET_NAME,
            'S3_INVOICES_PREFIX': cls.S3_INVOICES_PREFIX,
            'S3_PROCESSED_PREFIX': cls.S3_PROCESSED_PREFIX,
            'S3_ARCHIVED_PREFIX': cls.S3_ARCHIVED_PREFIX,
            'S3_FAILED_PREFIX': cls.S3_FAILED_PREFIX,
            'S3_MAX_FILE_SIZE': cls.S3_MAX_FILE_SIZE,
            'S3_ALLOWED_EXTENSIONS': cls.S3_ALLOWED_EXTENSIONS,
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

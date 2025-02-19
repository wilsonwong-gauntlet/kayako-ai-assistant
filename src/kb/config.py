import os
from typing import Optional, List
from pydantic import BaseSettings

class KayakoSettings(BaseSettings):
    """Kayako API configuration settings."""
    
    # Base URL for the Kayako API
    KAYAKO_BASE_URL: str = os.getenv('KAYAKO_BASE_URL', 'https://your-domain.kayako.com/api/v1')
    
    # OAuth credentials
    KAYAKO_CLIENT_ID: str = os.getenv('KAYAKO_CLIENT_ID', '')
    KAYAKO_CLIENT_SECRET: str = os.getenv('KAYAKO_CLIENT_SECRET', '')
    
    # Optional API key authentication (fallback)
    KAYAKO_API_KEY: Optional[str] = os.getenv('KAYAKO_API_KEY')
    KAYAKO_SECRET_KEY: Optional[str] = os.getenv('KAYAKO_SECRET_KEY')
    
    # Cache settings
    KAYAKO_CACHE_TTL: int = int(os.getenv('KAYAKO_CACHE_TTL', '300'))  # 5 minutes default
    KAYAKO_CACHE_SIZE: int = int(os.getenv('KAYAKO_CACHE_SIZE', '100'))
    
    # Rate limiting
    KAYAKO_RATE_LIMIT: int = int(os.getenv('KAYAKO_RATE_LIMIT', '100'))  # requests per minute
    
    # Retry settings
    KAYAKO_MAX_RETRIES: int = int(os.getenv('KAYAKO_MAX_RETRIES', '3'))
    KAYAKO_RETRY_BACKOFF_MIN: int = int(os.getenv('KAYAKO_RETRY_BACKOFF_MIN', '4'))
    KAYAKO_RETRY_BACKOFF_MAX: int = int(os.getenv('KAYAKO_RETRY_BACKOFF_MAX', '10'))
    
    # SSL/TLS settings
    SSL_CERT_PATH: str = os.getenv('SSL_CERT_PATH', 'certs/server.crt')
    SSL_KEY_PATH: str = os.getenv('SSL_KEY_PATH', 'certs/server.key')
    
    class Config:
        env_file = '.env'
        case_sensitive = True

# Create a global settings instance
kayako_settings = KayakoSettings() 
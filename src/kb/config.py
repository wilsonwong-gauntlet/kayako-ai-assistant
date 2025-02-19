import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class KayakoSettings(BaseSettings):
    """Kayako API configuration settings."""
    
    # Base URL for the Kayako API
    KAYAKO_API_URL: str = "https://your-domain.kayako.com/api/v1"
    KAYAKO_BASE_URL: str = "https://your-domain.kayako.com/api/v1"
    
    # Authentication
    KAYAKO_EMAIL: str
    KAYAKO_PASSWORD: str
    
    # Optional API key authentication (fallback)
    KAYAKO_API_KEY: Optional[str] = None
    KAYAKO_SECRET_KEY: Optional[str] = None
    
    # Cache settings
    KAYAKO_CACHE_TTL: int = 300  # 5 minutes default
    KAYAKO_CACHE_SIZE: int = 100
    
    # Rate limiting
    KAYAKO_RATE_LIMIT: int = 100  # requests per minute
    
    # Retry settings
    KAYAKO_MAX_RETRIES: int = 3
    KAYAKO_RETRY_BACKOFF_MIN: int = 4
    KAYAKO_RETRY_BACKOFF_MAX: int = 10
    
    # SSL/TLS settings
    SSL_CERT_PATH: str = "certs/server.crt"
    SSL_KEY_PATH: str = "certs/server.key"
    
    # OpenAI settings
    OPENAI_API_KEY: str
    
    # Twilio settings
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # Application settings
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    BASE_URL: str = "http://localhost:8000"
    
    # Ngrok settings
    NGROK_AUTHTOKEN: Optional[str] = None
    
    # Allow environment variables
    model_config = SettingsConfigDict(env_file='.env', case_sensitive=True)

# Create a global settings instance
kayako_settings = KayakoSettings() 
import os
from dotenv import load_dotenv

def test_core_environment_variables():
    """Test that core environment variables (OpenAI, Twilio) are set."""
    load_dotenv()
    
    required_vars = [
        'OPENAI_API_KEY',
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN'
    ]
    
    for var in required_vars:
        assert os.getenv(var) is not None, f"Environment variable {var} is not set"
        assert os.getenv(var) != "", f"Environment variable {var} is empty"
        assert not os.getenv(var).startswith("your_"), f"Environment variable {var} still has placeholder value"

def test_kayako_environment_variables():
    """Test Kayako environment variables if they are set."""
    load_dotenv()
    
    kayako_vars = [
        'KAYAKO_API_URL',
        'KAYAKO_API_KEY',
        'KAYAKO_SECRET_KEY'
    ]
    
    # Check if any Kayako variables are set
    kayako_configured = any(os.getenv(var) for var in kayako_vars)
    
    if kayako_configured:
        for var in kayako_vars:
            assert os.getenv(var) is not None, f"Environment variable {var} is not set"
            assert os.getenv(var) != "", f"Environment variable {var} is empty"
            assert not os.getenv(var).startswith("your_"), f"Environment variable {var} still has placeholder value" 
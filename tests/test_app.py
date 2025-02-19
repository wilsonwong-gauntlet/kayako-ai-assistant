import pytest
from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import patch
import hmac
import hashlib
import base64

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    health_data = response.json()
    assert health_data["status"] == "healthy"
    assert "twilio_configured" in health_data  # Allow this field to be present

def test_voice_endpoint():
    # Mock Twilio signature validation
    with patch('src.main.validate_twilio_request', return_value=True):
        response = client.post("/voice", 
            data={
                "CallSid": "test-call-sid",
                "From": "+1234567890",
                "To": "+0987654321"
            },
            headers={
                "X-Twilio-Signature": "dummy-signature"
            }
        )
        assert response.status_code == 200
        assert "<Response>" in response.text  # Basic TwiML response check
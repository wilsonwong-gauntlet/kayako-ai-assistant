from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "0.1.0"}

def test_voice_endpoint():
    response = client.post("/voice")
    assert response.status_code == 200
    assert "message" in response.json() 
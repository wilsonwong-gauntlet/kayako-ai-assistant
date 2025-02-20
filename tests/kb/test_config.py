import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(".env.test", override=True)

# Test configuration
TEST_CONFIG = {
    'base_url': os.getenv('KAYAKO_API_URL', 'https://test-instance.kayako.com/api/v1'),
    'client_id': os.getenv('KAYAKO_CLIENT_ID', 'test_client_id'),
    'client_secret': os.getenv('KAYAKO_SECRET_KEY', 'test_client_secret'),
}

# Test data
TEST_USER = {
    'email': 'test.user@example.com',
    'full_name': 'Test User',
    'phone': '+1234567890',
    'organization': 'Test Org',
    'role': 'customer'
}

TEST_MESSAGE = {
    'content': 'This is a test message',
    'type': 'reply',
    'is_private': False
}

TEST_TICKET = {
    'id': 'ticket-123',
    'subject': 'Test Ticket',
    'contents': 'This is a test ticket',
    'channel': 'phone',
    'channel_id': 1,
    'type_id': 1,
    'priority_id': 1,
    'status': 'ACTIVE'
} 
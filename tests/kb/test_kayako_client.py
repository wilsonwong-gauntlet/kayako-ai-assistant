import pytest
from datetime import datetime, timezone
import aiohttp
from unittest.mock import AsyncMock, patch

from src.kb.kayako_client import RealKayakoAPI
from src.kb.interfaces import User, Message, Ticket
from tests.kb.test_config import TEST_CONFIG, TEST_USER, TEST_MESSAGE, TEST_TICKET

@pytest.fixture
async def api_client():
    """Create a test instance of RealKayakoAPI."""
    client = RealKayakoAPI(
        base_url=TEST_CONFIG['base_url'],
        client_id=TEST_CONFIG['client_id'],
        client_secret=TEST_CONFIG['client_secret']
    )
    return client

@pytest.mark.asyncio
async def test_auth_token_refresh(api_client):
    """Test OAuth token refresh functionality."""
    # Mock token response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        'access_token': 'test_token',
        'expires_in': 3600
    }
    
    with patch('aiohttp.ClientSession.post', return_value=mock_response):
        token = await api_client.auth_manager.get_token()
        assert token == 'test_token'
        assert api_client.auth_manager.token_expiry is not None

@pytest.mark.asyncio
async def test_create_user(api_client):
    """Test user creation."""
    # Mock user creation response
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json.return_value = {
        'id': 'test123',
        **TEST_USER
    }
    
    with patch('aiohttp.ClientSession.post', return_value=mock_response):
        user = User(**TEST_USER)
        user_id = await api_client.create_user(user)
        assert user_id == 'test123'
        # Verify cache
        assert f"user:test123" in api_client.user_cache

@pytest.mark.asyncio
async def test_get_user(api_client):
    """Test retrieving a user."""
    # Mock user retrieval response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        'id': 'test123',
        **TEST_USER
    }
    
    with patch('aiohttp.ClientSession.get', return_value=mock_response):
        user = await api_client.get_user('test123')
        assert user is not None
        assert user.email == TEST_USER['email']
        assert user.full_name == TEST_USER['full_name']

@pytest.mark.asyncio
async def test_create_message(api_client):
    """Test message creation in a conversation."""
    # Mock message creation response
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json.return_value = {
        'id': 'msg123',
        'conversation_id': 'conv123',
        'created_at': datetime.now(timezone.utc).isoformat(),
        **TEST_MESSAGE
    }
    
    with patch('aiohttp.ClientSession.post', return_value=mock_response):
        message = Message(
            id='',
            conversation_id='conv123',
            **TEST_MESSAGE,
            created_at=datetime.now(timezone.utc)
        )
        message_id = await api_client.create_message('conv123', message)
        assert message_id == 'msg123'
        # Verify cache
        assert f"message:msg123" in api_client.message_cache

@pytest.mark.asyncio
async def test_get_messages(api_client):
    """Test retrieving messages from a conversation."""
    # Mock messages retrieval response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        'data': [
            {
                'id': 'msg123',
                'conversation_id': 'conv123',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': None,
                **TEST_MESSAGE
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.get', return_value=mock_response):
        messages = await api_client.get_messages('conv123')
        assert len(messages) == 1
        assert messages[0].id == 'msg123'
        assert messages[0].content == TEST_MESSAGE['content']

@pytest.mark.asyncio
async def test_create_ticket(api_client):
    """Test ticket creation."""
    # Mock ticket creation response
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json.return_value = {
        'id': 'tick123',
        **TEST_TICKET
    }
    
    with patch('aiohttp.ClientSession.post', return_value=mock_response):
        ticket = Ticket(**TEST_TICKET)
        ticket_id = await api_client.create_ticket(ticket)
        assert ticket_id == 'tick123'

@pytest.mark.asyncio
async def test_error_handling(api_client):
    """Test error handling and retry logic."""
    # Mock a failing response that succeeds on retry
    mock_fail = AsyncMock()
    mock_fail.status = 500
    mock_fail.raise_for_status.side_effect = aiohttp.ClientError
    
    mock_success = AsyncMock()
    mock_success.status = 200
    mock_success.json.return_value = {
        'id': 'test123',
        **TEST_USER
    }
    
    with patch('aiohttp.ClientSession.get', side_effect=[mock_fail, mock_success]):
        user = await api_client.get_user('test123')
        assert user is not None
        assert user.email == TEST_USER['email']

@pytest.mark.asyncio
async def test_cache_invalidation(api_client):
    """Test cache invalidation on updates."""
    # Mock initial get response
    mock_get = AsyncMock()
    mock_get.status = 200
    mock_get.json.return_value = {
        'id': 'test123',
        **TEST_USER
    }
    
    # Mock update response
    mock_update = AsyncMock()
    mock_update.status = 200
    updated_user = {**TEST_USER, 'full_name': 'Updated Name'}
    mock_update.json.return_value = {
        'id': 'test123',
        **updated_user
    }
    
    with patch('aiohttp.ClientSession.get', return_value=mock_get):
        # Initial get
        user = await api_client.get_user('test123')
        assert user.full_name == TEST_USER['full_name']
        
        with patch('aiohttp.ClientSession.put', return_value=mock_update):
            # Update user
            updated = User(id='test123', **updated_user)
            success = await api_client.update_user('test123', updated)
            assert success
            
            # Verify cache was updated
            cached_user = api_client.user_cache.get(f"user:test123")
            assert cached_user.full_name == 'Updated Name'

def test_cache_ttl(api_client):
    """Test cache TTL settings."""
    assert api_client.search_cache.ttl == 300  # 5 minutes
    assert api_client.user_cache.ttl == 60    # 1 minute
    assert api_client.message_cache.ttl == 30  # 30 seconds 
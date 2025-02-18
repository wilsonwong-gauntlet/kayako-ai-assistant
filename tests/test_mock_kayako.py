"""Tests for mock Kayako API implementation."""

import pytest
from src.kb.interfaces import Article, Ticket
from src.kb.mock_kayako import MockKayakoAPI

@pytest.fixture
def api():
    return MockKayakoAPI()

@pytest.mark.asyncio
async def test_search_articles(api):
    """Test article search functionality."""
    # Search by title
    results = await api.search_articles("password")
    assert len(results) == 1
    assert results[0].title == "How to Reset Your Password"

    # Search by content
    results = await api.search_articles("subscription")
    assert len(results) == 1
    assert results[0].title == "Billing Cycle Explained"

    # Search by tag
    results = await api.search_articles("onboarding")
    assert len(results) == 1
    assert results[0].title == "Getting Started Guide"

@pytest.mark.asyncio
async def test_create_ticket(api):
    """Test ticket creation."""
    ticket = Ticket(
        id="",  # Will be set by API
        subject="Test Issue",
        description="This is a test ticket",
        requester_email="test@example.com",
        phone_number="+1234567890",
        status="open",
        priority="medium"
    )
    
    ticket_id = await api.create_ticket(ticket)
    assert ticket_id.startswith("tick-")
    
    # Test invalid status
    with pytest.raises(ValueError):
        invalid_ticket = ticket.model_copy()
        invalid_ticket.status = "invalid"
        await api.create_ticket(invalid_ticket)

@pytest.mark.asyncio
async def test_get_article(api):
    """Test retrieving specific articles."""
    article = await api.get_article("art-001")
    assert article is not None
    assert article.title == "How to Reset Your Password"
    
    # Test non-existent article
    article = await api.get_article("non-existent")
    assert article is None 
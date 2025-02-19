import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pytest_asyncio
from src.conversation.flow import ConversationFlowManager
from src.kb.kayako_client import RealKayakoAPI
from src.tickets.ticket_manager import TicketManager

@pytest_asyncio.fixture(scope="function")
async def flow_manager():
    """Fixture for conversation flow manager."""
    manager = ConversationFlowManager()
    await manager.initialize()
    yield manager

@pytest_asyncio.fixture(scope="function")
async def api_client():
    """Fixture for Kayako API client."""
    client = RealKayakoAPI(
        base_url=os.getenv('KAYAKO_API_URL'),
        email=os.getenv('KAYAKO_EMAIL'),
        password=os.getenv('KAYAKO_PASSWORD')
    )
    await client.initialize()
    yield client
    await client.close()

@pytest_asyncio.fixture(scope="function")
async def ticket_manager():
    """Fixture for ticket manager."""
    manager = TicketManager()
    yield manager 
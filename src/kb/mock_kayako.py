"""Mock implementation of Kayako API for development."""

import uuid
from typing import List, Optional
from .interfaces import Article, Ticket, KayakoAPI
from .mock_data import SAMPLE_ARTICLES, SAMPLE_TICKETS, TICKET_STATUSES, TICKET_PRIORITIES

class MockKayakoAPI(KayakoAPI):
    """Mock implementation of Kayako API for development."""
    
    def __init__(self):
        """Initialize with sample data."""
        self._articles = {a["id"]: Article(**a) for a in SAMPLE_ARTICLES}
        self._tickets = {t["id"]: Ticket(**t) for t in SAMPLE_TICKETS}

    async def search_articles(self, query: str) -> List[Article]:
        """Search articles using simple keyword matching."""
        query = query.lower()
        matches = []
        
        for article in self._articles.values():
            # Search in title, content, and tags
            if (query in article.title.lower() or
                query in article.content.lower() or
                any(query in tag.lower() for tag in article.tags)):
                matches.append(article)
        
        return matches

    async def create_ticket(self, ticket: Ticket) -> str:
        """Create a new support ticket."""
        # Validate status
        if ticket.status not in ["ACTIVE", "CLOSED", "PENDING"]:
            raise ValueError(f"Invalid status. Must be one of: ACTIVE, CLOSED, PENDING")
        
        # Generate new ticket ID
        ticket_id = f"tick-{str(uuid.uuid4())[:8]}"
        ticket.id = ticket_id
        
        # Store ticket
        self._tickets[ticket_id] = ticket
        
        # Log ticket creation
        print(f"\nCreating ticket: {ticket_id}")
        print(f"Subject: {ticket.subject}")
        print(f"Contents: {ticket.contents}")
        print(f"Status: {ticket.status}")
        print(f"Total tickets: {len(self._tickets)}\n")
        
        return ticket_id

    async def get_article(self, article_id: str) -> Optional[Article]:
        """Get a specific article by ID."""
        return self._articles.get(article_id)

    # Helper methods for testing
    def add_article(self, article: Article) -> None:
        """Add a new article to the mock database."""
        self._articles[article.id] = article

    def add_ticket(self, ticket: Ticket) -> None:
        """Add a new ticket to the mock database."""
        self._tickets[ticket.id] = ticket 
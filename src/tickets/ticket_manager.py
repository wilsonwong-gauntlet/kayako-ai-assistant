"""Ticket management functionality for handling customer support tickets."""

import re
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from ..kb.interfaces import Ticket
from ..kb.mock_kayako import MockKayakoAPI
from ..conversation.state import ConversationContext, Message

class TicketMetadata(BaseModel):
    """Additional metadata for ticket creation."""
    source: str = "voice_assistant"
    channel: str = "phone"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    conversation_id: str
    transcript: List[Dict[str, str]]

class TicketManager:
    """Manages support ticket creation and updates."""
    
    def __init__(self):
        """Initialize the ticket manager with mock Kayako API."""
        self.api = MockKayakoAPI()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # Remove common separators and whitespace
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
        # Match various formats:
        # - 10 digits (US numbers)
        # - 11 digits starting with 1 (US numbers with country code)
        # - International numbers (up to 15 digits with optional + prefix)
        pattern = r'^\+?1?\d{10,14}$'
        return bool(re.match(pattern, cleaned))
    
    def _format_transcript(self, context: ConversationContext) -> List[Dict[str, str]]:
        """Format conversation transcript for ticket."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in context.messages
        ]
    
    def _determine_priority(self, context: ConversationContext) -> str:
        """Determine ticket priority based on conversation context."""
        # Check for keywords indicating urgency
        urgent_keywords = ["urgent", "emergency", "critical", "broken", "error"]
        
        # Check last few messages for urgent keywords
        recent_messages = " ".join(
            msg.content.lower() 
            for msg in context.messages[-3:] 
            if msg.role == "user"
        )
        
        if any(keyword in recent_messages for keyword in urgent_keywords):
            return "high"
        
        return "medium"
    
    async def create_ticket(
        self,
        context: ConversationContext,
        subject: str,
        description: str,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> str:
        """
        Create a new support ticket.
        
        Args:
            context: Conversation context
            subject: Ticket subject
            description: Ticket description
            email: Customer email (optional)
            phone: Customer phone number (optional)
        
        Returns:
            Ticket ID
        
        Raises:
            ValueError: If neither email nor phone is provided
        """
        if not email and not phone:
            raise ValueError("Either email or phone number must be provided")
        
        if email and not self._validate_email(email):
            raise ValueError("Invalid email format")
        
        if phone and not self._validate_phone(phone):
            raise ValueError("Invalid phone number format")
        
        # Create ticket metadata
        metadata = TicketMetadata(
            conversation_id=context.conversation_id,
            transcript=self._format_transcript(context)
        )
        
        # Create ticket
        ticket = Ticket(
            id="",  # Will be set by API
            subject=subject,
            description=description,
            requester_email=email or "",
            phone_number=phone,
            status="open",
            priority=self._determine_priority(context)
        )
        
        # Create ticket through API
        ticket_id = await self.api.create_ticket(ticket)
        
        return ticket_id
    
    def extract_contact_info(self, message: str) -> Dict[str, Optional[str]]:
        """
        Extract email and phone number from message if present.
        
        Args:
            message: User message to extract from
        
        Returns:
            Dictionary with 'email' and 'phone' keys
        """
        # Extract email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
        email = email_match.group(0) if email_match else None
        
        # Extract phone number
        phone_match = re.search(r'\+?1?\d{10,15}', message)
        phone = phone_match.group(0) if phone_match else None
        
        return {"email": email, "phone": phone}
    
    def format_ticket_description(self, context: ConversationContext) -> str:
        """Format ticket description from conversation context."""
        # Get the initial issue description
        initial_messages = [
            msg.content for msg in context.messages[:3] 
            if msg.role == "user"
        ]
        
        # Get the last attempted solution
        last_assistant_msg = next(
            (msg.content for msg in reversed(context.messages) 
             if msg.role == "assistant"),
            "No solution provided"
        )
        
        description = f"""
Issue Description:
{' '.join(initial_messages)}

Last Attempted Solution:
{last_assistant_msg}

Full transcript attached in ticket metadata.
        """.strip()
        
        return description 
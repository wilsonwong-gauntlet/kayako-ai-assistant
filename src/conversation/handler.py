"""Conversation handler using GPT for intent detection and response generation."""

import os
from typing import Dict, List, Optional, Tuple
import uuid
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json
import sentry_sdk

from .state import (
    ConversationContext,
    ConversationState,
    Intent,
    Entity,
    Message
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ConversationHandler:
    """Handles conversation flow and GPT interactions."""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationContext] = {}
    
    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = ConversationContext(
            conversation_id=conversation_id,
            current_state=ConversationState.GREETING
        )
        return conversation_id
    
    def extract_contact_info(self, message: str) -> Dict[str, Optional[str]]:
        """
        Extract email and phone number from message if present.
        
        Args:
            message: User message to extract from
        
        Returns:
            Dictionary with 'email' and 'phone' keys
        """
        with sentry_sdk.start_span(op="conversation.extract_contact", description="Extract contact info from message"):
            # Clean up the message for email extraction
            cleaned_message = message.lower().replace(" at ", "@").replace(" dot ", ".")
            
            # Extract email with more flexible pattern
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w{2,}', cleaned_message)
            email = email_match.group(0) if email_match else None
            
            # Extract phone number (support various formats)
            phone_patterns = [
                r'\+?1?\d{10}',  # Basic 10-digit
                r'\+?1?\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # With separators
                r'\+?1?\(\d{3}\)\s*\d{3}[-.\s]\d{4}'  # With parentheses
            ]
            
            phone = None
            for pattern in phone_patterns:
                phone_match = re.search(pattern, message)
                if phone_match:
                    phone = phone_match.group(0)
                    break
            
            # Log validation results to Sentry
            sentry_sdk.set_context("contact_validation", {
                "message": message,
                "cleaned_message": cleaned_message,
                "email_found": email is not None,
                "phone_found": phone is not None,
                "email_value": email,
                "phone_value": phone
            })
            
            return {"email": email, "phone": phone}
    
    async def detect_intent(self, text: str) -> Tuple[Intent, List[Entity]]:
        """Detect intent and entities from user input using GPT."""
        system_prompt = """You are an intent detection system for a customer service AI.
Analyze the user's message and identify:
1. The primary intent from these options (use EXACTLY these values):
   - "general_query" - For general questions or unclear intents
   - "password_reset" - For password-related issues
   - "billing_issue" - For billing or payment problems
   - "technical_problem" - For technical issues or errors
   - "account_access" - For account access issues (not password related)
   - "confirm" - For positive confirmations or agreement
   - "deny" - For negative responses or disagreement
   - "end_conversation" - For any indication that the user wants to end the conversation (e.g. "bye", "goodbye", "that's all", "thanks, I'm done", "have a good day", etc.)
   - "unknown" - When no other intent matches

2. Any relevant entities (name, email, account number, etc.)

Respond in JSON format:
{
    "intent": "intent_value_from_list_above",
    "entities": [
        {"type": "entity_type", "value": "extracted_value", "confidence": 0.95}
    ]
}

Example responses:
For "Thanks, that's all I needed today":
{
    "intent": "end_conversation",
    "entities": []
}

For "I can't log in to my account":
{
    "intent": "account_access",
    "entities": []
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        parsed = json.loads(result)
        
        # Convert to our types
        intent = Intent(parsed["intent"])
        entities = [Entity(**entity) for entity in parsed["entities"]]
        
        return intent, entities
    
    async def generate_response(self, context: ConversationContext) -> str:
        """Generate appropriate response based on conversation context."""
        messages = context.get_context_window()
        
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.7,
            max_tokens=150  # Keep responses concise for voice
        )
        
        return response.choices[0].message.content
    
    async def process_message(self, conversation_id: str, message: str) -> str:
        """Process a user message and return the appropriate response."""
        # Get or create conversation context
        context = self.conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Detect intent and entities
        intent, entities = await self.detect_intent(message)
        
        # Add user message to context
        context.add_message(
            role="user",
            content=message,
            intent=intent,
            entities=entities
        )
        
        # Check for state transition
        if new_state := context.should_transition_state():
            context.transition_state(new_state)
        
        # Generate response
        response = await self.generate_response(context)
        
        # Add assistant response to context
        context.add_message(
            role="assistant",
            content=response
        )
        
        return response
    
    def get_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get the context for a specific conversation."""
        return self.conversations.get(conversation_id) 
"""Core conversation flow management."""

from typing import Optional, Tuple
import uuid
from .state import ConversationState, Intent, ConversationContext
from .handler import ConversationHandler
from ..kb.search import KBSearchEngine
from ..tickets.ticket_manager import TicketManager

class ConversationFlowManager:
    """Manages the complete conversation flow, including KB search and escalation."""
    
    def __init__(self):
        """Initialize the flow manager."""
        self.conversation_handler = ConversationHandler()
        self.kb_engine = KBSearchEngine()
        self.ticket_manager = TicketManager()
        self.initialized = False
    
    async def initialize(self):
        """Initialize required components."""
        if not self.initialized:
            await self.kb_engine.initialize()
            self.initialized = True
    
    async def start_conversation(self) -> Tuple[str, str]:
        """
        Start a new conversation.
        
        Returns:
            Tuple of (conversation_id, initial_greeting)
        """
        await self.initialize()
        
        # Create new conversation
        conversation_id = self.conversation_handler.create_conversation()
        context = self.conversation_handler.get_conversation_context(conversation_id)
        
        # Generate initial greeting
        greeting = await self.conversation_handler.generate_response(context)
        
        return conversation_id, greeting
    
    async def process_message(self, conversation_id: str, message: str) -> str:
        """
        Process a user message and generate an appropriate response.
        
        Args:
            conversation_id: ID of the conversation
            message: User's message
        
        Returns:
            Assistant's response
        """
        await self.initialize()
        
        # Get conversation context
        context = self.conversation_handler.get_conversation_context(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Detect intent and entities
        intent, entities = await self.conversation_handler.detect_intent(message)
        
        # Add user message to context
        context.add_message(
            role="user",
            content=message,
            intent=intent,
            entities=entities
        )
        
        # Handle based on current state
        response = await self._handle_state(context, message, intent)
        
        # Add assistant response to context
        context.add_message(
            role="assistant",
            content=response
        )
        
        return response
    
    def _is_capability_query(self, message: str) -> bool:
        """Check if the message is asking about system capabilities."""
        capability_keywords = [
            "what can you do",
            "how can you help",
            "what do you do",
            "your capabilities",
            "help me with",
            "assist me with"
        ]
        return any(keyword in message.lower() for keyword in capability_keywords)
    
    async def _handle_state(self, context: ConversationContext, message: str, intent: Intent) -> str:
        """Handle the conversation based on current state."""
        # Special handling for capability queries
        if self._is_capability_query(message):
            context.transition_state(ConversationState.COLLECTING_ISSUE)
            return """I'm your AI customer service assistant. I can help you with:
1. Password resets and account access
2. Billing and subscription questions
3. Technical issues and troubleshooting
4. General product information

What specific issue can I help you with today?"""
        
        # For any state, first try to find relevant KB article
        kb_response = await self.kb_engine.search_and_summarize(message)
        
        if context.current_state == ConversationState.GREETING:
            if kb_response:
                context.transition_state(ConversationState.PROVIDING_SOLUTION)
                return f"{kb_response}\n\nWas this information helpful?"
            else:
                context.transition_state(ConversationState.COLLECTING_DETAILS)
                return "I apologize, but I don't have specific information about that topic. Could you please provide more details about what you're looking for? This will help me create a ticket for our support team."
        
        elif context.current_state == ConversationState.COLLECTING_ISSUE:
            if kb_response:
                context.transition_state(ConversationState.PROVIDING_SOLUTION)
                return f"{kb_response}\n\nWas this information helpful?"
            else:
                context.transition_state(ConversationState.COLLECTING_DETAILS)
                return "I don't have specific information about that in our knowledge base. Could you please provide more details about your request? This will help me create a ticket for our support team."
        
        elif context.current_state == ConversationState.PROVIDING_SOLUTION:
            if intent == Intent.CONFIRM:
                context.transition_state(ConversationState.ENDING_CALL)
                return "I'm glad I could help! Is there anything else you need assistance with?"
            elif intent == Intent.DENY:
                context.transition_state(ConversationState.COLLECTING_DETAILS)
                return "I apologize that wasn't helpful. Could you provide more details about your issue so I can better assist you?"
            else:
                # Search KB again with the new information
                kb_response = await self.kb_engine.search_and_summarize(message)
                if kb_response:
                    return f"{kb_response}\n\nDid this answer your question?"
                else:
                    context.transition_state(ConversationState.COLLECTING_DETAILS)
                    return "I see. Let me get some more information to help you better. Could you please provide specific details about what you're trying to do?"
        
        elif context.current_state == ConversationState.COLLECTING_DETAILS:
            # Try KB search with accumulated context
            full_context = " ".join([m.content for m in context.messages[-3:] if m.role == "user"])
            kb_response = await self.kb_engine.search_and_summarize(full_context)
            
            if kb_response:
                context.transition_state(ConversationState.PROVIDING_SOLUTION)
                return f"{kb_response}\n\nIs this what you were looking for?"
            else:
                # Extract any contact info from the message
                contact_info = self.ticket_manager.extract_contact_info(message)
                if contact_info["email"] or contact_info["phone"]:
                    # Create ticket with provided contact info
                    try:
                        description = self.ticket_manager.format_ticket_description(context)
                        ticket_id = await self.ticket_manager.create_ticket(
                            context=context,
                            subject="Support Request from Voice Assistant",
                            description=description,
                            email=contact_info["email"],
                            phone=contact_info["phone"]
                        )
                        context.transition_state(ConversationState.ENDING_CALL)
                        return ("I've created a support ticket for you and our team will contact you soon. "
                               "Is there anything else I can help you with?")
                    except ValueError as e:
                        context.transition_state(ConversationState.CREATING_TICKET)
                        return "I couldn't validate your contact information. Could you please provide a valid email address?"
                else:
                    context.transition_state(ConversationState.CREATING_TICKET)
                    return "I'll need to create a ticket for further assistance. Could you please provide your email address?"
        
        elif context.current_state == ConversationState.CREATING_TICKET:
            # Extract contact info from message
            contact_info = self.ticket_manager.extract_contact_info(message)
            if not (contact_info["email"] or contact_info["phone"]):
                return "I couldn't find a valid email address or phone number. Could you please provide one?"
            
            try:
                # Create ticket
                description = self.ticket_manager.format_ticket_description(context)
                ticket_id = await self.ticket_manager.create_ticket(
                    context=context,
                    subject="Support Request from Voice Assistant",
                    description=description,
                    email=contact_info["email"],
                    phone=contact_info["phone"]
                )
                context.transition_state(ConversationState.ENDING_CALL)
                return ("I've created a support ticket for you and our team will contact you soon. "
                       "Is there anything else I can help you with?")
            except ValueError as e:
                return f"I couldn't create the ticket: {str(e)}. Please provide a valid email address or phone number."
        
        elif context.current_state == ConversationState.ENDING_CALL:
            if intent in [Intent.CONFIRM, Intent.GENERAL_QUERY]:
                context.transition_state(ConversationState.COLLECTING_ISSUE)
                return "Of course! What else can I help you with?"
            else:
                return "Thank you for contacting us. Have a great day!"
        
        # Default response if no specific handler
        return await self.conversation_handler.generate_response(context) 
"""Core conversation flow management."""

from typing import Optional, Tuple
import uuid
from .state import ConversationState, Intent, ConversationContext
from .handler import ConversationHandler
from ..kb.search import KBSearchEngine
from ..tickets.ticket_manager import TicketManager
import sentry_sdk
from ..monitoring.metrics import metrics_manager

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
        
        try:
            # First try to find relevant knowledge base article
            kb_response = await self.kb_engine.search_and_summarize(message)
            
            # Get metrics for the conversation's call
            metrics = None
            for call_sid, call_metrics in metrics_manager.active_calls.items():
                if conversation_id in str(call_metrics.call_sid):
                    metrics = call_metrics
                    break
            
            # Track KB search result
            if metrics:
                metrics.track_kb_search(kb_response is not None)
            
            if kb_response:
                context.transition_state(ConversationState.PROVIDING_SOLUTION)
                return f"{kb_response}\n\nWas this information helpful?"
            
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
            
        except Exception as e:
            # Log error with context
            sentry_sdk.capture_exception(
                e,
                extras={
                    "conversation_id": conversation_id,
                    "message": message,
                    "state": context.to_dict() if context else None
                }
            )
            return "I apologize, but I encountered an error processing your request. Could you please try rephrasing that?"

    async def _handle_state(self, context: ConversationContext, message: str, intent: Intent) -> str:
        """
        Handle the conversation based on current state.
        
        Args:
            context: Current conversation context
            message: User's message
            intent: Detected intent
            
        Returns:
            Assistant's response
        """
        state = context.current_state
        
        if state == ConversationState.INITIAL:
            # Initial state - determine if we can help or need to create ticket
            if intent == Intent.GREETING:
                context.transition_state(ConversationState.GATHERING_INFO)
                return "Hello! How can I help you today?"
            else:
                context.transition_state(ConversationState.GATHERING_INFO)
                return await self.conversation_handler.generate_response(context)
        
        elif state == ConversationState.GATHERING_INFO:
            # Gathering information about the user's issue
            if intent == Intent.GOODBYE:
                context.transition_state(ConversationState.ENDED)
                return "Thank you for contacting us. Have a great day!"
            elif intent == Intent.ESCALATE:
                context.transition_state(ConversationState.CREATING_TICKET)
                return "I'll need to create a ticket for further assistance. Could you please provide your email address?"
            else:
                return await self.conversation_handler.generate_response(context)
        
        elif state == ConversationState.PROVIDING_SOLUTION:
            # After providing KB article, check if it was helpful
            if intent == Intent.AFFIRM:
                context.transition_state(ConversationState.ENDED)
                return "Great! Is there anything else I can help you with?"
            elif intent == Intent.DENY:
                context.transition_state(ConversationState.CREATING_TICKET)
                return "I'm sorry the information wasn't helpful. Let me create a ticket for further assistance. Could you please provide your email address?"
            else:
                return await self.conversation_handler.generate_response(context)
        
        elif state == ConversationState.CREATING_TICKET:
            # Creating support ticket
            contact_info = self.conversation_handler.extract_contact_info(message)
            if contact_info:
                # Create ticket with conversation history
                ticket_id = await self.ticket_manager.create_ticket(
                    contact_info=contact_info,
                    conversation_history=context.messages
                )
                context.transition_state(ConversationState.ENDED)
                return "I've created a support ticket for you and our team will contact you soon. Is there anything else I can help you with?"
            else:
                return "I couldn't find a valid email address or phone number. Could you please provide one?"
        
        elif state == ConversationState.ENDED:
            # Conversation ended
            if intent == Intent.AFFIRM:
                context.transition_state(ConversationState.GATHERING_INFO)
                return "What else can I help you with?"
            elif intent == Intent.DENY or intent == Intent.GOODBYE:
                return "Thank you for contacting us. Have a great day!"
            else:
                context.transition_state(ConversationState.GATHERING_INFO)
                return await self.conversation_handler.generate_response(context)
        
        # Default response if state not handled
        return await self.conversation_handler.generate_response(context)
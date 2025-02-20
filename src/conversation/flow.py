"""Core conversation flow management."""

from typing import Optional, Tuple
import uuid
import logging
from .state import ConversationState, Intent, ConversationContext
from .handler import ConversationHandler
from ..kb.search import KBSearchEngine
from ..tickets.ticket_manager import TicketManager
import sentry_sdk
from ..monitoring.metrics import metrics_manager

logger = logging.getLogger(__name__)

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
            try:
                await self.kb_engine.initialize()
                self.initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize KB engine: {str(e)}")
                # Don't raise the error, we can try again later
                # Instead, return a friendly message to the user
                return "I'm having trouble accessing our knowledge base right now. " \
                       "I can still help you create a support ticket if needed."
    
    async def start_conversation(self) -> Tuple[str, str]:
        """
        Start a new conversation.
        
        Returns:
            Tuple of (conversation_id, initial_greeting)
        """
        try:
            # Try to initialize, but don't fail if it doesn't work
            init_message = await self.initialize()
            
            # Create new conversation with initial state
            conversation_id = self.conversation_handler.create_conversation()
            context = self.conversation_handler.get_conversation_context(conversation_id)
            
            # Set initial state to COLLECTING_ISSUE to skip greeting
            context.transition_state(ConversationState.COLLECTING_ISSUE)
            
            # Generate initial greeting
            if init_message:
                # If we had initialization issues, use that message
                greeting = init_message
            else:
                greeting = "Welcome to Kayako Support. How can I help you today?"
            
            return conversation_id, greeting
            
        except Exception as e:
            logger.error(f"Error starting conversation: {str(e)}")
            # Return a generic conversation ID and friendly message
            return str(uuid.uuid4()), "I'm having some technical difficulties, but I'll do my best to help you. What can I assist you with?"
    
    async def process_message(self, conversation_id: str, message: str) -> str:
        """
        Process a user message and generate an appropriate response.
        
        Args:
            conversation_id: ID of the conversation
            message: User's message
        
        Returns:
            Assistant's response
        """
        try:
            # Try to initialize if not already done
            if not self.initialized:
                init_message = await self.initialize()
                if init_message:
                    return init_message
            
            # Get conversation context
            context = self.conversation_handler.get_conversation_context(conversation_id)
            if not context:
                logger.error(f"Conversation {conversation_id} not found")
                return "I seem to have lost track of our conversation. Could you please repeat what you were saying?"
            
            try:
                # Detect intent and entities first
                intent, entities = await self.conversation_handler.detect_intent(message)
                
                # Add user message to context
                context.add_message(
                    role="user",
                    content=message,
                    intent=intent,
                    entities=entities
                )
                
                # Process based on current state
                if context.current_state == ConversationState.COLLECTING_ISSUE:
                    # First check if this message contains contact info
                    contact_info = self.ticket_manager.extract_contact_info(message, context=context)
                    if contact_info.get("email") or contact_info.get("phone"):
                        # Store contact info and create ticket
                        context.metadata["email"] = contact_info.get("email")
                        context.metadata["phone"] = contact_info.get("phone")
                        context.transition_state(ConversationState.CREATING_TICKET)
                        success, response = await self._create_support_ticket(context)
                        if success:
                            context.transition_state(ConversationState.ENDED)
                        return response
                    
                    # No contact info, try to find relevant knowledge base article
                    kb_response = None
                    if self.initialized:
                        kb_response = await self.kb_engine.search_and_summarize(message)
                        logger.info(f"KB search result for '{message}': {kb_response is not None}")
                    
                    if kb_response:
                        context.transition_state(ConversationState.PROVIDING_SOLUTION)
                        response = f"{kb_response}\n\nWas this information helpful?"
                    else:
                        # No relevant KB articles found, ask for contact info
                        context.transition_state(ConversationState.CREATING_TICKET)
                        response = "I apologize, but I couldn't find a specific solution for your issue in our knowledge base. Let me create a support ticket so our team can assist you. Could you please provide your email address?"
                elif context.current_state == ConversationState.CREATING_TICKET:
                    # Collecting contact information and additional details
                    contact_info = self.ticket_manager.extract_contact_info(message, context=context)
                    logger.info(f"Extracted contact info: {contact_info}")
                    
                    if contact_info.get("email") or contact_info.get("phone"):
                        # Store contact info in context for later use
                        context.metadata["email"] = contact_info.get("email")
                        context.metadata["phone"] = contact_info.get("phone")
                        
                        # Create ticket immediately with what we have
                        success, response = await self._create_support_ticket(context)
                        if success:
                            context.transition_state(ConversationState.ENDED)
                        return response
                    else:
                        logger.info("No valid contact information found in message")
                        return "I couldn't find a valid email address or phone number. Could you please provide one?"
                else:
                    # Handle based on current state
                    response = await self._handle_state(context, message, intent)
                
                # Add assistant response to context
                context.add_message(
                    role="assistant",
                    content=response
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                return "I'm having trouble processing your request. Could you please rephrase that or let me know if you'd like to speak with a human agent?"
            
        except Exception as e:
            # Log error with context
            logger.error(f"Critical error in process_message: {str(e)}")
            sentry_sdk.capture_exception(
                e,
                extras={
                    "conversation_id": conversation_id,
                    "message": message
                }
            )
            return "I apologize, but I'm experiencing technical difficulties. Would you like me to create a support ticket for you?"

    async def _create_support_ticket(self, context: ConversationContext) -> Tuple[bool, str]:
        """
        Create a support ticket with proper formatting.
        
        Args:
            context: Current conversation context
            
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info("Creating ticket with complete conversation history...")
            # Find the first message that's not contact info and not from assistant
            initial_issue = next(
                (msg.content for msg in context.messages 
                 if msg.role == "user" and not self.ticket_manager.extract_contact_info(msg.content).get("email")),
                "No clear issue stated"
            )
            
            # Format conversation history excluding contact info exchanges
            conversation_history = "\n".join([
                f"{m.role}: {m.content}" for m in context.messages
                if not (m.role == "assistant" and "email address" in m.content.lower())
                and not (m.role == "user" and self.ticket_manager.extract_contact_info(m.content).get("email"))
            ])
            
            ticket_id = await self.ticket_manager.create_ticket(
                context=context,
                subject="Support Request from Voice Call",
                contents=f"User Issue: {initial_issue}\n\nConversation History:\n{conversation_history}",
                email=context.metadata.get("email"),
                phone=context.metadata.get("phone")
            )
            logger.info(f"Successfully created ticket: {ticket_id}")
            return True, "I've created a support ticket with our complete conversation. Thank you for contacting us. Have a great day!"
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            return False, "I'm having trouble creating your ticket. Please try again later."

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
        
        if state == ConversationState.GREETING:
            # Initial state - determine if we can help or need to create ticket
            context.transition_state(ConversationState.COLLECTING_ISSUE)
            return "Hello! How can I help you today?"
        
        elif state == ConversationState.COLLECTING_ISSUE:
            # First check if this message contains contact info
            contact_info = self.ticket_manager.extract_contact_info(message, context=context)
            if contact_info.get("email") or contact_info.get("phone"):
                # Store contact info and create ticket
                context.metadata["email"] = contact_info.get("email")
                context.metadata["phone"] = contact_info.get("phone")
                context.transition_state(ConversationState.CREATING_TICKET)
                success, response = await self._create_support_ticket(context)
                if success:
                    context.transition_state(ConversationState.ENDED)
                return response
            
            # Check if user wants to end conversation
            if intent == Intent.END_CONVERSATION:
                context.transition_state(ConversationState.ENDED)
                # Create ticket if we have contact info
                if "email" in context.metadata or "phone" in context.metadata:
                    success, message = await self._create_support_ticket(context)
                    return message
                return "Thank you for contacting us. Have a great day!"
            
            # Check if user wants to talk to human
            elif intent == Intent.UNKNOWN and "human" in message.lower():
                context.transition_state(ConversationState.CREATING_TICKET)
                return "I'll need to create a ticket for further assistance. Could you please provide your email address?"
            
            # Try to find relevant knowledge base article
            kb_response = None
            if self.initialized:
                kb_response = await self.kb_engine.search_and_summarize(message)
                logger.info(f"KB search result for '{message}': {kb_response is not None}")
            
            if kb_response:
                context.transition_state(ConversationState.PROVIDING_SOLUTION)
                return f"{kb_response}\n\nWas this information helpful?"
            else:
                # No relevant KB articles found, ask for contact info
                context.transition_state(ConversationState.CREATING_TICKET)
                return "I apologize, but I couldn't find a specific solution for your issue in our knowledge base. Let me create a support ticket so our team can assist you. Could you please provide your email address?"
        
        elif state == ConversationState.PROVIDING_SOLUTION:
            # After providing KB article, check if it was helpful
            if intent == Intent.CONFIRM:
                context.transition_state(ConversationState.ENDED)
                return "Great! Is there anything else I can help you with?"
            elif intent == Intent.DENY:
                context.transition_state(ConversationState.CREATING_TICKET)
                return "I'm sorry the information wasn't helpful. Let me create a ticket for further assistance. Could you please provide your email address?"
            else:
                return await self.conversation_handler.generate_response(context)
        
        elif state == ConversationState.CREATING_TICKET:
            # Check for contact info in message
            contact_info = self.ticket_manager.extract_contact_info(message, context=context)
            logger.info(f"Extracted contact info: {contact_info}")
            
            if contact_info.get("email") or contact_info.get("phone"):
                # Store contact info in context for later use
                context.metadata["email"] = contact_info.get("email")
                context.metadata["phone"] = contact_info.get("phone")
                
                # Create ticket immediately with what we have
                success, response = await self._create_support_ticket(context)
                if success:
                    context.transition_state(ConversationState.ENDED)
                return response
            else:
                logger.info("No valid contact information found in message")
                return "I couldn't find a valid email address or phone number. Could you please provide one?"
        
        elif state == ConversationState.ENDED:
            # Handle normal ended state responses
            if intent == Intent.CONFIRM:
                context.transition_state(ConversationState.COLLECTING_ISSUE)
                return "What else can I help you with?"
            elif intent == Intent.DENY or intent == Intent.END_CONVERSATION:
                return "Thank you for contacting us. Have a great day!"
            else:
                context.transition_state(ConversationState.COLLECTING_ISSUE)
                return await self.conversation_handler.generate_response(context)
        
        # Default response if state not handled
        return await self.conversation_handler.generate_response(context)

    async def handle_ticket_creation_state(self, message: str) -> None:
        """Handle the ticket creation state by extracting contact info."""
        # Extract contact info from message
        contact_info = self.ticket_manager.extract_contact_info(message, context=self.context)
        
        # Log the extracted info
        logger.info(f"Extracted contact info: {contact_info}")
        
        # If we have either email or phone
        if contact_info['email'] or contact_info['phone']:
            # Create ticket with conversation history
            ticket_id = await self.ticket_manager.create_ticket(
                subject="Customer Support Request",
                contents=self._get_conversation_history(),
                email=contact_info['email'],
                phone=contact_info['phone']
            )
            
            if ticket_id:
                logger.info(f"Created ticket {ticket_id}")
                self.state = "ENDED"
                await self.assistant.respond("Thank you! I've created a support ticket and our team will get back to you soon.")
            else:
                logger.error("Failed to create ticket")
                await self.assistant.respond("I'm having trouble creating your ticket. Please try again later.")
        else:
            logger.info("No valid contact information found in message")
            await self.assistant.respond("I couldn't find a valid email address or phone number. Could you please provide one?")
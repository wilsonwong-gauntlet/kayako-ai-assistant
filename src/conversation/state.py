"""Conversation state management for the AI assistant."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ConversationState(Enum):
    """States in the conversation flow."""
    GREETING = "greeting"
    COLLECTING_ISSUE = "collecting_issue"
    SEARCHING_KB = "searching_kb"
    PROVIDING_SOLUTION = "providing_solution"
    CREATING_TICKET = "creating_ticket"
    ENDED = "ended"

class Intent(Enum):
    """Detected intents in user messages."""
    GENERAL_QUERY = "general_query"
    PASSWORD_RESET = "password_reset"
    BILLING_ISSUE = "billing_issue"
    TECHNICAL_PROBLEM = "technical_problem"
    ACCOUNT_ACCESS = "account_access"
    CONFIRM = "confirm"
    DENY = "deny"
    UNKNOWN = "unknown"

class Entity(BaseModel):
    """Named entity extracted from conversation."""
    type: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)

class Message(BaseModel):
    """A single message in the conversation."""
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    intent: Optional[Intent] = None
    entities: List[Entity] = Field(default_factory=list)

class ConversationContext(BaseModel):
    """Maintains the context and state of a conversation."""
    conversation_id: str
    current_state: ConversationState
    messages: List[Message] = Field(default_factory=list)
    detected_entities: Dict[str, Entity] = Field(default_factory=dict)
    last_intent: Optional[Intent] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    def add_message(self, role: str, content: str, intent: Optional[Intent] = None, 
                   entities: Optional[List[Entity]] = None) -> None:
        """Add a message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            intent=intent,
            entities=entities or []
        )
        self.messages.append(message)
        
        # Update conversation state based on new message
        if intent:
            self.last_intent = intent
        
        # Store any new entities
        for entity in (entities or []):
            if entity.confidence > self.detected_entities.get(entity.type, Entity(type="", value="", confidence=0.0)).confidence:
                self.detected_entities[entity.type] = entity
    
    def get_context_window(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get the recent conversation context for the AI model."""
        # Start with system context
        context = [{"role": "system", "content": self._get_system_prompt()}]
        
        # Add recent messages
        for message in self.messages[-max_messages:]:
            context.append({
                "role": message.role,
                "content": message.content
            })
        
        return context
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt based on current state and context."""
        base_prompt = """You are a helpful and professional customer service AI assistant for Kayako.
Your goal is to help customers resolve their issues efficiently and professionally.
You should:
1. Be polite and empathetic
2. Focus on understanding the customer's issue
3. Provide clear and concise solutions
4. Collect necessary information when needed
5. Know when to escalate to a human agent

Current conversation state: {state}
Detected entities: {entities}
Last intent: {intent}"""
        
        return base_prompt.format(
            state=self.current_state.value,
            entities=", ".join(f"{k}: {v.value}" for k, v in self.detected_entities.items()),
            intent=self.last_intent.value if self.last_intent else "None"
        )
    
    def should_transition_state(self) -> Optional[ConversationState]:
        """Determine if the conversation should transition to a new state."""
        if self.current_state == ConversationState.GREETING:
            # After greeting, move to collecting the issue
            return ConversationState.COLLECTING_ISSUE
            
        elif self.current_state == ConversationState.COLLECTING_ISSUE and self.last_intent:
            # Once we have an intent, move to searching KB
            if self.last_intent == Intent.UNKNOWN and "human" in self.messages[-1].content.lower():
                return ConversationState.CREATING_TICKET
            return ConversationState.SEARCHING_KB
            
        elif self.current_state == ConversationState.SEARCHING_KB:
            # After searching, move to providing solution
            return ConversationState.PROVIDING_SOLUTION
            
        elif self.current_state == ConversationState.PROVIDING_SOLUTION:
            # After solution, check if it was helpful
            if self.last_intent == Intent.CONFIRM:
                return ConversationState.ENDED
            elif self.last_intent == Intent.DENY:
                return ConversationState.CREATING_TICKET
            
        elif self.current_state == ConversationState.CREATING_TICKET:
            # After creating ticket, end conversation
            return ConversationState.ENDED
            
        return None
    
    def transition_state(self, new_state: ConversationState) -> None:
        """Transition to a new conversation state."""
        self.current_state = new_state 
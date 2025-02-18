"""CLI tool for testing conversation functionality."""

import asyncio
import click
from .handler import ConversationHandler
from .state import ConversationState, Intent

@click.group()
def cli():
    """Test conversation functionality."""
    pass

@cli.command()
def chat():
    """Start an interactive chat session."""
    async def _chat():
        handler = ConversationHandler()
        conversation_id = handler.create_conversation()
        
        print("Chat session started. Type 'quit' to exit.")
        print("Starting conversation...")
        
        # Get initial greeting
        context = handler.get_conversation_context(conversation_id)
        response = await handler.generate_response(context)
        print(f"\nAssistant: {response}")
        
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'quit':
                break
            
            # Process message
            try:
                response = await handler.process_message(conversation_id, user_input)
                print(f"\nAssistant: {response}")
                
                # Show debug info
                context = handler.get_conversation_context(conversation_id)
                print(f"\nDebug Info:")
                print(f"State: {context.current_state.value}")
                print(f"Last Intent: {context.last_intent.value if context.last_intent else 'None'}")
                print(f"Entities: {', '.join(f'{k}: {v.value}' for k, v in context.detected_entities.items())}")
                
            except Exception as e:
                print(f"\nError: {e}")
    
    asyncio.run(_chat())

if __name__ == '__main__':
    cli() 
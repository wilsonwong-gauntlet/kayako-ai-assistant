"""CLI tool for testing the complete conversation flow."""

import asyncio
import click
from .flow import ConversationFlowManager

@click.group()
def cli():
    """Test complete conversation flow."""
    pass

@cli.command()
def chat():
    """Start an interactive chat session with the complete flow."""
    async def _chat():
        # Initialize flow manager
        flow_manager = ConversationFlowManager()
        
        print("Starting conversation...")
        conversation_id, greeting = await flow_manager.start_conversation()
        print(f"\nAssistant: {greeting}")
        
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'quit':
                break
            
            try:
                # Process message
                response = await flow_manager.process_message(conversation_id, user_input)
                print(f"\nAssistant: {response}")
                
                # Get context for debug info
                context = flow_manager.conversation_handler.get_conversation_context(conversation_id)
                print(f"\nDebug Info:")
                print(f"State: {context.current_state.value}")
                print(f"Last Intent: {context.last_intent.value if context.last_intent else 'None'}")
                if context.detected_entities:
                    print(f"Entities: {', '.join(f'{k}: {v.value}' for k, v in context.detected_entities.items())}")
                
            except Exception as e:
                print(f"\nError: {e}")
                if hasattr(e, '__traceback__'):
                    import traceback
                    traceback.print_exc()
    
    try:
        asyncio.run(_chat())
    except KeyboardInterrupt:
        print("\nChat session ended by user.")
    except Exception as e:
        print(f"\nError in chat session: {e}")

if __name__ == '__main__':
    cli() 
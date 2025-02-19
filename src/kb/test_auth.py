"""Test script for Kayako Basic Authentication."""

import asyncio
from dotenv import load_dotenv
import os
from .kayako_client import RealKayakoAPI

async def test_auth():
    """Test Basic HTTP authentication with Kayako."""
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    base_url = os.getenv('KAYAKO_API_URL')
    email = os.getenv('KAYAKO_EMAIL')
    password = os.getenv('KAYAKO_PASSWORD')
    
    if not all([base_url, email, password]):
        print("❌ Error: Missing Kayako credentials in .env file")
        print("\nPlease set the following variables:")
        print("KAYAKO_API_URL=https://<your-instance>.kayako.com/api/v1")
        print("KAYAKO_EMAIL=your.email@example.com")
        print("KAYAKO_PASSWORD=your_password")
        return
    
    try:
        # Initialize API client
        api = RealKayakoAPI(base_url, email, password)
        
        # Try to get a session ID
        session_id = await api.auth_manager.get_session_id()
        
        print("✅ Successfully authenticated with Kayako!")
        print(f"\nSession ID: {session_id[:10]}...")  # Show first 10 chars for verification
        
        # Test a simple API call
        print("\nTesting API access...")
        users = await api.search_users("test")
        print(f"✅ Successfully retrieved {len(users)} users")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nPlease verify your Kayako credentials and try again.")

if __name__ == "__main__":
    asyncio.run(test_auth()) 
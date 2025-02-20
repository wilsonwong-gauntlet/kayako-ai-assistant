"""Test the knowledge base search functionality."""

import os
import sys
import asyncio
import logging

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kb.search import KBSearchEngine
from src.kb.kayako_client import RealKayakoAPI

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_kb_search():
    """Test the knowledge base search functionality."""
    engine = KBSearchEngine()
    
    print("\n=== Testing KB Search Engine ===")
    
    # Test 1: Initialize
    print("\n1. Testing initialization")
    await engine.initialize()
    
    # Test 2: Direct API test
    print("\n2. Testing direct API access")
    api = RealKayakoAPI(
        base_url=os.getenv("KAYAKO_API_URL"),
        email=os.getenv("KAYAKO_EMAIL"),
        password=os.getenv("KAYAKO_PASSWORD")
    )
    articles = await api.search_articles("AdvocateHub unsearchable")
    print(f"\nDirect API results:")
    for article in articles:
        print(f"- Title: {article.title}")
        print(f"  Category: {article.category}")
        print(f"  Content length: {len(article.content)} chars")
    
    # Test 3: Search through KB engine
    print("\n3. Testing KB search")
    query = "How to make AdvocateHub unsearchable by search engines"
    results = await engine.search(query)
    print(f"\nKB search results for '{query}':")
    for article, score in results:
        print(f"- Title: {article.title}")
        print(f"  Score: {score:.3f}")
        print(f"  Category: {article.category}")
        print(f"  Content length: {len(article.content)} chars")
    
    # Test 4: Generate summary
    print("\n4. Testing summary generation")
    if results:
        summary = await engine.generate_summary(results[0][0], query)
        print(f"\nSummary for top result:\n{summary}")

if __name__ == "__main__":
    asyncio.run(test_kb_search()) 
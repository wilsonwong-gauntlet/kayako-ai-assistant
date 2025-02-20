"""Test the knowledge base search functionality."""

import os
import sys
import asyncio
import logging

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kb.search import KBSearchEngine

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_kb_search():
    """Test the knowledge base search functionality."""
    engine = KBSearchEngine()  # No storage_dir needed
    
    print("\n=== Testing KB Search Engine ===")
    
    # Test 1: Initialize without loading articles
    print("\n1. Testing initialization")
    await engine.initialize()
    print(f"Cache size after init: {len(engine.articles)} articles")
    
    # Test 2: First search query
    print("\n2. Testing first search query")
    query = "How to reset password"
    results = await engine.search(query)
    print(f"Results for '{query}': {len(results)} articles")
    if results:
        print(f"Top result: {results[0][0].title} (score: {results[0][1]:.2f})")
    
    # Test 3: Same query again (should use cache)
    print("\n3. Testing cached search")
    cached_results = await engine.search(query)
    print(f"Cached results for '{query}': {len(cached_results)} articles")
    
    # Test 4: Different query
    print("\n4. Testing different query")
    new_query = "How to configure email settings"
    new_results = await engine.search(new_query)
    print(f"Results for '{new_query}': {len(new_results)} articles")
    if new_results:
        print(f"Top result: {new_results[0][0].title} (score: {new_results[0][1]:.2f})")
    
    # Test 5: Generate summary
    print("\n5. Testing summary generation")
    if results:
        summary = await engine.generate_summary(results[0][0], query)
        print(f"Summary for '{query}':\n{summary}")

if __name__ == "__main__":
    asyncio.run(test_kb_search()) 
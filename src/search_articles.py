import asyncio
import os
from kb.kayako_client import RealKayakoAPI
from kb.config import kayako_settings
import json

async def main():
    # Initialize the Kayako API client
    api = RealKayakoAPI(
        base_url=kayako_settings.KAYAKO_API_URL,
        email=kayako_settings.KAYAKO_EMAIL,
        password=kayako_settings.KAYAKO_PASSWORD
    )
    
    # Perform the search with empty query to get all articles
    print("\n=== Retrieving all articles ===")
    print(f"Using Kayako API URL: {kayako_settings.KAYAKO_API_URL}")
    
    # Get first article only for testing
    articles = await api.search_articles("")
    
    if not articles:
        print("No articles found.")
        return
        
    # Get the first article for detailed inspection
    first_article = articles[0]
    print("\n=== Initial article data from search ===")
    print(json.dumps(first_article.__dict__, indent=2))
    
    print("\n=== Fetching full article details ===")
    full_article = await api.get_article(first_article.id)
    if full_article:
        print(json.dumps(full_article.__dict__, indent=2))
    else:
        print("Failed to fetch full article")

if __name__ == "__main__":
    asyncio.run(main()) 
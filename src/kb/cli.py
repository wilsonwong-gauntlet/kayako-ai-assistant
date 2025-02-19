"""CLI tool for testing knowledge base search functionality."""

import asyncio
import click
import os
import re
import html
from dotenv import load_dotenv
from .kayako_client import RealKayakoAPI
from .interfaces import Article

def clean_html(text: str) -> str:
    """Remove HTML tags and decode entities from text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@click.group()
def cli():
    """Test knowledge base search functionality."""
    pass

async def get_api() -> RealKayakoAPI:
    """Get an initialized Kayako API client."""
    load_dotenv()
    return RealKayakoAPI(
        base_url=os.getenv('KAYAKO_API_URL'),
        email=os.getenv('KAYAKO_EMAIL'),
        password=os.getenv('KAYAKO_PASSWORD')
    )

@cli.command(name='search')
@click.argument('query')
@click.option('--results', default=3, help='Maximum number of results to show')
def search_cmd(query: str, results: int):
    """Search the knowledge base."""
    async def _search():
        print(f"Searching Kayako knowledge base for: {query}")
        
        api = await get_api()
        articles = await api.search_articles(query)
        
        if not articles:
            print("\nNo articles found.")
            return
        
        print(f"\nFound {len(articles)} articles. Showing top {min(results, len(articles))}:")
        print()
        
        for i, article in enumerate(articles[:results], 1):
            article_obj = Article.from_api_response(article)
            
            # Print article title with border
            title = f"{i}. {article_obj.title}"
            print(title)
            print("=" * len(title))
            print()
            
            # Clean and format content preview
            content = clean_html(article_obj.content)
            words = content.split()
            preview = " ".join(words[:50]) + ("..." if len(words) > 50 else "")
            print(preview)
            print()
            
            # Print metadata
            if article_obj.category:
                print(f"Category: {article_obj.category}")
            if article_obj.tags:
                print(f"Tags: {', '.join(article_obj.tags)}")
            
            # Print separator between articles
            if i < len(articles[:results]):
                print("\n" + "-" * 80 + "\n")
    
    asyncio.run(_search())

@cli.command(name='answer')
@click.argument('query')
def quick_answer(query: str):
    """Get a quick answer from the knowledge base."""
    async def _quick_answer():
        api = await get_api()
        articles = await api.search_articles(query)
        
        if articles:
            article = Article.from_api_response(articles[0])
            print(f"\nBest match: {article.title}")
            print(f"\nAnswer: {clean_html(article.content)}")
        else:
            print("\nSorry, I couldn't find a relevant answer to your question.")
    
    asyncio.run(_quick_answer())

if __name__ == '__main__':
    cli() 
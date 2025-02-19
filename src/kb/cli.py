"""CLI tool for testing knowledge base search functionality."""

import asyncio
import click
from .search import KBSearchEngine

@click.group()
def cli():
    """Test knowledge base search functionality."""
    pass

@cli.command()
@click.argument('query')
@click.option('--results', default=3, help='Maximum number of results to show')
def search(query: str, results: int):
    """Search the knowledge base."""
    async def _search():
        # Initialize search engine
        engine = KBSearchEngine()
        print("Initializing search engine...")
        await engine.initialize()
        
        # Search for articles
        print(f"\nSearching for: {query}")
        search_results = await engine.search(query, max_results=results)
        
        if not search_results:
            print("\nNo relevant articles found.")
            return
        
        # Display results
        print("\nSearch Results:")
        for i, (article, score) in enumerate(search_results, 1):
            print(f"\n{i}. {article.title} (Relevance: {score:.2f})")
            print(f"Category: {article.category}")
            print(f"Tags: {', '.join(article.tags)}")
            print(f"Content Preview: {article.content[:150]}...")
            
            # Generate summary
            summary = await engine.generate_summary(article, query)
            print(f"\nSummary: {summary}")
    
    asyncio.run(_search())

@cli.command(name='answer')
@click.argument('query')
def quick_answer(query: str):
    """Get a quick answer from the knowledge base."""
    async def _quick_answer():
        # Initialize search engine
        engine = KBSearchEngine()
        print("Initializing search engine...")
        await engine.initialize()
        
        # Search and summarize
        print(f"\nFinding answer for: {query}")
        answer = await engine.search_and_summarize(query)
        
        if answer:
            print(f"\nAnswer: {answer}")
        else:
            print("\nSorry, I couldn't find a relevant answer to your question.")
    
    asyncio.run(_quick_answer())

if __name__ == '__main__':
    cli() 
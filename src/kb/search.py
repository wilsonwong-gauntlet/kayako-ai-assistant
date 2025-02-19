"""Knowledge base search functionality using OpenAI embeddings."""

import os
from typing import List, Optional, Dict, Tuple
import numpy as np
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json

from .kayako_client import RealKayakoAPI
from .interfaces import Article

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class KBSearchEngine:
    """Search engine for knowledge base articles."""
    
    def __init__(self):
        """Initialize the search engine."""
        self.api = RealKayakoAPI(
            base_url=os.getenv("KAYAKO_API_URL"),
            email=os.getenv("KAYAKO_EMAIL"),
            password=os.getenv("KAYAKO_PASSWORD")
        )
        self.article_embeddings: Dict[str, List[float]] = {}
        self.articles: Dict[str, Article] = {}
    
    async def initialize(self):
        """Initialize article embeddings."""
        # Search for articles using the real API
        articles = await self.api.search_articles("")
        
        # Store articles and create embeddings
        for article in articles:
            self.articles[article.id] = article
            
            # Create a searchable representation of the article
            article_text = f"Title: {article.title}\nContent: {article.content}\nTags: {', '.join(article.tags)}"
            
            # Get embedding for the article
            embedding = await self._get_embedding(article_text)
            self.article_embeddings[article.id] = embedding
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a piece of text."""
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        # Convert to numpy arrays for efficient calculation
        a = np.array(embedding1)
        b = np.array(embedding2)
        
        # Calculate cosine similarity
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    async def search(self, query: str, max_results: int = 3) -> List[Tuple[Article, float]]:
        """
        Search for articles relevant to the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
        
        Returns:
            List of (article, relevance_score) tuples
        """
        # Get query embedding
        query_embedding = await self._get_embedding(query)
        
        # Calculate similarity scores
        scores = []
        for article_id, article_embedding in self.article_embeddings.items():
            similarity = self._calculate_similarity(query_embedding, article_embedding)
            scores.append((self.articles[article_id], similarity))
        
        # Sort by similarity score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:max_results]
    
    async def generate_summary(self, article: Article, query: str) -> str:
        """
        Generate a concise, relevant summary of an article based on the query.
        
        Args:
            article: Article to summarize
            query: Original search query for context
        
        Returns:
            Concise summary focused on relevant information
        """
        system_prompt = """You are a helpful customer service AI that creates concise, relevant summaries of knowledge base articles.
Focus on the information that is most relevant to the user's query.
Keep the summary clear and suitable for voice responses (2-3 sentences).
Include any specific steps or requirements if they are relevant."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Query: {query}

Article Title: {article.title}

Article Content:
{article.content}

Create a concise, relevant summary focusing on answering the query."""}
        ]
        
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.7,
            max_tokens=150  # Keep summaries concise
        )
        
        return response.choices[0].message.content
    
    async def search_and_summarize(self, query: str, max_results: int = 1) -> Optional[str]:
        """
        Search for articles and generate a relevant summary.
        
        Args:
            query: Search query
            max_results: Maximum number of results to summarize
        
        Returns:
            Summarized response or None if no relevant articles found
        """
        try:
            # Search for relevant articles
            results = await self.search(query, max_results=max_results)
            
            if not results:
                return None
            
            # Get the most relevant article
            best_match, score = results[0]
            
            # Only use the article if it's reasonably relevant
            if score < 0.5:  # Lower threshold for quick answers
                return None
            
            # Generate a summary
            summary = await self.generate_summary(best_match, query)
            return summary
            
        except Exception as e:
            print(f"Error in search_and_summarize: {e}")
            return None 
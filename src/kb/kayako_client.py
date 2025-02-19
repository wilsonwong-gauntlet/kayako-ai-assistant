import os
from typing import List, Optional, Dict, Any
import aiohttp
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential
from cachetools import TTLCache
from datetime import datetime, timedelta
import base64
import re

from .interfaces import Article, Ticket, User, Message, KayakoAPI

class KayakoAuthManager:
    """Manages authentication for Kayako API."""
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._auth_header = None
        self._init_auth_header()

    def _init_auth_header(self) -> None:
        """Initialize the Basic Auth header."""
        auth_string = f"{self.email}:{self.password}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        self._auth_header = f"Basic {auth_b64}"

    async def get_auth_header(self) -> str:
        """Get Basic Auth header for API requests."""
        return self._auth_header

    @backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=3)
    async def authenticate(self) -> str:
        """Perform initial authentication and get session ID."""
        async with aiohttp.ClientSession() as session:
            # Use Basic HTTP Authentication header
            headers = {
                'Authorization': self.get_auth_header(),
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Try to get session by accessing /users endpoint
            users_url = f"{self.base_url}/api/v1/users"
            print(f"Attempting authentication by accessing: {users_url}")
            print(f"Using Basic Auth header: {headers['Authorization']}")  # Print full header for debugging
            
            async with session.get(
                users_url,
                headers=headers
            ) as response:
                print(f"Response status: {response.status}")
                data = await response.json()
                print(f"Response data: {data}")
                
                if response.status == 200 and 'session_id' in data:
                    self.session_id = data['session_id']
                    return self.session_id
                
                response.raise_for_status()
                return ''
    
    async def _handle_additional_auth(self) -> str:
        """Handle additional authentication steps if required."""
        if not self.auth_token:
            raise ValueError("No auth token available for additional authentication")
            
        async with aiohttp.ClientSession() as session:
            headers = {'X-Token': self.auth_token}
            
            # Try to complete authentication with token
            async with session.post(
                f"{self.base_url}/auth/complete",
                headers=headers
            ) as response:
                data = await response.json()
                
                if response.status == 200 and 'session_id' in data:
                    self.session_id = data['session_id']
                    return self.session_id
                
                response.raise_for_status()
                return ''
    
    async def get_session_id(self) -> str:
        """Get a valid session ID, authenticating if necessary."""
        if not self.session_id:
            await self.authenticate()
        return self.session_id

class RealKayakoAPI(KayakoAPI):
    """Real implementation of Kayako API with Basic Auth and session management."""
    
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.auth_manager = KayakoAuthManager(email, password)
        # Cache for article searches (5 minute TTL)
        self.search_cache = TTLCache(maxsize=100, ttl=300)
        # Cache for user lookups (1 minute TTL)
        self.user_cache = TTLCache(maxsize=100, ttl=60)
        # Cache for messages (30 second TTL)
        self.message_cache = TTLCache(maxsize=200, ttl=30)
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        auth_header = await self.auth_manager.get_auth_header()
        return {
            "Accept": "application/json",
            "Authorization": auth_header
        }

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the Kayako API."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            url = f"{self.base_url}/{endpoint}"
            
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                return await response.json()
    
    async def search_articles(self, query: str) -> List[Dict[str, Any]]:
        """Search for articles in Kayako."""
        params = {
            "query": query,
            "resources": "articles"
        }
        response = await self._get("search", params=params)
        articles = response.get("data", [])
        
        # Fetch full article details for each result
        for article in articles:
            article_id = article["data"]["id"]
            full_article = await self._get(f"articles/{article_id}")
            article_data = full_article["data"]
            
            # Get title from locale fields
            if article_data.get("titles"):
                title_id = article_data["titles"][0]["id"]
                title_response = await self._get(f"locale/fields/{title_id}")
                article["title"] = title_response["data"]["translation"]
            
            # Get content from locale fields
            if article_data.get("contents"):
                content_id = article_data["contents"][0]["id"]
                content_response = await self._get(f"locale/fields/{content_id}")
                article["content"] = content_response["data"]["translation"]
            
            # Add section/category info
            if article_data.get("section"):
                section_id = article_data["section"]["id"]
                section_response = await self._get(f"sections/{section_id}")
                if section_response["data"].get("titles"):
                    title_id = section_response["data"]["titles"][0]["id"]
                    title_response = await self._get(f"locale/fields/{title_id}")
                    article["category"] = title_response["data"]["translation"]
                else:
                    article["category"] = f"Section {section_id}"
            
            # Add tags
            article["tags"] = article_data.get("tags", [])
        
        return articles
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def create_ticket(self, ticket: Ticket) -> str:
        """Create a new support ticket with retry logic."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            
            # Prepare the ticket data according to Kayako's API format
            ticket_data = {
                'subject': ticket.subject,
                'channel': 'Phone',  # Since this is from voice calls
                'status': ticket.status,
                'priority': ticket.priority,
                'requester': {
                    'email': ticket.requester_email,
                    'phone': ticket.phone_number
                },
                'messages': [{
                    'content': ticket.description,
                    'type': 'reply'
                }]
            }
            
            async with session.post(
                f"{self.base_url}/conversations",
                headers=headers,
                json=ticket_data
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return str(data['id'])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_article(self, article_id: str) -> Article:
        """Get a specific article by ID with retry logic."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            
            async with session.get(
                f"{self.base_url}/articles/{article_id}",
                headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                return Article(
                    id=data['id'],
                    title=data['title'],
                    content=data['content'],
                    tags=data.get('tags', []),
                    category=data.get('category', 'General')
                )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID with retry logic."""
        # Check cache first
        cache_key = f"user:{user_id}"
        if cache_key in self.user_cache:
            return self.user_cache[cache_key]

        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            
            async with session.get(
                f"{self.base_url}/users/{user_id}",
                headers=headers
            ) as response:
                if response.status == 404:
                    return None
                    
                response.raise_for_status()
                data = await response.json()
                
                user = User(
                    id=data['id'],
                    email=data['email'],
                    full_name=data['full_name'],
                    phone=data.get('phone'),
                    organization=data.get('organization'),
                    role=data.get('role', 'customer'),
                    locale=data.get('locale', 'en-US'),
                    time_zone=data.get('time_zone', 'UTC')
                )
                
                # Cache the result
                self.user_cache[cache_key] = user
                return user
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email with retry logic."""
        # Check cache first
        cache_key = f"user_email:{email}"
        if cache_key in self.user_cache:
            return self.user_cache[cache_key]

        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            params = {'email': email}
            
            async with session.get(
                f"{self.base_url}/users",
                headers=headers,
                params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                if not data.get('data'):
                    return None
                
                user_data = data['data'][0]  # Get first matching user
                user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    full_name=user_data['full_name'],
                    phone=user_data.get('phone'),
                    organization=user_data.get('organization'),
                    role=user_data.get('role', 'customer'),
                    locale=user_data.get('locale', 'en-US'),
                    time_zone=user_data.get('time_zone', 'UTC')
                )
                
                # Cache the result
                self.user_cache[cache_key] = user
                return user
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def create_user(self, user: User) -> str:
        """Create a new user with retry logic."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            
            # Prepare user data
            user_data = {
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'organization': user.organization,
                'role': user.role,
                'locale': user.locale,
                'time_zone': user.time_zone
            }
            
            async with session.post(
                f"{self.base_url}/users",
                headers=headers,
                json=user_data
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Cache the new user
                new_user = User(**data)
                self.user_cache[f"user:{new_user.id}"] = new_user
                self.user_cache[f"user_email:{new_user.email}"] = new_user
                
                return str(data['id'])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def update_user(self, user_id: str, user: User) -> bool:
        """Update an existing user with retry logic."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            
            # Prepare update data
            update_data = {
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'organization': user.organization,
                'role': user.role,
                'locale': user.locale,
                'time_zone': user.time_zone
            }
            
            async with session.put(
                f"{self.base_url}/users/{user_id}",
                headers=headers,
                json=update_data
            ) as response:
                if response.status == 404:
                    return False
                    
                response.raise_for_status()
                data = await response.json()
                
                # Update cache
                updated_user = User(**data)
                self.user_cache[f"user:{user_id}"] = updated_user
                self.user_cache[f"user_email:{updated_user.email}"] = updated_user
                
                return True
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_users(self, query: str) -> List[User]:
        """Search for users with retry logic."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            params = {
                'query': query,
                **await self._get_session_params()  # Add session ID as query param
            }
            
            async with session.get(
                f"{self.base_url}/users",
                headers=headers,
                params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                users = []
                for user_data in data.get('data', []):
                    # Get email ID from the first email in the emails array
                    email_id = user_data.get('emails', [{}])[0].get('id', '')
                    
                    # Get role ID from the nested role object
                    role = user_data.get('role', {}).get('id', 4)  # Default to 4 (customer)
                    
                    # Get locale ID from the nested locale object
                    locale = user_data.get('locale', {}).get('id', 2)  # Default to 2 (en-US)
                    
                    # Get organization ID from the nested organization object
                    organization = user_data.get('organization', {}).get('id') if user_data.get('organization') else None
                    
                    user = User(
                        id=user_data['id'],
                        email=str(email_id),  # Convert to string to ensure compatibility
                        full_name=user_data['full_name'],
                        phone=None,  # Phone is in a separate phones array
                        organization=organization,
                        role=role,
                        locale=locale,
                        time_zone=user_data.get('time_zone')
                    )
                    users.append(user)
                    
                    # Cache individual users
                    self.user_cache[f"user:{user.id}"] = user
                    if email_id:
                        self.user_cache[f"user_email:{email_id}"] = user
                
                return users
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_messages(self, conversation_id: str, page: int = 1, per_page: int = 50) -> List[Message]:
        """Get messages for a conversation with retry logic."""
        # Check cache first
        cache_key = f"messages:{conversation_id}:{page}:{per_page}"
        if cache_key in self.message_cache:
            return self.message_cache[cache_key]

        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            params = {
                'page': page,
                'per_page': per_page,
                'sort': '-created_at'  # Sort by newest first
            }
            
            async with session.get(
                f"{self.base_url}/conversations/{conversation_id}/messages",
                headers=headers,
                params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                messages = []
                for msg_data in data.get('data', []):
                    message = Message(
                        id=msg_data['id'],
                        conversation_id=conversation_id,
                        content=msg_data['content'],
                        type=msg_data['type'],
                        creator=msg_data.get('creator'),
                        attachments=msg_data.get('attachments', []),
                        created_at=datetime.fromisoformat(msg_data['created_at'].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(msg_data['updated_at'].replace('Z', '+00:00')) if msg_data.get('updated_at') else None,
                        is_private=msg_data.get('is_private', False)
                    )
                    messages.append(message)
                    
                    # Cache individual messages
                    self.message_cache[f"message:{message.id}"] = message
                
                # Cache the list of messages
                self.message_cache[cache_key] = messages
                return messages
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def create_message(self, conversation_id: str, message: Message) -> str:
        """Create a new message in a conversation with retry logic."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            
            # Prepare message data
            message_data = {
                'content': message.content,
                'type': message.type,
                'is_private': message.is_private,
                'attachments': message.attachments
            }
            
            async with session.post(
                f"{self.base_url}/conversations/{conversation_id}/messages",
                headers=headers,
                json=message_data
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Create and cache the new message
                new_message = Message(
                    id=data['id'],
                    conversation_id=conversation_id,
                    content=data['content'],
                    type=data['type'],
                    creator=data.get('creator'),
                    attachments=data.get('attachments', []),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    updated_at=None,
                    is_private=data.get('is_private', False)
                )
                
                # Cache the new message
                self.message_cache[f"message:{new_message.id}"] = new_message
                
                # Invalidate conversation messages cache
                for key in list(self.message_cache.keys()):
                    if key.startswith(f"messages:{conversation_id}:"):
                        del self.message_cache[key]
                
                return str(data['id'])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def update_message(self, message_id: str, message: Message) -> bool:
        """Update an existing message with retry logic."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            
            # Prepare update data
            update_data = {
                'content': message.content,
                'type': message.type,
                'is_private': message.is_private,
                'attachments': message.attachments
            }
            
            async with session.put(
                f"{self.base_url}/messages/{message_id}",
                headers=headers,
                json=update_data
            ) as response:
                if response.status == 404:
                    return False
                    
                response.raise_for_status()
                data = await response.json()
                
                # Update cache with the updated message
                updated_message = Message(
                    id=data['id'],
                    conversation_id=message.conversation_id,
                    content=data['content'],
                    type=data['type'],
                    creator=data.get('creator'),
                    attachments=data.get('attachments', []),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None,
                    is_private=data.get('is_private', False)
                )
                
                # Update message cache
                self.message_cache[f"message:{message_id}"] = updated_message
                
                # Invalidate conversation messages cache
                for key in list(self.message_cache.keys()):
                    if key.startswith(f"messages:{message.conversation_id}:"):
                        del self.message_cache[key]
                
                return True
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def delete_message(self, message_id: str) -> bool:
        """Delete a message with retry logic."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            
            async with session.delete(
                f"{self.base_url}/messages/{message_id}",
                headers=headers
            ) as response:
                if response.status == 404:
                    return False
                
                response.raise_for_status()
                
                # Remove from cache
                if f"message:{message_id}" in self.message_cache:
                    message = self.message_cache[f"message:{message_id}"]
                    # Invalidate conversation messages cache
                    for key in list(self.message_cache.keys()):
                        if key.startswith(f"messages:{message.conversation_id}:"):
                            del self.message_cache[key]
                    del self.message_cache[f"message:{message_id}"]
                
                return True

@classmethod
def from_api_response(cls, item: Dict[str, Any]) -> "Article":
    # Convert integer ID to string
    article_id = str(item["id"])
    
    # Extract title from locale fields
    title_id = next((t["id"] for t in item["titles"] if t["resource_type"] == "locale_field"), None)
    title = f"Article {article_id}"  # Default title
    
    # Extract content from locale fields
    content_id = next((c["id"] for c in item["contents"] if c["resource_type"] == "locale_field"), None)
    content = ""  # Default content
    
    # If we have title/content IDs, we should fetch them from the locale fields endpoint
    # For now, use the slug as a fallback
    if not title_id:
        slug = next((s["translation"] for s in item["slugs"] if s["locale"] == "en-us"), "")
        title = re.sub(r'^\d+\s*-\s*', '', slug)  # Remove ID prefix from slug
    
    # Extract tags
    tags = [str(tag["id"]) for tag in item.get("tags", [])]
    
    # Extract category from section
    category = str(item.get("section", {}).get("id", ""))
    
    return cls(
        id=article_id,
        title=title,
        content=content or title,  # Use title as content if no content available
        tags=tags,
        category=category
    ) 
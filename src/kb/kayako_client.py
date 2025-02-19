import os
from typing import List, Optional, Dict, Any
import aiohttp
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential
from cachetools import TTLCache
from datetime import datetime, timedelta
import base64
from pydantic import BaseModel
import json

from .interfaces import Article, Ticket, User, Message, KayakoAPI

class KayakoAuthManager:
    """Manages Basic HTTP Authentication for Kayako API."""
    
    def __init__(self, email: str, password: str, base_url: str):
        self.email = email
        self.password = password
        # Ensure base_url doesn't include /api/v1
        self.base_url = base_url.rstrip('/').split('/api/v1')[0]
        self.session_id: Optional[str] = None
        self.auth_token: Optional[str] = None
    
    def _get_basic_auth_header(self) -> str:
        """Generate Basic Auth header value."""
        credentials = f"{self.email}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    @backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=3)
    async def authenticate(self) -> str:
        """Perform initial authentication and get session ID."""
        async with aiohttp.ClientSession() as session:
            # Use Basic HTTP Authentication header
            headers = {
                'Authorization': self._get_basic_auth_header(),
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
        self.auth_manager = KayakoAuthManager(email, password, base_url)
        # Cache for article searches (5 minute TTL)
        self.search_cache = TTLCache(maxsize=100, ttl=300)
        # Cache for user lookups (1 minute TTL)
        self.user_cache = TTLCache(maxsize=100, ttl=60)
        # Cache for messages (30 second TTL)
        self.message_cache = TTLCache(maxsize=200, ttl=30)
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with current session ID."""
        session_id = await self.auth_manager.get_session_id()
        return {
            'X-Session-ID': session_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    async def _get_session_params(self) -> Dict[str, str]:
        """Get session ID as query parameter (alternative to header)."""
        session_id = await self.auth_manager.get_session_id()
        return {'_session_id': session_id}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_articles(self, query: str = '') -> List[Article]:
        """Get all articles from the knowledge base."""
        # Check cache first
        cache_key = f"search:{query}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            url = f"{self.base_url}/articles.json"
            params = await self._get_session_params()
            params['include'] = 'contents,titles,tags,section'
            
            print(f"\n=== Making request to: {url} ===")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Params: {json.dumps(params, indent=2)}")
            
            try:
                async with session.get(
                    url,
                    headers=headers,
                    params=params
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    print(f"\n=== Raw API Response ===")
                    print(json.dumps(data, indent=2))
                    
                    articles = []
                    for item in data.get('data', []):
                        try:
                            article = await self.get_article(str(item.get('id', '')))
                            if article:
                                articles.append(article)
                        except Exception as e:
                            print(f"Error processing article: {e}")
                            continue
                    
                    # Cache the results
                    self.search_cache[cache_key] = articles
                    return articles
            except aiohttp.ClientResponseError as e:
                print(f"Articles API error: {e.status} - {e.message}")
                return []
            except Exception as e:
                print(f"Unexpected error fetching articles: {e}")
                return []
    
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
    async def get_article_content(self, content_id: str) -> str:
        """Get article content by content ID."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            params = await self._get_session_params()
            
            url = f"{self.base_url}/locale/fields/{content_id}.json"
            print(f"\n=== Making request to: {url} ===")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Params: {json.dumps(params, indent=2)}")
            
            try:
                async with session.get(
                    url,
                    headers=headers,
                    params=params
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    print(f"\n=== Raw API Response for content {content_id} ===")
                    print(json.dumps(data, indent=2))
                    
                    # Get the translation directly from the response
                    content = data.get('data', {}).get('translation', '')
                    return content or 'No content available'
            except aiohttp.ClientResponseError as e:
                print(f"Error fetching article content: {e.status} - {e.message}")
                return f"Error fetching content: {e.status}"
            except Exception as e:
                print(f"Unexpected error fetching article content: {e}")
                return "Error fetching content"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_article(self, article_id: str) -> Optional[Article]:
        """Get a single article by ID with full content."""
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()
            params = await self._get_session_params()
            params['include'] = 'contents,titles,tags,section'
            
            url = f"{self.base_url}/articles/{article_id}.json"
            print(f"\n=== Making request to: {url} ===")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Params: {json.dumps(params, indent=2)}")
            
            try:
                async with session.get(
                    url,
                    headers=headers,
                    params=params
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    print(f"\n=== Raw API Response for article {article_id} ===")
                    print(json.dumps(data, indent=2))
                    
                    item = data.get('data', {})
                    
                    # Get title from titles array
                    titles = item.get('titles', [])
                    title = ''
                    if titles:
                        title_content = await self.get_article_content(str(titles[0].get('id')))
                        title = title_content if title_content != 'No content available' else ''
                    
                    if not title:
                        # Fallback to slug if no title content
                        slugs = item.get('slugs', [])
                        for slug in slugs:
                            if slug.get('locale') == 'en-us':
                                title = slug.get('translation', '').replace('-', ' ').title()
                                break
                        if not title and slugs:
                            title = slugs[0].get('translation', '').replace('-', ' ').title()
                    
                    # Get content
                    contents = item.get('contents', [])
                    content = ''
                    if contents:
                        content = await self.get_article_content(str(contents[0].get('id')))
                    
                    # Get category from section
                    section = item.get('section', {})
                    section_slugs = section.get('slugs', [])
                    category = 'General'
                    if section_slugs:
                        for slug in section_slugs:
                            if slug.get('locale') == 'en-us':
                                category = slug.get('translation', '').replace('-', ' ').title()
                                break
                        if not category and section_slugs:
                            category = section_slugs[0].get('translation', '').replace('-', ' ').title()
                    
                    # Get tags
                    tags = [str(tag.get('id', '')) for tag in item.get('tags', [])]
                    
                    return Article(
                        id=str(item.get('id', '')),
                        title=title,
                        content=content,
                        tags=tags,
                        category=category
                    )
            except aiohttp.ClientResponseError as e:
                print(f"Error fetching article: {e.status} - {e.message}")
                return None
            except Exception as e:
                print(f"Unexpected error fetching article: {e}")
                return None
    
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
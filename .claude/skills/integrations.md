---
skill: integrations
description: External service integrations (REST APIs, databases, OAuth2, file storage) with MCP codebase search and web research.
---

## MCP-First Integration Workflow

**Always use MCP servers in this order:**

1. **codebase** - Find existing integration patterns
   ```python
   search_codebase("BaseAsyncClient", top_k=10)
   search_codebase("async with.*context", top_k=10)
   ```

2. **filesystem** - Read integration base classes
   ```python
   read_file("src/casare_rpa/infrastructure/clients/base.py")
   read_file("src/casare_rpa/infrastructure/database/supabase_client.py")
   ```

3. **sequential-thinking** - Plan integration architecture
   ```python
   think_step_by_step("""
   Design integration:
   1. Identify API/Service requirements
   2. Find existing base classes
   3. Plan authentication flow
   4. Design resource management
   5. Plan error handling and retries
   """)
   ```

4. **exa** - Research API documentation and patterns
   ```python
   websearch("Python aiohttp best practices 2025", numResults=5)
   websearch("asyncpg connection pooling patterns", numResults=5)
   websearch("OAuth2 flow implementation Python", numResults=5)
   ```

5. **ref** - Library documentation
   ```python
   search_documentation("aiohttp", library="python")
   search_documentation("asyncpg", library="python")
   ```

6. **git** - Check integration history
   ```python
   git_log("-10", "--oneline", "integration|client|auth")
   git_diff("HEAD~10..HEAD", "**/clients/*.py")
   ```

## Base Async Client Pattern

**MCP-Based Discovery:**
```python
# Search for existing base clients
search_codebase("class.*Client", top_k=20)
```

**Template:**
```python
from abc import ABC, abstractmethod
import aiohttp
from typing import Any, Optional
from loguru import logger

class BaseAsyncClient(ABC):
    """Base class for async API clients."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling."""
        if self._session is None:
            # Connection pooling with limits
            connector = aiohttp.TCPConnector(
                limit=100,  # Max total connections
                limit_per_host=10,  # Max per host
                ttl_dns_cache=300,
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
            )
        return self._session

    async def close(self) -> None:
        """Cleanup session."""
        if self._session:
            await self._session.close()
            self._session = None

    @abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with the service."""
        pass

    @abstractmethod
    async def make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict:
        """Make authenticated API request."""
        pass

    async def _handle_rate_limit(self, response: aiohttp.ClientResponse) -> None:
        """Handle rate limiting with exponential backoff."""
        if response.status == 429:
            retry_after = int(response.headers.get('Retry-After', '5'))
            logger.warning(f"Rate limited, retrying after {retry_after}s")
            await asyncio.sleep(retry_after)

    async def _handle_error(self, error: Exception) -> None:
        """Log and handle errors."""
        logger.error(f"Request failed: {error}")
        raise
```

## Database Integration (Supabase + asyncpg)

**MCP-Based Discovery:**
```python
# Search for database patterns
search_codebase("SupabaseClient", top_k=10)
search_codebase("asyncpg.*pool", top_k=10)
```

**Supabase Client with Connection Pooling:**
```python
import asyncpg
from typing import Any, Optional, List
from loguru import logger

class SupabaseClient:
    """Supabase client with connection pooling."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        min_size: int = 5,
        max_size: int = 20
    ):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize connection pool."""
        self._pool = await asyncpg.create_pool(
            dsn=self._build_dsn(),
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=60,
            max_inactive_connection_lifetime=300,
        )
        logger.info(f"Initialized connection pool (min={self.min_size}, max={self.max_size})")

    async def execute_query(self, query: str, *args) -> List[Any]:
        """Execute query with connection from pool."""
        if not self._pool:
            await self.initialize()

        async with self._pool.acquire() as conn:
            result = await conn.fetch(query, *args)
            logger.debug(f"Query returned {len(result)} rows")
            return result

    async def execute_command(self, command: str, *args) -> str:
        """Execute SQL command (INSERT/UPDATE/DELETE)."""
        if not self._pool:
            await self.initialize()

        async with self._pool.acquire() as conn:
            result = await conn.execute(command, *args)
            logger.debug(f"Command affected {result} rows")
            return result

    async def batch_insert(self, table: str, data: List[dict]) -> None:
        """Batch insert for performance."""
        # Avoid N+1 queries
        columns = list(data[0].keys())
        values = [[row[col] for col in columns] for row in data]

        if not self._pool:
            await self.initialize()

        async with self._pool.acquire() as conn:
            await conn.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['$' + str(i+1) for i in range(len(columns))])})",
                values
            )
            logger.info(f"Batch inserted {len(data)} rows into {table}")

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Connection pool closed")

    def _build_dsn(self) -> str:
        """Build DSN from URL and key."""
        return f"postgresql://postgres.{self.supabase_url}:{self.supabase_key}@aws-0-{self._parse_region()}.supabase.co/postgres"
```

## OAuth2 Authentication Flow

**MCP-Based Discovery:**
```python
# Search for OAuth patterns
search_codebase("OAuth2|oauth|token", top_k=20)
```

**OAuth2 Client Template:**
```python
import aiohttp
from typing import Any, Optional
from loguru import logger
import base64
import hashlib
import secrets

class OAuth2Client:
    """OAuth2 client for service authentication."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        auth_url: str,
        token_url: str,
        scope: Optional[str] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.scope = scope
        self._token: Optional[dict] = None

    async def get_auth_code(self) -> str:
        """Get authorization code from user."""
        # Generate PKCE verifier
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')

        # Build authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': 'http://localhost:8000/callback',
            'scope': self.scope or '',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }

        auth_url = f"{self.auth_url}?{ '&'.join(f'{k}={v}' for k, v in auth_params.items())}"
        logger.info(f"Authorization URL: {auth_url}")

        return auth_url

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': 'http://localhost:8000/callback',
            }) as response:
                if response.status != 200:
                    raise Exception(f"Token exchange failed: {response.status}")

                self._token = await response.json()
                logger.info("Successfully obtained access token")
                return self._token

    async def refresh_token(self) -> dict:
        """Refresh expired access token."""
        if not self._token:
            raise Exception("No token to refresh")

        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data={
                'grant_type': 'refresh_token',
                'refresh_token': self._token['refresh_token'],
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }) as response:
                if response.status != 200:
                    raise Exception(f"Token refresh failed: {response.status}")

                self._token = await response.json()
                logger.info("Successfully refreshed access token")
                return self._token

    def get_headers(self) -> dict:
        """Get headers with authorization."""
        if not self._token:
            raise Exception("Not authenticated")

        return {
            'Authorization': f"Bearer {self._token['access_token']}",
            'Content-Type': 'application/json',
        }
```

## Resource Manager Pattern

**MCP-Based Discovery:**
```python
# Search for resource managers
search_codebase("ResourceManager", top_k=15)
```

**Generic Resource Manager:**
```python
import asyncio
from abc import ABC, abstractmethod
from loguru import logger

class ResourceManager(ABC):
    """Base class for managing reusable resources."""

    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._pool: list = []
        self._available = asyncio.Condition()
        self._in_use = {}

    @abstractmethod
    async def create_resource(self) -> Any:
        """Create new resource instance."""
        pass

    @abstractmethod
    async def cleanup_resource(self, resource: Any) -> None:
        """Cleanup resource."""
        pass

    async def acquire(self) -> Any:
        """Acquire resource from pool."""
        async with self._available:
            # Wait for available resource or create new
            while len(self._pool) == 0 and len(self._in_use) >= self.max_size:
                await self._available.wait()

            if self._pool:
                resource = self._pool.pop()
            else:
                resource = await self.create_resource()

            self._in_use[id(resource)] = True
            return resource

    async def release(self, resource: Any) -> None:
        """Release resource back to pool."""
        if id(resource) not in self._in_use:
            logger.warning(f"Resource {resource} not in use")
            return

        del self._in_use[id(resource)]

        if len(self._pool) < self.max_size:
            self._pool.append(resource)
        else:
            await self.cleanup_resource(resource)

        async with self._available:
            self._available.notify()
```

## Integration Testing Patterns

**MCP-Based Discovery:**
```python
# Search for integration tests
search_codebase("test_integration", top_k=20)
```

**Test Template with Mocked External Services:**
```python
import pytest
from unittest.mock import AsyncMock, patch
from casare_rpa.infrastructure.clients.github_client import GitHubClient

@pytest.fixture
async def mock_github_client():
    """Mock GitHub client for testing."""
    with patch('casare_rpa.infrastructure.clients.github_client.aiohttp') as mock_http:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'login': 'test'})
        mock_http.ClientSession.return_value.__aenter__.return_value.get.return_value = mock_response

        client = GitHubClient('test_id', 'test_secret', 'http://mock')
        yield client

@pytest.mark.asyncio
async def test_get_auth_url(mock_github_client):
    """Test OAuth URL generation."""
    url = await mock_github_client.get_auth_code()

    assert 'github.com' in url
    assert 'client_id=test_id' in url

@pytest.mark.asyncio
async def test_exchange_token_success(mock_github_client):
    """Test token exchange."""
    token = await mock_github_client.exchange_code_for_token('test_code')

    assert 'access_token' in token
    assert 'refresh_token' in token
```

## Error Handling and Retries

**Exponential Backoff Retry:**
```python
import asyncio
import aiohttp
from loguru import logger

class RetryableClient(BaseAsyncClient):
    """Client with automatic retry on transient failures."""

    async def make_request(self, method: str, endpoint: str, max_retries: int = 3, **kwargs) -> dict:
        """Make request with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                return await super().make_request(method, endpoint, **kwargs)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for {endpoint}")
                    raise

                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)

        raise Exception(f"Failed after {max_retries} attempts")
```

## Common Integrations

### Google APIs (Gmail, Drive, Sheets)

**MCP-Based Research:**
```python
websearch("Python Google OAuth2 client example 2025", numResults=5)
websearch("Gmail API Python async implementation", numResults=3)
```

**Pattern:**
```python
class GoogleAPIClient(BaseAsyncClient):
    """Google API client with OAuth2."""

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
    ]

    async def authenticate(self) -> None:
        """OAuth2 flow for Google."""
        # Use Google OAuth2 endpoints
        # Exchange code for token
        pass

    async def get_gmail_messages(self) -> list[dict]:
        """Get Gmail messages."""
        headers = self.get_headers()
        async with self.get_session() as session:
            async with session.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/messages',
                headers=headers
            ) as response:
                return await response.json()
```

### Microsoft Graph (Office 365)

**MCP-Based Research:**
```python
websearch("Microsoft Graph API Python authentication 2025", numResults=5)
```

### REST API Generic

**Generic REST Client:**
```python
from .base import BaseAsyncClient
from typing import Any, Optional

class RESTAPIClient(BaseAsyncClient):
    """Generic REST API client."""

    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """Make REST API request."""
        session = await self.get_session()
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers()

        async with session.request(method, url, params=params, json=json_data, headers=headers) as response:
            # Handle rate limiting
            await self._handle_rate_limit(response)

            # Handle errors
            if response.status >= 400:
                await self._handle_error(response.status, await response.text())

            return await response.json()
```

## Integration Checklist

- [ ] Async pattern used throughout
- [ ] Connection pooling implemented
- [ ] Proper error handling with retries
- [ ] OAuth2 flow secure (PKCE)
- [ ] Resource managers for cleanup
- [ ] Mocks for integration tests
- [ ] Exponential backoff for retries
- [ ] Logging for all API calls
- [ ] Secrets from environment variables
- [ ] Rate limiting respected

## Usage

Invoke this skill when:
- Creating new API integration
- Implementing OAuth2 flow
- Setting up database connections
- Adding resource managers
- Debugging integration issues

```python
Task(subagent_type="integrations", prompt="""
Use integrations skill with MCP-first approach:

Task: Create Shopify API client for order management
Requirements:
- OAuth2 authentication
- Rate limiting with backoff retry
- Connection pooling (max 10 concurrent)
- Mockable for tests

MCP Workflow:
1. codebase: Find existing API client patterns
2. filesystem: Read base client implementation
3. exa: Research Shopify API authentication
4. ref: Look up aiohttp documentation
5. sequential-thinking: Plan client architecture

Implement with:
- BaseAsyncClient inheritance
- Proper error handling
- Resource pool management
- Integration test mocks
""")
```

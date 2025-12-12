# Authentication

CasareRPA implements multiple authentication methods to secure access to the Canvas designer, Orchestrator API, and Robot agents.

## Authentication Methods Overview

| Method | Use Case | Lifespan | Refresh |
|--------|----------|----------|---------|
| JWT Tokens | Canvas UI, API access | 1 hour | Yes |
| Robot API Keys | Robot-to-Orchestrator | Long-lived | Manual rotation |
| OAuth 2.0 | Google Workspace integration | Variable | Automatic |
| Session Tokens | UI session management | 8 hours | Activity-based |

## JWT Tokens

JSON Web Tokens provide stateless authentication for the Canvas UI and Orchestrator API.

### Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_uuid",
    "tenant_id": "tenant_uuid",
    "roles": ["developer", "operator"],
    "iat": 1704067200,
    "exp": 1704070800,
    "jti": "unique_token_id"
  }
}
```

### Token Flow

```mermaid
sequenceDiagram
    participant User
    participant Canvas
    participant Auth as Auth Service
    participant API as Orchestrator API

    User->>Canvas: Enter credentials
    Canvas->>Auth: POST /auth/login
    Auth->>Auth: Validate credentials
    Auth-->>Canvas: Access Token + Refresh Token

    Canvas->>API: Request + Bearer Token
    API->>API: Verify JWT signature
    API->>API: Check token claims
    API-->>Canvas: Response

    Note over Canvas: Token expires...

    Canvas->>Auth: POST /auth/refresh
    Auth->>Auth: Validate refresh token
    Auth-->>Canvas: New Access Token
```

### Usage Example

```python
from casare_rpa.infrastructure.auth import TokenManager, TokenConfig

# Configure token manager
config = TokenConfig(
    secret_key=settings.jwt_secret,
    algorithm="RS256",
    access_token_ttl_seconds=3600,  # 1 hour
    refresh_token_ttl_seconds=604800,  # 7 days
    issuer="casare-rpa"
)

token_manager = TokenManager(config)

# Create tokens on login
access_token = token_manager.create_access_token(
    user_id=user.id,
    tenant_id=user.tenant_id,
    roles=user.roles,
    additional_claims={"email": user.email}
)

refresh_token = token_manager.create_refresh_token(
    user_id=user.id,
    tenant_id=user.tenant_id
)

# Verify incoming token
try:
    claims = token_manager.verify_token(access_token)
    user_id = claims["sub"]
    roles = claims["roles"]
except TokenExpiredError:
    # Token expired, client should refresh
    raise HTTPException(status_code=401, detail="Token expired")
except InvalidTokenError:
    # Invalid signature or claims
    raise HTTPException(status_code=401, detail="Invalid token")
```

### Token Refresh Flow

```python
from casare_rpa.infrastructure.auth import TokenManager

async def refresh_tokens(refresh_token: str) -> dict:
    """Refresh access token using refresh token."""
    token_manager = TokenManager(config)

    # Verify refresh token
    claims = token_manager.verify_refresh_token(refresh_token)
    user_id = claims["sub"]

    # Load user to get current roles
    user = await user_repository.get(user_id)
    if not user or not user.is_active:
        raise InvalidTokenError("User not found or inactive")

    # Issue new tokens
    new_access = token_manager.create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        roles=user.roles
    )

    # Optionally rotate refresh token
    new_refresh = token_manager.create_refresh_token(
        user_id=user.id,
        tenant_id=user.tenant_id
    )

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": 3600
    }
```

## Robot API Keys

Robot agents authenticate using long-lived API keys for reliable unattended operation.

### Key Structure

Robot API keys follow this format:
```
casare_robot_<base64_encoded_payload>.<signature>
```

### Key Generation

```python
from casare_rpa.infrastructure.auth.robot_api_keys import (
    RobotApiKeyManager,
    RobotApiKeyConfig
)

config = RobotApiKeyConfig(
    signing_key=settings.api_key_signing_key,
    key_prefix="casare_robot_",
    default_expiry_days=365
)

key_manager = RobotApiKeyManager(config)

# Generate new API key for robot
api_key, key_id = await key_manager.create_key(
    robot_id=robot.id,
    tenant_id=robot.tenant_id,
    name="Production Robot 1",
    scopes=["execution.run", "heartbeat.send"],
    expires_at=datetime.now() + timedelta(days=365)
)

# Store key_id in database (never store the full key)
await robot_repository.update(robot.id, api_key_id=key_id)

# Return full key to user ONCE
return {"api_key": api_key, "expires_at": "2026-01-01"}
```

### Key Validation

```python
from casare_rpa.infrastructure.auth.robot_api_keys import RobotApiKeyManager

async def validate_robot_request(api_key: str) -> RobotContext:
    """Validate robot API key and return context."""
    key_manager = RobotApiKeyManager(config)

    try:
        key_data = await key_manager.validate_key(api_key)
    except InvalidApiKeyError:
        raise HTTPException(status_code=401, detail="Invalid API key")
    except ExpiredApiKeyError:
        raise HTTPException(status_code=401, detail="API key expired")

    # Check if key is revoked
    if await key_manager.is_revoked(key_data.key_id):
        raise HTTPException(status_code=401, detail="API key revoked")

    return RobotContext(
        robot_id=key_data.robot_id,
        tenant_id=key_data.tenant_id,
        scopes=key_data.scopes
    )
```

### Key Rotation

```python
async def rotate_robot_key(robot_id: UUID) -> dict:
    """Rotate API key for a robot."""
    key_manager = RobotApiKeyManager(config)

    # Get current key info
    robot = await robot_repository.get(robot_id)
    old_key_id = robot.api_key_id

    # Create new key
    new_key, new_key_id = await key_manager.create_key(
        robot_id=robot_id,
        tenant_id=robot.tenant_id,
        name=f"{robot.name} (rotated)",
        scopes=robot.scopes
    )

    # Update robot with new key
    await robot_repository.update(robot_id, api_key_id=new_key_id)

    # Revoke old key (with grace period)
    await key_manager.revoke_key(
        old_key_id,
        reason="Key rotation",
        grace_period_hours=24  # Allow 24h overlap
    )

    return {"api_key": new_key}
```

## OAuth 2.0 (Google Services)

CasareRPA uses OAuth 2.0 for Google Workspace integrations (Gmail, Drive, Sheets, Calendar).

### OAuth Flow

```mermaid
sequenceDiagram
    participant User
    participant Canvas
    participant Auth as CasareRPA Auth
    participant Google

    User->>Canvas: Add Google credential
    Canvas->>Auth: Initiate OAuth flow
    Auth-->>Canvas: Redirect URL

    Canvas->>Google: Authorization request
    Google->>User: Consent screen
    User->>Google: Grant permissions
    Google-->>Canvas: Authorization code

    Canvas->>Auth: Exchange code
    Auth->>Google: Token request
    Google-->>Auth: Access + Refresh tokens
    Auth->>Auth: Store encrypted tokens
    Auth-->>Canvas: Credential created
```

### OAuth Configuration

```python
from casare_rpa.infrastructure.security.google_oauth import (
    GoogleOAuthCredentialData,
    GoogleOAuthManager,
    get_google_access_token
)

# OAuth credential data structure
credential_data = GoogleOAuthCredentialData(
    client_id="your_client_id.apps.googleusercontent.com",
    client_secret="your_client_secret",
    access_token="ya29.xxx",
    refresh_token="1//xxx",
    token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
    scopes=[
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ],
    user_email="user@example.com"
)
```

### Automatic Token Refresh

```python
from casare_rpa.infrastructure.security.google_oauth import (
    GoogleOAuthManager,
    get_google_access_token
)

# Get access token (automatically refreshes if expired)
access_token = await get_google_access_token(credential_id)

# Use in workflow nodes
async def gmail_read_node(credential_id: str) -> list:
    manager = await GoogleOAuthManager.get_instance()
    token = await manager.get_access_token(credential_id)

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(GMAIL_API_URL, headers=headers) as resp:
            return await resp.json()
```

### Token Refresh Implementation

```python
# Internal refresh mechanism
async def _refresh_token(self, credential_id: str) -> GoogleOAuthCredentialData:
    """Refresh Google OAuth access token."""
    credential_data = await self._get_credential_data(credential_id)

    async with aiohttp.ClientSession() as session:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": credential_data.refresh_token,
            "client_id": credential_data.client_id,
            "client_secret": credential_data.client_secret,
        }

        async with session.post(GOOGLE_TOKEN_ENDPOINT, data=data) as response:
            result = await response.json()

            if "error" in result:
                raise TokenRefreshError(result["error_description"])

            # Update credential with new token
            credential_data.access_token = result["access_token"]
            credential_data.token_expiry = datetime.now(timezone.utc) + timedelta(
                seconds=result["expires_in"]
            )

            # Persist updated tokens
            await self._persist_credential(credential_id, credential_data)

            return credential_data
```

## Session Management

The SessionManager handles user sessions with security controls for the Canvas UI.

### Session Configuration

```python
from casare_rpa.infrastructure.auth import SessionManager, SessionConfig, ClientInfo

config = SessionConfig(
    session_timeout_minutes=480,  # 8 hour max session
    idle_timeout_minutes=30,      # 30 min idle timeout
    max_sessions_per_user=3,      # Max concurrent sessions
    refresh_token_days=30,
    enforce_single_session=False  # Set True for high-security
)

session_manager = SessionManager(config)
```

### Session Creation

```python
from casare_rpa.infrastructure.auth import SessionManager, ClientInfo

async def login(credentials: LoginRequest, request: Request) -> LoginResponse:
    # Validate credentials
    user = await authenticate_user(credentials.email, credentials.password)

    # Create JWT token
    token = token_manager.create_access_token(user.id, user.roles)

    # Create session with client info
    client_info = ClientInfo(
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        device_id=request.headers.get("x-device-id")
    )

    session = await session_manager.create_session(
        user_id=user.id,
        token=token,
        client_info=client_info
    )

    return LoginResponse(
        access_token=token,
        session_id=session.id,
        expires_at=session.expires_at
    )
```

### Session Validation

```python
async def validate_session(token: str, update_activity: bool = True) -> Session:
    """Validate session and update activity."""
    try:
        session = await session_manager.validate_session(
            token=token,
            update_activity=update_activity
        )
        return session
    except SessionExpiredError:
        raise HTTPException(status_code=401, detail="Session expired")
    except SessionError:
        raise HTTPException(status_code=401, detail="Invalid session")
```

### Session Invalidation (Logout)

```python
async def logout(token: str) -> None:
    """Invalidate user session."""
    await session_manager.invalidate_session(
        token=token,
        reason="User logout"
    )

async def logout_all_sessions(user_id: UUID) -> int:
    """Force logout from all sessions (password change, security event)."""
    count = await session_manager.invalidate_all_sessions(
        user_id=user_id,
        reason="Security: Password changed"
    )
    return count
```

### Session Activity Tracking

```python
# Session properties
session.is_valid           # Check if session is currently valid
session.is_expired         # Check if session has expired
session.time_since_activity  # Time since last activity

# Get all user sessions
sessions = await session_manager.get_user_sessions(user_id)
for s in sessions:
    print(f"Session {s.id[:12]}... from {s.client_info.ip_address}")
```

## Multi-Factor Authentication (TOTP)

CasareRPA supports TOTP-based MFA for enhanced security.

### Setup Flow

```python
from casare_rpa.infrastructure.auth import TOTPManager

totp = TOTPManager(issuer="CasareRPA")

# Generate secret for user
secret = totp.generate_secret()

# Generate provisioning URI for authenticator app
uri = totp.get_provisioning_uri(
    secret=secret,
    user_email=user.email
)

# Generate QR code
qr_bytes = totp.generate_qr_code(uri)

# Store secret securely (encrypted in credential store)
await store_totp_secret(user.id, secret)

# Return QR to user for setup
return Response(content=qr_bytes, media_type="image/png")
```

### Verification Flow

```python
async def verify_mfa(user_id: UUID, code: str) -> bool:
    """Verify MFA code during login."""
    totp = TOTPManager()

    # Retrieve user's TOTP secret
    secret = await get_totp_secret(user_id)
    if not secret:
        return False  # MFA not configured

    # Verify code (allows 1 interval before/after for clock skew)
    is_valid = totp.verify_code(
        secret=secret,
        code=code,
        valid_window=1  # +/- 30 seconds
    )

    if is_valid:
        # Log successful MFA
        await log_audit_event(
            action=AuditAction.LOGIN,
            actor_id=user_id,
            resource_type=ResourceType.USER,
            details={"mfa": "totp"}
        )

    return is_valid
```

### TOTP Properties

```python
# TOTP configuration
TOTP_DIGITS = 6          # 6-digit codes
TOTP_INTERVAL = 30       # 30-second validity
TOTP_VALID_WINDOW = 1    # Accept +/- 1 interval

# Check time remaining on current code
totp = TOTPManager()
seconds_remaining = totp.get_time_remaining()
```

## API Authentication Examples

### curl Examples

```bash
# Login and get tokens
curl -X POST https://orchestrator.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'

# Use access token
curl https://orchestrator.example.com/api/v1/workflows \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..."

# Refresh token
curl -X POST https://orchestrator.example.com/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJSUzI1NiIs..."}'

# Robot authentication
curl https://orchestrator.example.com/api/v1/robot/heartbeat \
  -H "X-API-Key: casare_robot_xxxxx.signature"
```

### Python Examples

```python
import httpx

# Login
async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://orchestrator.example.com/api/v1/auth/login",
        json={"email": "user@example.com", "password": "secret"}
    )
    tokens = response.json()

    # Use access token
    response = await client.get(
        "https://orchestrator.example.com/api/v1/workflows",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
```

## Security Considerations

### Token Security

- Store tokens securely (HttpOnly cookies for web, secure storage for desktop)
- Use short-lived access tokens (1 hour)
- Implement token refresh rotation
- Revoke tokens on password change

### API Key Security

- Never log or expose full API keys
- Rotate keys periodically (at least annually)
- Use key-specific scopes (least privilege)
- Monitor key usage for anomalies

### MFA Considerations

- Enforce MFA for admin roles
- Provide backup codes for account recovery
- Support multiple MFA methods (future: WebAuthn)
- Rate-limit MFA attempts

## Related Documentation

- [Security Architecture](./architecture.md)
- [Credential Management](./credentials.md)
- [Security Best Practices](./best-practices.md)

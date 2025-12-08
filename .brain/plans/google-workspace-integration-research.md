# Research: n8n-Style Google Workspace Integration for CasareRPA

**Date**: 2025-12-08
**Status**: Research Complete
**Researcher**: Research Agent

---

## Executive Summary

This document provides comprehensive research on implementing n8n-style Google Workspace integration for CasareRPA. CasareRPA already has a solid foundation with `GoogleAPIClient`, `GoogleBaseNode`, and a `CredentialStore` system. The key enhancements needed are:

1. OAuth2 desktop flow with PKCE for user authentication
2. Enhanced credential system for OAuth2 tokens (not just API keys)
3. Cascading dropdown UI for resource selection
4. Complete node operations covering all Google Workspace services

---

## 1. n8n Credential System Patterns

### How n8n Implements OAuth2 for Google

n8n uses a **Web Application** OAuth flow with redirect URI, configured in Google Cloud Console. Key aspects:

**Credential Fields Stored:**
| Field | Description |
|-------|-------------|
| `client_id` | OAuth client ID from Google Cloud Console |
| `client_secret` | OAuth client secret |
| `access_token` | Short-lived access token (~1 hour) |
| `refresh_token` | Long-lived token for automatic refresh |
| `token_uri` | Token endpoint (`https://oauth2.googleapis.com/token`) |
| `scopes` | List of granted OAuth scopes |
| `expiry` | Token expiration timestamp |

**n8n Credential Types for Google:**
1. **OAuth2 Single Service** - Pre-configured scopes for specific services (Gmail, Sheets, etc.)
2. **OAuth2 Generic** - Custom scope selection for advanced use cases
3. **Service Account** - For server-to-server authentication

**Credential Dropdown Filtering:**
- n8n filters credentials by type - only credentials compatible with the node appear
- Each node declares required credential types (e.g., `credentialTypes: ['googleSheetsOAuth2Api']`)

### CasareRPA Current State

CasareRPA already has:
- `CredentialStore` with encrypted storage (Fernet/DPAPI)
- `CredentialType.OAUTH_TOKEN` enum
- `GoogleCredentials` dataclass with all required fields
- `CredentialAwareMixin` for vault resolution

**Gap to Address:**
- Need OAuth2 flow UI for desktop apps (PKCE + localhost redirect)
- Need credential filtering by scope/service in node UI

---

## 2. Google OAuth2 Best Practices for Desktop Apps

### PKCE Flow (Required for Desktop Apps)

Google requires PKCE (Proof Key for Code Exchange) for native/desktop applications:

```
1. Generate code_verifier (43-128 chars, [A-Za-z0-9-._~])
2. Generate code_challenge = BASE64URL(SHA256(code_verifier))
3. Open browser to authorization URL with:
   - client_id
   - redirect_uri (http://localhost:{port} or http://127.0.0.1:{port})
   - response_type=code
   - scope
   - code_challenge
   - code_challenge_method=S256
4. User grants consent in browser
5. Browser redirects to localhost with authorization code
6. Exchange code + code_verifier for tokens
7. Store tokens securely
```

### PKCE Implementation Code Pattern

```python
import base64
import hashlib
import secrets
from urllib.parse import urlencode

def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge."""
    # Generate code_verifier (43-128 chars)
    code_verifier = secrets.token_urlsafe(64)[:64]

    # Generate code_challenge (S256 method)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

    return code_verifier, code_challenge

def build_auth_url(client_id: str, redirect_uri: str, scopes: list,
                   code_challenge: str, state: str = None):
    """Build Google OAuth2 authorization URL."""
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(scopes),
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'access_type': 'offline',  # Get refresh_token
        'prompt': 'consent',  # Force consent screen
    }
    if state:
        params['state'] = state

    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
```

### Token Storage Security

**Recommended Approach for CasareRPA (Windows Desktop):**

| Platform | Storage Method |
|----------|---------------|
| Windows | DPAPI (CryptProtectData) - already implemented in `CredentialStore` |
| macOS | Keychain Services |
| Linux | libsecret / GNOME Keyring |

CasareRPA's `CredentialStore` already uses DPAPI on Windows with fallback to machine-specific key derivation.

### Token Refresh Implementation

```python
async def refresh_google_token(credentials: GoogleCredentials) -> GoogleCredentials:
    """Refresh OAuth2 access token."""
    async with aiohttp.ClientSession() as session:
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': credentials.refresh_token,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
        }

        async with session.post('https://oauth2.googleapis.com/token', data=data) as resp:
            result = await resp.json()

            if 'error' in result:
                raise GoogleAuthError(result.get('error_description', result['error']))

            credentials.access_token = result['access_token']
            credentials.expiry = time.time() + result.get('expires_in', 3600)

            # New refresh_token may be issued
            if 'refresh_token' in result:
                credentials.refresh_token = result['refresh_token']

            return credentials
```

### Supporting Personal and Workspace Accounts

Both account types work with the same OAuth2 flow. Key differences:

| Aspect | Personal Account | Google Workspace |
|--------|-----------------|------------------|
| Consent Screen | External (requires verification for >100 users) | Internal (auto-approved for org users) |
| Scopes | May require app verification for sensitive scopes | Admin can pre-approve scopes |
| Domain | @gmail.com | Custom domain |

**Recommendation:** Use External consent screen to support both types, with clear user messaging.

---

## 3. Cascading Dropdown Patterns

### How n8n Loads Dependent Dropdowns

n8n uses `loadOptionsMethod` with `loadOptionsDependsOn` for cascading fields:

```typescript
// n8n node parameter definition
{
    displayName: 'Sheet',
    name: 'sheetName',
    type: 'options',
    typeOptions: {
        loadOptionsMethod: 'getSheets',
        loadOptionsDependsOn: ['spreadsheetId'],  // Reload when spreadsheetId changes
    },
}

// loadOptions implementation
methods = {
    loadOptions: {
        async getSheets(this: ILoadOptionsFunctions) {
            const spreadsheetId = this.getCurrentNodeParameter('spreadsheetId');
            // API call to get sheets...
            return sheets.map(s => ({ name: s.title, value: s.sheetId }));
        }
    }
}
```

### CasareRPA Cascading Dropdown Implementation

**Recommended Pattern for CasareRPA:**

```python
# In node schema
SPREADSHEET_SELECTION_PROPS = (
    PropertyDef(
        name="spreadsheet_mode",
        type=PropertyType.ENUM,
        default="from_list",
        options=["from_list", "by_id", "by_url"],
        label="Select Spreadsheet",
    ),
    PropertyDef(
        name="spreadsheet_id",
        type=PropertyType.STRING,
        default="",
        label="Spreadsheet",
        dynamic_options="load_spreadsheets",  # New: indicates dynamic loading
        depends_on=["credential_name"],  # Reload when credential changes
    ),
    PropertyDef(
        name="sheet_name",
        type=PropertyType.STRING,
        default="",
        label="Sheet",
        dynamic_options="load_sheets",
        depends_on=["spreadsheet_id"],  # Reload when spreadsheet changes
    ),
)

# In visual node
class VisualSheetsNode:
    async def load_spreadsheets(self, credential_name: str) -> list[tuple[str, str]]:
        """Load available spreadsheets for dropdown."""
        # 1. Get credentials from store
        # 2. Call Drive API to list spreadsheets
        # 3. Return [(id, title), ...]

    async def load_sheets(self, spreadsheet_id: str) -> list[tuple[str, str]]:
        """Load sheets within a spreadsheet."""
        # 1. Call Sheets API spreadsheets.get()
        # 2. Return [(sheetId, title), ...]
```

### Caching Strategy

| Cache Level | TTL | Purpose |
|-------------|-----|---------|
| Session | Until credential change | Avoid repeated auth |
| Resource List | 5 minutes | Spreadsheet/file lists |
| Schema | 10 minutes | Sheet structure, columns |

**Implementation:**

```python
from functools import lru_cache
from cachetools import TTLCache

class GoogleResourceCache:
    def __init__(self):
        self._cache = TTLCache(maxsize=100, ttl=300)  # 5 min TTL

    def get_spreadsheets(self, credential_id: str) -> list | None:
        return self._cache.get(f"spreadsheets:{credential_id}")

    def set_spreadsheets(self, credential_id: str, items: list):
        self._cache[f"spreadsheets:{credential_id}"] = items
```

### Loading States and Error Handling

**UI Pattern for CasareRPA:**

```python
class DynamicDropdown(QComboBox):
    def __init__(self):
        super().__init__()
        self._loading = False

    def set_loading(self, loading: bool):
        self._loading = loading
        if loading:
            self.clear()
            self.addItem("Loading...", None)
            self.setEnabled(False)
        else:
            self.setEnabled(True)

    def set_error(self, message: str):
        self.clear()
        self.addItem(f"Error: {message}", None)
        self.setEnabled(True)
```

---

## 4. Google API Specifics

### Complete OAuth2 Scopes by Service

#### Google Drive
| Scope | Access Level |
|-------|-------------|
| `https://www.googleapis.com/auth/drive` | Full access to all files |
| `https://www.googleapis.com/auth/drive.file` | Access only files created by app |
| `https://www.googleapis.com/auth/drive.readonly` | Read-only access to all files |
| `https://www.googleapis.com/auth/drive.metadata.readonly` | View file metadata only |
| `https://www.googleapis.com/auth/drive.activity` | View/add activity records |
| `https://www.googleapis.com/auth/drive.activity.readonly` | View activity only |

#### Google Sheets
| Scope | Access Level |
|-------|-------------|
| `https://www.googleapis.com/auth/spreadsheets` | Full access to all spreadsheets |
| `https://www.googleapis.com/auth/spreadsheets.readonly` | Read-only access |

#### Gmail
| Scope | Access Level |
|-------|-------------|
| `https://mail.google.com/` | Full access (IMAP/SMTP) |
| `https://www.googleapis.com/auth/gmail.readonly` | Read messages and settings |
| `https://www.googleapis.com/auth/gmail.modify` | Read, compose, send (no delete) |
| `https://www.googleapis.com/auth/gmail.compose` | Manage drafts and send |
| `https://www.googleapis.com/auth/gmail.send` | Send only |
| `https://www.googleapis.com/auth/gmail.insert` | Insert messages |
| `https://www.googleapis.com/auth/gmail.labels` | Manage labels |
| `https://www.googleapis.com/auth/gmail.metadata` | View metadata only |
| `https://www.googleapis.com/auth/gmail.settings.basic` | Manage settings/filters |
| `https://www.googleapis.com/auth/gmail.settings.sharing` | Manage sensitive settings |

#### Google Calendar
| Scope | Access Level |
|-------|-------------|
| `https://www.googleapis.com/auth/calendar` | Full access |
| `https://www.googleapis.com/auth/calendar.readonly` | Read-only |
| `https://www.googleapis.com/auth/calendar.events` | Manage events |
| `https://www.googleapis.com/auth/calendar.events.readonly` | Read events only |
| `https://www.googleapis.com/auth/calendar.settings.readonly` | Read settings |
| `https://www.googleapis.com/auth/calendar.acls` | Manage sharing |

#### Google Docs
| Scope | Access Level |
|-------|-------------|
| `https://www.googleapis.com/auth/documents` | Full access |
| `https://www.googleapis.com/auth/documents.readonly` | Read-only |

### Rate Limits by Service

| API | Limit | Notes |
|-----|-------|-------|
| Sheets | 300 read/min, 300 write/min per project | Batch requests count as 1 |
| Gmail | 250 quota units/user/second | Different operations cost different units |
| Drive | 12,000 queries/min per project | File operations have separate limits |
| Calendar | 100 requests/100 seconds/user | |
| Docs | 300 requests/min per project | |

**Rate Limit Handling (Already in CasareRPA):**

```python
# GoogleAPIClient already has rate limiting
self._rate_limiter = SlidingWindowRateLimiter(
    max_requests=config.rate_limit_requests,  # Default 10/s
    window_seconds=config.rate_limit_window,
)
```

### Batch Request Patterns

```python
async def batch_update_sheets(client: GoogleAPIClient, spreadsheet_id: str,
                              updates: list[dict]) -> list[dict]:
    """Batch multiple sheet updates into single request."""
    service = await client.get_service('sheets')

    body = {
        'requests': updates  # List of updateCells, appendCells, etc.
    }

    request = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    )

    return await client.execute_request(request)
```

---

## 5. Node Design Patterns (n8n Reference)

### Google Sheets Operations

| Operation | Description | Required Params |
|-----------|-------------|-----------------|
| **Document** | | |
| Create | Create new spreadsheet | title, sheets[] |
| Delete | Delete spreadsheet | spreadsheetId |
| **Sheet** | | |
| Append Row | Add row at end | spreadsheetId, sheetName, data |
| Append or Update | Upsert by key column | spreadsheetId, sheetName, keyColumn, data |
| Clear | Clear sheet contents | spreadsheetId, range |
| Create | Add new sheet | spreadsheetId, title |
| Delete | Remove sheet | spreadsheetId, sheetId |
| Get Row(s) | Read rows | spreadsheetId, range |
| Update Row | Update existing row | spreadsheetId, range, data |
| Delete Rows/Columns | Remove rows/cols | spreadsheetId, dimension, startIndex, endIndex |

### Gmail Operations

| Resource | Operation | Description |
|----------|-----------|-------------|
| **Message** | | |
| | Send | Send email |
| | Get | Get message by ID |
| | Get Many | List messages with filters |
| | Delete | Delete message |
| | Mark Read/Unread | Update read status |
| | Add Label | Add label to message |
| | Remove Label | Remove label |
| | Reply | Reply to thread |
| **Thread** | | |
| | Get | Get thread by ID |
| | Get Many | List threads |
| | Delete | Delete thread |
| | Trash/Untrash | Move to/from trash |
| | Add/Remove Label | Label operations |
| **Label** | | |
| | Create | Create label |
| | Delete | Delete label |
| | Get Many | List labels |
| **Draft** | | |
| | Create | Create draft |
| | Delete | Delete draft |
| | Get | Get draft |
| | Send | Send draft |

### Google Drive Operations

| Resource | Operation | Description |
|----------|-----------|-------------|
| **File** | | |
| | Upload | Upload file |
| | Download | Download file |
| | Copy | Copy file |
| | Update | Update file content |
| | Delete | Delete file |
| | Move | Move to folder |
| | Share | Update permissions |
| **Folder** | | |
| | Create | Create folder |
| | Delete | Delete folder |
| | Share | Update permissions |
| **File/Folder** | | |
| | Search | Find by name or query |

### Google Calendar Operations

| Resource | Operation | Description |
|----------|-----------|-------------|
| **Event** | | |
| | Create | Create event |
| | Delete | Delete event |
| | Get | Get event by ID |
| | Get Many | List events |
| | Update | Update event |
| **Calendar** | | |
| | Get Availability | Check free/busy |

### Google Docs Operations

| Operation | Description |
|-----------|-------------|
| Create | Create new document |
| Get | Get document content |
| Update | Insert/replace text (limited formatting in n8n core) |

---

## 6. Recommended Implementation for CasareRPA

### Phase 1: OAuth2 Desktop Flow

1. **Create `OAuthFlowManager`** in `infrastructure/auth/`:
   ```python
   class GoogleOAuthFlowManager:
       def __init__(self, client_id: str, client_secret: str):
           self.client_id = client_id
           self.client_secret = client_secret
           self._server: LocalhostServer = None

       async def start_auth_flow(self, scopes: list[str]) -> GoogleCredentials:
           """Start OAuth flow, open browser, wait for callback."""
           code_verifier, code_challenge = generate_pkce_pair()

           # Start localhost server
           port = find_free_port()
           self._server = LocalhostServer(port)

           # Build and open auth URL
           auth_url = build_auth_url(...)
           webbrowser.open(auth_url)

           # Wait for callback
           code = await self._server.wait_for_code()

           # Exchange code for tokens
           return await self.exchange_code(code, code_verifier)
   ```

2. **Create `GoogleOAuthDialog`** in `presentation/canvas/ui/dialogs/`:
   - Select scopes (checkboxes for each service)
   - "Connect" button triggers flow
   - Display connected account info
   - "Disconnect" to revoke tokens

### Phase 2: Enhanced Credential System

1. **Add `GOOGLE_OAUTH` credential type** to `CredentialStore`:
   ```python
   class CredentialType(Enum):
       # ... existing types ...
       GOOGLE_OAUTH = "google_oauth"
   ```

2. **Create Google-specific credential fields**:
   ```python
   GOOGLE_CREDENTIAL_FIELDS = {
       'access_token': str,
       'refresh_token': str,
       'token_uri': str,
       'client_id': str,
       'client_secret': str,
       'scopes': list[str],
       'expiry': float,
       'account_email': str,  # For display
   }
   ```

3. **Add scope-based filtering** to credential dropdown

### Phase 3: Cascading Dropdown Infrastructure

1. **Add `DynamicPropertyLoader`** protocol to node system
2. **Implement `GoogleResourceLoader`** for API calls
3. **Create `CascadingDropdown` widget** with loading states
4. **Add caching layer** for API responses

### Phase 4: Complete Node Implementation

Implement nodes following n8n operations list:

**Gmail Nodes:**
- GmailSendNode
- GmailReadNode
- GmailSearchNode
- GmailLabelNode
- GmailDraftNode

**Sheets Nodes:**
- SheetsReadNode
- SheetsAppendNode
- SheetsUpdateNode
- SheetsClearNode
- SheetsCreateNode

**Drive Nodes:**
- DriveUploadNode
- DriveDownloadNode
- DriveSearchNode
- DriveCreateFolderNode
- DriveShareNode

**Calendar Nodes:**
- CalendarCreateEventNode
- CalendarUpdateEventNode
- CalendarDeleteEventNode
- CalendarListEventsNode
- CalendarCheckAvailabilityNode

**Docs Nodes:**
- DocsCreateNode
- DocsReadNode
- DocsUpdateNode (basic text operations)

---

## 7. Unresolved Questions

1. **Service Account UI**: Should we provide a separate UI for service account setup, or combine with OAuth in one dialog?

2. **Scope Management**: Should users select individual scopes, or use preset "profiles" (e.g., "Gmail - Read Only", "Full Workspace Access")?

3. **Token Persistence**: Store tokens per-project or globally? n8n uses global credentials shared across workflows.

4. **Error Recovery**: How to handle token revocation mid-workflow? Pause and prompt for re-auth?

5. **Workspace Admin**: Should we detect Workspace vs personal accounts and adjust UI messaging?

---

## Sources

- [Google OAuth2 Generic | n8n Docs](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic/)
- [Google OAuth2 Single Service | n8n Docs](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service/)
- [OAuth 2.0 for Native Apps | Google for Developers](https://developers.google.com/identity/protocols/oauth2/native-app)
- [OAuth 2.0 Best Practices | Google for Developers](https://developers.google.com/identity/protocols/oauth2/resources/best-practices)
- [OAuth 2.0 Scopes for Google APIs | Google for Developers](https://developers.google.com/identity/protocols/oauth2/scopes)
- [Google Sheets Usage Limits | Google for Developers](https://developers.google.com/workspace/sheets/api/limits)
- [Gmail API Quota Reference | Google for Developers](https://developers.google.com/workspace/gmail/api/reference/quota)
- [RFC 8252 - OAuth 2.0 for Native Apps](https://tools.ietf.org/html/rfc8252)
- [n8n Google Sheets Node | n8n Docs](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/)
- [n8n Gmail Node | n8n Docs](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.gmail/)
- [n8n Google Drive Node | n8n Docs](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googledrive/)
- [n8n Google Calendar Node | n8n Docs](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecalendar/)
- [Google API Batch Requests | google-api-python-client](https://googleapis.github.io/google-api-python-client/docs/batch.html)
- [n8n Programmatic-style Parameters | n8n Docs](https://docs.n8n.io/integrations/creating-nodes/build/reference/node-base-files/programmatic-style-parameters/)

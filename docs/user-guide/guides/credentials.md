# Credential Management Guide

CasareRPA provides a secure credential management system for storing and using sensitive information like API keys, passwords, and OAuth tokens. This guide explains how to manage credentials safely.

## Table of Contents

- [Overview](#overview)
- [Adding Credentials](#adding-credentials)
- [Credential Types](#credential-types)
- [Using Credentials in Nodes](#using-credentials-in-nodes)
- [Credential Security](#credential-security)
- [Updating Credentials](#updating-credentials)

---

## Overview

The Credentials Panel provides secure storage for sensitive data used in your workflows. Key principles:

- **Values are never displayed** - Only credential names and metadata are visible
- **Encrypted storage** - Credentials are encrypted at rest
- **Centralized management** - One location for all credentials
- **Reference by alias** - Workflows reference credentials by name, not value

### Accessing the Credentials Panel

1. Open CasareRPA
2. Go to **View > Panels > Credentials**
3. Or use the keyboard shortcut configured in preferences

---

## Adding Credentials

### Using the Credentials Panel

1. Open the **Credentials Panel**
2. Click the **+** button in the header
3. Select the credential type
4. Fill in the required fields
5. Click **Save**

### Using the Credential Manager Dialog

1. Go to **Tools > Credential Manager**
2. Navigate to the appropriate tab (API Keys, Logins, Google, etc.)
3. Click **Add New**
4. Enter credential details
5. Click **Save**

### Required Information

When adding a credential, you'll need to provide:

| Field | Description |
|-------|-------------|
| **Name** | Unique identifier for the credential (e.g., "OpenAI API Key") |
| **Type** | Category of credential (see below) |
| **Value(s)** | The actual secret data (hidden after entry) |
| **Description** | Optional notes about the credential's purpose |

---

## Credential Types

CasareRPA supports several credential types for different use cases:

### API Key

For authenticating with external APIs.

| Field | Description |
|-------|-------------|
| Name | Credential identifier |
| API Key | The secret key value |
| Provider | Optional: Service provider (openai, anthropic, etc.) |

**Common uses:**
- OpenAI API access
- Anthropic Claude access
- Google AI access
- Custom API integrations

### Username/Password

For login credentials.

| Field | Description |
|-------|-------------|
| Name | Credential identifier |
| Username | Login username or email |
| Password | Login password |

**Common uses:**
- Website logins
- SMTP/IMAP email
- Database connections
- FTP/SFTP access

### Google OAuth

For Google Workspace integration.

| Field | Description |
|-------|-------------|
| Name | Credential identifier |
| Client ID | Google OAuth client ID |
| Client Secret | Google OAuth client secret |
| Refresh Token | OAuth refresh token |
| Scopes | Authorized API scopes |

**Common uses:**
- Google Sheets access
- Google Drive operations
- Gmail automation
- Google Calendar integration

### OAuth Token

For generic OAuth 2.0 authentication.

| Field | Description |
|-------|-------------|
| Name | Credential identifier |
| Access Token | Current access token |
| Refresh Token | Token for refreshing access |
| Token Expiry | When the token expires |

### Connection String

For database connections.

| Field | Description |
|-------|-------------|
| Name | Credential identifier |
| Connection String | Full connection string with embedded credentials |

**Common uses:**
- PostgreSQL connections
- MySQL connections
- SQL Server access
- MongoDB connections

### Bot Token

For messaging platform bots.

| Field | Description |
|-------|-------------|
| Name | Credential identifier |
| Bot Token | The bot authentication token |
| Platform | telegram, whatsapp, slack, etc. |

---

## Using Credentials in Nodes

### The credential_name Property

Most nodes that need authentication have a `credential_name` property:

```python
# Node configuration:
credential_name: "my_api_key"
```

### Resolution Order

When a node needs a credential, it looks in multiple places:

1. **Vault (credential_name)** - Primary source via Credential Store
2. **Direct Parameter** - Fallback if credential not found
3. **Context Variable** - Check execution context
4. **Environment Variable** - Last resort fallback

### Example: HTTP Request with API Key

```python
# HTTP Request Node configuration:
url: "https://api.example.com/data"
method: "GET"
credential_name: "example_api_key"  # References stored credential

# The node will automatically add the API key to headers
```

### Example: Email Node with Login

```python
# Send Email Node configuration:
credential_name: "gmail_login"      # References username/password credential
smtp_server: "smtp.gmail.com"
smtp_port: 587
```

### Credential Resolution in Code

For advanced users, credentials are resolved using the `CredentialAwareMixin`:

```python
# Inside a node execute method:
api_key = await self.resolve_credential(
    context,
    credential_name_param="credential_name",
    credential_field="api_key",
    env_var="MY_API_KEY",  # Fallback environment variable
    required=True
)
```

---

## Credential Security

### Encryption at Rest

All credentials are encrypted before storage using industry-standard encryption:

- AES-256 encryption for credential values
- Secure key derivation
- Salt-based protection

### In-Memory Protection

During runtime:

- Credentials are decrypted only when needed
- Values are cleared from memory after use
- No logging of credential values

### Access Control

- Credentials are scoped per user/project
- Role-based access control (RBAC) supported
- Audit logging of credential access

### Best Practices

1. **Use Descriptive Names**
   ```
   Good: "production_openai_api_key"
   Bad: "key1"
   ```

2. **One Credential Per Purpose**
   ```
   Good: Separate credentials for dev/staging/production
   Bad: Sharing credentials across environments
   ```

3. **Regular Rotation**
   - Rotate API keys periodically
   - Update passwords on schedule
   - Refresh OAuth tokens before expiry

4. **Least Privilege**
   - Grant minimal required permissions
   - Use scoped API keys when available
   - Limit OAuth scopes to what's needed

5. **Never Commit Credentials**
   - Credentials are stored separately from workflow files
   - Never hardcode values in nodes
   - Use environment variables for CI/CD

### Security Warnings

> **Warning:** Never share workflow files that contain hardcoded credentials. Always use the credential reference system.

> **Warning:** If you suspect a credential has been compromised, rotate it immediately in both CasareRPA and the external service.

---

## Updating Credentials

### Editing Existing Credentials

1. Open the **Credentials Panel**
2. Select the credential to edit
3. Click **Edit** or double-click the entry
4. Confirm the security prompt
5. Update the credential values
6. Click **Save**

### Testing Credentials

Before using a credential in production:

1. Select the credential in the panel
2. Click **Test**
3. Review the test results:
   - **API Keys**: Validates against the provider
   - **OAuth**: Checks token validity
   - **Username/Password**: Service-specific testing

### Deleting Credentials

> **Important:** Deleting a credential will cause workflows using it to fail.

1. Select the credential in the panel
2. Click **Delete**
3. Confirm the deletion warning
4. Update any workflows that referenced the deleted credential

### Credential Expiration

Some credentials expire and need refresh:

| Type | Expiration | Action |
|------|------------|--------|
| OAuth Token | Hours-days | Auto-refresh if refresh token valid |
| API Key | Never/Manual | Rotate periodically |
| Password | Per policy | Update when changed externally |

### Refreshing OAuth Tokens

For Google OAuth credentials:

1. Select the Google credential
2. Click **Refresh Token**
3. Complete the re-authorization flow if needed
4. Token is updated automatically

---

## Provider-Specific Configuration

### OpenAI

```python
# Credential type: API Key
# Provider: openai
# Field: api_key

# Usage in nodes:
credential_name: "openai_key"
```

### Google Workspace

```python
# Credential type: Google OAuth
# Required scopes depend on usage:
# - sheets: https://www.googleapis.com/auth/spreadsheets
# - drive: https://www.googleapis.com/auth/drive
# - gmail: https://www.googleapis.com/auth/gmail.send

# Usage in nodes:
credential_name: "google_workspace"
```

### Telegram Bot

```python
# Credential type: Bot Token
# Provider: telegram
# Field: bot_token

# Usage in nodes:
credential_name: "my_telegram_bot"
```

### Database

```python
# Credential type: Username/Password
# Fields: username, password

# Or: Connection String
# Field: connection_string (includes all auth info)

# Usage in nodes:
credential_name: "production_database"
```

---

## Troubleshooting

### Credential Not Found

**Error:** `Required credential 'xyz' not found`

**Solutions:**
1. Verify the credential name matches exactly
2. Check that the credential exists in the panel
3. Ensure you have access to the credential

### Authentication Failed

**Error:** `Authentication failed with credential 'xyz'`

**Solutions:**
1. Test the credential using the Test button
2. Verify the credential hasn't expired
3. Check if the external service has changed requirements
4. Try refreshing OAuth tokens

### Permission Denied

**Error:** `Access denied for credential 'xyz'`

**Solutions:**
1. Check your role/permissions
2. Contact administrator for access
3. Verify the credential belongs to your project

---

## Related Guides

- [AI Assistant Guide](./ai-assistant.md) - Configure AI provider credentials
- [Best Practices](./best-practices.md) - Security best practices
- [Error Handling](./error-handling.md) - Handle authentication errors

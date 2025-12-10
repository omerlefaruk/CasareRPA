"""
CasareRPA - Credential Property Definitions
Static definitions for credential types.
"""

from casare_rpa.domain.schemas import PropertyDef, PropertyType

# Generic credential name (for vault lookup)
CREDENTIAL_NAME_PROP = PropertyDef(
    "credential_name",
    PropertyType.STRING,
    default="",
    label="Credential Name",
    placeholder="my_credential",
    tooltip="Name of stored credential in vault",
    tab="connection",
)

# API Key
API_KEY_PROP = PropertyDef(
    "api_key",
    PropertyType.STRING,
    default="",
    label="API Key",
    placeholder="sk-...",
    tooltip="API key (or use Credential Name)",
    tab="connection",
)

# OAuth
OAUTH_TOKEN_PROP = PropertyDef(
    "oauth_token",
    PropertyType.STRING,
    default="",
    label="OAuth Token",
    placeholder="ya29.a0...",
    tooltip="OAuth access token",
    tab="connection",
)

# Username/Password
USERNAME_PROP = PropertyDef(
    "username",
    PropertyType.STRING,
    default="",
    label="Username",
    tooltip="Username",
    tab="connection",
)

PASSWORD_PROP = PropertyDef(
    "password",
    PropertyType.STRING,
    default="",
    label="Password",
    tooltip="Password",
    tab="connection",
)

# Database
CONNECTION_STRING_PROP = PropertyDef(
    "connection_string",
    PropertyType.STRING,
    default="",
    label="Connection String",
    placeholder="postgresql://user:pass@host:5432/db",
    tooltip="Database connection string",
    tab="connection",
)

# Bot Token
BOT_TOKEN_PROP = PropertyDef(
    "bot_token",
    PropertyType.STRING,
    default="",
    label="Bot Token",
    tooltip="Bot/API token",
    tab="connection",
)

# OAuth Client
CLIENT_ID_PROP = PropertyDef(
    "client_id",
    PropertyType.STRING,
    default="",
    label="Client ID",
    tooltip="OAuth Client ID",
    tab="connection",
)

CLIENT_SECRET_PROP = PropertyDef(
    "client_secret",
    PropertyType.STRING,
    default="",
    label="Client Secret",
    tooltip="OAuth Client Secret",
    tab="connection",
)

# Bearer
BEARER_TOKEN_PROP = PropertyDef(
    "bearer_token",
    PropertyType.STRING,
    default="",
    label="Bearer Token",
    tooltip="Bearer authentication token",
    tab="connection",
)

# Email - SMTP
SMTP_SERVER_PROP = PropertyDef(
    "smtp_server",
    PropertyType.STRING,
    default="smtp.gmail.com",
    label="SMTP Server",
    tooltip="SMTP server hostname",
    tab="connection",
)

SMTP_PORT_PROP = PropertyDef(
    "smtp_port",
    PropertyType.INTEGER,
    default=587,
    label="SMTP Port",
    tooltip="SMTP server port (587=TLS, 465=SSL)",
    tab="connection",
)

# Email - IMAP
IMAP_SERVER_PROP = PropertyDef(
    "imap_server",
    PropertyType.STRING,
    default="imap.gmail.com",
    label="IMAP Server",
    tooltip="IMAP server hostname",
    tab="connection",
)

IMAP_PORT_PROP = PropertyDef(
    "imap_port",
    PropertyType.INTEGER,
    default=993,
    label="IMAP Port",
    tooltip="IMAP server port (993=SSL)",
    tab="connection",
)

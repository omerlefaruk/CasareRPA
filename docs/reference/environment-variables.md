# Environment Variables Reference

Complete reference for all environment variables used to configure CasareRPA components.

---

## Overview

CasareRPA uses environment variables for configuration with the `CASARE_` prefix. Variables can be set in:

1. Shell environment
2. `.env` file in working directory
3. Configuration file (`config/settings.yaml`)

---

## General Configuration

### Application Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_ENV` | Environment name (`development`, `staging`, `production`) | `development` |
| `CASARE_LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `CASARE_CONFIG_PATH` | Path to configuration directory | `~/.casare-rpa/config` |
| `CASARE_DATA_PATH` | Path to data directory | `~/.casare-rpa/data` |

### URLs and Endpoints

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_API_URL` | Public API URL (for webhooks, etc.) | Auto-detect |
| `CASARE_WEBHOOK_URL` | Public webhook URL | Auto-detect |
| `CASARE_ROBOT_WS_URL` | WebSocket URL for robots | Auto-detect |

---

## Database Configuration

### Connection

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Full PostgreSQL connection URL | None |
| `POSTGRES_URL` | Alias for DATABASE_URL | None |
| `DB_PASSWORD` | Database password (for Supabase) | None |

### Pool Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_POOL_SIZE` | Connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `10` |

### URL Format

```bash
# Standard PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/database

# With SSL
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require

# Supabase Pooler
DATABASE_URL=postgresql://postgres.project:password@aws-0-region.pooler.supabase.com:6543/postgres
```

---

## Orchestrator Configuration

### Server Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ORCHESTRATOR_HOST` | Bind host address | `127.0.0.1` |
| `ORCHESTRATOR_PORT` | HTTP port | `8000` |
| `ORCHESTRATOR_WORKERS` | Number of worker processes | `1` |
| `ORCHESTRATOR_SECRET_KEY` | JWT signing key | Auto-generated |

### Rate Limiting

| Variable | Description | Default |
|----------|-------------|---------|
| `ORCHESTRATOR_RATE_LIMIT` | Requests per minute | `100` |
| `ORCHESTRATOR_BURST_LIMIT` | Burst request limit | `20` |

### Example Configuration

```bash
# Production orchestrator
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8000
ORCHESTRATOR_WORKERS=4
DATABASE_URL=postgresql://user:pass@db.example.com:5432/casare
```

---

## Robot Agent Configuration

### Identity

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_ROBOT_ID` | Unique robot identifier | Auto-generated UUID |
| `CASARE_ROBOT_NAME` | Display name | Hostname |
| `CASARE_ROBOT_TAGS` | Comma-separated capability tags | None |
| `CASARE_ENVIRONMENT` | Environment name | `default` |
| `CASARE_CAPABILITIES` | Robot capabilities | Auto-detect |

### Connection

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_CONTROL_PLANE_URL` | Orchestrator WebSocket URL | None |
| `ROBOT_API_KEY` | API key for orchestrator auth | None |

### Performance

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_MAX_CONCURRENT_JOBS` | Maximum parallel jobs | `1` |
| `CASARE_POLL_INTERVAL` | Job poll interval (seconds) | `1.0` |
| `CASARE_BATCH_SIZE` | Jobs per poll | `1` |
| `CASARE_JOB_TIMEOUT` | Job timeout (seconds) | `3600` |
| `CASARE_NODE_TIMEOUT` | Node timeout (seconds) | `120.0` |

### Heartbeat and Presence

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_HEARTBEAT_INTERVAL` | Heartbeat interval (seconds) | `10.0` |
| `CASARE_PRESENCE_INTERVAL` | Presence update interval (seconds) | `5.0` |
| `CASARE_SUBSCRIBE_TIMEOUT` | Subscribe timeout (seconds) | `5.0` |
| `CASARE_VISIBILITY_TIMEOUT` | Job visibility timeout (seconds) | `30` |
| `CASARE_SHUTDOWN_GRACE` | Graceful shutdown time (seconds) | `60` |

### Features

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_ENABLE_CHECKPOINTING` | Enable crash recovery | `true` |
| `CASARE_ENABLE_REALTIME` | Enable WebSocket updates | `true` |
| `CASARE_ENABLE_CIRCUIT_BREAKER` | Enable failure protection | `true` |

### Resource Pools

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_BROWSER_POOL_SIZE` | Browser instance pool | `5` |
| `CASARE_DB_POOL_SIZE` | Database connection pool | `10` |
| `CASARE_HTTP_POOL_SIZE` | HTTP session pool | `20` |

### Example Robot Configuration

```bash
# Production robot
CASARE_ROBOT_NAME=production-robot-01
CASARE_ROBOT_TAGS=browser-capable,desktop-capable
CASARE_ENVIRONMENT=production
CASARE_MAX_CONCURRENT_JOBS=3
CASARE_ENABLE_CHECKPOINTING=true
DATABASE_URL=postgresql://user:pass@db.example.com:5432/casare
```

---

## Security Configuration

### Vault Integration

| Variable | Description | Default |
|----------|-------------|---------|
| `VAULT_ADDR` | HashiCorp Vault server URL | `http://localhost:8200` |
| `VAULT_TOKEN` | Vault authentication token | None |
| `VAULT_ROLE_ID` | AppRole role ID | None |
| `VAULT_SECRET_ID` | AppRole secret ID | None |
| `VAULT_NAMESPACE` | Vault namespace | None |
| `VAULT_AUTH_METHOD` | Authentication method | `approle` |
| `VAULT_CACERT` | Path to CA certificate | None |
| `VAULT_SKIP_VERIFY` | Skip SSL verification | `false` |

### Example Vault Configuration

```bash
# Token authentication
VAULT_ADDR=https://vault.example.com:8200
VAULT_TOKEN=hvs.xxxxxxxxxxxxx

# AppRole authentication
VAULT_ADDR=https://vault.example.com:8200
VAULT_ROLE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
VAULT_SECRET_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### SSL/TLS

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_CA_CERT_PATH` | Path to CA certificate | None |
| `CASARE_CLIENT_CERT_PATH` | Path to client certificate | None |
| `CASARE_CLIENT_KEY_PATH` | Path to client key | None |

---

## Browser Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PLAYWRIGHT_BROWSERS_PATH` | Browser installation path | System default |
| `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` | Skip browser download | `false` |
| `BROWSER_HEADLESS` | Run browsers headless | `true` |
| `BROWSER_DEFAULT_TIMEOUT` | Default timeout (ms) | `30000` |

---

## Logging Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_LOG_LEVEL` | Log level | `INFO` |
| `CASARE_LOG_FORMAT` | Log format (`json`, `text`) | `json` |
| `CASARE_LOG_PATH` | Log file directory | `~/.casare-rpa/logs` |
| `CASARE_LOG_ROTATION` | Log rotation (`daily`, `size`) | `daily` |
| `CASARE_LOG_RETENTION` | Log retention (days) | `30` |

---

## Messaging Integration

### Telegram

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | None |
| `TELEGRAM_WEBHOOK_URL` | Webhook URL for bot | Auto-detect |

### WhatsApp

| Variable | Description | Default |
|----------|-------------|---------|
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID | None |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Cloud API token | None |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification token | None |

### Email

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server host | None |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | None |
| `SMTP_PASSWORD` | SMTP password | None |
| `SMTP_USE_TLS` | Use TLS | `true` |

---

## Update Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_UPDATE_REPO_URL` | Update repository URL | Official repo |
| `CASARE_UPDATE_CHECK_INTERVAL` | Check interval (hours) | `4` |
| `CASARE_AUTO_UPDATE` | Enable auto-updates | `false` |

---

## Development Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_DEBUG` | Enable debug mode | `false` |
| `CASARE_DEV_MODE` | Development mode | `false` |
| `CASARE_PROFILE` | Enable profiling | `false` |
| `CASARE_TRACE` | Enable tracing | `false` |

---

## Environment Files

### Search Order

CasareRPA searches for `.env` files in:

1. Current working directory
2. Project root
3. `config/` directory
4. Home directory (`~/.casare-rpa/`)

### File Format

```bash
# .env file
# Comments start with #

CASARE_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/db

# Multi-line values use quotes
CASARE_DESCRIPTION="This is a
multi-line value"

# Reference other variables
CASARE_LOG_PATH=${HOME}/.casare-rpa/logs
```

### Environment-Specific Files

```bash
config/
  .env                  # Base configuration
  .env.development      # Development overrides
  .env.staging          # Staging overrides
  .env.production       # Production overrides
```

Load specific environment:

```bash
CASARE_ENV=production casare-rpa robot start
```

---

## Configuration Priority

Variables are loaded in order (later overrides earlier):

1. Default values (in code)
2. Configuration file (`config/settings.yaml`)
3. Environment-specific `.env` file
4. Base `.env` file
5. Shell environment variables

---

## Validation

Check configuration:

```bash
# Validate configuration
casare-rpa config validate

# Show loaded configuration (redacted)
casare-rpa config show

# Show specific setting
casare-rpa config get DATABASE_URL
```

---

## Security Best Practices

### Never Commit Secrets

```bash
# .gitignore
.env
.env.local
.env.*.local
config/secrets.yaml
```

### Use Secret Managers

```bash
# Use Vault for production
VAULT_ADDR=https://vault.example.com
VAULT_ROLE_ID=...
VAULT_SECRET_ID=...

# Reference secrets
DATABASE_URL=vault://secret/data/casare/database#url
```

### Rotate Credentials

```bash
# Generate new API key
casare-rpa orchestrator rotate-api-key ROBOT_001

# Update robot with new key
ROBOT_API_KEY=new_key_here
```

---

## Related Documentation

- [Robot Setup](../user-guide/deployment/robot-setup.md) - Robot configuration
- [Orchestrator Setup](../user-guide/deployment/orchestrator-setup.md) - Server configuration
- [Security Best Practices](../security/best-practices.md) - Secure configuration
- [Credentials Management](../security/credentials.md) - Vault integration

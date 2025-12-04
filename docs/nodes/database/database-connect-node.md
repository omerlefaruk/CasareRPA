# DatabaseConnectNode

Establish a database connection.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.database.sql_nodes`
**File:** `src\casare_rpa\nodes\database\sql_nodes.py:272`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `db_type` | INPUT | No | DataType.STRING |
| `host` | INPUT | No | DataType.STRING |
| `port` | INPUT | No | DataType.INTEGER |
| `database` | INPUT | No | DataType.STRING |
| `username` | INPUT | No | DataType.STRING |
| `password` | INPUT | No | DataType.STRING |
| `connection_string` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `connection` | OUTPUT | DataType.ANY |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `timeout` | FLOAT | `30.0` | No | Connection timeout in seconds (min: 0.1) |
| `ssl` | BOOLEAN | `False` | No | Use SSL for connection (PostgreSQL/MySQL) |
| `ssl_ca` | STRING | `` | No | Path to CA certificate for SSL |
| `pool_size` | INTEGER | `5` | No | Connection pool size (PostgreSQL/MySQL) (min: 1) |
| `auto_commit` | BOOLEAN | `True` | No | Enable auto-commit mode |
| `charset` | STRING | `utf8mb4` | No | Character set (MySQL) |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts on connection failure (min: 0) |
| `retry_interval` | INTEGER | `2000` | No | Delay between retry attempts in milliseconds (min: 0) |

### Connection Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `username` | STRING | `` | No | Database username (PostgreSQL/MySQL) |
| `password` | STRING | `` | No | Database password (PostgreSQL/MySQL) |
| `connection_string` | STRING | `` | No | Full connection string (overrides individual parameters) |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `db_type` | CHOICE | `sqlite` | No | Type of database to connect to Choices: sqlite, postgresql, mysql |
| `host` | STRING | `localhost` | No | Database server host (PostgreSQL/MySQL) |
| `port` | INTEGER | `5432` | No | Database server port |
| `database` | STRING | `` | No | Database name or SQLite file path |

## Inheritance

Extends: `CredentialAwareMixin`, `BaseNode`

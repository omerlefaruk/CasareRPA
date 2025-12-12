# Database Nodes

Database nodes provide connectivity and operations for SQLite, PostgreSQL, and MySQL/MariaDB databases. All nodes support parameterized queries, connection pooling, and transaction management.

## Overview

| Node | Purpose |
|------|---------|
| DatabaseConnectNode | Establish database connection |
| ExecuteQueryNode | Execute SELECT queries |
| ExecuteNonQueryNode | Execute INSERT/UPDATE/DELETE |
| BeginTransactionNode | Start database transaction |
| CommitTransactionNode | Commit transaction |
| RollbackTransactionNode | Rollback transaction |
| CloseDatabaseNode | Close database connection |
| ExecuteBatchNode | Execute multiple statements |

## Supported Databases

| Database | Driver | Installation |
|----------|--------|--------------|
| SQLite | Built-in (aiosqlite optional) | `pip install aiosqlite` |
| PostgreSQL | asyncpg | `pip install asyncpg` |
| MySQL/MariaDB | aiomysql | `pip install aiomysql` |

---

## DatabaseConnectNode

Establish a connection to a database. Supports both individual connections and connection pools.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| credential_name | STRING | "" | Vault credential alias |
| db_type | CHOICE | "sqlite" | Database type (sqlite/postgresql/mysql) |
| host | STRING | "localhost" | Database server host |
| port | INTEGER | 5432 | Database server port |
| database | STRING | "" | Database name or SQLite file path |
| username | STRING | "" | Database username |
| password | STRING | "" | Database password |
| connection_string | STRING | "" | Full connection string (overrides other params) |
| timeout | FLOAT | 30.0 | Connection timeout in seconds |
| ssl | BOOLEAN | false | Use SSL encryption |
| ssl_ca | STRING | "" | Path to SSL CA certificate |
| pool_size | INTEGER | 5 | Connection pool size |
| auto_commit | BOOLEAN | true | Enable auto-commit mode |
| charset | STRING | "utf8mb4" | Character set (MySQL) |
| retry_count | INTEGER | 0 | Retry attempts on failure |
| retry_interval | INTEGER | 2000 | Retry delay in milliseconds |

### Ports

**Inputs:**
- `db_type` (STRING)
- `host` (STRING)
- `port` (INTEGER)
- `database` (STRING)
- `username` (STRING)
- `password` (STRING)
- `connection_string` (STRING)

**Outputs:**
- `connection` (ANY) - DatabaseConnection object
- `success` (BOOLEAN)
- `error` (STRING)

### Credential Resolution

Credentials are resolved in this order:
1. Vault lookup via `credential_name`
2. Direct parameters (`username`, `password`, `connection_string`)
3. Environment variables (`DB_USERNAME`, `DB_PASSWORD`, `DATABASE_URL`)

### Connection String Examples

**SQLite:**
```python
{
    "db_type": "sqlite",
    "database": "C:\\data\\myapp.db"  # File path
}
# Or for in-memory:
{
    "db_type": "sqlite",
    "database": ":memory:"
}
```

**PostgreSQL:**
```python
{
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "myapp",
    "username": "postgres",
    "password": "secret"
}
# Or connection string:
{
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@host:5432/database"
}
```

**MySQL:**
```python
{
    "db_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "myapp",
    "username": "root",
    "password": "secret"
}
```

### Example: Connect with Vault Credentials

```python
from casare_rpa.nodes.database import DatabaseConnectNode

node = DatabaseConnectNode(
    node_id="db_connect",
    config={
        "db_type": "postgresql",
        "credential_name": "production_db",  # Vault lookup
        "host": "db.example.com",
        "port": 5432,
        "database": "production",
        "pool_size": 10,
        "ssl": True,
    }
)
```

---

## ExecuteQueryNode

Execute SELECT queries and retrieve results as a list of dictionaries.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| query | STRING | "" | SQL SELECT query |
| parameters | LIST | [] | Parameterized query values |
| retry_count | INTEGER | 0 | Retry attempts |
| retry_interval | INTEGER | 1000 | Retry delay (ms) |

### Ports

**Inputs:**
- `connection` (ANY) - DatabaseConnection from ConnectNode
- `query` (STRING)
- `parameters` (LIST) - Optional

**Outputs:**
- `results` (LIST) - List of row dictionaries
- `row_count` (INTEGER)
- `columns` (LIST) - Column names
- `success` (BOOLEAN)
- `error` (STRING)

### Parameterized Queries

Always use parameterized queries to prevent SQL injection:

```python
# SQLite / MySQL - Use ? placeholders
query = "SELECT * FROM users WHERE id = ? AND status = ?"
parameters = [123, "active"]

# PostgreSQL - Use $1, $2 placeholders
query = "SELECT * FROM users WHERE id = $1 AND status = $2"
parameters = [123, "active"]
```

### Example: Simple Query

```python
from casare_rpa.nodes.database import ExecuteQueryNode

node = ExecuteQueryNode(
    node_id="query_users",
    config={
        "query": "SELECT id, name, email FROM users WHERE active = ?",
        "parameters": [True],
    }
)

# Result: [{"id": 1, "name": "John", "email": "john@example.com"}, ...]
```

### Example: Dynamic Query with Variables

```python
node = ExecuteQueryNode(
    node_id="dynamic_query",
    config={
        "query": "SELECT * FROM orders WHERE customer_id = $1 AND date >= $2",
        "parameters": ["{{variables.customer_id}}", "{{variables.start_date}}"],
    }
)
```

> **Warning:** CasareRPA detects potential SQL injection when variables are resolved. Always prefer parameterized queries over string interpolation in the query itself.

---

## ExecuteNonQueryNode

Execute INSERT, UPDATE, DELETE, or DDL statements.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| query | STRING | "" | SQL statement |
| parameters | LIST | [] | Parameterized values |
| retry_count | INTEGER | 0 | Retry attempts |
| retry_interval | INTEGER | 1000 | Retry delay (ms) |

### Ports

**Inputs:**
- `connection` (ANY)
- `query` (STRING)
- `parameters` (LIST)

**Outputs:**
- `rows_affected` (INTEGER)
- `last_insert_id` (INTEGER) - For INSERT statements
- `success` (BOOLEAN)
- `error` (STRING)

### Example: Insert Row

```python
from casare_rpa.nodes.database import ExecuteNonQueryNode

node = ExecuteNonQueryNode(
    node_id="insert_user",
    config={
        "query": "INSERT INTO users (name, email, created_at) VALUES (?, ?, ?)",
        "parameters": ["{{variables.name}}", "{{variables.email}}", "{{now}}"],
    }
)
# Output: rows_affected=1, last_insert_id=42
```

### Example: Update Rows

```python
node = ExecuteNonQueryNode(
    node_id="update_status",
    config={
        "query": "UPDATE orders SET status = ? WHERE id = ?",
        "parameters": ["shipped", "{{variables.order_id}}"],
    }
)
```

### Example: Delete Rows

```python
node = ExecuteNonQueryNode(
    node_id="delete_old",
    config={
        "query": "DELETE FROM logs WHERE created_at < ?",
        "parameters": ["{{variables.cutoff_date}}"],
    }
)
```

---

## Transaction Nodes

Use transaction nodes for atomic operations that must succeed or fail together.

### BeginTransactionNode

Start a database transaction. Subsequent queries/statements will not auto-commit until CommitTransactionNode is called.

**Ports:**
- Input: `connection` (ANY)
- Output: `connection` (ANY), `success` (BOOLEAN), `error` (STRING)

### CommitTransactionNode

Commit the current transaction, making all changes permanent.

**Ports:**
- Input: `connection` (ANY)
- Output: `connection` (ANY), `success` (BOOLEAN), `error` (STRING)

### RollbackTransactionNode

Rollback the current transaction, undoing all changes since BeginTransaction.

**Ports:**
- Input: `connection` (ANY)
- Output: `connection` (ANY), `success` (BOOLEAN), `error` (STRING)

### Example: Transaction Workflow

```python
# Transaction pattern:
# Begin -> Execute -> Execute -> Commit (or Rollback on error)

workflow = {
    "nodes": [
        {
            "id": "connect",
            "type": "DatabaseConnectNode",
            "config": {
                "db_type": "postgresql",
                "database": "inventory"
            }
        },
        {
            "id": "begin",
            "type": "BeginTransactionNode"
        },
        {
            "id": "debit",
            "type": "ExecuteNonQueryNode",
            "config": {
                "query": "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
                "parameters": [100.00, 1]
            }
        },
        {
            "id": "credit",
            "type": "ExecuteNonQueryNode",
            "config": {
                "query": "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
                "parameters": [100.00, 2]
            }
        },
        {
            "id": "commit",
            "type": "CommitTransactionNode"
        },
        {
            "id": "close",
            "type": "CloseDatabaseNode"
        }
    ],
    "connections": [
        {"from": "connect.connection", "to": "begin.connection"},
        {"from": "begin.connection", "to": "debit.connection"},
        {"from": "debit.connection", "to": "credit.connection"},
        {"from": "credit.connection", "to": "commit.connection"},
        {"from": "commit.connection", "to": "close.connection"}
    ]
}
```

---

## CloseDatabaseNode

Close a database connection or connection pool.

### Ports

**Inputs:**
- `connection` (ANY)

**Outputs:**
- `success` (BOOLEAN)
- `error` (STRING)

> **Important:** Always close connections when finished to release resources. For pooled connections (PostgreSQL/MySQL), this closes the entire pool.

---

## ExecuteBatchNode

Execute multiple SQL statements as a batch operation.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| statements | LIST | [] | List of SQL statements |
| stop_on_error | BOOLEAN | true | Stop on first error |
| retry_count | INTEGER | 0 | Retries per statement |
| retry_interval | INTEGER | 1000 | Retry delay (ms) |

### Ports

**Inputs:**
- `connection` (ANY)
- `statements` (LIST)

**Outputs:**
- `results` (LIST) - Per-statement results
- `total_rows_affected` (INTEGER)
- `success` (BOOLEAN)
- `error` (STRING)

### Example: Schema Migration

```python
from casare_rpa.nodes.database import ExecuteBatchNode

node = ExecuteBatchNode(
    node_id="run_migrations",
    config={
        "statements": [
            "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT)",
            "CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, user_id INT)",
            "CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)",
        ],
        "stop_on_error": True,
    }
)
```

### Example: Bulk Insert

```python
node = ExecuteBatchNode(
    node_id="bulk_insert",
    config={
        "statements": [
            "INSERT INTO products (name, price) VALUES ('Widget', 9.99)",
            "INSERT INTO products (name, price) VALUES ('Gadget', 19.99)",
            "INSERT INTO products (name, price) VALUES ('Gizmo', 29.99)",
        ],
        "stop_on_error": False,  # Continue even if one fails
    }
)
```

---

## Complete Workflow Example

```python
# Database synchronization workflow:
# 1. Connect to source and target databases
# 2. Read from source
# 3. Insert/update in target
# 4. Log results

workflow = {
    "name": "Database Sync",
    "nodes": [
        # Source connection
        {
            "id": "source_connect",
            "type": "DatabaseConnectNode",
            "config": {
                "db_type": "postgresql",
                "credential_name": "source_db",
                "pool_size": 2
            }
        },
        # Target connection
        {
            "id": "target_connect",
            "type": "DatabaseConnectNode",
            "config": {
                "db_type": "mysql",
                "credential_name": "target_db",
                "pool_size": 5
            }
        },
        # Read source data
        {
            "id": "read_source",
            "type": "ExecuteQueryNode",
            "config": {
                "query": "SELECT id, name, email, updated_at FROM users WHERE updated_at > $1",
                "parameters": ["{{variables.last_sync}}"]
            }
        },
        # Loop through results
        {
            "id": "loop_users",
            "type": "ForEachNode"
        },
        # Upsert to target
        {
            "id": "upsert_target",
            "type": "ExecuteNonQueryNode",
            "config": {
                "query": "INSERT INTO users (id, name, email) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE name=?, email=?",
                "parameters": [
                    "{{loop.item.id}}",
                    "{{loop.item.name}}",
                    "{{loop.item.email}}",
                    "{{loop.item.name}}",
                    "{{loop.item.email}}"
                ]
            }
        },
        # Close connections
        {
            "id": "close_source",
            "type": "CloseDatabaseNode"
        },
        {
            "id": "close_target",
            "type": "CloseDatabaseNode"
        }
    ]
}
```

---

## Security Best Practices

### 1. Always Use Parameterized Queries

```python
# GOOD - Parameterized
query = "SELECT * FROM users WHERE id = ?"
parameters = [user_id]

# BAD - String interpolation (SQL injection risk!)
query = f"SELECT * FROM users WHERE id = {user_id}"
```

### 2. Use Vault for Credentials

```python
# GOOD - Vault credential
config = {
    "credential_name": "production_db",
    "database": "myapp"
}

# AVOID - Hardcoded credentials
config = {
    "username": "admin",
    "password": "secret123"  # Never do this!
}
```

### 3. Limit Pool Sizes

```python
# Production recommendation
config = {
    "pool_size": 10,  # Match expected concurrency
    "timeout": 30.0   # Prevent connection hanging
}
```

### 4. Always Close Connections

```python
# Use CloseDatabaseNode at workflow end
# Or use TryCatch with finally path to ensure cleanup
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Wrong host/port | Verify server address |
| Authentication failed | Invalid credentials | Check username/password |
| Database does not exist | Wrong database name | Verify database exists |
| Permission denied | Insufficient privileges | Check user permissions |
| asyncpg not available | Missing driver | `pip install asyncpg` |
| Query timeout | Long-running query | Increase timeout or optimize query |

### Retry Configuration

```python
# Automatic retries for transient failures
config = {
    "retry_count": 3,      # Retry up to 3 times
    "retry_interval": 2000 # Wait 2 seconds between retries
}
```

---

## See Also

- [Control Flow Nodes](control-flow.md) - Loop through query results
- [Error Handling Nodes](error-handling.md) - Try/Catch for transactions
- [Variable Nodes](../variable-nodes.md) - Store query results

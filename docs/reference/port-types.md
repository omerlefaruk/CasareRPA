# Port Types

Node port types and connection rules.

## Port Directions

| Direction | Symbol | Description |
|-----------|--------|-------------|
| Input | ← | Receives data/execution |
| Output | → | Sends data/execution |

## Port Categories

### Execution Ports

| Port | Type | Description |
|------|------|-------------|
| exec_in | EXEC | Execution input |
| exec_out | EXEC | Execution output |

Execution ports control workflow order.

### Data Ports

Data ports pass values between nodes:

- Must match data types (or be compatible)
- Multiple outputs can connect to one input
- One output can connect to multiple inputs

## Connection Rules

### Valid Connections

| From | To | Result |
|------|-----|--------|
| exec_out | exec_in | Execution flow |
| STRING out | STRING in | Direct |
| INTEGER out | FLOAT in | Coerced |
| ANY out | ANY in | Pass-through |

### Invalid Connections

| From | To | Reason |
|------|-----|--------|
| STRING out | INTEGER in | Incompatible |
| exec_out | STRING in | Wrong category |

## Port Colors

| Data Type | Color |
|-----------|-------|
| EXEC | Orange |
| STRING | Green |
| INTEGER | Blue |
| FLOAT | Cyan |
| BOOLEAN | Red |
| ARRAY | Purple |
| OBJECT | Yellow |
| ANY | Gray |

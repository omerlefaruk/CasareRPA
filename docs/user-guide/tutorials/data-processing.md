# Data Processing Tutorial

Learn to build data pipelines: read CSV files, transform data, filter records, and export to different formats.

**Time required:** 20 minutes

**What you will build:**
A workflow that reads sales data from CSV, filters for high-value orders, calculates totals, and exports results to JSON.

## Prerequisites

- CasareRPA installed and running
- Sample CSV file (we'll create one)
- Basic understanding of data formats

## Goals

By the end of this tutorial, you will:
- Read data from CSV files
- Filter and transform data
- Use list operations (map, filter, reduce)
- Calculate aggregates (sum, average, count)
- Export data to JSON format
- Handle data validation

---

## Step 1: Create Sample Data

First, create a sample CSV file for testing.

Create `C:\data\sales.csv` with this content:

```csv
order_id,customer,product,quantity,unit_price,date
1001,Acme Corp,Widget A,10,25.00,2025-01-01
1002,Beta Inc,Widget B,5,50.00,2025-01-02
1003,Acme Corp,Widget A,20,25.00,2025-01-03
1004,Gamma LLC,Widget C,2,100.00,2025-01-04
1005,Beta Inc,Widget A,15,25.00,2025-01-05
1006,Delta Co,Widget B,8,50.00,2025-01-06
1007,Acme Corp,Widget C,3,100.00,2025-01-07
1008,Gamma LLC,Widget A,25,25.00,2025-01-08
1009,Beta Inc,Widget C,1,100.00,2025-01-09
1010,Delta Co,Widget A,30,25.00,2025-01-10
```

---

## Step 2: Create New Workflow

1. Open CasareRPA Canvas
2. **File** > **New Workflow**
3. Save as `data_processing_tutorial.json`

---

## Step 3: Add Start Node

1. Drag **Start** from **Basic** to position (100, 300)

---

## Step 4: Read CSV File

1. Drag **Read CSV** from **File** category
2. Position at (400, 300)
3. Connect: Start -> Read CSV

### Configure Read CSV

| Property | Value |
|----------|-------|
| file_path | `C:\data\sales.csv` |
| has_header | `true` |
| delimiter | `,` |
| encoding | `utf-8` |

### Output Ports

- `data` (LIST) - List of row dictionaries
- `headers` (LIST) - Column names
- `row_count` (INTEGER) - Number of rows

---

## Step 5: Store Data in Variable

1. Drag **Set Variable** from **Variable**
2. Position at (700, 300)
3. Connect: Read CSV `exec_out` -> Set Variable
4. Connect: Read CSV `data` -> Set Variable `value`

| Property | Value |
|----------|-------|
| name | `orders` |

---

## Step 6: Log Data Summary

1. Drag **Log** from **Basic**
2. Position at (1000, 300)

| Property | Value |
|----------|-------|
| message | `Loaded {{row_count}} orders` |
| level | `info` |

Connect `row_count` from Read CSV.

---

## Step 7: Calculate Order Totals

Add a calculated field to each order (total = quantity * unit_price).

### Using ForEach Pattern

1. Drag **For Loop Start** from **Control Flow**
2. Position at (1300, 300)
3. Connect: Log -> For Loop Start
4. Connect: `orders` variable to `items` input

| Property | Value |
|----------|-------|
| mode | `items` |
| item_var | `order` |

### Add Math Operation

1. Drag **Math Operation** from **Data Operations**
2. Position at (1600, 300)
3. Connect: For Loop Start `body` -> Math Operation

| Property | Value |
|----------|-------|
| operation | `multiply` |
| a | `{{order.quantity}}` |
| b | `{{order.unit_price}}` |
| output_var | `line_total` |

### Update Order with Total

1. Drag **Dict Set** from **Data Operations**
2. Position at (1900, 300)

| Property | Value |
|----------|-------|
| key | `total` |

Connect:
- `order` (current item) to `dict` input
- `line_total` to `value` input

### Store Updated Order

1. Drag **List Append** from **Data Operations**
2. Position at (2200, 300)

Connect the updated order dict to the `item` input.
Connect a variable `processed_orders` to the `list` input (initialize this before the loop).

### Complete Loop

1. Drag **For Loop End** from **Control Flow**
2. Position at (2500, 300)

---

## Step 8: Filter High-Value Orders

Filter for orders with total > $200:

1. Drag **List Filter** from **Data Operations**
2. Position after the loop's `completed` output

### Configure List Filter

| Property | Value |
|----------|-------|
| condition | `greater_than` |
| key_path | `total` |

Connect:
- `processed_orders` to `list` input
- Set value `200` for comparison

### Output Ports

- `result` (LIST) - Filtered orders
- `removed` (LIST) - Orders that didn't match
- `count` (INTEGER) - Number of matches

---

## Step 9: Sort by Total (Descending)

1. Drag **List Sort** from **Data Operations**
2. Connect after List Filter

### Configure List Sort

| Property | Value |
|----------|-------|
| key_path | `total` |
| reverse | `true` |

---

## Step 10: Calculate Summary Statistics

### Total Revenue

1. Drag **List Reduce** from **Data Operations**
2. Position at a new row (Y=500)

| Property | Value |
|----------|-------|
| operation | `sum` |
| key_path | `total` |

Connect `processed_orders` to input.
Store result in variable `total_revenue`.

### Order Count

1. Drag **List Reduce** from **Data Operations**

| Property | Value |
|----------|-------|
| operation | `count` |

Store result in variable `order_count`.

### Average Order Value

1. Drag **Math Operation** from **Data Operations**

| Property | Value |
|----------|-------|
| operation | `divide` |
| a | `{{total_revenue}}` |
| b | `{{order_count}}` |
| round_digits | `2` |
| output_var | `average_order` |

---

## Step 11: Group by Customer

Create a summary by customer using a loop:

```
[For Loop Start]
    items: processed_orders
    item_var: order
        |
      body
        |
[Dict Get]
    dict: customer_totals
    key: {{order.customer}}
    default: 0
        |
[Math Operation]
    operation: "add"
    a: {{current_value}}
    b: {{order.total}}
        |
[Dict Set]
    dict: customer_totals
    key: {{order.customer}}
    value: {{sum}}
        |
[For Loop End]
```

---

## Step 12: Build Output Structure

Create the final JSON structure:

1. Drag **Create Dict** from **Data Operations**
2. Add keys for the output structure

### Output Structure

```json
{
    "summary": {
        "total_revenue": 5000.00,
        "order_count": 10,
        "average_order": 500.00,
        "high_value_orders": 5
    },
    "high_value_orders": [...],
    "customer_totals": {...},
    "generated_at": "2025-01-15T10:30:00"
}
```

### Build Summary Dict

```
[Create Dict]
    |
[Dict Set: total_revenue]
    |
[Dict Set: order_count]
    |
[Dict Set: average_order]
    |
[Dict Set: high_value_count]
    |
    +---> summary_dict
```

### Build Final Output

```
[Create Dict]
    |
[Dict Set: summary]
    value: {{summary_dict}}
    |
[Dict Set: high_value_orders]
    value: {{filtered_orders}}
    |
[Dict Set: customer_totals]
    value: {{customer_totals}}
    |
[Dict Set: generated_at]
    value: {{timestamp}}
    |
    +---> output_data
```

---

## Step 13: Write JSON Output

1. Drag **Write JSON** from **File** category
2. Position near the end

### Configure Write JSON

| Property | Value |
|----------|-------|
| file_path | `C:\data\sales_report.json` |
| indent | `2` |
| ensure_ascii | `false` |

Connect `output_data` to the `data` input.

---

## Step 14: Log Completion

1. Drag **Log** from **Basic**

| Property | Value |
|----------|-------|
| message | `Report generated: {{order_count}} orders, ${{total_revenue}} total revenue` |
| level | `info` |

---

## Step 15: Add End Node

1. Drag **End** from **Basic**
2. Connect: Log -> End

---

## Complete Workflow Diagram

```
[Start]
    |
[Read CSV]
    file_path: "C:\data\sales.csv"
    |
[Set Variable: orders]
    |
[Log: "Loaded X orders"]
    |
[Set Variable: processed_orders = []]  # Initialize empty list
    |
[For Loop Start]  # Calculate line totals
    items: orders
    item_var: order
        |
      body
        |
    [Math Operation: quantity * unit_price]
        |
    [Dict Set: total]
        |
    [List Append: to processed_orders]
        |
    [For Loop End]
        |
    completed
        |
[List Filter]  # Filter high value orders
    condition: greater_than
    key_path: total
    value: 200
        |
[List Sort]  # Sort descending
    key_path: total
    reverse: true
        |
[List Reduce: sum]  # Calculate total revenue
    key_path: total
        |
[List Reduce: count]  # Count orders
        |
[Math Operation: divide]  # Calculate average
        |
[Create Dict]  # Build output
        |
[Write JSON]
    file_path: "C:\data\sales_report.json"
        |
[Log: "Report generated"]
        |
[End]
```

---

## Step 16: Run the Workflow

1. Click **Run** (or `F5`)
2. Check the log panel for progress
3. Open `C:\data\sales_report.json` to see results

### Expected Output

```json
{
  "summary": {
    "total_revenue": 2925.00,
    "order_count": 10,
    "average_order": 292.50,
    "high_value_count": 5
  },
  "high_value_orders": [
    {
      "order_id": 1010,
      "customer": "Delta Co",
      "product": "Widget A",
      "quantity": 30,
      "unit_price": 25.00,
      "date": "2025-01-10",
      "total": 750.00
    },
    {
      "order_id": 1008,
      "customer": "Gamma LLC",
      "product": "Widget A",
      "quantity": 25,
      "unit_price": 25.00,
      "date": "2025-01-08",
      "total": 625.00
    }
  ],
  "customer_totals": {
    "Acme Corp": 800.00,
    "Beta Inc": 475.00,
    "Gamma LLC": 825.00,
    "Delta Co": 825.00
  },
  "generated_at": "2025-01-15T10:30:00"
}
```

---

## Alternative: Using List Map

Instead of a ForEach loop, use ListMap for transformations:

### Original Data to Totals List

```
[List Map]
    transform: "get_property"
    key_path: "quantity"
        |
        +---> quantities_list

[List Map]
    transform: "get_property"
    key_path: "unit_price"
        |
        +---> prices_list
```

---

## Data Validation

Add validation before processing:

### Check File Exists

```
[Path Exists]
    path: "C:\data\sales.csv"
        |
[If: exists == false]
    |
  true
    |
[Throw Error]
    message: "Input file not found"
```

### Validate Required Fields

```
[List Filter]
    condition: "is_not_none"
    key_path: "order_id"
        |
    valid_orders

[List Filter]
    condition: "is_none"
    key_path: "order_id"
        |
    invalid_orders

[If: invalid_count > 0]
    |
  true
    |
[Log: "Warning: {{invalid_count}} orders missing order_id"]
```

---

## Working with Different Data Formats

### Reading JSON

```
[Read JSON]
    file_path: "C:\data\input.json"
        |
        +---> data (dict or list)
```

### Reading Excel

```
[Read Excel]
    file_path: "C:\data\sales.xlsx"
    sheet_name: "Orders"
    has_header: true
        |
        +---> data (list of dicts)
```

### Writing CSV

```
[Write CSV]
    file_path: "C:\data\output.csv"
    data: {{processed_orders}}
    include_header: true
    delimiter: ","
```

### Writing Excel

```
[Write Excel]
    file_path: "C:\data\report.xlsx"
    sheet_name: "Summary"
    data: {{output_data}}
```

---

## Common Data Operations

### String Operations

```
[Concatenate]
    string_1: {{first_name}}
    string_2: {{last_name}}
    separator: " "
        |
        +---> full_name

[Format String]
    template: "Order #{order_id} - {customer}"
    variables: {{order}}
        |
        +---> formatted_string
```

### Type Conversions

```
[To Integer]
    value: "123"
        |
        +---> 123 (int)

[To Float]
    value: "45.67"
        |
        +---> 45.67 (float)

[To String]
    value: 100
        |
        +---> "100" (string)
```

### Date Operations

```
[Get Current DateTime]
        |
        +---> now

[Format DateTime]
    datetime: {{now}}
    format: "%Y-%m-%d"
        |
        +---> "2025-01-15"
```

---

## Error Handling for Data Processing

```
[Try]
    |
  try_body
    |
[Read CSV]
    |
[List Filter]  # Might fail on malformed data
    |
[Write JSON]
    |
    +---(error)---> [Catch]
    |                   |
    |              catch_body
    |                   |
    |              [Log: "Data error: {{error_message}}"]
    |                   |
    |              [Write JSON]  # Write error log
    |                   file_path: "C:\data\errors.json"
    |                   |
    +--------+---------+
             |
         [Finally]
             |
        [Log: "Processing complete"]
```

---

## Best Practices

### 1. Validate Input Data

Check for:
- File existence
- Required fields
- Data types
- Value ranges

### 2. Handle Empty Data

```
[If: row_count == 0]
    |
  true
    |
[Log: "No data to process"]
    |
[End]  # Exit early
```

### 3. Use Variables for Paths

```
[Set Variable: input_path]
    value: "C:\data\{{env.DATA_ENV}}\sales.csv"
```

### 4. Log Progress

For large datasets, log progress:

```
[If: {{current_index}} % 100 == 0]
    |
  true
    |
[Log: "Processed {{current_index}} of {{total}}"]
```

### 5. Backup Before Overwriting

```
[Copy File]
    source: "C:\data\output.json"
    destination: "C:\data\output.json.bak"
```

---

## Node Reference

### ReadCSVNode

| Property | Type | Description |
|----------|------|-------------|
| file_path | FILE_PATH | CSV file path |
| has_header | BOOLEAN | First row is header |
| delimiter | STRING | Field separator |
| encoding | STRING | File encoding |

### WriteJSONNode

| Property | Type | Description |
|----------|------|-------------|
| file_path | FILE_PATH | Output file path |
| data | ANY | Data to write |
| indent | INTEGER | JSON indentation |

### ListFilterNode

| Property | Type | Description |
|----------|------|-------------|
| condition | CHOICE | Filter condition |
| key_path | STRING | Nested property path |
| value | ANY | Comparison value |

### ListReduceNode

| Property | Type | Description |
|----------|------|-------------|
| operation | CHOICE | sum/count/avg/min/max |
| key_path | STRING | Property to aggregate |

---

## Next Steps

- [API Integration](api-integration.md) - Send processed data to APIs
- [Email Processing](email-processing.md) - Process email attachments
- [Scheduled Workflows](scheduled-workflows.md) - Automate data pipelines
- [Error Handling](error-handling.md) - Handle data errors gracefully

---

## Summary

You learned how to:
1. Read data from CSV files
2. Transform data with calculated fields
3. Filter records by criteria
4. Calculate aggregates (sum, count, average)
5. Group data by categories
6. Export results to JSON format
7. Handle data validation

Data processing is fundamental to ETL pipelines, report generation, and data integration workflows.

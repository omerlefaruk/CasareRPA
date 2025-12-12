# Data Operation Nodes

Data operation nodes manipulate data: strings, lists, dictionaries, and perform mathematical operations. They are pure data transformations without side effects.

## Overview

| Category | Nodes |
|----------|-------|
| **String** | ConcatenateNode, FormatStringNode, RegexMatchNode, RegexReplaceNode |
| **List** | CreateListNode, ListGetItemNode, ListAppendNode, ListFilterNode, ListSortNode, ListMapNode, ListReduceNode |
| **Dictionary** | CreateDictNode, DictGetNode, DictSetNode, DictMergeNode, DictKeysNode, DictValuesNode |
| **Math** | MathOperationNode, ComparisonNode |
| **Type Conversion** | ToStringNode, ToIntNode, ToFloatNode, ToBoolNode |

---

## String Nodes

### ConcatenateNode

Joins two strings together with an optional separator.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `separator` | STRING | No | `""` | Separator between strings |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `string_1` | STRING | Input | First string |
| `string_2` | STRING | Input | Second string |
| `result` | STRING | Output | Concatenated result |

#### Example

```python
[Concatenate]
    separator: " "

# Inputs: string_1="Hello", string_2="World"
# Output: result="Hello World"
```

---

### FormatStringNode

Formats a string using Python's `.format()` method.

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `template` | STRING | Input | Template with `{key}` placeholders |
| `variables` | DICT | Input | Dictionary of values |
| `result` | STRING | Output | Formatted string |

#### Example

```python
[FormatString]

# Inputs:
#   template="Hello, {name}! You have {count} messages."
#   variables={"name": "Alice", "count": 5}
# Output: result="Hello, Alice! You have 5 messages."
```

---

### RegexMatchNode

Searches for regex patterns in text.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ignore_case` | BOOLEAN | No | `false` | Case-insensitive matching |
| `multiline` | BOOLEAN | No | `false` | `^` and `$` match line boundaries |
| `dotall` | BOOLEAN | No | `false` | `.` matches newlines |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `text` | STRING | Input | Text to search |
| `pattern` | STRING | Input | Regex pattern |
| `match_found` | BOOLEAN | Output | True if pattern found |
| `first_match` | STRING | Output | First match text |
| `all_matches` | LIST | Output | All match texts |
| `groups` | LIST | Output | Capture groups from first match |
| `match_count` | INTEGER | Output | Number of matches |

#### Example

```python
[RegexMatch]
    ignore_case: true

# Inputs:
#   text="Email: alice@example.com, bob@test.org"
#   pattern="\w+@\w+\.\w+"
# Outputs:
#   match_found=true
#   first_match="alice@example.com"
#   all_matches=["alice@example.com", "bob@test.org"]
#   match_count=2
```

---

### RegexReplaceNode

Replaces text matching a regex pattern.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ignore_case` | BOOLEAN | No | `false` | Case-insensitive matching |
| `multiline` | BOOLEAN | No | `false` | `^` and `$` match line boundaries |
| `dotall` | BOOLEAN | No | `false` | `.` matches newlines |
| `max_count` | INTEGER | No | `0` | Max replacements (0=unlimited) |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `text` | STRING | Input | Text to modify |
| `pattern` | STRING | Input | Regex pattern |
| `replacement` | STRING | Input | Replacement text |
| `result` | STRING | Output | Modified text |
| `count` | INTEGER | Output | Number of replacements |

#### Example

```python
[RegexReplace]
    max_count: 0

# Inputs:
#   text="The quick brown fox"
#   pattern="\\b\\w{5}\\b"
#   replacement="*****"
# Output: result="The ***** ***** fox"
#         count=2
```

---

## List Nodes

### CreateListNode

Creates a list from individual items.

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `item_1` | ANY | Input | First item |
| `item_2` | ANY | Input | Second item |
| `item_3` | ANY | Input | Third item |
| `list` | LIST | Output | Created list |

#### Example

```python
[CreateList]

# Inputs: item_1="apple", item_2="banana", item_3="cherry"
# Output: list=["apple", "banana", "cherry"]
```

---

### ListGetItemNode

Gets an item from a list by index.

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `index` | INTEGER | Input | Index (0-based, negative allowed) |
| `item` | ANY | Output | Item at index |

#### Example

```python
[ListGetItem]

# Inputs: list=["a", "b", "c"], index=1
# Output: item="b"

# Negative index:
# Inputs: list=["a", "b", "c"], index=-1
# Output: item="c"
```

---

### ListLengthNode

Returns the length of a list.

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `length` | INTEGER | Output | List length |

---

### ListAppendNode

Appends an item to a list.

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `item` | ANY | Input | Item to append |
| `result` | LIST | Output | New list with item |

---

### ListContainsNode

Checks if a list contains an item.

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `item` | ANY | Input | Item to find |
| `contains` | BOOLEAN | Output | True if found |
| `index` | INTEGER | Output | Index of item (-1 if not found) |

---

### ListSliceNode

Gets a slice of a list.

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `start` | INTEGER | Input | Start index (default: 0) |
| `end` | INTEGER | Input | End index (default: end of list) |
| `result` | LIST | Output | Sliced list |

---

### ListJoinNode

Joins list items into a string.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `separator` | STRING | No | `", "` | Separator between items |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `separator` | STRING | Input | Separator override |
| `result` | STRING | Output | Joined string |

#### Example

```python
[ListJoin]
    separator: " | "

# Input: list=["red", "green", "blue"]
# Output: result="red | green | blue"
```

---

### ListSortNode

Sorts a list.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `reverse` | BOOLEAN | No | `false` | Sort descending |
| `key_path` | STRING | No | `""` | Dot path for sorting dicts |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `reverse` | BOOLEAN | Input | Reverse override |
| `key_path` | STRING | Input | Key path override |
| `result` | LIST | Output | Sorted list |

#### Example

```python
# Sort list of dicts by nested key
[ListSort]
    key_path: "user.name"
    reverse: false

# Input: list=[{"user": {"name": "Bob"}}, {"user": {"name": "Alice"}}]
# Output: result=[{"user": {"name": "Alice"}}, {"user": {"name": "Bob"}}]
```

---

### ListFilterNode

Filters a list based on conditions.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `condition` | CHOICE | No | `"is_not_none"` | Filter condition |
| `key_path` | STRING | No | `""` | Dot path for comparing dict values |

#### Condition Options

| Condition | Description |
|-----------|-------------|
| `equals` | Item equals value |
| `not_equals` | Item does not equal value |
| `contains` | Item contains value (string) |
| `starts_with` | Item starts with value |
| `ends_with` | Item ends with value |
| `greater_than` | Item > value |
| `less_than` | Item < value |
| `is_not_none` | Item is not None |
| `is_none` | Item is None |
| `is_truthy` | Item is truthy |
| `is_falsy` | Item is falsy |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `condition` | STRING | Input | Condition override |
| `value` | ANY | Input | Comparison value |
| `key_path` | STRING | Input | Key path override |
| `result` | LIST | Output | Filtered list |
| `removed` | LIST | Output | Removed items |

#### Example

```python
[ListFilter]
    condition: "greater_than"
    key_path: "score"

# Input: list=[{"name": "A", "score": 80}, {"name": "B", "score": 50}]
#        value=60
# Output: result=[{"name": "A", "score": 80}]
#         removed=[{"name": "B", "score": 50}]
```

---

### ListMapNode

Transforms each item in a list.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `transform` | CHOICE | No | `"to_string"` | Transformation to apply |
| `key_path` | STRING | No | `""` | Dot path to extract |

#### Transform Options

| Transform | Description |
|-----------|-------------|
| `get_property` | Extract value at key_path |
| `to_string` | Convert to string |
| `to_int` | Convert to integer |
| `to_float` | Convert to float |
| `to_upper` | Uppercase string |
| `to_lower` | Lowercase string |
| `trim` | Strip whitespace |
| `length` | Get length |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `transform` | STRING | Input | Transform override |
| `key_path` | STRING | Input | Key path override |
| `result` | LIST | Output | Transformed list |

#### Example

```python
# Extract names from list of user objects
[ListMap]
    transform: "get_property"
    key_path: "name"

# Input: list=[{"name": "Alice"}, {"name": "Bob"}]
# Output: result=["Alice", "Bob"]
```

---

### ListReduceNode

Reduces a list to a single value.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `operation` | CHOICE | No | `"sum"` | Reduction operation |
| `key_path` | STRING | No | `""` | Dot path to values |

#### Operation Options

| Operation | Description |
|-----------|-------------|
| `sum` | Sum all values |
| `product` | Multiply all values |
| `min` | Minimum value |
| `max` | Maximum value |
| `avg` | Average value |
| `count` | Count items |
| `first` | First item |
| `last` | Last item |
| `join` | Join as string |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `operation` | STRING | Input | Operation override |
| `key_path` | STRING | Input | Key path override |
| `initial` | ANY | Input | Initial value |
| `result` | ANY | Output | Reduced value |

#### Example

```python
# Calculate total price from order items
[ListReduce]
    operation: "sum"
    key_path: "price"

# Input: list=[{"item": "A", "price": 10}, {"item": "B", "price": 20}]
# Output: result=30
```

---

### ListUniqueNode

Removes duplicates from a list (preserves order).

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Source list |
| `result` | LIST | Output | Deduplicated list |

---

### ListFlattenNode

Flattens nested lists.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `depth` | INTEGER | No | `1` | Levels to flatten |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `list` | LIST | Input | Nested list |
| `depth` | INTEGER | Input | Depth override |
| `result` | LIST | Output | Flattened list |

#### Example

```python
[ListFlatten]
    depth: 1

# Input: list=[[1, 2], [3, [4, 5]]]
# Output: result=[1, 2, 3, [4, 5]]

# With depth=2:
# Output: result=[1, 2, 3, 4, 5]
```

---

## Math Nodes

### MathOperationNode

Performs mathematical operations on numbers.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `operation` | CHOICE | No | `"add"` | Math operation |
| `a` | FLOAT | No | `0.0` | First operand |
| `b` | FLOAT | No | `0.0` | Second operand |
| `round_digits` | INTEGER | No | `null` | Decimal places to round |
| `output_var` | STRING | No | `""` | Variable to store result |

#### Operation Options

**Two-operand:**
| Operation | Formula | Description |
|-----------|---------|-------------|
| `add` | a + b | Addition |
| `subtract` | a - b | Subtraction |
| `multiply` | a * b | Multiplication |
| `divide` | a / b | Division |
| `floor_divide` | a // b | Floor division |
| `power` | a^b | Exponentiation |
| `modulo` | a % b | Remainder |
| `min` | min(a, b) | Minimum |
| `max` | max(a, b) | Maximum |

**Single-operand (uses `a` only):**
| Operation | Formula | Description |
|-----------|---------|-------------|
| `abs` | |a| | Absolute value |
| `sqrt` | sqrt(a) | Square root |
| `floor` | floor(a) | Round down |
| `ceil` | ceil(a) | Round up |
| `round` | round(a) | Round |
| `sin` | sin(a) | Sine |
| `cos` | cos(a) | Cosine |
| `tan` | tan(a) | Tangent |
| `log` | log(a) | Natural log |
| `log10` | log10(a) | Log base 10 |
| `exp` | e^a | Exponential |
| `negate` | -a | Negation |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `a` | FLOAT | Input | First operand |
| `b` | FLOAT | Input | Second operand |
| `result` | FLOAT | Output | Calculation result |

#### Example

```python
# Calculate percentage
[MathOperation]
    operation: "multiply"
    round_digits: 2
    output_var: "percentage"

# Inputs: a=75, b=0.01
# Output: result=0.75, stored in {{percentage}}
```

---

### ComparisonNode

Compares two values.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `a` | ANY | No | `null` | First value |
| `b` | ANY | No | `null` | Second value |
| `operator` | CHOICE | No | `"=="` | Comparison operator |

#### Operator Options

| Operator | Description |
|----------|-------------|
| `==` / `equals (==)` | Equal |
| `!=` / `not equals (!=)` | Not equal |
| `>` / `greater than (>)` | Greater than |
| `<` / `less than (<)` | Less than |
| `>=` / `greater or equal (>=)` | Greater or equal |
| `<=` / `less or equal (<=)` | Less or equal |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `a` | ANY | Input | First value |
| `b` | ANY | Input | Second value |
| `result` | BOOLEAN | Output | Comparison result |

#### Example

```python
[Comparison]
    operator: ">="

# Inputs: a=85, b=60
# Output: result=true
```

---

## Complete Workflow Examples

### Example 1: Process CSV Data

```
[ReadCSV] --data--> [ListFilter]
    file_path: "data.csv"      condition: "is_not_none"
                               key_path: "email"
                                    |
                               --result--> [ListMap]
                                              transform: "get_property"
                                              key_path: "email"
                                                   |
                                              --result--> [ListJoin]
                                                             separator: "; "
                                                                  |
                                                             --result--> [SetVariable]
                                                                            name: "emails"
```

### Example 2: Calculate Statistics

```
[GetVariable] --value--> [ListReduce]
    name: "scores"          operation: "sum"
                                |
                           --result--> (sum)

[GetVariable] --value--> [ListReduce]
    name: "scores"          operation: "count"
                                |
                           --result--> (count)

[MathOperation]
    operation: "divide"
    a: {{sum}}
    b: {{count}}
        |
    --result--> [SetVariable]
                   name: "average"
```

### Example 3: Data Transformation Pipeline

```
[ExtractText]
    selector: ".items"
        |
    --text--> [RegexMatch]
                 pattern: "\\$([\\d,]+\\.\\d{2})"
                      |
                 --all_matches--> [ListMap]
                                     transform: "to_float"
                                          |
                                     --result--> [ListReduce]
                                                    operation: "sum"
                                                         |
                                                    --result--> [FormatString]
                                                                   template: "Total: ${total}"
```

## Best Practices

1. **Use ListFilter before processing**: Remove invalid/null items early
2. **Chain transformations**: ListMap -> ListFilter -> ListReduce for ETL
3. **Prefer ListMap over loops**: More efficient for bulk transformations
4. **Use key_path for nested data**: Access dict values without loops
5. **Store intermediate results**: Use `output_var` for debugging
6. **Validate regex patterns**: Test patterns before using in production
7. **Handle empty lists**: Check ListLength before operations that fail on empty

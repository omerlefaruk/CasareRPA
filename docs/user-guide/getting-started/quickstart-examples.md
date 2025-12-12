# Quickstart Examples

This guide provides three practical 5-minute workflows to help you understand CasareRPA's capabilities. Each example demonstrates a different automation scenario.

**Prerequisites:** Complete the [First Workflow Tutorial](first-workflow.md) before starting these examples.

---

## Example 1: Browser Automation - Google Search

**Time:** 5 minutes
**Goal:** Open a browser, navigate to Google, and perform a search

### What You Will Build

```
[Start] -> [Launch Browser] -> [Type Text] -> [Click Element] -> [End]
```

### Step-by-Step Instructions

#### Step 1: Create New Workflow

1. Open CasareRPA Canvas
2. Create a new workflow: **File** > **New Workflow** (`Ctrl+N`)

#### Step 2: Add Start Node

1. From **Node Palette** > **Basic**, drag **Start** onto the canvas
2. Position it on the left side

#### Step 3: Add Launch Browser Node

1. From **Node Palette** > **Browser**, drag **Launch Browser** onto the canvas
2. Position it to the right of Start
3. **Connect** Start output to Launch Browser input

**Configure Launch Browser:**

| Property | Value |
|----------|-------|
| URL | `https://www.google.com` |
| Browser Type | `chromium` |
| Headless | `unchecked` (so you can see the browser) |

[Screenshot: Launch Browser node configured with Google URL]

#### Step 4: Add Type Text Node

1. From **Node Palette** > **Browser**, drag **Type Text** onto the canvas
2. Position it to the right of Launch Browser
3. **Connect** Launch Browser output to Type Text input
4. **Connect** the `page` data port from Launch Browser to Type Text's `page` input

**Configure Type Text:**

| Property | Value |
|----------|-------|
| Selector | `textarea[name="q"]` |
| Text | `CasareRPA automation` |
| Press Enter After | `checked` |

> **Note:** The selector `textarea[name="q"]` targets Google's search input field.

[Screenshot: Type Text node with selector and text configured]

#### Step 5: Add End Node

1. From **Node Palette** > **Basic**, drag **End** onto the canvas
2. Position it to the right of Type Text
3. **Connect** Type Text output to End input

#### Step 6: Run the Workflow

1. Click **Run** (`F5`)
2. Watch as:
   - A Chrome browser window opens
   - Navigates to google.com
   - Types "CasareRPA automation" in the search box
   - Presses Enter to search
3. Workflow completes

[Screenshot: Google search results page]

#### Step 7: Save Your Workflow

1. **File** > **Save** (`Ctrl+S`)
2. Name it `google_search.json`

### What You Learned

- **Launch Browser** opens a browser and navigates to a URL
- **Type Text** finds an input element and types text
- **Data connections** pass the browser page between nodes
- Selectors identify elements on the page

### Try These Variations

- Change the search query to something else
- Try `firefox` or `webkit` as Browser Type
- Add a **Wait** node before Type Text (Node Palette > Utility)
- Add a **Screenshot** node to capture the results

---

## Example 2: File Operations - Read CSV and Display Data

**Time:** 5 minutes
**Goal:** Read data from a CSV file and display it in a message box

### Preparation

First, create a sample CSV file:

1. Open Notepad
2. Paste this content:
```csv
Name,Email,Department
Alice,alice@example.com,Engineering
Bob,bob@example.com,Marketing
Carol,carol@example.com,Sales
```
3. Save as `C:\temp\employees.csv`

### What You Will Build

```
[Start] -> [Read CSV] -> [Message Box] -> [End]
```

### Step-by-Step Instructions

#### Step 1: Create New Workflow

1. Create a new workflow: **File** > **New Workflow** (`Ctrl+N`)

#### Step 2: Add Start Node

1. From **Node Palette** > **Basic**, drag **Start** onto the canvas

#### Step 3: Add Read CSV Node

1. From **Node Palette** > **File**, drag **Read CSV** onto the canvas
2. Position it to the right of Start
3. **Connect** Start output to Read CSV input

**Configure Read CSV:**

| Property | Value |
|----------|-------|
| File Path | `C:\temp\employees.csv` |
| Has Header | `checked` |
| Delimiter | `,` |

[Screenshot: Read CSV node configured with file path]

#### Step 4: Add Message Box Node

1. From **Node Palette** > **System**, drag **Message Box** onto the canvas
2. Position it to the right of Read CSV
3. **Connect** Read CSV output to Message Box input
4. **Connect** the `data` output port from Read CSV to Message Box's `message` input (if available), OR use a variable

**Configure Message Box:**

| Property | Value |
|----------|-------|
| Title | `CSV Data` |
| Message | `Loaded ${row_count} rows from CSV` |

> **Note:** The `${row_count}` variable is set by Read CSV with the number of rows read.

[Screenshot: Message Box with variable in message field]

#### Step 5: Add End Node

1. From **Node Palette** > **Basic**, drag **End** onto the canvas
2. **Connect** Message Box output to End input

#### Step 6: Run the Workflow

1. Click **Run** (`F5`)
2. A message box appears showing the row count
3. Check the **Variables** tab in the bottom panel to see the loaded data

[Screenshot: Variables panel showing CSV data]

#### Step 7: Save Your Workflow

1. **File** > **Save** (`Ctrl+S`)
2. Name it `read_csv_example.json`

### What You Learned

- **Read CSV** loads CSV file data into a variable
- Variables can be used in node properties with `${variable_name}`
- The **Variables** tab shows all workflow data

### Try These Variations

- Change the file path to read a different CSV
- Add a **For Each Row** loop to process each row
- Use **Write CSV** to create a new file
- Try **Read JSON** with a JSON file

---

## Example 3: System Interaction - Input Dialog and Response

**Time:** 5 minutes
**Goal:** Prompt the user for input and display a personalized greeting

### What You Will Build

```
[Start] -> [Input Dialog] -> [Message Box] -> [End]
```

### Step-by-Step Instructions

#### Step 1: Create New Workflow

1. Create a new workflow: **File** > **New Workflow** (`Ctrl+N`)

#### Step 2: Add Start Node

1. From **Node Palette** > **Basic**, drag **Start** onto the canvas

#### Step 3: Add Input Dialog Node

1. From **Node Palette** > **System**, drag **Input Dialog** onto the canvas
2. Position it to the right of Start
3. **Connect** Start output to Input Dialog input

**Configure Input Dialog:**

| Property | Value |
|----------|-------|
| Title | `Welcome` |
| Prompt | `What is your name?` |
| Default Value | (leave empty) |

[Screenshot: Input Dialog node configuration]

#### Step 4: Add Set Variable Node (Optional)

To use the input in multiple places, store it in a variable:

1. From **Node Palette** > **Variable**, drag **Set Variable** onto the canvas
2. Position it after Input Dialog
3. **Connect** Input Dialog output to Set Variable input
4. **Connect** the `value` data port from Input Dialog to Set Variable's `value` input

**Configure Set Variable:**

| Property | Value |
|----------|-------|
| Variable Name | `user_name` |

> **Alternative:** Skip this step and use the Input Dialog's output directly in the next node.

#### Step 5: Add Message Box Node

1. From **Node Palette** > **System**, drag **Message Box** onto the canvas
2. Position it to the right of the previous node
3. **Connect** execution ports

**Configure Message Box:**

| Property | Value |
|----------|-------|
| Title | `Greeting` |
| Message | `Hello, ${user_name}! Welcome to CasareRPA.` |
| Icon Type | `information` |

[Screenshot: Message Box with personalized greeting]

#### Step 6: Add End Node

1. From **Node Palette** > **Basic**, drag **End** onto the canvas
2. **Connect** Message Box output to End input

#### Step 7: Run the Workflow

1. Click **Run** (`F5`)
2. An input dialog appears asking for your name
3. Type your name (e.g., "Alice") and click **OK**
4. A message box appears: "Hello, Alice! Welcome to CasareRPA."

[Screenshot: Input dialog and resulting message box]

#### Step 8: Save Your Workflow

1. **File** > **Save** (`Ctrl+S`)
2. Name it `greeting_workflow.json`

### What You Learned

- **Input Dialog** pauses workflow and waits for user input
- **Set Variable** stores data for later use
- Variables flow through the workflow and can be referenced anywhere

### Try These Variations

- Add a second Input Dialog for another piece of information
- Use **If** node to respond differently based on input
- Add a **Text Area Dialog** for multi-line input
- Use **Yes/No Dialog** to ask confirmation questions

---

## Combining What You Learned

Now try combining concepts from all three examples:

### Challenge Workflow: User-Driven Web Search

Create a workflow that:
1. Asks the user what to search for (Input Dialog)
2. Opens a browser to Google (Launch Browser)
3. Types the user's query (Type Text)
4. Displays a success message (Message Box)

**Hints:**
- Use `${search_query}` variable from Input Dialog in Type Text
- Connect the data ports properly for the page object

### Challenge Workflow: Process CSV and Report

Create a workflow that:
1. Reads a CSV file (Read CSV)
2. Loops through each row (For Each Row)
3. Displays each name in a message (Message Box inside loop)
4. Shows total count at the end (Message Box)

**Hints:**
- For Each Row node is in Control Flow category
- Access row data with `${current_row.Name}`

---

## Summary

These examples demonstrate three core automation scenarios:

| Example | Key Concepts |
|---------|--------------|
| Browser Search | Launch Browser, Type Text, Selectors, Page data |
| CSV Read | File operations, Variables, Data display |
| User Input | Dialogs, Variable storage, String interpolation |

## Common Patterns

From these examples, notice these patterns that apply to all workflows:

1. **Always start with Start** - Every workflow needs a Start node
2. **Connect execution first** - Draw the main flow, then add data connections
3. **Use variables** - Store data in variables to use across nodes
4. **Test incrementally** - Run after each major addition to catch errors early
5. **Save often** - Save your workflow frequently

## Next Steps

With these fundamentals, you're ready to explore more advanced topics:

- **Control Flow** - If/Else, Loops, Switch statements
- **Error Handling** - Try-Catch, Retry, Error recovery
- **Desktop Automation** - Windows application control
- **HTTP/API** - REST API calls and data processing
- **Database** - SQL queries and data manipulation

---

> **Tip:** The best way to learn is to experiment. Modify these examples, try different nodes, and see what happens. CasareRPA's visual interface makes it easy to explore without writing code.

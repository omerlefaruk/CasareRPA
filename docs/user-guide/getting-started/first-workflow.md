# Creating Your First Workflow

This tutorial guides you through creating, running, and saving your first CasareRPA workflow. You will build a simple automation that displays a message box to the user.

**Time required:** 10 minutes

**What you will learn:**
- Opening the Canvas designer
- Adding nodes to the canvas
- Connecting nodes together
- Running a workflow
- Viewing execution results
- Saving your workflow

## Step 1: Open CasareRPA Canvas

Start CasareRPA by running:

```cmd
python run.py
```

The Canvas window opens. This is your visual workflow designer.

[Screenshot: CasareRPA Canvas window with empty canvas area]

## Step 2: Understand the Interface

Before we begin, let's identify the main areas:

| Area | Location | Purpose |
|------|----------|---------|
| Node Palette | Left panel | Contains all available nodes |
| Canvas | Center | Where you build workflows |
| Properties Panel | Right panel | Configure selected node |
| Log Panel | Bottom | Shows execution output |
| Toolbar | Top | Run, stop, save actions |

[Screenshot: Canvas window with labeled areas]

## Step 3: Create a New Workflow

Your canvas should be empty. If not, create a new workflow:

1. Click **File** > **New Workflow** (or press `Ctrl+N`)
2. A blank canvas appears

## Step 4: Add a Start Node

Every workflow begins with a **Start** node:

1. In the **Node Palette** (left side), expand the **Basic** category
2. Find **Start** node
3. **Drag** the Start node onto the canvas
4. Drop it on the left side of the canvas

[Screenshot: Dragging Start node from palette to canvas]

The Start node appears as a green node with one output connection point (called a "port").

> **Tip:** You can also right-click the canvas and select **Add Node** > **Basic** > **Start**.

## Step 5: Add a MessageBox Node

Now add a node that does something - a message dialog:

1. In the **Node Palette**, expand the **System** category
2. Find **Message Box** node
3. **Drag** it onto the canvas
4. Place it to the right of the Start node

[Screenshot: Canvas with Start and MessageBox nodes, not connected]

## Step 6: Configure the MessageBox

Click on the **Message Box** node to select it. The **Properties Panel** on the right shows its settings:

| Property | Value to Enter |
|----------|----------------|
| Title | `Hello CasareRPA` |
| Message | `Welcome to your first workflow!` |
| Icon Type | `information` |
| Buttons | `ok` |

[Screenshot: Properties panel with MessageBox settings filled in]

## Step 7: Connect the Nodes

Nodes communicate through connections. The triangular ports handle execution flow:

1. **Click** on the **output port** (right side) of the Start node
2. **Drag** a line to the **input port** (left side) of the MessageBox node
3. **Release** to create the connection

[Screenshot: Drawing a connection line between Start and MessageBox]

A line now connects the two nodes, showing execution will flow from Start to MessageBox.

> **Note:** The connection line should turn solid when properly connected. If it's dashed or red, the connection isn't valid.

## Step 8: Add an End Node

Complete the workflow with an **End** node:

1. From **Node Palette** > **Basic**, drag an **End** node onto the canvas
2. Place it to the right of the MessageBox node
3. Connect **MessageBox output** to **End input**

Your workflow should now look like this:

```
[Start] -----> [Message Box] -----> [End]
```

[Screenshot: Complete workflow with Start, MessageBox, and End nodes connected]

## Step 9: Run the Workflow

Now let's execute your workflow:

1. Click the **Run** button in the toolbar (green play icon)
   - Or press `F5`
   - Or use menu **Workflow** > **Run**

[Screenshot: Run button highlighted in toolbar]

## Step 10: See the Result

When the workflow runs:

1. The **Start** node highlights briefly (green glow)
2. The **Message Box** node highlights
3. A dialog appears on your screen with your message

[Screenshot: Message box dialog showing "Welcome to your first workflow!"]

4. Click **OK** to dismiss the dialog
5. The **End** node highlights
6. Workflow completes

## Step 11: View the Log

The **Log Panel** at the bottom shows what happened:

```
[INFO] Workflow started
[INFO] Executing: Start
[INFO] Executing: Message Box
[INFO] Message Box: User clicked OK
[INFO] Executing: End
[INFO] Workflow completed successfully
```

[Screenshot: Log panel showing successful execution]

This log helps you understand workflow execution and debug issues.

## Step 12: Save Your Workflow

Save your workflow to use it later:

1. Click **File** > **Save** (or press `Ctrl+S`)
2. Choose a location and filename (e.g., `my_first_workflow.json`)
3. Click **Save**

[Screenshot: Save dialog with filename entered]

> **Note:** CasareRPA workflows are saved as JSON files. You can organize them in folders.

## Understanding What Happened

Let's review what you built:

1. **Start Node** - Entry point that triggers when you click Run
2. **MessageBox Node** - Displays a dialog and waits for user interaction
3. **End Node** - Marks workflow completion
4. **Connections** - Define the order of execution

The **execution flow** moved from Start to MessageBox to End, following your connections.

## Try These Modifications

Practice by modifying your workflow:

### Change the Message

1. Select the MessageBox node
2. In Properties, change **Message** to something new
3. Run again to see the change

### Add Multiple Messages

1. Add another MessageBox node between the first MessageBox and End
2. Connect: `Start -> MessageBox1 -> MessageBox2 -> End`
3. Configure different messages
4. Run to see both dialogs in sequence

### Change the Icon

1. Select the MessageBox node
2. Change **Icon Type** to:
   - `warning` - Yellow warning icon
   - `error` - Red error icon
   - `question` - Question mark icon

[Screenshot: MessageBox with different icon types]

### Add Buttons

1. Change **Buttons** to `yes_no`
2. Run the workflow
3. Notice the dialog now has Yes and No buttons

## Common Issues

### Workflow doesn't run

**Check:** Are all nodes connected? Each node (except Start) needs an incoming connection.

### MessageBox doesn't appear

**Check:** Is the MessageBox configured with a message? Empty messages may not display.

### Nodes won't connect

**Check:** You must connect output ports (right) to input ports (left). You cannot connect output to output.

### "Node not found" error

**Check:** Save and reload the workflow. Some nodes may need a restart to register.

## What You Learned

In this tutorial, you:

- Created a new workflow in Canvas
- Added nodes from the Node Palette
- Configured node properties
- Connected nodes to define execution flow
- Ran the workflow and saw results
- Viewed execution logs
- Saved your workflow

## Next Steps

Now that you've built your first workflow, continue learning:

- [Canvas Overview](canvas-overview.md) - Deep dive into the interface
- [Quickstart Examples](quickstart-examples.md) - Try browser and file automation
- Node Reference - Explore all available nodes

---

> **Congratulations!** You've created your first CasareRPA workflow. The same principles apply to complex automations - add nodes, configure them, connect them, and run.

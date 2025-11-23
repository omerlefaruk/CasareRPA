# Workflow Templates

This directory contains pre-built workflow templates to help you get started with CasareRPA quickly. Templates demonstrate various features and provide a foundation for common automation tasks.

## 📁 Template Categories

### Basic Templates (`basic/`)
Simple workflows perfect for learning the fundamentals of CasareRPA.

**1. Hello World** (`hello_world.py`)
- **Description**: The simplest possible workflow - prints "Hello, World!" to the log
- **Features**: Single log node, basic workflow structure
- **Use Case**: Testing installation, learning workflow basics
- **Nodes**: 1 (LogNode)

**2. Variable Usage** (`variable_usage.py`)
- **Description**: Demonstrates setting and using variables across multiple nodes
- **Features**: Variable creation, variable substitution in messages
- **Use Case**: Understanding variable flow and persistence
- **Nodes**: 3 (2× SetVariableNode, 1× LogNode)

**3. Sequential Tasks** (`sequential_tasks.py`)
- **Description**: Chain of tasks executed in order with delays
- **Features**: Task chaining, progress logging, delays between steps
- **Use Case**: Building multi-step automation workflows
- **Nodes**: 8 (LogNode, SetVariableNode, DelayNode sequences)

---

### Control Flow Templates (`control_flow/`)
Demonstrate conditional logic and looping constructs.

**1. Conditional Logic** (`conditional_logic.py`)
- **Description**: If/else branching based on age variable
- **Features**: IfNode conditional evaluation, true/false branches
- **Use Case**: Decision-making in workflows, branching logic
- **Nodes**: 5 (SetVariableNode, IfNode, 2× LogNode branches, merge)
- **Example**: Age verification (adult vs. minor paths)

**2. For Loop** (`for_loop.py`)
- **Description**: Iterate over a list of items (fruits)
- **Features**: ForLoopNode, loop variable access (item, index)
- **Use Case**: Processing collections, batch operations
- **Nodes**: 5 (SetVariableNode, LogNode, ForLoopNode, loop body, completion)
- **Example**: Processing 5 fruits one-by-one

**3. While Loop** (`while_loop.py`)
- **Description**: Conditional iteration with counter increment
- **Features**: WhileLoopNode, condition evaluation, loop exit
- **Use Case**: Repeat tasks until condition met
- **Nodes**: 6 (counter init, WhileLoopNode, log, increment, loop back, complete)
- **Example**: Countdown from 0 to 5

**4. Error Handling** (`error_handling.py`)
- **Description**: Try-except blocks for error recovery
- **Features**: TryExceptNode, error catching, fallback values
- **Use Case**: Graceful error handling, fault tolerance
- **Nodes**: 8 (setup, try block, risky operation, success/error paths, fallback, complete)
- **Example**: Division by zero with fallback

---

### Debugging Templates (`debugging/`)
Showcase debugging features for workflow development.

**1. Breakpoint Debugging** (`breakpoint_debugging.py`)
- **Description**: Demonstrates breakpoint usage and inspection
- **Features**: Breakpoint setting, execution pause, variable inspection
- **Use Case**: Step-through debugging, state inspection
- **Nodes**: 5 (variable operations with breakpoints at key points)
- **Breakpoints**: Set at nodes "set_y" and "log_result"

**2. Step Mode Debugging** (`step_mode_debugging.py`)
- **Description**: Step-by-step execution with state tracking
- **Features**: Step mode, manual step control, per-step inspection
- **Use Case**: Detailed execution analysis, learning workflows
- **Nodes**: 6 (initialization through multi-step calculation)
- **Execution**: Manual stepping through each node

**3. Variable Inspection** (`variable_inspection.py`)
- **Description**: Real-time variable watching during execution
- **Features**: Variable tracking, transformation monitoring, multi-variable workflows
- **Use Case**: Understanding variable changes, debugging data flow
- **Nodes**: 9 (multiple variable operations and transformations)
- **Variables Tracked**: name, version, execution_count, name_upper, message, stats

---

### Automation Templates (`automation/`)
Real-world automation examples and skeletons.

**1. File Processing** (`file_processing.py`)
- **Description**: Batch file processing workflow structure
- **Features**: File path management, loop over files, input/output handling
- **Use Case**: Processing multiple files, batch operations
- **Nodes**: 12 (setup, file list, ForLoop over files, path operations, complete)
- **Example**: Processing 3 document files (simulated)
- **Note**: Placeholder for actual file I/O nodes

**2. Data Transformation** (`data_transformation.py`)
- **Description**: Filter, transform, and aggregate data
- **Features**: Collection filtering, iteration, aggregation (sum, average)
- **Use Case**: Data analysis, ETL operations, reporting
- **Nodes**: 17 (load data, filter loop, conditionals, aggregation, statistics)
- **Example**: Filter numbers >= 50, calculate sum and average
- **Data Flow**: Raw data → Filter → Transform → Aggregate → Output

**3. Web Scraping Skeleton** (`web_scraping_skeleton.py`)
- **Description**: Framework for browser automation and data extraction
- **Features**: Browser lifecycle, navigation, element extraction, data storage
- **Use Case**: Web scraping, automated testing, data collection
- **Nodes**: 17 (browser open/close, navigation, extraction, processing)
- **Status**: SKELETON/TEMPLATE (placeholders for future browser nodes)
- **Future Nodes**: BrowserLaunchNode, BrowserNavigateNode, BrowserExtractNode, BrowserClickNode, BrowserCloseNode

---

## 🚀 Using Templates

### From GUI

1. **Open CasareRPA**
2. **File Menu → New from Template...** (or press `Ctrl+Shift+N`)
3. **Browse templates** by category or use search
4. **Select a template** to see description and details
5. **Click "Use Template"** to load into graph editor

### From Code

```python
import asyncio
from casare_rpa.utils.template_loader import get_template_loader
from casare_rpa.core.runner import WorkflowRunner

async def main():
    # Get template loader
    loader = get_template_loader()
    
    # Discover all templates
    templates = loader.discover_templates()
    
    # Get a specific template
    basic_templates = loader.get_templates_by_category("basic")
    hello_world = basic_templates[0]  # First basic template
    
    # Create workflow from template
    workflow = await loader.create_workflow_from_template(hello_world)
    
    # Run the workflow
    runner = WorkflowRunner(workflow)
    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Running Templates Directly

Each template can be executed as a standalone script:

```bash
# From project root with virtual environment activated
python templates/basic/hello_world.py
python templates/control_flow/for_loop.py
python templates/debugging/step_mode_debugging.py
python templates/automation/data_transformation.py
```

---

## 🛠️ Customizing Templates

Templates are Python files that create workflows programmatically. To customize:

1. **Copy the template file** to your own location
2. **Modify the `create_*_workflow()` function**
   - Add/remove nodes
   - Change connections
   - Adjust parameters
3. **Run directly** or load through the GUI

### Template Structure

```python
async def create_my_workflow() -> Workflow:
    """
    Create a custom workflow.
    
    Returns:
        Configured workflow
    """
    workflow = Workflow(name="My Workflow")
    
    # Create nodes
    node1 = SomeNode(node_id="node1", param="value")
    node2 = AnotherNode(node_id="node2")
    
    # Add to workflow
    workflow.add_node(node1)
    workflow.add_node(node2)
    
    # Connect nodes
    workflow.add_edge(node1.node_id, node2.node_id)
    
    # Set start node
    workflow.set_start_node(node1.node_id)
    
    return workflow
```

---

## 📊 Template Statistics

| Category | Templates | Total Nodes | Complexity |
|----------|-----------|-------------|------------|
| Basic | 3 | 12 | Beginner |
| Control Flow | 4 | 24 | Intermediate |
| Debugging | 3 | 20 | Intermediate |
| Automation | 3 | 46 | Advanced |
| **Total** | **13** | **102** | - |

---

## 🎯 Learning Path

### For Beginners
1. **Hello World** - Understand basic workflow structure
2. **Variable Usage** - Learn variable management
3. **Sequential Tasks** - Build multi-step workflows

### For Intermediate Users
4. **Conditional Logic** - Add decision-making
5. **For Loop** - Process collections
6. **While Loop** - Conditional iteration
7. **Breakpoint Debugging** - Learn debugging tools

### For Advanced Users
8. **Error Handling** - Build robust workflows
9. **Data Transformation** - Complex data operations
10. **File Processing** - Real automation tasks
11. **Web Scraping Skeleton** - Browser automation framework

---

## 🔧 Creating Your Own Templates

To add a new template:

1. **Create a Python file** in the appropriate category folder
2. **Add docstring** describing the template
3. **Implement `create_*_workflow()` function** that returns a Workflow
4. **Document** with clear comments
5. **Test** by running directly

### Template Checklist

- ✅ Clear docstring with description and usage
- ✅ Descriptive function name (`create_something_workflow`)
- ✅ Returns `Workflow` instance
- ✅ Nodes have meaningful IDs
- ✅ Proper edge connections
- ✅ Start node set correctly
- ✅ `async def main()` for standalone execution
- ✅ Can be run with `python template_file.py`

---

## 🐛 Troubleshooting

**Template not appearing in browser?**
- Ensure file is in correct category subfolder
- Check file has `.py` extension
- Verify `create_*_workflow()` function exists

**Template fails to load?**
- Check for syntax errors
- Ensure all nodes are properly imported
- Verify node parameters are correct

**Template runs but doesn't work as expected?**
- Check node connections (edges)
- Verify variable names match across nodes
- Use debugging templates to inspect execution

---

## 📚 Additional Resources

- **Documentation**: See `docs/` folder for comprehensive guides
- **Examples**: Check `demos/` folder for more example scripts
- **Tests**: Look at `tests/` for unit test examples
- **Node Reference**: See `src/casare_rpa/nodes/` for available node types

---

## 🤝 Contributing Templates

Have a useful template? Contributions welcome!

1. Create your template following the guidelines above
2. Test thoroughly
3. Document clearly
4. Submit as a pull request with:
   - Template file
   - Description of use case
   - Screenshot/demo if applicable

---

## 📝 License

All templates are provided under the same license as CasareRPA.
Free to use, modify, and distribute.

---

**Happy Automating! 🤖**

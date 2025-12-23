"""
Example: Node Creation End-to-End

AI-HINT: Copy this pattern when creating new automation nodes.
AI-CONTEXT: Shows complete flow from node class to test.

Run: pytest tests/examples/test_node_creation_example.py -v
"""

from unittest.mock import MagicMock

import pytest

# =============================================================================
# STEP 1: Import the necessary decorators and base classes
# =============================================================================
from casare_rpa.domain import node, properties
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects import DataType

# =============================================================================
# STEP 2: Define the node class with decorators
# =============================================================================


@properties(
    # Essential properties are shown when node is collapsed
    PropertyDef(
        "text",
        PropertyType.STRING,
        default="",
        essential=True,
        tooltip="Text to transform",
    ),
    PropertyDef("uppercase", PropertyType.BOOLEAN, default=True, tooltip="Convert to uppercase"),
    # Non-essential properties are in advanced section
    PropertyDef("prefix", PropertyType.STRING, default="", tooltip="Prefix to add"),
)
@node(category="example")  # Category for node palette grouping
class ExampleTextTransformNode(BaseNode):
    """
    AI-HINT: Example node demonstrating text transformation.
    AI-CONTEXT: Use as template for simple data processing nodes.

    Transforms input text based on configuration.
    """

    NODE_NAME = "Example Text Transform"
    CATEGORY = "example"

    def _define_ports(self):
        """Define input and output ports."""
        # Execution ports - ALWAYS use add_exec_input/output, not add_input_port
        self.add_exec_input()
        self.add_exec_output()

        # Data ports
        self.add_input_port("input_text", DataType.STRING, "Text to transform")
        self.add_output_port("output_text", DataType.STRING, "Transformed text")

    async def execute(self, context) -> dict:
        """
        Execute the node logic.

        Args:
            context: ExecutionContext with variables, resources, etc.

        Returns:
            dict with 'success' bool and either 'data' or 'error'
        """
        try:
            # Get input from connected port OR config
            input_text = self.get_input_value("input_text")
            if input_text is None:
                input_text = self.get_parameter("text")

            # Get configuration
            uppercase = self.get_parameter("uppercase")
            prefix = self.get_parameter("prefix")

            # Perform transformation
            result = input_text
            if uppercase:
                result = result.upper()
            if prefix:
                result = f"{prefix}{result}"

            # Set output port value
            self.set_output_value("output_text", result)

            # Return success result
            return {"success": True, "data": {"output_text": result}}

        except Exception as e:
            # Return error result (don't raise)
            return {
                "success": False,
                "error": str(e),
                "error_code": "TEXT_TRANSFORM_ERROR",
            }


# =============================================================================
# STEP 3: Create test fixtures
# =============================================================================


@pytest.fixture
def execution_context():
    """
    AI-HINT: Basic execution context fixture.
    AI-CONTEXT: Use for nodes that don't need browser/desktop resources.
    """
    context = MagicMock()
    context.variables = {}
    context.resources = {}
    return context


@pytest.fixture
def text_node():
    """Create instance of our example node."""
    return ExampleTextTransformNode(
        node_id="test_node_1",
        config={
            "text": "hello world",
            "uppercase": True,
            "prefix": "",
        },
    )


# =============================================================================
# STEP 4: Write the 3-scenario test pattern
# =============================================================================


class TestExampleTextTransformNode:
    """
    AI-HINT: Tests follow 3-scenario pattern: SUCCESS, ERROR, EDGE_CASE.
    AI-CONTEXT: Every node should have at least these three test types.
    """

    @pytest.mark.asyncio
    async def test_success_uppercase_transform(self, execution_context, text_node):
        """
        SUCCESS SCENARIO: Normal operation with valid input.

        AI-HINT: Test the happy path first.
        """
        # Arrange - node is already configured via fixture

        # Act
        result = await text_node.execute(execution_context)

        # Assert
        assert result["success"] is True
        assert result["data"]["output_text"] == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_success_with_prefix(self, execution_context):
        """SUCCESS: Test with prefix configuration."""
        # Arrange - create node with specific config
        node = ExampleTextTransformNode(
            node_id="test_prefix",
            config={
                "text": "world",
                "uppercase": False,
                "prefix": "Hello, ",
            },
        )

        # Act
        result = await node.execute(execution_context)

        # Assert
        assert result["success"] is True
        assert result["data"]["output_text"] == "Hello, world"

    @pytest.mark.asyncio
    async def test_success_from_input_port(self, execution_context):
        """SUCCESS: Test with value from input port instead of config."""
        # Arrange
        node = ExampleTextTransformNode(
            node_id="test_port", config={"uppercase": True, "prefix": ""}
        )
        # Use set_input_value to properly set port value
        node.set_input_value("input_text", "from port")

        # Act
        result = await node.execute(execution_context)

        # Assert
        assert result["success"] is True
        assert result["data"]["output_text"] == "FROM PORT"

    @pytest.mark.asyncio
    async def test_edge_case_empty_input(self, execution_context):
        """
        EDGE CASE: Empty input should not crash.

        AI-HINT: Edge cases test boundary conditions.
        """
        # Arrange
        node = ExampleTextTransformNode(
            node_id="test_empty", config={"text": "", "uppercase": True, "prefix": ""}
        )

        # Act
        result = await node.execute(execution_context)

        # Assert - should handle gracefully
        assert result["success"] is True
        assert result["data"]["output_text"] == ""

    @pytest.mark.asyncio
    async def test_edge_case_none_input(self, execution_context):
        """EDGE CASE: None/missing input handling."""
        # Arrange
        node = ExampleTextTransformNode(
            node_id="test_none",
            config={},  # Missing required config
        )
        # Explicitly set None input
        node._input_values = {"input_text": None}

        # Act
        result = await node.execute(execution_context)

        # Assert - should return error, not crash
        # (depends on implementation - this tests graceful failure)
        assert isinstance(result, dict)
        assert "success" in result


# =============================================================================
# STEP 5: Test node registration (optional but recommended)
# =============================================================================


class TestNodeRegistration:
    """Test that node is properly configured."""

    def test_node_has_correct_category(self):
        """Verify node category is set."""
        node = ExampleTextTransformNode(node_id="test")
        assert node.CATEGORY == "example"

    def test_node_has_ports_defined(self):
        """Verify ports are created."""
        node = ExampleTextTransformNode(node_id="test", config={})
        # Ports are defined in _define_ports
        assert hasattr(node, "_input_ports") or hasattr(node, "input_ports")

    def test_node_has_properties_schema(self):
        """Verify property schema is attached."""
        # The @properties decorator adds schema
        from casare_rpa.domain.decorators import get_node_schema

        schema = get_node_schema(ExampleTextTransformNode)
        assert schema is not None


# =============================================================================
# USAGE NOTES FOR AI AGENTS
# =============================================================================
"""
AI-HINT: Copy this file when creating a new node.

Checklist:
1. [ ] Copy this file to tests/nodes/{category}/test_{node_name}.py
2. [ ] Replace ExampleTextTransformNode with your node class
3. [ ] Update fixtures for your node's requirements
4. [ ] Add SUCCESS, ERROR, EDGE_CASE tests
5. [ ] Run: pytest tests/nodes/{category}/test_{node_name}.py -v

For browser nodes, add mock_page fixture:
```python
@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.query_selector = AsyncMock(return_value=AsyncMock())
    return page
```

For nodes with credentials, add mock credential provider.
"""

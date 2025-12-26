# Node Testing Reference

Detailed templates for testing CasareRPA nodes.

## Node Test Template

```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from casare_rpa.nodes.{category}.{node_name}_node import {NodeName}Node
from casare_rpa.domain.value_objects import ExecutionResult, DataType

@pytest.fixture
def node():
    return {NodeName}Node()

@pytest.fixture
def mock_context():
    context = MagicMock()
    context.get_variable = MagicMock(side_effect=lambda x: {
        'input_port_1': 'test_value_1',
    }.get(x))
    context.set_variable = MagicMock()
    return context

class Test{NodeName}Node:
    def test_initialization(self, node):
        assert node.id == "{node_id}"
        assert node.name == "{Node Display Name}"
        assert node.category == "{category}"

    def test_has_correct_input_ports(self, node):
        assert "input_port_1" in node.inputs
        assert node.inputs["input_port_1"].data_type == DataType.STRING

    def test_has_correct_output_ports(self, node):
        assert "output_port_1" in node.outputs
        assert node.outputs["output_port_1"].data_type == DataType.STRING

    @pytest.mark.asyncio
    async def test_execute_success(self, node, mock_context):
        result = await node.execute(mock_context)
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert "output_port_1" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_missing_input(self, node, mock_context):
        mock_context.get_variable.return_value = None
        result = await node.execute(mock_context)
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_with_invalid_input_type(self, node, mock_context):
        mock_context.get_variable.return_value = 12345
        result = await node.execute(mock_context)
        assert result.success is False
        assert "type" in result.error.lower() or "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, node, mock_context):
        mock_context.get_variable.side_effect = RuntimeError("Test error")
        result = await node.execute(mock_context)
        assert result.success is False
        assert "Test error" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_empty_string(self, node, mock_context):
        mock_context.get_variable.return_value = ""
        result = await node.execute(mock_context)
        assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    async def test_execute_with_special_characters(self, node, mock_context):
        mock_context.get_variable.return_value = "test\n\t\\\"special"
        result = await node.execute(mock_context)
        assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    @patch('casare_rpa.infrastructure.resources.browser_manager.BrowserResourceManager')
    async def test_execute_with_browser_resource(self, mock_browser_manager, node, mock_context):
        mock_page = AsyncMock()
        mock_browser_manager.get_page.return_value = mock_page
        result = await node.execute(mock_context)
        mock_browser_manager.get_page.assert_called_once()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_logs_info_on_success(self, node, mock_context, caplog):
        result = await node.execute(mock_context)
        assert result.success is True
        assert any("completed" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_execute_logs_error_on_failure(self, node, mock_context, caplog):
        mock_context.get_variable.side_effect = ValueError("Test error")
        result = await node.execute(mock_context)
        assert result.success is False
        assert any(record.levelname == "ERROR" for record in caplog.records)
```

## Browser Node Testing

```python
@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    return page

@pytest.fixture
def mock_browser_manager(mock_page):
    manager = MagicMock()
    manager.get_page = AsyncMock(return_value=mock_page)
    return manager

@pytest.mark.asyncio
async def test_browser_node_click_element(node, mock_context, mock_browser_manager):
    # Setup mock page with element
    mock_context.resources = {'browser': mock_browser_manager}

    result = await node.execute(mock_context)

    mock_page.click.assert_called_once_with('#selector')
    assert result.success is True
```

## Desktop Node Testing

```python
@pytest.fixture
def mock_desktop_context():
    from uiautomation import Control
    control = MagicMock(spec=Control)
    control.Click = MagicMock()
    control.SendKeys = MagicMock()
    control.GetWindowTextAsync = AsyncMock(return_value="Window Title")
    return control
```

## Data Node Testing

```python
@pytest.mark.asyncio
async def test_data_node_transforms_list(node, mock_context):
    input_data = [1, 2, 3, 4, 5]
    mock_context.get_variable.return_value = input_data

    result = await node.execute(mock_context)

    assert result.success is True
    assert "output" in result.output
    # Verify transformation logic
```

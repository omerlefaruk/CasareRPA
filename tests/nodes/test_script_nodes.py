"""
Tests for Script execution nodes.

Tests 5 script nodes:
- RunPythonScriptNode: Execute inline Python code
- RunPythonFileNode: Execute Python file
- EvalExpressionNode: Evaluate Python expression
- RunBatchScriptNode: Execute batch/shell scripts
- RunJavaScriptNode: Execute JavaScript with Node.js

All subprocess calls are mocked for security - no real scripts executed.
"""

import sys
import subprocess
import pytest
from unittest.mock import Mock, patch, MagicMock

# Uses execution_context fixture from tests/conftest.py - no import needed


class TestRunPythonScriptNode:
    """Tests for RunPythonScriptNode."""

    @pytest.mark.asyncio
    async def test_inline_script_success(self, execution_context) -> None:
        """Test running inline Python script successfully."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode

        node = RunPythonScriptNode(node_id="test_py_inline")
        node.set_input_value("code", "result = 2 + 2")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 4
        assert node.get_output_value("success") is True
        assert node.get_output_value("error") == ""

    @pytest.mark.asyncio
    async def test_inline_script_with_variables(self, execution_context) -> None:
        """Test script with input variables."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode

        node = RunPythonScriptNode(node_id="test_py_vars")
        node.set_input_value("code", "result = x + y")
        node.set_input_value("variables", {"x": 10, "y": 5})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 15

    @pytest.mark.asyncio
    async def test_inline_script_captures_print(self, execution_context) -> None:
        """Test capturing print output."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode

        node = RunPythonScriptNode(node_id="test_py_print")
        node.set_input_value("code", "print('Hello World')\nresult = 'done'")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "Hello World" in node.get_output_value("output")
        assert node.get_output_value("result") == "done"

    @pytest.mark.asyncio
    async def test_inline_script_syntax_error(self, execution_context) -> None:
        """Test handling syntax error."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode

        node = RunPythonScriptNode(node_id="test_py_syntax")
        node.set_input_value("code", "def broken(")  # Syntax error
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is True  # Node execution succeeded
        assert node.get_output_value("success") is False  # Script failed
        # Error message contains info about unclosed parenthesis or syntax issue
        error_msg = node.get_output_value("error").lower()
        assert len(error_msg) > 0  # Some error message was captured

    @pytest.mark.asyncio
    async def test_inline_script_runtime_error(self, execution_context) -> None:
        """Test handling runtime error."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode

        node = RunPythonScriptNode(node_id="test_py_runtime")
        node.set_input_value("code", "result = 1 / 0")  # ZeroDivisionError
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("success") is False
        assert "division" in node.get_output_value("error").lower()

    @pytest.mark.asyncio
    async def test_inline_script_empty_code_error(self, execution_context) -> None:
        """Test empty code raises error."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode

        node = RunPythonScriptNode(node_id="test_py_empty")
        node.set_input_value("code", "")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_isolated_script_success(self, execution_context) -> None:
        """Test running isolated script in subprocess."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="__RESULT__:42\n", stderr=""
            )

            node = RunPythonScriptNode(
                node_id="test_py_isolated", config={"isolated": True}
            )
            node.set_input_value("code", "result = 42")
            node.set_input_value("variables", {})

            result = await node.execute(execution_context)

            assert result["success"] is True


class TestRunPythonFileNode:
    """Tests for RunPythonFileNode."""

    @pytest.mark.asyncio
    async def test_run_file_success(self, execution_context) -> None:
        """Test running Python file successfully."""
        from casare_rpa.nodes.script_nodes import RunPythonFileNode

        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_run.return_value = Mock(
                returncode=0, stdout="Script output", stderr=""
            )

            node = RunPythonFileNode(node_id="test_py_file")
            node.set_input_value("file_path", "/path/to/script.py")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("stdout") == "Script output"
            assert node.get_output_value("return_code") == 0
            assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_run_file_with_args(self, execution_context) -> None:
        """Test running Python file with arguments."""
        from casare_rpa.nodes.script_nodes import RunPythonFileNode

        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_run.return_value = Mock(
                returncode=0, stdout="Args received", stderr=""
            )

            node = RunPythonFileNode(node_id="test_py_file_args")
            node.set_input_value("file_path", "/path/to/script.py")
            node.set_input_value("args", ["--flag", "value"])

            result = await node.execute(execution_context)

            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "--flag" in call_args
            assert "value" in call_args

    @pytest.mark.asyncio
    async def test_run_file_not_found(self, execution_context) -> None:
        """Test error when file not found."""
        from casare_rpa.nodes.script_nodes import RunPythonFileNode

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            node = RunPythonFileNode(node_id="test_py_notfound")
            node.set_input_value("file_path", "/nonexistent/script.py")

            result = await node.execute(execution_context)

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_file_timeout(self, execution_context) -> None:
        """Test file execution timeout."""
        from casare_rpa.nodes.script_nodes import RunPythonFileNode

        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_run.side_effect = subprocess.TimeoutExpired("python", 60)

            node = RunPythonFileNode(node_id="test_py_timeout", config={"timeout": 60})
            node.set_input_value("file_path", "/path/to/slow_script.py")

            result = await node.execute(execution_context)

            assert result["success"] is False
            assert node.get_output_value("return_code") == -1

    @pytest.mark.asyncio
    async def test_run_file_nonzero_exit(self, execution_context) -> None:
        """Test file with non-zero exit code."""
        from casare_rpa.nodes.script_nodes import RunPythonFileNode

        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="Script error")

            node = RunPythonFileNode(node_id="test_py_fail")
            node.set_input_value("file_path", "/path/to/failing_script.py")

            result = await node.execute(execution_context)

            assert result["success"] is True  # Node succeeded
            assert node.get_output_value("success") is False  # Script failed
            assert node.get_output_value("return_code") == 1


class TestEvalExpressionNode:
    """Tests for EvalExpressionNode."""

    @pytest.mark.asyncio
    async def test_eval_simple_expression(self, execution_context) -> None:
        """Test evaluating simple expression."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval")
        node.set_input_value("expression", "2 + 2 * 3")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 8
        assert node.get_output_value("type") == "int"
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_eval_with_variables(self, execution_context) -> None:
        """Test evaluation with variables."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval_vars")
        node.set_input_value("expression", "x * y + z")
        node.set_input_value("variables", {"x": 5, "y": 3, "z": 2})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 17

    @pytest.mark.asyncio
    async def test_eval_string_operations(self, execution_context) -> None:
        """Test string expression evaluation."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval_str")
        node.set_input_value("expression", "'Hello' + ' ' + 'World'")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello World"
        assert node.get_output_value("type") == "str"

    @pytest.mark.asyncio
    async def test_eval_list_comprehension(self, execution_context) -> None:
        """Test list comprehension evaluation."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval_list")
        node.set_input_value("expression", "[x**2 for x in range(5)]")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [0, 1, 4, 9, 16]
        assert node.get_output_value("type") == "list"

    @pytest.mark.asyncio
    async def test_eval_error_handling(self, execution_context) -> None:
        """Test error handling in evaluation."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval_error")
        node.set_input_value("expression", "undefined_variable + 1")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert node.get_output_value("success") is False
        assert node.get_output_value("type") == "error"

    @pytest.mark.asyncio
    async def test_eval_empty_expression(self, execution_context) -> None:
        """Test empty expression raises error."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval_empty")
        node.set_input_value("expression", "")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_eval_safe_builtins_available(self, execution_context) -> None:
        """Test safe builtins are available."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval_builtins")
        node.set_input_value("expression", "len([1,2,3]) + sum([1,2,3])")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 9  # 3 + 6


class TestRunBatchScriptNode:
    """Tests for RunBatchScriptNode."""

    @pytest.mark.asyncio
    async def test_batch_script_success(self, execution_context) -> None:
        """Test running batch script successfully."""
        from casare_rpa.nodes.script_nodes import RunBatchScriptNode

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("os.unlink") as mock_unlink,
            patch("os.path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.name = "/tmp/test_script.bat"
            mock_tempfile.return_value = mock_file

            mock_run.return_value = Mock(returncode=0, stdout="Batch output", stderr="")

            node = RunBatchScriptNode(node_id="test_batch")
            node.set_input_value("script", "echo Hello")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("stdout") == "Batch output"
            assert node.get_output_value("return_code") == 0

    @pytest.mark.asyncio
    async def test_batch_script_with_working_dir(self, execution_context) -> None:
        """Test batch script with working directory."""
        from casare_rpa.nodes.script_nodes import RunBatchScriptNode

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("os.unlink") as mock_unlink,
            patch("os.path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.name = "/tmp/script.bat"
            mock_tempfile.return_value = mock_file

            mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

            node = RunBatchScriptNode(node_id="test_batch_dir")
            node.set_input_value("script", "dir")
            node.set_input_value("working_dir", "C:\\Users")

            result = await node.execute(execution_context)

            assert result["success"] is True
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cwd"] == "C:\\Users"

    @pytest.mark.asyncio
    async def test_batch_script_timeout(self, execution_context) -> None:
        """Test batch script timeout."""
        from casare_rpa.nodes.script_nodes import RunBatchScriptNode

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("os.unlink") as mock_unlink,
            patch("os.path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.name = "/tmp/script.bat"
            mock_tempfile.return_value = mock_file

            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)

            node = RunBatchScriptNode(
                node_id="test_batch_timeout", config={"timeout": 60}
            )
            node.set_input_value("script", "sleep 999")

            result = await node.execute(execution_context)

            assert result["success"] is False
            assert node.get_output_value("return_code") == -1

    @pytest.mark.asyncio
    async def test_batch_script_nonzero_exit(self, execution_context) -> None:
        """Test batch script with non-zero exit."""
        from casare_rpa.nodes.script_nodes import RunBatchScriptNode

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("os.unlink") as mock_unlink,
            patch("os.path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.name = "/tmp/script.bat"
            mock_tempfile.return_value = mock_file

            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Command not found"
            )

            node = RunBatchScriptNode(node_id="test_batch_fail")
            node.set_input_value("script", "invalid_command")

            result = await node.execute(execution_context)

            assert result["success"] is True  # Node succeeded
            assert node.get_output_value("success") is False  # Script failed
            assert node.get_output_value("return_code") == 1

    @pytest.mark.asyncio
    async def test_batch_script_empty_error(self, execution_context) -> None:
        """Test empty script raises error."""
        from casare_rpa.nodes.script_nodes import RunBatchScriptNode

        node = RunBatchScriptNode(node_id="test_batch_empty")
        node.set_input_value("script", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestRunJavaScriptNode:
    """Tests for RunJavaScriptNode."""

    @pytest.mark.asyncio
    async def test_javascript_success(self, execution_context) -> None:
        """Test running JavaScript successfully."""
        from casare_rpa.nodes.script_nodes import RunJavaScriptNode

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("os.unlink") as mock_unlink,
        ):
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.name = "/tmp/script.js"
            mock_tempfile.return_value = mock_file

            mock_run.return_value = Mock(
                returncode=0, stdout="Hello from JS", stderr=""
            )

            node = RunJavaScriptNode(node_id="test_js")
            node.set_input_value("code", "console.log('Hello from JS')")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("result") == "Hello from JS"
            assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_javascript_with_input_data(self, execution_context) -> None:
        """Test JavaScript with input data."""
        from casare_rpa.nodes.script_nodes import RunJavaScriptNode

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("os.unlink") as mock_unlink,
        ):
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.name = "/tmp/script.js"
            mock_tempfile.return_value = mock_file

            mock_run.return_value = Mock(returncode=0, stdout="15", stderr="")

            node = RunJavaScriptNode(node_id="test_js_input")
            node.set_input_value("code", "console.log(inputData.x + inputData.y)")
            node.set_input_value("input_data", {"x": 10, "y": 5})

            result = await node.execute(execution_context)

            assert result["success"] is True
            # Verify inputData was serialized in wrapper
            write_call = mock_file.write.call_args[0][0]
            assert "inputData" in write_call

    @pytest.mark.asyncio
    async def test_javascript_node_not_found(self, execution_context) -> None:
        """Test error when Node.js not found."""
        from casare_rpa.nodes.script_nodes import RunJavaScriptNode

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("os.unlink") as mock_unlink,
        ):
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.name = "/tmp/script.js"
            mock_tempfile.return_value = mock_file

            mock_run.side_effect = FileNotFoundError("node not found")

            node = RunJavaScriptNode(node_id="test_js_nonode")
            node.set_input_value("code", "console.log('test')")

            result = await node.execute(execution_context)

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_javascript_syntax_error(self, execution_context) -> None:
        """Test JavaScript syntax error."""
        from casare_rpa.nodes.script_nodes import RunJavaScriptNode

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("os.unlink") as mock_unlink,
        ):
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.name = "/tmp/script.js"
            mock_tempfile.return_value = mock_file

            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="SyntaxError: Unexpected token"
            )

            node = RunJavaScriptNode(node_id="test_js_error")
            node.set_input_value("code", "function broken(")

            result = await node.execute(execution_context)

            assert result["success"] is True  # Node succeeded
            assert node.get_output_value("success") is False  # Script failed
            assert "SyntaxError" in node.get_output_value("error")

    @pytest.mark.asyncio
    async def test_javascript_empty_code_error(self, execution_context) -> None:
        """Test empty JavaScript code raises error."""
        from casare_rpa.nodes.script_nodes import RunJavaScriptNode

        node = RunJavaScriptNode(node_id="test_js_empty")
        node.set_input_value("code", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

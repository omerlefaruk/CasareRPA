"""
Script execution nodes for CasareRPA.

This module provides nodes for executing scripts:
- RunPythonScriptNode: Execute Python code
- RunPythonFileNode: Execute Python file
- EvalExpressionNode: Evaluate Python expression
- RunBatchScriptNode: Execute batch/shell script
"""

import asyncio
import subprocess
import sys
import tempfile
import os
from typing import Any, Optional, Dict
from pathlib import Path

from loguru import logger

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext


class RunPythonScriptNode(BaseNode):
    """
    Execute Python code inline.

    Config:
        timeout: Execution timeout in seconds (default: 60)
        isolated: Run in isolated subprocess (default: False)

    Inputs:
        code: Python code to execute
        variables: Dict of variables to pass to the script

    Outputs:
        result: Return value (last expression or explicit 'result' variable)
        output: Captured print output
        success: Whether execution succeeded
        error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Run Python Script", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunPythonScriptNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("code", PortType.INPUT, DataType.STRING)
        self.add_input_port("variables", PortType.INPUT, DataType.DICT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("output", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            code = str(self.get_input_value("code", context) or "")
            variables = self.get_input_value("variables", context) or {}
            timeout = self.config.get("timeout", 60)
            isolated = self.config.get("isolated", False)

            if not code:
                raise ValueError("code is required")

            if not isinstance(variables, dict):
                variables = {}

            if isolated:
                # Run in subprocess
                result, output, error = await self._run_isolated(code, variables, timeout)
            else:
                # Run inline (faster but shares memory)
                result, output, error = self._run_inline(code, variables)

            success = error == ""

            self.set_output_value("result", result)
            self.set_output_value("output", output)
            self.set_output_value("success", success)
            self.set_output_value("error", error)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"success": success},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("result", None)
            self.set_output_value("output", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _run_inline(self, code: str, variables: Dict[str, Any]) -> tuple[Any, str, str]:
        """Execute Python code inline."""
        import io
        from contextlib import redirect_stdout

        # Capture stdout
        output_buffer = io.StringIO()

        # Prepare execution namespace
        namespace = {
            '__builtins__': __builtins__,
            'result': None,
            **variables
        }

        error = ""
        result = None

        try:
            with redirect_stdout(output_buffer):
                exec(code, namespace)

            result = namespace.get('result')
            output = output_buffer.getvalue()

        except Exception as e:
            error = str(e)
            output = output_buffer.getvalue()

        return result, output, error

    async def _run_isolated(self, code: str, variables: Dict[str, Any], timeout: int) -> tuple[Any, str, str]:
        """Execute Python code in isolated subprocess."""
        import json

        # Create wrapper script
        wrapper = f'''
import sys
import json

# Input variables
_vars = json.loads(sys.argv[1])
result = None

# Make variables available
for _k, _v in _vars.items():
    exec(f"{{_k}} = _v")

# Execute user code
{code}

# Output result
print("__RESULT__:" + json.dumps(result, default=str))
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapper)
            script_path = f.name

        try:
            proc = subprocess.run(
                [sys.executable, script_path, json.dumps(variables)],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = proc.stdout
            error = proc.stderr

            # Extract result
            result = None
            if "__RESULT__:" in output:
                result_line = [l for l in output.split('\n') if l.startswith("__RESULT__:")]
                if result_line:
                    try:
                        result = json.loads(result_line[0].replace("__RESULT__:", ""))
                    except json.JSONDecodeError:
                        pass
                    output = output.replace(result_line[0] + "\n", "")

            return result, output.strip(), error.strip()

        finally:
            os.unlink(script_path)

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class RunPythonFileNode(BaseNode):
    """
    Execute a Python file.

    Config:
        timeout: Execution timeout in seconds (default: 60)
        python_path: Python interpreter path (default: current)
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries in ms (default: 1000)

    Inputs:
        file_path: Path to Python file
        args: Command line arguments (list or string)
        working_dir: Working directory

    Outputs:
        stdout: Standard output
        stderr: Standard error
        return_code: Process return code
        success: Whether execution succeeded
    """

    def __init__(self, node_id: str, name: str = "Run Python File", **kwargs) -> None:
        # Default config with all options
        default_config = {
            "timeout": 60,
            "python_path": sys.executable,
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
            "retry_on_nonzero": False,  # Retry if return code is non-zero
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunPythonFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("args", PortType.INPUT, DataType.ANY)
        self.add_input_port("working_dir", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("stdout", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("stderr", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("return_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = str(self.get_input_value("file_path", context) or "")
            args = self.get_input_value("args", context)
            working_dir = self.get_input_value("working_dir", context)
            timeout = self.config.get("timeout", 60)
            python_path = self.config.get("python_path", sys.executable)

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 1000))
            retry_on_nonzero = self.config.get("retry_on_nonzero", False)

            if not file_path:
                raise ValueError("file_path is required")

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Python file not found: {file_path}")

            # Build command
            cmd = [python_path, str(path)]

            if args:
                if isinstance(args, list):
                    cmd.extend(str(a) for a in args)
                elif isinstance(args, str):
                    cmd.extend(args.split())

            logger.info(f"Running Python file: {file_path}")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for Python file execution")

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=working_dir
                    )

                    stdout = result.stdout
                    stderr = result.stderr
                    return_code = result.returncode
                    success = return_code == 0

                    # Check if we should retry on non-zero return code
                    if not success and retry_on_nonzero and attempts < max_attempts:
                        logger.warning(f"Python file returned non-zero ({return_code}), retrying...")
                        await asyncio.sleep(retry_interval / 1000)
                        continue

                    self.set_output_value("stdout", stdout)
                    self.set_output_value("stderr", stderr)
                    self.set_output_value("return_code", return_code)
                    self.set_output_value("success", success)
                    self.status = NodeStatus.SUCCESS

                    logger.info(f"Python file executed: return_code={return_code} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"return_code": return_code, "success": success, "attempts": attempts},
                        "next_nodes": ["exec_out"]
                    }

                except subprocess.TimeoutExpired as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Python file timed out (attempt {attempts})")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Python file execution failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            # All attempts failed
            if isinstance(last_error, subprocess.TimeoutExpired):
                self.set_output_value("stdout", "")
                self.set_output_value("stderr", f"Execution timed out after {timeout}s")
                self.set_output_value("return_code", -1)
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                logger.error(f"Python file execution timed out after {max_attempts} attempts")
                return {"success": False, "error": "Timeout", "next_nodes": []}

            raise last_error

        except Exception as e:
            self.set_output_value("stdout", "")
            self.set_output_value("stderr", str(e))
            self.set_output_value("return_code", -1)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to run Python file: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class EvalExpressionNode(BaseNode):
    """
    Evaluate a Python expression and return the result.

    Inputs:
        expression: Python expression to evaluate
        variables: Dict of variables available in expression

    Outputs:
        result: Expression result
        type: Result type name
        success: Whether evaluation succeeded
        error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Eval Expression", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "EvalExpressionNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("expression", PortType.INPUT, DataType.STRING)
        self.add_input_port("variables", PortType.INPUT, DataType.DICT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("type", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            expression = str(self.get_input_value("expression", context) or "")
            variables = self.get_input_value("variables", context) or {}

            if not expression:
                raise ValueError("expression is required")

            if not isinstance(variables, dict):
                variables = {}

            # Provide safe builtins
            safe_builtins = {
                'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
                'chr': chr, 'dict': dict, 'enumerate': enumerate, 'filter': filter,
                'float': float, 'format': format, 'hex': hex, 'int': int,
                'len': len, 'list': list, 'map': map, 'max': max, 'min': min,
                'oct': oct, 'ord': ord, 'pow': pow, 'range': range, 'repr': repr,
                'reversed': reversed, 'round': round, 'set': set, 'slice': slice,
                'sorted': sorted, 'str': str, 'sum': sum, 'tuple': tuple, 'type': type,
                'zip': zip, 'True': True, 'False': False, 'None': None,
            }

            namespace = {**safe_builtins, **variables}

            result = eval(expression, {"__builtins__": {}}, namespace)
            result_type = type(result).__name__

            self.set_output_value("result", result)
            self.set_output_value("type", result_type)
            self.set_output_value("success", True)
            self.set_output_value("error", "")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result, "type": result_type},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("result", None)
            self.set_output_value("type", "error")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class RunBatchScriptNode(BaseNode):
    """
    Execute a batch script (Windows) or shell script (Unix).

    Config:
        timeout: Execution timeout in seconds (default: 60)
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries in ms (default: 1000)

    Inputs:
        script: Script content to execute
        working_dir: Working directory

    Outputs:
        stdout: Standard output
        stderr: Standard error
        return_code: Process return code
        success: Whether execution succeeded
    """

    def __init__(self, node_id: str, name: str = "Run Batch Script", **kwargs) -> None:
        # Default config with all options
        default_config = {
            "timeout": 60,
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
            "retry_on_nonzero": False,  # Retry if return code is non-zero
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunBatchScriptNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("script", PortType.INPUT, DataType.STRING)
        self.add_input_port("working_dir", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("stdout", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("stderr", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("return_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            script = str(self.get_input_value("script", context) or "")
            working_dir = self.get_input_value("working_dir", context)
            timeout = self.config.get("timeout", 60)

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 1000))
            retry_on_nonzero = self.config.get("retry_on_nonzero", False)

            if not script:
                raise ValueError("script is required")

            # Determine script extension based on platform
            if sys.platform == "win32":
                suffix = ".bat"
            else:
                suffix = ".sh"

            logger.info(f"Running batch script")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1
            script_path = None

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for batch script")

                    # Create temp file for each attempt
                    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
                        if sys.platform != "win32":
                            f.write("#!/bin/bash\n")
                        f.write(script)
                        script_path = f.name

                    try:
                        if sys.platform == "win32":
                            cmd = ["cmd", "/c", script_path]
                        else:
                            os.chmod(script_path, 0o755)
                            cmd = [script_path]

                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=timeout,
                            cwd=working_dir
                        )

                        stdout = result.stdout
                        stderr = result.stderr
                        return_code = result.returncode
                        success = return_code == 0

                    finally:
                        if script_path and os.path.exists(script_path):
                            os.unlink(script_path)
                            script_path = None

                    # Check if we should retry on non-zero return code
                    if not success and retry_on_nonzero and attempts < max_attempts:
                        logger.warning(f"Batch script returned non-zero ({return_code}), retrying...")
                        await asyncio.sleep(retry_interval / 1000)
                        continue

                    self.set_output_value("stdout", stdout)
                    self.set_output_value("stderr", stderr)
                    self.set_output_value("return_code", return_code)
                    self.set_output_value("success", success)
                    self.status = NodeStatus.SUCCESS

                    logger.info(f"Batch script executed: return_code={return_code} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"return_code": return_code, "success": success, "attempts": attempts},
                        "next_nodes": ["exec_out"]
                    }

                except subprocess.TimeoutExpired as e:
                    last_error = e
                    if script_path and os.path.exists(script_path):
                        os.unlink(script_path)
                        script_path = None
                    if attempts < max_attempts:
                        logger.warning(f"Batch script timed out (attempt {attempts})")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

                except Exception as e:
                    last_error = e
                    if script_path and os.path.exists(script_path):
                        os.unlink(script_path)
                        script_path = None
                    if attempts < max_attempts:
                        logger.warning(f"Batch script execution failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            # All attempts failed
            if isinstance(last_error, subprocess.TimeoutExpired):
                self.set_output_value("stdout", "")
                self.set_output_value("stderr", f"Execution timed out after {timeout}s")
                self.set_output_value("return_code", -1)
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                logger.error(f"Batch script execution timed out after {max_attempts} attempts")
                return {"success": False, "error": "Timeout", "next_nodes": []}

            raise last_error

        except Exception as e:
            self.set_output_value("stdout", "")
            self.set_output_value("stderr", str(e))
            self.set_output_value("return_code", -1)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to run batch script: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class RunJavaScriptNode(BaseNode):
    """
    Execute JavaScript code using Node.js.

    Config:
        timeout: Execution timeout in seconds (default: 60)
        node_path: Path to Node.js executable (default: 'node')

    Inputs:
        code: JavaScript code to execute
        input_data: JSON data to pass to script (available as 'inputData')

    Outputs:
        result: Execution result (from console.log)
        success: Whether execution succeeded
        error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Run JavaScript", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunJavaScriptNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("code", PortType.INPUT, DataType.STRING)
        self.add_input_port("input_data", PortType.INPUT, DataType.ANY)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import json

            code = str(self.get_input_value("code", context) or "")
            input_data = self.get_input_value("input_data", context)
            timeout = self.config.get("timeout", 60)
            node_path = self.config.get("node_path", "node")

            if not code:
                raise ValueError("code is required")

            # Create wrapper script
            wrapper = f'''
const inputData = {json.dumps(input_data)};

{code}
'''

            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(wrapper)
                script_path = f.name

            try:
                result = subprocess.run(
                    [node_path, script_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                output = result.stdout.strip()
                error = result.stderr.strip()
                success = result.returncode == 0

            finally:
                os.unlink(script_path)

            self.set_output_value("result", output)
            self.set_output_value("success", success)
            self.set_output_value("error", error)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"success": success},
                "next_nodes": ["exec_out"]
            }

        except FileNotFoundError:
            self.set_output_value("result", "")
            self.set_output_value("success", False)
            self.set_output_value("error", "Node.js not found. Please install Node.js.")
            self.status = NodeStatus.ERROR
            return {"success": False, "error": "Node.js not found", "next_nodes": []}

        except Exception as e:
            self.set_output_value("result", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

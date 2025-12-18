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
from typing import Any, Dict
from pathlib import Path

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@properties(
    PropertyDef(
        "code",
        PropertyType.CODE,
        required=True,
        label="Python Code",
        tooltip="Python code to execute",
    ),
    PropertyDef(
        "variables",
        PropertyType.JSON,
        label="Variables",
        tooltip="Dictionary of variables to pass to the script",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=60,
        min_value=1,
        label="Timeout (seconds)",
        tooltip="Execution timeout in seconds (default: 60)",
    ),
    PropertyDef(
        "isolated",
        PropertyType.BOOLEAN,
        default=False,
        label="Isolated",
        tooltip="Run in isolated subprocess (default: False)",
    ),
)
@node(category="scripts")
class RunPythonScriptNode(BaseNode):
    """
    Execute Python code inline.

    Config (via @properties):
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

    # @category: system
    # @requires: none
    # @ports: code, variables -> result, output, success, error

    def __init__(self, node_id: str, name: str = "Run Python Script", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunPythonScriptNode"

    def _define_ports(self) -> None:
        self.add_input_port("code", DataType.STRING, required=True)
        self.add_input_port("variables", DataType.DICT)
        self.add_output_port("result", DataType.ANY)
        self.add_output_port("output", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            code = str(self.get_parameter("code", ""))
            variables = self.get_parameter("variables", {})
            timeout = self.get_parameter("timeout", 60)
            isolated = self.get_parameter("isolated", False)

            code = context.resolve_value(code)

            if not code:
                raise ValueError("code is required")

            if not isinstance(variables, dict):
                variables = {}

            if isolated:
                result, output, error = await self._run_isolated(
                    code, variables, timeout
                )
            else:
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
                "next_nodes": ["exec_out"],
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

        output_buffer = io.StringIO()

        namespace = {"__builtins__": __builtins__, "result": None, **variables}

        error = ""
        result = None

        try:
            with redirect_stdout(output_buffer):
                exec(code, namespace)

            result = namespace.get("result")
            output = output_buffer.getvalue()

        except Exception as e:
            error = str(e)
            output = output_buffer.getvalue()

        return result, output, error

    async def _run_isolated(
        self, code: str, variables: Dict[str, Any], timeout: int
    ) -> tuple[Any, str, str]:
        """Execute Python code in isolated subprocess."""
        import json

        wrapper = f"""
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
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(wrapper)
            script_path = f.name

        try:
            proc = subprocess.run(
                [sys.executable, script_path, json.dumps(variables)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = proc.stdout
            error = proc.stderr

            result = None
            if "__RESULT__:" in output:
                result_line = [
                    line
                    for line in output.split("\n")
                    if line.startswith("__RESULT__:")
                ]
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


@properties(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        tooltip="Path to Python file",
    ),
    PropertyDef(
        "args",
        PropertyType.ANY,
        label="Arguments",
        tooltip="Command line arguments (list or string)",
    ),
    PropertyDef(
        "working_dir",
        PropertyType.DIRECTORY_PATH,
        label="Working Directory",
        tooltip="Working directory for execution",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=60,
        min_value=1,
        label="Timeout (seconds)",
        tooltip="Execution timeout in seconds (default: 60)",
    ),
    PropertyDef(
        "python_path",
        PropertyType.STRING,
        default=sys.executable,
        label="Python Path",
        tooltip="Python interpreter path (default: current)",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retries on failure (default: 0)",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in ms (default: 1000)",
    ),
    PropertyDef(
        "retry_on_nonzero",
        PropertyType.BOOLEAN,
        default=False,
        label="Retry on Non-Zero",
        tooltip="Retry if return code is non-zero (default: False)",
    ),
)
@node(category="scripts")
class RunPythonFileNode(BaseNode):
    """
    Execute a Python file.

    Config (via @properties):
        timeout: Execution timeout in seconds (default: 60)
        python_path: Python interpreter path (default: current)
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries in ms (default: 1000)
        retry_on_nonzero: Retry if return code is non-zero (default: False)

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

    # @category: system
    # @requires: none
    # @ports: file_path, args, working_dir -> stdout, stderr, return_code, success

    def __init__(self, node_id: str, name: str = "Run Python File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunPythonFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_input_port("args", DataType.ANY)
        self.add_input_port("working_dir", DataType.STRING)
        self.add_output_port("stdout", DataType.STRING)
        self.add_output_port("stderr", DataType.STRING)
        self.add_output_port("return_code", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = str(self.get_parameter("file_path", ""))
            args = self.get_parameter("args")
            working_dir = self.get_parameter("working_dir")
            timeout = self.get_parameter("timeout", 60)
            python_path = self.get_parameter("python_path", sys.executable)
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            retry_on_nonzero = self.get_parameter("retry_on_nonzero", False)

            file_path = context.resolve_value(file_path)
            python_path = context.resolve_value(python_path)
            if working_dir:
                working_dir = context.resolve_value(working_dir)

            if not file_path:
                raise ValueError("file_path is required")

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Python file not found: {file_path}")

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
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for Python file execution"
                        )

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=working_dir,
                    )

                    stdout = result.stdout
                    stderr = result.stderr
                    return_code = result.returncode
                    success = return_code == 0

                    if not success and retry_on_nonzero and attempts < max_attempts:
                        logger.warning(
                            f"Python file returned non-zero ({return_code}), retrying..."
                        )
                        await asyncio.sleep(retry_interval / 1000)
                        continue

                    self.set_output_value("stdout", stdout)
                    self.set_output_value("stderr", stderr)
                    self.set_output_value("return_code", return_code)
                    self.set_output_value("success", success)
                    self.status = NodeStatus.SUCCESS

                    logger.info(
                        f"Python file executed: return_code={return_code} (attempt {attempts})"
                    )

                    return {
                        "success": True,
                        "data": {
                            "return_code": return_code,
                            "success": success,
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
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
                        logger.warning(
                            f"Python file execution failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            if isinstance(last_error, subprocess.TimeoutExpired):
                self.set_output_value("stdout", "")
                self.set_output_value("stderr", f"Execution timed out after {timeout}s")
                self.set_output_value("return_code", -1)
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                logger.error(
                    f"Python file execution timed out after {max_attempts} attempts"
                )
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


@properties(
    PropertyDef(
        "expression",
        PropertyType.STRING,
        default="",
        required=True,
        label="Expression",
        tooltip="Python expression to evaluate (e.g., '{{num1}} + {{num2}}')",
    ),
)
@node(category="scripts")
class EvalExpressionNode(BaseNode):
    """
    Evaluate a Python expression and return the result.

    Config (via @properties):
        expression: Python expression to evaluate (supports {{variable}} syntax)

    Outputs:
        result: Expression result
        type: Result type name
        success: Whether evaluation succeeded
        error: Error message if failed
    """

    # @category: system
    # @requires: none
    # @ports: -> result, type, success, error

    def __init__(self, node_id: str, name: str = "Eval Expression", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "EvalExpressionNode"

    def _define_ports(self) -> None:
        # expression is now a PropertyDef, not an input port
        self.add_output_port("result", DataType.ANY)
        self.add_output_port("type", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            expression = str(self.get_parameter("expression", ""))
            variables = self.get_parameter("variables", {})

            expression = context.resolve_value(expression)

            if not expression:
                raise ValueError("expression is required")

            if not isinstance(variables, dict):
                variables = {}

            safe_builtins = {
                "abs": abs,
                "all": all,
                "any": any,
                "bin": bin,
                "bool": bool,
                "chr": chr,
                "dict": dict,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "format": format,
                "hex": hex,
                "int": int,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "oct": oct,
                "ord": ord,
                "pow": pow,
                "range": range,
                "repr": repr,
                "reversed": reversed,
                "round": round,
                "set": set,
                "slice": slice,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "type": type,
                "zip": zip,
                "True": True,
                "False": False,
                "None": None,
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
                "next_nodes": ["exec_out"],
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


@properties(
    PropertyDef(
        "script",
        PropertyType.TEXT,
        required=True,
        label="Script",
        tooltip="Script content to execute",
    ),
    PropertyDef(
        "working_dir",
        PropertyType.DIRECTORY_PATH,
        label="Working Directory",
        tooltip="Working directory for execution",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=60,
        min_value=1,
        label="Timeout (seconds)",
        tooltip="Execution timeout in seconds (default: 60)",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retries on failure (default: 0)",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retries in ms (default: 1000)",
    ),
    PropertyDef(
        "retry_on_nonzero",
        PropertyType.BOOLEAN,
        default=False,
        label="Retry on Non-Zero",
        tooltip="Retry if return code is non-zero (default: False)",
    ),
)
@node(category="scripts")
class RunBatchScriptNode(BaseNode):
    """
    Execute a batch script (Windows) or shell script (Unix).

    Config (via @properties):
        script: Script content to execute
        timeout: Execution timeout in seconds (default: 60)
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries in ms (default: 1000)
        retry_on_nonzero: Retry if return code is non-zero (default: False)

    Inputs:
        script: Script content to execute
        working_dir: Working directory

    Outputs:
        stdout: Standard output
        stderr: Standard error
        return_code: Process return code
        success: Whether execution succeeded
    """

    # @category: system
    # @requires: none
    # @ports: script, working_dir -> stdout, stderr, return_code, success

    def __init__(self, node_id: str, name: str = "Run Batch Script", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunBatchScriptNode"

    def _define_ports(self) -> None:
        self.add_input_port("script", DataType.STRING, required=True)
        self.add_input_port("working_dir", DataType.STRING)
        self.add_output_port("stdout", DataType.STRING)
        self.add_output_port("stderr", DataType.STRING)
        self.add_output_port("return_code", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            script = str(self.get_parameter("script", ""))
            working_dir = self.get_parameter("working_dir")
            timeout = self.get_parameter("timeout", 60)
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)
            retry_on_nonzero = self.get_parameter("retry_on_nonzero", False)

            script = context.resolve_value(script)
            if working_dir:
                working_dir = context.resolve_value(working_dir)

            if not script:
                raise ValueError("script is required")

            if sys.platform == "win32":
                suffix = ".bat"
            else:
                suffix = ".sh"

            logger.info("Running batch script")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1
            script_path = None

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for batch script"
                        )

                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=suffix, delete=False
                    ) as f:
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
                            cwd=working_dir,
                        )

                        stdout = result.stdout
                        stderr = result.stderr
                        return_code = result.returncode
                        success = return_code == 0

                    finally:
                        if script_path and os.path.exists(script_path):
                            os.unlink(script_path)
                            script_path = None

                    if not success and retry_on_nonzero and attempts < max_attempts:
                        logger.warning(
                            f"Batch script returned non-zero ({return_code}), retrying..."
                        )
                        await asyncio.sleep(retry_interval / 1000)
                        continue

                    self.set_output_value("stdout", stdout)
                    self.set_output_value("stderr", stderr)
                    self.set_output_value("return_code", return_code)
                    self.set_output_value("success", success)
                    self.status = NodeStatus.SUCCESS

                    logger.info(
                        f"Batch script executed: return_code={return_code} (attempt {attempts})"
                    )

                    return {
                        "success": True,
                        "data": {
                            "return_code": return_code,
                            "success": success,
                            "attempts": attempts,
                        },
                        "next_nodes": ["exec_out"],
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
                        logger.warning(
                            f"Batch script execution failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            if isinstance(last_error, subprocess.TimeoutExpired):
                self.set_output_value("stdout", "")
                self.set_output_value("stderr", f"Execution timed out after {timeout}s")
                self.set_output_value("return_code", -1)
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                logger.error(
                    f"Batch script execution timed out after {max_attempts} attempts"
                )
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


@properties(
    PropertyDef(
        "code",
        PropertyType.TEXT,
        required=True,
        label="JavaScript Code",
        tooltip="JavaScript code to execute",
    ),
    PropertyDef(
        "input_data",
        PropertyType.ANY,
        label="Input Data",
        tooltip="JSON data to pass to script (available as 'inputData')",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=60,
        min_value=1,
        label="Timeout (seconds)",
        tooltip="Execution timeout in seconds (default: 60)",
    ),
    PropertyDef(
        "node_path",
        PropertyType.STRING,
        default="node",
        label="Node.js Path",
        tooltip="Path to Node.js executable (default: 'node')",
    ),
)
@node(category="scripts")
class RunJavaScriptNode(BaseNode):
    """
    Execute JavaScript code using Node.js.

    Config (via @properties):
        code: JavaScript code to execute
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

    # @category: system
    # @requires: none
    # @ports: code, input_data -> result, success, error

    def __init__(self, node_id: str, name: str = "Run JavaScript", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunJavaScriptNode"

    def _define_ports(self) -> None:
        self.add_input_port("code", DataType.STRING, required=True)
        self.add_input_port("input_data", DataType.ANY)
        self.add_output_port("result", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import json

            code = str(self.get_parameter("code", ""))
            input_data = self.get_parameter("input_data")
            timeout = self.get_parameter("timeout", 60)
            node_path = self.get_parameter("node_path", "node")

            code = context.resolve_value(code)
            node_path = context.resolve_value(node_path)

            if not code:
                raise ValueError("code is required")

            wrapper = f"""
const inputData = {json.dumps(input_data)};

{code}
"""

            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(wrapper)
                script_path = f.name

            try:
                result = subprocess.run(
                    [node_path, script_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
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
                "next_nodes": ["exec_out"],
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

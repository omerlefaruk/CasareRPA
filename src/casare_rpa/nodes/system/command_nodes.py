"""
Terminal and command execution nodes for CasareRPA.

This module provides nodes for executing system commands:
- Run shell/CMD commands
- Run PowerShell scripts
"""

import subprocess

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


class SecurityError(Exception):
    """Raised when a security check fails."""

    pass


@properties(
    PropertyDef(
        "command",
        PropertyType.STRING,
        default="",
        label="Command",
        tooltip="Command to execute",
        required=True,
    ),
    PropertyDef(
        "args",
        PropertyType.STRING,
        default="",
        label="Arguments",
        tooltip="Command arguments",
    ),
    PropertyDef(
        "shell",
        PropertyType.BOOLEAN,
        default=False,
        label="Use Shell",
        tooltip="Use shell execution (less secure)",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=60,
        min_value=1,
        label="Timeout (seconds)",
        tooltip="Command timeout in seconds",
    ),
    PropertyDef(
        "working_dir",
        PropertyType.STRING,
        default="",
        label="Working Directory",
        tooltip="Working directory for command execution",
    ),
    PropertyDef(
        "capture_output",
        PropertyType.BOOLEAN,
        default=True,
        label="Capture Output",
        tooltip="Capture stdout and stderr",
    ),
    PropertyDef(
        "allow_dangerous",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Commands",
        tooltip="Allow blocked commands and dangerous characters (NOT RECOMMENDED)",
    ),
)
@node(category="system")
class RunCommandNode(BaseNode):
    """
    Run a terminal/CMD command.

    Config (via @properties):
        shell: Use shell execution (default: False for security)
        timeout: Command timeout in seconds (default: 60)
        working_dir: Working directory (default: current)
        capture_output: Capture stdout/stderr (default: True)
        allow_dangerous: Allow dangerous commands (default: False)

    Inputs:
        command: Command to execute
        args: Additional arguments (list or string)

    Outputs:
        stdout: Standard output
        stderr: Standard error
        return_code: Process return code
        success: Whether command succeeded (return_code == 0)
    """

    # @category: system
    # @requires: none
    # @ports: command, args -> stdout, stderr, return_code, success

    # SECURITY: Dangerous shell metacharacters that enable command injection
    DANGEROUS_CHARS = [
        "|",
        "&",
        ";",
        "$",
        "`",
        "(",
        ")",
        "{",
        "}",
        "<",
        ">",
        "\n",
        "\r",
    ]

    # SECURITY: Commands that should never be executed via workflows
    BLOCKED_COMMANDS = [
        "rm",
        "del",
        "format",
        "fdisk",
        "mkfs",  # Destructive
        "wget",
        "curl",
        "invoke-webrequest",  # Network download
        "nc",
        "netcat",
        "ncat",  # Network tools
        "powershell",
        "pwsh",
        "cmd",  # Shell spawning (use dedicated nodes)
        "reg",
        "regedit",  # Registry modification
        "net",
        "sc",  # Service/network management
        "shutdown",
        "reboot",  # System control
    ]

    def __init__(self, node_id: str, name: str = "Run Command", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunCommandNode"

    def _define_ports(self) -> None:
        self.add_input_port("command", DataType.STRING)
        self.add_input_port("args", DataType.ANY)
        self.add_output_port("stdout", DataType.STRING)
        self.add_output_port("stderr", DataType.STRING)
        self.add_output_port("return_code", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        import shlex

        try:
            command = str(self.get_input_value("command", context) or "")
            args = self.get_input_value("args", context)
            shell = self.get_parameter("shell", False)
            timeout = self.get_parameter("timeout", 60)
            working_dir = self.get_parameter("working_dir", "")
            capture_output = self.get_parameter("capture_output", True)
            allow_dangerous = self.get_parameter("allow_dangerous", False)

            # Resolve {{variable}} patterns

            if not command:
                raise ValueError("command is required")

            # SECURITY: Extract base command for validation
            base_cmd = command.split()[0].lower() if command else ""
            base_cmd = base_cmd.replace(".exe", "").replace(".cmd", "").replace(".bat", "")

            # SECURITY: Block dangerous commands unless explicitly allowed
            if not allow_dangerous:
                if base_cmd in self.BLOCKED_COMMANDS:
                    raise SecurityError(
                        f"Command '{base_cmd}' is blocked for security reasons. "
                        f"Set allow_dangerous=True in config to override (not recommended)."
                    )

                # SECURITY: Check for dangerous characters when shell=True
                if shell:
                    for char in self.DANGEROUS_CHARS:
                        if char in command or (isinstance(args, str) and char in args):
                            raise SecurityError(
                                f"Dangerous character '{char}' detected in command. "
                                f"This could enable command injection. "
                                f"Use shell=False or set allow_dangerous=True to override."
                            )

            # SECURITY: Build command safely
            if shell:
                # When shell=True, concatenate as string (less safe)
                if args:
                    if isinstance(args, list):
                        command = command + " " + " ".join(shlex.quote(str(a)) for a in args)
                    elif isinstance(args, str):
                        command = command + " " + args
                logger.warning(f"RunCommandNode executing with shell=True: {command[:100]}...")
            else:
                # When shell=False, build command list (safer)
                if isinstance(command, str):
                    try:
                        cmd_list = shlex.split(command)
                    except ValueError:
                        cmd_list = command.split()
                else:
                    cmd_list = list(command)

                if args:
                    if isinstance(args, list):
                        cmd_list.extend(str(a) for a in args)
                    elif isinstance(args, str):
                        try:
                            cmd_list.extend(shlex.split(args))
                        except ValueError:
                            cmd_list.extend(args.split())

                command = cmd_list

            # Log command execution for audit
            logger.info(f"RunCommandNode executing: {str(command)[:200]}...")

            # Run command
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=working_dir if working_dir else None,
            )

            stdout = result.stdout if capture_output else ""
            stderr = result.stderr if capture_output else ""
            return_code = result.returncode
            success = return_code == 0

            self.set_output_value("stdout", stdout)
            self.set_output_value("stderr", stderr)
            self.set_output_value("return_code", return_code)
            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"return_code": return_code, "success": success},
                "next_nodes": ["exec_out"],
            }

        except subprocess.TimeoutExpired:
            timeout_val = self.get_parameter("timeout", 60)
            self.set_output_value("stdout", "")
            self.set_output_value("stderr", f"Command timed out after {timeout_val}s")
            self.set_output_value("return_code", -1)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": f"Command timed out after {timeout_val}s",
                "next_nodes": [],
            }

        except Exception as e:
            self.set_output_value("stdout", "")
            self.set_output_value("stderr", str(e))
            self.set_output_value("return_code", -1)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "script",
        PropertyType.STRING,
        default="",
        label="Script",
        tooltip="PowerShell script or command",
        required=True,
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=60,
        min_value=1,
        label="Timeout (seconds)",
        tooltip="Command timeout in seconds",
    ),
    PropertyDef(
        "execution_policy",
        PropertyType.CHOICE,
        default="RemoteSigned",
        choices=["RemoteSigned", "Bypass", "Unrestricted", "AllSigned", "Restricted"],
        label="Execution Policy",
        tooltip="PowerShell execution policy",
    ),
    PropertyDef(
        "allow_dangerous",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Commands",
        tooltip="Allow dangerous PowerShell patterns (NOT RECOMMENDED)",
    ),
    PropertyDef(
        "constrained_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Constrained Language Mode",
        tooltip="Use PowerShell Constrained Language Mode for additional security",
    ),
)
@node(category="system")
class RunPowerShellNode(BaseNode):
    """
    Run a PowerShell script or command.

    Config (via @properties):
        timeout: Command timeout in seconds (default: 60)
        execution_policy: 'Bypass', 'Unrestricted', etc. (default: RemoteSigned)
        allow_dangerous: Allow dangerous commands (default: False)
        constrained_mode: Use PowerShell Constrained Language Mode (default: False)

    Inputs:
        script: PowerShell script or command

    Outputs:
        stdout: Standard output
        stderr: Standard error
        return_code: Process return code
        success: Whether command succeeded
    """

    # @category: system
    # @requires: none
    # @ports: script -> stdout, stderr, return_code, success

    # SECURITY: Dangerous PowerShell commands/patterns that could be malicious
    DANGEROUS_PATTERNS = [
        # Download and execute
        "invoke-webrequest",
        "iwr",
        "wget",
        "curl",
        "invoke-restmethod",
        "irm",
        "downloadstring",
        "downloadfile",
        "start-bitstransfer",
        # Code execution
        "invoke-expression",
        "iex",
        "invoke-command",
        "icm",
        "start-process",
        "saps",
        # Credential theft
        "get-credential",
        "convertto-securestring",
        "export-clixml",
        # System modification
        "set-executionpolicy",
        "new-service",
        "set-service",
        "new-scheduledtask",
        "register-scheduledjob",
        # Registry
        "set-itemproperty",
        "new-itemproperty",
        "remove-itemproperty",
        # Encoding (often used for obfuscation)
        "-encodedcommand",
        "-enc",
        "-e",
        "fromb64string",
        "tob64string",
        # Reflection/Assembly loading
        "add-type",
        "reflection.assembly",
        "[system.reflection",
    ]

    def __init__(self, node_id: str, name: str = "Run PowerShell", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunPowerShellNode"

    def _define_ports(self) -> None:
        self.add_input_port("script", DataType.STRING)
        self.add_output_port("stdout", DataType.STRING)
        self.add_output_port("stderr", DataType.STRING)
        self.add_output_port("return_code", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            script = str(self.get_input_value("script", context) or "")
            timeout = self.get_parameter("timeout", 60)
            execution_policy = self.get_parameter("execution_policy", "RemoteSigned")
            allow_dangerous = self.get_parameter("allow_dangerous", False)
            constrained_mode = self.get_parameter("constrained_mode", False)

            # Resolve {{variable}} patterns in script

            if not script:
                raise ValueError("script is required")

            # SECURITY: Check for dangerous patterns unless explicitly allowed
            if not allow_dangerous:
                script_lower = script.lower()
                for pattern in self.DANGEROUS_PATTERNS:
                    if pattern in script_lower:
                        raise SecurityError(
                            f"Dangerous PowerShell pattern '{pattern}' detected in script. "
                            f"Set allow_dangerous=True in config to override (not recommended)."
                        )

            # SECURITY: Log all PowerShell executions for audit
            logger.warning(
                f"RunPowerShellNode executing script (policy={execution_policy}, "
                f"constrained={constrained_mode}): {script[:200]}..."
            )

            # Build PowerShell command
            ps_cmd = [
                "powershell.exe",
                "-ExecutionPolicy",
                execution_policy,
                "-NoProfile",
                "-NonInteractive",  # SECURITY: Prevent interactive prompts
            ]

            # SECURITY: Add Constrained Language Mode if requested
            if constrained_mode:
                script = (
                    f"$ExecutionContext.SessionState.LanguageMode = "
                    f'"ConstrainedLanguage"; {script}'
                )

            ps_cmd.extend(["-Command", script])

            result = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=timeout)

            stdout = result.stdout
            stderr = result.stderr
            return_code = result.returncode
            success = return_code == 0

            self.set_output_value("stdout", stdout)
            self.set_output_value("stderr", stderr)
            self.set_output_value("return_code", return_code)
            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"return_code": return_code, "success": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("stdout", "")
            self.set_output_value("stderr", str(e))
            self.set_output_value("return_code", -1)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

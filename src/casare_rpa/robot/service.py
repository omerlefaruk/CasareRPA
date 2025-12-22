"""
Windows Service Wrapper for CasareRPA Robot Agent.

Allows the robot agent to run as a Windows Service with proper
lifecycle management, event logging, and service control.

Usage:
    # Install service (requires admin)
    python -m casare_rpa.robot.service install

    # Start service
    python -m casare_rpa.robot.service start

    # Stop service
    python -m casare_rpa.robot.service stop

    # Remove service
    python -m casare_rpa.robot.service remove

    # Debug mode (run as console)
    python -m casare_rpa.robot.service debug

Service Name: CasareRPARobot
Display Name: CasareRPA Robot Agent
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Check if we're on Windows
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager

        PYWIN32_AVAILABLE = True
    except ImportError:
        PYWIN32_AVAILABLE = False
        win32serviceutil = None
        win32service = None
        win32event = None
        servicemanager = None
else:
    PYWIN32_AVAILABLE = False
    win32serviceutil = None
    win32service = None
    win32event = None
    servicemanager = None

from loguru import logger


# Service configuration
SERVICE_NAME = "CasareRPARobot"
SERVICE_DISPLAY_NAME = "CasareRPA Robot Agent"
SERVICE_DESCRIPTION = (
    "CasareRPA distributed robot agent for automated workflow execution. "
    "Connects to the CasareRPA orchestrator to receive and execute jobs."
)
SERVICE_START_TYPE = win32service.SERVICE_AUTO_START if win32service else None

# Default config path
DEFAULT_CONFIG_PATH = Path(
    os.environ.get("CASARE_CONFIG_PATH", str(Path.home() / ".casare_rpa" / "robot_config.yaml"))
)


def get_service_config() -> dict:
    """Load service configuration from file or environment."""
    config = {
        "robot_id": os.environ.get("CASARE_ROBOT_ID"),
        "robot_name": os.environ.get("CASARE_ROBOT_NAME", SERVICE_NAME),
        "postgres_url": os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL"),
        "environment": os.environ.get("CASARE_ENVIRONMENT", "default"),
        "max_concurrent_jobs": int(os.environ.get("CASARE_MAX_CONCURRENT_JOBS", "1")),
        "poll_interval_seconds": float(os.environ.get("CASARE_POLL_INTERVAL", "1.0")),
    }

    # Try to load from config file
    if DEFAULT_CONFIG_PATH.exists():
        try:
            import yaml

            file_config = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text())
            config.update(file_config)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")

    return config


if PYWIN32_AVAILABLE:

    class CasareRobotService(win32serviceutil.ServiceFramework):
        """
        Windows Service implementation for CasareRPA Robot Agent.

        Handles service lifecycle events and manages the robot agent
        in a Windows service context.
        """

        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY_NAME
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args):
            """Initialize the service."""
            win32serviceutil.ServiceFramework.__init__(self, args)

            # Create stop event
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.is_alive = True

            # Agent instance
            self.agent = None
            self.loop = None

            # Setup logging to Windows Event Log
            self._setup_event_logging()

        def _setup_event_logging(self):
            """Configure logging to Windows Event Log and file."""
            log_dir = Path.home() / ".casare_rpa" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            # File logging
            logger.remove()
            logger.add(
                str(log_dir / "service_{time}.log"),
                rotation="1 day",
                retention="7 days",
                compression="zip",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message}",
                level="DEBUG",
            )

            # Also log to Windows Event Log
            try:
                import win32evtlogutil
                import win32evtlog

                def event_log_handler(message):
                    """Log to Windows Event Log."""
                    try:
                        win32evtlogutil.ReportEvent(
                            SERVICE_NAME,
                            0,
                            eventCategory=0,
                            eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE,
                            strings=[str(message.record["message"])],
                        )
                    except Exception:
                        pass

                logger.add(
                    event_log_handler,
                    level="INFO",
                    format="{message}",
                )
            except ImportError:
                pass

        def SvcStop(self):
            """Handle service stop request."""
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            logger.info("Service stop requested")

            self.is_alive = False
            win32event.SetEvent(self.stop_event)

            # Stop agent gracefully
            if self.agent and self.loop:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.agent.stop(),
                        self.loop,
                    )
                    future.result(timeout=60)
                except Exception as e:
                    logger.error(f"Error stopping agent: {e}")

        def SvcDoRun(self):
            """Main service execution entry point."""
            try:
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, ""),
                )

                logger.info(f"Starting {SERVICE_DISPLAY_NAME}")
                self._run_agent()

                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STOPPED,
                    (self._svc_name_, ""),
                )
                logger.info(f"Stopped {SERVICE_DISPLAY_NAME}")

            except Exception as e:
                logger.exception(f"Service error: {e}")
                servicemanager.LogErrorMsg(f"{SERVICE_NAME} error: {e}")

        def _run_agent(self):
            """Run the robot agent."""
            from casare_rpa.robot.agent import RobotAgent, RobotConfig

            # Load configuration
            config_data = get_service_config()

            if not config_data.get("postgres_url"):
                logger.error("POSTGRES_URL not configured. Service cannot start.")
                return

            config = RobotConfig(
                robot_id=config_data.get("robot_id"),
                robot_name=config_data.get("robot_name"),
                postgres_url=config_data["postgres_url"],
                environment=config_data.get("environment", "default"),
                max_concurrent_jobs=config_data.get("max_concurrent_jobs", 1),
                poll_interval_seconds=config_data.get("poll_interval_seconds", 1.0),
            )

            # Create and run agent in event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            try:
                self.agent = RobotAgent(config)
                self.loop.run_until_complete(self._agent_main())
            finally:
                self.loop.close()

        async def _agent_main(self):
            """Async main loop for the agent."""
            await self.agent.start()

            # Wait for stop event
            while self.is_alive:
                await asyncio.sleep(1)
                if win32event.WaitForSingleObject(self.stop_event, 0) == win32event.WAIT_OBJECT_0:
                    break

            await self.agent.stop()


def install_service() -> bool:
    """
    Install the Windows service.

    Returns:
        True if installation successful.
    """
    if not IS_WINDOWS:
        print("Windows service installation is only available on Windows.")
        return False

    if not PYWIN32_AVAILABLE:
        print("pywin32 is required for Windows service support.")
        print("Install with: pip install pywin32")
        return False

    try:
        # Get the Python executable and script path
        os.path.abspath(__file__)

        # Install the service
        win32serviceutil.InstallService(
            pythonClassString=f"{__name__}.CasareRobotService",
            serviceName=SERVICE_NAME,
            displayName=SERVICE_DISPLAY_NAME,
            description=SERVICE_DESCRIPTION,
            startType=SERVICE_START_TYPE,
        )

        print(f"Service '{SERVICE_NAME}' installed successfully.")
        print("\nTo start the service:")
        print(f"  net start {SERVICE_NAME}")
        print("  - or -")
        print("  python -m casare_rpa.robot.service start")
        return True

    except Exception as e:
        print(f"Failed to install service: {e}")
        print("\nMake sure you are running as Administrator.")
        return False


def remove_service() -> bool:
    """
    Remove the Windows service.

    Returns:
        True if removal successful.
    """
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        print("Windows service is only available on Windows with pywin32.")
        return False

    try:
        # Stop service first if running
        try:
            win32serviceutil.StopService(SERVICE_NAME)
            print(f"Service '{SERVICE_NAME}' stopped.")
        except Exception:
            pass

        # Remove the service
        win32serviceutil.RemoveService(SERVICE_NAME)
        print(f"Service '{SERVICE_NAME}' removed successfully.")
        return True

    except Exception as e:
        print(f"Failed to remove service: {e}")
        print("\nMake sure you are running as Administrator.")
        return False


def start_service() -> bool:
    """
    Start the Windows service.

    Returns:
        True if start successful.
    """
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        print("Windows service is only available on Windows with pywin32.")
        return False

    try:
        win32serviceutil.StartService(SERVICE_NAME)
        print(f"Service '{SERVICE_NAME}' started.")
        return True
    except Exception as e:
        print(f"Failed to start service: {e}")
        return False


def stop_service() -> bool:
    """
    Stop the Windows service.

    Returns:
        True if stop successful.
    """
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        print("Windows service is only available on Windows with pywin32.")
        return False

    try:
        win32serviceutil.StopService(SERVICE_NAME)
        print(f"Service '{SERVICE_NAME}' stopped.")
        return True
    except Exception as e:
        print(f"Failed to stop service: {e}")
        return False


def restart_service() -> bool:
    """
    Restart the Windows service.

    Returns:
        True if restart successful.
    """
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        print("Windows service is only available on Windows with pywin32.")
        return False

    try:
        win32serviceutil.RestartService(SERVICE_NAME)
        print(f"Service '{SERVICE_NAME}' restarted.")
        return True
    except Exception as e:
        print(f"Failed to restart service: {e}")
        return False


def service_status() -> Optional[str]:
    """
    Get the Windows service status.

    Returns:
        Status string or None if error.
    """
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        print("Windows service is only available on Windows with pywin32.")
        return None

    try:
        status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)

        status_map = {
            win32service.SERVICE_STOPPED: "Stopped",
            win32service.SERVICE_START_PENDING: "Starting...",
            win32service.SERVICE_STOP_PENDING: "Stopping...",
            win32service.SERVICE_RUNNING: "Running",
            win32service.SERVICE_CONTINUE_PENDING: "Resuming...",
            win32service.SERVICE_PAUSE_PENDING: "Pausing...",
            win32service.SERVICE_PAUSED: "Paused",
        }

        state = status[1]
        status_str = status_map.get(state, f"Unknown ({state})")
        print(f"Service '{SERVICE_NAME}': {status_str}")
        return status_str

    except Exception as e:
        print(f"Failed to query service status: {e}")
        return None


def debug_service():
    """Run the service in debug/console mode."""
    print(f"Running {SERVICE_DISPLAY_NAME} in debug mode...")
    print("Press Ctrl+C to stop.\n")

    # Configure logging for console
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
    )

    from casare_rpa.robot.agent import RobotConfig, run_agent

    config_data = get_service_config()

    if not config_data.get("postgres_url"):
        print("Error: POSTGRES_URL not configured.")
        print("Set environment variable or create config file at:")
        print(f"  {DEFAULT_CONFIG_PATH}")
        return

    config = RobotConfig(
        robot_id=config_data.get("robot_id"),
        robot_name=config_data.get("robot_name"),
        postgres_url=config_data["postgres_url"],
        environment=config_data.get("environment", "default"),
        max_concurrent_jobs=config_data.get("max_concurrent_jobs", 1),
        poll_interval_seconds=config_data.get("poll_interval_seconds", 1.0),
    )

    try:
        asyncio.run(run_agent(config))
    except KeyboardInterrupt:
        print("\nShutdown requested.")


def print_usage():
    """Print usage information."""
    print(f"""
CasareRPA Robot Agent - Windows Service Manager

Usage: python -m casare_rpa.robot.service <command>

Commands:
  install     Install the Windows service (requires admin)
  remove      Remove the Windows service (requires admin)
  start       Start the service
  stop        Stop the service
  restart     Restart the service
  status      Show service status
  debug       Run in console/debug mode (no service)

Service Name: {SERVICE_NAME}
Config File:  {DEFAULT_CONFIG_PATH}

Environment Variables:
  POSTGRES_URL              PostgreSQL connection URL (required)
  CASARE_ROBOT_ID           Robot identifier
  CASARE_ROBOT_NAME         Robot display name
  CASARE_ENVIRONMENT        Environment name (default: 'default')
  CASARE_MAX_CONCURRENT_JOBS Maximum concurrent jobs (default: 1)
  CASARE_CONFIG_PATH        Config file path (default: ~/.casare_rpa/robot_config.yaml)

Examples:
  # Install and start (run as Administrator)
  python -m casare_rpa.robot.service install
  python -m casare_rpa.robot.service start

  # Check status
  python -m casare_rpa.robot.service status

  # Test without installing as service
  python -m casare_rpa.robot.service debug
""")


def main():
    """Main entry point for service management."""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "install":
        install_service()
    elif command == "remove":
        remove_service()
    elif command == "start":
        start_service()
    elif command == "stop":
        stop_service()
    elif command == "restart":
        restart_service()
    elif command == "status":
        service_status()
    elif command == "debug":
        debug_service()
    elif command in ("-h", "--help", "help"):
        print_usage()
    else:
        # If running as service (by Windows SCM)
        if IS_WINDOWS and PYWIN32_AVAILABLE:
            win32serviceutil.HandleCommandLine(CasareRobotService)
        else:
            print(f"Unknown command: {command}")
            print_usage()


if __name__ == "__main__":
    main()

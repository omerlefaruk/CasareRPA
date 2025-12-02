"""
CasareRPA Robot Agent Entry Point.

Standalone robot agent that connects to an orchestrator via WebSocket
and executes workflow jobs. Runs headless without requiring a GUI.

Usage:
    # From command line
    python -m casare_rpa.agent_main

    # With specific config file
    python -m casare_rpa.agent_main --config /path/to/config.json

Environment Variables:
    CASARE_ROBOT_NAME - Robot name (required)
    CASARE_CONTROL_PLANE_URL - WebSocket URL (required)
    CASARE_ROBOT_ID - Optional robot ID (auto-generated if not set)
    CASARE_HEARTBEAT_INTERVAL - Heartbeat interval in seconds (default: 30)
    CASARE_MAX_CONCURRENT_JOBS - Max concurrent jobs (default: 1)
    CASARE_CAPABILITIES - Comma-separated capabilities
    CASARE_TAGS - Comma-separated tags
    CASARE_ENVIRONMENT - Environment name (default: production)
    CASARE_WORK_DIR - Working directory
    CASARE_LOG_LEVEL - Log level (default: INFO)
    CASARE_CA_CERT_PATH - CA certificate path for mTLS
    CASARE_CLIENT_CERT_PATH - Client certificate path for mTLS
    CASARE_CLIENT_KEY_PATH - Client key path for mTLS

Example config.json:
    {
        "robot_name": "Production Robot 1",
        "control_plane_url": "wss://orchestrator.example.com/ws/robot",
        "max_concurrent_jobs": 2,
        "capabilities": ["browser", "desktop"],
        "tags": ["production", "team-a"],
        "environment": "production"
    }
"""

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load .env file before importing config
load_dotenv()

from casare_rpa.infrastructure.agent.robot_config import RobotConfig, ConfigurationError
from casare_rpa.infrastructure.agent.robot_agent import RobotAgent


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure loguru logger for agent operation.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Add file handler for persistent logs
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "robot_agent_{time:YYYY-MM-DD}.log",
        level=log_level.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="7 days",
        compression="zip",
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CasareRPA Robot Agent - Workflow execution worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variables
  export CASARE_ROBOT_NAME="Robot-1"
  export CASARE_CONTROL_PLANE_URL="wss://orchestrator.example.com/ws/robot"
  python -m casare_rpa.agent_main

  # Using config file
  python -m casare_rpa.agent_main --config ./robot_config.json

  # Override log level
  python -m casare_rpa.agent_main --log-level DEBUG
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to JSON configuration file",
    )

    parser.add_argument(
        "--robot-name",
        type=str,
        help="Robot name (overrides env/config)",
    )

    parser.add_argument(
        "--control-plane-url",
        type=str,
        help="WebSocket URL for orchestrator (overrides env/config)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and exit",
    )

    return parser.parse_args()


def load_config(args: argparse.Namespace) -> RobotConfig:
    """
    Load configuration from file, environment, or command line.

    Priority (highest first):
    1. Command line arguments
    2. Config file
    3. Environment variables

    Args:
        args: Parsed command line arguments

    Returns:
        RobotConfig instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    config: RobotConfig

    # Try config file first
    if args.config:
        logger.info(f"Loading config from file: {args.config}")
        config = RobotConfig.from_file(args.config)
    else:
        # Fall back to environment variables
        logger.info("Loading config from environment variables")
        config = RobotConfig.from_env()

    # Override with command line arguments
    if args.robot_name:
        config.robot_name = args.robot_name
    if args.control_plane_url:
        config.control_plane_url = args.control_plane_url
    if args.log_level:
        config.log_level = args.log_level

    return config


async def run_agent(config: RobotConfig) -> int:
    """
    Run the robot agent.

    Args:
        config: Robot configuration

    Returns:
        Exit code (0 for success, 1 for error)
    """
    agent = RobotAgent(config)

    # Set up event callbacks
    def on_connected() -> None:
        logger.info("Robot connected to orchestrator")

    def on_disconnected() -> None:
        logger.warning("Robot disconnected from orchestrator")

    def on_job_started(job_id: str) -> None:
        logger.info(f"Job started: {job_id}")

    def on_job_completed(job_id: str, success: bool) -> None:
        status = "successfully" if success else "with errors"
        logger.info(f"Job completed {status}: {job_id}")

    agent.on_connected = on_connected
    agent.on_disconnected = on_disconnected
    agent.on_job_started = on_job_started
    agent.on_job_completed = on_job_completed

    try:
        await agent.start()
        return 0
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await agent.stop()
        return 0
    except Exception as e:
        logger.exception(f"Agent error: {e}")
        return 1


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    args = parse_args()

    # Configure logging first
    configure_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("CasareRPA Robot Agent Starting")
    logger.info("=" * 60)

    try:
        config = load_config(args)
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Log configuration (without sensitive data)
    logger.info(f"Robot Name: {config.robot_name}")
    logger.info(f"Robot ID: {config.robot_id}")
    logger.info(f"Control Plane: {config.control_plane_url}")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Capabilities: {', '.join(config.capabilities)}")
    logger.info(f"Max Concurrent Jobs: {config.max_concurrent_jobs}")
    logger.info(f"Heartbeat Interval: {config.heartbeat_interval}s")

    if config.uses_mtls:
        logger.info("mTLS: Enabled")
    else:
        logger.info("mTLS: Disabled")

    if args.dry_run:
        logger.info("Configuration valid - dry run complete")
        return 0

    # Run the agent
    try:
        return asyncio.run(run_agent(config))
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        return 0


if __name__ == "__main__":
    sys.exit(main())

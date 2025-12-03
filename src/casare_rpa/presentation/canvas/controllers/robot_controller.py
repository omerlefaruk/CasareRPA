"""
Robot Controller for Canvas UI.

Manages robot selection, listing, and job submission for cloud execution.
Coordinates between the UI panel and application use cases.
Connects to remote orchestrator API for real robot fleet management.
"""

import os
from typing import Optional, List, Dict, TYPE_CHECKING

from PySide6.QtCore import Signal

from loguru import logger

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow
    from casare_rpa.domain.orchestrator.entities.robot import Robot, RobotCapability
    from casare_rpa.infrastructure.orchestrator.client import OrchestratorClient


class RobotController(BaseController):
    """
    Controller for robot management and job submission.

    Responsibilities:
    - Fetch and display robot list from orchestrator API
    - Handle robot selection for cloud execution
    - Manage execution mode (local vs cloud)
    - Submit jobs to selected robots
    - Coordinate with RobotPickerPanel UI
    - Real-time updates via WebSocket

    Signals:
        robots_updated: Emitted when robot list is updated (List[Robot])
        robot_selected: Emitted when a robot is selected (robot_id: str)
        execution_mode_changed: Emitted when mode changes ('local' or 'cloud')
        job_submitted: Emitted when job is submitted (job_id: str)
        job_submission_failed: Emitted on submission error (error: str)
        connection_status_changed: Emitted when orchestrator connection changes (connected: bool)
    """

    robots_updated = Signal(list)
    robot_selected = Signal(str)
    execution_mode_changed = Signal(str)
    job_submitted = Signal(str)
    job_submission_failed = Signal(str)
    connection_status_changed = Signal(bool)

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize Robot Controller.

        Args:
            main_window: Reference to main window for accessing shared components
        """
        super().__init__(main_window)

        self._orchestrator_client: Optional["OrchestratorClient"] = None
        self._orchestrator_url: Optional[str] = None

        self._current_robots: List = []
        self._selected_robot_id: Optional[str] = None
        self._execution_mode: str = "local"
        self._connected: bool = False

        # Reference to panel (set during panel creation)
        self._panel = None

        logger.debug("RobotController created")

    def initialize(self) -> None:
        """
        Initialize controller resources and connections.

        Called after all controllers are instantiated.
        Sets up connections to robot picker panel signals.
        """
        super().initialize()

        # Connect to panel if available
        self._connect_panel_signals()

        # Try to initialize orchestrator connection
        self._init_orchestrator_client()

        logger.info("RobotController initialized")

    def _init_orchestrator_client(self) -> None:
        """
        Initialize orchestrator client with configuration.

        Priority for orchestrator URL:
        1. ClientConfigManager (config.yaml from setup wizard)
        2. ORCHESTRATOR_URL environment variable
        3. Default: try tunnel first, then localhost
        """
        try:
            from casare_rpa.infrastructure.orchestrator.client import (
                OrchestratorClient,
                OrchestratorConfig,
            )

            # Try to get URL from ClientConfigManager first
            self._orchestrator_url = self._get_orchestrator_url_from_config()
            if not self._orchestrator_url:
                # Fall back to environment variable
                self._orchestrator_url = os.getenv("ORCHESTRATOR_URL", "")

            # If still no URL, try tunnel first, then localhost
            if not self._orchestrator_url:
                # Check CASARE_API_URL for tunnel URL
                # Default to api.casare.net (persistent Cloudflare tunnel)
                self._orchestrator_url = os.getenv(
                    "CASARE_API_URL", "https://api.casare.net"
                )

            # Store fallback URLs for auto-switching
            self._orchestrator_urls = self._get_orchestrator_url_list()

            ws_url = self._orchestrator_url.replace("http://", "ws://").replace(
                "https://", "wss://"
            )

            # Get API key from config or environment
            api_key = self._get_api_key_from_config()
            if not api_key:
                api_key = os.getenv("ORCHESTRATOR_API_KEY")

            config = OrchestratorConfig(
                base_url=self._orchestrator_url,
                ws_url=ws_url,
                api_key=api_key,
            )

            self._orchestrator_client = OrchestratorClient(config)

            # Register callbacks for real-time updates
            self._orchestrator_client.on("robot_status", self._on_robot_status_update)
            self._orchestrator_client.on("connected", self._on_orchestrator_connected)
            self._orchestrator_client.on(
                "disconnected", self._on_orchestrator_disconnected
            )
            self._orchestrator_client.on("error", self._on_orchestrator_error)

            logger.debug(f"OrchestratorClient configured for {self._orchestrator_url}")

        except ImportError as e:
            logger.warning(f"Could not import OrchestratorClient: {e}")
        except Exception as e:
            logger.warning(f"Orchestrator client initialization failed: {e}")

    def _get_orchestrator_url_from_config(self) -> Optional[str]:
        """
        Get orchestrator URL from ClientConfigManager (config.yaml).

        Returns:
            URL string if configured, None otherwise
        """
        try:
            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                url = config.orchestrator.url
                if url:
                    # Config stores WebSocket URL (ws://), convert to HTTP
                    if url.startswith("ws://"):
                        url = url.replace("ws://", "http://")
                    elif url.startswith("wss://"):
                        url = url.replace("wss://", "https://")
                    logger.debug(f"Orchestrator URL from config.yaml: {url}")
                    return url
        except Exception as e:
            logger.debug(f"Could not read config.yaml: {e}")
        return None

    def _get_api_key_from_config(self) -> Optional[str]:
        """
        Get API key from ClientConfigManager (config.yaml).

        Returns:
            API key string if configured, None otherwise
        """
        try:
            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                api_key = config.orchestrator.api_key
                if api_key:
                    logger.debug("API key loaded from config.yaml")
                    return api_key
        except Exception as e:
            logger.debug(f"Could not read API key from config.yaml: {e}")
        return None

    def _get_orchestrator_url_list(self) -> List[str]:
        """
        Get list of orchestrator URLs to try (tunnel first, then localhost).

        Returns:
            List of URLs in priority order
        """
        urls = []

        # Add configured URL first
        if self._orchestrator_url:
            urls.append(self._orchestrator_url)

        # Add Cloudflare Tunnel URL (priority for cloud connection)
        tunnel_url = os.getenv("CASARE_API_URL")
        if tunnel_url and tunnel_url not in urls:
            urls.append(tunnel_url)

        # Add localhost as fallback
        localhost = "http://localhost:8000"
        if localhost not in urls:
            urls.append(localhost)

        return urls

    async def connect_to_orchestrator(self, url: Optional[str] = None) -> bool:
        """
        Connect to orchestrator API with automatic fallback.

        Tries URLs in order:
        1. Provided URL (if any)
        2. Configured URL (from config.yaml or env)
        3. CASARE_API_URL env var (Cloudflare tunnel)
        4. Localhost (http://localhost:8000) - fallback

        Args:
            url: Optional orchestrator URL (uses fallback list if None)

        Returns:
            True if connected successfully to any URL
        """
        if self._orchestrator_client is None:
            self._init_orchestrator_client()

        if self._orchestrator_client is None:
            logger.error("OrchestratorClient not available")
            return False

        from casare_rpa.infrastructure.orchestrator.client import OrchestratorConfig

        # Build list of URLs to try
        urls_to_try = []
        if url:
            urls_to_try.append(url)
        urls_to_try.extend(self._orchestrator_urls)

        # Remove duplicates while preserving order
        seen = set()
        urls_to_try = [u for u in urls_to_try if not (u in seen or seen.add(u))]

        # Try each URL until one works
        for try_url in urls_to_try:
            logger.info(f"Trying orchestrator at {try_url}...")

            ws_url = try_url.replace("http://", "ws://").replace("https://", "wss://")
            api_key = self._get_api_key_from_config() or os.getenv(
                "ORCHESTRATOR_API_KEY"
            )

            self._orchestrator_client.config = OrchestratorConfig(
                base_url=try_url,
                ws_url=ws_url,
                api_key=api_key,
            )

            try:
                connected = await self._orchestrator_client.connect()
                if connected:
                    self._orchestrator_url = try_url
                    self._connected = True
                    self.connection_status_changed.emit(True)
                    logger.info(f"Connected to orchestrator at {try_url}")

                    # Start WebSocket subscriptions for real-time updates
                    await self._orchestrator_client.subscribe_live_updates()
                    return True

            except Exception as e:
                logger.debug(f"Failed to connect to {try_url}: {e}")
                continue

        # All URLs failed
        logger.error("Failed to connect to any orchestrator URL")
        self._connected = False
        self.connection_status_changed.emit(False)
        return False

    async def disconnect_from_orchestrator(self) -> None:
        """Disconnect from orchestrator."""
        if self._orchestrator_client:
            await self._orchestrator_client.disconnect()
            self._connected = False
            self.connection_status_changed.emit(False)
            logger.info("Disconnected from orchestrator")

    def _on_robot_status_update(self, data: dict) -> None:
        """Handle real-time robot status update from WebSocket."""
        robot_id = data.get("robot_id")
        status = data.get("status")

        if robot_id and status:
            # Update local robot list
            for robot in self._current_robots:
                if getattr(robot, "id", None) == robot_id:
                    robot.status = status
                    break

            # Notify UI
            self.robots_updated.emit(self._current_robots)
            logger.debug(f"Robot {robot_id} status updated to {status}")

    def _on_orchestrator_connected(self, data: dict) -> None:
        """Handle orchestrator connected event."""
        self._connected = True
        self.connection_status_changed.emit(True)

    def _on_orchestrator_disconnected(self, data: dict) -> None:
        """Handle orchestrator disconnected event."""
        self._connected = False
        self.connection_status_changed.emit(False)

    def _on_orchestrator_error(self, data: dict) -> None:
        """Handle orchestrator error event."""
        error = data.get("error", "Unknown error")
        logger.error(f"Orchestrator error: {error}")

    def _connect_panel_signals(self) -> None:
        """Connect to robot picker panel signals."""
        if hasattr(self.main_window, "_robot_picker_panel"):
            panel = self.main_window._robot_picker_panel
            if panel:
                self._panel = panel
                panel.robot_selected.connect(self._on_panel_robot_selected)
                panel.execution_mode_changed.connect(self._on_panel_mode_changed)
                panel.refresh_requested.connect(self._on_panel_refresh_requested)
                logger.debug("Connected to RobotPickerPanel signals")

    def set_panel(self, panel) -> None:
        """
        Set the robot picker panel reference.

        Called by DockCreator after panel is created.

        Args:
            panel: RobotPickerPanel instance
        """
        self._panel = panel

        # Connect signals
        panel.robot_selected.connect(self._on_panel_robot_selected)
        panel.execution_mode_changed.connect(self._on_panel_mode_changed)
        panel.refresh_requested.connect(self._on_panel_refresh_requested)
        panel.submit_to_cloud_requested.connect(self._on_submit_to_cloud_requested)

        # Keep panel updated on connection status
        self.connection_status_changed.connect(panel.set_connected)

        # Set initial connection status
        panel.set_connected(self._connected)

        logger.debug("RobotPickerPanel connected to controller")

    def cleanup(self) -> None:
        """Clean up controller resources."""
        super().cleanup()

        self._current_robots.clear()
        self._selected_robot_id = None
        self._panel = None

        logger.debug("RobotController cleaned up")

    # ==================== Panel Signal Handlers ====================

    def _on_panel_robot_selected(self, robot_id: str) -> None:
        """Handle robot selection from panel."""
        self.select_robot(robot_id)

    def _on_panel_mode_changed(self, mode: str) -> None:
        """Handle execution mode change from panel."""
        self.set_execution_mode(mode)

    def _on_panel_refresh_requested(self) -> None:
        """Handle refresh request from panel."""
        import asyncio

        asyncio.create_task(self.refresh_robots())

    def _on_submit_to_cloud_requested(self) -> None:
        """
        Handle submit to cloud request from panel.

        Gets workflow data from main window and submits to selected robot.
        """
        import asyncio

        asyncio.create_task(self._submit_current_workflow())

    async def _submit_current_workflow(self) -> None:
        """
        Submit the current workflow to the selected robot.

        Gets workflow data from the main window and calls submit_job.
        Updates panel with submission status.
        """
        if not self._panel:
            return

        if not self._selected_robot_id:
            self._panel.show_submit_result(False, "No robot selected")
            return

        # Show submitting state
        self._panel.set_submitting(True)

        try:
            # Get workflow data from main window
            workflow_data = self._get_workflow_data()
            if not workflow_data:
                self._panel.set_submitting(False)
                self._panel.show_submit_result(False, "No workflow data available")
                return

            # Get variables if available
            variables = self._get_workflow_variables()

            # Submit job
            job_id = await self.submit_job(
                workflow_data=workflow_data,
                variables=variables,
                robot_id=self._selected_robot_id,
            )

            self._panel.set_submitting(False)

            if job_id:
                self._panel.show_submit_result(True, job_id)
                logger.info(f"Workflow submitted to cloud: job_id={job_id}")
            else:
                self._panel.show_submit_result(False, "Submission failed")

        except Exception as e:
            logger.error(f"Failed to submit workflow: {e}")
            self._panel.set_submitting(False)
            self._panel.show_submit_result(False, str(e))

    def _get_workflow_data(self) -> Optional[dict]:
        """
        Get current workflow data from main window.

        Returns:
            Workflow data dict or None if not available
        """
        try:
            # Try using the workflow data provider
            if hasattr(self.main_window, "_get_workflow_data"):
                return self.main_window._get_workflow_data()

            # Try getting from workflow controller
            if hasattr(self.main_window, "_workflow_controller"):
                wf_controller = self.main_window._workflow_controller
                if wf_controller and hasattr(wf_controller, "get_workflow_data"):
                    return wf_controller.get_workflow_data()

            logger.warning("Could not get workflow data from main window")
            return None

        except Exception as e:
            logger.error(f"Error getting workflow data: {e}")
            return None

    def _get_workflow_variables(self) -> Optional[dict]:
        """
        Get current workflow variables from main window.

        Returns:
            Variables dict or None if not available
        """
        try:
            # Try getting from project controller
            if hasattr(self.main_window, "_project_controller"):
                proj_controller = self.main_window._project_controller
                if proj_controller and hasattr(
                    proj_controller, "get_current_variables"
                ):
                    return proj_controller.get_current_variables()

            # Try getting from workflow controller
            if hasattr(self.main_window, "_workflow_controller"):
                wf_controller = self.main_window._workflow_controller
                if wf_controller and hasattr(wf_controller, "get_variables"):
                    return wf_controller.get_variables()

            return None

        except Exception as e:
            logger.error(f"Error getting workflow variables: {e}")
            return None

    # ==================== Public Methods ====================

    async def refresh_robots(self) -> None:
        """
        Fetch robots from orchestrator API and update UI.

        Uses OrchestratorClient to fetch from remote API.
        Falls back to local storage if not connected.

        Emits robots_updated signal when complete.
        """
        if self._panel:
            self._panel.set_refreshing(True)

        try:
            robots = []

            # Try orchestrator API first
            if self._orchestrator_client and self._connected:
                robot_data_list = await self._orchestrator_client.get_robots()
                # Convert RobotData to Robot-like objects
                robots = self._convert_robot_data(robot_data_list)
                logger.debug(f"Fetched {len(robots)} robots from orchestrator API")

            elif self._orchestrator_client:
                # Try to connect first
                connected = await self.connect_to_orchestrator()
                if connected:
                    robot_data_list = await self._orchestrator_client.get_robots()
                    robots = self._convert_robot_data(robot_data_list)
                    logger.debug(f"Fetched {len(robots)} robots from orchestrator API")
                else:
                    # Fall back to local storage
                    robots = await self._get_local_robots()

            else:
                # No orchestrator client, use local storage
                robots = await self._get_local_robots()

            self._current_robots = robots

            # Update panel
            if self._panel:
                self._panel.update_robots(self._current_robots)

            # Emit signal
            self.robots_updated.emit(self._current_robots)

        except Exception as e:
            logger.error(f"Failed to refresh robots: {e}")
            self._current_robots = []
            if self._panel:
                self._panel.update_robots([])

        finally:
            if self._panel:
                self._panel.set_refreshing(False)

    def _convert_robot_data(self, robot_data_list: list) -> list:
        """
        Convert RobotData objects to Robot domain entities.

        Args:
            robot_data_list: List of RobotData from API

        Returns:
            List of Robot entities
        """
        from casare_rpa.domain.orchestrator.entities.robot import (
            Robot,
            RobotStatus,
            RobotCapability,
        )

        robots = []
        for rd in robot_data_list:
            try:
                # Map status string to enum
                status_map = {
                    "idle": RobotStatus.ONLINE,
                    "online": RobotStatus.ONLINE,
                    "busy": RobotStatus.BUSY,
                    "offline": RobotStatus.OFFLINE,
                    "error": RobotStatus.ERROR,
                    "maintenance": RobotStatus.MAINTENANCE,
                }
                status = status_map.get(rd.status, RobotStatus.OFFLINE)

                # Map capabilities
                capabilities = set()
                for cap in rd.capabilities:
                    try:
                        capabilities.add(RobotCapability(cap))
                    except ValueError:
                        pass

                robot = Robot(
                    id=rd.id,
                    name=rd.name,
                    status=status,
                    environment=rd.environment,
                    max_concurrent_jobs=rd.max_concurrent_jobs,
                    last_seen=rd.last_seen,
                    last_heartbeat=rd.last_seen,
                    capabilities=capabilities,
                    tags=rd.tags,
                    current_job_ids=[rd.current_job] if rd.current_job else [],
                )
                robots.append(robot)

            except Exception as e:
                logger.warning(f"Failed to convert robot data: {e}")

        return robots

    async def _get_local_robots(self) -> list:
        """Get robots from local storage (fallback)."""
        try:
            from casare_rpa.infrastructure.orchestrator.persistence import (
                LocalRobotRepository,
                LocalStorageRepository,
            )

            storage = LocalStorageRepository()
            repo = LocalRobotRepository(storage)
            robots = await repo.get_all()
            logger.debug(f"Fetched {len(robots)} robots from local storage")
            return robots

        except Exception as e:
            logger.warning(f"Failed to get local robots: {e}")
            return []

    async def get_available_robots(self) -> list:
        """
        Get list of robots that can accept jobs.

        Returns:
            List of available Robot entities
        """
        if self._orchestrator_client and self._connected:
            try:
                robot_data_list = await self._orchestrator_client.get_robots(
                    status="idle"
                )
                return self._convert_robot_data(robot_data_list)
            except Exception as e:
                logger.error(f"Failed to get available robots: {e}")
                return []

        return [
            r for r in self._current_robots if getattr(r, "status", None) == "online"
        ]

    async def get_robots_by_capability(self, capability: str) -> list:
        """
        Get robots with a specific capability.

        Args:
            capability: Required capability string

        Returns:
            List of robots with the capability
        """
        # Filter from current robots
        return [
            r
            for r in self._current_robots
            if capability in [c.value for c in getattr(r, "capabilities", [])]
        ]

    async def submit_job(
        self,
        workflow_data: dict,
        variables: Optional[dict] = None,
        robot_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Submit job to selected robot via orchestrator API.

        Args:
            workflow_data: Workflow JSON data to execute
            variables: Optional initial variables
            robot_id: Optional specific robot ID (uses selected robot if None)

        Returns:
            Job ID if submitted successfully, None on failure
        """
        target_robot_id = robot_id or self._selected_robot_id

        if self._execution_mode == "local":
            logger.warning("Cannot submit job in local execution mode")
            self.job_submission_failed.emit("Local execution mode selected")
            return None

        if target_robot_id is None:
            logger.warning("No robot selected for job submission")
            self.job_submission_failed.emit("No robot selected")
            return None

        if not self._orchestrator_client or not self._connected:
            logger.warning("Not connected to orchestrator")
            self.job_submission_failed.emit("Not connected to orchestrator")
            return None

        try:
            # Submit via orchestrator API
            import aiohttp

            # Get API key for authentication - try multiple sources
            api_key = None

            # 1. Try from orchestrator client config (already authenticated)
            if self._orchestrator_client and self._orchestrator_client.config:
                api_key = self._orchestrator_client.config.api_key

            # 2. Try from config.yaml
            if not api_key:
                api_key = self._get_api_key_from_config()

            # 3. Try from environment variable
            if not api_key:
                api_key = os.getenv("ORCHESTRATOR_API_KEY")

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            else:
                logger.warning(
                    "No API key configured. Set ORCHESTRATOR_API_KEY env var or "
                    "configure in Settings > Orchestrator."
                )

            async with aiohttp.ClientSession() as session:
                # Extract workflow name from data or use default
                workflow_name = (
                    workflow_data.get("metadata", {}).get("name")
                    or workflow_data.get("name")
                    or "Untitled Workflow"
                )

                # Build payload matching WorkflowSubmissionRequest schema
                payload = {
                    "workflow_name": workflow_name,
                    "workflow_json": workflow_data,
                    "trigger_type": "manual",
                    "execution_mode": "lan",
                    "priority": 10,
                    "metadata": {
                        "robot_id": target_robot_id,
                        "variables": variables or {},
                    },
                }

                async with session.post(
                    f"{self._orchestrator_url}/api/v1/workflows",
                    headers=headers,
                    json=payload,
                ) as resp:
                    if resp.status in (200, 201):
                        data = await resp.json()
                        job_id = data.get("job_id") or data.get("data", {}).get(
                            "job_id"
                        )
                        logger.info(
                            f"Job submitted: {job_id} to robot {target_robot_id}"
                        )
                        self.job_submitted.emit(job_id)
                        return job_id
                    elif resp.status == 401:
                        # Authentication error - provide helpful message
                        error_detail = (
                            "Authentication required. To fix:\n"
                            "1. Start orchestrator with: JWT_DEV_MODE=true python manage.py orchestrator start\n"
                            "2. Or set ORCHESTRATOR_API_KEY environment variable\n"
                            "3. Or login via the Orchestrator Dashboard"
                        )
                        logger.error(f"Auth error: {error_detail}")
                        raise Exception("Authentication required - see log for details")
                    else:
                        error = await resp.text()
                        raise Exception(f"API error: {resp.status} - {error}")

        except Exception as e:
            error_msg = f"Failed to submit job: {e}"
            logger.error(error_msg)
            self.job_submission_failed.emit(str(e))
            return None

    def select_robot(self, robot_id: str) -> None:
        """
        Select a robot by ID.

        Args:
            robot_id: Robot ID to select
        """
        if robot_id != self._selected_robot_id:
            self._selected_robot_id = robot_id
            self.robot_selected.emit(robot_id)
            logger.debug(f"Robot selected: {robot_id}")

            # Update panel selection if not already selected
            if self._panel and self._panel.get_selected_robot() != robot_id:
                self._panel.select_robot(robot_id)

    def clear_selection(self) -> None:
        """Clear current robot selection."""
        self._selected_robot_id = None
        if self._panel:
            self._panel.clear_selection()
        logger.debug("Robot selection cleared")

    def set_execution_mode(self, mode: str) -> None:
        """
        Set execution mode.

        Args:
            mode: 'local' or 'cloud'
        """
        if mode not in ("local", "cloud"):
            logger.warning(f"Invalid execution mode: {mode}")
            return

        if mode != self._execution_mode:
            self._execution_mode = mode
            self.execution_mode_changed.emit(mode)
            logger.debug(f"Execution mode set to: {mode}")

            # Update panel if not already set
            if self._panel and self._panel.get_execution_mode() != mode:
                self._panel.set_execution_mode(mode)

            # Clear robot selection when switching to local mode
            if mode == "local":
                self.clear_selection()

    # ==================== Properties ====================

    @property
    def selected_robot_id(self) -> Optional[str]:
        """Get currently selected robot ID."""
        return self._selected_robot_id

    @property
    def execution_mode(self) -> str:
        """Get current execution mode ('local' or 'cloud')."""
        return self._execution_mode

    @property
    def robots(self) -> list:
        """Get current robot list."""
        return self._current_robots.copy()

    @property
    def is_cloud_mode(self) -> bool:
        """Check if cloud execution mode is enabled."""
        return self._execution_mode == "cloud"

    @property
    def is_local_mode(self) -> bool:
        """Check if local execution mode is enabled."""
        return self._execution_mode == "local"

    @property
    def has_robot_selected(self) -> bool:
        """Check if a robot is currently selected."""
        return self._selected_robot_id is not None

    @property
    def is_connected(self) -> bool:
        """Check if connected to orchestrator."""
        return self._connected

    @property
    def orchestrator_url(self) -> Optional[str]:
        """Get configured orchestrator URL."""
        return self._orchestrator_url

    def get_selected_robot(self):
        """
        Get the currently selected robot entity.

        Returns:
            Selected Robot entity or None
        """
        if self._selected_robot_id is None:
            return None

        for robot in self._current_robots:
            if getattr(robot, "id", None) == self._selected_robot_id:
                return robot
        return None

    async def get_statistics(self) -> dict:
        """
        Get robot fleet statistics from orchestrator.

        Returns:
            Dictionary with fleet statistics
        """
        if not self._orchestrator_client or not self._connected:
            return {
                "total": len(self._current_robots),
                "by_status": {},
                "connected": False,
            }

        try:
            metrics = await self._orchestrator_client.get_fleet_metrics()
            return {
                "total": metrics.get("total_robots", 0),
                "online": metrics.get("active_robots", 0),
                "busy": metrics.get("busy_robots", 0),
                "offline": metrics.get("offline_robots", 0),
                "active_jobs": metrics.get("active_jobs", 0),
                "queue_depth": metrics.get("queue_depth", 0),
                "connected": True,
            }

        except Exception as e:
            logger.error(f"Failed to get robot statistics: {e}")
            return {
                "total": len(self._current_robots),
                "by_status": {},
                "connected": False,
                "error": str(e),
            }

    # ==================== Remote Robot Management ====================

    async def start_robot(self, robot_id: str) -> bool:
        """
        Send start command to a remote robot.

        Args:
            robot_id: Robot ID to start

        Returns:
            True if command sent successfully
        """
        if not self._orchestrator_client or not self._connected:
            logger.warning("Cannot start robot: not connected to orchestrator")
            return False

        try:
            result = await self._orchestrator_client._request(
                "POST", f"/api/v1/robots/{robot_id}/start"
            )
            if result:
                logger.info(f"Start command sent to robot {robot_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to start robot {robot_id}: {e}")
            return False

    async def stop_robot(self, robot_id: str, force: bool = False) -> bool:
        """
        Send stop command to a remote robot.

        Args:
            robot_id: Robot ID to stop
            force: If True, force stop even if job is running

        Returns:
            True if command sent successfully
        """
        if not self._orchestrator_client or not self._connected:
            logger.warning("Cannot stop robot: not connected to orchestrator")
            return False

        try:
            result = await self._orchestrator_client._request(
                "POST",
                f"/api/v1/robots/{robot_id}/stop",
                json_data={"force": force},
            )
            if result:
                logger.info(f"Stop command sent to robot {robot_id} (force={force})")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to stop robot {robot_id}: {e}")
            return False

    async def pause_robot(self, robot_id: str) -> bool:
        """
        Send pause command to a remote robot.

        Paused robots won't accept new jobs but complete current ones.

        Args:
            robot_id: Robot ID to pause

        Returns:
            True if command sent successfully
        """
        if not self._orchestrator_client or not self._connected:
            logger.warning("Cannot pause robot: not connected to orchestrator")
            return False

        try:
            result = await self._orchestrator_client._request(
                "POST", f"/api/v1/robots/{robot_id}/pause"
            )
            if result:
                logger.info(f"Pause command sent to robot {robot_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to pause robot {robot_id}: {e}")
            return False

    async def resume_robot(self, robot_id: str) -> bool:
        """
        Send resume command to a paused robot.

        Args:
            robot_id: Robot ID to resume

        Returns:
            True if command sent successfully
        """
        if not self._orchestrator_client or not self._connected:
            logger.warning("Cannot resume robot: not connected to orchestrator")
            return False

        try:
            result = await self._orchestrator_client._request(
                "POST", f"/api/v1/robots/{robot_id}/resume"
            )
            if result:
                logger.info(f"Resume command sent to robot {robot_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to resume robot {robot_id}: {e}")
            return False

    async def restart_robot(self, robot_id: str) -> bool:
        """
        Send restart command to a remote robot.

        Args:
            robot_id: Robot ID to restart

        Returns:
            True if command sent successfully
        """
        if not self._orchestrator_client or not self._connected:
            logger.warning("Cannot restart robot: not connected to orchestrator")
            return False

        try:
            result = await self._orchestrator_client._request(
                "POST", f"/api/v1/robots/{robot_id}/restart"
            )
            if result:
                logger.info(f"Restart command sent to robot {robot_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to restart robot {robot_id}: {e}")
            return False

    # ==================== Batch Operations ====================

    async def stop_all_robots(self, force: bool = False) -> Dict[str, bool]:
        """
        Send stop command to all online robots.

        Args:
            force: If True, force stop even if jobs are running

        Returns:
            Dictionary mapping robot_id to success status
        """
        results = {}
        for robot in self._current_robots:
            if hasattr(robot, "status") and robot.status.value in ("online", "busy"):
                results[robot.id] = await self.stop_robot(robot.id, force)
        return results

    async def restart_all_robots(self) -> Dict[str, bool]:
        """
        Send restart command to all robots.

        Returns:
            Dictionary mapping robot_id to success status
        """
        results = {}
        for robot in self._current_robots:
            results[robot.id] = await self.restart_robot(robot.id)
        return results

    async def get_robot_logs(
        self, robot_id: str, limit: int = 100, since: Optional[str] = None
    ) -> List[dict]:
        """
        Get logs for a specific robot.

        Args:
            robot_id: Robot ID
            limit: Max number of log entries
            since: Optional ISO timestamp to get logs after

        Returns:
            List of log entry dictionaries
        """
        if not self._orchestrator_client or not self._connected:
            return []

        try:
            params = {"limit": limit}
            if since:
                params["since"] = since

            result = await self._orchestrator_client._request(
                "GET", f"/api/v1/robots/{robot_id}/logs", params=params
            )
            return result.get("logs", []) if result else []

        except Exception as e:
            logger.error(f"Failed to get robot logs: {e}")
            return []

    async def get_robot_metrics(self, robot_id: str) -> dict:
        """
        Get detailed metrics for a specific robot.

        Args:
            robot_id: Robot ID

        Returns:
            Dictionary with robot metrics (CPU, memory, jobs, etc.)
        """
        if not self._orchestrator_client or not self._connected:
            return {}

        try:
            result = await self._orchestrator_client._request(
                "GET", f"/api/v1/robots/{robot_id}/metrics"
            )
            return result or {}

        except Exception as e:
            logger.error(f"Failed to get robot metrics: {e}")
            return {}

# Cross References

This page shows which functions call which other functions.


## Most Called Functions

| Function | Called By (count) |
|----------|-------------------|
| `casare_rpa.config.loader.ConfigManager.get` | 1400 |
| `casare_rpa.robot.circuit_breaker.CircuitBreakerRegistry.get` | 1400 |
| `casare_rpa.triggers.registry.TriggerRegistry.get` | 1400 |
| `casare_rpa.utils.settings_manager.SettingsManager.get` | 1400 |
| `casare_rpa.utils.pooling.http_session_pool.HttpSessionPool.get` | 1400 |
| `casare_rpa.utils.security.secrets_manager.SecretsManager.get` | 1400 |
| `casare_rpa.utils.selectors.selector_cache.SelectorCache.get` | 1400 |
| `casare_rpa.triggers.implementations.google_trigger_base.GoogleAPIClient.get` | 1400 |
| `casare_rpa.presentation.canvas.component_factory.ComponentFactory.get` | 1400 |
| `casare_rpa.presentation.canvas.events.event.Event.get` | 1400 |
| `casare_rpa.infrastructure.analytics.metric_storage.WorkflowMetricsCache.get` | 1400 |
| `casare_rpa.infrastructure.analytics.metric_storage.RobotMetricsCache.get` | 1400 |
| `casare_rpa.infrastructure.resources.unified_resource_manager.LRUResourceCache.get` | 1400 |
| `casare_rpa.infrastructure.security.rbac.PermissionRegistry.get` | 1400 |
| `casare_rpa.infrastructure.security.vault_client.SecretValue.get` | 1400 |
| `casare_rpa.infrastructure.security.vault_client.SecretCache.get` | 1400 |
| `casare_rpa.application.dependency_injection.container.TypedContainer.get` | 1400 |
| `casare_rpa.application.dependency_injection.singleton.Singleton.get` | 1400 |
| `casare_rpa.application.dependency_injection.singleton.LazySingleton.get` | 1400 |
| `casare_rpa.infrastructure.observability.facade.Observability.info` | 1219 |
| `casare_rpa.infrastructure.observability.logging.SpanLogger.info` | 1219 |
| `casare_rpa.infrastructure.observability.facade.Observability.debug` | 1008 |
| `casare_rpa.infrastructure.observability.logging.SpanLogger.debug` | 1008 |
| `casare_rpa.infrastructure.observability.facade.Observability.error` | 990 |
| `casare_rpa.infrastructure.observability.logging.SpanLogger.error` | 990 |
| `casare_rpa.domain.orchestrator.protocols.robot_protocol.MessageBuilder.error` | 990 |
| `casare_rpa.cloud.dbos_cloud.DBOSCloudError.__init__` | 834 |
| `casare_rpa.cloud.dbos_cloud.DBOSCloudClient.__init__` | 834 |
| `casare_rpa.config.file_loader.ConfigFileLoader.__init__` | 834 |
| `casare_rpa.config.loader.ConfigurationError.__init__` | 834 |
| `casare_rpa.config.loader.ConfigManager.__init__` | 834 |
| `casare_rpa.desktop.context.DesktopContext.__init__` | 834 |
| `casare_rpa.desktop.desktop_recorder.DesktopRecorder.__init__` | 834 |
| `casare_rpa.desktop.element.DesktopElement.__init__` | 834 |
| `casare_rpa.domain.events.Event.__init__` | 834 |
| `casare_rpa.domain.events.EventBus.__init__` | 834 |
| `casare_rpa.domain.events.EventLogger.__init__` | 834 |
| `casare_rpa.domain.events.EventRecorder.__init__` | 834 |
| `casare_rpa.nodes.basic_nodes.StartNode.__init__` | 834 |
| `casare_rpa.nodes.basic_nodes.EndNode.__init__` | 834 |
| `casare_rpa.nodes.basic_nodes.CommentNode.__init__` | 834 |
| `casare_rpa.nodes.browser_nodes.LaunchBrowserNode.__init__` | 834 |
| `casare_rpa.nodes.browser_nodes.CloseBrowserNode.__init__` | 834 |
| `casare_rpa.nodes.browser_nodes.NewTabNode.__init__` | 834 |
| `casare_rpa.nodes.browser_nodes.GetAllImagesNode.__init__` | 834 |
| `casare_rpa.nodes.browser_nodes.DownloadFileNode.__init__` | 834 |
| `casare_rpa.nodes.control_flow_nodes.IfNode.__init__` | 834 |
| `casare_rpa.nodes.control_flow_nodes.ForLoopStartNode.__init__` | 834 |
| `casare_rpa.nodes.control_flow_nodes.ForLoopEndNode.__init__` | 834 |
| `casare_rpa.nodes.control_flow_nodes.WhileLoopStartNode.__init__` | 834 |

## Most Complex Functions (by call count)

| Function | Calls (count) |
|----------|---------------|
| `casare_rpa.presentation.canvas.ui.dialogs.schedule_dialog.ScheduleDialog._setup_ui` | 39 |
| `casare_rpa.infrastructure.tunnel.mtls.CertificateManager.generate_certificate` | 39 |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.jobs_tab.JobsTabWidget._setup_ui` | 38 |
| `casare_rpa.presentation.canvas.ui.panels.log_viewer_panel.LogViewerPanel._setup_ui` | 36 |
| `casare_rpa.infrastructure.orchestrator.api.routers.workflows.submit_workflow` | 34 |
| `casare_rpa.presentation.canvas.ui.panels.robot_picker_panel.RobotPickerPanel._setup_ui` | 33 |
| `casare_rpa.presentation.canvas.graph.node_graph_widget.NodeGraphWidget._handle_drop` | 32 |
| `casare_rpa.presentation.canvas.ui.panels.history_tab.HistoryTab._setup_ui` | 32 |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.schedules_tab.SchedulesTabWidget._populate_table` | 32 |
| `casare_rpa.nodes.browser_nodes.DownloadFileNode.execute` | 31 |
| `casare_rpa.presentation.canvas.ui.panels.api_key_panel.ApiKeyPanel._populate_table` | 31 |
| `casare_rpa.presentation.canvas.graph.node_graph_widget.NodeGraphWidget.__init__` | 30 |
| `casare_rpa.presentation.canvas.ui.dialogs.update_dialog.UpdateDialog._setup_ui` | 30 |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.jobs_tab.JobsTabWidget._populate_table` | 30 |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.robots_tab.RobotsTabWidget._populate_table` | 30 |
| `casare_rpa.presentation.canvas.connections.connection_cutter.ConnectionCutter._cut_intersecting_connections` | 29 |
| `casare_rpa.presentation.canvas.ui.panels.api_key_panel.GenerateApiKeyDialog._setup_ui` | 29 |
| `casare_rpa.presentation.canvas.ui.panels.api_key_panel.ApiKeyPanel._setup_ui` | 29 |
| `casare_rpa.presentation.canvas.ui.panels.output_tab.OutputTab._setup_ui` | 29 |
| `casare_rpa.infrastructure.orchestrator.communication.delegates.ProgressBarDelegate.paint` | 29 |
| `casare_rpa.infrastructure.orchestrator.communication.delegates.PriorityDelegate.paint` | 29 |
| `casare_rpa.nodes.browser_nodes.LaunchBrowserNode.execute` | 28 |
| `casare_rpa.presentation.canvas.graph.node_registry.SearchLineEdit.keyPressEvent` | 28 |
| `casare_rpa.presentation.canvas.graph.node_registry.NodeRegistry.register_all_nodes` | 28 |
| `casare_rpa.presentation.canvas.ui.dialogs.template_browser_dialog.TemplateBrowserDialog._create_ui` | 28 |
| `casare_rpa.presentation.canvas.ui.panels.minimap_panel.MinimapPanel.update_minimap` | 28 |
| `casare_rpa.presentation.canvas.ui.panels.process_mining_panel.ProcessMiningPanel._create_insights_tab` | 28 |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.robots_tab.RobotsTabWidget._setup_ui` | 28 |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.schedules_tab.SchedulesTabWidget._setup_ui` | 28 |
| `casare_rpa.presentation.canvas.graph.node_icons.create_node_icon` | 27 |
| `casare_rpa.presentation.canvas.ui.panels.variables_panel.VariablesPanel._setup_ui` | 27 |
| `casare_rpa.infrastructure.agent.job_executor.JobExecutor.execute` | 27 |
| `casare_rpa.infrastructure.tunnel.mtls.CertificateManager.generate_ca` | 27 |
| `casare_rpa.infrastructure.orchestrator.communication.delegates.StatusDelegate.paint` | 27 |
| `casare_rpa.infrastructure.orchestrator.communication.delegates.RobotStatusDelegate.paint` | 27 |
| `casare_rpa.nodes.http.http_advanced.HttpDownloadFileNode.execute` | 26 |
| `casare_rpa.nodes.http.http_advanced.HttpUploadFileNode.execute` | 26 |
| `casare_rpa.presentation.setup.setup_wizard.OrchestratorPage._setup_ui` | 25 |
| `casare_rpa.presentation.canvas.graph.node_graph_widget.NodeGraphWidget._setup_graph` | 25 |
| `casare_rpa.presentation.canvas.graph.node_graph_widget.NodeGraphWidget.eventFilter` | 25 |
| `casare_rpa.presentation.canvas.ui.debug_panel.DebugPanel._create_logs_tab` | 25 |
| `casare_rpa.presentation.canvas.ui.dialogs.remote_robot_dialog.RemoteRobotDialog._setup_ui` | 25 |
| `casare_rpa.nodes.email.send_nodes.SendEmailNode.execute` | 25 |
| `casare_rpa.infrastructure.execution.dbos_executor.DBOSWorkflowExecutor.execute_workflow` | 25 |
| `casare_rpa.infrastructure.orchestrator.websocket_handlers.robot_websocket` | 25 |
| `casare_rpa.application.use_cases.execute_workflow.ExecuteWorkflowUseCase.execute` | 25 |
| `casare_rpa.application.use_cases.workflow_migration.WorkflowMigrationUseCase.migrate` | 25 |
| `casare_rpa.nodes.browser_nodes.NewTabNode.execute` | 24 |
| `casare_rpa.robot.agent.RobotAgent._execute_job` | 24 |
| `casare_rpa.robot.distributed_agent.DistributedRobotAgent.start` | 24 |

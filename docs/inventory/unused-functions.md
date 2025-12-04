# Potentially Unused Functions

!!! warning "Review Required"

    These functions appear to have no callers in the codebase.

    They may be: entry points, event handlers, or truly unused.


**Total:** 1807 potentially unused functions


## casare_rpa.application.dependency_injection.container

**7 unused functions**


- `DIContainer.reset_instance` (line 132)
- `DIContainer.register_scoped` (line 168)
- `DIContainer.register_transient` (line 188)
- `DIContainer.register_instance` (line 208)
- `DIContainer.is_registered` (line 293)
- `DIContainer.create_scope` (line 299)
- `TypedContainer.get_optional` (line 365)

## casare_rpa.application.dependency_injection.providers

**16 unused functions**


- `ConfigProvider.config_factory` (line 45)
- `EventBusProvider.event_bus_factory` (line 66)
- `StorageProvider.schedule_storage_factory` (line 92)
- `StorageProvider.recent_files_factory` (line 99)
- `StorageProvider.template_loader_factory` (line 104)
- `StorageProvider.settings_manager_factory` (line 109)
- `InfrastructureProvider.recovery_registry_factory` (line 150)
- `InfrastructureProvider.migration_registry_factory` (line 157)
- `InfrastructureProvider.healing_telemetry_factory` (line 164)
- `InfrastructureProvider.api_key_store_factory` (line 171)
- `InfrastructureProvider.credential_store_factory` (line 176)
- `InfrastructureProvider.memory_queue_factory` (line 183)
- `InfrastructureProvider.robot_metrics_factory` (line 188)
- `InfrastructureProvider.error_handler_factory` (line 193)
- `UILogController.set_callback` (line 278)
- `register_all_providers` (line 349)

## casare_rpa.application.dependency_injection.singleton

**3 unused functions**


- `Singleton.get_optional` (line 111)
- `Singleton.is_initialized` (line 157)
- `create_singleton_accessor` (line 213)

## casare_rpa.application.execution.trigger_runner

**6 unused functions**


- `CanvasTriggerRunner.active_trigger_count` (line 60)
- `CanvasTriggerRunner.set_event_handler` (line 64)
- `CanvasTriggerRunner.start_triggers` (line 74)
- `CanvasTriggerRunner.stop_triggers` (line 148)
- `CanvasTriggerRunner.get_last_trigger_event` (line 206)
- `CanvasTriggerRunner.clear_last_trigger_event` (line 210)

## casare_rpa.application.orchestrator.orchestrator_engine

**17 unused functions**


- `OrchestratorEngine.start_server` (line 222)
- `OrchestratorEngine.dispatch_job_to_robot` (line 288)
- `OrchestratorEngine.server_port` (line 319)
- `OrchestratorEngine.connected_robots` (line 324)
- `OrchestratorEngine.available_robots` (line 331)
- `OrchestratorEngine.cancel_job` (line 447)
- `OrchestratorEngine.retry_job` (line 470)
- `OrchestratorEngine.robot_heartbeat` (line 621)
- `OrchestratorEngine.create_schedule` (line 672)
- `OrchestratorEngine.get_dispatcher_stats` (line 857)
- `OrchestratorEngine.get_upcoming_schedules` (line 863)
- `OrchestratorEngine.on_trigger_event` (line 904)
- `OrchestratorEngine.enable_trigger` (line 923)
- `OrchestratorEngine.disable_trigger` (line 933)
- `OrchestratorEngine.fire_trigger_manually` (line 943)
- `OrchestratorEngine.get_trigger_manager` (line 960)
- `OrchestratorEngine.get_trigger_stats` (line 964)

## casare_rpa.application.orchestrator.services.dispatcher_service

**5 unused functions**


- `RobotPool.is_workflow_allowed` (line 92)
- `RobotPool.utilization` (line 99)
- `RobotPool.online_count` (line 110)
- `JobDispatcher.get_robots_by_status` (line 246)
- `JobDispatcher.delete_pool` (line 270)

## casare_rpa.application.orchestrator.services.distribution_service

**14 unused functions**


- `RobotSelector.score` (line 165)
- `RobotSelector.clear_affinity` (line 188)
- `RobotSelector.clear_all_affinity` (line 192)
- `WorkflowDistributor.set_send_job_function` (line 241)
- `WorkflowDistributor.add_rule` (line 254)
- `WorkflowDistributor.remove_rule` (line 259)
- `WorkflowDistributor.clear_rules` (line 267)
- `WorkflowDistributor.distribute_batch` (line 419)
- `WorkflowDistributor.get_recent_results` (line 485)
- `JobRouter.add_route` (line 506)
- `JobRouter.add_tag_route` (line 510)
- `JobRouter.set_fallback_robots` (line 514)
- `JobRouter.get_eligible_robots` (line 518)
- `JobRouter.clear_routes` (line 557)

## casare_rpa.application.orchestrator.services.job_lifecycle_service

**6 unused functions**


- `JobLifecycleService.set_robot_management_service` (line 58)
- `JobLifecycleService.is_cloud_mode` (line 71)
- `JobLifecycleService.get_queued_jobs` (line 153)
- `JobLifecycleService.cancel_job` (line 265)
- `JobLifecycleService.retry_job` (line 315)
- `JobLifecycleService.dispatch_workflow_file` (line 330)

## casare_rpa.application.orchestrator.services.job_queue_manager

**3 unused functions**


- `JobTimeoutManager.get_remaining_time` (line 274)
- `JobQueue.get_queued_jobs` (line 623)
- `JobQueue.get_robot_jobs` (line 642)

## casare_rpa.application.orchestrator.services.metrics_service

**2 unused functions**


- `MetricsService.calculate_dashboard_metrics` (line 26)
- `MetricsService.calculate_job_history` (line 124)

## casare_rpa.application.orchestrator.services.result_collector_service

**18 unused functions**


- `JobResult.is_success` (line 42)
- `JobResult.duration_seconds` (line 47)
- `ResultCollector.collect_result` (line 191)
- `ResultCollector.collect_failure` (line 226)
- `ResultCollector.collect_cancellation` (line 268)
- `ResultCollector.collect_timeout` (line 297)
- `ResultCollector.add_log_batch` (line 360)
- `ResultCollector.get_results_by_workflow` (line 419)
- `ResultCollector.get_results_by_robot` (line 423)
- `ResultCollector.get_recent_results` (line 427)
- `ResultCollector.get_failed_results` (line 432)
- `ResultCollector.get_hourly_stats` (line 528)
- `ResultCollector.get_workflow_stats` (line 574)
- `ResultCollector.get_robot_stats` (line 587)
- `ResultCollector.result_count` (line 609)
- `ResultCollector.pending_log_count` (line 614)
- `ResultExporter.to_csv` (line 633)
- `ResultExporter.to_summary` (line 673)

## casare_rpa.application.orchestrator.services.robot_management_service

**1 unused functions**


- `RobotManagementService.is_cloud_mode` (line 38)

## casare_rpa.application.orchestrator.services.schedule_management_service

**1 unused functions**


- `ScheduleManagementService.is_cloud_mode` (line 33)

## casare_rpa.application.orchestrator.services.scheduling_coordinator

**3 unused functions**


- `JobScheduler.pause_all` (line 262)
- `JobScheduler.resume_all` (line 268)
- `JobScheduler.get_schedule_info` (line 306)

## casare_rpa.application.orchestrator.services.workflow_management_service

**2 unused functions**


- `WorkflowManagementService.is_cloud_mode` (line 36)
- `WorkflowManagementService.import_workflow_from_file` (line 121)

## casare_rpa.application.orchestrator.use_cases.assign_robot

**11 unused functions**


- `AssignRobotUseCase.assign_to_node` (line 121)
- `AssignRobotUseCase.remove_workflow_assignment` (line 199)
- `AssignRobotUseCase.remove_node_override` (line 226)
- `AssignRobotUseCase.deactivate_node_override` (line 253)
- `AssignRobotUseCase.activate_node_override` (line 276)
- `AssignRobotUseCase.get_workflow_assignments` (line 294)
- `AssignRobotUseCase.get_node_overrides` (line 308)
- `AssignRobotUseCase.get_active_node_overrides` (line 322)
- `AssignRobotUseCase.set_default_robot` (line 336)
- `AssignRobotUseCase.unassign_robot_from_all_workflows` (line 376)
- `AssignRobotUseCase.remove_all_node_overrides_for_robot` (line 397)

## casare_rpa.application.orchestrator.use_cases.execute_local

**2 unused functions**


- `ExecutionResult.progress` (line 59)
- `ExecuteLocalUseCase.execute_from_json` (line 219)

## casare_rpa.application.orchestrator.use_cases.list_robots

**6 unused functions**


- `ListRobotsUseCase.get_for_workflow` (line 107)
- `ListRobotsUseCase.get_by_name` (line 193)
- `ListRobotsUseCase.get_online` (line 208)
- `ListRobotsUseCase.get_offline` (line 221)
- `ListRobotsUseCase.get_busy` (line 234)
- `ListRobotsUseCase.get_with_available_capacity` (line 247)

## casare_rpa.application.scheduling.schedule_storage

**5 unused functions**


- `ScheduleStorage.get_due_schedules` (line 173)
- `ScheduleStorage.mark_schedule_run` (line 189)
- `ScheduleStorage.get_schedules_for_workflow` (line 224)
- `set_schedule_storage` (line 266)
- `reset_schedule_storage` (line 279)

## casare_rpa.application.services.execution_lifecycle_manager

**1 unused functions**


- `ExecutionLifecycleManager.get_session_info` (line 534)

## casare_rpa.application.services.port_type_service

**3 unused functions**


- `PortTypeRegistry.set_compatibility_rule` (line 177)
- `PortTypeRegistry.get_compatible_types` (line 188)
- `is_types_compatible` (line 210)

## casare_rpa.application.services.template_loader

**5 unused functions**


- `TemplateLoader.get_templates_by_difficulty` (line 293)
- `TemplateLibraryService.get_template_for_instantiation` (line 401)
- `TemplateLibraryService.browse_templates` (line 416)
- `TemplateLibraryService.get_featured_templates` (line 479)
- `TemplateLibraryService.get_templates_for_category_page` (line 502)

## casare_rpa.application.use_cases.error_recovery

**5 unused functions**


- `ErrorRecoveryUseCase.get_node_error_history` (line 560)
- `ErrorRecoveryIntegration.wrap_node_execution` (line 615)
- `ErrorRecoveryIntegration.create_custom_handler` (line 681)
- `ErrorRecoveryIntegration.get_report` (line 695)
- `handle_node_error` (line 701)

## casare_rpa.application.use_cases.execute_workflow

**4 unused functions**


- `ExecuteWorkflowUseCase.executed_nodes` (line 151)
- `ExecuteWorkflowUseCase.current_node_id` (line 156)
- `ExecuteWorkflowUseCase.start_time` (line 161)
- `ExecuteWorkflowUseCase.end_time` (line 166)

## casare_rpa.application.use_cases.execution_state_manager

**5 unused functions**


- `ExecutionStateManager.is_failed` (line 212)
- `ExecutionStateManager.execution_error` (line 217)
- `ExecutionStateManager.target_reached` (line 222)
- `ExecutionStateManager.total_nodes` (line 227)
- `ExecutionStateManager.duration` (line 234)

## casare_rpa.application.use_cases.template_management

**6 unused functions**


- `CreateTemplateUseCase.from_workflow` (line 207)
- `GetTemplateUseCase.by_id` (line 281)
- `GetTemplateUseCase.by_category` (line 309)
- `GetTemplateUseCase.builtin` (line 325)
- `GetTemplateUseCase.user_created` (line 337)
- `ExportTemplateUseCase.to_file` (line 704)

## casare_rpa.application.use_cases.validate_workflow

**4 unused functions**


- `ValidationResult.warnings` (line 65)
- `ValidationResult.error_count` (line 70)
- `ValidationResult.warning_count` (line 75)
- `ValidateWorkflowUseCase.get_cache_stats` (line 351)

## casare_rpa.application.use_cases.workflow_migration

**15 unused functions**


- `reset_rule_registry` (line 209)
- `register_migration_rule` (line 219)
- `decorator` (line 235)
- `WorkflowMigrationUseCase.migrate` (line 332)
- `WorkflowMigrationUseCase.validate_running_jobs` (line 790)
- `VersionPinManager.pin_job` (line 829)
- `VersionPinManager.unpin_job` (line 856)
- `VersionPinManager.get_pinned_version` (line 872)
- `VersionPinManager.get_execution_version` (line 876)
- `VersionPinManager.get_jobs_pinned_to_version` (line 893)
- `VersionPinManager.validate_pins` (line 897)
- `AutoMigrationPolicy.should_auto_migrate` (line 963)
- `AutoMigrationPolicy.permissive` (line 1031)
- `AutoMigrationPolicy.strict` (line 1041)
- `AutoMigrationPolicy.manual` (line 1051)

## casare_rpa.application.workflow.recent_files

**1 unused functions**


- `reset_recent_files_manager` (line 148)

## casare_rpa.application.workflow.workflow_import

**1 unused functions**


- `import_workflow_data` (line 218)

## casare_rpa.cli.db

**1 unused functions**


- `setup_db` (line 57)

## casare_rpa.cli.main

**4 unused functions**


- `start_orchestrator` (line 28)
- `start_canvas` (line 67)
- `tunnel_start` (line 91)
- `run_auto_setup` (line 130)

## casare_rpa.cloud.dbos_cloud

**7 unused functions**


- `DBOSCloudClient.get_logs` (line 451)
- `DBOSCloudClient.destroy` (line 546)
- `DBOSCloudClient.set_env_vars` (line 595)
- `DBOSCloudClient.health_check` (line 650)
- `DBOSCloudClient.list_deployments` (line 744)
- `DBOSCloudClient.get_postgres_connection_string` (line 779)
- `deploy_from_config` (line 983)

## casare_rpa.config.file_loader

**5 unused functions**


- `ConfigFileLoader.add_source` (line 129)
- `ConfigFileLoader.clear_sources` (line 134)
- `ConfigFileLoader.load_all` (line 197)
- `load_config_file` (line 379)
- `load_config_file_with_env` (line 394)

## casare_rpa.config.loader

**2 unused functions**


- `clear_config_cache` (line 518)
- `reset_config_manager` (line 523)

## casare_rpa.config.schema

**8 unused functions**


- `DatabaseConfig.connection_url` (line 36)
- `SupabaseConfig.is_configured` (line 63)
- `SecurityConfig.uses_mtls` (line 92)
- `SecurityConfig.validate_mtls` (line 97)
- `OrchestratorConfig.uses_ssl` (line 123)
- `LoggingConfig.validate_level` (line 157)
- `VaultConfig.is_configured` (line 211)
- `VaultConfig.auth_method` (line 216)

## casare_rpa.config.startup

**5 unused functions**


- `validate_orchestrator_config` (line 15)
- `validate_robot_config` (line 47)
- `validate_canvas_config` (line 73)
- `print_config_summary` (line 93)
- `check_required_env_vars` (line 122)

## casare_rpa.desktop.element

**3 unused functions**


- `with_stale_check` (line 24)
- `wrapper` (line 32)
- `DesktopElement.find_children` (line 408)

## casare_rpa.desktop.managers.keyboard_controller

**3 unused functions**


- `KeyboardController.press_key` (line 162)
- `KeyboardController.key_down` (line 205)
- `KeyboardController.key_up` (line 240)

## casare_rpa.desktop.managers.mouse_controller

**1 unused functions**


- `MouseController.scroll` (line 249)

## casare_rpa.desktop.managers.screen_capture

**1 unused functions**


- `ScreenCapture.find_image_on_screen` (line 429)

## casare_rpa.desktop.managers.wait_manager

**1 unused functions**


- `WaitManager.wait_for_condition` (line 328)

## casare_rpa.domain.credentials

**2 unused functions**


- `CredentialAwareMixin.resolve_oauth_credentials` (line 419)
- `resolve_node_credential` (line 619)

## casare_rpa.domain.decorators

**5 unused functions**


- `executable_node` (line 18)
- `wrapped_define` (line 45)
- `node_schema` (line 56)
- `decorator` (line 93)
- `wrapped_init` (line 102)

## casare_rpa.domain.entities.base_node

**3 unused functions**


- `BaseNode.set_breakpoint` (line 278)
- `BaseNode.has_breakpoint` (line 290)
- `BaseNode.get_debug_info` (line 294)

## casare_rpa.domain.entities.execution_state

**4 unused functions**


- `ExecutionState.project_context` (line 115)
- `ExecutionState.has_project_context` (line 120)
- `ExecutionState.get_execution_path` (line 227)
- `ExecutionState.get_errors` (line 247)

## casare_rpa.domain.entities.node_connection

**6 unused functions**


- `NodeConnection.source_node` (line 41)
- `NodeConnection.source_port` (line 46)
- `NodeConnection.target_node` (line 51)
- `NodeConnection.target_port` (line 56)
- `NodeConnection.source_id` (line 61)
- `NodeConnection.target_id` (line 66)

## casare_rpa.domain.entities.project.credentials

**3 unused functions**


- `CredentialBindingsFile.get_binding` (line 90)
- `CredentialBindingsFile.set_binding` (line 94)
- `CredentialBindingsFile.remove_binding` (line 98)

## casare_rpa.domain.entities.project.project

**4 unused functions**


- `Project.scenarios_dir` (line 69)
- `Project.project_file` (line 76)
- `Project.variables_file` (line 83)
- `Project.credentials_file` (line 90)

## casare_rpa.domain.entities.project.scenario

**4 unused functions**


- `Scenario.file_path` (line 93)
- `Scenario.file_path` (line 98)
- `Scenario.get_variable_value` (line 181)
- `Scenario.set_variable_value` (line 194)

## casare_rpa.domain.entities.tenant

**7 unused functions**


- `Tenant.robot_count` (line 118)
- `Tenant.can_add_robot` (line 123)
- `Tenant.has_robot` (line 154)
- `Tenant.add_admin` (line 158)
- `Tenant.remove_admin` (line 165)
- `Tenant.is_admin` (line 172)
- `Tenant.update_settings` (line 186)

## casare_rpa.domain.entities.workflow

**5 unused functions**


- `WorkflowSchema.add_connection` (line 86)
- `WorkflowSchema.remove_connection` (line 105)
- `WorkflowSchema.get_node` (line 132)
- `WorkflowSchema.get_connections_from` (line 144)
- `WorkflowSchema.get_connections_to` (line 156)

## casare_rpa.domain.entities.workflow_schedule

**2 unused functions**


- `WorkflowSchedule.success_rate` (line 171)
- `WorkflowSchedule.frequency_display` (line 178)

## casare_rpa.domain.errors.context

**2 unused functions**


- `ErrorContext.is_retryable` (line 120)
- `ErrorContext.is_ui_error` (line 131)

## casare_rpa.domain.errors.registry

**5 unused functions**


- `ErrorHandlerRegistry.register_node_handler` (line 52)
- `ErrorHandlerRegistry.register_category_handler` (line 65)
- `ErrorHandlerRegistry.register_global_handler` (line 80)
- `ErrorHandlerRegistry.unregister_custom_handler` (line 104)
- `reset_error_handler_registry` (line 371)

## casare_rpa.domain.events

**6 unused functions**


- `EventBus.get_handler_count` (line 190)
- `reset_event_bus` (line 236)
- `EventLogger.handle_event` (line 266)
- `EventRecorder.handle_event` (line 308)
- `EventRecorder.get_recorded_events` (line 318)
- `EventRecorder.export_to_dict` (line 322)

## casare_rpa.domain.orchestrator.entities.job

**1 unused functions**


- `Job.duration_formatted` (line 133)

## casare_rpa.domain.orchestrator.entities.robot

**6 unused functions**


- `Robot.current_jobs` (line 75)
- `Robot.is_available` (line 84)
- `Robot.utilization` (line 96)
- `Robot.assign_workflow` (line 190)
- `Robot.unassign_workflow` (line 199)
- `Robot.is_assigned_to_workflow` (line 208)

## casare_rpa.domain.orchestrator.entities.schedule

**1 unused functions**


- `Schedule.success_rate` (line 64)

## casare_rpa.domain.orchestrator.entities.workflow

**1 unused functions**


- `Workflow.success_rate` (line 58)

## casare_rpa.domain.orchestrator.repositories.robot_repository

**2 unused functions**


- `RobotRepository.get_all_online` (line 23)
- `RobotRepository.get_by_environment` (line 28)

## casare_rpa.domain.orchestrator.repositories.trigger_repository

**3 unused functions**


- `TriggerRepository.get_by_scenario` (line 28)
- `TriggerRepository.get_by_type` (line 38)
- `TriggerRepository.delete_by_scenario` (line 53)

## casare_rpa.domain.orchestrator.services.robot_selection_service

**3 unused functions**


- `RobotSelectionService.select_robot_for_node` (line 121)
- `RobotSelectionService.get_robots_by_capability` (line 237)
- `RobotSelectionService.calculate_robot_scores` (line 266)

## casare_rpa.domain.orchestrator.value_objects.node_robot_override

**2 unused functions**


- `NodeRobotOverride.is_specific_robot` (line 57)
- `NodeRobotOverride.is_capability_based` (line 66)

## casare_rpa.domain.ports.port_type_interfaces

**1 unused functions**


- `PortTypeRegistryProtocol.get_compatible_types` (line 127)

## casare_rpa.domain.protocols.credential_protocols

**3 unused functions**


- `ExecutionContextProtocol.resources` (line 125)
- `ExecutionContextProtocol.has_project_context` (line 130)
- `ExecutionContextProtocol.project_context` (line 135)

## casare_rpa.domain.repositories.project_repository

**2 unused functions**


- `ProjectRepository.get_project_credentials` (line 211)
- `ProjectRepository.get_global_credentials` (line 237)

## casare_rpa.domain.services.execution_orchestrator

**8 unused functions**


- `ExecutionOrchestrator.find_trigger_node` (line 116)
- `ExecutionOrchestrator.is_trigger_node` (line 135)
- `ExecutionOrchestrator.should_stop_on_error` (line 379)
- `ExecutionOrchestrator.handle_control_flow` (line 405)
- `ExecutionOrchestrator.validate_execution_order` (line 458)
- `ExecutionOrchestrator.find_loop_body_nodes` (line 505)
- `ExecutionOrchestrator.find_try_body_nodes` (line 545)
- `ExecutionOrchestrator.get_all_nodes` (line 641)

## casare_rpa.domain.services.project_context

**10 unused functions**


- `ProjectContext.project` (line 70)
- `ProjectContext.project_id` (line 75)
- `ProjectContext.project_name` (line 80)
- `ProjectContext.scenario` (line 85)
- `ProjectContext.scenario_id` (line 90)
- `ProjectContext.scenario_name` (line 95)
- `ProjectContext.get_merged_variables` (line 136)
- `ProjectContext.get_all_credential_aliases` (line 228)
- `ProjectContext.get_retry_count` (line 283)
- `ProjectContext.get_default_browser` (line 292)

## casare_rpa.domain.services.variable_resolver

**3 unused functions**


- `replace_match` (line 51)
- `extract_variable_names` (line 96)
- `has_variables` (line 116)

## casare_rpa.domain.validation.rules

**1 unused functions**


- `find_reachable_nodes` (line 264)

## casare_rpa.domain.validation.types

**5 unused functions**


- `ValidationResult.warnings` (line 54)
- `ValidationResult.error_count` (line 59)
- `ValidationResult.warning_count` (line 64)
- `ValidationResult.add_info` (line 105)
- `ValidationResult.merge` (line 121)

## casare_rpa.domain.validation.validators

**2 unused functions**


- `validate_node` (line 64)
- `validate_connections` (line 80)

## casare_rpa.domain.value_objects.log_entry

**1 unused functions**


- `LogLevel.severity` (line 54)

## casare_rpa.domain.value_objects.port

**3 unused functions**


- `Port.data_type` (line 80)
- `Port.label` (line 85)
- `Port.required` (line 90)

## casare_rpa.domain.value_objects.types

**2 unused functions**


- `ErrorCode.category` (line 256)
- `ErrorCode.is_retryable` (line 275)

## casare_rpa.domain.workflow.templates

**10 unused functions**


- `TemplateUsageStats.success_rate` (line 356)
- `TemplateReview.mark_helpful` (line 560)
- `TemplateReview.helpfulness_score` (line 573)
- `TemplateVersion.create_from_template` (line 717)
- `WorkflowTemplate.file_path` (line 880)
- `WorkflowTemplate.file_path` (line 885)
- `WorkflowTemplate.category` (line 895)
- `WorkflowTemplate.remove_parameter` (line 914)
- `WorkflowTemplate.get_required_parameters` (line 946)
- `WorkflowTemplate.get_parameters_by_group` (line 950)

## casare_rpa.domain.workflow.versioning

**17 unused functions**


- `SemanticVersion.with_prerelease` (line 122)
- `SemanticVersion.with_build` (line 132)
- `SemanticVersion.is_compatible_with` (line 142)
- `SemanticVersion.is_prerelease` (line 160)
- `CompatibilityResult.has_breaking_changes` (line 240)
- `CompatibilityResult.error_count` (line 245)
- `VersionDiff.has_changes` (line 278)
- `WorkflowVersion.is_draft` (line 360)
- `WorkflowVersion.is_deprecated` (line 368)
- `WorkflowVersion.can_modify` (line 380)
- `VersionHistory.active_version` (line 486)
- `VersionHistory.latest_version` (line 493)
- `VersionHistory.version_count` (line 500)
- `VersionHistory.activate_version` (line 548)
- `VersionHistory.can_rollback_to` (line 852)
- `VersionHistory.get_versions_by_status` (line 880)
- `VersionHistory.get_version_timeline` (line 884)

## casare_rpa.infrastructure.agent.heartbeat_service

**4 unused functions**


- `HeartbeatService.send_immediate` (line 272)
- `HeartbeatService.last_heartbeat` (line 282)
- `HeartbeatService.total_heartbeats` (line 287)
- `HeartbeatService.consecutive_failures` (line 292)

## casare_rpa.infrastructure.agent.job_executor

**6 unused functions**


- `JobExecutor.cancel_job` (line 250)
- `JobExecutor.clear_result` (line 279)
- `JobExecutor.active_job_count` (line 284)
- `_ProgressTracker.on_node_started` (line 304)
- `_ProgressTracker.on_node_completed` (line 325)
- `_ProgressTracker.on_node_error` (line 346)

## casare_rpa.infrastructure.agent.log_handler

**5 unused functions**


- `RobotLogHandler.set_send_callback` (line 103)
- `RobotLogHandler.min_level` (line 134)
- `RobotLogHandler.min_level` (line 139)
- `RobotLogHandler.sink` (line 143)
- `create_robot_log_handler` (line 317)

## casare_rpa.infrastructure.agent.robot_agent

**3 unused functions**


- `RobotAgent.is_registered` (line 544)
- `RobotAgent.active_job_count` (line 549)
- `RobotAgent.active_job_ids` (line 554)

## casare_rpa.infrastructure.agent.robot_config

**4 unused functions**


- `RobotConfig.uses_mtls` (line 175)
- `RobotConfig.uses_api_key` (line 180)
- `RobotConfig.hostname` (line 185)
- `RobotConfig.os_info` (line 190)

## casare_rpa.infrastructure.analytics.aggregation_strategies

**8 unused functions**


- `DimensionalBucket.avg_value` (line 358)
- `DimensionalAggregationStrategy.get_top_dimensions` (line 452)
- `DimensionalAggregationStrategy.get_sum` (line 466)
- `DimensionalAggregationStrategy.get_avg` (line 469)
- `AggregationStrategyFactory.create_time_based` (line 624)
- `AggregationStrategyFactory.create_statistical` (line 637)
- `AggregationStrategyFactory.create_dimensional` (line 642)
- `AggregationStrategyFactory.create_rolling_window` (line 655)

## casare_rpa.infrastructure.analytics.bottleneck_detector

**2 unused functions**


- `NodeExecutionStats.success_rate` (line 85)
- `NodeExecutionStats.failure_rate` (line 92)

## casare_rpa.infrastructure.analytics.execution_analyzer

**2 unused functions**


- `ExecutionAnalysisResult.success_rate` (line 141)
- `ExecutionAnalysisResult.failure_rate` (line 148)

## casare_rpa.infrastructure.analytics.metric_calculators

**3 unused functions**


- `MetricsDataSource.get_job_records` (line 29)
- `MetricsDataSource.get_healing_data` (line 38)
- `MetricsDataSource.get_error_data` (line 42)

## casare_rpa.infrastructure.analytics.metric_models

**5 unused functions**


- `WorkflowMetrics.success_rate` (line 108)
- `WorkflowMetrics.failure_rate` (line 115)
- `RobotPerformanceMetrics.utilization_percent` (line 186)
- `RobotPerformanceMetrics.success_rate` (line 194)
- `RobotPerformanceMetrics.availability_percent` (line 201)

## casare_rpa.infrastructure.analytics.metric_storage

**5 unused functions**


- `WorkflowMetricsData.success_rate` (line 93)
- `WorkflowMetricsData.failure_rate` (line 100)
- `RobotMetricsData.utilization_percent` (line 146)
- `RobotMetricsData.success_rate` (line 154)
- `RobotMetricsData.availability_percent` (line 161)

## casare_rpa.infrastructure.analytics.metrics_aggregator

**10 unused functions**


- `MetricsAggregator.configure_costs` (line 104)
- `MetricsAggregator.configure_sla` (line 117)
- `MetricsAggregator.record_job_execution` (line 131)
- `MetricsAggregator.record_queue_depth` (line 176)
- `MetricsAggregator.record_healing_result` (line 180)
- `MetricsAggregator.compare_versions` (line 395)
- `MetricsAggregator.generate_report` (line 410)
- `MetricsAggregator.export_csv` (line 463)
- `MetricsAggregator.reset_instance` (line 494)
- `get_metrics_aggregator` (line 502)

## casare_rpa.infrastructure.analytics.process_mining

**8 unused functions**


- `ExecutionTrace.variant` (line 109)
- `ExecutionTrace.total_duration_ms` (line 115)
- `ExecutionTrace.activity_sequence` (line 122)
- `ExecutionTrace.success_rate` (line 127)
- `ProcessModel.get_edge_frequency` (line 179)
- `ProcessModel.get_variant_path` (line 286)
- `ProcessModel.get_all_variant_paths` (line 297)
- `ProcessMiner.record_trace` (line 1172)

## casare_rpa.infrastructure.auth.robot_api_keys

**5 unused functions**


- `RobotApiKey.is_valid` (line 118)
- `RobotApiKey.status` (line 123)
- `RobotApiKeyService.list_keys_for_robot` (line 402)
- `RobotApiKeyService.rotate_key` (line 445)
- `RobotApiKeyService.delete_expired_keys` (line 491)

## casare_rpa.infrastructure.browser.healing.anchor_healer

**1 unused functions**


- `AnchorHealer.find_nearby_elements` (line 613)

## casare_rpa.infrastructure.browser.healing.cv_healer

**7 unused functions**


- `OCRMatch.center_x` (line 109)
- `OCRMatch.center_y` (line 114)
- `TemplateMatch.center_x` (line 155)
- `TemplateMatch.center_y` (line 160)
- `CVHealer.is_available` (line 332)
- `CVHealer.find_text_on_page` (line 1177)
- `CVHealer.find_template_on_page` (line 1218)

## casare_rpa.infrastructure.browser.healing.healing_chain

**7 unused functions**


- `HealingChainResult.cv_click_coordinates` (line 76)
- `HealingChainResult.is_cv_result` (line 95)
- `SelectorHealingChain.capture_element_context` (line 186)
- `SelectorHealingChain.locate_element` (line 250)
- `SelectorHealingChain.healing_budget_ms` (line 632)
- `SelectorHealingChain.healing_budget_ms` (line 637)
- `create_healing_chain` (line 643)

## casare_rpa.infrastructure.browser.healing.models

**6 unused functions**


- `BoundingRect.center_x` (line 67)
- `BoundingRect.center_y` (line 72)
- `BoundingRect.distance_to` (line 86)
- `BoundingRect.edge_distance_to` (line 100)
- `AnchorElement.is_stable` (line 165)
- `SpatialContext.get_best_anchor` (line 216)

## casare_rpa.infrastructure.browser.healing.telemetry

**6 unused functions**


- `SelectorStats.success_rate` (line 132)
- `SelectorStats.healing_rate` (line 139)
- `SelectorStats.healing_success_rate` (line 146)
- `HealingTelemetry.get_selector_stats` (line 336)
- `HealingTelemetry.cleanup_old_events` (line 449)
- `reset_healing_telemetry` (line 559)

## casare_rpa.infrastructure.config.cloudflare_config

**4 unused functions**


- `CloudflareConfig.production` (line 44)
- `CloudflareConfig.local` (line 53)
- `CloudflareConfig.is_production` (line 62)
- `CloudflareConfig.is_secure` (line 67)

## casare_rpa.infrastructure.events.monitoring_events

**1 unused functions**


- `MonitoringEventBus.clear_all` (line 257)

## casare_rpa.infrastructure.execution.dbos_executor

**2 unused functions**


- `DBOSWorkflowExecutor.clear_checkpoint` (line 602)
- `start_durable_workflow` (line 645)

## casare_rpa.infrastructure.execution.debug_executor

**6 unused functions**


- `DebugExecutor.state` (line 172)
- `DebugExecutor.session` (line 177)
- `DebugExecutor.get_execution_records` (line 453)
- `DebugExecutor.get_current_record` (line 464)
- `DebugExecutor.get_variable_history` (line 473)
- `DebugExecutor.get_node_execution_info` (line 493)

## casare_rpa.infrastructure.execution.execution_context

**16 unused functions**


- `ExecutionContext.workflow_name` (line 346)
- `ExecutionContext.mode` (line 351)
- `ExecutionContext.started_at` (line 356)
- `ExecutionContext.completed_at` (line 361)
- `ExecutionContext.variables` (line 366)
- `ExecutionContext.current_node_id` (line 371)
- `ExecutionContext.execution_path` (line 376)
- `ExecutionContext.stopped` (line 386)
- `ExecutionContext.browser` (line 391)
- `ExecutionContext.browser` (line 396)
- `ExecutionContext.browser_contexts` (line 404)
- `ExecutionContext.pages` (line 409)
- `ExecutionContext.active_page` (line 414)
- `ExecutionContext.active_page` (line 419)
- `ExecutionContext.project_context` (line 424)
- `ExecutionContext.has_project_context` (line 429)

## casare_rpa.infrastructure.execution.recovery_strategies

**8 unused functions**


- `CircuitBreaker.is_open` (line 104)
- `CircuitBreaker.is_half_open` (line 117)
- `EscalateStrategy.resolve_escalation` (line 785)
- `RecoveryStrategyRegistry.register_strategy` (line 960)
- `RecoveryStrategyRegistry.get_or_create_circuit_breaker` (line 985)
- `RecoveryStrategyRegistry.get_circuit_breaker` (line 1004)
- `RecoveryStrategyRegistry.screenshot_capture` (line 1017)
- `reset_recovery_strategy_registry` (line 1080)

## casare_rpa.infrastructure.logging.log_cleanup

**3 unused functions**


- `LogCleanupJob.retention_days` (line 211)
- `LogCleanupJob.retention_days` (line 216)
- `init_log_cleanup_job` (line 246)

## casare_rpa.infrastructure.logging.log_streaming_service

**6 unused functions**


- `LogStreamingService.receive_single_log` (line 228)
- `LogStreamingService.buffer_log` (line 428)
- `LogStreamingService.get_buffered_logs` (line 446)
- `LogStreamingService.get_subscriber_count` (line 458)
- `init_log_streaming_service` (line 528)
- `reset_log_streaming_service` (line 551)

## casare_rpa.infrastructure.observability.facade

**6 unused functions**


- `Observability.is_configured` (line 256)
- `Observability.gauge` (line 434)
- `Observability.trace` (line 466)
- `Observability.capture_stdout` (line 537)
- `Observability.captured_output` (line 560)
- `configure_observability` (line 657)

## casare_rpa.infrastructure.observability.logging

**4 unused functions**


- `get_ui_log_sink` (line 334)
- `trace_context_patcher` (line 362)
- `get_span_logger` (line 539)
- `log_with_trace` (line 552)

## casare_rpa.infrastructure.observability.metrics

**24 unused functions**


- `JobMetrics.success_rate` (line 81)
- `JobMetrics.average_duration_seconds` (line 88)
- `JobMetrics.average_queue_wait_seconds` (line 96)
- `RobotMetrics.utilization_percent` (line 118)
- `RobotMetrics.success_rate` (line 126)
- `RPAMetricsCollector.active_jobs_callback` (line 259)
- `RPAMetricsCollector.queue_throughput_callback` (line 269)
- `RPAMetricsCollector.record_job_enqueue` (line 322)
- `RPAMetricsCollector.record_job_start` (line 360)
- `RPAMetricsCollector.record_job_complete` (line 415)
- `RPAMetricsCollector.record_job_retry` (line 488)
- `RPAMetricsCollector.record_job_cancel` (line 517)
- `RPAMetricsCollector.track_node_execution` (line 636)
- `RPAMetricsCollector.get_node_metrics` (line 704)
- `RPAMetricsCollector.record_healing_attempt` (line 716)
- `RPAMetricsCollector.record_browser_acquired` (line 784)
- `RPAMetricsCollector.record_browser_released` (line 789)
- `RPAMetricsCollector.reset_metrics` (line 810)
- `MetricsExporter.add_json_callback` (line 1030)
- `MetricsExporter.add_dict_callback` (line 1040)
- `MetricsExporter.add_prometheus_callback` (line 1050)
- `MetricsExporter.get_last_snapshot` (line 1073)
- `MetricsExporter.get_snapshot_json` (line 1077)
- `MetricsExporter.get_snapshot_dict` (line 1083)

## casare_rpa.infrastructure.observability.stdout_capture

**2 unused functions**


- `_CallbackWriter.encoding` (line 144)
- `get_output_capture` (line 205)

## casare_rpa.infrastructure.observability.telemetry

**20 unused functions**


- `TelemetryProvider.queue_depth_callback` (line 562)
- `TelemetryProvider.robot_utilization_callback` (line 575)
- `record_queue_depth` (line 871)
- `record_robot_utilization` (line 876)
- `trace_workflow` (line 888)
- `decorator` (line 908)
- `sync_wrapper` (line 910)
- `async_wrapper` (line 962)
- `trace_node` (line 1023)
- `decorator` (line 1043)
- `sync_wrapper` (line 1045)
- `async_wrapper` (line 1095)
- `trace_async` (line 1153)
- `decorator` (line 1174)
- `wrapper` (line 1176)
- `DBOSSpanContext.create_step_span` (line 1333)
- `setup_loguru_otel_sink` (line 1361)
- `otel_context_patcher` (line 1372)
- `inject_context_to_headers` (line 1425)
- `extract_context_from_headers` (line 1445)

## casare_rpa.infrastructure.orchestrator.api.adapters

**2 unused functions**


- `MonitoringDataAdapter.has_db` (line 54)
- `MonitoringDataAdapter.get_job_details` (line 433)

## casare_rpa.infrastructure.orchestrator.api.auth

**12 unused functions**


- `AuthenticatedUser.is_admin` (line 76)
- `require_role` (line 243)
- `role_checker` (line 259)
- `get_current_user` (line 279)
- `optional_auth` (line 303)
- `configure_robot_authenticator` (line 488)
- `verify_robot_token` (line 509)
- `optional_robot_token` (line 559)
- `get_tenant_id` (line 588)
- `require_tenant` (line 617)
- `require_same_tenant` (line 645)
- `get_current_user_or_robot` (line 694)

## casare_rpa.infrastructure.orchestrator.api.database

**2 unused functions**


- `MonitoringDatabase.get_job_details` (line 222)
- `create_db_pool` (line 684)

## casare_rpa.infrastructure.orchestrator.api.dependencies

**2 unused functions**


- `DatabasePoolManager.pool` (line 96)
- `DatabasePoolManager.is_healthy` (line 101)

## casare_rpa.infrastructure.orchestrator.api.main

**10 unused functions**


- `lifespan` (line 138)
- `RequestIdMiddleware.dispatch` (line 250)
- `validation_exception_handler` (line 273)
- `generic_exception_handler` (line 310)
- `http_exception_handler` (line 334)
- `health_check` (line 497)
- `detailed_health_check` (line 523)
- `readiness_check` (line 576)
- `liveness_check` (line 609)
- `root` (line 620)

## casare_rpa.infrastructure.orchestrator.api.rate_limit

**12 unused functions**


- `get_user_or_ip` (line 86)
- `get_ip_only` (line 105)
- `limit_high` (line 148)
- `limit_standard` (line 157)
- `limit_low` (line 166)
- `limit_auth` (line 175)
- `limit_progress` (line 184)
- `limit_custom` (line 193)
- `decorator` (line 205)
- `rate_limit_exceeded_handler` (line 222)
- `setup_rate_limiting` (line 274)
- `get_rate_limit_info` (line 306)

## casare_rpa.infrastructure.orchestrator.api.responses

**2 unused functions**


- `ResponseMeta.serialize_timestamp` (line 78)
- `success_response` (line 143)

## casare_rpa.infrastructure.orchestrator.api.routers.analytics

**6 unused functions**


- `get_process_insights` (line 404)
- `list_workflows_with_traces` (line 454)
- `get_node_performance` (line 573)
- `analyze_execution` (line 643)
- `get_traces` (line 893)
- `clear_traces` (line 919)

## casare_rpa.infrastructure.orchestrator.api.routers.jobs

**3 unused functions**


- `set_db_pool` (line 25)
- `cancel_job` (line 70)
- `retry_job` (line 162)

## casare_rpa.infrastructure.orchestrator.api.routers.metrics

**7 unused functions**


- `get_job_details` (line 196)
- `get_activity` (line 277)
- `get_metrics_snapshot` (line 332)
- `get_prometheus_metrics` (line 354)
- `metrics_websocket_stream` (line 379)
- `broadcast_metrics_to_websockets` (line 458)
- `get_websocket_connection_count` (line 490)

## casare_rpa.infrastructure.orchestrator.api.routers.robots

**3 unused functions**


- `set_db_pool` (line 24)
- `list_robots` (line 174)
- `robot_heartbeat` (line 442)

## casare_rpa.infrastructure.orchestrator.api.routers.schedules

**7 unused functions**


- `set_db_pool` (line 90)
- `ScheduleRequest.validate_cron` (line 123)
- `ScheduleRequest.validate_execution_mode` (line 133)
- `create_schedule` (line 529)
- `list_schedules` (line 626)
- `trigger_schedule_now` (line 896)
- `get_upcoming_schedules` (line 1011)

## casare_rpa.infrastructure.orchestrator.api.routers.websockets

**6 unused functions**


- `websocket_live_jobs` (line 154)
- `websocket_robot_status` (line 200)
- `websocket_queue_metrics` (line 245)
- `on_job_status_changed` (line 359)
- `on_robot_heartbeat` (line 374)
- `on_queue_depth_changed` (line 391)

## casare_rpa.infrastructure.orchestrator.api.routers.workflows

**5 unused functions**


- `set_db_pool` (line 46)
- `WorkflowSubmissionRequest.validate_trigger_type` (line 141)
- `WorkflowSubmissionRequest.validate_execution_mode` (line 149)
- `set_trigger_manager` (line 210)
- `upload_workflow` (line 754)

## casare_rpa.infrastructure.orchestrator.client

**6 unused functions**


- `OrchestratorClient.cancel_job` (line 377)
- `OrchestratorClient.retry_job` (line 382)
- `OrchestratorClient.get_activity` (line 403)
- `OrchestratorClient.trigger_schedule` (line 428)
- `get_orchestrator_client` (line 536)
- `configure_orchestrator` (line 544)

## casare_rpa.infrastructure.orchestrator.communication.cloud_service

**1 unused functions**


- `CloudService.dispatch_job` (line 80)

## casare_rpa.infrastructure.orchestrator.communication.realtime_service

**2 unused functions**


- `RobotStatusTracker.on_robot_update` (line 280)
- `RobotStatusTracker.get_robot_status` (line 292)

## casare_rpa.infrastructure.orchestrator.communication.websocket_client

**7 unused functions**


- `RobotClient.report_progress` (line 552)
- `RobotClient.report_job_complete` (line 574)
- `RobotClient.send_log` (line 636)
- `RobotClient.send_log_batch` (line 665)
- `RobotClient.is_paused` (line 687)
- `RobotClient.active_job_count` (line 692)
- `RobotClient.is_available` (line 697)

## casare_rpa.infrastructure.orchestrator.communication.websocket_server

**6 unused functions**


- `RobotConnection.is_available` (line 62)
- `OrchestratorServer.cancel_job` (line 634)
- `OrchestratorServer.request_status` (line 670)
- `OrchestratorServer.is_robot_connected` (line 712)
- `OrchestratorServer.connected_count` (line 717)
- `OrchestratorServer.available_count` (line 722)

## casare_rpa.infrastructure.orchestrator.health_endpoints

**3 unused functions**


- `health_check` (line 16)
- `liveness_check` (line 22)
- `readiness_check` (line 28)

## casare_rpa.infrastructure.orchestrator.persistence.local_robot_repository

**2 unused functions**


- `LocalRobotRepository.get_all_online` (line 31)
- `LocalRobotRepository.get_by_environment` (line 40)

## casare_rpa.infrastructure.orchestrator.persistence.local_trigger_repository

**3 unused functions**


- `LocalTriggerRepository.get_by_scenario` (line 38)
- `LocalTriggerRepository.get_by_type` (line 56)
- `LocalTriggerRepository.delete_by_scenario` (line 74)

## casare_rpa.infrastructure.orchestrator.resilience.error_recovery

**18 unused functions**


- `ErrorRecoveryManager.handle_job_error` (line 204)
- `ErrorRecoveryManager.handle_robot_crash` (line 295)
- `ErrorRecoveryManager.get_recent_actions` (line 390)
- `HealthMetrics.is_healthy` (line 422)
- `HealthMonitor.record_request` (line 571)
- `HealthMonitor.get_robot_health` (line 670)
- `HealthMonitor.get_all_health` (line 674)
- `HealthMonitor.get_unhealthy_robots` (line 678)
- `HealthMonitor.get_overall_health` (line 686)
- `SecurityManager.generate_token` (line 796)
- `SecurityManager.validate_token` (line 827)
- `SecurityManager.revoke_token` (line 848)
- `SecurityManager.revoke_robot_tokens` (line 863)
- `SecurityManager.check_rate_limit` (line 912)
- `SecurityManager.get_rate_limit_remaining` (line 944)
- `SecurityManager.cleanup_expired_tokens` (line 955)
- `SecurityManager.cleanup_stale_rate_limits` (line 969)
- `SecurityManager.active_token_count` (line 1006)

## casare_rpa.infrastructure.orchestrator.resilience.robot_recovery

**2 unused functions**


- `RobotRecoveryManager.recovery_history` (line 375)
- `RobotRecoveryManager.manually_recover_robot` (line 997)

## casare_rpa.infrastructure.orchestrator.rest_endpoints

**7 unused functions**


- `list_robots` (line 123)
- `list_jobs` (line 211)
- `query_logs` (line 250)
- `get_log_stats` (line 301)
- `get_log_streaming_metrics` (line 329)
- `get_log_cleanup_status` (line 342)
- `trigger_log_cleanup` (line 355)

## casare_rpa.infrastructure.orchestrator.robot_manager

**2 unused functions**


- `ConnectedRobot.status` (line 34)
- `ConnectedRobot.available_slots` (line 43)

## casare_rpa.infrastructure.orchestrator.scheduling

**2 unused functions**


- `reset_scheduler_state` (line 201)
- `set_state` (line 212)

## casare_rpa.infrastructure.orchestrator.scheduling.advanced_scheduler

**10 unused functions**


- `AdvancedScheduler.sla_monitor` (line 167)
- `AdvancedScheduler.dependency_tracker` (line 172)
- `AdvancedScheduler.register_calendar` (line 218)
- `AdvancedScheduler.get_schedules_by_status` (line 372)
- `AdvancedScheduler.trigger_event` (line 376)
- `AdvancedScheduler.check_missed_runs` (line 499)
- `AdvancedScheduler.execute_catch_up` (line 525)
- `AdvancedScheduler.get_sla_report` (line 803)
- `AdvancedScheduler.get_dependency_graph` (line 860)
- `AdvancedScheduler.validate_dependency_graph` (line 878)

## casare_rpa.infrastructure.orchestrator.scheduling.calendar

**16 unused functions**


- `BlackoutPeriod.overlaps` (line 224)
- `BusinessCalendar.timezone` (line 370)
- `BusinessCalendar.config` (line 375)
- `BusinessCalendar.add_holiday` (line 379)
- `BusinessCalendar.remove_holiday` (line 391)
- `BusinessCalendar.add_blackout` (line 410)
- `BusinessCalendar.remove_blackout` (line 422)
- `BusinessCalendar.remove_custom_date` (line 443)
- `BusinessCalendar.set_working_hours` (line 450)
- `BusinessCalendar.get_holidays_for_year` (line 464)
- `BusinessCalendar.count_working_days` (line 717)
- `BusinessCalendar.add_working_days` (line 739)
- `BusinessCalendar.get_working_hours_remaining` (line 764)
- `BusinessCalendar.create_us_calendar` (line 790)
- `BusinessCalendar.create_uk_calendar` (line 812)
- `BusinessCalendar.create_24_7_calendar` (line 834)

## casare_rpa.infrastructure.orchestrator.scheduling.job_assignment

**16 unused functions**


- `RobotPresenceProtocol.robot_id` (line 151)
- `RobotPresenceProtocol.status` (line 161)
- `RobotPresenceProtocol.current_jobs` (line 176)
- `RobotPresenceProtocol.max_concurrent_jobs` (line 181)
- `RobotPresenceProtocol.tags` (line 186)
- `RobotPresenceProtocol.environment` (line 191)
- `RobotPresenceProtocol.capabilities` (line 196)
- `RobotInfo.is_available` (line 223)
- `RobotInfo.utilization` (line 228)
- `JobAssignmentEngine.weights` (line 479)
- `JobAssignmentEngine.weights` (line 484)
- `JobAssignmentEngine.record_job_completion` (line 838)
- `JobAssignmentEngine.clear_state_affinity` (line 858)
- `JobAssignmentEngine.cleanup_expired_state` (line 872)
- `JobAssignmentEngine.get_assignment_stats` (line 881)
- `assign_job_to_robot` (line 907)

## casare_rpa.infrastructure.orchestrator.scheduling.schedule_conflict_resolver

**12 unused functions**


- `DependencyTracker.wait_for_dependencies` (line 196)
- `DependencyTracker.get_latest_completion` (line 263)
- `DependencyTracker.get_completion_history` (line 269)
- `ConflictResolver.acquire_resource` (line 331)
- `ConflictResolver.release_resource` (line 361)
- `ConflictResolver.release_all_resources` (line 376)
- `ConflictResolver.get_resource_holders` (line 387)
- `ConflictResolver.has_conflict` (line 400)
- `DependencyGraphValidator.build_graph_from_dependencies` (line 450)
- `DependencyGraphValidator.get_execution_order` (line 501)
- `DependencyGraphValidator.get_all_upstream` (line 561)
- `DependencyGraphValidator.get_all_downstream` (line 582)

## casare_rpa.infrastructure.orchestrator.scheduling.schedule_models

**2 unused functions**


- `AdvancedSchedule.success_rate` (line 200)
- `AdvancedSchedule.sla_status` (line 207)

## casare_rpa.infrastructure.orchestrator.scheduling.schedule_optimizer

**12 unused functions**


- `SlidingWindowRateLimiter.max_executions` (line 55)
- `SlidingWindowRateLimiter.window_seconds` (line 60)
- `SlidingWindowRateLimiter.get_remaining_capacity` (line 110)
- `ExecutionOptimizer.active_count` (line 188)
- `ExecutionOptimizer.can_start_execution` (line 193)
- `ExecutionOptimizer.should_coalesce` (line 198)
- `ExecutionOptimizer.mark_pending` (line 224)
- `ExecutionOptimizer.mark_started` (line 234)
- `ExecutionOptimizer.get_execution_duration` (line 262)
- `ExecutionOptimizer.get_active_executions` (line 278)
- `PriorityQueue.peek` (line 325)
- `PriorityQueue.size_by_priority` (line 360)

## casare_rpa.infrastructure.orchestrator.scheduling.scheduling_strategies

**21 unused functions**


- `SchedulingStrategy.get_next_run_time` (line 45)
- `CronExpressionParser.get_available_aliases` (line 287)
- `CronSchedulingStrategy.expression` (line 315)
- `CronSchedulingStrategy.timezone` (line 320)
- `CronSchedulingStrategy.get_parsed` (line 324)
- `CronSchedulingStrategy.get_next_run_time` (line 330)
- `IntervalSchedulingStrategy.interval_seconds` (line 368)
- `IntervalSchedulingStrategy.timezone` (line 373)
- `IntervalSchedulingStrategy.get_next_run_time` (line 377)
- `OneTimeSchedulingStrategy.run_at` (line 430)
- `OneTimeSchedulingStrategy.timezone` (line 435)
- `OneTimeSchedulingStrategy.get_next_run_time` (line 439)
- `OneTimeSchedulingStrategy.mark_executed` (line 451)
- `EventDrivenStrategy.event_type` (line 492)
- `EventDrivenStrategy.event_source` (line 497)
- `EventDrivenStrategy.event_filter` (line 502)
- `EventDrivenStrategy.get_next_run_time` (line 506)
- `DependencySchedulingStrategy.depends_on` (line 553)
- `DependencySchedulingStrategy.wait_for_all` (line 558)
- `DependencySchedulingStrategy.trigger_on_success_only` (line 563)
- `DependencySchedulingStrategy.get_next_run_time` (line 567)

## casare_rpa.infrastructure.orchestrator.scheduling.sla_monitor

**11 unused functions**


- `SLAMonitor.add_alert_callback` (line 102)
- `SLAMonitor.remove_alert_callback` (line 113)
- `SLAMonitor.get_active_executions` (line 298)
- `SLAMonitor.get_failure_rate` (line 327)
- `SLAMonitor.get_percentile_duration` (line 368)
- `SLAMonitor.generate_report` (line 456)
- `SLAMonitor.clear_metrics` (line 509)
- `SLAAggregator.get_fleet_success_rate` (line 539)
- `SLAAggregator.get_fleet_status_summary` (line 571)
- `SLAAggregator.get_worst_performers` (line 594)
- `SLAAggregator.get_slowest_performers` (line 625)

## casare_rpa.infrastructure.orchestrator.scheduling.state_affinity

**12 unused functions**


- `RobotState.age_seconds` (line 73)
- `RobotState.idle_seconds` (line 78)
- `StateAffinityManager.touch_state` (line 326)
- `StateAffinityManager.get_all_state_for_workflow` (line 371)
- `StateAffinityManager.create_session` (line 387)
- `StateAffinityManager.end_session` (line 437)
- `StateAffinityManager.get_session_robot` (line 449)
- `StateAffinityManager.record_session_job` (line 454)
- `StateAffinityManager.register_migration_handler` (line 745)
- `StateAffinityManager.migrate_state` (line 760)
- `StateAffinityManager.clear_queue_attempts` (line 912)
- `StateAffinityManager.get_workflow_state_summary` (line 945)

## casare_rpa.infrastructure.orchestrator.server

**1 unused functions**


- `create_app` (line 86)

## casare_rpa.infrastructure.orchestrator.server_auth

**2 unused functions**


- `verify_api_key` (line 24)
- `verify_admin_api_key` (line 181)

## casare_rpa.infrastructure.orchestrator.server_lifecycle

**2 unused functions**


- `reset_orchestrator_state` (line 143)
- `lifespan` (line 226)

## casare_rpa.infrastructure.orchestrator.websocket_handlers

**4 unused functions**


- `robot_websocket` (line 31)
- `admin_websocket` (line 153)
- `log_stream_websocket` (line 210)
- `all_logs_stream_websocket` (line 256)

## casare_rpa.infrastructure.persistence.file_system_project_repository

**2 unused functions**


- `FileSystemProjectRepository.get_project_credentials` (line 267)
- `FileSystemProjectRepository.get_global_credentials` (line 291)

## casare_rpa.infrastructure.persistence.project_storage

**1 unused functions**


- `ProjectStorage.load_workflow` (line 501)

## casare_rpa.infrastructure.persistence.repositories.api_key_repository

**10 unused functions**


- `ApiKeyRepository.get_by_hash` (line 152)
- `ApiKeyRepository.get_valid_by_hash` (line 177)
- `ApiKeyRepository.list_for_robot` (line 207)
- `ApiKeyRepository.list_all` (line 249)
- `ApiKeyRepository.update_last_used` (line 296)
- `ApiKeyRepository.revoke` (line 327)
- `ApiKeyRepository.revoke_all_for_robot` (line 369)
- `ApiKeyRepository.delete_expired` (line 437)
- `ApiKeyRepository.count_for_robot` (line 469)
- `ApiKeyRepository.get_robot_id_by_hash` (line 502)

## casare_rpa.infrastructure.persistence.repositories.job_repository

**8 unused functions**


- `JobRepository.get_pending` (line 336)
- `JobRepository.get_queued` (line 345)
- `JobRepository.get_running` (line 354)
- `JobRepository.get_pending_for_robot` (line 363)
- `JobRepository.append_logs` (line 480)
- `JobRepository.calculate_duration` (line 505)
- `JobRepository.delete_old_jobs` (line 553)
- `JobRepository.claim_next_job` (line 583)

## casare_rpa.infrastructure.persistence.repositories.log_repository

**1 unused functions**


- `LogRepository.get_cleanup_history` (line 390)

## casare_rpa.infrastructure.persistence.repositories.node_override_repository

**3 unused functions**


- `NodeOverrideRepository.get_by_node` (line 201)
- `NodeOverrideRepository.delete_all_for_workflow` (line 427)
- `NodeOverrideRepository.get_override_map` (line 487)

## casare_rpa.infrastructure.persistence.repositories.robot_repository

**3 unused functions**


- `RobotRepository.add_current_job` (line 475)
- `RobotRepository.remove_current_job` (line 508)
- `RobotRepository.mark_stale_robots_offline` (line 568)

## casare_rpa.infrastructure.persistence.repositories.tenant_repository

**5 unused functions**


- `TenantRepository.get_by_name` (line 192)
- `TenantRepository.get_by_admin_email` (line 264)
- `TenantRepository.get_by_robot_id` (line 292)
- `TenantRepository.add_robot_to_tenant` (line 321)
- `TenantRepository.remove_robot_from_tenant` (line 355)

## casare_rpa.infrastructure.persistence.repositories.user_repository

**3 unused functions**


- `UserRepository.get_by_email` (line 295)
- `UserRepository.create_user` (line 320)
- `UserRepository.update_password` (line 366)

## casare_rpa.infrastructure.persistence.repositories.workflow_assignment_repository

**2 unused functions**


- `WorkflowAssignmentRepository.delete_all_for_workflow` (line 358)
- `WorkflowAssignmentRepository.get_workflows_for_robot` (line 420)

## casare_rpa.infrastructure.persistence.template_storage

**6 unused functions**


- `TemplateStorage.get_builtin` (line 337)
- `TemplateStorage.get_user_templates` (line 347)
- `TemplateStorage.get_category_counts` (line 357)
- `TemplateStorage.import_template` (line 373)
- `TemplateStorage.export_template` (line 416)
- `TemplateStorageFactory.create_for_project` (line 461)

## casare_rpa.infrastructure.queue.dlq_manager

**7 unused functions**


- `DLQManager.max_retries` (line 407)
- `DLQManager.handle_job_failure` (line 542)
- `DLQManager.list_dlq_entries` (line 712)
- `DLQManager.get_dlq_entry` (line 753)
- `DLQManager.retry_from_dlq` (line 781)
- `DLQManager.get_dlq_stats` (line 826)
- `DLQManager.purge_reprocessed` (line 857)

## casare_rpa.infrastructure.queue.memory_queue

**6 unused functions**


- `MemoryQueue.claim` (line 196)
- `MemoryQueue.extend_claim` (line 308)
- `MemoryQueue.get_jobs_by_status` (line 340)
- `MemoryQueue.get_jobs_by_robot` (line 358)
- `initialize_memory_queue` (line 462)
- `shutdown_memory_queue` (line 474)

## casare_rpa.infrastructure.queue.pgqueuer_consumer

**7 unused functions**


- `PgQueuerConsumer.state` (line 348)
- `PgQueuerConsumer.robot_id` (line 353)
- `PgQueuerConsumer.active_job_count` (line 358)
- `PgQueuerConsumer.add_state_callback` (line 367)
- `PgQueuerConsumer.remove_state_callback` (line 376)
- `PgQueuerConsumer.requeue_timed_out_jobs` (line 887)
- `PgQueuerConsumer.get_job_status` (line 916)

## casare_rpa.infrastructure.queue.pgqueuer_producer

**10 unused functions**


- `PgQueuerProducer.state` (line 320)
- `PgQueuerProducer.total_enqueued` (line 332)
- `PgQueuerProducer.total_cancelled` (line 337)
- `PgQueuerProducer.add_state_callback` (line 341)
- `PgQueuerProducer.remove_state_callback` (line 350)
- `PgQueuerProducer.enqueue_batch` (line 659)
- `PgQueuerProducer.cancel_job` (line 739)
- `PgQueuerProducer.get_job_status` (line 784)
- `PgQueuerProducer.get_queue_depth_by_priority` (line 868)
- `PgQueuerProducer.purge_old_jobs` (line 883)

## casare_rpa.infrastructure.realtime.supabase_realtime

**7 unused functions**


- `PresenceState.get_robot_by_id` (line 310)
- `SubscriptionManager.on_subscribe` (line 380)
- `RealtimeClient.state` (line 551)
- `RealtimeClient.subscription_manager` (line 566)
- `RealtimeClient.on_job_inserted` (line 583)
- `RealtimeClient.on_control_command` (line 592)
- `RealtimeClient.on_connection_state` (line 628)

## casare_rpa.infrastructure.resources.browser_resource_manager

**2 unused functions**


- `BrowserResourceManager.get_browser_contexts` (line 66)
- `BrowserResourceManager.set_page` (line 75)

## casare_rpa.infrastructure.resources.gmail_client

**5 unused functions**


- `GmailConfig.users_url` (line 49)
- `GmailClient.modify_labels` (line 810)
- `GmailClient.trash_message` (line 840)
- `GmailClient.untrash_message` (line 845)
- `GmailClient.get_labels` (line 855)

## casare_rpa.infrastructure.resources.google_client

**6 unused functions**


- `GoogleAPIClient.execute_request` (line 515)
- `GoogleAPIClient.execute_batch` (line 597)
- `GoogleAPIClient.batch_callback` (line 624)
- `GoogleAPIClient.credentials` (line 673)
- `GoogleAPIClient.rate_limit_stats` (line 683)
- `create_google_client` (line 689)

## casare_rpa.infrastructure.resources.google_docs_client

**1 unused functions**


- `GoogleDocsClient.delete_content` (line 599)

## casare_rpa.infrastructure.resources.google_drive_client

**6 unused functions**


- `DriveFile.is_folder` (line 163)
- `DriveFile.is_google_doc` (line 168)
- `GoogleDriveClient.export_file` (line 541)
- `GoogleDriveClient.update_file` (line 689)
- `GoogleDriveClient.get_about` (line 870)
- `GoogleDriveClient.empty_trash` (line 876)

## casare_rpa.infrastructure.resources.google_sheets_client

**1 unused functions**


- `GoogleSheetsClient.get_sheet_row_count` (line 771)

## casare_rpa.infrastructure.resources.llm_model_provider

**1 unused functions**


- `LLMModelProvider.refresh_cache` (line 368)

## casare_rpa.infrastructure.resources.llm_resource_manager

**5 unused functions**


- `LLMResourceManager.get_conversation` (line 692)
- `LLMResourceManager.clear_conversation` (line 696)
- `LLMResourceManager.delete_conversation` (line 703)
- `LLMResourceManager.metrics` (line 711)
- `LLMResourceManager.config` (line 716)

## casare_rpa.infrastructure.resources.telegram_client

**2 unused functions**


- `TelegramConfig.api_url` (line 41)
- `TelegramClient.edit_message_caption` (line 504)

## casare_rpa.infrastructure.resources.unified_resource_manager

**8 unused functions**


- `ResourceLease.time_remaining` (line 74)
- `ResourceLease.idle_time` (line 84)
- `JobResources.get_lease` (line 118)
- `JobResources.count_by_type` (line 125)
- `LRUResourceCache.max_size` (line 184)
- `LRUResourceCache.peek_lru` (line 241)
- `UnifiedResourceManager.release_all_job_resources` (line 1210)
- `UnifiedResourceManager.get_job_leases` (line 1288)

## casare_rpa.infrastructure.resources.whatsapp_client

**9 unused functions**


- `WhatsAppConfig.api_url` (line 46)
- `WhatsAppConfig.media_url` (line 51)
- `WhatsAppConfig.templates_url` (line 56)
- `WhatsAppClient.send_audio` (line 414)
- `WhatsAppClient.send_contacts` (line 534)
- `WhatsAppClient.mark_as_read` (line 608)
- `WhatsAppClient.list_templates` (line 631)
- `WhatsAppClient.upload_media` (line 657)
- `WhatsAppClient.get_media_url` (line 703)

## casare_rpa.infrastructure.security.api_key_store

**5 unused functions**


- `APIKeyStore.delete_key` (line 350)
- `APIKeyStore.list_providers` (line 371)
- `APIKeyStore.has_key` (line 376)
- `APIKeyStore.get_key_info` (line 394)
- `set_api_key` (line 437)

## casare_rpa.infrastructure.security.credential_provider

**7 unused functions**


- `VaultCredentialProvider.register_alias` (line 176)
- `VaultCredentialProvider.get_dynamic_credential` (line 277)
- `VaultCredentialProvider.invalidate_credential` (line 403)
- `VaultCredentialProvider.get_registered_aliases` (line 430)
- `VaultCredentialProvider.get_active_leases` (line 434)
- `create_credential_resolver` (line 465)
- `resolve_credentials_for_node` (line 480)

## casare_rpa.infrastructure.security.credential_store

**4 unused functions**


- `CredentialStore.get_credentials_for_dropdown` (line 512)
- `CredentialStore.rename_credential` (line 543)
- `CredentialStore.save_api_key` (line 564)
- `CredentialStore.save_username_password` (line 581)

## casare_rpa.infrastructure.security.merkle_audit

**6 unused functions**


- `MerkleAuditService.verify_chain` (line 292)
- `MerkleAuditService.compute_merkle_root` (line 454)
- `MerkleAuditService.generate_merkle_proof` (line 473)
- `MerkleAuditService.verify_merkle_proof` (line 517)
- `MerkleAuditService.export_audit_log` (line 546)
- `log_audit_event` (line 619)

## casare_rpa.infrastructure.security.providers.factory

**1 unused functions**


- `get_recommended_backend` (line 140)

## casare_rpa.infrastructure.security.providers.sqlite_vault

**1 unused functions**


- `create_development_vault` (line 472)

## casare_rpa.infrastructure.security.rbac

**22 unused functions**


- `Permission.permission_key` (line 146)
- `UserPermissions.is_cache_valid` (line 292)
- `UserPermissions.highest_priority_role` (line 298)
- `PermissionRegistry.register_many` (line 381)
- `RoleManager.load_system_roles` (line 433)
- `RoleManager.load_tenant_roles` (line 441)
- `RoleManager.get_system_role` (line 450)
- `RoleManager.get_system_role_by_name` (line 454)
- `RoleManager.get_all_system_roles` (line 482)
- `RoleManager.get_available_roles` (line 490)
- `RoleManager.create_custom_role` (line 496)
- `RoleManager.update_role_permissions` (line 557)
- `RoleManager.delete_custom_role` (line 596)
- `AuthorizationService.check_any_permission` (line 734)
- `AuthorizationService.check_all_permissions` (line 746)
- `AuthorizationService.invalidate_user_cache` (line 758)
- `AuthorizationService.get_available_permissions` (line 793)
- `require_permission` (line 822)
- `decorator` (line 841)
- `wrapper` (line 842)
- `create_authorization_service` (line 887)
- `get_default_permissions` (line 904)

## casare_rpa.infrastructure.security.rotation

**5 unused functions**


- `SecretRotationManager.unregister_policy` (line 196)
- `SecretRotationManager.get_rotation_history` (line 366)
- `SecretRotationManager.get_policies` (line 386)
- `SecretRotationManager.get_due_rotations` (line 390)
- `setup_rotation_for_credentials` (line 405)

## casare_rpa.infrastructure.security.tenancy

**21 unused functions**


- `Tenant.validate_slug` (line 381)
- `Tenant.is_subscription_valid` (line 397)
- `Tenant.get_quota_remaining` (line 428)
- `APIKey.is_valid` (line 493)
- `TenantContextManager.current` (line 601)
- `TenantContextManager.with_tenant` (line 647)
- `TenantContextManager.get_rls_parameters` (line 663)
- `TenantService.create_tenant` (line 700)
- `TenantService.get_tenant_by_slug` (line 770)
- `TenantService.update_tenant` (line 788)
- `TenantService.suspend_tenant` (line 815)
- `TenantService.activate_tenant` (line 842)
- `TenantService.configure_sso` (line 966)
- `TenantService.update_subscription` (line 1000)
- `APIKeyService.create_key` (line 1045)
- `APIKeyService.validate_key` (line 1098)
- `APIKeyService.revoke_key` (line 1139)
- `APIKeyService.list_keys` (line 1168)
- `create_tenant_service` (line 1415)
- `create_api_key_service` (line 1431)
- `create_audit_service` (line 1436)

## casare_rpa.infrastructure.security.vault_client

**4 unused functions**


- `SecretMetadata.time_until_expiry` (line 148)
- `VaultConfig.validate_hashicorp_url` (line 292)
- `VaultClient.get_cache_stats` (line 1011)
- `VaultClient.get_audit_events` (line 1015)

## casare_rpa.infrastructure.security.workflow_schema

**2 unused functions**


- `WorkflowNodeSchema.validate_node_type` (line 33)
- `WorkflowSchema.validate_nodes_not_empty` (line 116)

## casare_rpa.infrastructure.tunnel.agent_tunnel

**3 unused functions**


- `AgentTunnel.state` (line 158)
- `AgentTunnel.report_job_progress` (line 420)
- `AgentTunnel.report_job_complete` (line 445)

## casare_rpa.infrastructure.tunnel.mtls

**3 unused functions**


- `CertificateManager.generate_ca` (line 155)
- `CertificateManager.generate_certificate` (line 253)
- `CertificateManager.check_expiration` (line 470)

## casare_rpa.infrastructure.updater.tuf_updater

**1 unused functions**


- `TUFUpdater.version_key` (line 643)

## casare_rpa.infrastructure.updater.update_manager

**8 unused functions**


- `UpdateManager.state` (line 133)
- `UpdateManager.update_info` (line 138)
- `UpdateManager.is_update_available` (line 143)
- `UpdateManager.is_ready_to_install` (line 150)
- `UpdateManager.is_version_skipped` (line 341)
- `UpdateManager.clear_skipped_versions` (line 352)
- `get_update_manager` (line 381)
- `reset_update_manager` (line 413)

## casare_rpa.nodes

**2 unused functions**


- `get_all_node_classes` (line 770)
- `preload_nodes` (line 783)

## casare_rpa.nodes.basic_nodes

**2 unused functions**


- `CommentNode.set_comment` (line 207)
- `CommentNode.get_comment` (line 216)

## casare_rpa.nodes.browser.browser_base

**1 unused functions**


- `BrowserBaseNode.get_page_async` (line 242)

## casare_rpa.nodes.browser.property_constants

**4 unused functions**


- `get_retry_properties` (line 182)
- `get_screenshot_properties` (line 187)
- `get_selector_properties` (line 192)
- `get_action_properties` (line 197)

## casare_rpa.nodes.browser_nodes

**1 unused functions**


- `CloseBrowserNode.close_browser` (line 480)

## casare_rpa.nodes.data_nodes

**3 unused functions**


- `ExtractTextNode.perform_extraction` (line 153)
- `GetAttributeNode.perform_get_attribute` (line 302)
- `ScreenshotNode.perform_screenshot` (line 496)

## casare_rpa.nodes.desktop_nodes.window_nodes

**6 unused functions**


- `ResizeWindowNode.do_resize` (line 147)
- `MoveWindowNode.do_move` (line 221)
- `MaximizeWindowNode.do_maximize` (line 282)
- `MinimizeWindowNode.do_minimize` (line 337)
- `RestoreWindowNode.do_restore` (line 392)
- `SetWindowStateNode.do_set_state` (line 530)

## casare_rpa.nodes.google.drive.drive_batch

**1 unused functions**


- `BatchRequestBuilder.content_type` (line 92)

## casare_rpa.nodes.google.google_base

**8 unused functions**


- `get_gmail_scopes` (line 517)
- `get_sheets_scopes` (line 522)
- `get_docs_scopes` (line 527)
- `get_drive_scopes` (line 532)
- `get_calendar_scopes` (line 539)
- `SheetsBaseNode.cell_to_indices` (line 733)
- `DriveBaseNode.get_mime_type_from_extension` (line 846)
- `DriveBaseNode.is_google_workspace_type` (line 856)

## casare_rpa.nodes.http.http_auth

**1 unused functions**


- `OAuth2CallbackServerNode.callback_handler` (line 696)

## casare_rpa.nodes.interaction_nodes

**3 unused functions**


- `ClickElementNode.perform_click` (line 216)
- `TypeTextNode.perform_type` (line 436)
- `SelectDropdownNode.perform_select` (line 617)

## casare_rpa.nodes.system.dialog_nodes

**4 unused functions**


- `MessageBoxNode.on_timeout` (line 283)
- `MessageBoxNode.on_finished` (line 296)
- `MessageBoxNode.auto_close_timer` (line 407)
- `InputDialogNode.on_finished` (line 514)

## casare_rpa.nodes.trigger_nodes.base_trigger_node

**5 unused functions**


- `BaseTriggerNode.populate_from_trigger_event` (line 131)
- `BaseTriggerNode.create_trigger_instance` (line 176)
- `BaseTriggerNode.is_listening` (line 204)
- `BaseTriggerNode.get_trigger_instance` (line 212)
- `trigger_node` (line 217)

## casare_rpa.presentation

**3 unused functions**


- `get_setup_wizard` (line 15)
- `get_config_manager` (line 22)
- `show_setup_if_needed` (line 29)

## casare_rpa.presentation.canvas.app

**6 unused functions**


- `CasareRPAApp.get_workflow_controller` (line 670)
- `CasareRPAApp.get_execution_controller` (line 674)
- `CasareRPAApp.get_selector_controller` (line 682)
- `CasareRPAApp.get_preferences_controller` (line 686)
- `CasareRPAApp.get_autosave_controller` (line 690)
- `CasareRPAApp.run_async` (line 710)

## casare_rpa.presentation.canvas.component_factory

**2 unused functions**


- `ComponentFactory.has` (line 90)
- `ComponentFactory.get_cached_count` (line 154)

## casare_rpa.presentation.canvas.components.fleet_dashboard_manager

**1 unused functions**


- `FleetDashboardManager.dialog` (line 42)

## casare_rpa.presentation.canvas.connections.auto_connect

**2 unused functions**


- `AutoConnectManager.reset_drag_state` (line 90)
- `AutoConnectManager.get_max_distance` (line 572)

## casare_rpa.presentation.canvas.connections.connection_validator

**2 unused functions**


- `ConnectionValidator.get_compatible_ports` (line 193)
- `ConnectionValidator.get_incompatible_ports` (line 242)

## casare_rpa.presentation.canvas.connections.node_insert

**1 unused functions**


- `NodeInsertManager.debug_find_pipes` (line 144)

## casare_rpa.presentation.canvas.controllers.autosave_controller

**2 unused functions**


- `AutosaveController.update_interval` (line 115)
- `AutosaveController.trigger_autosave_now` (line 138)

## casare_rpa.presentation.canvas.controllers.base_controller

**1 unused functions**


- `BaseController.is_initialized` (line 79)

## casare_rpa.presentation.canvas.controllers.connection_controller

**4 unused functions**


- `ConnectionController.create_connection` (line 55)
- `ConnectionController.delete_connection` (line 95)
- `ConnectionController.toggle_auto_connect` (line 142)
- `ConnectionController.auto_connect_enabled` (line 161)

## casare_rpa.presentation.canvas.controllers.event_bus_controller

**7 unused functions**


- `EventBusController.dispatch` (line 95)
- `EventBusController.enable_event_filtering` (line 134)
- `EventBusController.disable_event_filtering` (line 145)
- `EventBusController.get_event_history` (line 151)
- `EventBusController.clear_event_history` (line 165)
- `EventBusController.get_subscriber_count` (line 170)
- `EventBusController.get_event_types` (line 184)

## casare_rpa.presentation.canvas.controllers.example_workflow_controller

**4 unused functions**


- `ExampleWorkflowController.close_workflow` (line 207)
- `ExampleWorkflowController.current_file` (line 326)
- `ExampleWorkflowController.is_modified` (line 331)
- `ExampleWorkflowController.workflow_name` (line 336)

## casare_rpa.presentation.canvas.controllers.execution_controller

**11 unused functions**


- `ExecutionController.on_log_received` (line 185)
- `ExecutionController.log_callback` (line 210)
- `ExecutionController.on_stdout_received` (line 242)
- `ExecutionController.on_stderr_received` (line 248)
- `ExecutionController.stdout_callback` (line 262)
- `ExecutionController.stderr_callback` (line 267)
- `ExecutionController.cleanup_async` (line 344)
- `ExecutionController.enable_browser_actions` (line 615)
- `ExecutionController.is_paused` (line 1168)
- `ExecutionController.is_listening` (line 1173)
- `ExecutionController.toggle_trigger_listening` (line 1272)

## casare_rpa.presentation.canvas.controllers.menu_controller

**1 unused functions**


- `MenuController.update_action_state` (line 71)

## casare_rpa.presentation.canvas.controllers.node_controller

**1 unused functions**


- `NodeController.update_node_property` (line 277)

## casare_rpa.presentation.canvas.controllers.panel_controller

**4 unused functions**


- `PanelController.toggle_bottom_panel` (line 58)
- `PanelController.toggle_variable_inspector` (line 86)
- `PanelController.update_variables_panel` (line 159)
- `PanelController.show_validation_tab_if_errors` (line 192)

## casare_rpa.presentation.canvas.controllers.preferences_controller

**5 unused functions**


- `PreferencesController.save_preferences` (line 151)
- `PreferencesController.reset_preferences` (line 186)
- `PreferencesController.set_theme` (line 221)
- `PreferencesController.update_hotkey` (line 254)
- `PreferencesController.get_hotkeys` (line 290)

## casare_rpa.presentation.canvas.controllers.project_controller

**3 unused functions**


- `ProjectController.current_project` (line 77)
- `ProjectController.has_project` (line 82)
- `ProjectController.close_project` (line 371)

## casare_rpa.presentation.canvas.controllers.robot_controller

**15 unused functions**


- `RobotController.disconnect_from_orchestrator` (line 299)
- `RobotController.get_robots_by_capability` (line 665)
- `RobotController.selected_robot_id` (line 850)
- `RobotController.execution_mode` (line 855)
- `RobotController.robots` (line 860)
- `RobotController.is_cloud_mode` (line 865)
- `RobotController.is_local_mode` (line 870)
- `RobotController.has_robot_selected` (line 875)
- `RobotController.orchestrator_url` (line 885)
- `RobotController.start_robot` (line 941)
- `RobotController.pause_robot` (line 998)
- `RobotController.resume_robot` (line 1027)
- `RobotController.stop_all_robots` (line 1083)
- `RobotController.restart_all_robots` (line 1099)
- `RobotController.get_robot_logs` (line 1111)

## casare_rpa.presentation.canvas.controllers.scheduling_controller

**1 unused functions**


- `SchedulingController.get_schedule_count` (line 165)

## casare_rpa.presentation.canvas.controllers.selector_controller

**3 unused functions**


- `SelectorController.stop_picker` (line 115)
- `SelectorController.get_selector_integration` (line 176)
- `SelectorController.is_picker_active` (line 185)

## casare_rpa.presentation.canvas.controllers.ui_state_controller

**7 unused functions**


- `UIStateController.get_last_directory` (line 420)
- `UIStateController.remove_recent_file` (line 499)
- `UIStateController.get_auto_save_enabled` (line 529)
- `UIStateController.set_auto_save_enabled` (line 541)
- `UIStateController.get_auto_validate_enabled` (line 554)
- `UIStateController.set_auto_validate_enabled` (line 566)
- `UIStateController.is_initialized` (line 581)

## casare_rpa.presentation.canvas.controllers.viewport_controller

**5 unused functions**


- `ViewportController.get_current_zoom` (line 200)
- `ViewportController.is_minimap_visible` (line 209)
- `ViewportController.reset_viewport` (line 218)
- `ViewportController.fit_to_view` (line 231)
- `ViewportController.center_on_node` (line 241)

## casare_rpa.presentation.canvas.controllers.workflow_controller

**6 unused functions**


- `WorkflowController.close_workflow` (line 247)
- `WorkflowController.current_file` (line 302)
- `WorkflowController.is_modified` (line 307)
- `WorkflowController.on_import_file` (line 487)
- `WorkflowController.on_import_data` (line 531)
- `WorkflowController.check_validation_before_run` (line 580)

## casare_rpa.presentation.canvas.debugger.debug_controller

**16 unused functions**


- `Breakpoint.reset_hit_count` (line 143)
- `DebugController.enable_debug_mode` (line 268)
- `DebugController.is_debug_mode` (line 291)
- `DebugController.toggle_breakpoint_enabled` (line 364)
- `DebugController.get_all_breakpoints` (line 395)
- `DebugController.clear_all_breakpoints` (line 404)
- `DebugController.has_breakpoint` (line 419)
- `DebugController.get_call_stack` (line 608)
- `DebugController.add_watch` (line 617)
- `DebugController.remove_watch` (line 633)
- `DebugController.get_watches` (line 651)
- `DebugController.get_variable_value` (line 714)
- `DebugController.set_variable_value` (line 732)
- `DebugController.get_snapshots` (line 832)
- `DebugController.get_repl_history` (line 841)
- `DebugController.clear_repl` (line 850)

## casare_rpa.presentation.canvas.desktop.rich_comment_node

**2 unused functions**


- `create_markdown_comment` (line 155)
- `get_comment_shortcuts` (line 205)

## casare_rpa.presentation.canvas.events.domain_bridge

**2 unused functions**


- `DomainEventBridge.reset_instance` (line 230)
- `start_domain_bridge` (line 247)

## casare_rpa.presentation.canvas.events.event

**4 unused functions**


- `Event.category` (line 146)
- `Event.datetime` (line 156)
- `Event.has_data` (line 180)
- `Event.is_high_priority` (line 192)

## casare_rpa.presentation.canvas.events.event_batcher

**2 unused functions**


- `EventBatcher.batch` (line 87)
- `EventBatcher.has_pending` (line 166)

## casare_rpa.presentation.canvas.events.event_bus

**4 unused functions**


- `EventBus.reset_metrics` (line 517)
- `EventBus.enable_history` (line 530)
- `EventBus.clear_all_subscribers` (line 554)
- `EventBus.reset_instance` (line 568)

## casare_rpa.presentation.canvas.events.event_handler

**2 unused functions**


- `decorator` (line 88)
- `wrapper` (line 95)

## casare_rpa.presentation.canvas.events.event_types

**1 unused functions**


- `EventType.category` (line 523)

## casare_rpa.presentation.canvas.events.lazy_subscription

**5 unused functions**


- `LazySubscriptionGroup.active` (line 179)
- `LazySubscriptionGroup.activate_all` (line 183)
- `LazySubscriptionGroup.deactivate_all` (line 188)
- `_SharedVisibilitySubscription.wrapped_activate` (line 233)
- `_SharedVisibilitySubscription.wrapped_deactivate` (line 237)

## casare_rpa.presentation.canvas.execution.canvas_workflow_runner

**3 unused functions**


- `CanvasWorkflowRunner.is_paused` (line 575)
- `CanvasWorkflowRunner.is_listening` (line 580)
- `CanvasWorkflowRunner.trigger_run_count` (line 585)

## casare_rpa.presentation.canvas.graph.category_utils

**12 unused functions**


- `CategoryPath.depth` (line 43)
- `CategoryPath.root` (line 48)
- `CategoryPath.leaf` (line 53)
- `CategoryPath.parent_path` (line 65)
- `CategoryPath.is_descendant_of` (line 76)
- `CategoryNode.has_nodes` (line 112)
- `build_category_tree` (line 117)
- `update_category_counts` (line 145)
- `get_full_display_path` (line 307)
- `get_category_color_with_alpha` (line 397)
- `normalize_category` (line 421)
- `get_all_parent_paths` (line 443)

## casare_rpa.presentation.canvas.graph.collapse_components

**1 unused functions**


- `ExposedPortManager.indicators` (line 193)

## casare_rpa.presentation.canvas.graph.composite_node_creator

**2 unused functions**


- `CompositeNodeCreator.graph` (line 51)
- `CompositeNodeCreator.replace_composite` (line 77)

## casare_rpa.presentation.canvas.graph.custom_node_item

**7 unused functions**


- `AnimationCoordinator.animated_count` (line 90)
- `CasareNodeItem.clear_execution_state` (line 445)
- `CasareNodeItem.clear_robot_override` (line 460)
- `CasareNodeItem.get_robot_override_tooltip` (line 542)
- `CasareNodeItem.set_icon` (line 554)
- `CasareNodeItem.borderColor` (line 559)
- `CasareNodeItem.setBorderColor` (line 565)

## casare_rpa.presentation.canvas.graph.custom_pipe

**5 unused functions**


- `CasarePipe.set_label` (line 208)
- `CasarePipe.set_show_label` (line 213)
- `CasarePipe.is_insert_highlighted` (line 241)
- `set_show_connection_labels` (line 250)
- `get_show_connection_labels` (line 256)

## casare_rpa.presentation.canvas.graph.frame_factory

**2 unused functions**


- `FrameNode.get_frame_rect` (line 36)
- `add_frame_menu_actions` (line 132)

## casare_rpa.presentation.canvas.graph.frame_managers

**4 unused functions**


- `FrameDeletedCmd.undo` (line 56)
- `FrameDeletedCmd.redo` (line 69)
- `FrameBoundsManager.reset_instance` (line 104)
- `FrameBoundsManager.frame_count` (line 144)

## casare_rpa.presentation.canvas.graph.minimap

**3 unused functions**


- `MinimapView.drawForeground` (line 185)
- `Minimap.set_update_interval` (line 387)
- `Minimap.set_visible` (line 396)

## casare_rpa.presentation.canvas.graph.node_creation_helper

**5 unused functions**


- `NodeCreationHelper.graph` (line 61)
- `NodeCreationHelper.y_offset` (line 66)
- `NodeCreationHelper.y_offset` (line 71)
- `NodeCreationHelper.x_gap` (line 76)
- `NodeCreationHelper.x_gap` (line 81)

## casare_rpa.presentation.canvas.graph.node_frame

**2 unused functions**


- `NodeFrame.is_collapsed` (line 194)
- `NodeFrame.contextMenuEvent` (line 546)

## casare_rpa.presentation.canvas.graph.node_graph_widget

**13 unused functions**


- `NodeGraphWidget.graph` (line 484)
- `NodeGraphWidget.clear_graph` (line 493)
- `NodeGraphWidget.zoom_in` (line 505)
- `NodeGraphWidget.zoom_out` (line 510)
- `NodeGraphWidget.center_on_nodes` (line 515)
- `NodeGraphWidget.selection` (line 522)
- `NodeGraphWidget.auto_connect` (line 545)
- `NodeGraphWidget.node_insert` (line 555)
- `NodeGraphWidget.is_auto_connect_enabled` (line 573)
- `NodeGraphWidget.set_auto_connect_distance` (line 582)
- `NodeGraphWidget.quick_actions` (line 592)
- `NodeGraphWidget.tab_on_node_created` (line 669)
- `NodeGraphWidget.on_node_created` (line 1127)

## casare_rpa.presentation.canvas.graph.node_icons

**6 unused functions**


- `create_category_icon` (line 204)
- `get_node_color` (line 241)
- `register_custom_icon` (line 259)
- `get_all_node_icons` (line 271)
- `get_cached_node_icon` (line 352)
- `clear_icon_cache` (line 396)

## casare_rpa.presentation.canvas.graph.node_quick_actions

**1 unused functions**


- `setup_node_quick_actions` (line 293)

## casare_rpa.presentation.canvas.graph.node_registry

**16 unused functions**


- `get_visual_class_for_type` (line 212)
- `get_identifier_for_type` (line 230)
- `get_casare_class_for_type` (line 252)
- `get_all_node_types` (line 269)
- `is_valid_node_type` (line 279)
- `create_node_from_type` (line 292)
- `NodeRegistry.on_search_changed` (line 716)
- `NodeRegistry.on_menu_shown` (line 848)
- `NodeRegistry.get_node_class` (line 869)
- `NodeRegistry.get_all_nodes_in_category` (line 893)
- `NodeRegistry.get_subcategories` (line 918)
- `NodeRegistry.get_root_categories` (line 946)
- `NodeRegistry.get_all_nodes` (line 968)
- `NodeFactory.create_linked_node` (line 1050)
- `clear_node_type_caches` (line 1103)
- `get_cache_stats` (line 1115)

## casare_rpa.presentation.canvas.graph.node_widgets

**11 unused functions**


- `CasareComboBox.patched_show_popup` (line 59)
- `CasareComboBox.patched_hide_popup` (line 64)
- `CasareLivePipe.fixed_draw_index_pointer` (line 177)
- `CasarePipeItemFix.fixed_draw_path` (line 255)
- `CasareNodeDataDropFix.fixed_on_node_data_dropped` (line 297)
- `CasareNodeBaseFontFix.fixed_add_port` (line 363)
- `CasareViewerFontFix.safe_font` (line 411)
- `CasareNodeItemPaintFix.patched_paint` (line 449)
- `apply_all_node_widget_fixes` (line 508)
- `patched_combo_init` (line 549)
- `patched_checkbox_init` (line 558)

## casare_rpa.presentation.canvas.graph.port_shapes

**3 unused functions**


- `draw_port_shape` (line 312)
- `get_shape_for_type` (line 392)
- `get_shape_description` (line 410)

## casare_rpa.presentation.canvas.graph.selection_manager

**13 unused functions**


- `SelectionManager.graph` (line 50)
- `SelectionManager.get_selected_node_ids` (line 63)
- `SelectionManager.select_node` (line 82)
- `SelectionManager.add_to_selection` (line 105)
- `SelectionManager.remove_from_selection` (line 115)
- `SelectionManager.toggle_selection` (line 125)
- `SelectionManager.select_all` (line 135)
- `SelectionManager.is_selected` (line 140)
- `SelectionManager.get_selection_count` (line 152)
- `SelectionManager.has_selection` (line 161)
- `SelectionManager.get_selected_frames` (line 199)
- `SelectionManager.select_nodes_in_frame` (line 223)
- `SelectionManager.center_on_selection` (line 234)

## casare_rpa.presentation.canvas.graph.style_manager

**1 unused functions**


- `FrameStyleManager.get_frame_color` (line 63)

## casare_rpa.presentation.canvas.graph.viewport_culling

**5 unused functions**


- `SpatialHash.node_count` (line 132)
- `SpatialHash.cell_count` (line 137)
- `ViewportCullingManager.update_node_position` (line 253)
- `ViewportCullingManager.get_visible_nodes` (line 416)
- `create_viewport_culler_for_graph` (line 442)

## casare_rpa.presentation.canvas.initializers.ui_component_initializer

**1 unused functions**


- `UIComponentInitializer.is_normal_loaded` (line 59)

## casare_rpa.presentation.canvas.main_window

**36 unused functions**


- `MainWindow.bottom_panel` (line 309)
- `MainWindow.properties_panel` (line 316)
- `MainWindow.execution_timeline` (line 323)
- `MainWindow.validation_panel` (line 330)
- `MainWindow.hide_validation_panel` (line 351)
- `MainWindow.show_log_viewer` (line 356)
- `MainWindow.hide_log_viewer` (line 361)
- `MainWindow.show_execution_history` (line 370)
- `MainWindow.update_properties_panel` (line 377)
- `MainWindow.trigger_workflow_run` (line 407)
- `MainWindow.set_auto_validate` (line 506)
- `MainWindow.is_auto_validate_enabled` (line 511)
- `MainWindow.graph` (line 557)
- `MainWindow.workflow_runner` (line 565)
- `MainWindow.node_registry` (line 569)
- `MainWindow.command_palette` (line 573)
- `MainWindow.recent_files_menu` (line 577)
- `MainWindow.minimap` (line 581)
- `MainWindow.variable_inspector_dock` (line 585)
- `MainWindow.node_controller` (line 589)
- `MainWindow.viewport_controller` (line 593)
- `MainWindow.scheduling_controller` (line 597)
- `MainWindow.get_workflow_runner` (line 604)
- `MainWindow.get_viewport_controller` (line 625)
- `MainWindow.get_scheduling_controller` (line 628)
- `MainWindow.get_robot_controller` (line 634)
- `MainWindow.robot_picker_panel` (line 638)
- `MainWindow.get_robot_picker_panel` (line 641)
- `MainWindow.process_mining_panel` (line 645)
- `MainWindow.get_process_mining_panel` (line 648)
- `MainWindow.get_variable_inspector` (line 651)
- `MainWindow.get_execution_history_viewer` (line 654)
- `MainWindow.is_auto_connect_enabled` (line 657)
- `MainWindow.is_modified` (line 710)
- `MainWindow.reset_ui_state` (line 1105)
- `MainWindow.get_ui_state_controller` (line 1109)

## casare_rpa.presentation.canvas.port_type_system

**3 unused functions**


- `PortTypeRegistry.set_compatibility_rule` (line 363)
- `PortTypeRegistry.get_compatible_types` (line 374)
- `is_types_compatible` (line 401)

## casare_rpa.presentation.canvas.resources

**3 unused functions**


- `ResourceCache.preload_icons` (line 179)
- `get_cached_icon` (line 194)
- `get_cached_pixmap` (line 209)

## casare_rpa.presentation.canvas.search.command_palette

**2 unused functions**


- `CommandPalette.register_callback` (line 345)
- `CommandPalette.clear_commands` (line 373)

## casare_rpa.presentation.canvas.search.node_search_dialog

**1 unused functions**


- `NodeSearchDialog.set_node_items` (line 148)

## casare_rpa.presentation.canvas.search.searchable_menu

**3 unused functions**


- `SearchableNodeMenu.setup_search` (line 43)
- `SearchableNodeMenu.add_node_item` (line 72)
- `SearchableNodeMenu.build_menu` (line 86)

## casare_rpa.presentation.canvas.selectors.desktop_selector_builder

**2 unused functions**


- `DesktopSelectorBuilder.on_element_selected` (line 425)
- `DesktopSelectorBuilder.on_cancelled` (line 431)

## casare_rpa.presentation.canvas.selectors.element_picker

**1 unused functions**


- `ElementPickerOverlay.paintEvent` (line 202)

## casare_rpa.presentation.canvas.selectors.element_tree_widget

**2 unused functions**


- `ElementTreeWidget.get_selected_element` (line 358)
- `ElementTreeWidget.expand_to_element` (line 365)

## casare_rpa.presentation.canvas.selectors.selector_integration

**1 unused functions**


- `SelectorIntegration.is_picking` (line 198)

## casare_rpa.presentation.canvas.selectors.selector_validator

**9 unused functions**


- `ValidationResult.is_valid` (line 41)
- `ValidationResult.is_unique` (line 49)
- `ValidationResult.icon` (line 54)
- `ValidationResult.color` (line 64)
- `ValidationResult.message` (line 74)
- `SelectorValidator.validate_multiple` (line 191)
- `SelectorValidator.quick_check` (line 219)
- `SelectorValidator.get_element_at_position` (line 261)
- `validate_selector_sync` (line 282)

## casare_rpa.presentation.canvas.services.trigger_event_handler

**2 unused functions**


- `QtTriggerEventHandler.do_update` (line 95)
- `create_trigger_event_handler` (line 160)

## casare_rpa.presentation.canvas.services.websocket_bridge

**1 unused functions**


- `get_websocket_bridge` (line 315)

## casare_rpa.presentation.canvas.theme

**2 unused functions**


- `get_node_status_color` (line 648)
- `get_wire_color` (line 669)

## casare_rpa.presentation.canvas.ui.action_factory

**2 unused functions**


- `ActionFactory.create_all_actions` (line 59)
- `ActionFactory.load_hotkeys` (line 576)

## casare_rpa.presentation.canvas.ui.base_widget

**3 unused functions**


- `BaseWidget.set_state` (line 259)
- `BaseWidget.is_initialized` (line 291)
- `BaseDockWidget.get_title` (line 325)

## casare_rpa.presentation.canvas.ui.debug_panel

**2 unused functions**


- `DebugPanel.set_debug_controller` (line 147)
- `DebugPanel.clear_logs` (line 919)

## casare_rpa.presentation.canvas.ui.dialogs.fleet_dashboard

**7 unused functions**


- `FleetDashboardDialog.show_robots_tab` (line 376)
- `FleetDashboardDialog.show_jobs_tab` (line 380)
- `FleetDashboardDialog.show_schedules_tab` (line 384)
- `FleetDashboardDialog.show_analytics_tab` (line 388)
- `FleetDashboardDialog.show_api_keys_tab` (line 392)
- `FleetDashboardDialog.connect_websocket_bridge` (line 473)
- `FleetDashboardDialog.disconnect_websocket_bridge` (line 494)

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.analytics_tab

**4 unused functions**


- `BarChart.paintEvent` (line 111)
- `PieChart.paintEvent` (line 176)
- `AnalyticsTabWidget.update_fleet_status` (line 499)
- `AnalyticsTabWidget.update_active_jobs` (line 511)

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.base_tab

**3 unused functions**


- `BaseTabWidget.pause_auto_refresh` (line 147)
- `BaseTabWidget.resume_auto_refresh` (line 151)
- `BaseTabWidget.set_refresh_interval` (line 155)

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.jobs_tab

**2 unused functions**


- `JobsTabWidget.create_progress_bar_widget` (line 647)
- `JobsTabWidget.get_job_by_id` (line 725)

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.robots_tab

**1 unused functions**


- `RobotsTabWidget.get_robot_by_id` (line 743)

## casare_rpa.presentation.canvas.ui.dialogs.node_properties_dialog

**1 unused functions**


- `NodePropertiesDialog.get_properties` (line 320)

## casare_rpa.presentation.canvas.ui.dialogs.project_manager_dialog

**1 unused functions**


- `ProjectManagerDialog.update_recent_projects` (line 710)

## casare_rpa.presentation.canvas.ui.dialogs.remote_robot_dialog

**1 unused functions**


- `RemoteRobotDialog.append_log` (line 745)

## casare_rpa.presentation.canvas.ui.dialogs.update_dialog

**4 unused functions**


- `UpdateDialog.update_info` (line 456)
- `UpdateDialog.is_downloading` (line 461)
- `UpdateDialog.is_download_complete` (line 466)
- `UpdateNotificationWidget.set_update_info` (line 526)

## casare_rpa.presentation.canvas.ui.icons

**1 unused functions**


- `ToolbarIcons.get_all_icons` (line 137)

## casare_rpa.presentation.canvas.ui.panels.api_key_panel

**1 unused functions**


- `GenerateApiKeyDialog.set_generated_key` (line 198)

## casare_rpa.presentation.canvas.ui.panels.bottom_panel_dock

**9 unused functions**


- `BottomPanelDock.get_output_tab` (line 258)
- `BottomPanelDock.get_terminal_tab` (line 299)
- `BottomPanelDock.show_terminal_tab` (line 303)
- `BottomPanelDock.set_validation_result` (line 411)
- `BottomPanelDock.clear_validation` (line 421)
- `BottomPanelDock.has_validation_errors` (line 426)
- `BottomPanelDock.terminal_write` (line 474)
- `BottomPanelDock.prepare_for_execution` (line 498)
- `BottomPanelDock.execution_finished` (line 507)

## casare_rpa.presentation.canvas.ui.panels.history_tab

**1 unused functions**


- `HistoryTab.scroll_to_bottom` (line 414)

## casare_rpa.presentation.canvas.ui.panels.log_tab

**1 unused functions**


- `LogTab.set_max_entries` (line 375)

## casare_rpa.presentation.canvas.ui.panels.log_viewer_panel

**1 unused functions**


- `LogViewerPanel.clear_robots` (line 466)

## casare_rpa.presentation.canvas.ui.panels.minimap_panel

**2 unused functions**


- `MinimapView.drawForeground` (line 146)
- `MinimapPanel.set_graph_view` (line 218)

## casare_rpa.presentation.canvas.ui.panels.output_tab

**1 unused functions**


- `OutputTab.get_outputs` (line 363)

## casare_rpa.presentation.canvas.ui.panels.process_mining_panel

**1 unused functions**


- `ProcessMiningPanel.add_demo_data` (line 1186)

## casare_rpa.presentation.canvas.ui.panels.properties_panel

**1 unused functions**


- `PropertiesPanel.set_node_override` (line 575)

## casare_rpa.presentation.canvas.ui.panels.terminal_tab

**1 unused functions**


- `TerminalTab.get_line_count` (line 134)

## casare_rpa.presentation.canvas.ui.panels.variables_panel

**3 unused functions**


- `TypeComboDelegate.createEditor` (line 68)
- `TypeComboDelegate.setEditorData` (line 95)
- `TypeComboDelegate.setModelData` (line 108)

## casare_rpa.presentation.canvas.ui.signal_bridge

**5 unused functions**


- `ControllerSignalBridge.connect_all_controllers` (line 66)
- `BottomPanelSignalBridge.connect_bottom_panel` (line 315)
- `BottomPanelSignalBridge.connect_variable_inspector` (line 339)
- `BottomPanelSignalBridge.connect_properties_panel` (line 355)
- `BottomPanelSignalBridge.connect_execution_timeline` (line 374)

## casare_rpa.presentation.canvas.ui.toolbars.main_toolbar

**3 unused functions**


- `MainToolbar.set_execution_state` (line 249)
- `MainToolbar.set_undo_enabled` (line 261)
- `MainToolbar.set_redo_enabled` (line 270)

## casare_rpa.presentation.canvas.ui.widgets.ai_settings_widget

**8 unused functions**


- `AISettingsWidget.set_settings` (line 404)
- `AISettingsWidget.get_model` (line 431)
- `AISettingsWidget.set_model` (line 437)
- `AISettingsWidget.get_provider` (line 448)
- `AISettingsWidget.set_provider` (line 454)
- `AISettingsWidget.get_credential_id` (line 461)
- `AISettingsWidget.refresh_credentials` (line 468)
- `AISettingsWidget.apply_dark_style` (line 472)

## casare_rpa.presentation.canvas.ui.widgets.execution_timeline

**4 unused functions**


- `TimelineBar.paintEvent` (line 65)
- `TimelineBar.enterEvent` (line 108)
- `TimelineBar.leaveEvent` (line 120)
- `ExecutionTimeline.get_events` (line 305)

## casare_rpa.presentation.canvas.ui.widgets.output_console_widget

**3 unused functions**


- `OutputConsoleWidget.set_auto_scroll` (line 213)
- `OutputConsoleWidget.set_show_timestamps` (line 223)
- `OutputConsoleWidget.set_max_lines` (line 233)

## casare_rpa.presentation.canvas.ui.widgets.performance_dashboard

**2 unused functions**


- `PerformanceDashboardDialog.register_pool_callback` (line 741)
- `show_performance_dashboard` (line 752)

## casare_rpa.presentation.canvas.ui.widgets.robot_override_widget

**1 unused functions**


- `RobotOverrideWidget.is_override_enabled` (line 471)

## casare_rpa.presentation.canvas.ui.widgets.search_widget

**6 unused functions**


- `SearchWidget.set_items` (line 117)
- `SearchWidget.add_item` (line 127)
- `SearchWidget.clear_items` (line 139)
- `SearchWidget.set_fuzzy_match_function` (line 145)
- `SearchWidget.clear_search` (line 154)
- `SearchWidget.focus_search` (line 159)

## casare_rpa.presentation.canvas.ui.widgets.tenant_selector

**4 unused functions**


- `TenantSelectorWidget.set_show_all_option` (line 141)
- `TenantSelectorWidget.set_show_refresh` (line 151)
- `TenantSelectorWidget.get_current_tenant_name` (line 235)
- `TenantSelectorWidget.is_all_tenants_selected` (line 260)

## casare_rpa.presentation.canvas.ui.widgets.variable_editor_widget

**1 unused functions**


- `VariableEditorWidget.get_remove_button` (line 194)

## casare_rpa.presentation.canvas.visual_nodes.base_visual_node

**2 unused functions**


- `VisualNode.sync_types_from_casare_node` (line 287)
- `VisualNode.ensure_casare_node` (line 549)

## casare_rpa.presentation.canvas.visual_nodes.data_operations.nodes

**32 unused functions**


- `VisualConcatenateNode.get_node_class` (line 66)
- `VisualFormatStringNode.get_node_class` (line 83)
- `VisualRegexMatchNode.get_node_class` (line 103)
- `VisualRegexReplaceNode.get_node_class` (line 122)
- `VisualMathOperationNode.get_node_class` (line 144)
- `VisualComparisonNode.get_node_class` (line 166)
- `VisualCreateListNode.get_node_class` (line 184)
- `VisualListGetItemNode.get_node_class` (line 201)
- `VisualJsonParseNode.get_node_class` (line 217)
- `VisualGetPropertyNode.get_node_class` (line 234)
- `VisualListLengthNode.get_node_class` (line 257)
- `VisualListAppendNode.get_node_class` (line 276)
- `VisualListContainsNode.get_node_class` (line 296)
- `VisualListSliceNode.get_node_class` (line 322)
- `VisualListJoinNode.get_node_class` (line 344)
- `VisualListSortNode.get_node_class` (line 365)
- `VisualListReverseNode.get_node_class` (line 383)
- `VisualListUniqueNode.get_node_class` (line 402)
- `VisualListFilterNode.get_node_class` (line 427)
- `VisualListMapNode.get_node_class` (line 450)
- `VisualListReduceNode.get_node_class` (line 473)
- `VisualListFlattenNode.get_node_class` (line 495)
- `VisualDictGetNode.get_node_class` (line 526)
- `VisualDictSetNode.get_node_class` (line 550)
- `VisualDictRemoveNode.get_node_class` (line 574)
- `VisualDictMergeNode.get_node_class` (line 593)
- `VisualDictKeysNode.get_node_class` (line 611)
- `VisualDictValuesNode.get_node_class` (line 629)
- `VisualDictHasKeyNode.get_node_class` (line 652)
- `VisualCreateDictNode.get_node_class` (line 675)
- `VisualDictToJsonNode.get_node_class` (line 697)
- `VisualDictItemsNode.get_node_class` (line 715)

## casare_rpa.presentation.canvas.visual_nodes.email.nodes

**8 unused functions**


- `VisualSendEmailNode.get_node_class` (line 37)
- `VisualReadEmailsNode.get_node_class` (line 60)
- `VisualGetEmailContentNode.get_node_class` (line 117)
- `VisualSaveAttachmentNode.get_node_class` (line 146)
- `VisualFilterEmailsNode.get_node_class` (line 178)
- `VisualMarkEmailNode.get_node_class` (line 209)
- `VisualDeleteEmailNode.get_node_class` (line 245)
- `VisualMoveEmailNode.get_node_class` (line 275)

## casare_rpa.presentation.canvas.visual_nodes.error_handling.nodes

**1 unused functions**


- `VisualLogErrorNode.get_node_class` (line 145)

## casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes

**16 unused functions**


- `VisualReadFileNode.get_node_class` (line 44)
- `VisualWriteFileNode.get_node_class` (line 68)
- `VisualAppendFileNode.get_node_class` (line 92)
- `VisualDeleteFileNode.get_node_class` (line 116)
- `VisualCopyFileNode.get_node_class` (line 138)
- `VisualMoveFileNode.get_node_class` (line 162)
- `VisualFileExistsNode.get_node_class` (line 186)
- `VisualGetFileSizeNode.get_node_class` (line 210)
- `VisualGetFileInfoNode.get_node_class` (line 233)
- `VisualListFilesNode.get_node_class` (line 261)
- `VisualReadCsvNode.get_node_class` (line 290)
- `VisualWriteCsvNode.get_node_class` (line 315)
- `VisualReadJsonNode.get_node_class` (line 345)
- `VisualWriteJsonNode.get_node_class` (line 368)
- `VisualZipFilesNode.get_node_class` (line 396)
- `VisualUnzipFileNode.get_node_class` (line 421)

## casare_rpa.presentation.canvas.visual_nodes.messaging.nodes

**4 unused functions**


- `VisualTelegramSendMessageNode.get_node_class` (line 76)
- `VisualTelegramSendPhotoNode.get_node_class` (line 150)
- `VisualTelegramSendDocumentNode.get_node_class` (line 231)
- `VisualTelegramSendLocationNode.get_node_class` (line 300)

## casare_rpa.presentation.canvas.visual_nodes.messaging.telegram_action_nodes

**5 unused functions**


- `VisualTelegramEditMessageNode.get_node_class` (line 69)
- `VisualTelegramDeleteMessageNode.get_node_class` (line 127)
- `VisualTelegramSendMediaGroupNode.get_node_class` (line 185)
- `VisualTelegramAnswerCallbackNode.get_node_class` (line 250)
- `VisualTelegramGetUpdatesNode.get_node_class` (line 312)

## casare_rpa.presentation.canvas.visual_nodes.messaging.whatsapp_nodes

**7 unused functions**


- `VisualWhatsAppSendMessageNode.get_node_class` (line 66)
- `VisualWhatsAppSendTemplateNode.get_node_class` (line 144)
- `VisualWhatsAppSendImageNode.get_node_class` (line 217)
- `VisualWhatsAppSendDocumentNode.get_node_class` (line 296)
- `VisualWhatsAppSendVideoNode.get_node_class` (line 369)
- `VisualWhatsAppSendLocationNode.get_node_class` (line 455)
- `VisualWhatsAppSendInteractiveNode.get_node_class` (line 551)

## casare_rpa.presentation.canvas.visual_nodes.scripts.nodes

**5 unused functions**


- `VisualRunPythonScriptNode.get_node_class` (line 28)
- `VisualRunPythonFileNode.get_node_class` (line 52)
- `VisualEvalExpressionNode.get_node_class` (line 73)
- `VisualRunBatchScriptNode.get_node_class` (line 96)
- `VisualRunJavaScriptNode.get_node_class` (line 117)

## casare_rpa.presentation.canvas.visual_nodes.system.nodes

**13 unused functions**


- `VisualClipboardCopyNode.get_node_class` (line 36)
- `VisualClipboardPasteNode.get_node_class` (line 53)
- `VisualClipboardClearNode.get_node_class` (line 69)
- `VisualMessageBoxNode.get_node_class` (line 97)
- `VisualInputDialogNode.get_node_class` (line 122)
- `VisualTooltipNode.get_node_class` (line 147)
- `VisualRunCommandNode.get_node_class` (line 176)
- `VisualRunPowerShellNode.get_node_class` (line 204)
- `VisualGetServiceStatusNode.get_node_class` (line 229)
- `VisualStartServiceNode.get_node_class` (line 248)
- `VisualStopServiceNode.get_node_class` (line 266)
- `VisualRestartServiceNode.get_node_class` (line 291)
- `VisualListServicesNode.get_node_class` (line 316)

## casare_rpa.presentation.canvas.visual_nodes.triggers.base

**1 unused functions**


- `VisualTriggerNode.is_listening` (line 108)

## casare_rpa.presentation.setup.config_manager

**1 unused functions**


- `ClientConfigManager.validate_robot_name` (line 330)

## casare_rpa.presentation.setup.setup_wizard

**3 unused functions**


- `OrchestratorPage.isComplete` (line 490)
- `RobotConfigPage.isComplete` (line 567)
- `SummaryPage.initializePage` (line 721)

## casare_rpa.robot.agent

**6 unused functions**


- `RobotAgent.state` (line 495)
- `RobotAgent.is_paused` (line 505)
- `RobotAgent.current_job_count` (line 510)
- `RobotAgent.connected` (line 515)
- `RobotAgent.running` (line 520)
- `RobotAgent.cancel_job` (line 1300)

## casare_rpa.robot.audit

**15 unused functions**


- `AuditLogger.job_context` (line 214)
- `AuditLogger.node_context` (line 224)
- `AuditLogger.connection_lost` (line 327)
- `AuditLogger.connection_reconnecting` (line 335)
- `AuditLogger.job_received` (line 343)
- `AuditLogger.job_claimed` (line 352)
- `AuditLogger.node_started` (line 397)
- `AuditLogger.node_completed` (line 407)
- `AuditLogger.node_failed` (line 417)
- `AuditLogger.node_retried` (line 427)
- `AuditLogger.error_logged` (line 437)
- `AuditLogger.checkpoint_saved` (line 451)
- `AuditLogger.checkpoint_restored` (line 462)
- `AuditLogger.get_recent` (line 490)
- `get_audit_logger` (line 544)

## casare_rpa.robot.checkpoint

**3 unused functions**


- `CheckpointManager.is_node_executed` (line 289)
- `CheckpointManager.update_variable` (line 298)
- `create_checkpoint_state` (line 412)

## casare_rpa.robot.circuit_breaker

**14 unused functions**


- `CircuitBreaker.state` (line 108)
- `CircuitBreaker.is_closed` (line 113)
- `CircuitBreaker.is_open` (line 118)
- `CircuitBreaker.force_open` (line 270)
- `CircuitBreakerStats.total_calls` (line 304)
- `CircuitBreakerStats.successful_calls` (line 308)
- `CircuitBreakerStats.failed_calls` (line 312)
- `CircuitBreakerStats.blocked_calls` (line 316)
- `CircuitBreakerStats.times_opened` (line 320)
- `CircuitBreakerStats.increment_times_opened` (line 343)
- `CircuitBreakerRegistry.get_all_status` (line 386)
- `CircuitBreakerRegistry.reset_all` (line 390)
- `get_circuit_breaker` (line 400)
- `get_circuit_breaker_registry` (line 408)

## casare_rpa.robot.cli

**10 unused functions**


- `RobotCLIState.shutdown_event` (line 97)
- `RobotCLIState.shutdown_event` (line 102)
- `RobotCLIState.agent` (line 108)
- `RobotCLIState.agent` (line 113)
- `RobotCLIState.trigger_shutdown` (line 118)
- `signal_handler` (line 298)
- `win32_handler` (line 320)
- `status` (line 678)
- `logs` (line 822)
- `config` (line 938)

## casare_rpa.robot.distributed_agent

**6 unused functions**


- `RealtimeChannelManager.on_job_insert` (line 404)
- `DistributedRobotAgent.state` (line 683)
- `DistributedRobotAgent.current_job_count` (line 693)
- `DistributedRobotAgent.create_state_affinity` (line 1338)
- `DistributedRobotAgent.clear_state_affinity` (line 1369)
- `run_distributed_agent` (line 1415)

## casare_rpa.robot.metrics

**3 unused functions**


- `MetricsCollector.record_node` (line 221)
- `MetricsCollector.record_node_skipped` (line 271)
- `MetricsCollector.get_full_report` (line 430)

## casare_rpa.robot.service

**3 unused functions**


- `CasareRobotService.event_log_handler` (line 154)
- `CasareRobotService.SvcStop` (line 175)
- `CasareRobotService.SvcDoRun` (line 194)

## casare_rpa.robot.tray_icon

**1 unused functions**


- `RobotTrayApp.exit_app` (line 67)

## casare_rpa.triggers.base

**3 unused functions**


- `BaseTrigger.status` (line 390)
- `BaseTrigger.error_message` (line 400)
- `BaseTrigger.get_info` (line 404)

## casare_rpa.triggers.implementations.calendar_trigger

**1 unused functions**


- `CalendarTrigger.get_required_scopes` (line 85)

## casare_rpa.triggers.implementations.chat_trigger

**1 unused functions**


- `ChatTrigger.process_message` (line 69)

## casare_rpa.triggers.implementations.drive_trigger

**2 unused functions**


- `DriveTrigger.get_required_scopes` (line 76)
- `DriveTrigger.handle_push_notification` (line 388)

## casare_rpa.triggers.implementations.file_watch

**1 unused functions**


- `TriggerHandler.on_any_event` (line 93)

## casare_rpa.triggers.implementations.form_trigger

**1 unused functions**


- `FormTrigger.process_submission` (line 62)

## casare_rpa.triggers.implementations.gmail_trigger

**1 unused functions**


- `GmailTrigger.get_required_scopes` (line 64)

## casare_rpa.triggers.implementations.google_trigger_base

**2 unused functions**


- `GoogleAPIClient.credentials` (line 103)
- `GoogleTriggerBase.get_required_scopes` (line 340)

## casare_rpa.triggers.implementations.scheduled

**1 unused functions**


- `ScheduledTrigger.get_next_run` (line 281)

## casare_rpa.triggers.implementations.sheets_trigger

**1 unused functions**


- `SheetsTrigger.get_required_scopes` (line 77)

## casare_rpa.triggers.implementations.telegram_trigger

**1 unused functions**


- `TelegramTrigger.handle_webhook_update` (line 368)

## casare_rpa.triggers.implementations.whatsapp_trigger

**2 unused functions**


- `WhatsAppTrigger.verify_webhook` (line 370)
- `WhatsAppTrigger.handle_webhook_update` (line 439)

## casare_rpa.triggers.implementations.workflow_call

**1 unused functions**


- `WorkflowCallTrigger.invoke` (line 75)

## casare_rpa.triggers.manager

**10 unused functions**


- `TriggerManager.webhook_base_url` (line 125)
- `TriggerManager.get_webhook_url_by_path` (line 141)
- `TriggerManager.update_trigger` (line 493)
- `TriggerManager.enable_trigger` (line 513)
- `TriggerManager.disable_trigger` (line 530)
- `TriggerManager.call_workflow` (line 577)
- `TriggerManager.get_triggers_by_scenario` (line 615)
- `TriggerManager.get_triggers_by_type` (line 621)
- `TriggerManager.get_active_triggers` (line 625)
- `TriggerManager.http_port` (line 660)

## casare_rpa.triggers.registry

**4 unused functions**


- `TriggerRegistry.get_types` (line 132)
- `TriggerRegistry.is_registered` (line 142)
- `TriggerRegistry.get_config_schemas` (line 198)
- `reset_trigger_registry` (line 247)

## casare_rpa.triggers.webhook_auth

**1 unused functions**


- `WebhookAuthenticator.generate_signature` (line 241)

## casare_rpa.utils.config_loader

**4 unused functions**


- `ConfigLoader.add_source` (line 128)
- `ConfigLoader.clear_sources` (line 133)
- `ConfigLoader.load_all` (line 196)
- `load_config_with_env` (line 393)

## casare_rpa.utils.datetime_helpers

**2 unused functions**


- `format_datetime` (line 116)
- `to_iso_format` (line 134)

## casare_rpa.utils.fuzzy_search

**1 unused functions**


- `fuzzy_match` (line 338)

## casare_rpa.utils.hotkey_settings

**3 unused functions**


- `HotkeySettings.reset_to_defaults` (line 109)
- `HotkeySettings.get_all_hotkeys` (line 114)
- `reset_hotkey_settings` (line 135)

## casare_rpa.utils.id_generator

**3 unused functions**


- `is_valid_node_id` (line 70)
- `clear_session_ids` (line 104)
- `get_session_ids` (line 109)

## casare_rpa.utils.lazy_loader

**3 unused functions**


- `lazy_import` (line 232)
- `get_import_stats` (line 298)
- `reset_import_stats` (line 308)

## casare_rpa.utils.performance.parallel_executor

**5 unused functions**


- `DependencyGraph.get_independent_groups` (line 75)
- `DependencyGraph.get_parallel_batches` (line 134)
- `ParallelExecutor.execute_batches` (line 228)
- `analyze_workflow_dependencies` (line 259)
- `identify_parallel_branches` (line 287)

## casare_rpa.utils.performance.performance_metrics

**5 unused functions**


- `PerformanceMetrics.register_callback` (line 384)
- `PerformanceMetrics.unregister_callback` (line 391)
- `PerformanceMetrics.start_background_collection` (line 399)
- `PerformanceMetrics.stop_background_collection` (line 408)
- `time_operation` (line 549)

## casare_rpa.utils.pooling.browser_pool

**8 unused functions**


- `BrowserContextPool.available_count` (line 347)
- `BrowserContextPool.in_use_count` (line 352)
- `BrowserContextPool.total_count` (line 357)
- `BrowserPoolManager.acquire_context` (line 437)
- `BrowserPoolManager.release_context` (line 455)
- `BrowserPoolManager.is_initialized` (line 506)
- `get_browser_pool_manager` (line 515)
- `reset_browser_pool_manager` (line 523)

## casare_rpa.utils.pooling.database_pool

**7 unused functions**


- `PoolStatistics.avg_wait_time_ms` (line 68)
- `DatabaseConnectionPool.db_type` (line 195)
- `DatabaseConnectionPool.available_count` (line 200)
- `DatabaseConnectionPool.in_use_count` (line 205)
- `DatabaseConnectionPool.total_count` (line 210)
- `DatabasePoolManager.close_pool` (line 601)
- `DatabasePoolManager.reset_instance` (line 616)

## casare_rpa.utils.pooling.http_session_pool

**7 unused functions**


- `SessionStatistics.avg_request_time_ms` (line 39)
- `SessionStatistics.success_rate` (line 46)
- `HttpSessionPool.available_count` (line 161)
- `HttpSessionPool.in_use_count` (line 166)
- `HttpSessionPool.total_count` (line 171)
- `HttpSessionManager.reset_instance` (line 579)
- `get_session_manager` (line 596)

## casare_rpa.utils.recording.action_processor

**2 unused functions**


- `ActionProcessor.process` (line 67)
- `ActionProcessor.add_element_waits` (line 276)

## casare_rpa.utils.recording.browser_recorder

**4 unused functions**


- `BrowserRecorder.is_paused` (line 167)
- `BrowserRecorder.action_count` (line 177)
- `BrowserRecorder.add_wait_action` (line 514)
- `BrowserRecorder.add_screenshot_action` (line 533)

## casare_rpa.utils.recording.workflow_generator

**1 unused functions**


- `RecordingWorkflowGenerator.merge_workflows` (line 280)

## casare_rpa.utils.resilience.error_handler

**11 unused functions**


- `ErrorAnalytics.get_recent_errors` (line 176)
- `ErrorAnalytics.get_error_trend` (line 204)
- `GlobalErrorHandler.analytics` (line 283)
- `GlobalErrorHandler.set_default_strategy` (line 287)
- `GlobalErrorHandler.set_strategy_for_error` (line 297)
- `GlobalErrorHandler.set_fallback_workflow` (line 310)
- `GlobalErrorHandler.add_notification_handler` (line 324)
- `GlobalErrorHandler.remove_notification_handler` (line 338)
- `GlobalErrorHandler.get_fallback_workflow` (line 362)
- `get_global_error_handler` (line 476)
- `reset_global_error_handler` (line 484)

## casare_rpa.utils.resilience.rate_limiter

**10 unused functions**


- `RateLimitConfig.min_interval` (line 38)
- `RateLimiter.stats` (line 111)
- `RateLimiter.try_acquire` (line 178)
- `SlidingWindowRateLimiter.stats` (line 252)
- `SlidingWindowRateLimiter.try_acquire` (line 310)
- `rate_limited` (line 332)
- `decorator` (line 353)
- `wrapper` (line 355)
- `get_rate_limiter` (line 374)
- `clear_rate_limiters` (line 407)

## casare_rpa.utils.resilience.retry

**7 unused functions**


- `RetryResult.failed` (line 105)
- `with_retry` (line 254)
- `decorator` (line 265)
- `wrapper` (line 267)
- `retry_with_timeout` (line 309)
- `RetryStats.record_attempt` (line 377)
- `RetryStats.success_rate` (line 389)

## casare_rpa.utils.security.credential_manager

**3 unused functions**


- `CredentialManager.credential_exists` (line 455)
- `CredentialManager.store_telegram_credential` (line 481)
- `CredentialManager.store_whatsapp_credential` (line 513)

## casare_rpa.utils.security.secrets_manager

**2 unused functions**


- `SecretsManager.has` (line 183)
- `get_required_secret` (line 229)

## casare_rpa.utils.security.vault_client

**4 unused functions**


- `VaultClient.client` (line 179)
- `VaultClient.get_secret_metadata` (line 385)
- `VaultClient.renew_token` (line 413)
- `create_vault_client` (line 425)

## casare_rpa.utils.selectors.ai_selector_healer

**2 unused functions**


- `AISelectorHealer.find_best_match` (line 605)
- `AISelectorHealer.enhance_similarity_score` (line 695)

## casare_rpa.utils.selectors.selector_cache

**2 unused functions**


- `SelectorCache.enabled` (line 255)
- `reset_selector_cache` (line 276)

## casare_rpa.utils.selectors.selector_generator

**5 unused functions**


- `ElementFingerprint.get_primary_selector` (line 60)
- `ElementFingerprint.get_fallback_selectors` (line 66)
- `ElementFingerprint.promote_selector` (line 75)
- `ElementFingerprint.demote_selector` (line 81)
- `SmartSelectorGenerator.calculate_element_similarity` (line 260)

## casare_rpa.utils.selectors.selector_healing

**4 unused functions**


- `ElementFingerprint.fingerprint_hash` (line 73)
- `SelectorHealer.get_fingerprint` (line 207)
- `SelectorHealer.healing_history` (line 551)
- `get_selector_healer` (line 582)

## casare_rpa.utils.selectors.selector_manager

**3 unused functions**


- `SelectorManager.get_cache_stats` (line 489)
- `SelectorManager.enable_cache` (line 505)
- `SelectorManager.disable_cache` (line 509)

## casare_rpa.utils.selectors.selector_normalizer

**2 unused functions**


- `detect_selector_type` (line 99)
- `validate_selector_format` (line 138)

## casare_rpa.utils.settings_manager

**3 unused functions**


- `SettingsManager.set_autosave_enabled` (line 175)
- `SettingsManager.set_autosave_interval` (line 179)
- `reset_settings_manager` (line 202)

## casare_rpa.utils.type_converters

**3 unused functions**


- `safe_float` (line 30)
- `safe_str` (line 50)
- `safe_bool` (line 70)

## casare_rpa.utils.workflow.subgraph_calculator

**1 unused functions**


- `SubgraphCalculator.get_execution_order` (line 205)

## casare_rpa.utils.workflow.template_loader

**2 unused functions**


- `TemplateLoader.create_workflow_from_template` (line 458)
- `reset_template_loader` (line 500)

## casare_rpa.utils.workflow.workflow_migration

**1 unused functions**


- `remap_ids_for_import` (line 112)

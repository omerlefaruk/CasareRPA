# Execution Plan: Python Application

Root: `C:/Users/Rau/Desktop/CasareRPA/src/casare_rpa/application`

## Boundary violations (application imports outer layers)

Auto-detected imports from `infrastructure/` or `presentation/` outside the DI composition root.

### Resolved

- `src/casare_rpa/application/orchestrator/use_cases/assign_robot.py:24` → now depends on `casare_rpa.domain.orchestrator.repositories`
- `src/casare_rpa/application/orchestrator/use_cases/list_robots.py:13` → now depends on `casare_rpa.domain.orchestrator.repositories`
- `src/casare_rpa/application/orchestrator/use_cases/submit_job.py:32` → now depends on `casare_rpa.domain.orchestrator.repositories`
- `src/casare_rpa/application/services/cache_invalidator.py:7` → now depends on `casare_rpa.domain.interfaces`
- `src/casare_rpa/application/use_cases/environment_management.py:18` → now depends on `casare_rpa.domain.interfaces` + DI
- `src/casare_rpa/application/use_cases/folder_management.py:16` → now depends on `casare_rpa.domain.interfaces` + DI
- `src/casare_rpa/application/use_cases/template_management.py:32` → now depends on `casare_rpa.domain.interfaces` + DI
- `src/casare_rpa/application/services/browser_recording_service.py` → now depends on `casare_rpa.domain.interfaces` + DI
- `src/casare_rpa/application/services/orchestrator_client.py` → now depends on DI-provided HTTP adapter
- `src/casare_rpa/application/use_cases/error_recovery.py` → now depends on `casare_rpa.domain.interfaces` + DI
- `src/casare_rpa/application/use_cases/execute_workflow.py` → now depends on `casare_rpa.domain.interfaces` + DI-provided context factory
- `src/casare_rpa/application/use_cases/subflow_executor.py` → now depends on `casare_rpa.domain.interfaces`
- `src/casare_rpa/application/use_cases/node_executor.py` → now depends on `casare_rpa.domain.interfaces` + domain cache key generator
- `src/casare_rpa/application/use_cases/generate_workflow.py` → now depends on domain ports (`ILLMManager`, `INodeManifestProvider`) + DI

### Remaining

- None (enforced by `scripts/check_application_purity.py`)

## File inventory

- `src/casare_rpa/application/__init__.py`
- `src/casare_rpa/application/dependency_injection/__init__.py`
- `src/casare_rpa/application/dependency_injection/container.py`
- `src/casare_rpa/application/dependency_injection/providers.py`
- `src/casare_rpa/application/dependency_injection/singleton.py`
- `src/casare_rpa/application/execution/__init__.py`
- `src/casare_rpa/application/execution/interfaces.py`
- `src/casare_rpa/application/execution/trigger_runner.py`
- `src/casare_rpa/application/orchestrator/__init__.py`
- `src/casare_rpa/application/orchestrator/orchestrator_engine.py`
- `src/casare_rpa/application/orchestrator/services/__init__.py`
- `src/casare_rpa/application/orchestrator/services/dead_letter_queue.py`
- `src/casare_rpa/application/orchestrator/services/dispatcher_service.py`
- `src/casare_rpa/application/orchestrator/services/distribution_service.py`
- `src/casare_rpa/application/orchestrator/services/job_lifecycle_service.py`
- `src/casare_rpa/application/orchestrator/services/job_queue_manager.py`
- `src/casare_rpa/application/orchestrator/services/metrics_service.py`
- `src/casare_rpa/application/orchestrator/services/result_collector_service.py`
- `src/casare_rpa/application/orchestrator/services/robot_management_service.py`
- `src/casare_rpa/application/orchestrator/services/schedule_management_service.py`
- `src/casare_rpa/application/orchestrator/services/scheduling_coordinator.py`
- `src/casare_rpa/application/orchestrator/services/workflow_management_service.py`
- `src/casare_rpa/application/orchestrator/use_cases/__init__.py`
- `src/casare_rpa/application/orchestrator/use_cases/assign_robot.py`
- `src/casare_rpa/application/orchestrator/use_cases/execute_job.py`
- `src/casare_rpa/application/orchestrator/use_cases/execute_local.py`
- `src/casare_rpa/application/orchestrator/use_cases/list_robots.py`
- `src/casare_rpa/application/orchestrator/use_cases/submit_job.py`
- `src/casare_rpa/application/queries/__init__.py`
- `src/casare_rpa/application/queries/execution_queries.py`
- `src/casare_rpa/application/queries/workflow_queries.py`
- `src/casare_rpa/application/scheduling/__init__.py`
- `src/casare_rpa/application/services/__init__.py`
- `src/casare_rpa/application/services/browser_recording_service.py`
- `src/casare_rpa/application/services/cache_invalidator.py`
- `src/casare_rpa/application/services/execution_lifecycle_manager.py`
- `src/casare_rpa/application/services/orchestrator_client.py`
- `src/casare_rpa/application/services/port_type_service.py`
- `src/casare_rpa/application/services/queue_service.py`
- `src/casare_rpa/application/services/selector_service.py`
- `src/casare_rpa/application/use_cases/__init__.py`
- `src/casare_rpa/application/use_cases/environment_management.py`
- `src/casare_rpa/application/use_cases/error_recovery.py`
- `src/casare_rpa/application/use_cases/execute_workflow.py`
- `src/casare_rpa/application/use_cases/execution_engine.py`
- `src/casare_rpa/application/use_cases/execution_handlers.py`
- `src/casare_rpa/application/use_cases/execution_state_manager.py`
- `src/casare_rpa/application/use_cases/execution_strategies_parallel.py`
- `src/casare_rpa/application/use_cases/folder_management.py`
- `src/casare_rpa/application/use_cases/generate_workflow.py`
- `src/casare_rpa/application/use_cases/node_executor.py`
- `src/casare_rpa/application/use_cases/parallel_agent_executor.py`
- `src/casare_rpa/application/use_cases/project_management.py`
- `src/casare_rpa/application/use_cases/subflow_executor.py`
- `src/casare_rpa/application/use_cases/template_management.py`
- `src/casare_rpa/application/use_cases/validate_workflow.py`
- `src/casare_rpa/application/use_cases/variable_resolver.py`
- `src/casare_rpa/application/workflow/__init__.py`
- `src/casare_rpa/application/workflow/recent_files.py`
- `src/casare_rpa/application/workflow/workflow_import.py`

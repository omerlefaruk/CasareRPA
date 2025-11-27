# Week 2 Day 3: Repository Infrastructure Layer Implementation Plan

**Version**: 1.0.0
**Created**: November 27, 2025
**Target Duration**: 8 hours
**Assigned Agent**: rpa-engine-architect

---

## Executive Summary

This document provides a comprehensive implementation plan for creating the Repository Infrastructure Layer in CasareRPA. The goal is to establish a clean, testable persistence layer that implements the repository pattern for Workflow and Project entities.

### Objectives

1. Create repository interfaces (protocols) in the domain layer
2. Implement concrete JSON file-based repositories in the infrastructure layer
3. Extract and consolidate file I/O operations from existing code
4. Ensure backward compatibility with existing workflow/project files
5. Enable future extensibility (database storage, remote APIs)

### Current State Analysis

| Component | Current Location | Current State |
|-----------|-----------------|---------------|
| Workflow persistence | `WorkflowSchema.save_to_file/load_from_file` | Embedded in entity |
| Project persistence | `infrastructure/persistence/project_storage.py` | Static methods, no interface |
| Repository interfaces | `domain/repositories/__init__.py` | Empty placeholder |
| Domain ports | `domain/ports/__init__.py` | Empty |

### Target Architecture

```
Domain Layer (Abstractions)
    domain/repositories/
        workflow_repository.py     # Protocol/ABC for workflow persistence
        project_repository.py      # Protocol/ABC for project persistence
        scenario_repository.py     # Protocol/ABC for scenario persistence

Infrastructure Layer (Implementations)
    infrastructure/repositories/
        json_workflow_repository.py    # JSON file implementation
        json_project_repository.py     # JSON file implementation
        json_scenario_repository.py    # JSON file implementation
```

---

## Part 1: Detailed Task Breakdown

### Hour-by-Hour Schedule

| Hour | Task | Description | Dependencies |
|------|------|-------------|--------------|
| 1 | Repository Protocol Design | Define abstract interfaces in domain layer | Day 1 entities |
| 2 | WorkflowRepository Interface | Complete workflow protocol with all methods | Hour 1 |
| 3 | ProjectRepository Interface | Complete project protocol with all methods | Hour 1 |
| 4 | JSON Workflow Repository | Implement file-based workflow persistence | Hour 2 |
| 5 | JSON Project Repository | Migrate ProjectStorage to repository pattern | Hour 3 |
| 6 | JSON Scenario Repository | Create scenario persistence implementation | Hours 4-5 |
| 7 | Integration & Testing | Unit tests and integration with existing code | Hours 4-6 |
| 8 | Documentation & Validation | Docstrings, type hints, validation | Hour 7 |

### Critical Path

```
Hour 1: Protocols
    |
    +---> Hour 2: Workflow Protocol ---> Hour 4: JSON Workflow Repo --+
    |                                                                  |
    +---> Hour 3: Project Protocol  ---> Hour 5: JSON Project Repo  --+--> Hour 7: Testing
                                    |                                  |
                                    +--> Hour 6: JSON Scenario Repo --+
                                                                       |
                                                                       v
                                                                  Hour 8: Validation
```

---

## Part 2: File Structure and Locations

### Domain Layer: Repository Interfaces

```
src/casare_rpa/domain/repositories/
    __init__.py                 # Re-exports all repository interfaces
    base_repository.py          # Generic base protocol
    workflow_repository.py      # WorkflowRepository protocol
    project_repository.py       # ProjectRepository protocol
    scenario_repository.py      # ScenarioRepository protocol
```

### Infrastructure Layer: Repository Implementations

```
src/casare_rpa/infrastructure/repositories/
    __init__.py                 # Re-exports all implementations
    json_workflow_repository.py # JSON file-based workflow storage
    json_project_repository.py  # JSON file-based project storage
    json_scenario_repository.py # JSON file-based scenario storage
```

### Import Hierarchy

```python
# Clean import pattern for consumers
from casare_rpa.domain.repositories import (
    WorkflowRepository,
    ProjectRepository,
    ScenarioRepository,
)

from casare_rpa.infrastructure.repositories import (
    JSONWorkflowRepository,
    JSONProjectRepository,
    JSONScenarioRepository,
)

# Dependency injection in use cases
def __init__(self, workflow_repo: WorkflowRepository = None):
    self.workflow_repo = workflow_repo or JSONWorkflowRepository()
```

---

## Part 3: Code Patterns and Examples

### 3.1 Repository Protocol Base

**File**: `src/casare_rpa/domain/repositories/base_repository.py`

```python
"""
Base repository protocol defining common CRUD operations.
"""
from typing import Protocol, TypeVar, Generic, Optional, List
from pathlib import Path

T = TypeVar("T")
ID = TypeVar("ID")


class BaseRepository(Protocol[T, ID]):
    """
    Generic repository protocol for aggregate roots.

    Type Parameters:
        T: Entity type (e.g., Workflow, Project)
        ID: Identifier type (e.g., str, UUID)
    """

    async def get(self, id: ID) -> Optional[T]:
        """Retrieve entity by identifier."""
        ...

    async def save(self, entity: T) -> None:
        """Persist entity (create or update)."""
        ...

    async def delete(self, id: ID) -> bool:
        """Delete entity by identifier. Returns True if deleted."""
        ...

    async def exists(self, id: ID) -> bool:
        """Check if entity exists."""
        ...
```

### 3.2 Workflow Repository Protocol

**File**: `src/casare_rpa/domain/repositories/workflow_repository.py`

```python
"""
Repository protocol for Workflow aggregate.

Defines the contract for workflow persistence operations.
Implementations can be JSON files, databases, or remote APIs.
"""
from typing import Protocol, Optional, List, AsyncIterator
from pathlib import Path
from datetime import datetime

from ..entities.workflow import WorkflowSchema


class WorkflowRepository(Protocol):
    """
    Abstract repository for Workflow persistence.

    This protocol defines WHAT operations are available,
    not HOW they are implemented. Infrastructure layer
    provides concrete implementations.

    All methods are async to support non-blocking I/O.
    """

    # ===========================================================
    # Core CRUD Operations
    # ===========================================================

    async def save(self, workflow: WorkflowSchema, path: Path) -> None:
        """
        Save workflow to storage.

        Args:
            workflow: Workflow to persist
            path: Path/identifier for storage location

        Raises:
            RepositoryError: If save operation fails
            ValidationError: If workflow is invalid
        """
        ...

    async def load(self, path: Path) -> WorkflowSchema:
        """
        Load workflow from storage.

        Args:
            path: Path/identifier of workflow to load

        Returns:
            WorkflowSchema instance

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
            CorruptedWorkflowError: If workflow data is invalid
        """
        ...

    async def delete(self, path: Path) -> bool:
        """
        Delete workflow from storage.

        Args:
            path: Path/identifier of workflow to delete

        Returns:
            True if workflow was deleted, False if not found

        Raises:
            RepositoryError: If delete operation fails
        """
        ...

    async def exists(self, path: Path) -> bool:
        """
        Check if workflow exists at path.

        Args:
            path: Path/identifier to check

        Returns:
            True if workflow exists
        """
        ...

    # ===========================================================
    # Query Operations
    # ===========================================================

    async def list(self, directory: Path) -> List[Path]:
        """
        List all workflows in directory.

        Args:
            directory: Directory to search

        Returns:
            List of workflow paths
        """
        ...

    async def find_by_name(
        self,
        name: str,
        directory: Path
    ) -> Optional[Path]:
        """
        Find workflow by name in directory.

        Args:
            name: Workflow name to find
            directory: Directory to search

        Returns:
            Path to workflow if found, None otherwise
        """
        ...

    async def find_modified_since(
        self,
        since: datetime,
        directory: Path
    ) -> List[Path]:
        """
        Find workflows modified since timestamp.

        Args:
            since: Datetime threshold
            directory: Directory to search

        Returns:
            List of paths to modified workflows
        """
        ...

    # ===========================================================
    # Streaming Operations (for large datasets)
    # ===========================================================

    async def stream_all(
        self,
        directory: Path
    ) -> AsyncIterator[WorkflowSchema]:
        """
        Stream all workflows in directory.

        Memory-efficient iteration over large workflow collections.

        Args:
            directory: Directory to search

        Yields:
            WorkflowSchema instances
        """
        ...

    # ===========================================================
    # Backup Operations
    # ===========================================================

    async def backup(self, path: Path, backup_dir: Path) -> Path:
        """
        Create backup of workflow.

        Args:
            path: Source workflow path
            backup_dir: Directory for backup

        Returns:
            Path to backup file
        """
        ...

    async def restore(self, backup_path: Path, target_path: Path) -> None:
        """
        Restore workflow from backup.

        Args:
            backup_path: Path to backup file
            target_path: Path to restore to
        """
        ...
```

### 3.3 Project Repository Protocol

**File**: `src/casare_rpa/domain/repositories/project_repository.py`

```python
"""
Repository protocol for Project aggregate.
"""
from typing import Protocol, Optional, List
from pathlib import Path

from ..entities.project import (
    Project,
    Scenario,
    ProjectsIndex,
    VariablesFile,
    CredentialBindingsFile,
)


class ProjectRepository(Protocol):
    """
    Abstract repository for Project persistence.

    Handles project folder structure, metadata, variables, and credentials.
    """

    # ===========================================================
    # Project CRUD
    # ===========================================================

    async def save(self, project: Project) -> None:
        """
        Save project to storage.

        Creates project folder structure if needed.
        Updates modified timestamp.

        Args:
            project: Project to save (must have path set)

        Raises:
            ValueError: If project path is not set
            RepositoryError: If save fails
        """
        ...

    async def load(self, path: Path) -> Project:
        """
        Load project from folder.

        Args:
            path: Path to project folder

        Returns:
            Project instance with path set

        Raises:
            ProjectNotFoundError: If project.json doesn't exist
            CorruptedProjectError: If project data is invalid
        """
        ...

    async def delete(
        self,
        project: Project,
        remove_files: bool = False
    ) -> None:
        """
        Delete project from index and optionally files.

        Args:
            project: Project to delete
            remove_files: If True, delete project folder
        """
        ...

    async def exists(self, path: Path) -> bool:
        """Check if valid project exists at path."""
        ...

    async def is_project_folder(self, path: Path) -> bool:
        """Check if folder contains a CasareRPA project."""
        ...

    # ===========================================================
    # Project Variables
    # ===========================================================

    async def save_variables(
        self,
        project: Project,
        variables: VariablesFile
    ) -> None:
        """Save project variables."""
        ...

    async def load_variables(self, project: Project) -> VariablesFile:
        """Load project variables (empty if not found)."""
        ...

    # ===========================================================
    # Project Credentials
    # ===========================================================

    async def save_credentials(
        self,
        project: Project,
        credentials: CredentialBindingsFile
    ) -> None:
        """Save project credential bindings."""
        ...

    async def load_credentials(
        self,
        project: Project
    ) -> CredentialBindingsFile:
        """Load project credentials (empty if not found)."""
        ...

    # ===========================================================
    # Global Storage
    # ===========================================================

    async def save_global_variables(self, variables: VariablesFile) -> None:
        """Save global variables."""
        ...

    async def load_global_variables(self) -> VariablesFile:
        """Load global variables."""
        ...

    async def save_global_credentials(
        self,
        credentials: CredentialBindingsFile
    ) -> None:
        """Save global credentials."""
        ...

    async def load_global_credentials(self) -> CredentialBindingsFile:
        """Load global credentials."""
        ...

    # ===========================================================
    # Projects Index
    # ===========================================================

    async def save_index(self, index: ProjectsIndex) -> None:
        """Save projects index."""
        ...

    async def load_index(self) -> ProjectsIndex:
        """Load projects index."""
        ...

    async def list_scenarios(self, project: Project) -> List[Path]:
        """List scenario files in project."""
        ...
```

### 3.4 JSON Workflow Repository Implementation

**File**: `src/casare_rpa/infrastructure/repositories/json_workflow_repository.py`

```python
"""
JSON file-based implementation of WorkflowRepository.

Provides file system persistence for workflows using JSON format.
Uses orjson for high-performance serialization.
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, List, Optional
import shutil

import aiofiles
import aiofiles.os
import orjson
from loguru import logger

from ...domain.entities.workflow import WorkflowSchema
from ...domain.repositories.workflow_repository import WorkflowRepository
from .exceptions import (
    RepositoryError,
    WorkflowNotFoundError,
    CorruptedWorkflowError,
)


# File extension for workflow files
WORKFLOW_EXTENSION = ".json"

# Backup file suffix
BACKUP_SUFFIX = ".backup"


class JSONWorkflowRepository:
    """
    JSON file-based workflow repository.

    Features:
    - Async file I/O using aiofiles
    - Atomic writes (write to temp, then rename)
    - Automatic backup on save
    - JSON schema migration support
    - Corruption detection and recovery
    """

    def __init__(
        self,
        create_backups: bool = True,
        validate_on_load: bool = True,
        validate_on_save: bool = False,
    ) -> None:
        """
        Initialize repository.

        Args:
            create_backups: Create backup before overwriting
            validate_on_load: Validate workflow after loading
            validate_on_save: Validate workflow before saving
        """
        self.create_backups = create_backups
        self.validate_on_load = validate_on_load
        self.validate_on_save = validate_on_save

    # ===========================================================
    # Core CRUD Operations
    # ===========================================================

    async def save(self, workflow: WorkflowSchema, path: Path) -> None:
        """
        Save workflow to JSON file with atomic write.

        Steps:
        1. Optionally validate workflow
        2. Create backup of existing file (if enabled)
        3. Write to temporary file
        4. Atomically rename temp to target

        Args:
            workflow: Workflow to save
            path: Target file path

        Raises:
            RepositoryError: If save fails
            ValidationError: If validation fails
        """
        path = Path(path)

        try:
            # Optional validation
            if self.validate_on_save:
                is_valid, errors = workflow.validate()
                if not is_valid:
                    raise RepositoryError(
                        f"Workflow validation failed: {'; '.join(errors)}"
                    )

            # Update modified timestamp
            workflow.metadata.update_modified_timestamp()

            # Serialize to JSON
            json_data = orjson.dumps(
                workflow.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )

            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if file exists
            if self.create_backups and path.exists():
                await self._create_backup(path)

            # Atomic write: write to temp file, then rename
            temp_path = path.with_suffix(f"{path.suffix}.tmp")

            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(json_data)

            # Atomic rename (works on same filesystem)
            await aiofiles.os.replace(temp_path, path)

            logger.debug(f"Saved workflow to {path}")

        except Exception as e:
            logger.error(f"Failed to save workflow to {path}: {e}")
            raise RepositoryError(f"Failed to save workflow: {e}") from e

    async def load(self, path: Path) -> WorkflowSchema:
        """
        Load workflow from JSON file.

        Includes:
        - File existence check
        - JSON parsing with error handling
        - Optional validation
        - Legacy format migration

        Args:
            path: Path to workflow file

        Returns:
            WorkflowSchema instance

        Raises:
            WorkflowNotFoundError: If file doesn't exist
            CorruptedWorkflowError: If JSON is invalid
        """
        path = Path(path)

        if not path.exists():
            raise WorkflowNotFoundError(f"Workflow not found: {path}")

        try:
            async with aiofiles.open(path, "rb") as f:
                json_data = await f.read()

            # Parse JSON
            data = orjson.loads(json_data)

            # Migrate legacy formats if needed
            data = await self._migrate_if_needed(data, path)

            # Create workflow from dict
            workflow = WorkflowSchema.from_dict(data)

            # Optional validation
            if self.validate_on_load:
                is_valid, errors = workflow.validate()
                if not is_valid:
                    logger.warning(
                        f"Loaded workflow has validation issues: "
                        f"{'; '.join(errors)}"
                    )

            logger.debug(f"Loaded workflow from {path}")
            return workflow

        except orjson.JSONDecodeError as e:
            logger.error(f"Corrupted workflow file {path}: {e}")
            raise CorruptedWorkflowError(
                f"Invalid JSON in workflow file: {e}"
            ) from e

        except KeyError as e:
            logger.error(f"Missing required field in {path}: {e}")
            raise CorruptedWorkflowError(
                f"Missing required field: {e}"
            ) from e

        except Exception as e:
            logger.error(f"Failed to load workflow from {path}: {e}")
            raise RepositoryError(f"Failed to load workflow: {e}") from e

    async def delete(self, path: Path) -> bool:
        """
        Delete workflow file.

        Args:
            path: Path to workflow file

        Returns:
            True if deleted, False if not found
        """
        path = Path(path)

        if not path.exists():
            return False

        try:
            # Create backup before deletion
            if self.create_backups:
                await self._create_backup(path)

            await aiofiles.os.remove(path)
            logger.debug(f"Deleted workflow: {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete workflow {path}: {e}")
            raise RepositoryError(f"Failed to delete workflow: {e}") from e

    async def exists(self, path: Path) -> bool:
        """Check if workflow file exists."""
        return Path(path).exists()

    # ===========================================================
    # Query Operations
    # ===========================================================

    async def list(self, directory: Path) -> List[Path]:
        """
        List all workflow files in directory.

        Args:
            directory: Directory to search

        Returns:
            List of workflow file paths
        """
        directory = Path(directory)

        if not directory.exists():
            return []

        try:
            # Get all JSON files in directory
            workflows = sorted(directory.glob(f"*{WORKFLOW_EXTENSION}"))
            return [p for p in workflows if not p.name.startswith(".")]

        except Exception as e:
            logger.error(f"Failed to list workflows in {directory}: {e}")
            return []

    async def find_by_name(
        self,
        name: str,
        directory: Path
    ) -> Optional[Path]:
        """
        Find workflow by name.

        Searches workflow files for matching metadata.name.

        Args:
            name: Workflow name to find
            directory: Directory to search

        Returns:
            Path to workflow if found
        """
        for path in await self.list(directory):
            try:
                workflow = await self.load(path)
                if workflow.metadata.name == name:
                    return path
            except (RepositoryError, CorruptedWorkflowError):
                continue

        return None

    async def find_modified_since(
        self,
        since: datetime,
        directory: Path
    ) -> List[Path]:
        """
        Find workflows modified since timestamp.

        Uses file modification time for efficiency,
        falls back to metadata timestamp if available.
        """
        directory = Path(directory)
        results = []

        for path in await self.list(directory):
            try:
                # Check file modification time first (fast)
                stat = await aiofiles.os.stat(path)
                mtime = datetime.fromtimestamp(stat.st_mtime)

                if mtime >= since:
                    results.append(path)

            except Exception as e:
                logger.warning(f"Error checking {path}: {e}")
                continue

        return results

    # ===========================================================
    # Streaming Operations
    # ===========================================================

    async def stream_all(
        self,
        directory: Path
    ) -> AsyncIterator[WorkflowSchema]:
        """
        Stream all workflows in directory.

        Memory-efficient iteration - loads one workflow at a time.
        Skips corrupted files with warning.

        Yields:
            WorkflowSchema instances
        """
        for path in await self.list(directory):
            try:
                yield await self.load(path)
            except (RepositoryError, CorruptedWorkflowError) as e:
                logger.warning(f"Skipping corrupted workflow {path}: {e}")
                continue

    # ===========================================================
    # Backup Operations
    # ===========================================================

    async def backup(self, path: Path, backup_dir: Path) -> Path:
        """
        Create timestamped backup of workflow.

        Args:
            path: Source workflow path
            backup_dir: Directory for backup

        Returns:
            Path to backup file
        """
        path = Path(path)
        backup_dir = Path(backup_dir)

        if not path.exists():
            raise WorkflowNotFoundError(f"Workflow not found: {path}")

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_{timestamp}{WORKFLOW_EXTENSION}"
        backup_path = backup_dir / backup_name

        # Ensure backup directory exists
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy file
        async with aiofiles.open(path, "rb") as src:
            content = await src.read()

        async with aiofiles.open(backup_path, "wb") as dst:
            await dst.write(content)

        logger.info(f"Created backup: {backup_path}")
        return backup_path

    async def restore(self, backup_path: Path, target_path: Path) -> None:
        """
        Restore workflow from backup.

        Args:
            backup_path: Path to backup file
            target_path: Path to restore to
        """
        backup_path = Path(backup_path)
        target_path = Path(target_path)

        if not backup_path.exists():
            raise WorkflowNotFoundError(f"Backup not found: {backup_path}")

        # Load backup to validate it
        workflow = await self.load(backup_path)

        # Save to target location
        await self.save(workflow, target_path)

        logger.info(f"Restored workflow from {backup_path} to {target_path}")

    # ===========================================================
    # Private Helper Methods
    # ===========================================================

    async def _create_backup(self, path: Path) -> None:
        """Create backup of file before modification."""
        backup_path = path.with_suffix(f"{path.suffix}{BACKUP_SUFFIX}")

        try:
            async with aiofiles.open(path, "rb") as src:
                content = await src.read()

            async with aiofiles.open(backup_path, "wb") as dst:
                await dst.write(content)

        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    async def _migrate_if_needed(
        self,
        data: dict,
        path: Path
    ) -> dict:
        """
        Migrate legacy workflow formats if needed.

        Checks schema version and applies migrations.
        """
        # Import migration utilities
        from ...utils.workflow_migration import (
            needs_migration,
            migrate_workflow_ids,
        )

        if needs_migration(data):
            logger.info(f"Migrating legacy workflow format: {path}")
            data, _ = migrate_workflow_ids(data)

        return data
```

### 3.5 Repository Exceptions

**File**: `src/casare_rpa/infrastructure/repositories/exceptions.py`

```python
"""
Repository layer exceptions.

Custom exceptions for repository operations.
"""


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class WorkflowNotFoundError(RepositoryError):
    """Raised when workflow doesn't exist."""
    pass


class ProjectNotFoundError(RepositoryError):
    """Raised when project doesn't exist."""
    pass


class ScenarioNotFoundError(RepositoryError):
    """Raised when scenario doesn't exist."""
    pass


class CorruptedWorkflowError(RepositoryError):
    """Raised when workflow file is corrupted or invalid."""
    pass


class CorruptedProjectError(RepositoryError):
    """Raised when project file is corrupted or invalid."""
    pass


class ConcurrentModificationError(RepositoryError):
    """Raised when file was modified by another process."""
    pass


class BackupError(RepositoryError):
    """Raised when backup operation fails."""
    pass
```

---

## Part 4: Data Contracts

### 4.1 Workflow JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CasareRPA Workflow",
  "type": "object",
  "required": ["metadata", "nodes", "connections"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string", "default": "" },
        "author": { "type": "string", "default": "" },
        "version": { "type": "string", "default": "1.0.0" },
        "schema_version": { "type": "string", "default": "1.0" },
        "created_at": { "type": "string", "format": "date-time" },
        "modified_at": { "type": "string", "format": "date-time" },
        "tags": {
          "type": "array",
          "items": { "type": "string" },
          "default": []
        }
      }
    },
    "nodes": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["node_id", "node_type"],
        "properties": {
          "node_id": { "type": "string" },
          "node_type": { "type": "string" },
          "position": {
            "type": "array",
            "items": { "type": "number" },
            "minItems": 2,
            "maxItems": 2
          },
          "config": { "type": "object" }
        }
      }
    },
    "connections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["source_node", "source_port", "target_node", "target_port"],
        "properties": {
          "source_node": { "type": "string" },
          "source_port": { "type": "string" },
          "target_node": { "type": "string" },
          "target_port": { "type": "string" }
        }
      }
    },
    "frames": {
      "type": "array",
      "default": []
    },
    "variables": {
      "type": "object",
      "default": {}
    },
    "settings": {
      "type": "object",
      "properties": {
        "stop_on_error": { "type": "boolean", "default": true },
        "timeout": { "type": "integer", "default": 30 },
        "retry_count": { "type": "integer", "default": 0 }
      }
    }
  }
}
```

### 4.2 Project JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CasareRPA Project",
  "type": "object",
  "required": ["id", "name"],
  "properties": {
    "$schema_version": { "type": "string", "default": "1.0.0" },
    "id": {
      "type": "string",
      "pattern": "^proj_[a-f0-9]{8}$"
    },
    "name": { "type": "string" },
    "description": { "type": "string", "default": "" },
    "author": { "type": "string", "default": "" },
    "created_at": { "type": "string", "format": "date-time" },
    "modified_at": { "type": "string", "format": "date-time" },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "settings": {
      "type": "object",
      "properties": {
        "default_browser": { "type": "string", "default": "chromium" },
        "stop_on_error": { "type": "boolean", "default": true },
        "timeout_seconds": { "type": "integer", "default": 30 },
        "retry_count": { "type": "integer", "default": 0 }
      }
    }
  }
}
```

### 4.3 Error Handling Contract

```python
# Repository methods should raise specific exceptions:

# File not found:
raise WorkflowNotFoundError(f"Workflow not found: {path}")

# Invalid data:
raise CorruptedWorkflowError(f"Invalid JSON: {error}")

# I/O errors:
raise RepositoryError(f"Failed to save: {error}")

# Concurrent access:
raise ConcurrentModificationError(f"File modified externally: {path}")
```

---

## Part 5: Dependencies and Prerequisites

### 5.1 External Dependencies

| Dependency | Purpose | Installation |
|------------|---------|--------------|
| `aiofiles` | Async file I/O | `pip install aiofiles` |
| `orjson` | Fast JSON serialization | Already installed |
| `loguru` | Logging | Already installed |

### 5.2 Day 1 Entity Dependencies

The repository layer depends on these domain entities from Day 1:

```python
# From domain/entities/workflow.py
from ...domain.entities.workflow import WorkflowSchema

# From domain/entities/project.py
from ...domain.entities.project import (
    Project,
    Scenario,
    ProjectsIndex,
    VariablesFile,
    CredentialBindingsFile,
)
```

### 5.3 Day 2 Service Dependencies

The repositories integrate with Day 2 services:

```python
# Services can inject repositories for persistence
from ...domain.services.project_context import ProjectContext

class ProjectContext:
    def __init__(
        self,
        project_repo: ProjectRepository = None,
        workflow_repo: WorkflowRepository = None,
    ):
        self._project_repo = project_repo or JSONProjectRepository()
        self._workflow_repo = workflow_repo or JSONWorkflowRepository()
```

### 5.4 Configuration Integration

```python
# From utils/config.py
from ...utils.config import (
    PROJECTS_INDEX_FILE,
    GLOBAL_VARIABLES_FILE,
    GLOBAL_CREDENTIALS_FILE,
    CONFIG_DIR,
)
```

---

## Part 6: Success Criteria and Validation

### 6.1 Unit Test Requirements

**File**: `tests/infrastructure/repositories/test_json_workflow_repository.py`

```python
"""Unit tests for JSONWorkflowRepository."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from casare_rpa.infrastructure.repositories import JSONWorkflowRepository
from casare_rpa.infrastructure.repositories.exceptions import (
    WorkflowNotFoundError,
    CorruptedWorkflowError,
)


class TestJSONWorkflowRepository:
    """Test suite for JSON workflow repository."""

    @pytest.fixture
    def repo(self):
        """Create repository instance."""
        return JSONWorkflowRepository(
            create_backups=False,  # Disable for tests
            validate_on_load=False,
        )

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def valid_workflow(self):
        """Create valid workflow schema."""
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata

        return WorkflowSchema(WorkflowMetadata(name="Test Workflow"))

    # =========================================================
    # Save Tests
    # =========================================================

    @pytest.mark.asyncio
    async def test_save_creates_file(self, repo, temp_dir, valid_workflow):
        """Test that save creates workflow file."""
        path = temp_dir / "test.json"

        await repo.save(valid_workflow, path)

        assert path.exists()

    @pytest.mark.asyncio
    async def test_save_creates_parent_directories(
        self, repo, temp_dir, valid_workflow
    ):
        """Test that save creates parent directories."""
        path = temp_dir / "subdir" / "nested" / "test.json"

        await repo.save(valid_workflow, path)

        assert path.exists()

    @pytest.mark.asyncio
    async def test_save_updates_modified_timestamp(
        self, repo, temp_dir, valid_workflow
    ):
        """Test that save updates modified timestamp."""
        path = temp_dir / "test.json"
        original_time = valid_workflow.metadata.modified_at

        await repo.save(valid_workflow, path)

        assert valid_workflow.metadata.modified_at > original_time

    # =========================================================
    # Load Tests
    # =========================================================

    @pytest.mark.asyncio
    async def test_load_returns_workflow(self, repo, temp_dir, valid_workflow):
        """Test that load returns workflow."""
        path = temp_dir / "test.json"
        await repo.save(valid_workflow, path)

        loaded = await repo.load(path)

        assert loaded.metadata.name == valid_workflow.metadata.name

    @pytest.mark.asyncio
    async def test_load_nonexistent_raises_not_found(self, repo, temp_dir):
        """Test that loading nonexistent file raises error."""
        path = temp_dir / "nonexistent.json"

        with pytest.raises(WorkflowNotFoundError):
            await repo.load(path)

    @pytest.mark.asyncio
    async def test_load_invalid_json_raises_corrupted(self, repo, temp_dir):
        """Test that loading invalid JSON raises error."""
        path = temp_dir / "invalid.json"
        path.write_text("{ invalid json }")

        with pytest.raises(CorruptedWorkflowError):
            await repo.load(path)

    # =========================================================
    # Delete Tests
    # =========================================================

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, repo, temp_dir, valid_workflow):
        """Test that delete removes file."""
        path = temp_dir / "test.json"
        await repo.save(valid_workflow, path)

        result = await repo.delete(path)

        assert result is True
        assert not path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, repo, temp_dir):
        """Test that deleting nonexistent file returns False."""
        path = temp_dir / "nonexistent.json"

        result = await repo.delete(path)

        assert result is False

    # =========================================================
    # List Tests
    # =========================================================

    @pytest.mark.asyncio
    async def test_list_returns_workflow_paths(
        self, repo, temp_dir, valid_workflow
    ):
        """Test that list returns workflow file paths."""
        # Create multiple workflows
        await repo.save(valid_workflow, temp_dir / "wf1.json")
        await repo.save(valid_workflow, temp_dir / "wf2.json")

        paths = await repo.list(temp_dir)

        assert len(paths) == 2
        assert all(p.suffix == ".json" for p in paths)

    @pytest.mark.asyncio
    async def test_list_empty_directory_returns_empty(self, repo, temp_dir):
        """Test that listing empty directory returns empty list."""
        paths = await repo.list(temp_dir)

        assert paths == []

    # =========================================================
    # Atomic Write Tests
    # =========================================================

    @pytest.mark.asyncio
    async def test_save_is_atomic(self, repo, temp_dir, valid_workflow):
        """Test that save operation is atomic."""
        path = temp_dir / "test.json"

        # Save initial workflow
        await repo.save(valid_workflow, path)

        # Verify no temp files left behind
        temp_files = list(temp_dir.glob("*.tmp"))
        assert len(temp_files) == 0
```

### 6.2 Integration Test Scenarios

```python
"""Integration tests for repository layer."""

@pytest.mark.asyncio
async def test_workflow_round_trip():
    """Test save and load preserves workflow data."""
    repo = JSONWorkflowRepository()

    # Create workflow with nodes and connections
    workflow = create_complex_workflow()

    async with temp_workflow_file() as path:
        await repo.save(workflow, path)
        loaded = await repo.load(path)

    assert_workflows_equal(workflow, loaded)


@pytest.mark.asyncio
async def test_concurrent_saves():
    """Test concurrent saves to different files."""
    repo = JSONWorkflowRepository()
    workflows = [create_workflow() for _ in range(10)]

    async with temp_directory() as dir:
        tasks = [
            repo.save(wf, dir / f"wf{i}.json")
            for i, wf in enumerate(workflows)
        ]
        await asyncio.gather(*tasks)

        # Verify all saved correctly
        paths = await repo.list(dir)
        assert len(paths) == 10


@pytest.mark.asyncio
async def test_backup_on_overwrite():
    """Test backup creation when overwriting."""
    repo = JSONWorkflowRepository(create_backups=True)

    async with temp_workflow_file() as path:
        await repo.save(create_workflow(name="v1"), path)
        await repo.save(create_workflow(name="v2"), path)

        # Verify backup exists
        backup = path.with_suffix(".json.backup")
        assert backup.exists()
```

### 6.3 Performance Benchmarks

```python
"""Performance benchmarks for repository operations."""

@pytest.mark.benchmark
async def test_large_workflow_save_performance():
    """Benchmark saving large workflow (1000 nodes)."""
    repo = JSONWorkflowRepository()
    workflow = create_large_workflow(num_nodes=1000)

    async with temp_workflow_file() as path:
        start = time.perf_counter()
        await repo.save(workflow, path)
        elapsed = time.perf_counter() - start

    # Should complete in under 1 second
    assert elapsed < 1.0


@pytest.mark.benchmark
async def test_large_workflow_load_performance():
    """Benchmark loading large workflow."""
    repo = JSONWorkflowRepository()
    workflow = create_large_workflow(num_nodes=1000)

    async with temp_workflow_file() as path:
        await repo.save(workflow, path)

        start = time.perf_counter()
        await repo.load(path)
        elapsed = time.perf_counter() - start

    # Should complete in under 500ms
    assert elapsed < 0.5


@pytest.mark.benchmark
async def test_list_many_workflows_performance():
    """Benchmark listing 100 workflows."""
    repo = JSONWorkflowRepository()

    async with temp_directory() as dir:
        # Create 100 workflows
        for i in range(100):
            await repo.save(create_workflow(), dir / f"wf{i}.json")

        start = time.perf_counter()
        paths = await repo.list(dir)
        elapsed = time.perf_counter() - start

    assert len(paths) == 100
    assert elapsed < 0.1  # Should be very fast
```

---

## Part 7: Risk Assessment and Mitigation

### 7.1 File Corruption Handling

| Risk | Impact | Mitigation |
|------|--------|------------|
| JSON syntax error | Cannot load workflow | Graceful error with CorruptedWorkflowError |
| Missing required fields | Partial data | Schema validation with defaults |
| Encoding issues | Garbled text | Use UTF-8 explicitly, validate on load |
| Truncated file | Incomplete data | Check JSON structure completeness |

**Recovery Strategy**:
```python
async def load_with_recovery(self, path: Path) -> WorkflowSchema:
    """Attempt load with automatic backup recovery."""
    try:
        return await self.load(path)
    except CorruptedWorkflowError:
        backup = path.with_suffix(".json.backup")
        if backup.exists():
            logger.warning(f"Recovering from backup: {backup}")
            return await self.load(backup)
        raise
```

### 7.2 Concurrent Access

| Risk | Impact | Mitigation |
|------|--------|------------|
| Multiple writers | Data loss | File locking (future) |
| Read during write | Incomplete data | Atomic writes via temp file |
| External modification | Stale data | Check mtime before overwrite |

**File Lock Implementation (Future)**:
```python
import fcntl  # Unix
import msvcrt  # Windows

async def save_with_lock(self, workflow, path):
    """Save with exclusive file lock."""
    async with aiofiles.open(path, "wb") as f:
        # Acquire exclusive lock
        if sys.platform == "win32":
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)

        try:
            await f.write(json_data)
        finally:
            # Release lock
            if sys.platform == "win32":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

### 7.3 Backward Compatibility

| Risk | Impact | Mitigation |
|------|--------|------------|
| Old schema version | Load failure | Version detection and migration |
| Missing new fields | Incomplete data | Defaults for new fields |
| Removed fields | Extra data | Ignore unknown fields |
| ID format changes | Broken references | Auto-migration on load |

**Migration Registry**:
```python
MIGRATIONS = {
    "0.9": migrate_0_9_to_1_0,
    "1.0": migrate_1_0_to_1_1,
}

def migrate_workflow(data: dict) -> dict:
    """Apply migrations in sequence."""
    current_version = data.get("metadata", {}).get("schema_version", "0.9")

    for version, migrate_func in MIGRATIONS.items():
        if version > current_version:
            data = migrate_func(data)

    return data
```

### 7.4 Data Loss Prevention

| Strategy | Implementation |
|----------|----------------|
| Atomic writes | Write to temp, then rename |
| Automatic backups | Create .backup before overwrite |
| Versioned backups | Timestamped backup directory |
| Validation before save | Optional pre-save validation |

---

## Part 8: Implementation Guide for rpa-engine-architect

### Step-by-Step Coding Sequence

#### Phase 1: Repository Interfaces (Hours 1-3)

**Step 1.1**: Create base repository protocol
```
File: src/casare_rpa/domain/repositories/base_repository.py
Action: Create with generic CRUD protocol
Test: Type check with mypy
```

**Step 1.2**: Create WorkflowRepository protocol
```
File: src/casare_rpa/domain/repositories/workflow_repository.py
Action: Define all workflow persistence methods
Dependencies: domain/entities/workflow.py
Test: Verify Protocol can be implemented
```

**Step 1.3**: Create ProjectRepository protocol
```
File: src/casare_rpa/domain/repositories/project_repository.py
Action: Define all project persistence methods
Dependencies: domain/entities/project.py
Test: Verify Protocol can be implemented
```

**Step 1.4**: Create ScenarioRepository protocol
```
File: src/casare_rpa/domain/repositories/scenario_repository.py
Action: Define scenario persistence methods
Dependencies: domain/entities/project.py (Scenario class)
Test: Verify Protocol can be implemented
```

**Step 1.5**: Update domain repositories __init__.py
```
File: src/casare_rpa/domain/repositories/__init__.py
Action: Export all protocols
Test: Import test from external module
```

#### Phase 2: Infrastructure Implementations (Hours 4-6)

**Step 2.1**: Create repository exceptions
```
File: src/casare_rpa/infrastructure/repositories/exceptions.py
Action: Define all exception classes
Test: Verify exceptions can be raised and caught
```

**Step 2.2**: Create JSONWorkflowRepository
```
File: src/casare_rpa/infrastructure/repositories/json_workflow_repository.py
Action: Implement full WorkflowRepository protocol
Dependencies: aiofiles, orjson
Test: Unit tests for all CRUD operations
```

**Step 2.3**: Create JSONProjectRepository
```
File: src/casare_rpa/infrastructure/repositories/json_project_repository.py
Action: Migrate from ProjectStorage, implement protocol
Dependencies: aiofiles, orjson
Test: Unit tests, verify backward compat with existing projects
```

**Step 2.4**: Create JSONScenarioRepository
```
File: src/casare_rpa/infrastructure/repositories/json_scenario_repository.py
Action: Implement scenario persistence
Dependencies: aiofiles, orjson
Test: Unit tests for scenario CRUD
```

**Step 2.5**: Update infrastructure repositories __init__.py
```
File: src/casare_rpa/infrastructure/repositories/__init__.py
Action: Export all implementations
Test: Import test
```

#### Phase 3: Integration (Hours 7-8)

**Step 3.1**: Update WorkflowSchema to use repository
```
File: src/casare_rpa/domain/entities/workflow.py
Action: Deprecate save_to_file/load_from_file, add warnings
Test: Verify deprecation warnings emitted
```

**Step 3.2**: Update ProjectStorage for compatibility
```
File: src/casare_rpa/infrastructure/persistence/project_storage.py
Action: Add deprecation warnings, delegate to new repository
Test: Verify existing code still works
```

**Step 3.3**: Run full test suite
```
Command: pytest tests/ -v
Expected: All 1255+ tests pass
```

**Step 3.4**: Add repository integration tests
```
File: tests/infrastructure/repositories/test_integration.py
Action: End-to-end tests with real files
Test: Verify complete workflows
```

### Testing Strategy with Fixtures

```python
# tests/conftest.py additions

@pytest.fixture
def workflow_repo():
    """Create test workflow repository."""
    return JSONWorkflowRepository(
        create_backups=False,
        validate_on_load=False,
    )

@pytest.fixture
def project_repo():
    """Create test project repository."""
    return JSONProjectRepository(
        create_backups=False,
    )

@pytest.fixture
async def temp_workflow_dir():
    """Create temporary workflow directory."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

@pytest.fixture
def sample_workflow():
    """Create sample workflow for testing."""
    from casare_rpa.domain.entities.workflow import WorkflowSchema
    from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata

    workflow = WorkflowSchema(WorkflowMetadata(name="Test"))
    # Add start and end nodes
    workflow.add_node({
        "node_id": "start",
        "node_type": "StartNode",
        "position": [0, 0],
        "config": {},
    })
    workflow.add_node({
        "node_id": "end",
        "node_type": "EndNode",
        "position": [200, 0],
        "config": {},
    })
    return workflow
```

### Migration Path from Current File Handling

```
Current State:
  WorkflowSchema.save_to_file() -> Direct file write
  WorkflowSchema.load_from_file() -> Direct file read
  ProjectStorage (static methods) -> Direct file I/O

Target State:
  WorkflowSchema.save_to_file() -> [DEPRECATED] -> JSONWorkflowRepository.save()
  WorkflowSchema.load_from_file() -> [DEPRECATED] -> JSONWorkflowRepository.load()
  ProjectStorage -> [DEPRECATED] -> JSONProjectRepository

Migration Steps:
1. Add deprecation warnings to existing methods
2. Internally delegate to new repositories
3. Update use cases to accept repository via DI
4. Document new patterns in MIGRATION_GUIDE.md
5. Remove deprecated methods in v3.0
```

---

## Appendix A: File Checklist

### Domain Layer Files

- [ ] `src/casare_rpa/domain/repositories/__init__.py`
- [ ] `src/casare_rpa/domain/repositories/base_repository.py`
- [ ] `src/casare_rpa/domain/repositories/workflow_repository.py`
- [ ] `src/casare_rpa/domain/repositories/project_repository.py`
- [ ] `src/casare_rpa/domain/repositories/scenario_repository.py`

### Infrastructure Layer Files

- [ ] `src/casare_rpa/infrastructure/repositories/__init__.py`
- [ ] `src/casare_rpa/infrastructure/repositories/exceptions.py`
- [ ] `src/casare_rpa/infrastructure/repositories/json_workflow_repository.py`
- [ ] `src/casare_rpa/infrastructure/repositories/json_project_repository.py`
- [ ] `src/casare_rpa/infrastructure/repositories/json_scenario_repository.py`

### Test Files

- [ ] `tests/infrastructure/repositories/__init__.py`
- [ ] `tests/infrastructure/repositories/test_json_workflow_repository.py`
- [ ] `tests/infrastructure/repositories/test_json_project_repository.py`
- [ ] `tests/infrastructure/repositories/test_json_scenario_repository.py`
- [ ] `tests/infrastructure/repositories/test_integration.py`

---

## Appendix B: Dependencies to Add

```toml
# pyproject.toml additions (if not present)
[project.dependencies]
aiofiles = ">=23.0.0"
```

---

## Appendix C: Related Documentation

- `REFACTORING_ROADMAP.md` - Overall refactoring plan
- `ARCHITECTURE.md` - System architecture documentation
- `MIGRATION_GUIDE.md` - Migration guide for deprecated APIs

---

**Document End**

*This implementation plan should be followed sequentially by the rpa-engine-architect agent. Each step has clear success criteria and test requirements.*

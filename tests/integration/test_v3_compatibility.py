"""
v3.0 Compatibility Tests - Gates for v3.0 release.

These tests verify that deprecated compatibility layers have been removed
and all imports use the new domain-driven architecture.

Current State (v2.x):
- core/ compatibility layer exists -> these tests FAIL
- visual_nodes.py monolith deleted -> those tests PASS

Target State (v3.0):
- All tests PASS
- Zero deprecated imports
- All types imported from domain layer
"""

import ast
import importlib
import sys
import warnings
from pathlib import Path
from typing import List, Set, Tuple

import pytest


def get_all_python_files(root: Path = Path("src/casare_rpa")) -> List[Path]:
    """Get all Python files in source tree, excluding __pycache__."""
    return [p for p in root.rglob("*.py") if "__pycache__" not in str(p)]


def parse_file_safely(pyfile: Path) -> ast.Module | None:
    """Parse Python file, return None on syntax error."""
    try:
        with open(pyfile, "r", encoding="utf-8") as f:
            return ast.parse(f.read(), filename=str(pyfile))
    except SyntaxError:
        return None


def find_imports_from_module(
    tree: ast.Module, module_prefix: str
) -> List[Tuple[int, str]]:
    """Find all imports from a given module prefix."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(module_prefix):
                    imports.append((node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(module_prefix):
                names = ", ".join(a.name for a in node.names)
                imports.append((node.lineno, f"from {node.module} import {names}"))
    return imports


class TestCoreCompatibilityLayerRemoval:
    """Tests for removal of core/ compatibility layer (v3.0 requirement)."""

    def test_no_core_imports(self):
        """
        Verify zero imports from casare_rpa.core in source code.

        The core/ module is a compatibility layer that should be removed in v3.0.
        All code should import from casare_rpa.domain instead.
        """
        deprecated_imports = []

        for pyfile in get_all_python_files():
            # Skip core/ itself - it's allowed to have internal imports
            if "casare_rpa/core" in str(pyfile).replace("\\", "/"):
                continue

            tree = parse_file_safely(pyfile)
            if tree is None:
                continue

            imports = find_imports_from_module(tree, "casare_rpa.core")
            for lineno, import_str in imports:
                deprecated_imports.append(f"{pyfile}:{lineno} - {import_str}")

        # Format error message with first 20 violations
        msg = f"Found {len(deprecated_imports)} deprecated core imports:\n"
        msg += "\n".join(deprecated_imports[:20])
        if len(deprecated_imports) > 20:
            msg += f"\n... and {len(deprecated_imports) - 20} more"

        assert not deprecated_imports, msg

    def test_core_compatibility_layer_deleted(self):
        """
        Verify core/ compatibility layer directory has been deleted.

        The core/ directory contains deprecated types that have been
        moved to domain/value_objects and domain/entities.
        """
        core_path = Path("src/casare_rpa/core")
        if core_path.exists():
            files = list(core_path.glob("*.py"))
            file_list = ", ".join(f.name for f in files[:10])
            pytest.fail(
                f"core/ compatibility layer still exists at {core_path}\n"
                f"Contains: {file_list}"
                f"{' ...' if len(files) > 10 else ''}"
            )

    def test_no_core_types_import(self):
        """
        Verify no imports from casare_rpa.core.types.

        Types should be imported from casare_rpa.domain.value_objects.types.
        """
        deprecated_imports = []

        for pyfile in get_all_python_files():
            if "casare_rpa/core" in str(pyfile).replace("\\", "/"):
                continue

            tree = parse_file_safely(pyfile)
            if tree is None:
                continue

            imports = find_imports_from_module(tree, "casare_rpa.core.types")
            for lineno, import_str in imports:
                deprecated_imports.append(f"{pyfile}:{lineno} - {import_str}")

        assert not deprecated_imports, (
            f"Found {len(deprecated_imports)} imports from core.types "
            f"(should use domain.value_objects.types):\n"
            + "\n".join(deprecated_imports[:10])
        )

    def test_no_core_base_node_import(self):
        """
        Verify no imports from casare_rpa.core.base_node.

        BaseNode should be imported from casare_rpa.domain.entities.base_node.
        """
        deprecated_imports = []

        for pyfile in get_all_python_files():
            if "casare_rpa/core" in str(pyfile).replace("\\", "/"):
                continue

            tree = parse_file_safely(pyfile)
            if tree is None:
                continue

            imports = find_imports_from_module(tree, "casare_rpa.core.base_node")
            for lineno, import_str in imports:
                deprecated_imports.append(f"{pyfile}:{lineno} - {import_str}")

        assert not deprecated_imports, (
            f"Found {len(deprecated_imports)} imports from core.base_node "
            f"(should use domain.entities.base_node):\n"
            + "\n".join(deprecated_imports[:10])
        )


class TestVisualNodesMonolithRemoval:
    """Tests for removal of visual_nodes.py monolith (already done)."""

    def test_visual_nodes_monolith_deleted(self):
        """
        Verify visual_nodes.py monolith file has been deleted.

        The monolith has been split into category-specific modules
        in presentation/canvas/visual_nodes/.
        """
        monolith_path = Path(
            "src/casare_rpa/presentation/canvas/visual_nodes/visual_nodes.py"
        )
        assert (
            not monolith_path.exists()
        ), f"visual_nodes.py monolith still exists at {monolith_path}"

    def test_no_visual_nodes_monolith_imports(self):
        """
        Verify visual_nodes.py monolith is not imported anywhere.

        All imports should use category-specific modules.
        """
        monolith_imports = []

        for pyfile in get_all_python_files():
            tree = parse_file_safely(pyfile)
            if tree is None:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if (
                        node.module
                        == "casare_rpa.presentation.canvas.visual_nodes.visual_nodes"
                    ):
                        names = ", ".join(a.name for a in node.names)
                        monolith_imports.append(
                            f"{pyfile}:{node.lineno} - from {node.module} import {names}"
                        )

        assert not monolith_imports, (
            f"Found {len(monolith_imports)} monolith imports:\n"
            + "\n".join(monolith_imports)
        )


class TestDeprecationWarnings:
    """Tests for deprecation warning cleanup."""

    def test_no_deprecation_warnings_on_import(self):
        """
        Verify importing core modules produces zero DeprecationWarnings.

        All deprecation warnings should be resolved before v3.0.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            # Import domain layer modules
            from casare_rpa.domain.value_objects import types, port
            from casare_rpa.domain.entities import workflow

            # Import node modules
            from casare_rpa.nodes import file, http, database

            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]

        assert not deprecation_warnings, (
            f"Found {len(deprecation_warnings)} DeprecationWarnings:\n"
            + "\n".join(str(w.message) for w in deprecation_warnings[:5])
        )


class TestNewImportsResolve:
    """Tests to verify new import paths work correctly."""

    def test_domain_types_import(self):
        """Verify domain value object types can be imported."""
        from casare_rpa.domain.value_objects.types import (
            NodeStatus,
            DataType,
            ExecutionMode,
            PortType,
            ErrorCode,
        )

        assert NodeStatus is not None
        assert DataType is not None
        assert ExecutionMode is not None
        assert PortType is not None
        assert ErrorCode is not None

    def test_domain_port_import(self):
        """Verify Port value object can be imported."""
        from casare_rpa.domain.value_objects.port import Port

        assert Port is not None
        # Verify it's actually the class we expect
        assert hasattr(Port, "name")
        assert hasattr(Port, "port_type")
        assert hasattr(Port, "data_type")

    def test_domain_entities_import(self):
        """Verify domain entities can be imported."""
        from casare_rpa.domain.entities import (
            WorkflowMetadata,
            NodeConnection,
            WorkflowSchema,
            ExecutionState,
        )

        assert WorkflowMetadata is not None
        assert NodeConnection is not None
        assert WorkflowSchema is not None
        assert ExecutionState is not None

    def test_file_nodes_import(self):
        """Verify file nodes can be imported from new location."""
        from casare_rpa.nodes.file import ReadFileNode, ReadCSVNode, WriteFileNode

        assert ReadFileNode is not None
        assert ReadCSVNode is not None
        assert WriteFileNode is not None

    def test_http_nodes_import(self):
        """Verify HTTP nodes can be imported from new location."""
        from casare_rpa.nodes.http import HttpRequestNode, SetHttpHeadersNode

        assert HttpRequestNode is not None
        assert SetHttpHeadersNode is not None

    def test_database_nodes_import(self):
        """Verify database nodes can be imported from new location."""
        from casare_rpa.nodes.database import DatabaseConnectNode, ExecuteQueryNode

        assert DatabaseConnectNode is not None
        assert ExecuteQueryNode is not None


class TestNodeModuleStructure:
    """Tests to verify node module organization follows v3.0 patterns."""

    def test_file_module_has_all_exports(self):
        """Verify file module exports all expected nodes."""
        from casare_rpa.nodes import file as file_module

        expected_nodes = [
            "ReadFileNode",
            "WriteFileNode",
            "AppendFileNode",
            "DeleteFileNode",
            "CopyFileNode",
            "MoveFileNode",
            "ReadCSVNode",
            "WriteCSVNode",
            "ReadJSONFileNode",
            "WriteJSONFileNode",
        ]

        missing = [name for name in expected_nodes if not hasattr(file_module, name)]
        assert not missing, f"Missing exports from file module: {missing}"

    def test_http_module_has_all_exports(self):
        """Verify HTTP module exports all expected nodes."""
        from casare_rpa.nodes import http as http_module

        # HttpRequestNode supports all HTTP methods via dropdown
        expected_nodes = [
            "HttpRequestNode",
            "SetHttpHeadersNode",
            "HttpAuthNode",
            "ParseJsonResponseNode",
            "HttpDownloadFileNode",
            "HttpUploadFileNode",
            "BuildUrlNode",
        ]

        missing = [name for name in expected_nodes if not hasattr(http_module, name)]
        assert not missing, f"Missing exports from http module: {missing}"

    def test_database_module_has_all_exports(self):
        """Verify database module exports all expected nodes."""
        from casare_rpa.nodes import database as database_module

        expected_nodes = [
            "DatabaseConnectNode",
            "ExecuteQueryNode",
            "ExecuteNonQueryNode",
            "BeginTransactionNode",
            "CommitTransactionNode",
            "RollbackTransactionNode",
        ]

        missing = [
            name for name in expected_nodes if not hasattr(database_module, name)
        ]
        assert not missing, f"Missing exports from database module: {missing}"


@pytest.mark.slow
class TestFullTestSuitePasses:
    """Integration test to verify entire suite passes after migration."""

    def test_full_suite_runs_without_errors(self):
        """
        Run abbreviated test suite to verify no import errors.

        Note: Full suite run delegated to CI/CD pipeline.
        """
        # Just verify core modules can be imported without error
        import casare_rpa.domain
        import casare_rpa.nodes
        import casare_rpa.presentation

        assert True  # If we get here, imports succeeded

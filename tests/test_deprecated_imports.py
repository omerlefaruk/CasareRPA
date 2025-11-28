"""
Tests for backward compatibility of deprecated node module imports.

These tests verify that:
1. Old import paths still work
2. DeprecationWarning is raised when using old paths
3. Old and new imports resolve to identical classes
"""

import warnings
import pytest


class TestFileNodesDeprecatedImport:
    """Tests for deprecated file_nodes.py imports."""

    def test_file_nodes_deprecated_import(self):
        """Verify old file_nodes import works but warns."""
        with pytest.warns(DeprecationWarning, match="file_nodes is deprecated"):
            from casare_rpa.nodes.file_nodes import ReadFileNode

    def test_old_and_new_file_imports_identical(self):
        """Verify old and new file imports resolve to same class."""
        # Suppress the deprecation warning for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from casare_rpa.nodes.file_nodes import ReadFileNode as OldRead

        from casare_rpa.nodes.file import ReadFileNode as NewRead

        assert OldRead is NewRead, "Old and new imports must be identical"


class TestHttpNodesDeprecatedImport:
    """Tests for deprecated http_nodes.py imports."""

    def test_http_nodes_deprecated_import(self):
        """Verify old http_nodes import works but warns."""
        with pytest.warns(DeprecationWarning, match="http_nodes is deprecated"):
            from casare_rpa.nodes.http_nodes import HttpGetNode

    def test_old_and_new_http_imports_identical(self):
        """Verify old and new HTTP imports resolve to same class."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from casare_rpa.nodes.http_nodes import HttpGetNode as OldGet

        from casare_rpa.nodes.http import HttpGetNode as NewGet

        assert OldGet is NewGet, "Old and new imports must be identical"


class TestDatabaseNodesDeprecatedImport:
    """Tests for deprecated database_nodes.py imports."""

    def test_database_nodes_deprecated_import(self):
        """Verify old database_nodes import works but warns."""
        with pytest.warns(DeprecationWarning, match="database_nodes is deprecated"):
            from casare_rpa.nodes.database_nodes import DatabaseConnectNode

    def test_old_and_new_database_imports_identical(self):
        """Verify old and new database imports resolve to same class."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from casare_rpa.nodes.database_nodes import (
                DatabaseConnectNode as OldConnect,
            )

        from casare_rpa.nodes.database import DatabaseConnectNode as NewConnect

        assert OldConnect is NewConnect, "Old and new imports must be identical"


class TestAllExportsConsistent:
    """Verify all exports from deprecated modules match new modules."""

    def test_file_nodes_all_exports(self):
        """Verify all file_nodes exports are available from both paths."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from casare_rpa.nodes import file_nodes as old_module

        from casare_rpa.nodes import file as new_module

        # Check all __all__ items from old module exist in new
        for name in old_module.__all__:
            assert hasattr(new_module, name), f"Missing {name} in new module"
            old_obj = getattr(old_module, name)
            new_obj = getattr(new_module, name)
            assert old_obj is new_obj, f"{name} not identical between old and new"

    def test_http_nodes_all_exports(self):
        """Verify all http_nodes exports are available from both paths."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from casare_rpa.nodes import http_nodes as old_module

        from casare_rpa.nodes import http as new_module

        for name in old_module.__all__:
            assert hasattr(new_module, name), f"Missing {name} in new module"
            old_obj = getattr(old_module, name)
            new_obj = getattr(new_module, name)
            assert old_obj is new_obj, f"{name} not identical between old and new"

    def test_database_nodes_all_exports(self):
        """Verify all database_nodes exports are available from both paths."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from casare_rpa.nodes import database_nodes as old_module

        from casare_rpa.nodes import database as new_module

        for name in old_module.__all__:
            assert hasattr(new_module, name), f"Missing {name} in new module"
            old_obj = getattr(old_module, name)
            new_obj = getattr(new_module, name)
            assert old_obj is new_obj, f"{name} not identical between old and new"

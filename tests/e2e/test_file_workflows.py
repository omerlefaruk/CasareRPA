"""
CasareRPA - E2E Tests for File Operation Workflows.

Tests basic file operations including:
- Text file read/write/append
- File system operations (copy, move, delete, exists)
- Directory operations (create, list, delete)
- File info retrieval

Uses real ExecutionContext and temp_workspace fixture.
"""

from pathlib import Path

import pytest

from tests.e2e.helpers import WorkflowBuilder


# =============================================================================
# TEXT FILE OPERATIONS
# =============================================================================


class TestTextFileOperations:
    """Test basic text file read/write operations."""

    @pytest.mark.asyncio
    async def test_write_and_read_text_file(self, temp_workspace: Path) -> None:
        """Write content to file, then read and verify."""
        file_path = str(temp_workspace / "test.txt")
        content = "Hello, World!"

        result = await (
            WorkflowBuilder("write_read_file")
            .add_start()
            .add_write_file(file_path, content, node_id="write")
            .add_read_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("result") == content
        assert Path(file_path).exists()
        assert Path(file_path).read_text() == content

    @pytest.mark.asyncio
    async def test_append_to_file(self, temp_workspace: Path) -> None:
        """Write initial content, then append and verify both lines."""
        file_path = str(temp_workspace / "append_test.txt")
        line1 = "Line 1\n"
        line2 = "Line 2\n"

        result = await (
            WorkflowBuilder("append_file")
            .add_start()
            .add_write_file(file_path, line1, node_id="write1")
            .add_append_file(file_path, line2, node_id="write2")
            .add_read_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("result") == line1 + line2
        assert Path(file_path).read_text() == line1 + line2

    @pytest.mark.asyncio
    async def test_read_file_with_multiple_lines(self, temp_workspace: Path) -> None:
        """Write multiple lines, read and verify line count."""
        file_path = str(temp_workspace / "multi_line.txt")
        lines = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

        result = await (
            WorkflowBuilder("multi_line_file")
            .add_start()
            .add_write_file(file_path, lines, node_id="write")
            .add_read_file(file_path, node_id="read")
            .add_set_variable("content", "{{read.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        content = result["variables"].get("content", "")
        assert content.count("\n") == 4  # 5 lines = 4 newlines

    @pytest.mark.asyncio
    async def test_overwrite_file(self, temp_workspace: Path) -> None:
        """Write content, then overwrite with new content."""
        file_path = str(temp_workspace / "overwrite.txt")
        old_content = "Old content"
        new_content = "New content"

        result = await (
            WorkflowBuilder("overwrite_file")
            .add_start()
            .add_write_file(file_path, old_content, node_id="write1")
            .add_write_file(file_path, new_content, node_id="write2")
            .add_read_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("result") == new_content
        assert Path(file_path).read_text() == new_content

    @pytest.mark.asyncio
    async def test_write_file_with_utf8_content(self, temp_workspace: Path) -> None:
        """Write and read UTF-8 content including special characters."""
        file_path = str(temp_workspace / "utf8.txt")
        content = "Hello World! Hola Mundo! Bonjour!"

        result = await (
            WorkflowBuilder("utf8_file")
            .add_start()
            .add_write_file(file_path, content, encoding="utf-8", node_id="write")
            .add_read_file(file_path, encoding="utf-8", node_id="read")
            .add_set_variable("result", "{{read.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("result") == content

    @pytest.mark.asyncio
    async def test_write_empty_file(self, temp_workspace: Path) -> None:
        """Write empty content to file."""
        file_path = str(temp_workspace / "empty.txt")

        result = await (
            WorkflowBuilder("empty_file")
            .add_start()
            .add_write_file(file_path, "", node_id="write")
            .add_read_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.content}}")
            .add_set_variable("size", "{{read.size}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("result") == ""
        assert result["variables"].get("size") == 0


# =============================================================================
# FILE SYSTEM OPERATIONS
# =============================================================================


class TestFileSystemOperations:
    """Test file system operations: copy, move, delete, exists."""

    @pytest.mark.asyncio
    async def test_file_exists_true(self, temp_workspace: Path) -> None:
        """Write file, then check it exists."""
        file_path = str(temp_workspace / "exists_test.txt")

        result = await (
            WorkflowBuilder("file_exists_true")
            .add_start()
            .add_write_file(file_path, "test content", node_id="write")
            .add_file_exists(file_path, node_id="check")
            .add_set_variable("exists", "{{check.exists}}")
            .add_set_variable("is_file", "{{check.is_file}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("exists") is True
        assert result["variables"].get("is_file") is True

    @pytest.mark.asyncio
    async def test_file_exists_false(self, temp_workspace: Path) -> None:
        """Check non-existent file returns false."""
        file_path = str(temp_workspace / "nonexistent.txt")

        result = await (
            WorkflowBuilder("file_exists_false")
            .add_start()
            .add_file_exists(file_path, node_id="check")
            .add_set_variable("exists", "{{check.exists}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("exists") is False

    @pytest.mark.asyncio
    async def test_copy_file(self, temp_workspace: Path) -> None:
        """Write file, copy to new location, verify both exist with same content."""
        src_path = str(temp_workspace / "source.txt")
        dst_path = str(temp_workspace / "destination.txt")
        content = "Copy me!"

        result = await (
            WorkflowBuilder("copy_file")
            .add_start()
            .add_write_file(src_path, content, node_id="write")
            .add_copy_file(src_path, dst_path, node_id="copy")
            .add_read_file(dst_path, node_id="read")
            .add_set_variable("copied_content", "{{read.content}}")
            .add_file_exists(src_path, node_id="check_src")
            .add_set_variable("src_exists", "{{check_src.exists}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("copied_content") == content
        assert result["variables"].get("src_exists") is True
        assert Path(src_path).exists()
        assert Path(dst_path).exists()

    @pytest.mark.asyncio
    async def test_copy_file_to_subdirectory(self, temp_workspace: Path) -> None:
        """Copy file to new subdirectory (creates dirs automatically)."""
        src_path = str(temp_workspace / "source.txt")
        dst_path = str(temp_workspace / "subdir" / "nested" / "copy.txt")
        content = "Nested copy"

        result = await (
            WorkflowBuilder("copy_to_subdir")
            .add_start()
            .add_write_file(src_path, content, node_id="write")
            .add_copy_file(src_path, dst_path, create_dirs=True, node_id="copy")
            .add_read_file(dst_path, node_id="read")
            .add_set_variable("copied_content", "{{read.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("copied_content") == content
        assert Path(dst_path).exists()

    @pytest.mark.asyncio
    async def test_move_file(self, temp_workspace: Path) -> None:
        """Write file, move to new location, verify old gone, new exists."""
        src_path = str(temp_workspace / "to_move.txt")
        dst_path = str(temp_workspace / "moved.txt")
        content = "Move me!"

        result = await (
            WorkflowBuilder("move_file")
            .add_start()
            .add_write_file(src_path, content, node_id="write")
            .add_move_file(src_path, dst_path, node_id="move")
            .add_read_file(dst_path, node_id="read")
            .add_set_variable("moved_content", "{{read.content}}")
            .add_file_exists(src_path, node_id="check_src")
            .add_set_variable("src_exists", "{{check_src.exists}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("moved_content") == content
        assert result["variables"].get("src_exists") is False
        assert not Path(src_path).exists()
        assert Path(dst_path).exists()

    @pytest.mark.asyncio
    async def test_delete_file(self, temp_workspace: Path) -> None:
        """Write file, delete it, verify gone."""
        file_path = str(temp_workspace / "to_delete.txt")

        result = await (
            WorkflowBuilder("delete_file")
            .add_start()
            .add_write_file(file_path, "Delete me!", node_id="write")
            .add_delete_file(file_path, node_id="delete")
            .add_file_exists(file_path, node_id="check")
            .add_set_variable("exists", "{{check.exists}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("exists") is False
        assert not Path(file_path).exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_with_ignore(self, temp_workspace: Path) -> None:
        """Delete non-existent file with ignore_missing=True succeeds."""
        file_path = str(temp_workspace / "does_not_exist.txt")

        result = await (
            WorkflowBuilder("delete_ignore")
            .add_start()
            .add_delete_file(file_path, ignore_missing=True, node_id="delete")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    @pytest.mark.asyncio
    async def test_get_file_info(self, temp_workspace: Path) -> None:
        """Write file, get info, verify size and extension."""
        file_path = str(temp_workspace / "info_test.txt")
        content = "Test content for info"

        result = await (
            WorkflowBuilder("file_info")
            .add_start()
            .add_write_file(file_path, content, node_id="write")
            .add_get_file_info(file_path, node_id="info")
            .add_set_variable("size", "{{info.size}}")
            .add_set_variable("extension", "{{info.extension}}")
            .add_set_variable("name", "{{info.name}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("size") == len(content)
        assert result["variables"].get("extension") == ".txt"
        assert result["variables"].get("name") == "info_test.txt"

    @pytest.mark.asyncio
    async def test_get_file_size(self, temp_workspace: Path) -> None:
        """Write file, get size, verify matches content length."""
        file_path = str(temp_workspace / "size_test.txt")
        content = "Exactly 20 chars!!!"  # 20 characters

        result = await (
            WorkflowBuilder("file_size")
            .add_start()
            .add_write_file(file_path, content, node_id="write")
            .add_get_file_size(file_path, node_id="size")
            .add_set_variable("size", "{{size.size}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("size") == len(content)


# =============================================================================
# DIRECTORY OPERATIONS
# =============================================================================


class TestDirectoryOperations:
    """Test directory operations: create, list, exists."""

    @pytest.mark.asyncio
    async def test_create_directory(self, temp_workspace: Path) -> None:
        """Create directory, verify it exists."""
        dir_path = str(temp_workspace / "new_dir")

        result = await (
            WorkflowBuilder("create_directory")
            .add_start()
            .add_create_directory(dir_path, node_id="create")
            .add_file_exists(dir_path, check_type="directory", node_id="check")
            .add_set_variable("exists", "{{check.exists}}")
            .add_set_variable("is_dir", "{{check.is_dir}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("exists") is True
        assert result["variables"].get("is_dir") is True
        assert Path(dir_path).is_dir()

    @pytest.mark.asyncio
    async def test_create_nested_directories(self, temp_workspace: Path) -> None:
        """Create nested directory structure."""
        dir_path = str(temp_workspace / "a" / "b" / "c")

        result = await (
            WorkflowBuilder("nested_dirs")
            .add_start()
            .add_create_directory(dir_path, parents=True, node_id="create")
            .add_file_exists(dir_path, check_type="directory", node_id="check")
            .add_set_variable("exists", "{{check.exists}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("exists") is True
        assert Path(dir_path).is_dir()
        assert (temp_workspace / "a").is_dir()
        assert (temp_workspace / "a" / "b").is_dir()

    @pytest.mark.asyncio
    async def test_list_directory(self, temp_workspace: Path) -> None:
        """Create files, list directory, verify count."""
        # Create test files
        (temp_workspace / "file1.txt").write_text("content1")
        (temp_workspace / "file2.txt").write_text("content2")
        (temp_workspace / "file3.txt").write_text("content3")

        dir_path = str(temp_workspace)

        result = await (
            WorkflowBuilder("list_directory")
            .add_start()
            .add_list_directory(
                dir_path, pattern="*.txt", files_only=True, node_id="list"
            )
            .add_set_variable("items", "{{list.items}}")
            .add_set_variable("count", "{{list.count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("count") == 3
        items = result["variables"].get("items", [])
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_list_directory_with_pattern(self, temp_workspace: Path) -> None:
        """Create mixed files, list with pattern filter."""
        (temp_workspace / "data1.txt").write_text("txt1")
        (temp_workspace / "data2.txt").write_text("txt2")
        (temp_workspace / "data.csv").write_text("csv")
        (temp_workspace / "data.json").write_text("{}")

        dir_path = str(temp_workspace)

        result = await (
            WorkflowBuilder("list_pattern")
            .add_start()
            .add_list_directory(
                dir_path, pattern="*.txt", files_only=True, node_id="list"
            )
            .add_set_variable("count", "{{list.count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("count") == 2

    @pytest.mark.asyncio
    async def test_list_directory_recursive(self, temp_workspace: Path) -> None:
        """Create nested files, list recursively."""
        (temp_workspace / "file1.txt").write_text("root")
        subdir = temp_workspace / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("nested")
        subsubdir = subdir / "nested"
        subsubdir.mkdir()
        (subsubdir / "file3.txt").write_text("deep")

        dir_path = str(temp_workspace)

        result = await (
            WorkflowBuilder("list_recursive")
            .add_start()
            .add_list_directory(
                dir_path,
                pattern="*.txt",
                recursive=True,
                files_only=True,
                node_id="list",
            )
            .add_set_variable("count", "{{list.count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("count") == 3

    @pytest.mark.asyncio
    async def test_list_files_only(self, temp_workspace: Path) -> None:
        """List files only (exclude directories) using ListFilesNode."""
        (temp_workspace / "file.txt").write_text("file")
        (temp_workspace / "subdir").mkdir()

        dir_path = str(temp_workspace)

        result = await (
            WorkflowBuilder("list_files_only")
            .add_start()
            .add_list_files(dir_path, pattern="*", node_id="list")
            .add_set_variable("count", "{{list.count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("count") == 1


# =============================================================================
# ERROR HANDLING
# =============================================================================


class TestFileErrorHandling:
    """Test error handling for file operations."""

    @pytest.mark.asyncio
    async def test_read_nonexistent_file_error(self, temp_workspace: Path) -> None:
        """Reading non-existent file should fail."""
        file_path = str(temp_workspace / "does_not_exist.txt")

        result = await (
            WorkflowBuilder("read_nonexistent")
            .add_start()
            .add_read_file(file_path, node_id="read")
            .add_end()
            .execute()
        )

        assert not result["success"]
        assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_error(self, temp_workspace: Path) -> None:
        """Deleting non-existent file without ignore_missing should fail."""
        file_path = str(temp_workspace / "does_not_exist.txt")

        result = await (
            WorkflowBuilder("delete_nonexistent")
            .add_start()
            .add_delete_file(file_path, ignore_missing=False, node_id="delete")
            .add_end()
            .execute()
        )

        assert not result["success"]
        assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_copy_nonexistent_source_error(self, temp_workspace: Path) -> None:
        """Copying non-existent source file should fail."""
        src_path = str(temp_workspace / "no_source.txt")
        dst_path = str(temp_workspace / "destination.txt")

        result = await (
            WorkflowBuilder("copy_nonexistent")
            .add_start()
            .add_copy_file(src_path, dst_path, node_id="copy")
            .add_end()
            .execute()
        )

        assert not result["success"]
        assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_copy_to_existing_no_overwrite_error(
        self, temp_workspace: Path
    ) -> None:
        """Copying to existing file without overwrite should fail."""
        src_path = str(temp_workspace / "source.txt")
        dst_path = str(temp_workspace / "existing.txt")

        # Create both files
        Path(src_path).write_text("source content")
        Path(dst_path).write_text("existing content")

        result = await (
            WorkflowBuilder("copy_no_overwrite")
            .add_start()
            .add_copy_file(src_path, dst_path, overwrite=False, node_id="copy")
            .add_end()
            .execute()
        )

        assert not result["success"]
        assert result.get("error") is not None
        # Original content preserved
        assert Path(dst_path).read_text() == "existing content"


# =============================================================================
# WORKFLOW PATTERNS
# =============================================================================


class TestFileWorkflowPatterns:
    """Test common file operation workflow patterns."""

    @pytest.mark.asyncio
    async def test_file_backup_workflow(self, temp_workspace: Path) -> None:
        """Read file, create backup, modify original."""
        original_path = str(temp_workspace / "original.txt")
        backup_path = str(temp_workspace / "original.txt.bak")
        original_content = "Original content"
        modified_content = "Modified content"

        # Create original file
        Path(original_path).write_text(original_content)

        result = await (
            WorkflowBuilder("backup_workflow")
            .add_start()
            .add_copy_file(original_path, backup_path, node_id="backup")
            .add_write_file(original_path, modified_content, node_id="modify")
            .add_read_file(original_path, node_id="read_new")
            .add_set_variable("new_content", "{{read_new.content}}")
            .add_read_file(backup_path, node_id="read_backup")
            .add_set_variable("backup_content", "{{read_backup.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("new_content") == modified_content
        assert result["variables"].get("backup_content") == original_content

    @pytest.mark.asyncio
    async def test_directory_setup_workflow(self, temp_workspace: Path) -> None:
        """Create directory structure, add files, verify."""
        base = temp_workspace / "project"
        src_dir = str(base / "src")
        test_dir = str(base / "tests")
        config_file = str(base / "config.txt")

        result = await (
            WorkflowBuilder("dir_setup")
            .add_start()
            .add_create_directory(src_dir, node_id="create_src")
            .add_create_directory(test_dir, node_id="create_tests")
            .add_write_file(config_file, "config=value", node_id="write_config")
            .add_file_exists(src_dir, check_type="directory", node_id="check_src")
            .add_set_variable("src_exists", "{{check_src.exists}}")
            .add_file_exists(test_dir, check_type="directory", node_id="check_tests")
            .add_set_variable("tests_exists", "{{check_tests.exists}}")
            .add_file_exists(config_file, check_type="file", node_id="check_config")
            .add_set_variable("config_exists", "{{check_config.exists}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("src_exists") is True
        assert result["variables"].get("tests_exists") is True
        assert result["variables"].get("config_exists") is True

    @pytest.mark.asyncio
    async def test_file_rename_with_move(self, temp_workspace: Path) -> None:
        """Rename file using move operation."""
        old_name = str(temp_workspace / "old_name.txt")
        new_name = str(temp_workspace / "new_name.txt")
        content = "Rename test"

        result = await (
            WorkflowBuilder("rename_file")
            .add_start()
            .add_write_file(old_name, content, node_id="write")
            .add_move_file(old_name, new_name, node_id="rename")
            .add_file_exists(old_name, node_id="check_old")
            .add_set_variable("old_exists", "{{check_old.exists}}")
            .add_file_exists(new_name, node_id="check_new")
            .add_set_variable("new_exists", "{{check_new.exists}}")
            .add_read_file(new_name, node_id="read")
            .add_set_variable("content", "{{read.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("old_exists") is False
        assert result["variables"].get("new_exists") is True
        assert result["variables"].get("content") == content

    @pytest.mark.asyncio
    async def test_copy_with_overwrite(self, temp_workspace: Path) -> None:
        """Copy file, then copy again with overwrite."""
        src_path = str(temp_workspace / "source.txt")
        dst_path = str(temp_workspace / "dest.txt")
        content1 = "Version 1"
        content2 = "Version 2"

        result = await (
            WorkflowBuilder("copy_overwrite")
            .add_start()
            .add_write_file(src_path, content1, node_id="write1")
            .add_copy_file(src_path, dst_path, node_id="copy1")
            .add_write_file(src_path, content2, node_id="write2")
            .add_copy_file(src_path, dst_path, overwrite=True, node_id="copy2")
            .add_read_file(dst_path, node_id="read")
            .add_set_variable("content", "{{read.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("content") == content2

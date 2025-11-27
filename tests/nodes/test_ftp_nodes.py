"""
Tests for FTP operation nodes.

Tests 10 FTP nodes for connection, file transfer, and directory operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import ftplib
from pathlib import Path
from casare_rpa.core.execution_context import ExecutionContext


class TestFTPNodes:
    """Tests for FTP category nodes."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.get_variable = lambda k: context.variables.get(k)
        context.set_variable = lambda k, v: context.variables.__setitem__(k, v)
        return context

    @pytest.fixture
    def mock_ftp(self) -> None:
        """Create a mock FTP connection."""
        ftp = MagicMock()
        ftp.login.return_value = "230 Login successful"
        ftp.nlst.return_value = ["file1.txt", "file2.txt", "folder1"]
        ftp.size.return_value = 1024
        return ftp

    @pytest.fixture
    def connected_context(self, execution_context, mock_ftp) -> None:
        """Create context with active FTP connection."""
        execution_context.variables["_ftp_connection"] = mock_ftp
        return execution_context

    # =========================================================================
    # FTPConnectNode Tests (5 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_connect_node_success(self, execution_context) -> None:
        """Test FTPConnectNode establishes connection."""
        from casare_rpa.nodes.ftp_nodes import FTPConnectNode

        mock_ftp = MagicMock()
        mock_ftp.login.return_value = "230 Login OK"

        with patch("casare_rpa.nodes.ftp_nodes.ftplib.FTP", return_value=mock_ftp):
            node = FTPConnectNode(node_id="test_connect")
            node.set_input_value("host", "ftp.example.com")
            node.set_input_value("port", 21)
            node.set_input_value("username", "user")
            node.set_input_value("password", "pass")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("connected") is True
            assert "230" in node.get_output_value("server_message")
            assert "_ftp_connection" in execution_context.variables

    @pytest.mark.asyncio
    async def test_ftp_connect_node_tls(self, execution_context) -> None:
        """Test FTPConnectNode with TLS."""
        from casare_rpa.nodes.ftp_nodes import FTPConnectNode

        mock_ftp_tls = MagicMock()
        mock_ftp_tls.login.return_value = "234 AUTH TLS OK"

        with patch(
            "casare_rpa.nodes.ftp_nodes.ftplib.FTP_TLS", return_value=mock_ftp_tls
        ):
            node = FTPConnectNode(node_id="test_tls", config={"use_tls": True})
            node.set_input_value("host", "ftps.example.com")
            node.set_input_value("username", "user")
            node.set_input_value("password", "pass")

            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_ftp_tls.prot_p.assert_called_once()

    @pytest.mark.asyncio
    async def test_ftp_connect_node_missing_host(self, execution_context) -> None:
        """Test FTPConnectNode handles missing host."""
        from casare_rpa.nodes.ftp_nodes import FTPConnectNode

        node = FTPConnectNode(node_id="test_no_host")
        node.set_input_value("host", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()
        assert node.get_output_value("connected") is False

    @pytest.mark.asyncio
    async def test_ftp_connect_node_connection_refused(self, execution_context) -> None:
        """Test FTPConnectNode handles connection error."""
        from casare_rpa.nodes.ftp_nodes import FTPConnectNode

        with patch("casare_rpa.nodes.ftp_nodes.ftplib.FTP") as mock_ftp_class:
            mock_ftp_class.return_value.connect.side_effect = ConnectionRefusedError(
                "Connection refused"
            )

            node = FTPConnectNode(node_id="test_refused")
            node.set_input_value("host", "ftp.example.com")

            result = await node.execute(execution_context)

            assert result["success"] is False
            assert node.get_output_value("connected") is False

    @pytest.mark.asyncio
    async def test_ftp_connect_node_passive_mode(self, execution_context) -> None:
        """Test FTPConnectNode sets passive mode."""
        from casare_rpa.nodes.ftp_nodes import FTPConnectNode

        mock_ftp = MagicMock()
        mock_ftp.login.return_value = "230 OK"

        with patch("casare_rpa.nodes.ftp_nodes.ftplib.FTP", return_value=mock_ftp):
            node = FTPConnectNode(node_id="test_passive", config={"passive": True})
            node.set_input_value("host", "ftp.example.com")

            await node.execute(execution_context)

            mock_ftp.set_pasv.assert_called_with(True)

    # =========================================================================
    # FTPDisconnectNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_disconnect_node_success(
        self, connected_context, mock_ftp
    ) -> None:
        """Test FTPDisconnectNode disconnects properly."""
        from casare_rpa.nodes.ftp_nodes import FTPDisconnectNode

        node = FTPDisconnectNode(node_id="test_disconnect")

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("disconnected") is True
        mock_ftp.quit.assert_called_once()
        assert connected_context.variables.get("_ftp_connection") is None

    @pytest.mark.asyncio
    async def test_ftp_disconnect_node_no_connection(self, execution_context) -> None:
        """Test FTPDisconnectNode when no connection exists."""
        from casare_rpa.nodes.ftp_nodes import FTPDisconnectNode

        node = FTPDisconnectNode(node_id="test_no_conn")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("disconnected") is True

    @pytest.mark.asyncio
    async def test_ftp_disconnect_node_quit_error(
        self, connected_context, mock_ftp
    ) -> None:
        """Test FTPDisconnectNode falls back to close on quit error."""
        from casare_rpa.nodes.ftp_nodes import FTPDisconnectNode

        mock_ftp.quit.side_effect = Exception("Connection reset")

        node = FTPDisconnectNode(node_id="test_quit_err")

        result = await node.execute(connected_context)

        assert result["success"] is True
        mock_ftp.close.assert_called_once()

    # =========================================================================
    # FTPUploadNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_upload_node_success(
        self, connected_context, mock_ftp, tmp_path
    ) -> None:
        """Test FTPUploadNode uploads file."""
        from casare_rpa.nodes.ftp_nodes import FTPUploadNode

        local_file = tmp_path / "upload.txt"
        local_file.write_text("Upload content")

        node = FTPUploadNode(node_id="test_upload")
        node.set_input_value("local_path", str(local_file))
        node.set_input_value("remote_path", "/remote/upload.txt")

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("uploaded") is True
        assert node.get_output_value("bytes_sent") > 0
        mock_ftp.storbinary.assert_called_once()

    @pytest.mark.asyncio
    async def test_ftp_upload_node_no_connection(
        self, execution_context, tmp_path
    ) -> None:
        """Test FTPUploadNode fails without connection."""
        from casare_rpa.nodes.ftp_nodes import FTPUploadNode

        local_file = tmp_path / "test.txt"
        local_file.write_text("test")

        node = FTPUploadNode(node_id="test_no_conn_upload")
        node.set_input_value("local_path", str(local_file))
        node.set_input_value("remote_path", "/remote/test.txt")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "connection" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ftp_upload_node_file_not_found(self, connected_context) -> None:
        """Test FTPUploadNode handles missing local file."""
        from casare_rpa.nodes.ftp_nodes import FTPUploadNode

        node = FTPUploadNode(node_id="test_missing_upload")
        node.set_input_value("local_path", "/nonexistent/file.txt")
        node.set_input_value("remote_path", "/remote/file.txt")

        result = await node.execute(connected_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ftp_upload_node_create_dirs(
        self, connected_context, mock_ftp, tmp_path
    ) -> None:
        """Test FTPUploadNode creates remote directories."""
        from casare_rpa.nodes.ftp_nodes import FTPUploadNode

        local_file = tmp_path / "test.txt"
        local_file.write_text("test")

        node = FTPUploadNode(node_id="test_create_dirs", config={"create_dirs": True})
        node.set_input_value("local_path", str(local_file))
        node.set_input_value("remote_path", "/remote/subdir/file.txt")

        result = await node.execute(connected_context)

        assert result["success"] is True
        mock_ftp.mkd.assert_called()

    # =========================================================================
    # FTPDownloadNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_download_node_success(
        self, connected_context, mock_ftp, tmp_path
    ) -> None:
        """Test FTPDownloadNode downloads file."""
        from casare_rpa.nodes.ftp_nodes import FTPDownloadNode

        def write_callback(cmd, callback):
            callback(b"Downloaded content")

        mock_ftp.retrbinary.side_effect = write_callback

        local_path = tmp_path / "downloaded.txt"

        node = FTPDownloadNode(node_id="test_download")
        node.set_input_value("remote_path", "/remote/file.txt")
        node.set_input_value("local_path", str(local_path))

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("downloaded") is True
        assert node.get_output_value("bytes_received") > 0

    @pytest.mark.asyncio
    async def test_ftp_download_node_no_connection(
        self, execution_context, tmp_path
    ) -> None:
        """Test FTPDownloadNode fails without connection."""
        from casare_rpa.nodes.ftp_nodes import FTPDownloadNode

        node = FTPDownloadNode(node_id="test_no_conn_dl")
        node.set_input_value("remote_path", "/remote/file.txt")
        node.set_input_value("local_path", str(tmp_path / "file.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "connection" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ftp_download_node_file_exists_no_overwrite(
        self, connected_context, tmp_path
    ) -> None:
        """Test FTPDownloadNode respects overwrite setting."""
        from casare_rpa.nodes.ftp_nodes import FTPDownloadNode

        local_file = tmp_path / "existing.txt"
        local_file.write_text("existing content")

        node = FTPDownloadNode(node_id="test_no_overwrite", config={"overwrite": False})
        node.set_input_value("remote_path", "/remote/file.txt")
        node.set_input_value("local_path", str(local_file))

        result = await node.execute(connected_context)

        assert result["success"] is False
        assert "exists" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ftp_download_node_overwrite(
        self, connected_context, mock_ftp, tmp_path
    ) -> None:
        """Test FTPDownloadNode overwrites when allowed."""
        from casare_rpa.nodes.ftp_nodes import FTPDownloadNode

        local_file = tmp_path / "existing.txt"
        local_file.write_text("old content")

        def write_callback(cmd, callback):
            callback(b"new content")

        mock_ftp.retrbinary.side_effect = write_callback

        node = FTPDownloadNode(node_id="test_overwrite", config={"overwrite": True})
        node.set_input_value("remote_path", "/remote/file.txt")
        node.set_input_value("local_path", str(local_file))

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("downloaded") is True

    # =========================================================================
    # FTPListNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_list_node_success(self, connected_context, mock_ftp) -> None:
        """Test FTPListNode lists directory contents."""
        from casare_rpa.nodes.ftp_nodes import FTPListNode

        node = FTPListNode(node_id="test_list")
        node.set_input_value("remote_path", "/remote/dir")

        result = await node.execute(connected_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert len(items) == 3
        assert "file1.txt" in items

    @pytest.mark.asyncio
    async def test_ftp_list_node_detailed(self, connected_context, mock_ftp) -> None:
        """Test FTPListNode with detailed listing."""
        from casare_rpa.nodes.ftp_nodes import FTPListNode

        def mock_dir(path, callback):
            callback("-rw-r--r-- 1 user group 1024 Jan 1 12:00 file1.txt")
            callback("drwxr-xr-x 2 user group 4096 Jan 1 12:00 folder1")

        mock_ftp.dir = mock_dir

        node = FTPListNode(node_id="test_detailed", config={"detailed": True})
        node.set_input_value("remote_path", "/remote")

        result = await node.execute(connected_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert len(items) == 2
        assert "file1.txt" in items[0]

    @pytest.mark.asyncio
    async def test_ftp_list_node_no_connection(self, execution_context) -> None:
        """Test FTPListNode fails without connection."""
        from casare_rpa.nodes.ftp_nodes import FTPListNode

        node = FTPListNode(node_id="test_no_conn_list")
        node.set_input_value("remote_path", "/remote")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "connection" in result["error"].lower()

    # =========================================================================
    # FTPDeleteNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_delete_node_success(self, connected_context, mock_ftp) -> None:
        """Test FTPDeleteNode deletes file."""
        from casare_rpa.nodes.ftp_nodes import FTPDeleteNode

        node = FTPDeleteNode(node_id="test_delete")
        node.set_input_value("remote_path", "/remote/file.txt")

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("deleted") is True
        mock_ftp.delete.assert_called_with("/remote/file.txt")

    @pytest.mark.asyncio
    async def test_ftp_delete_node_missing_path(self, connected_context) -> None:
        """Test FTPDeleteNode handles missing path."""
        from casare_rpa.nodes.ftp_nodes import FTPDeleteNode

        node = FTPDeleteNode(node_id="test_no_path")
        node.set_input_value("remote_path", "")

        result = await node.execute(connected_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ftp_delete_node_no_connection(self, execution_context) -> None:
        """Test FTPDeleteNode fails without connection."""
        from casare_rpa.nodes.ftp_nodes import FTPDeleteNode

        node = FTPDeleteNode(node_id="test_no_conn_del")
        node.set_input_value("remote_path", "/remote/file.txt")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "connection" in result["error"].lower()

    # =========================================================================
    # FTPRenameNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_rename_node_success(self, connected_context, mock_ftp) -> None:
        """Test FTPRenameNode renames file."""
        from casare_rpa.nodes.ftp_nodes import FTPRenameNode

        node = FTPRenameNode(node_id="test_rename")
        node.set_input_value("old_path", "/remote/old.txt")
        node.set_input_value("new_path", "/remote/new.txt")

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("renamed") is True
        mock_ftp.rename.assert_called_with("/remote/old.txt", "/remote/new.txt")

    @pytest.mark.asyncio
    async def test_ftp_rename_node_missing_paths(self, connected_context) -> None:
        """Test FTPRenameNode handles missing paths."""
        from casare_rpa.nodes.ftp_nodes import FTPRenameNode

        node = FTPRenameNode(node_id="test_no_paths")
        node.set_input_value("old_path", "")
        node.set_input_value("new_path", "")

        result = await node.execute(connected_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ftp_rename_node_no_connection(self, execution_context) -> None:
        """Test FTPRenameNode fails without connection."""
        from casare_rpa.nodes.ftp_nodes import FTPRenameNode

        node = FTPRenameNode(node_id="test_no_conn_rename")
        node.set_input_value("old_path", "/old.txt")
        node.set_input_value("new_path", "/new.txt")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "connection" in result["error"].lower()

    # =========================================================================
    # FTPMakeDirNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_mkdir_node_success(self, connected_context, mock_ftp) -> None:
        """Test FTPMakeDirNode creates directory."""
        from casare_rpa.nodes.ftp_nodes import FTPMakeDirNode

        node = FTPMakeDirNode(node_id="test_mkdir")
        node.set_input_value("remote_path", "/remote/newdir")

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("created") is True
        mock_ftp.mkd.assert_called_with("/remote/newdir")

    @pytest.mark.asyncio
    async def test_ftp_mkdir_node_parents(self, connected_context, mock_ftp) -> None:
        """Test FTPMakeDirNode creates parent directories."""
        from casare_rpa.nodes.ftp_nodes import FTPMakeDirNode

        node = FTPMakeDirNode(node_id="test_mkdir_parents", config={"parents": True})
        node.set_input_value("remote_path", "/remote/path/to/dir")

        result = await node.execute(connected_context)

        assert result["success"] is True
        # Should call mkd multiple times for parent dirs
        assert mock_ftp.mkd.call_count >= 1

    @pytest.mark.asyncio
    async def test_ftp_mkdir_node_no_connection(self, execution_context) -> None:
        """Test FTPMakeDirNode fails without connection."""
        from casare_rpa.nodes.ftp_nodes import FTPMakeDirNode

        node = FTPMakeDirNode(node_id="test_no_conn_mkdir")
        node.set_input_value("remote_path", "/remote/dir")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "connection" in result["error"].lower()

    # =========================================================================
    # FTPRemoveDirNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_rmdir_node_success(self, connected_context, mock_ftp) -> None:
        """Test FTPRemoveDirNode removes directory."""
        from casare_rpa.nodes.ftp_nodes import FTPRemoveDirNode

        node = FTPRemoveDirNode(node_id="test_rmdir")
        node.set_input_value("remote_path", "/remote/emptydir")

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("removed") is True
        mock_ftp.rmd.assert_called_with("/remote/emptydir")

    @pytest.mark.asyncio
    async def test_ftp_rmdir_node_missing_path(self, connected_context) -> None:
        """Test FTPRemoveDirNode handles missing path."""
        from casare_rpa.nodes.ftp_nodes import FTPRemoveDirNode

        node = FTPRemoveDirNode(node_id="test_no_rmdir_path")
        node.set_input_value("remote_path", "")

        result = await node.execute(connected_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ftp_rmdir_node_no_connection(self, execution_context) -> None:
        """Test FTPRemoveDirNode fails without connection."""
        from casare_rpa.nodes.ftp_nodes import FTPRemoveDirNode

        node = FTPRemoveDirNode(node_id="test_no_conn_rmdir")
        node.set_input_value("remote_path", "/remote/dir")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "connection" in result["error"].lower()

    # =========================================================================
    # FTPGetSizeNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ftp_getsize_node_success(self, connected_context, mock_ftp) -> None:
        """Test FTPGetSizeNode gets file size."""
        from casare_rpa.nodes.ftp_nodes import FTPGetSizeNode

        node = FTPGetSizeNode(node_id="test_size")
        node.set_input_value("remote_path", "/remote/file.txt")

        result = await node.execute(connected_context)

        assert result["success"] is True
        assert node.get_output_value("found") is True
        assert node.get_output_value("size") == 1024

    @pytest.mark.asyncio
    async def test_ftp_getsize_node_file_not_found(
        self, connected_context, mock_ftp
    ) -> None:
        """Test FTPGetSizeNode handles missing file."""
        from casare_rpa.nodes.ftp_nodes import FTPGetSizeNode

        mock_ftp.size.side_effect = ftplib.error_perm("550 File not found")

        node = FTPGetSizeNode(node_id="test_no_file_size")
        node.set_input_value("remote_path", "/remote/missing.txt")

        result = await node.execute(connected_context)

        assert result["success"] is True  # Returns success=True but found=False
        assert node.get_output_value("found") is False
        assert node.get_output_value("size") == 0

    @pytest.mark.asyncio
    async def test_ftp_getsize_node_missing_path(self, connected_context) -> None:
        """Test FTPGetSizeNode handles missing path."""
        from casare_rpa.nodes.ftp_nodes import FTPGetSizeNode

        node = FTPGetSizeNode(node_id="test_no_size_path")
        node.set_input_value("remote_path", "")

        result = await node.execute(connected_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ftp_getsize_node_no_connection(self, execution_context) -> None:
        """Test FTPGetSizeNode fails without connection."""
        from casare_rpa.nodes.ftp_nodes import FTPGetSizeNode

        node = FTPGetSizeNode(node_id="test_no_conn_size")
        node.set_input_value("remote_path", "/remote/file.txt")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "connection" in result["error"].lower()


class TestFTPNodesEdgeCases:
    """Edge case tests for FTP nodes."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.get_variable = lambda k: context.variables.get(k)
        context.set_variable = lambda k, v: context.variables.__setitem__(k, v)
        return context

    @pytest.mark.asyncio
    async def test_ftp_connect_retry_on_failure(self, execution_context) -> None:
        """Test FTPConnectNode retries on failure."""
        from casare_rpa.nodes.ftp_nodes import FTPConnectNode

        mock_ftp = MagicMock()
        call_count = 0

        def connect_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")

        mock_ftp.connect.side_effect = connect_side_effect
        mock_ftp.login.return_value = "230 OK"

        with (
            patch("casare_rpa.nodes.ftp_nodes.ftplib.FTP", return_value=mock_ftp),
            patch("asyncio.sleep"),
        ):
            node = FTPConnectNode(
                node_id="test_retry", config={"retry_count": 2, "retry_interval": 100}
            )
            node.set_input_value("host", "ftp.example.com")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_ftp_upload_text_mode(self, execution_context, tmp_path) -> None:
        """Test FTPUploadNode in text mode."""
        from casare_rpa.nodes.ftp_nodes import FTPUploadNode

        local_file = tmp_path / "text.txt"
        local_file.write_text("text content")

        mock_ftp = MagicMock()
        execution_context.variables["_ftp_connection"] = mock_ftp

        node = FTPUploadNode(node_id="test_text_upload", config={"binary_mode": False})
        node.set_input_value("local_path", str(local_file))
        node.set_input_value("remote_path", "/remote/text.txt")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_ftp.storlines.assert_called_once()

    @pytest.mark.asyncio
    async def test_ftp_download_text_mode(self, execution_context, tmp_path) -> None:
        """Test FTPDownloadNode in text mode."""
        from casare_rpa.nodes.ftp_nodes import FTPDownloadNode

        mock_ftp = MagicMock()

        def retrlines_callback(cmd, callback):
            callback("line 1")
            callback("line 2")

        mock_ftp.retrlines.side_effect = retrlines_callback
        execution_context.variables["_ftp_connection"] = mock_ftp

        local_path = tmp_path / "text_download.txt"

        node = FTPDownloadNode(node_id="test_text_dl", config={"binary_mode": False})
        node.set_input_value("remote_path", "/remote/file.txt")
        node.set_input_value("local_path", str(local_path))

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_ftp.retrlines.assert_called_once()

    @pytest.mark.asyncio
    async def test_ftp_list_empty_path(self, execution_context) -> None:
        """Test FTPListNode with empty path lists current directory."""
        from casare_rpa.nodes.ftp_nodes import FTPListNode

        mock_ftp = MagicMock()
        mock_ftp.nlst.return_value = ["file.txt"]
        execution_context.variables["_ftp_connection"] = mock_ftp

        node = FTPListNode(node_id="test_empty_path")
        node.set_input_value("remote_path", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Should call nlst with no arguments
        mock_ftp.nlst.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_ftp_mkdir_already_exists(self, execution_context) -> None:
        """Test FTPMakeDirNode handles existing directory with parents option."""
        from casare_rpa.nodes.ftp_nodes import FTPMakeDirNode

        mock_ftp = MagicMock()
        mock_ftp.mkd.side_effect = ftplib.error_perm("550 Directory exists")
        execution_context.variables["_ftp_connection"] = mock_ftp

        node = FTPMakeDirNode(node_id="test_exists", config={"parents": True})
        node.set_input_value("remote_path", "/existing/dir")

        result = await node.execute(execution_context)

        # Should succeed (ignores "already exists" error with parents=True)
        assert result["success"] is True

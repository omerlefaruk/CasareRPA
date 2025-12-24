"""
Tests for inline secret encryption feature.

Tests the CredentialStore inline secret methods and ExecutionContext
secret resolution ({{$secret:id}} pattern).
"""

import os

import pytest


class TestCredentialStoreInlineSecrets:
    """Tests for CredentialStore inline secret methods."""

    @pytest.fixture
    def temp_store(self, tmp_path):
        """Create a temporary credential store."""
        from casare_rpa.infrastructure.security.credential_store import CredentialStore

        store_path = tmp_path / "credentials" / "credentials.enc"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        return CredentialStore(store_path=store_path)

    def test_encrypt_inline_secret(self, temp_store):
        """Test encrypting a secret and getting back a credential ID."""
        plaintext = "my-secret-api-key-12345"
        credential_id = temp_store.encrypt_inline_secret(plaintext)

        assert credential_id is not None
        assert credential_id.startswith("cred_")
        assert len(credential_id) > 10

    def test_decrypt_inline_secret(self, temp_store):
        """Test decrypting an inline secret."""
        plaintext = "super-secret-password"
        credential_id = temp_store.encrypt_inline_secret(plaintext)

        decrypted = temp_store.decrypt_inline_secret(credential_id)
        assert decrypted == plaintext

    def test_decrypt_nonexistent_secret(self, temp_store):
        """Test decrypting a non-existent secret returns None."""
        result = temp_store.decrypt_inline_secret("cred_nonexistent")
        assert result is None

    def test_update_inline_secret(self, temp_store):
        """Test updating an existing inline secret."""
        original = "password123"
        credential_id = temp_store.encrypt_inline_secret(original)

        # Verify original
        assert temp_store.decrypt_inline_secret(credential_id) == original

        # Update
        new_value = "newpassword456"
        success = temp_store.update_inline_secret(credential_id, new_value)
        assert success is True

        # Verify updated
        assert temp_store.decrypt_inline_secret(credential_id) == new_value

    def test_update_nonexistent_secret(self, temp_store):
        """Test updating a non-existent secret fails gracefully."""
        success = temp_store.update_inline_secret("cred_fake", "value")
        assert success is False

    def test_list_inline_secrets(self, temp_store):
        """Test listing inline secrets."""
        # Create some secrets
        temp_store.encrypt_inline_secret("secret1", name="API Key 1")
        temp_store.encrypt_inline_secret("secret2", name="API Key 2")

        secrets = temp_store.list_inline_secrets()
        assert len(secrets) == 2
        names = [s["name"] for s in secrets]
        assert "API Key 1" in names
        assert "API Key 2" in names

    def test_encrypt_with_description(self, temp_store):
        """Test encrypting with custom name and description."""
        credential_id = temp_store.encrypt_inline_secret(
            plaintext="token123",
            name="GitHub Token",
            description="Personal access token for GitHub",
        )

        info = temp_store.get_credential_info(credential_id)
        assert info["name"] == "GitHub Token"
        assert info["description"] == "Personal access token for GitHub"
        assert info["category"] == "inline_secret"


class TestExecutionContextSecretResolution:
    """Tests for {{$secret:id}} resolution in ExecutionContext."""

    @pytest.fixture
    def temp_store(self, tmp_path):
        """Create a temporary credential store."""
        from casare_rpa.infrastructure.security.credential_store import CredentialStore

        store_path = tmp_path / "credentials" / "credentials.enc"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        return CredentialStore(store_path=store_path)

    @pytest.fixture
    def execution_context(self):
        """Create an execution context."""
        from casare_rpa.infrastructure.execution.execution_context import (
            ExecutionContext,
        )

        return ExecutionContext(workflow_name="test")

    def test_resolve_secret_pattern(self, temp_store, execution_context, monkeypatch):
        """Test resolving {{$secret:id}} pattern."""
        # Create a secret
        plaintext = "my-api-key"
        credential_id = temp_store.encrypt_inline_secret(plaintext)

        # Monkeypatch get_credential_store to return our temp store
        def mock_get_store():
            return temp_store

        monkeypatch.setattr(
            "casare_rpa.infrastructure.security.credential_store.get_credential_store",
            mock_get_store,
        )

        # Resolve the secret pattern
        value = f"{{{{$secret:{credential_id}}}}}"
        resolved = execution_context.resolve_value(value)

        assert resolved == plaintext

    def test_resolve_secret_in_mixed_string(self, temp_store, execution_context, monkeypatch):
        """Test resolving secret pattern embedded in a larger string."""
        plaintext = "secret123"
        credential_id = temp_store.encrypt_inline_secret(plaintext)

        def mock_get_store():
            return temp_store

        monkeypatch.setattr(
            "casare_rpa.infrastructure.security.credential_store.get_credential_store",
            mock_get_store,
        )

        value = f"Bearer {{{{$secret:{credential_id}}}}}"
        resolved = execution_context.resolve_value(value)

        assert resolved == f"Bearer {plaintext}"

    def test_resolve_nonexistent_secret_keeps_pattern(
        self, execution_context, temp_store, monkeypatch
    ):
        """Test that non-existent secrets keep the original pattern."""

        def mock_get_store():
            return temp_store

        monkeypatch.setattr(
            "casare_rpa.infrastructure.security.credential_store.get_credential_store",
            mock_get_store,
        )

        value = "{{$secret:cred_nonexistent}}"
        resolved = execution_context.resolve_value(value)

        # Should keep original pattern when not found
        assert resolved == value

    def test_resolve_mixed_variables_and_secrets(self, temp_store, execution_context, monkeypatch):
        """Test resolving both regular variables and secrets."""
        # Set up secret
        plaintext = "apikey123"
        credential_id = temp_store.encrypt_inline_secret(plaintext)

        # Set up regular variable
        execution_context.set_variable("host", "api.example.com")

        def mock_get_store():
            return temp_store

        monkeypatch.setattr(
            "casare_rpa.infrastructure.security.credential_store.get_credential_store",
            mock_get_store,
        )

        value = f"https://{{{{host}}}}/auth?key={{{{$secret:{credential_id}}}}}"
        resolved = execution_context.resolve_value(value)

        assert resolved == f"https://api.example.com/auth?key={plaintext}"


@pytest.mark.skipif(
    "CI" in os.environ or os.environ.get("QT_QPA_PLATFORM") == "offscreen",
    reason="Qt widget tests require display",
)
class TestEncryptableLineEditWidget:
    """Tests for the EncryptableLineEdit widget."""

    @pytest.fixture(autouse=True)
    def mock_qt(self, monkeypatch):
        """Mock Qt for headless testing."""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    def test_widget_creation(self):
        """Test creating the widget."""
        # Skip if Qt not available
        pytest.importorskip("PySide6")

        from casare_rpa.presentation.canvas.ui.widgets.encryptable_line_edit import (
            EncryptableLineEdit,
        )

        widget = EncryptableLineEdit()
        assert widget is not None
        assert not widget.isEncrypted()
        assert widget.getCredentialId() is None

    def test_set_plaintext(self):
        """Test setting plaintext value."""
        pytest.importorskip("PySide6")

        from casare_rpa.presentation.canvas.ui.widgets.encryptable_line_edit import (
            EncryptableLineEdit,
        )

        widget = EncryptableLineEdit()
        widget.setText("hello world")

        assert widget.text() == "hello world"
        assert not widget.isEncrypted()

    def test_set_secret_reference(self):
        """Test setting a secret reference."""
        pytest.importorskip("PySide6")

        from casare_rpa.presentation.canvas.ui.widgets.encryptable_line_edit import (
            EncryptableLineEdit,
        )

        widget = EncryptableLineEdit()
        widget.setText("{{$secret:cred_abc123}}")

        assert widget.isEncrypted()
        assert widget.getCredentialId() == "cred_abc123"
        # Text should return the secret reference
        assert widget.text() == "{{$secret:cred_abc123}}"

    def test_clear_widget(self):
        """Test clearing the widget."""
        pytest.importorskip("PySide6")

        from casare_rpa.presentation.canvas.ui.widgets.encryptable_line_edit import (
            EncryptableLineEdit,
        )

        widget = EncryptableLineEdit()
        widget.setText("{{$secret:cred_test}}")

        assert widget.isEncrypted()

        widget.clear()

        assert not widget.isEncrypted()
        assert widget.getCredentialId() is None
        assert widget.text() == ""

"""
Tests for Tenant domain entity.

Tests the TenantId value object, TenantSettings dataclass, and Tenant entity
for multi-tenant fleet management.

NO MOCKS - Domain layer tests use real domain objects only.
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID

from casare_rpa.domain.entities.tenant import (
    Tenant,
    TenantId,
    TenantSettings,
)


class TestTenantId:
    """Tests for TenantId value object."""

    def test_create_with_valid_uuid(self) -> None:
        """TenantId accepts valid UUID string."""
        tenant_id = TenantId("550e8400-e29b-41d4-a716-446655440000")
        assert tenant_id.value == "550e8400-e29b-41d4-a716-446655440000"

    def test_create_with_simple_string(self) -> None:
        """TenantId accepts any non-empty string."""
        tenant_id = TenantId("tenant-123")
        assert tenant_id.value == "tenant-123"

    def test_empty_string_raises_error(self) -> None:
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TenantId("")

    def test_whitespace_only_raises_error(self) -> None:
        """Whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TenantId("   ")

    def test_generate_creates_valid_uuid(self) -> None:
        """TenantId.generate() creates valid UUID."""
        tenant_id = TenantId.generate()
        # Should be able to parse as UUID
        UUID(tenant_id.value)
        assert len(tenant_id.value) == 36  # UUID format

    def test_generate_creates_unique_ids(self) -> None:
        """TenantId.generate() creates unique IDs each time."""
        ids = [TenantId.generate() for _ in range(10)]
        values = [t.value for t in ids]
        assert len(set(values)) == 10  # All unique

    def test_immutable(self) -> None:
        """TenantId is frozen dataclass (immutable)."""
        tenant_id = TenantId("test-id")
        with pytest.raises(Exception):  # FrozenInstanceError
            tenant_id.value = "new-value"

    def test_str_returns_value(self) -> None:
        """__str__ returns the value."""
        tenant_id = TenantId("my-tenant-id")
        assert str(tenant_id) == "my-tenant-id"

    def test_equality(self) -> None:
        """TenantId with same value are equal."""
        id1 = TenantId("same-value")
        id2 = TenantId("same-value")
        assert id1 == id2

    def test_inequality(self) -> None:
        """TenantId with different values are not equal."""
        id1 = TenantId("value-1")
        id2 = TenantId("value-2")
        assert id1 != id2

    def test_hashable(self) -> None:
        """TenantId can be used in sets and as dict keys."""
        id1 = TenantId("test-id")
        id2 = TenantId("test-id")
        id3 = TenantId("other-id")

        tenant_set = {id1, id2, id3}
        assert len(tenant_set) == 2  # id1 and id2 are same

        tenant_dict = {id1: "value1"}
        assert tenant_dict[id2] == "value1"


class TestTenantSettings:
    """Tests for TenantSettings dataclass."""

    def test_default_values(self) -> None:
        """TenantSettings has sensible defaults."""
        settings = TenantSettings()

        assert settings.max_robots == 10
        assert settings.max_concurrent_jobs == 20
        assert settings.allowed_capabilities == []
        assert settings.max_api_keys_per_robot == 5
        assert settings.job_retention_days == 30
        assert settings.enable_audit_logging is True
        assert settings.custom_settings == {}

    def test_custom_values(self) -> None:
        """TenantSettings accepts custom values."""
        settings = TenantSettings(
            max_robots=50,
            max_concurrent_jobs=100,
            allowed_capabilities=["browser", "desktop"],
            max_api_keys_per_robot=10,
            job_retention_days=90,
            enable_audit_logging=False,
            custom_settings={"feature_x": True},
        )

        assert settings.max_robots == 50
        assert settings.max_concurrent_jobs == 100
        assert settings.allowed_capabilities == ["browser", "desktop"]
        assert settings.max_api_keys_per_robot == 10
        assert settings.job_retention_days == 90
        assert settings.enable_audit_logging is False
        assert settings.custom_settings == {"feature_x": True}

    def test_negative_max_robots_raises_error(self) -> None:
        """Negative max_robots raises ValueError."""
        with pytest.raises(ValueError, match="max_robots must be >= 0"):
            TenantSettings(max_robots=-1)

    def test_zero_max_robots_allowed(self) -> None:
        """Zero max_robots is allowed (disabled tenant)."""
        settings = TenantSettings(max_robots=0)
        assert settings.max_robots == 0

    def test_negative_max_concurrent_jobs_raises_error(self) -> None:
        """Negative max_concurrent_jobs raises ValueError."""
        with pytest.raises(ValueError, match="max_concurrent_jobs must be >= 0"):
            TenantSettings(max_concurrent_jobs=-1)

    def test_zero_max_concurrent_jobs_allowed(self) -> None:
        """Zero max_concurrent_jobs is allowed (paused tenant)."""
        settings = TenantSettings(max_concurrent_jobs=0)
        assert settings.max_concurrent_jobs == 0

    def test_zero_api_keys_per_robot_raises_error(self) -> None:
        """max_api_keys_per_robot must be >= 1."""
        with pytest.raises(ValueError, match="max_api_keys_per_robot must be >= 1"):
            TenantSettings(max_api_keys_per_robot=0)

    def test_zero_job_retention_raises_error(self) -> None:
        """job_retention_days must be >= 1."""
        with pytest.raises(ValueError, match="job_retention_days must be >= 1"):
            TenantSettings(job_retention_days=0)

    def test_to_dict_serialization(self) -> None:
        """to_dict returns complete dictionary."""
        settings = TenantSettings(
            max_robots=15,
            allowed_capabilities=["browser"],
            custom_settings={"key": "value"},
        )

        result = settings.to_dict()

        assert result["max_robots"] == 15
        assert result["max_concurrent_jobs"] == 20  # default
        assert result["allowed_capabilities"] == ["browser"]
        assert result["max_api_keys_per_robot"] == 5  # default
        assert result["job_retention_days"] == 30  # default
        assert result["enable_audit_logging"] is True  # default
        assert result["custom_settings"] == {"key": "value"}

    def test_from_dict_deserialization(self) -> None:
        """from_dict creates settings from dictionary."""
        data = {
            "max_robots": 25,
            "max_concurrent_jobs": 50,
            "allowed_capabilities": ["desktop", "gpu"],
            "max_api_keys_per_robot": 3,
            "job_retention_days": 60,
            "enable_audit_logging": False,
            "custom_settings": {"rate_limit": 100},
        }

        settings = TenantSettings.from_dict(data)

        assert settings.max_robots == 25
        assert settings.max_concurrent_jobs == 50
        assert settings.allowed_capabilities == ["desktop", "gpu"]
        assert settings.max_api_keys_per_robot == 3
        assert settings.job_retention_days == 60
        assert settings.enable_audit_logging is False
        assert settings.custom_settings == {"rate_limit": 100}

    def test_from_dict_with_missing_keys(self) -> None:
        """from_dict uses defaults for missing keys."""
        data = {"max_robots": 5}

        settings = TenantSettings.from_dict(data)

        assert settings.max_robots == 5
        assert settings.max_concurrent_jobs == 20  # default
        assert settings.allowed_capabilities == []  # default

    def test_from_dict_with_empty_dict(self) -> None:
        """from_dict creates default settings from empty dict."""
        settings = TenantSettings.from_dict({})

        assert settings.max_robots == 10
        assert settings.max_concurrent_jobs == 20

    def test_round_trip_serialization(self) -> None:
        """to_dict -> from_dict preserves all values."""
        original = TenantSettings(
            max_robots=42,
            max_concurrent_jobs=84,
            allowed_capabilities=["browser", "desktop", "gpu"],
            max_api_keys_per_robot=7,
            job_retention_days=365,
            enable_audit_logging=False,
            custom_settings={"nested": {"key": "value"}},
        )

        reconstructed = TenantSettings.from_dict(original.to_dict())

        assert reconstructed.max_robots == original.max_robots
        assert reconstructed.max_concurrent_jobs == original.max_concurrent_jobs
        assert reconstructed.allowed_capabilities == original.allowed_capabilities
        assert reconstructed.max_api_keys_per_robot == original.max_api_keys_per_robot
        assert reconstructed.job_retention_days == original.job_retention_days
        assert reconstructed.enable_audit_logging == original.enable_audit_logging
        assert reconstructed.custom_settings == original.custom_settings


class TestTenant:
    """Tests for Tenant domain entity."""

    def test_create_with_valid_data(self) -> None:
        """Tenant created with minimal required data."""
        tenant = Tenant(
            id=TenantId("tenant-1"),
            name="Test Tenant",
        )

        assert str(tenant.id) == "tenant-1"
        assert tenant.name == "Test Tenant"
        assert tenant.is_active is True
        assert tenant.description == ""
        assert tenant.robot_count == 0

    def test_create_with_all_fields(self) -> None:
        """Tenant created with all fields."""
        settings = TenantSettings(max_robots=5)
        now = datetime.now(timezone.utc)

        tenant = Tenant(
            id=TenantId("tenant-full"),
            name="Full Tenant",
            settings=settings,
            admin_emails=["admin@example.com"],
            created_at=now,
            is_active=True,
            description="Test description",
            contact_email="contact@example.com",
            robot_ids={"robot-1", "robot-2"},
        )

        assert tenant.name == "Full Tenant"
        assert tenant.settings.max_robots == 5
        assert tenant.admin_emails == ["admin@example.com"]
        assert tenant.description == "Test description"
        assert tenant.contact_email == "contact@example.com"
        assert tenant.robot_count == 2

    def test_create_with_string_id_converts_to_tenant_id(self) -> None:
        """String ID is converted to TenantId."""
        tenant = Tenant(
            id="string-id",  # type: ignore
            name="Test",
        )
        assert isinstance(tenant.id, TenantId)
        assert str(tenant.id) == "string-id"

    def test_empty_name_raises_error(self) -> None:
        """Empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Tenant(id=TenantId("t1"), name="")

    def test_whitespace_name_raises_error(self) -> None:
        """Whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Tenant(id=TenantId("t1"), name="   ")

    def test_created_at_defaults_to_now(self) -> None:
        """created_at defaults to current UTC time."""
        before = datetime.now(timezone.utc)
        tenant = Tenant(id=TenantId("t1"), name="Test")
        after = datetime.now(timezone.utc)

        assert before <= tenant.created_at <= after

    def test_robot_count_property(self) -> None:
        """robot_count returns number of robots."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            robot_ids={"r1", "r2", "r3"},
        )
        assert tenant.robot_count == 3

    def test_can_add_robot_when_under_limit(self) -> None:
        """can_add_robot returns True when under limit."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=5),
            robot_ids={"r1", "r2"},
        )
        assert tenant.can_add_robot is True

    def test_can_add_robot_when_at_limit(self) -> None:
        """can_add_robot returns False when at limit."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=2),
            robot_ids={"r1", "r2"},
        )
        assert tenant.can_add_robot is False

    def test_add_robot_success(self) -> None:
        """add_robot adds robot ID to set."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=5),
        )

        tenant.add_robot("robot-new")

        assert "robot-new" in tenant.robot_ids
        assert tenant.robot_count == 1

    def test_add_robot_updates_timestamp(self) -> None:
        """add_robot updates updated_at timestamp."""
        tenant = Tenant(id=TenantId("t1"), name="Test")
        original_updated = tenant.updated_at

        tenant.add_robot("robot-1")

        assert tenant.updated_at is not None
        if original_updated is not None:
            assert tenant.updated_at > original_updated

    def test_add_robot_when_at_capacity_raises_error(self) -> None:
        """add_robot raises ValueError when at capacity."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=1),
            robot_ids={"r1"},
        )

        with pytest.raises(ValueError, match="reached max robots"):
            tenant.add_robot("r2")

    def test_add_robot_idempotent(self) -> None:
        """Adding same robot twice doesn't duplicate."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=5),
        )

        tenant.add_robot("robot-1")
        tenant.add_robot("robot-1")

        assert tenant.robot_count == 1

    def test_remove_robot_success(self) -> None:
        """remove_robot removes robot from set."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            robot_ids={"r1", "r2"},
        )

        tenant.remove_robot("r1")

        assert "r1" not in tenant.robot_ids
        assert "r2" in tenant.robot_ids
        assert tenant.robot_count == 1

    def test_remove_robot_updates_timestamp(self) -> None:
        """remove_robot updates updated_at timestamp."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            robot_ids={"r1"},
        )
        original_updated = tenant.updated_at

        tenant.remove_robot("r1")

        assert tenant.updated_at is not None
        if original_updated is not None:
            assert tenant.updated_at > original_updated

    def test_remove_nonexistent_robot_no_error(self) -> None:
        """Removing nonexistent robot doesn't raise error."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            robot_ids={"r1"},
        )

        tenant.remove_robot("nonexistent")  # No error

        assert tenant.robot_count == 1

    def test_has_robot_true(self) -> None:
        """has_robot returns True for existing robot."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            robot_ids={"r1", "r2"},
        )
        assert tenant.has_robot("r1") is True

    def test_has_robot_false(self) -> None:
        """has_robot returns False for nonexistent robot."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            robot_ids={"r1"},
        )
        assert tenant.has_robot("r2") is False

    def test_add_admin_success(self) -> None:
        """add_admin adds email to admin list."""
        tenant = Tenant(id=TenantId("t1"), name="Test")

        tenant.add_admin("admin@example.com")

        assert "admin@example.com" in tenant.admin_emails

    def test_add_admin_normalizes_email(self) -> None:
        """add_admin normalizes email to lowercase and strips whitespace."""
        tenant = Tenant(id=TenantId("t1"), name="Test")

        tenant.add_admin("  ADMIN@Example.COM  ")

        assert "admin@example.com" in tenant.admin_emails
        assert "  ADMIN@Example.COM  " not in tenant.admin_emails

    def test_add_admin_updates_timestamp(self) -> None:
        """add_admin updates updated_at timestamp."""
        tenant = Tenant(id=TenantId("t1"), name="Test")

        tenant.add_admin("admin@example.com")

        assert tenant.updated_at is not None

    def test_add_admin_no_duplicates(self) -> None:
        """add_admin doesn't add duplicate emails."""
        tenant = Tenant(id=TenantId("t1"), name="Test")

        tenant.add_admin("admin@example.com")
        tenant.add_admin("admin@example.com")
        tenant.add_admin("ADMIN@example.com")  # Different case

        assert len(tenant.admin_emails) == 1

    def test_add_empty_admin_ignored(self) -> None:
        """Empty email string is ignored."""
        tenant = Tenant(id=TenantId("t1"), name="Test")

        tenant.add_admin("")
        tenant.add_admin("   ")

        assert len(tenant.admin_emails) == 0

    def test_remove_admin_success(self) -> None:
        """remove_admin removes email from list."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            admin_emails=["admin@example.com", "other@example.com"],
        )

        tenant.remove_admin("admin@example.com")

        assert "admin@example.com" not in tenant.admin_emails
        assert "other@example.com" in tenant.admin_emails

    def test_remove_admin_normalizes_email(self) -> None:
        """remove_admin normalizes email for comparison."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            admin_emails=["admin@example.com"],
        )

        tenant.remove_admin("  ADMIN@Example.COM  ")

        assert len(tenant.admin_emails) == 0

    def test_remove_admin_updates_timestamp(self) -> None:
        """remove_admin updates updated_at timestamp."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            admin_emails=["admin@example.com"],
        )

        tenant.remove_admin("admin@example.com")

        assert tenant.updated_at is not None

    def test_is_admin_true(self) -> None:
        """is_admin returns True for existing admin."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            admin_emails=["admin@example.com"],
        )
        assert tenant.is_admin("admin@example.com") is True

    def test_is_admin_normalizes_email(self) -> None:
        """is_admin normalizes email for comparison."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            admin_emails=["admin@example.com"],
        )
        assert tenant.is_admin("  ADMIN@Example.COM  ") is True

    def test_is_admin_false(self) -> None:
        """is_admin returns False for non-admin."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            admin_emails=["admin@example.com"],
        )
        assert tenant.is_admin("other@example.com") is False

    def test_deactivate(self) -> None:
        """deactivate sets is_active to False."""
        tenant = Tenant(id=TenantId("t1"), name="Test", is_active=True)

        tenant.deactivate()

        assert tenant.is_active is False
        assert tenant.updated_at is not None

    def test_activate(self) -> None:
        """activate sets is_active to True."""
        tenant = Tenant(id=TenantId("t1"), name="Test", is_active=False)

        tenant.activate()

        assert tenant.is_active is True
        assert tenant.updated_at is not None

    def test_update_settings(self) -> None:
        """update_settings replaces settings."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=5),
        )
        new_settings = TenantSettings(max_robots=20)

        tenant.update_settings(new_settings)

        assert tenant.settings.max_robots == 20
        assert tenant.updated_at is not None

    def test_to_dict_serialization(self) -> None:
        """to_dict returns complete dictionary."""
        tenant = Tenant(
            id=TenantId("tenant-123"),
            name="Test Tenant",
            description="A test tenant",
            settings=TenantSettings(max_robots=15),
            admin_emails=["admin@test.com"],
            contact_email="contact@test.com",
            robot_ids={"r1", "r2"},
            is_active=True,
        )

        result = tenant.to_dict()

        assert result["id"] == "tenant-123"
        assert result["name"] == "Test Tenant"
        assert result["description"] == "A test tenant"
        assert result["settings"]["max_robots"] == 15
        assert result["admin_emails"] == ["admin@test.com"]
        assert result["contact_email"] == "contact@test.com"
        assert set(result["robot_ids"]) == {"r1", "r2"}
        assert result["robot_count"] == 2
        assert result["is_active"] is True
        assert result["created_at"] is not None

    def test_from_dict_deserialization(self) -> None:
        """from_dict creates Tenant from dictionary."""
        data = {
            "id": "tenant-from-dict",
            "name": "Deserialized Tenant",
            "description": "From dict",
            "settings": {"max_robots": 25},
            "admin_emails": ["admin@test.com"],
            "contact_email": "contact@test.com",
            "robot_ids": ["r1", "r2", "r3"],
            "is_active": False,
            "created_at": "2024-01-01T00:00:00Z",
        }

        tenant = Tenant.from_dict(data)

        assert str(tenant.id) == "tenant-from-dict"
        assert tenant.name == "Deserialized Tenant"
        assert tenant.description == "From dict"
        assert tenant.settings.max_robots == 25
        assert tenant.admin_emails == ["admin@test.com"]
        assert tenant.contact_email == "contact@test.com"
        assert tenant.robot_ids == {"r1", "r2", "r3"}
        assert tenant.is_active is False

    def test_round_trip_serialization(self) -> None:
        """to_dict -> from_dict preserves entity state."""
        original = Tenant(
            id=TenantId("round-trip-test"),
            name="Round Trip Tenant",
            description="Testing serialization",
            settings=TenantSettings(
                max_robots=42,
                allowed_capabilities=["browser", "desktop"],
            ),
            admin_emails=["admin1@test.com", "admin2@test.com"],
            contact_email="contact@test.com",
            robot_ids={"robot-a", "robot-b"},
            is_active=True,
        )

        reconstructed = Tenant.from_dict(original.to_dict())

        assert str(reconstructed.id) == str(original.id)
        assert reconstructed.name == original.name
        assert reconstructed.description == original.description
        assert reconstructed.settings.max_robots == original.settings.max_robots
        assert reconstructed.admin_emails == original.admin_emails
        assert reconstructed.contact_email == original.contact_email
        assert reconstructed.robot_ids == original.robot_ids
        assert reconstructed.is_active == original.is_active

    def test_repr(self) -> None:
        """__repr__ returns informative string."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test Tenant",
            robot_ids={"r1", "r2"},
        )

        repr_str = repr(tenant)

        assert "Tenant" in repr_str
        assert "t1" in repr_str
        assert "Test Tenant" in repr_str
        assert "2" in repr_str  # robot count


class TestTenantBusinessRules:
    """Tests for Tenant business rules and edge cases."""

    def test_tenant_cannot_exceed_robot_limit(self) -> None:
        """Tenant enforces robot limit."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=2),
        )

        tenant.add_robot("r1")
        tenant.add_robot("r2")

        with pytest.raises(ValueError):
            tenant.add_robot("r3")

    def test_deactivated_tenant_keeps_robots(self) -> None:
        """Deactivating tenant doesn't remove robots."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            robot_ids={"r1", "r2"},
        )

        tenant.deactivate()

        assert tenant.robot_count == 2
        assert tenant.is_active is False

    def test_tenant_with_zero_max_robots(self) -> None:
        """Tenant with max_robots=0 cannot add any robots."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=0),
        )

        assert tenant.can_add_robot is False
        with pytest.raises(ValueError):
            tenant.add_robot("r1")

    def test_multiple_admins(self) -> None:
        """Tenant supports multiple admins."""
        tenant = Tenant(id=TenantId("t1"), name="Test")

        tenant.add_admin("admin1@test.com")
        tenant.add_admin("admin2@test.com")
        tenant.add_admin("admin3@test.com")

        assert len(tenant.admin_emails) == 3
        assert tenant.is_admin("admin1@test.com")
        assert tenant.is_admin("admin2@test.com")
        assert tenant.is_admin("admin3@test.com")

    def test_settings_update_doesnt_affect_robots(self) -> None:
        """Updating settings doesn't affect existing robots."""
        tenant = Tenant(
            id=TenantId("t1"),
            name="Test",
            settings=TenantSettings(max_robots=5),
            robot_ids={"r1", "r2", "r3"},
        )

        # Reduce limit below current count
        tenant.update_settings(TenantSettings(max_robots=2))

        # Existing robots are preserved
        assert tenant.robot_count == 3
        # But can't add more
        assert tenant.can_add_robot is False

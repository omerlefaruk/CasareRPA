from __future__ import annotations

from pathlib import Path

from casare_rpa.robot.identity_store import RobotIdentityStore


<<<<<<< HEAD
def test_identity_store_resolve_creates_and_persists(
    tmp_path: Path, monkeypatch
) -> None:
=======
def test_identity_store_resolve_creates_and_persists(tmp_path: Path, monkeypatch) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
    identity_path = tmp_path / "robot_identity.json"
    monkeypatch.setenv("CASARE_ROBOT_IDENTITY_PATH", str(identity_path))

    store = RobotIdentityStore()
    identity1 = store.resolve(hostname="test-host")
    assert identity_path.exists()
    assert identity1.worker_robot_id
    assert identity1.worker_robot_name
    assert identity1.fleet_robot_id == identity1.worker_robot_id
    assert identity1.fleet_robot_name == identity1.worker_robot_name
    assert identity1.fleet_linked is True

    identity2 = store.resolve(hostname="test-host")
    assert identity2.worker_robot_id == identity1.worker_robot_id
    assert identity2.worker_robot_name == identity1.worker_robot_name


def test_identity_store_overrides_worker_identity(tmp_path: Path, monkeypatch) -> None:
    identity_path = tmp_path / "robot_identity.json"
    monkeypatch.setenv("CASARE_ROBOT_IDENTITY_PATH", str(identity_path))

    store = RobotIdentityStore()
    identity1 = store.resolve(hostname="test-host")
    identity2 = store.resolve(
        worker_robot_id="robot-fixed",
        worker_robot_name="Fixed Robot",
        hostname="test-host",
    )
    assert identity2.worker_robot_id == "robot-fixed"
    assert identity2.worker_robot_name == "Fixed Robot"

    identity3 = store.load()
    assert identity3 is not None
    assert identity3.worker_robot_id == "robot-fixed"
    assert identity3.worker_robot_name == "Fixed Robot"


def test_identity_store_backward_compatible_missing_fleet_fields(
    tmp_path: Path, monkeypatch
) -> None:
    identity_path = tmp_path / "robot_identity.json"
    monkeypatch.setenv("CASARE_ROBOT_IDENTITY_PATH", str(identity_path))

    identity_path.write_text(
        """
{
  "worker_robot_id": "worker-1",
  "worker_robot_name": "Worker One"
}
""".strip(),
        encoding="utf-8",
    )

    store = RobotIdentityStore()
    identity = store.load()
    assert identity is not None
    assert identity.fleet_robot_id == "worker-1"
    assert identity.fleet_robot_name == "Worker One"
    assert identity.fleet_linked is True

"""
Robot identity persistence for stable Fleet registration.

Stores a local worker identity plus an optional Fleet link identity in %APPDATA%/CasareRPA.
"""

from __future__ import annotations

import os
import socket
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import orjson
from loguru import logger


def _default_identity_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home()
    return base / "CasareRPA" / "robot_identity.json"


@dataclass(frozen=True)
class RobotIdentity:
    worker_robot_id: str
    worker_robot_name: str
    fleet_robot_id: str
    fleet_robot_name: str
    fleet_linked: bool
    fleet_ever_registered: bool
    fleet_unlinked_reason: Optional[str]
    fleet_unlinked_at_utc: Optional[str]
    updated_at_utc: str

    @staticmethod
    def now_utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "worker_robot_id": self.worker_robot_id,
            "worker_robot_name": self.worker_robot_name,
            "fleet_robot_id": self.fleet_robot_id,
            "fleet_robot_name": self.fleet_robot_name,
            "fleet_linked": self.fleet_linked,
            "fleet_ever_registered": self.fleet_ever_registered,
            "fleet_unlinked_reason": self.fleet_unlinked_reason,
            "fleet_unlinked_at_utc": self.fleet_unlinked_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, Any]) -> "RobotIdentity":
        return cls(
            worker_robot_id=str(data["worker_robot_id"]),
            worker_robot_name=str(data["worker_robot_name"]),
            fleet_robot_id=str(data.get("fleet_robot_id") or data["worker_robot_id"]),
            fleet_robot_name=str(
                data.get("fleet_robot_name") or data["worker_robot_name"]
            ),
            fleet_linked=bool(data.get("fleet_linked", True)),
            fleet_ever_registered=bool(data.get("fleet_ever_registered", False)),
            fleet_unlinked_reason=(
                str(data["fleet_unlinked_reason"])
                if data.get("fleet_unlinked_reason") is not None
                else None
            ),
            fleet_unlinked_at_utc=(
                str(data["fleet_unlinked_at_utc"])
                if data.get("fleet_unlinked_at_utc") is not None
                else None
            ),
            updated_at_utc=str(data.get("updated_at_utc") or cls.now_utc_iso()),
        )


class RobotIdentityStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        override = os.getenv("CASARE_ROBOT_IDENTITY_PATH")
        self._path = Path(override) if override else (path or _default_identity_path())

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Optional[RobotIdentity]:
        try:
            if not self._path.exists():
                return None
            data = orjson.loads(self._path.read_bytes())
            if not isinstance(data, dict):
                logger.warning(f"Invalid robot identity file format: {self._path}")
                return None
            return RobotIdentity.from_json_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load robot identity from {self._path}: {e}")
            return None

    def save(self, identity: RobotIdentity) -> bool:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload = orjson.dumps(identity.to_json_dict(), option=orjson.OPT_INDENT_2)
            self._path.write_bytes(payload)
            return True
        except Exception as e:
            logger.error(f"Failed to save robot identity to {self._path}: {e}")
            return False

    def resolve(
        self,
        *,
        worker_robot_id: Optional[str] = None,
        worker_robot_name: Optional[str] = None,
        hostname: Optional[str] = None,
    ) -> RobotIdentity:
        """
        Load the identity if present, otherwise create it and persist it.

        Precedence:
        - If `worker_robot_id`/`worker_robot_name` are provided, they override stored values.
        - Fleet identity defaults to worker identity on first creation.
        """
        existing = self.load()
        if existing is None:
            resolved_hostname = hostname or socket.gethostname()
            new_worker_id = (
                worker_robot_id or f"robot-{resolved_hostname}-{uuid.uuid4().hex[:8]}"
            )
            new_worker_name = worker_robot_name or f"Robot-{resolved_hostname}"
            identity = RobotIdentity(
                worker_robot_id=new_worker_id,
                worker_robot_name=new_worker_name,
                fleet_robot_id=new_worker_id,
                fleet_robot_name=new_worker_name,
                fleet_linked=True,
                fleet_ever_registered=False,
                fleet_unlinked_reason=None,
                fleet_unlinked_at_utc=None,
                updated_at_utc=RobotIdentity.now_utc_iso(),
            )
            self.save(identity)
            return identity

        updated = existing
        if worker_robot_id and worker_robot_id != existing.worker_robot_id:
            updated = replace(updated, worker_robot_id=worker_robot_id)
            # If fleet identity was still tracking the worker identity, keep it in sync.
            if existing.fleet_robot_id == existing.worker_robot_id:
                updated = replace(updated, fleet_robot_id=worker_robot_id)
        if worker_robot_name and worker_robot_name != existing.worker_robot_name:
            updated = replace(updated, worker_robot_name=worker_robot_name)
            if existing.fleet_robot_name == existing.worker_robot_name:
                updated = replace(updated, fleet_robot_name=worker_robot_name)

        # Ensure required Fleet fields exist (backward compatible with older files).
        if not updated.fleet_robot_id:
            updated = replace(updated, fleet_robot_id=updated.worker_robot_id)
        if not updated.fleet_robot_name:
            updated = replace(updated, fleet_robot_name=updated.worker_robot_name)

        if updated is not existing:
            updated = replace(updated, updated_at_utc=RobotIdentity.now_utc_iso())
            self.save(updated)
        return updated

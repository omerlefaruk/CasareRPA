"""
Multi-account manager for Antigravity OAuth with load balancing and rate limiting.

Supports sticky account selection with automatic failover on rate limits.
Tracks rate limits per model family (Claude/Gemini) with dual quota pools for Gemini.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from casare_rpa.infrastructure.security.antigravity_constants import (
    HeaderStyle,
    ModelFamily,
    QuotaKey,
    get_quota_key,
)
from casare_rpa.infrastructure.security.antigravity_oauth import (
    format_refresh_parts,
    parse_refresh_parts,
)
from casare_rpa.infrastructure.security.antigravity_token import (
    AntigravityAuthDetails,
    refresh_antigravity_token,
)

if TYPE_CHECKING:
    pass


def _now_ms() -> int:
    return int(time.time() * 1000)


def _get_accounts_file_path() -> Path:
    import os
    import platform

    if platform.system() == "Windows":
        app_data = os.environ.get("APPDATA", "")
        if app_data:
            return Path(app_data) / "casare-rpa" / "antigravity-accounts.json"
    config_dir = Path.home() / ".config" / "casare-rpa"
    return config_dir / "antigravity-accounts.json"


@dataclass
class RateLimitState:
    claude: int | None = None
    gemini_antigravity: int | None = None
    gemini_cli: int | None = None

    def get(self, key: QuotaKey) -> int | None:
        if key == QuotaKey.CLAUDE:
            return self.claude
        elif key == QuotaKey.GEMINI_ANTIGRAVITY:
            return self.gemini_antigravity
        return self.gemini_cli

    def set(self, key: QuotaKey, value: int | None) -> None:
        if key == QuotaKey.CLAUDE:
            self.claude = value
        elif key == QuotaKey.GEMINI_ANTIGRAVITY:
            self.gemini_antigravity = value
        else:
            self.gemini_cli = value

    def to_dict(self) -> dict[str, int]:
        result = {}
        if self.claude is not None:
            result["claude"] = self.claude
        if self.gemini_antigravity is not None:
            result["gemini-antigravity"] = self.gemini_antigravity
        if self.gemini_cli is not None:
            result["gemini-cli"] = self.gemini_cli
        return result

    @classmethod
    def from_dict(cls, data: dict[str, int] | None) -> RateLimitState:
        if not data:
            return cls()
        return cls(
            claude=data.get("claude"),
            gemini_antigravity=data.get("gemini-antigravity"),
            gemini_cli=data.get("gemini-cli"),
        )


@dataclass
class ManagedAccount:
    index: int
    email: str | None
    added_at: int
    last_used: int
    refresh_token: str
    project_id: str
    managed_project_id: str | None = None
    access_token: str | None = None
    expires_at: int | None = None
    rate_limit_state: RateLimitState = field(default_factory=RateLimitState)
    last_switch_reason: str | None = None

    def to_auth_details(self) -> AntigravityAuthDetails:
        return AntigravityAuthDetails(
            refresh_token=format_refresh_parts(
                self.refresh_token,
                self.project_id,
                self.managed_project_id,
            ),
            access_token=self.access_token,
            expires_at=self.expires_at,
        )

    def update_from_auth(self, auth: AntigravityAuthDetails) -> None:
        token, project_id, managed_project_id = parse_refresh_parts(auth.refresh_token)
        self.refresh_token = token
        self.project_id = project_id
        self.managed_project_id = managed_project_id
        self.access_token = auth.access_token
        self.expires_at = auth.expires_at


def _is_rate_limited_for_quota_key(account: ManagedAccount, key: QuotaKey) -> bool:
    reset_time = account.rate_limit_state.get(key)
    return reset_time is not None and _now_ms() < reset_time


def _is_rate_limited_for_family(account: ManagedAccount, family: ModelFamily) -> bool:
    if family == ModelFamily.CLAUDE:
        return _is_rate_limited_for_quota_key(account, QuotaKey.CLAUDE)
    return _is_rate_limited_for_quota_key(
        account, QuotaKey.GEMINI_ANTIGRAVITY
    ) and _is_rate_limited_for_quota_key(account, QuotaKey.GEMINI_CLI)


def _clear_expired_rate_limits(account: ManagedAccount) -> None:
    now = _now_ms()
    for key in QuotaKey:
        reset_time = account.rate_limit_state.get(key)
        if reset_time is not None and now >= reset_time:
            account.rate_limit_state.set(key, None)


class AntigravityAccountManager:
    def __init__(self) -> None:
        self._accounts: list[ManagedAccount] = []
        self._cursor: int = 0
        self._current_index_by_family: dict[ModelFamily, int] = {
            ModelFamily.CLAUDE: -1,
            ModelFamily.GEMINI: -1,
        }
        self._last_toast_index: int = -1
        self._last_toast_time: int = 0

    @classmethod
    async def load_from_disk(cls) -> AntigravityAccountManager:
        manager = cls()
        await manager._load()
        return manager

    async def _load(self) -> None:
        path = _get_accounts_file_path()
        if not path.exists():
            return

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            version = data.get("version", 1)
            if version < 3:
                await self._migrate_storage(data, version)
                return

            accounts_data = data.get("accounts", [])
            for idx, acc in enumerate(accounts_data):
                if not acc.get("refreshToken"):
                    continue
                self._accounts.append(
                    ManagedAccount(
                        index=idx,
                        email=acc.get("email"),
                        added_at=acc.get("addedAt", _now_ms()),
                        last_used=acc.get("lastUsed", 0),
                        refresh_token=acc["refreshToken"],
                        project_id=acc.get("projectId", ""),
                        managed_project_id=acc.get("managedProjectId"),
                        rate_limit_state=RateLimitState.from_dict(acc.get("rateLimitResetTimes")),
                        last_switch_reason=acc.get("lastSwitchReason"),
                    )
                )

            self._cursor = data.get("activeIndex", 0)
            if self._accounts:
                self._cursor = self._cursor % len(self._accounts)
                family_indices = data.get("activeIndexByFamily", {})
                self._current_index_by_family[ModelFamily.CLAUDE] = family_indices.get(
                    "claude", self._cursor
                ) % len(self._accounts)
                self._current_index_by_family[ModelFamily.GEMINI] = family_indices.get(
                    "gemini", self._cursor
                ) % len(self._accounts)

        except Exception as e:
            logger.error(f"Failed to load Antigravity accounts: {e}")

    async def _migrate_storage(self, data: dict, version: int) -> None:
        logger.info(f"Migrating Antigravity account storage from v{version} to v3")
        await self.save_to_disk()

    async def save_to_disk(self) -> None:
        path = _get_accounts_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        claude_index = max(0, self._current_index_by_family.get(ModelFamily.CLAUDE, 0))
        gemini_index = max(0, self._current_index_by_family.get(ModelFamily.GEMINI, 0))

        storage = {
            "version": 3,
            "accounts": [
                {
                    "email": acc.email,
                    "refreshToken": acc.refresh_token,
                    "projectId": acc.project_id,
                    "managedProjectId": acc.managed_project_id,
                    "addedAt": acc.added_at,
                    "lastUsed": acc.last_used,
                    "lastSwitchReason": acc.last_switch_reason,
                    "rateLimitResetTimes": acc.rate_limit_state.to_dict() or None,
                }
                for acc in self._accounts
            ],
            "activeIndex": claude_index,
            "activeIndexByFamily": {
                "claude": claude_index,
                "gemini": gemini_index,
            },
        }

        path.write_text(json.dumps(storage, indent=2), encoding="utf-8")

    def get_account_count(self) -> int:
        return len(self._accounts)

    def get_accounts(self) -> list[ManagedAccount]:
        return list(self._accounts)

    def add_account(
        self,
        refresh_token: str,
        project_id: str,
        email: str | None = None,
        access_token: str | None = None,
        expires_at: int | None = None,
    ) -> ManagedAccount:
        now = _now_ms()
        account = ManagedAccount(
            index=len(self._accounts),
            email=email,
            added_at=now,
            last_used=0,
            refresh_token=refresh_token,
            project_id=project_id,
            access_token=access_token,
            expires_at=expires_at,
        )
        self._accounts.append(account)

        if len(self._accounts) == 1:
            self._current_index_by_family[ModelFamily.CLAUDE] = 0
            self._current_index_by_family[ModelFamily.GEMINI] = 0

        return account

    def remove_account(self, account: ManagedAccount) -> bool:
        if account not in self._accounts:
            return False

        idx = self._accounts.index(account)
        self._accounts.remove(account)

        for i, acc in enumerate(self._accounts):
            acc.index = i

        if not self._accounts:
            self._cursor = 0
            self._current_index_by_family[ModelFamily.CLAUDE] = -1
            self._current_index_by_family[ModelFamily.GEMINI] = -1
            return True

        if self._cursor > idx:
            self._cursor -= 1
        self._cursor = self._cursor % len(self._accounts)

        for family in ModelFamily:
            current = self._current_index_by_family.get(family, -1)
            if current > idx:
                self._current_index_by_family[family] = current - 1
            if self._current_index_by_family.get(family, -1) >= len(self._accounts):
                self._current_index_by_family[family] = -1

        return True

    def get_current_for_family(self, family: ModelFamily) -> ManagedAccount | None:
        current_index = self._current_index_by_family.get(family, -1)
        if 0 <= current_index < len(self._accounts):
            return self._accounts[current_index]
        return None

    def get_current_or_next_for_family(self, family: ModelFamily) -> ManagedAccount | None:
        current = self.get_current_for_family(family)
        if current:
            _clear_expired_rate_limits(current)
            if not _is_rate_limited_for_family(current, family):
                current.last_used = _now_ms()
                return current

        next_account = self._get_next_for_family(family)
        if next_account:
            self._current_index_by_family[family] = next_account.index
        return next_account

    def _get_next_for_family(self, family: ModelFamily) -> ManagedAccount | None:
        available = []
        for acc in self._accounts:
            _clear_expired_rate_limits(acc)
            if not _is_rate_limited_for_family(acc, family):
                available.append(acc)

        if not available:
            return None

        account = available[self._cursor % len(available)]
        self._cursor += 1
        account.last_used = _now_ms()
        return account

    def mark_rate_limited(
        self,
        account: ManagedAccount,
        retry_after_ms: int,
        family: ModelFamily,
        header_style: HeaderStyle = HeaderStyle.ANTIGRAVITY,
    ) -> None:
        key = get_quota_key(family, header_style)
        account.rate_limit_state.set(key, _now_ms() + retry_after_ms)

    def is_rate_limited_for_style(
        self, account: ManagedAccount, family: ModelFamily, header_style: HeaderStyle
    ) -> bool:
        _clear_expired_rate_limits(account)
        key = get_quota_key(family, header_style)
        return _is_rate_limited_for_quota_key(account, key)

    def get_available_header_style(
        self, account: ManagedAccount, family: ModelFamily
    ) -> HeaderStyle | None:
        _clear_expired_rate_limits(account)
        if family == ModelFamily.CLAUDE:
            if not _is_rate_limited_for_quota_key(account, QuotaKey.CLAUDE):
                return HeaderStyle.ANTIGRAVITY
            return None
        if not _is_rate_limited_for_quota_key(account, QuotaKey.GEMINI_ANTIGRAVITY):
            return HeaderStyle.ANTIGRAVITY
        if not _is_rate_limited_for_quota_key(account, QuotaKey.GEMINI_CLI):
            return HeaderStyle.GEMINI_CLI
        return None

    def get_min_wait_time_for_family(self, family: ModelFamily) -> int:
        available = [acc for acc in self._accounts if not _is_rate_limited_for_family(acc, family)]
        if available:
            return 0

        wait_times: list[int] = []
        now = _now_ms()

        for acc in self._accounts:
            if family == ModelFamily.CLAUDE:
                reset = acc.rate_limit_state.claude
                if reset is not None:
                    wait_times.append(max(0, reset - now))
            else:
                t1 = acc.rate_limit_state.gemini_antigravity
                t2 = acc.rate_limit_state.gemini_cli
                account_wait = min(
                    max(0, t1 - now) if t1 is not None else float("inf"),
                    max(0, t2 - now) if t2 is not None else float("inf"),
                )
                if account_wait != float("inf"):
                    wait_times.append(int(account_wait))

        return min(wait_times) if wait_times else 0

    async def ensure_valid_token(self, account: ManagedAccount) -> ManagedAccount:
        auth = account.to_auth_details()
        if not auth.is_expired and auth.access_token:
            return account

        refreshed = await refresh_antigravity_token(auth)
        if refreshed:
            account.update_from_auth(refreshed)
            await self.save_to_disk()
        return account

    def should_show_account_toast(self, account_index: int, debounce_ms: int = 30000) -> bool:
        now = _now_ms()
        if account_index == self._last_toast_index and now - self._last_toast_time < debounce_ms:
            return False
        return True

    def mark_toast_shown(self, account_index: int) -> None:
        self._last_toast_index = account_index
        self._last_toast_time = _now_ms()


_account_manager: AntigravityAccountManager | None = None


async def get_antigravity_account_manager() -> AntigravityAccountManager:
    global _account_manager
    if _account_manager is None:
        _account_manager = await AntigravityAccountManager.load_from_disk()
    return _account_manager


__all__ = [
    "RateLimitState",
    "ManagedAccount",
    "AntigravityAccountManager",
    "get_antigravity_account_manager",
]

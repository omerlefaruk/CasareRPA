import hashlib

import pytest

from casare_rpa.infrastructure.orchestrator.api.auth import RobotAuthenticator


class _AcquireConn:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireConn(self._conn)


class _FakeConnection:
    def __init__(self, *, token_hash: str, robot_id: str):
        self._token_hash = token_hash
        self._robot_id = robot_id
        self.fetch_calls: list[tuple[str, tuple]] = []
        self.fetchrow_calls: list[tuple[str, tuple]] = []
        self.execute_calls: list[tuple[str, tuple]] = []

    async def fetch(self, query: str, *params):
        self.fetch_calls.append((query, params))
        if "information_schema.columns" in query:
            return [
                {"column_name": "api_key_hash"},
                {"column_name": "robot_id"},
                {"column_name": "is_revoked"},
                {"column_name": "expires_at"},
                {"column_name": "last_used_at"},
                {"column_name": "last_used_ip"},
            ]
        return []

    async def fetchrow(self, query: str, *params):
        self.fetchrow_calls.append((query, params))
        if "FROM robot_api_keys" in query and params and params[0] == self._token_hash:
            return {"robot_id": self._robot_id}
        return None

    async def execute(self, query: str, *params):
        self.execute_calls.append((query, params))
        return "UPDATE 1"


@pytest.mark.asyncio
async def test_verify_token_async_validates_and_updates_last_used():
    token = "crpa_" + ("a" * 40)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    conn = _FakeConnection(token_hash=token_hash, robot_id="robot-123")
    auth = RobotAuthenticator(use_database=True, db_pool=_FakePool(conn))

    robot_id = await auth.verify_token_async(token, client_ip="1.2.3.4")

    assert robot_id == "robot-123"
    assert any("information_schema.columns" in q for (q, _) in conn.fetch_calls)
    assert any("UPDATE robot_api_keys" in q for (q, _) in conn.execute_calls)


@pytest.mark.asyncio
async def test_verify_token_async_rejects_invalid_format_without_db_access():
    class _ExplodingPool:
        def acquire(self):
<<<<<<< HEAD
            raise AssertionError(
                "Database should not be queried for invalid key format"
            )
=======
            raise AssertionError("Database should not be queried for invalid key format")
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

    auth = RobotAuthenticator(use_database=True, db_pool=_ExplodingPool())

    robot_id = await auth.verify_token_async("not_a_key")

    assert robot_id is None

import os
import stat

import pytest
from starlette.testclient import TestClient

from superuser.bridge import BearerAuthMiddleware, build_bridge_app, load_or_create_token

TOKEN = "test-token-abc123"


async def _ok_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


@pytest.fixture
def client():
    return TestClient(BearerAuthMiddleware(_ok_app, TOKEN))


def test_missing_token_rejected(client):
    r = client.get("/mcp")
    assert r.status_code == 401
    assert TOKEN not in r.text


def test_wrong_token_rejected(client):
    assert client.get("/mcp", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.get("/mcp", headers={"Authorization": f"Basic {TOKEN}"}).status_code == 401


def test_right_token_accepted(client):
    r = client.get("/mcp", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200 and r.text == "ok"


def test_token_file_created_0600_and_stable(tmp_path):
    p = tmp_path / "sub" / "token"
    t1 = load_or_create_token(p)
    assert len(t1) >= 32
    if os.name == "posix":
        assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert load_or_create_token(p) == t1


def test_real_mcp_app_requires_token(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_DEFENSE_ENABLED", "false")
    monkeypatch.chdir(tmp_path)
    from superuser.config import Config
    from superuser.server import build_server

    app = build_bridge_app(build_server(Config.load(None)), TOKEN)
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "t", "version": "0"}}}
    hdrs = {"Accept": "application/json, text/event-stream"}
    with TestClient(app) as c:
        assert c.post("/mcp", json=init, headers=hdrs).status_code == 401
        r = c.post("/mcp", json=init, headers={**hdrs, "Authorization": f"Bearer {TOKEN}"})
        assert r.status_code == 200

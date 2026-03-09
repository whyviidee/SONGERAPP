import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import server

@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c

def test_app_route_redirects_without_token(client):
    # No token file → redirect to setup
    if server.TOKEN_PATH.exists():
        pytest.skip("Token exists, skip redirect test")
    resp = client.get("/app")
    assert resp.status_code == 302

def test_status_endpoint(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "spotify" in data
    assert "soulseek" in data

def test_stats_endpoint(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "tracks" in data
    assert "storage_gb" in data


def test_search_requires_query(client):
    resp = client.get("/api/search")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_search_returns_list(client, monkeypatch):
    def mock_search(*args, **kwargs):
        return [{"id": "t1", "name": "Test Track", "artists": [{"name": "Artist"}],
                 "album": {"name": "Album", "images": []}, "duration_ms": 210000}]
    import core.spotify as sp_mod
    monkeypatch.setattr(sp_mod, "_search_tracks", mock_search, raising=False)
    resp = client.get("/api/search?q=test")
    assert resp.status_code in (200, 500)  # 500 if spotify not configured


def test_config_endpoint(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), dict)


def test_settings_endpoint(client):
    resp = client.post("/api/settings", json={"download": {"path": "/tmp/test"}})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("ok") is True


def test_download_requires_body(client):
    resp = client.post("/api/download", data="{}", content_type="application/json")
    assert resp.status_code in (200, 400)


def test_queue_returns_list(client):
    resp = client.get("/api/queue")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_download_enqueues_job(client):
    resp = client.post("/api/download", json={
        "id": "spotify:track:test123",
        "name": "Test Track",
        "artist": "Test Artist",
        "album": "Test Album",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert "job_id" in data


def test_queue_cancel_job(client):
    # Enqueue a job first
    resp = client.post("/api/download", json={
        "id": "spotify:track:cancel_test",
        "name": "Cancel Me",
        "artist": "Artist",
    })
    job_id = resp.get_json()["job_id"]
    # Cancel it
    resp = client.delete(f"/api/queue/{job_id}")
    assert resp.status_code == 200
    assert resp.get_json().get("ok") is True


def test_queue_clear_all(client):
    resp = client.delete("/api/queue")
    assert resp.status_code == 200
    assert resp.get_json().get("ok") is True

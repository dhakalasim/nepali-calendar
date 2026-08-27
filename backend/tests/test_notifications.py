import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine, init_db
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    init_db()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def test_settings_default_and_update(client):
    assert client.get("/api/notifications/settings").json() == {
        "notify_emails": "",
        "notify_phones": "",
        "email_enabled": True,
        "sms_enabled": False,
    }

    r = client.put(
        "/api/notifications/settings",
        json={"notify_emails": "A@B.com , c@d.com", "notify_phones": "+977 98-00000000", "sms_enabled": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["notify_emails"].split("@")[1].startswith("b.com")  # domain lower-cased
    assert body["notify_phones"] == "+9779800000000"
    assert body["sms_enabled"] is True


def test_bad_recipients_rejected(client):
    assert client.put("/api/notifications/settings", json={"notify_emails": "nope"}).status_code == 422
    assert client.put("/api/notifications/settings", json={"notify_phones": "12"}).status_code == 422


def test_status_reflects_targets(client):
    client.put("/api/notifications/settings", json={"notify_emails": "x@y.com"})
    status = client.get("/api/notifications/status").json()
    assert status["email"]["recipients"] == ["x@y.com"]
    assert status["email"]["active"] is True
    assert status["sms"]["active"] is False


def test_test_endpoint_without_providers_logs(client):
    client.put("/api/notifications/settings", json={"notify_emails": "x@y.com", "notify_phones": "+9779812345678", "sms_enabled": True})
    out = client.post("/api/notifications/test", json={}).json()["channels"]
    assert out["email"]["status"] == "logged"
    assert out["sms"]["status"] == "logged"


def test_test_endpoint_skips_unset_channel(client):
    out = client.post("/api/notifications/test", json={"channels": ["sms"]}).json()["channels"]
    assert out["sms"]["status"] == "skipped"


def test_run_delivers_once_then_dedupes(client):
    client.put("/api/notifications/settings", json={"notify_emails": "x@y.com"})
    client.post("/api/events", json={"title": "Renew passport", "ad_date": "2030-01-05", "notify_days_before": 7})

    first = client.post("/api/notifications/run", params={"as_of": "2030-01-01"}).json()
    assert first["sent"] is True
    assert first["count"] == 1
    assert "email" in first["channels"]

    second = client.post("/api/notifications/run", params={"as_of": "2030-01-01"}).json()
    assert second["count"] == 0

    log = client.get("/api/notifications/log").json()
    assert len(log) == 1
    assert log[0]["channel"] == "email"

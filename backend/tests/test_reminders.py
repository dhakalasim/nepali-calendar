from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine, init_db
from app.main import app

NPT = timezone(timedelta(hours=5, minutes=45))


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    init_db()
    with TestClient(app) as c:
        c.put("/api/notifications/settings", json={"notify_emails": "me@example.com"})
        yield c
    Base.metadata.drop_all(bind=engine)


def _npt(offset_minutes):
    return (datetime.now(NPT) + timedelta(minutes=offset_minutes)).strftime("%Y-%m-%dT%H:%M")


def test_scheduled_reminder_fires_when_due(client):
    ev = client.post(
        "/api/events",
        json={
            "title": "Dentist",
            "ad_date": "2030-06-01",
            "reminders": [
                {"remind_at": _npt(-2), "channels": "email"},
                {"remind_at": _npt(60 * 24), "channels": "all"},
            ],
        },
    ).json()
    assert [r["status"] for r in ev["reminders"]] == ["pending", "pending"]

    run = client.post("/api/notifications/run-scheduled").json()
    assert run["processed"] == 1

    after = client.get(f"/api/events/{ev['id']}").json()["reminders"]
    statuses = sorted(r["status"] for r in after)
    assert statuses == ["pending", "sent"]
    assert any(r["sent_at"] for r in after if r["status"] == "sent")

    # idempotent
    assert client.post("/api/notifications/run-scheduled").json()["processed"] == 0


def test_send_reminder_now_targets_requested_channel(client):
    client.put("/api/notifications/settings", json={"notify_phones": "+9779812345678", "sms_enabled": True})
    ev = client.post("/api/events", json={"title": "Pay bill", "ad_date": "2030-01-10"}).json()

    res = client.post(f"/api/events/{ev['id']}/send-reminder", json={"channels": "sms"}).json()
    assert res["sent"] is True
    assert set(res["channels"]) == {"sms"}

    res_all = client.post(f"/api/events/{ev['id']}/send-reminder", json={"channels": "all"}).json()
    assert set(res_all["channels"]) == {"email", "sms"}


def test_updating_reminders_keeps_sent_drops_pending(client):
    ev = client.post(
        "/api/events",
        json={"title": "X", "ad_date": "2030-02-02", "reminders": [{"remind_at": _npt(-1)}]},
    ).json()
    client.post("/api/notifications/run-scheduled")

    updated = client.put(
        f"/api/events/{ev['id']}",
        json={"reminders": [{"remind_at": _npt(60 * 24 * 3)}]},
    ).json()
    statuses = sorted(r["status"] for r in updated["reminders"])
    assert statuses == ["pending", "sent"]


def test_send_reminder_now_without_recipient_reports_note(client):
    client.put("/api/notifications/settings", json={"notify_emails": ""})
    ev = client.post("/api/events", json={"title": "Y", "ad_date": "2030-03-03"}).json()
    res = client.post(f"/api/events/{ev['id']}/send-reminder", json={"channels": "email"}).json()
    assert res["sent"] is False
    assert res["note"]

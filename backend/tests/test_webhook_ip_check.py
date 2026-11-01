"""The optional IP lock on the StroWallet webhook (STROWALLET_WEBHOOK_IPS)."""
import json

from app.core.config import settings
from app.database import SessionLocal
from app.models.strowallet_webhook_event import StroWalletWebhookEvent

from tests.conftest import WEBHOOK_TOKEN, make_account, make_user
from tests.test_strowallet_money_safety import payload

ALLOWED = "209.74.72.48"


def post(client, forwarded=None, token=WEBHOOK_TOKEN):
    headers = {"content-type": "application/json"}
    if forwarded:
        headers["x-forwarded-for"] = forwarded
    return client.post("/strowallet/webhook", params={"token": token}, content=json.dumps(payload()), headers=headers)


def event_count():
    with SessionLocal() as db:
        return db.query(StroWalletWebhookEvent).count()


def test_without_a_configured_list_every_caller_with_the_token_is_accepted(client, stro, monkeypatch):
    monkeypatch.setattr(settings, "strowallet_webhook_ips", "")
    make_account(make_user())
    assert post(client, "198.51.100.7").status_code == 200


def test_the_allowed_address_is_accepted_and_others_are_refused(client, stro, monkeypatch):
    monkeypatch.setattr(settings, "strowallet_webhook_ips", ALLOWED)
    make_account(make_user())

    assert post(client, f"203.0.113.9, {ALLOWED}").status_code == 200
    stored = event_count()
    assert post(client, "198.51.100.7").status_code == 403
    assert post(client).status_code == 403          # no forwarding header at all: the direct caller is not on the list
    assert event_count() == stored                  # refused callers store nothing


def test_a_forged_forwarding_header_cannot_borrow_the_allowed_address(client, stro, monkeypatch):
    monkeypatch.setattr(settings, "strowallet_webhook_ips", ALLOWED)
    make_account(make_user())

    # The attacker writes the allowed address first; the platform appends the real caller last.
    assert post(client, f"{ALLOWED}, 198.51.100.7").status_code == 403
    assert event_count() == 0


def test_a_wrong_token_is_still_refused_first(client, stro, monkeypatch):
    monkeypatch.setattr(settings, "strowallet_webhook_ips", ALLOWED)
    assert post(client, ALLOWED, token="wrong-token-value-1234").status_code == 401

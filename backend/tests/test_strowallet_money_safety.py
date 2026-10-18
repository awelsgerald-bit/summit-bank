"""
Permanent safety tests for the StroWallet bank-transfer flow.

They guard one promise: money only reaches a user when StroWallet itself has confirmed a real
transfer AND an admin has approved the resulting deposit. Run them from the backend folder:

    pip install -r requirements-dev.txt
    python -m pytest -v

Do not delete or weaken the "forged" tests. They are the reason this flow can be trusted.
"""
import json
from decimal import Decimal

from sqlalchemy import func

from app.database import SessionLocal
from app.models.ledger import LedgerEntry
from app.models.strowallet_webhook_event import StroWalletWebhookEvent
from app.models.transaction import Transaction
from app.models.user import User

from tests.conftest import (
    PASSWORD, WEBHOOK_TOKEN, make_account, make_user,
)

ACCOUNT_NUMBER = "2426237910"


def payload(session_id="REAL-SESSION-1", account=ACCOUNT_NUMBER, gross="1000", net="990"):
    return {
        "sessionId": session_id,
        "accountNumber": account,
        "transactionAmount": gross,
        "settledAmount": net,
    }


def send(client, body, token=WEBHOOK_TOKEN):
    return client.post(
        "/strowallet/webhook",
        params={"token": token},
        content=json.dumps(body),
        headers={"content-type": "application/json"},
    )


def count(model):
    with SessionLocal() as db:
        return db.query(func.count(model.id)).scalar()


def balance(user_id):
    with SessionLocal() as db:
        return db.query(User).filter(User.id == user_id).one().balance


def events():
    with SessionLocal() as db:
        return db.query(StroWalletWebhookEvent).order_by(StroWalletWebhookEvent.id).all()


def only_transaction():
    with SessionLocal() as db:
        rows = db.query(Transaction).all()
        assert len(rows) == 1, f"expected exactly one transaction, found {len(rows)}"
        row = rows[0]
        db.expunge(row)
        return row


# ---------------------------------------------------------------------------------------
# The forged-webhook negative test (permanent)
# ---------------------------------------------------------------------------------------

def test_forged_webhook_with_fake_session_id_never_credits(client, stro):
    """Someone who learns the webhook URL (token included) posts a made-up transfer. StroWallet
    has never heard of that sessionId, so nothing may be created, however often it is re-sent."""
    user_id = make_user()
    make_account(user_id)
    stro.says_not_received()

    for _ in range(6):
        response = send(client, payload(session_id="FAKE-SESSION-ID-123", gross="500000", net="500000"))
        assert response.status_code == 200  # we always acknowledge; we just never trust it

    [event] = events()
    assert event.status == "rejected"
    assert event.verified_at is None
    assert event.transaction_id is None
    assert count(Transaction) == 0
    assert count(LedgerEntry) == 0
    assert balance(user_id) == Decimal("50.00")
    assert len(stro.calls) >= 1, "the forged event must have been checked with StroWallet"


def test_forged_webhook_when_stro_wallet_is_unreachable_still_creates_nothing(client, stro):
    user_id = make_user()
    make_account(user_id)
    stro.is_down()

    send(client, payload(session_id="FAKE-WHEN-DOWN"))

    [event] = events()
    assert event.status == "unverified"
    assert count(Transaction) == 0
    assert balance(user_id) == Decimal("50.00")


def test_wrong_token_is_rejected_and_nothing_is_stored(client, stro):
    user_id = make_user()
    make_account(user_id)

    response = send(client, payload(), token="not-the-secret")

    assert response.status_code == 401
    assert events() == []
    assert stro.calls == []
    assert count(Transaction) == 0


def test_missing_token_is_rejected(client, stro):
    make_account(make_user())
    response = client.post("/strowallet/webhook", content=json.dumps(payload()))
    assert response.status_code == 401
    assert events() == []


# ---------------------------------------------------------------------------------------
# A genuine transfer: pending deposit only, credited by an admin
# ---------------------------------------------------------------------------------------

def test_verified_transfer_creates_a_pending_deposit_and_credits_nothing(client, stro):
    user_id = make_user()
    make_account(user_id)
    stro.says_verified()

    response = send(client, payload())

    assert response.status_code == 200
    transaction = only_transaction()
    assert transaction.status == "pending"
    assert transaction.amount == Decimal("990")  # the net amount, not the gross
    assert transaction.receiver_id == user_id
    assert balance(user_id) == Decimal("50.00")  # nothing credited yet
    assert count(LedgerEntry) == 0
    [event] = events()
    assert event.status == "deposit_created"
    assert event.transaction_id == transaction.id
    # StroWallet was asked about this exact session and amount
    assert stro.calls[0]["params"]["sessionID"] == "REAL-SESSION-1"
    assert stro.calls[0]["params"]["amount"] == "1000.00"


def test_duplicate_delivery_never_makes_a_second_deposit(client, stro):
    user_id = make_user()
    make_account(user_id)
    stro.says_verified()

    for _ in range(4):
        assert send(client, payload()).status_code == 200

    assert count(Transaction) == 1
    [event] = events()
    assert event.delivery_count == 4


def test_resending_the_same_session_with_a_bigger_amount_changes_nothing(client, stro):
    user_id = make_user()
    make_account(user_id)
    stro.says_verified()
    send(client, payload(gross="1000", net="990"))

    send(client, payload(gross="999999", net="999999"))

    transaction = only_transaction()
    assert transaction.amount == Decimal("990")


def test_wrong_amount_reported_by_stro_wallet_is_not_verified(client, stro):
    user_id = make_user()
    make_account(user_id)
    stro.says_verified('{"status":200,"transactionAmount":10}')  # we were told 1000

    send(client, payload(gross="1000", net="990"))

    [event] = events()
    assert event.status == "unverified"
    assert count(Transaction) == 0


def test_impossible_amounts_are_stored_as_invalid_and_never_verified(client, stro):
    user_id = make_user()
    make_account(user_id)
    stro.says_verified()

    send(client, payload(session_id="BAD-1", gross="1000", net="1500"))  # net larger than gross
    send(client, payload(session_id="BAD-2", gross="-5", net="-5"))
    send(client, payload(session_id="BAD-3", gross="abc", net="abc"))

    assert [e.status for e in events()] == ["invalid", "invalid", "invalid"]
    assert stro.calls == []
    assert count(Transaction) == 0


def test_unknown_account_number_is_stored_but_never_processed(client, stro):
    make_account(make_user())
    stro.says_verified()

    send(client, payload(account="9999999999"))

    [event] = events()
    assert event.status == "unmatched"
    assert stro.calls == []
    assert count(Transaction) == 0


def test_sandbox_account_never_creates_a_deposit(client, stro):
    user_id = make_user()
    make_account(user_id, mode="sandbox")
    stro.says_verified()  # even if StroWallet somehow confirmed it

    send(client, payload())

    assert count(Transaction) == 0
    assert balance(user_id) == Decimal("50.00")


def test_suspended_account_never_creates_a_deposit(client, stro):
    user_id = make_user()
    make_account(user_id, status="suspended")
    stro.says_verified()

    send(client, payload())

    assert count(Transaction) == 0


# ---------------------------------------------------------------------------------------
# Admin approval: credits once, with the StroWallet reference on the ledger
# ---------------------------------------------------------------------------------------

def _admin_headers(client):
    make_user(email="admin@example.com", role="admin")
    response = client.post("/auth/login", json={"email": "admin@example.com", "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_approval_credits_exactly_once_and_tags_the_ledger(client, stro):
    user_id = make_user()
    make_account(user_id)
    stro.says_verified()
    send(client, payload(session_id="APPROVE-ME-1"))
    transaction = only_transaction()
    headers = _admin_headers(client)

    first = client.post(f"/admin/transactions/{transaction.id}/approve", headers=headers)
    second = client.post(f"/admin/transactions/{transaction.id}/approve", headers=headers)

    assert first.status_code == 200, first.text
    assert second.status_code == 409
    assert balance(user_id) == Decimal("1040")  # 50 + 990, once
    with SessionLocal() as db:
        entries = db.query(LedgerEntry).filter(LedgerEntry.transaction_type == "deposit").all()
        assert len(entries) == 2  # one credit, one debit
        assert {e.external_reference for e in entries} == {"APPROVE-ME-1"}
        assert {e.reference_transaction_id for e in entries} == {transaction.id}


def test_rejecting_the_deposit_leaves_the_balance_alone(client, stro):
    user_id = make_user()
    make_account(user_id)
    stro.says_verified()
    send(client, payload(session_id="REJECT-ME-1"))
    transaction = only_transaction()

    response = client.post(f"/admin/transactions/{transaction.id}/reject", headers=_admin_headers(client))

    assert response.status_code == 200
    assert balance(user_id) == Decimal("50.00")
    assert count(LedgerEntry) == 0

"""QR transfers: signed codes, scanning, instant settlement with ledger entries, PIN, idempotency,
limits, held payments, dynamic requests, and concurrency."""
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.core.config import settings
from app.database import SessionLocal
from app.models.ledger import LedgerAccount, LedgerEntry
from app.models.qr import QrPaymentRequest, QrTransfer
from app.models.transaction import Transaction
from app.models.user import User
from app.services import qr_service

from tests.conftest import PASSWORD, make_user
from tests.test_round1_account_features import login
from tests.test_round2_features import account_of, balance
from tests.test_round3a_pin_and_savings import PIN, detail, set_pin, with_pin


def setup_pair(client, sender_balance="1000.00", receiver_balance="0.00"):
    """Ada (sender, PIN set) and Bola (receiver). Returns ids, headers, and Bola's static code."""
    sender_id = make_user(email="ada@example.com", balance=sender_balance)
    receiver_id = make_user(email="bola@example.com", balance=receiver_balance)
    ada = login(client, "ada@example.com")
    assert set_pin(client, ada).status_code == 200
    bola = login(client, "bola@example.com")
    code = client.get("/qr/me", headers=bola).json()["payload"]
    return sender_id, receiver_id, with_pin(ada), bola, code


_key = {"n": 0}


def pay(client, headers, payload, amount="100.00", narration=None, key=None):
    _key["n"] += 1
    body = {"payload": payload, "amount": amount}
    if narration is not None:
        body["narration"] = narration
    return client.post("/qr/transfer", headers={**headers, "Idempotency-Key": key or f"key-test-{_key['n']:06d}"}, json=body)


def set_active(user_id, value):
    with SessionLocal() as db:
        db.query(User).filter(User.id == user_id).one().is_active = value
        db.commit()


def ledger_rows(reference_transaction_id):
    with SessionLocal() as db:
        return [(e.direction, Decimal(e.amount), e.ledger_account_id, e.transaction_type)
                for e in db.query(LedgerEntry).filter(LedgerEntry.reference_transaction_id == reference_transaction_id).all()]


# ------------------------------------------------------------------ my QR code

def test_my_qr_shows_name_account_bank_and_hides_account_details_in_the_code(client):
    user_id = make_user()
    headers = login(client)
    body = client.get("/qr/me", headers=headers).json()
    assert body["full_name"] == "Test User" and body["bank_name"] == "Summit Bank"
    assert body["account_number"] == account_of(user_id)
    assert body["payload"].startswith("SBQ1:S:")
    assert body["account_number"] not in body["payload"] and "ada@example.com" not in body["payload"]
    assert client.get("/qr/me", headers=headers).json()["payload"] == body["payload"]  # permanent


def test_qr_endpoints_need_a_login(client):
    assert client.get("/qr/me").status_code == 401
    assert client.post("/qr/resolve", json={"payload": "x"}).status_code == 401
    assert client.post("/qr/transfer", json={"payload": "x", "amount": "1"}).status_code == 401
    assert client.get("/qr/history").status_code == 401


# ------------------------------------------------------------------ scanning

def test_scanning_a_valid_code_shows_the_verified_recipient(client):
    _, receiver_id, ada, _, code = setup_pair(client)
    response = client.post("/qr/resolve", headers=ada, json={"payload": code})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "static" and body["recipient"]["account_number"] == account_of(receiver_id)
    assert body["recipient"]["full_name"] == "Test User" and body["recipient"]["bank_name"] == "Summit Bank"


def test_invalid_codes_are_refused(client):
    _, receiver_id, ada, _, code = setup_pair(client)
    tampered = code[:-1] + ("0" if code[-1] != "0" else "1")
    other_user = code.replace(f"SBQ1:S:{receiver_id}:", f"SBQ1:S:{receiver_id + 5}:")  # edited id, old signature
    for bad in ["", "hello", account_of(receiver_id), '{"type":"summit_bank_account","account_number":"123"}',
                tampered, other_user, code.replace("SBQ1", "SBQ2"), "SBQ1:S:1:" + "a" * 20, "x" * 500]:
        response = client.post("/qr/resolve", headers=ada, json={"payload": bad or " "})
        assert response.status_code in (400, 422), (bad, response.text)


def test_you_cannot_scan_your_own_code(client):
    _, _, ada, _, _ = setup_pair(client)
    own = client.get("/qr/me", headers=ada).json()["payload"]
    assert client.post("/qr/resolve", headers=ada, json={"payload": own}).status_code == 400
    assert pay(client, ada, own).status_code == 400


def test_inactive_recipient_cannot_be_scanned_or_paid(client):
    _, receiver_id, ada, _, code = setup_pair(client)
    set_active(receiver_id, False)
    assert client.post("/qr/resolve", headers=ada, json={"payload": code}).status_code == 400
    response = pay(client, ada, code)
    assert response.status_code == 400 and "cannot receive" in detail(response)


def test_inactive_sender_cannot_pay(client):
    sender_id, _, ada, _, code = setup_pair(client)
    set_active(sender_id, False)
    assert pay(client, ada, code).status_code == 403


# ------------------------------------------------------------------ paying

def test_successful_payment_moves_money_and_writes_balanced_ledger_entries(client):
    sender_id, receiver_id, ada, bola, code = setup_pair(client, "1000.00", "50.00")
    response = pay(client, ada, code, "250.50", narration="lunch")
    assert response.status_code == 201, response.text
    receipt = response.json()
    assert receipt["status"] == "completed" and receipt["amount"] == "250.50"
    assert receipt["reference"].startswith("SBQ-") and receipt["narration"] == "lunch"
    assert receipt["recipient"]["account_number"] == account_of(receiver_id) and receipt["duplicate"] is False

    assert balance(sender_id) == Decimal("749.50")
    assert balance(receiver_id) == Decimal("300.50")

    rows = ledger_rows(receipt["transaction_id"])
    assert sorted(r[0] for r in rows) == ["credit", "debit"]
    assert all(r[1] == Decimal("250.50") and r[3] == "transfer" for r in rows)
    assert len({r[2] for r in rows}) == 2  # two different ledger accounts
    with SessionLocal() as db:
        owners = {r[0]: db.query(LedgerAccount).filter(LedgerAccount.id == r[2]).one().user_id for r in rows}
    assert owners["debit"] == sender_id and owners["credit"] == receiver_id

    with SessionLocal() as db:
        tx = db.query(Transaction).filter(Transaction.id == receipt["transaction_id"]).one()
        assert tx.status == "approved" and tx.sender_id == sender_id and tx.receiver_id == receiver_id


def test_both_people_see_it_in_their_histories(client):
    _, _, ada, bola, code = setup_pair(client)
    receipt = pay(client, ada, code, "100.00").json()
    mine = client.get("/qr/history", headers=ada).json()
    theirs = client.get("/qr/history", headers=bola).json()
    assert [r["reference"] for r in mine] == [receipt["reference"]] and mine[0]["direction"] == "sent"
    assert [r["reference"] for r in theirs] == [receipt["reference"]] and theirs[0]["direction"] == "received"
    for headers in (ada, bola):  # and in the normal transaction history
        ids = [t["id"] for t in client.get("/transactions/history", headers=headers).json()]
        assert receipt["transaction_id"] in ids
    assert client.get(f"/qr/receipts/{receipt['reference']}", headers=ada).status_code == 200


def test_a_stranger_cannot_read_someone_elses_receipt(client):
    _, _, ada, _, code = setup_pair(client)
    receipt = pay(client, ada, code).json()
    make_user(email="eve@example.com")
    eve = login(client, "eve@example.com")
    assert client.get(f"/qr/receipts/{receipt['reference']}", headers=eve).status_code == 404
    assert client.get("/qr/history", headers=eve).json() == []


def test_insufficient_balance_is_refused_and_nothing_moves(client):
    sender_id, receiver_id, ada, _, code = setup_pair(client, "50.00", "0.00")
    response = pay(client, ada, code, "50.01")
    assert response.status_code == 400 and "Insufficient" in detail(response)
    assert balance(sender_id) == Decimal("50.00") and balance(receiver_id) == Decimal("0.00")
    with SessionLocal() as db:
        assert db.query(QrTransfer).count() == 0 and db.query(LedgerEntry).count() == 0


def test_bad_amounts_are_refused(client):
    _, _, ada, _, code = setup_pair(client)
    for amount in ["0", "-5", "abc", "10.005", "NaN", "Infinity"]:
        response = pay(client, ada, code, amount)
        assert response.status_code in (400, 422), (amount, response.text)


def test_pin_is_required_and_checked(client):
    sender_id, _, ada, _, code = setup_pair(client)
    no_pin = {k: v for k, v in ada.items() if k != "X-Transaction-Pin"}
    response = pay(client, no_pin, code)
    assert response.status_code == 428 and detail(response) == "PIN_REQUIRED"
    response = pay(client, {**ada, "X-Transaction-Pin": "0000"}, code)
    assert response.status_code == 403 and detail(response).startswith("PIN_INVALID")
    assert balance(sender_id) == Decimal("1000.00")


def test_a_user_with_no_pin_cannot_pay_by_qr(client):
    make_user(email="ada@example.com")
    make_user(email="bola@example.com")
    ada = login(client, "ada@example.com")
    code = client.get("/qr/me", headers=login(client, "bola@example.com")).json()["payload"]
    response = pay(client, ada, code)
    assert response.status_code == 428 and detail(response) == "PIN_NOT_SET"


def test_the_pin_locks_after_five_wrong_tries(client):
    _, _, ada, _, code = setup_pair(client)
    wrong = {**ada, "X-Transaction-Pin": "0000"}
    for _ in range(4):
        assert pay(client, wrong, code).status_code == 403
    response = pay(client, wrong, code)
    assert response.status_code == 429 and detail(response).startswith("PIN_LOCKED")
    assert pay(client, ada, code).status_code == 429  # even the right PIN is refused while locked


# ------------------------------------------------------------------ idempotency

def test_the_same_request_twice_moves_money_once(client):
    sender_id, receiver_id, ada, _, code = setup_pair(client)
    first = pay(client, ada, code, "100.00", key="same-key-0001")
    second = pay(client, ada, code, "100.00", key="same-key-0001")
    assert first.status_code == 201 and second.status_code == 201
    assert second.json()["reference"] == first.json()["reference"] and second.json()["duplicate"] is True
    assert balance(sender_id) == Decimal("900.00") and balance(receiver_id) == Decimal("100.00")
    with SessionLocal() as db:
        assert db.query(QrTransfer).count() == 1 and db.query(LedgerEntry).count() == 2


def test_the_same_key_with_different_details_is_refused(client):
    sender_id, _, ada, _, code = setup_pair(client)
    assert pay(client, ada, code, "100.00", key="same-key-0002").status_code == 201
    response = pay(client, ada, code, "200.00", key="same-key-0002")
    assert response.status_code == 409
    assert balance(sender_id) == Decimal("900.00")


def test_an_idempotency_key_is_required(client):
    _, _, ada, _, code = setup_pair(client)
    response = client.post("/qr/transfer", headers=ada, json={"payload": code, "amount": "10.00"})
    assert response.status_code == 400
    assert pay(client, ada, code, key="short").status_code == 400


# ------------------------------------------------------------------ limits and held payments

def test_per_payment_limit(client, monkeypatch):
    sender_id, _, ada, _, code = setup_pair(client)
    monkeypatch.setattr(settings, "qr_transfer_max_amount", Decimal("200"))
    assert pay(client, ada, code, "200.01").status_code == 400
    assert pay(client, ada, code, "200.00").status_code == 201


def test_daily_limit(client, monkeypatch):
    sender_id, _, ada, _, code = setup_pair(client)
    monkeypatch.setattr(settings, "qr_daily_limit", Decimal("300"))
    assert pay(client, ada, code, "200.00").status_code == 201
    response = pay(client, ada, code, "150.00")
    assert response.status_code == 400 and "daily" in detail(response)
    assert pay(client, ada, code, "100.00").status_code == 201


def test_a_flagged_payment_is_held_and_moves_no_money_until_an_admin_approves(client):
    sender_id, receiver_id, ada, _, code = setup_pair(client, "20000.00", "0.00")
    response = pay(client, ada, code, "6000.00")  # large with no history: the existing fraud rule flags it
    assert response.status_code == 201
    receipt = response.json()
    assert receipt["status"] == "pending_review"
    assert balance(sender_id) == Decimal("20000.00") and balance(receiver_id) == Decimal("0.00")
    assert ledger_rows(receipt["transaction_id"]) == []

    make_user(email="admin@example.com", role="admin")
    admin = login(client, "admin@example.com")
    assert client.post(f"/admin/transactions/{receipt['transaction_id']}/approve", headers=admin).status_code == 200
    assert balance(sender_id) == Decimal("14000.00") and balance(receiver_id) == Decimal("6000.00")
    assert sorted(r[0] for r in ledger_rows(receipt["transaction_id"])) == ["credit", "debit"]
    assert client.get(f"/qr/receipts/{receipt['reference']}", headers=ada).json()["status"] == "completed"


# ------------------------------------------------------------------ dynamic payment requests

def make_request(client, headers, **body):
    response = client.post("/qr/requests", headers=headers, json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_dynamic_request_with_fixed_amount_can_be_paid_once(client):
    sender_id, receiver_id, ada, bola, _ = setup_pair(client)
    req = make_request(client, bola, amount="75.00", reference="INV-42", note="Invoice 42")
    assert req["payload"].startswith("SBQ1:D:") and req["status"] == "open"

    scan = client.post("/qr/resolve", headers=ada, json={"payload": req["payload"]}).json()
    assert scan["kind"] == "dynamic" and scan["request"]["amount"] == "75.00" and scan["request"]["reference"] == "INV-42"
    assert scan["recipient"]["account_number"] == account_of(receiver_id)

    assert pay(client, ada, req["payload"], "70.00").status_code == 400  # must be the exact amount
    first = pay(client, ada, req["payload"], "75.00")
    assert first.status_code == 201
    assert balance(receiver_id) == Decimal("75.00")
    again = pay(client, ada, req["payload"], "75.00")
    assert again.status_code == 409  # already paid
    assert balance(receiver_id) == Decimal("75.00")
    assert client.get("/qr/requests", headers=bola).json()[0]["status"] == "paid"


def test_dynamic_request_without_amount_lets_the_payer_choose(client):
    _, receiver_id, ada, bola, _ = setup_pair(client)
    req = make_request(client, bola)
    assert pay(client, ada, req["payload"], "33.00").status_code == 201
    assert balance(receiver_id) == Decimal("33.00")


def test_expired_and_cancelled_requests_cannot_be_paid(client):
    _, receiver_id, ada, bola, _ = setup_pair(client)
    expired = make_request(client, bola, amount="10.00")
    with SessionLocal() as db:
        row = db.query(QrPaymentRequest).filter(QrPaymentRequest.id == expired["id"]).one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    assert client.post("/qr/resolve", headers=ada, json={"payload": expired["payload"]}).status_code == 410
    assert pay(client, ada, expired["payload"], "10.00").status_code == 410

    cancelled = make_request(client, bola, amount="10.00")
    assert client.post(f"/qr/requests/{cancelled['id']}/cancel", headers=bola).status_code == 200
    assert pay(client, ada, cancelled["payload"], "10.00").status_code == 410
    assert balance(receiver_id) == Decimal("0.00")


def test_only_the_owner_can_cancel_a_request(client):
    _, _, ada, bola, _ = setup_pair(client)
    req = make_request(client, bola, amount="10.00")
    assert client.post(f"/qr/requests/{req['id']}/cancel", headers=ada).status_code == 404


def test_a_forged_dynamic_code_is_refused(client):
    _, _, ada, bola, _ = setup_pair(client)
    req = make_request(client, bola, amount="10.00")
    forged = req["payload"][:-3] + "abc"
    assert client.post("/qr/resolve", headers=ada, json={"payload": forged}).status_code == 400


# ------------------------------------------------------------------ concurrency

def run_threads(client, calls):
    results = [None] * len(calls)

    def work(i, fn):
        try:
            results[i] = fn().status_code
        except Exception as exc:  # a locked SQLite database counts as "did not go through"
            results[i] = f"error:{exc.__class__.__name__}"

    threads = [threading.Thread(target=work, args=(i, fn)) for i, fn in enumerate(calls)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def test_two_payments_cannot_spend_the_same_money(client):
    sender_id, receiver_id, ada, _, code = setup_pair(client, "100.00", "0.00")
    results = run_threads(client, [
        lambda: pay(client, ada, code, "80.00", key="race-key-0001"),
        lambda: pay(client, ada, code, "80.00", key="race-key-0002"),
    ])
    assert results.count(201) <= 1, results
    assert balance(sender_id) >= 0
    assert balance(sender_id) + balance(receiver_id) == Decimal("100.00")  # nothing created or lost
    with SessionLocal() as db:
        assert db.query(QrTransfer).count() == results.count(201)
        assert db.query(LedgerEntry).count() == 2 * results.count(201)


def test_the_same_request_sent_at_once_moves_money_once(client):
    sender_id, receiver_id, ada, _, code = setup_pair(client, "1000.00", "0.00")
    results = run_threads(client, [lambda: pay(client, ada, code, "100.00", key="race-same-key") for _ in range(4)])
    with SessionLocal() as db:
        assert db.query(QrTransfer).count() <= 1
    assert balance(sender_id) + balance(receiver_id) == Decimal("1000.00")
    assert balance(receiver_id) in (Decimal("0.00"), Decimal("100.00")), results


def test_two_people_cannot_both_pay_one_request(client):
    sender_id, receiver_id, ada, bola, _ = setup_pair(client, "1000.00", "0.00")
    make_user(email="cy@example.com", balance="1000.00")
    cy = login(client, "cy@example.com")
    assert set_pin(client, cy).status_code == 200
    cy = with_pin(cy)
    req = make_request(client, bola, amount="50.00")
    run_threads(client, [lambda: pay(client, ada, req["payload"], "50.00"), lambda: pay(client, cy, req["payload"], "50.00")])
    assert balance(receiver_id) == Decimal("50.00")

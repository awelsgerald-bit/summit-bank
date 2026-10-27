"""Round 2: account-name lookup, saved payments, contact us (support tickets), card freeze."""
from decimal import Decimal

import pytest

from app.database import SessionLocal
from app.models.card import CardApplication
from app.models.saved_payment import SavedPayment
from app.models.transaction import Transaction
from app.models.user import User
from app.services import email_service, rate_limit

from tests.conftest import make_user
from tests.test_round1_account_features import login


@pytest.fixture(autouse=True)
def clean_limits():
    rate_limit.reset()
    yield
    rate_limit.reset()


def account_of(user_id):
    with SessionLocal() as db:
        return db.query(User).filter(User.id == user_id).one().account_number


def set_name(user_id, name):
    with SessionLocal() as db:
        db.query(User).filter(User.id == user_id).one().full_name = name
        db.commit()


def balance(user_id):
    with SessionLocal() as db:
        return db.query(User).filter(User.id == user_id).one().balance


def tx_count():
    with SessionLocal() as db:
        return db.query(Transaction).count()


# ------------------------------------------------------------------ lookup

def test_lookup_shows_a_partly_hidden_name(client):
    make_user()
    other = make_user(email="bola@example.com")
    set_name(other, "Ada Okafor Bello")
    headers = login(client)

    body = client.get(f"/account/lookup/{account_of(other)}", headers=headers).json()

    assert body["name"] == "Ada O*** B***"
    assert body["is_self"] is False
    assert "Okafor" not in str(body)


def test_lookup_flags_my_own_account_and_unknown_accounts(client):
    me = make_user()
    headers = login(client)

    assert client.get(f"/account/lookup/{account_of(me)}", headers=headers).json()["is_self"] is True
    assert client.get("/account/lookup/0000000000", headers=headers).status_code == 404
    assert client.get("/account/lookup/abc", headers=headers).status_code == 400
    assert client.get("/account/lookup/12", headers=headers).status_code == 400


def test_lookup_needs_login_and_is_rate_limited(client):
    make_user()
    assert client.get("/account/lookup/1234567890").status_code == 401
    headers = login(client)
    codes = [client.get("/account/lookup/0000000000", headers=headers).status_code for _ in range(25)]
    assert codes[:20] == [404] * 20
    assert 429 in codes[20:]


# ------------------------------------------------------------------ saved payments

def make_saved(client, headers, to_account, amount="25.50", label="Rent"):
    return client.post("/saved-payments", headers=headers, json={
        "label": label, "recipient_account_number": to_account, "amount": amount, "description": "monthly",
    })


def test_saved_payment_can_be_created_listed_and_deleted(client):
    make_user()
    other = make_user(email="bola@example.com")
    headers = login(client)

    created = make_saved(client, headers, account_of(other))
    assert created.status_code == 201, created.text
    assert created.json()["recipient_name"].startswith("Test")
    assert len(client.get("/saved-payments", headers=headers).json()) == 1

    assert client.delete(f"/saved-payments/{created.json()['id']}", headers=headers).status_code == 204
    assert client.get("/saved-payments", headers=headers).json() == []


def test_saved_payment_needs_a_real_other_recipient(client):
    me = make_user()
    headers = login(client)
    assert make_saved(client, headers, "0000000000").status_code == 404
    assert make_saved(client, headers, account_of(me)).status_code == 400


def test_paying_a_saved_payment_makes_one_pending_transfer_and_moves_no_money(client):
    me = make_user(balance="100.00")
    other = make_user(email="bola@example.com")
    headers = login(client)
    saved_id = make_saved(client, headers, account_of(other), amount="25.50").json()["id"]

    response = client.post(f"/saved-payments/{saved_id}/pay", headers=headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert Decimal(body["amount"]) == Decimal("25.50")
    assert tx_count() == 1
    assert balance(me) == Decimal("100.00")  # nothing moves until an admin approves


def test_double_tap_does_not_send_twice(client):
    make_user(balance="100.00")
    other = make_user(email="bola@example.com")
    headers = login(client)
    saved_id = make_saved(client, headers, account_of(other)).json()["id"]

    first = client.post(f"/saved-payments/{saved_id}/pay", headers=headers)
    second = client.post(f"/saved-payments/{saved_id}/pay", headers=headers)

    assert first.status_code == 201
    assert second.status_code == 429
    assert tx_count() == 1


def test_failed_payment_does_not_block_a_retry(client):
    make_user(balance="10.00")  # not enough for 25.50
    other = make_user(email="bola@example.com")
    headers = login(client)
    saved_id = make_saved(client, headers, account_of(other), amount="25.50").json()["id"]

    first = client.post(f"/saved-payments/{saved_id}/pay", headers=headers)
    second = client.post(f"/saved-payments/{saved_id}/pay", headers=headers)

    assert first.status_code == 400 and second.status_code == 400  # insufficient balance, not "wait"
    assert tx_count() == 0


def test_nobody_can_use_or_delete_someone_elses_saved_payment(client):
    make_user()
    other = make_user(email="bola@example.com", balance="500.00")
    make_user(email="spy@example.com", balance="500.00")
    owner_headers = login(client)
    saved_id = make_saved(client, owner_headers, account_of(other)).json()["id"]
    spy = login(client, "spy@example.com")

    assert client.post(f"/saved-payments/{saved_id}/pay", headers=spy).status_code == 404
    assert client.delete(f"/saved-payments/{saved_id}", headers=spy).status_code == 404
    assert client.get("/saved-payments", headers=spy).json() == []
    assert tx_count() == 0


# ------------------------------------------------------------------ contact us

def test_ticket_is_created_listed_privately_and_admins_are_emailed(client, monkeypatch):
    sent = []
    monkeypatch.setattr(email_service, "send_email", lambda to, subject, body: sent.append((to, subject, body)))
    make_user()
    make_user(email="admin@example.com", role="admin")
    make_user(email="other@example.com")
    headers = login(client)

    created = client.post("/support/tickets", headers=headers, json={
        "category": "payment", "subject": "Missing deposit", "message": "<b>Hello</b> my deposit is missing",
    })

    assert created.status_code == 201, created.text
    assert created.json()["status"] == "open"
    assert len(client.get("/support/tickets", headers=headers).json()) == 1
    assert client.get("/support/tickets", headers=login(client, "other@example.com")).json() == []
    assert [to for to, _, _ in sent] == ["admin@example.com"]
    assert "<b>Hello</b>" not in sent[0][2]            # user text is escaped in the email
    assert "&lt;b&gt;Hello" in sent[0][2]


def test_ticket_validation_and_spam_limit(client):
    make_user()
    headers = login(client)
    assert client.post("/support/tickets", headers=headers, json={"category": "bogus", "subject": "Hello there", "message": "A real message"}).status_code == 400
    assert client.post("/support/tickets", headers=headers, json={"subject": "x", "message": "y"}).status_code == 422
    codes = [
        client.post("/support/tickets", headers=headers, json={"subject": "Question", "message": f"Message number {i}"}).status_code
        for i in range(7)
    ]
    assert codes[:5] == [201] * 5
    assert codes[5:] == [429, 429]


def test_admin_can_reply_and_close_but_users_cannot(client, monkeypatch):
    sent = []
    monkeypatch.setattr(email_service, "send_email", lambda to, subject, body: sent.append(to))
    make_user()
    make_user(email="admin@example.com", role="admin")
    user_headers = login(client)
    admin_headers = login(client, "admin@example.com")
    ticket_id = client.post("/support/tickets", headers=user_headers, json={"subject": "Help me", "message": "I need help"}).json()["id"]
    sent.clear()

    assert client.get("/admin/support/tickets", headers=user_headers).status_code == 403
    assert client.post(f"/admin/support/tickets/{ticket_id}/reply", headers=user_headers, json={"reply": "hi"}).status_code == 403

    listing = client.get("/admin/support/tickets", headers=admin_headers).json()
    assert listing[0]["user_email"] == "ada@example.com"

    replied = client.post(f"/admin/support/tickets/{ticket_id}/reply", headers=admin_headers, json={"reply": "Fixed it"})
    assert replied.status_code == 200 and replied.json()["status"] == "answered"
    assert sent == ["ada@example.com"]
    mine = client.get("/support/tickets", headers=user_headers).json()[0]
    assert mine["admin_reply"] == "Fixed it"

    assert client.post(f"/admin/support/tickets/{ticket_id}/close", headers=admin_headers).json()["status"] == "closed"
    assert client.post(f"/admin/support/tickets/{ticket_id}/reply", headers=admin_headers, json={"reply": "more"}).status_code == 409


# ------------------------------------------------------------------ card freeze

def make_card(user_id, status="approved"):
    with SessionLocal() as db:
        card = CardApplication(user_id=user_id, card_type="virtual", status=status, card_number="4111 1111 1111 1111")
        db.add(card)
        db.commit()
        return card.id


def test_owner_can_freeze_and_unfreeze_an_active_card(client):
    me = make_user()
    card_id = make_card(me)
    headers = login(client)

    assert client.get("/cards", headers=headers).json()[0]["is_frozen"] is False
    assert client.post(f"/cards/{card_id}/freeze", headers=headers).json()["is_frozen"] is True
    assert client.get("/cards", headers=headers).json()[0]["is_frozen"] is True
    assert client.post(f"/cards/{card_id}/unfreeze", headers=headers).json()["is_frozen"] is False


def test_only_active_cards_of_the_owner_can_be_frozen(client):
    me = make_user()
    other = make_user(email="bola@example.com")
    pending = make_card(me, status="pending")
    theirs = make_card(other)
    headers = login(client)

    assert client.post(f"/cards/{pending}/freeze", headers=headers).status_code == 409
    assert client.post(f"/cards/{theirs}/freeze", headers=headers).status_code == 404
    assert client.post("/cards/9999/freeze", headers=headers).status_code == 404
    assert client.post(f"/cards/{pending}/freeze").status_code == 401

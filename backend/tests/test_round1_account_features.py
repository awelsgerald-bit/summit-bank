"""Round 1 features: profile edits, password change, profile photo, statements and receipts.
None of these may ever change a balance or a transaction."""
import base64
from datetime import datetime, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models.transaction import Transaction, TransactionType
from app.models.user import User

from tests.conftest import PASSWORD, make_user

# A real 1x1 PNG.
PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def login(client, email="ada@example.com", password=PASSWORD):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def add_tx(kind, amount, sender=None, receiver=None, status="approved", when=None, description="", currency="NGN"):
    with SessionLocal() as db:
        tx = Transaction(
            transaction_type=kind, amount=Decimal(amount), sender_id=sender, receiver_id=receiver,
            status=status, description=description, currency=currency,
            timestamp=when or datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
        )
        db.add(tx)
        db.commit()
        return tx.id


def balance(user_id):
    with SessionLocal() as db:
        return db.query(User).filter(User.id == user_id).one().balance


# ---------------------------------------------------------------- profile and password

def test_profile_can_be_edited_but_not_email_or_balance(client):
    user_id = make_user()
    headers = login(client)

    response = client.patch("/account/profile", headers=headers, json={
        "full_name": "  Ada Obi ", "phone_number": "08031234567", "balance": "999999", "email": "x@y.com",
    })

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["full_name"] == "Ada Obi"
    assert body["phone_number"] == "08031234567"
    assert body["email"] == "ada@example.com"
    assert balance(user_id) == Decimal("50.00")


def test_change_password_needs_the_current_one(client):
    make_user()
    headers = login(client)

    wrong = client.post("/account/change-password", headers=headers,
                        json={"current_password": "not-it-at-all", "new_password": "brand-new-pass-1"})
    assert wrong.status_code == 400

    ok = client.post("/account/change-password", headers=headers,
                     json={"current_password": PASSWORD, "new_password": "brand-new-pass-1"})
    assert ok.status_code == 200
    assert client.post("/auth/login", json={"email": "ada@example.com", "password": PASSWORD}).status_code == 401
    assert client.post("/auth/login", json={"email": "ada@example.com", "password": "brand-new-pass-1"}).status_code == 200


# ---------------------------------------------------------------- profile photo

def test_avatar_can_be_set_and_removed(client):
    make_user()
    headers = login(client)

    set_response = client.put("/account/avatar", headers=headers, json={"image": PNG})
    assert set_response.status_code == 200, set_response.text
    assert set_response.json()["avatar"] == PNG
    assert client.get("/account/profile", headers=headers).json()["avatar"] == PNG

    assert client.delete("/account/avatar", headers=headers).json()["avatar"] is None


def test_avatar_rejects_anything_that_is_not_a_real_small_image(client):
    make_user()
    headers = login(client)
    fake_png = "data:image/png;base64," + base64.b64encode(b"<script>alert(1)</script>").decode()
    svg = "data:image/svg+xml;base64," + base64.b64encode(b"<svg onload=alert(1)/>").decode()
    big = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 210_000).decode()

    for bad in (fake_png, svg, "javascript:alert(1)", "not an image", big):
        response = client.put("/account/avatar", headers=headers, json={"image": bad})
        assert response.status_code in (400, 413, 422), (bad[:30], response.status_code)

    assert client.get("/account/profile", headers=headers).json()["avatar"] is None


# ---------------------------------------------------------------- statements

def test_statement_lists_only_my_transactions_and_totals_only_approved(client):
    me = make_user()
    other = make_user(email="bola@example.com")
    third = make_user(email="chi@example.com")
    add_tx(TransactionType.DEPOSIT, "1000", receiver=me)
    add_tx(TransactionType.TRANSFER, "300", sender=me, receiver=other, description="rent")
    add_tx(TransactionType.DEPOSIT, "777", receiver=me, status="pending")      # not money yet
    add_tx(TransactionType.TRANSFER, "5", sender=other, receiver=third)        # not mine
    headers = login(client)

    body = client.get("/statements", headers=headers).json()

    assert body["count"] == 3
    assert Decimal(body["total_in"]) == Decimal("1000")
    assert Decimal(body["total_out"]) == Decimal("300")
    assert {i["direction"] for i in body["items"]} == {"credit", "debit"}
    sent = next(i for i in body["items"] if i["description"] == "rent")
    assert sent["counterparty"] == "Test User"
    assert balance(me) == Decimal("50.00")  # reading a statement changes nothing


def test_statement_date_filter_uses_nigerian_days(client):
    me = make_user()
    # 23:30 UTC on 10 March is 00:30 on 11 March in Nigeria.
    add_tx(TransactionType.DEPOSIT, "10", receiver=me, when=datetime(2026, 3, 10, 23, 30, tzinfo=timezone.utc), description="late")
    add_tx(TransactionType.DEPOSIT, "20", receiver=me, when=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc), description="noon")
    headers = login(client)

    day10 = client.get("/statements", headers=headers, params={"start": "2026-03-10", "end": "2026-03-10"}).json()
    day11 = client.get("/statements", headers=headers, params={"start": "2026-03-11", "end": "2026-03-11"}).json()

    assert [i["description"] for i in day10["items"]] == ["noon"]
    assert [i["description"] for i in day11["items"]] == ["late"]


def test_statement_rejects_backwards_or_huge_ranges(client):
    make_user()
    headers = login(client)
    assert client.get("/statements", headers=headers, params={"start": "2026-03-10", "end": "2026-03-01"}).status_code == 400
    assert client.get("/statements", headers=headers, params={"start": "2000-01-01", "end": "2026-03-01"}).status_code == 400
    assert client.get("/statements", headers=headers, params={"start": "not-a-date"}).status_code == 422


def test_statement_csv_downloads_and_defuses_spreadsheet_formulas(client):
    me = make_user()
    add_tx(TransactionType.DEPOSIT, "1000", receiver=me, description='=HYPERLINK("http://evil.example","click")')
    headers = login(client)

    response = client.get("/statements/csv", headers=headers, params={"start": "2026-03-01", "end": "2026-03-31"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    text = response.content.decode("utf-8-sig")
    assert "Date (WAT),Reference,Type" in text
    assert "SB-0000" in text
    assert "'=HYPERLINK" in text           # neutralised
    assert ",=HYPERLINK" not in text


def test_statements_need_a_login(client):
    assert client.get("/statements").status_code == 401
    assert client.get("/statements/csv").status_code == 401
    assert client.get("/transactions/1/receipt").status_code == 401


# ---------------------------------------------------------------- receipts

def test_receipt_for_my_transfer_and_masked_for_the_receiver(client):
    me = make_user()
    other = make_user(email="bola@example.com")
    tx_id = add_tx(TransactionType.TRANSFER, "300", sender=me, receiver=other, description="rent")

    mine = client.get(f"/transactions/{tx_id}/receipt", headers=login(client)).json()
    theirs = client.get(f"/transactions/{tx_id}/receipt", headers=login(client, "bola@example.com")).json()

    assert mine["reference"] == f"SB-{tx_id:08d}"
    assert mine["direction"] == "debit"
    assert mine["other_party"]["account_number"].isdigit()           # sender sees the number they used
    assert theirs["direction"] == "credit"
    assert theirs["other_party"]["account_number"].startswith("******")  # receiver sees only the end


def test_nobody_can_read_someone_elses_receipt(client):
    me = make_user()
    other = make_user(email="bola@example.com")
    make_user(email="spy@example.com")
    tx_id = add_tx(TransactionType.TRANSFER, "300", sender=me, receiver=other)

    assert client.get(f"/transactions/{tx_id}/receipt", headers=login(client, "spy@example.com")).status_code == 404
    assert client.get("/transactions/99999/receipt", headers=login(client)).status_code == 404

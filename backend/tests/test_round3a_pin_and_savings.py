"""Round 3A: transaction PIN (lockout, enforcement) and Save4Me savings pots.
Pots only ever move a user's own money between wallet and pot: the total never changes."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models.savings import SavingsMovement, SavingsPot
from app.models.transaction import Transaction
from app.models.user import User

from tests.conftest import PASSWORD, make_user
from tests.test_round1_account_features import login
from tests.test_round2_features import account_of, balance, tx_count

PIN = "4821"


def with_pin(headers, pin=PIN):
    return {**headers, "X-Transaction-Pin": pin}


def set_pin(client, headers, pin=PIN, password=PASSWORD):
    return client.post("/account/pin", headers=headers, json={"password": password, "new_pin": pin})


def transfer(client, headers, to_account, amount="10.00"):
    return client.post("/transactions/transfer", headers=headers,
                       json={"recipient_account_number": to_account, "amount": amount})


def detail(response):
    return response.json()["detail"]


# ------------------------------------------------------------------ PIN setup

def test_setting_a_pin_needs_the_account_password_and_a_valid_pin(client):
    make_user()
    headers = login(client)

    assert set_pin(client, headers, password="not-my-password").status_code == 400
    assert set_pin(client, headers, pin="12").status_code == 422
    assert set_pin(client, headers, pin="abcd").status_code == 422
    assert set_pin(client, headers, pin="1234567").status_code == 422
    assert client.get("/account/profile", headers=headers).json()["has_pin"] is False

    ok = set_pin(client, headers)
    assert ok.status_code == 200 and ok.json()["has_pin"] is True
    assert "transaction_pin_hash" not in ok.json() and PIN not in str(ok.json())  # never returned


def test_pin_is_stored_hashed(client):
    user_id = make_user()
    set_pin(client, login(client))
    with SessionLocal() as db:
        stored = db.query(User).filter(User.id == user_id).one().transaction_pin_hash
    assert stored and PIN not in stored


# ------------------------------------------------------------------ PIN enforcement

def test_without_a_pin_set_sending_money_still_works(client):
    make_user(balance="100.00")
    other = make_user(email="bola@example.com")
    assert transfer(client, login(client), account_of(other)).status_code == 201


def test_once_a_pin_is_set_transfers_need_it(client):
    make_user(balance="100.00")
    other = make_user(email="bola@example.com")
    headers = login(client)
    set_pin(client, headers)

    missing = transfer(client, headers, account_of(other))
    wrong = transfer(client, with_pin(headers, "0000"), account_of(other))
    assert missing.status_code == 428 and detail(missing) == "PIN_REQUIRED"
    assert wrong.status_code == 403 and detail(wrong) == "PIN_INVALID|4"
    assert tx_count() == 0

    right = transfer(client, with_pin(headers), account_of(other))
    assert right.status_code == 201
    assert tx_count() == 1


def test_pin_also_guards_saved_payments_withdrawals_and_fixed_deposits(client):
    user_id = make_user(balance="500.00")
    other = make_user(email="bola@example.com")
    headers = login(client)
    saved_id = client.post("/saved-payments", headers=headers, json={
        "label": "Rent", "recipient_account_number": account_of(other), "amount": "10.00"}).json()["id"]
    set_pin(client, headers)

    assert client.post(f"/saved-payments/{saved_id}/pay", headers=headers).status_code == 428
    assert client.post("/transactions/withdraw", headers=headers, json={"amount": "10.00"}).status_code == 428
    assert client.post("/fixed-deposits", headers=headers, json={"principal_amount": "100.00", "term_days": 30}).status_code == 428
    assert tx_count() == 0
    assert balance(user_id) == Decimal("500.00")  # the refused fixed deposit took nothing
    assert client.post(f"/saved-payments/{saved_id}/pay", headers=with_pin(headers)).status_code == 201


def test_wrong_attempts_are_counted_across_requests_and_five_lock_the_pin(client):
    make_user(balance="100.00")
    other = make_user(email="bola@example.com")
    headers = login(client)
    set_pin(client, headers)
    bad = with_pin(headers, "0000")

    remaining = [detail(transfer(client, bad, account_of(other))) for _ in range(4)]
    assert remaining == ["PIN_INVALID|4", "PIN_INVALID|3", "PIN_INVALID|2", "PIN_INVALID|1"]

    fifth = transfer(client, bad, account_of(other))
    assert fifth.status_code == 429 and detail(fifth).startswith("PIN_LOCKED|")

    # Even the CORRECT pin is refused while locked.
    locked = transfer(client, with_pin(headers), account_of(other))
    assert locked.status_code == 429
    assert tx_count() == 0


def test_lock_expires_and_a_correct_pin_resets_the_counter(client):
    user_id = make_user(balance="100.00")
    other = make_user(email="bola@example.com")
    headers = login(client)
    set_pin(client, headers)
    for _ in range(5):
        transfer(client, with_pin(headers, "0000"), account_of(other))
    with SessionLocal() as db:  # pretend 16 minutes passed
        db.query(User).filter(User.id == user_id).one().pin_locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    assert transfer(client, with_pin(headers), account_of(other)).status_code == 201
    # the counter was reset: a fresh wrong try starts from 4 left again
    assert detail(transfer(client, with_pin(headers, "0000"), account_of(other), amount="1.00")) == "PIN_INVALID|4"


def test_changing_the_pin_needs_the_password_even_when_logged_in(client):
    make_user()
    headers = login(client)
    set_pin(client, headers)
    assert set_pin(client, headers, pin="9999", password="stolen-session-no-password").status_code == 400
    assert set_pin(client, headers, pin="9999").status_code == 200


# ------------------------------------------------------------------ Save4Me

def make_pot(client, headers, name="Rent", target=None):
    body = {"name": name}
    if target:
        body["target_amount"] = target
    return client.post("/savings/pots", headers=headers, json=body)


def pot_total():
    with SessionLocal() as db:
        return sum((p.balance for p in db.query(SavingsPot).all()), Decimal("0"))


def setup_user_with_pin(client, balance="100.00"):
    user_id = make_user(balance=balance)
    headers = login(client)
    set_pin(client, headers)
    return user_id, with_pin(headers)


def test_savings_moves_need_a_pin_even_if_transfers_do_not(client):
    make_user(balance="100.00")
    headers = login(client)
    pot_id = make_pot(client, headers).json()["id"]

    no_pin_set = client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": "10.00"})
    assert no_pin_set.status_code == 428 and detail(no_pin_set) == "PIN_NOT_SET"

    set_pin(client, headers)
    needs_it = client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": "10.00"})
    assert needs_it.status_code == 428 and detail(needs_it) == "PIN_REQUIRED"
    assert pot_total() == Decimal("0")


def test_deposit_and_withdraw_move_only_the_users_own_money(client):
    user_id, headers = setup_user_with_pin(client, "100.00")
    pot_id = make_pot(client, headers, target="500.00").json()["id"]

    dep = client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": "40.00"})
    assert dep.status_code == 200, dep.text
    assert Decimal(dep.json()["pot"]["balance"]) == Decimal("40.00")
    assert Decimal(dep.json()["wallet_balance"]) == Decimal("60.00")
    assert balance(user_id) + pot_total() == Decimal("100.00")

    out = client.post(f"/savings/pots/{pot_id}/withdraw", headers=headers, json={"amount": "15.00"})
    assert Decimal(out.json()["pot"]["balance"]) == Decimal("25.00")
    assert balance(user_id) + pot_total() == Decimal("100.00")

    listing = client.get("/savings/pots", headers=headers).json()
    assert Decimal(listing["total_saved"]) == Decimal("25.00")
    moves = client.get(f"/savings/pots/{pot_id}/movements", headers=headers).json()
    assert [(m["kind"], Decimal(m["amount"])) for m in moves] == [("out", Decimal("15.00")), ("in", Decimal("40.00"))]


def test_cannot_save_more_than_the_wallet_or_take_more_than_the_pot(client):
    user_id, headers = setup_user_with_pin(client, "100.00")
    pot_id = make_pot(client, headers).json()["id"]

    assert client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": "100.01"}).status_code == 400
    assert client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": "100.00"}).status_code == 200
    assert client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": "0.01"}).status_code == 400  # wallet empty
    assert client.post(f"/savings/pots/{pot_id}/withdraw", headers=headers, json={"amount": "100.01"}).status_code == 400
    assert balance(user_id) == Decimal("0.00") and pot_total() == Decimal("100.00")


def test_bad_amounts_are_refused(client):
    user_id, headers = setup_user_with_pin(client, "100.00")
    pot_id = make_pot(client, headers).json()["id"]
    for amount in ("0", "-5", "abc", "1.005"):
        r = client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": amount})
        assert r.status_code == 422, (amount, r.status_code)
    assert balance(user_id) == Decimal("100.00") and pot_total() == Decimal("0")


def test_money_in_a_pot_cannot_be_sent_as_a_transfer(client):
    _, headers = setup_user_with_pin(client, "100.00")
    other = make_user(email="bola@example.com")
    pot_id = make_pot(client, headers).json()["id"]
    client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": "90.00"})

    response = transfer(client, headers, account_of(other), amount="50.00")

    assert response.status_code == 400 and detail(response) == "Insufficient balance"
    assert tx_count() == 0


def test_closing_a_pot_returns_everything_and_a_closed_pot_is_finished(client):
    user_id, headers = setup_user_with_pin(client, "100.00")
    pot_id = make_pot(client, headers).json()["id"]
    client.post(f"/savings/pots/{pot_id}/deposit", headers=headers, json={"amount": "70.00"})

    closed = client.post(f"/savings/pots/{pot_id}/close", headers=headers)

    assert closed.status_code == 200
    assert closed.json()["pot"]["status"] == "closed"
    assert balance(user_id) == Decimal("100.00") and pot_total() == Decimal("0")
    assert client.get("/savings/pots", headers=headers).json()["pots"] == []
    for path in ("deposit", "withdraw"):
        assert client.post(f"/savings/pots/{pot_id}/{path}", headers=headers, json={"amount": "1.00"}).status_code == 409
    assert client.post(f"/savings/pots/{pot_id}/close", headers=headers).status_code == 409


def test_nobody_can_touch_someone_elses_pot(client):
    make_user(balance="100.00")
    owner = login(client)
    set_pin(client, owner)
    pot_id = make_pot(client, owner).json()["id"]
    make_user(email="spy@example.com", balance="100.00")
    spy = login(client, "spy@example.com")
    set_pin(client, spy)
    spy = with_pin(spy)

    for path, body in (("deposit", {"amount": "1.00"}), ("withdraw", {"amount": "1.00"}), ("close", None)):
        r = client.post(f"/savings/pots/{pot_id}/{path}", headers=spy, json=body) if body else client.post(f"/savings/pots/{pot_id}/{path}", headers=spy)
        assert r.status_code == 404, path
    assert client.get(f"/savings/pots/{pot_id}/movements", headers=spy).status_code == 404
    assert client.get("/savings/pots", headers=spy).json()["pots"] == []
    assert pot_total() == Decimal("0")


def test_pot_limit(client):
    make_user()
    headers = login(client)
    codes = [make_pot(client, headers, name=f"Pot {i}").status_code for i in range(11)]
    assert codes[:10] == [201] * 10 and codes[10] == 400


def test_many_moves_never_change_the_total(client):
    user_id, headers = setup_user_with_pin(client, "1000.00")
    a = make_pot(client, headers, name="A").json()["id"]
    b = make_pot(client, headers, name="B").json()["id"]
    steps = [(a, "deposit", "123.45"), (b, "deposit", "300.00"), (a, "withdraw", "23.45"),
             (b, "deposit", "999.00"), (b, "withdraw", "50.55"), (a, "deposit", "0.01"), (a, "close", None)]
    for pot_id, op, amount in steps:
        client.post(f"/savings/pots/{pot_id}/{op}", headers=headers, **({"json": {"amount": amount}} if amount else {}))
        assert balance(user_id) + pot_total() == Decimal("1000.00"), (pot_id, op, amount)
    with SessionLocal() as db:
        in_ = sum((m.amount for m in db.query(SavingsMovement).filter(SavingsMovement.kind == "in")), Decimal("0"))
        out = sum((m.amount for m in db.query(SavingsMovement).filter(SavingsMovement.kind == "out")), Decimal("0"))
    assert in_ - out == pot_total()

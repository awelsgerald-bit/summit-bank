"""Round 3B: scheduled / recurring transfers and referrals.
Scheduled transfers create ordinary PENDING transfers, at most once per due time. Referral bonuses
are ordinary PENDING deposits that an admin approves."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.config import settings
from app.database import SessionLocal
from app.models.referral import ReferralReward
from app.models.scheduled_transfer import ScheduledTransfer, ScheduledTransferRun
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services import email_service, referral_service, scheduled_transfer_service as sts

from tests.conftest import PASSWORD, make_user
from tests.test_round1_account_features import add_tx, login
from tests.test_round2_features import account_of, balance, tx_count
from tests.test_round3a_pin_and_savings import detail, set_pin, with_pin


def utc_now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.isoformat()


def new_schedule(client, headers, to_account, amount="25.00", frequency="weekly", start=None, end=None):
    body = {
        "recipient_account_number": to_account, "amount": amount, "frequency": frequency,
        "first_run_at": iso(start or utc_now() + timedelta(hours=1)), "description": "rent",
    }
    if end:
        body["end_at"] = iso(end)
    return client.post("/scheduled-transfers", headers=headers, json=body)


def sender_with_pin(client, balance_="500.00"):
    user_id = make_user(balance=balance_)
    other = make_user(email="bola@example.com")
    headers = login(client)
    set_pin(client, headers)
    return user_id, account_of(other), with_pin(headers)


def schedule_row(schedule_id):
    with SessionLocal() as db:
        row = db.query(ScheduledTransfer).filter(ScheduledTransfer.id == schedule_id).one()
        db.expunge(row)
        return row


def run_at(when):
    with SessionLocal() as db:
        return sts.run_due(db, now=when)


def runs(schedule_id):
    with SessionLocal() as db:
        return db.query(ScheduledTransferRun).filter(ScheduledTransferRun.schedule_id == schedule_id).all()


def aware(ts):
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


# ================================================================== scheduled transfers

def test_a_schedule_needs_the_pin(client):
    make_user(balance="500.00")
    other = make_user(email="bola@example.com")
    headers = login(client)

    no_pin_set = new_schedule(client, headers, account_of(other))
    assert no_pin_set.status_code == 428 and detail(no_pin_set) == "PIN_NOT_SET"

    set_pin(client, headers)
    missing = new_schedule(client, headers, account_of(other))
    assert missing.status_code == 428 and detail(missing) == "PIN_REQUIRED"
    assert new_schedule(client, with_pin(headers, "0000"), account_of(other)).status_code == 403
    assert new_schedule(client, with_pin(headers), account_of(other)).status_code == 201


def test_schedule_validation(client):
    user_id, other, headers = sender_with_pin(client)
    own = account_of(user_id)

    assert new_schedule(client, headers, other, start=utc_now() - timedelta(minutes=5)).status_code == 400   # the past
    assert new_schedule(client, headers, "0000000000").status_code == 404                                  # no such account
    assert new_schedule(client, headers, own).status_code == 400                                           # to yourself
    assert new_schedule(client, headers, other, frequency="hourly").status_code == 400
    assert new_schedule(client, headers, other, amount="0").status_code == 422
    start = utc_now() + timedelta(days=2)
    assert new_schedule(client, headers, other, start=start, end=start - timedelta(days=1)).status_code == 400
    codes = [new_schedule(client, headers, other).status_code for _ in range(11)]
    assert codes[:10] == [201] * 10 and codes[10] == 400                                                    # limit of 10


def test_a_naive_time_means_nigerian_time(client):
    _, other, headers = sender_with_pin(client)
    local = (utc_now() + timedelta(hours=3)).astimezone(timezone(timedelta(hours=1))).replace(tzinfo=None, microsecond=0)

    response = client.post("/scheduled-transfers", headers=headers, json={
        "recipient_account_number": other, "amount": "10.00", "frequency": "once", "first_run_at": local.isoformat()})

    assert response.status_code == 201, response.text
    stored = aware(schedule_row(response.json()["id"]).next_run_at)
    assert stored == local.replace(tzinfo=timezone(timedelta(hours=1))).astimezone(timezone.utc)


def test_a_one_off_transfer_runs_once_as_a_pending_transfer(client):
    user_id, other, headers = sender_with_pin(client, "500.00")
    schedule = new_schedule(client, headers, other, frequency="once").json()
    due = aware(schedule_row(schedule["id"]).next_run_at)

    assert run_at(due - timedelta(minutes=1))["due"] == 0 and tx_count() == 0   # not yet
    first = run_at(due + timedelta(minutes=1))
    again = run_at(due + timedelta(minutes=2))

    assert first["created"] == 1 and again["due"] == 0
    assert tx_count() == 1
    with SessionLocal() as db:
        tx = db.query(Transaction).one()
        assert tx.status == "pending" and tx.amount == Decimal("25.00") and tx.sender_id == user_id
    assert balance(user_id) == Decimal("500.00")                                 # nothing moves until an admin approves
    assert schedule_row(schedule["id"]).status == "completed"
    assert [r.outcome for r in runs(schedule["id"])] == ["created"]


def test_two_runners_racing_for_the_same_due_time_send_once(client):
    _, other, headers = sender_with_pin(client)
    schedule_id = new_schedule(client, headers, other, frequency="daily").json()["id"]
    due_raw = schedule_row(schedule_id).next_run_at
    now = aware(due_raw) + timedelta(minutes=1)

    with SessionLocal() as one, SessionLocal() as two:
        results = [sts._run_one(one, schedule_id, due_raw, now), sts._run_one(two, schedule_id, due_raw, now)]

    assert sorted(results) == ["created", "skipped"]
    assert tx_count() == 1 and len(runs(schedule_id)) == 1


def test_recurring_schedule_moves_on_and_never_bursts_after_downtime(client):
    _, other, headers = sender_with_pin(client)
    schedule_id = new_schedule(client, headers, other, frequency="daily").json()["id"]
    due = aware(schedule_row(schedule_id).next_run_at)

    run_at(due + timedelta(minutes=1))
    assert tx_count() == 1
    assert aware(schedule_row(schedule_id).next_run_at) == due + timedelta(days=1)

    # The server was off for a month: ONE transfer, the missed days are skipped.
    later = due + timedelta(days=31)
    run_at(later)
    assert tx_count() == 2
    nxt = aware(schedule_row(schedule_id).next_run_at)
    assert nxt > later and nxt - later <= timedelta(days=1)
    assert any("skipped" in (r.detail or "") for r in runs(schedule_id))
    run_at(later + timedelta(minutes=1))
    assert tx_count() == 2


def test_a_failed_run_is_recorded_emailed_and_does_not_loop(client, monkeypatch):
    sent = []
    monkeypatch.setattr(email_service, "send_email", lambda to, subject, body: sent.append((to, subject, body)))
    user_id, other, headers = sender_with_pin(client, "10.00")   # needs 25
    schedule_id = new_schedule(client, headers, other, frequency="weekly").json()["id"]
    due = aware(schedule_row(schedule_id).next_run_at)

    result = run_at(due + timedelta(minutes=1))
    run_at(due + timedelta(minutes=2))
    run_at(due + timedelta(minutes=3))

    assert result["failed"] == 1
    assert tx_count() == 0
    row = schedule_row(schedule_id)
    assert row.status == "active" and row.last_status == "failed" and "Insufficient" in row.last_error
    assert aware(row.next_run_at) == due + timedelta(days=7)          # waits for next week, no retry loop
    assert [r.outcome for r in runs(schedule_id)] == ["failed"]
    assert [to for to, _, _ in sent] == ["ada@example.com"]

    with SessionLocal() as db:                                          # topped up: next week's run works
        db.query(User).filter(User.id == user_id).one().balance = Decimal("100.00")
        db.commit()
    assert run_at(due + timedelta(days=7, minutes=1))["created"] == 1


def test_end_date_completes_the_schedule(client):
    _, other, headers = sender_with_pin(client)
    start = utc_now() + timedelta(hours=1)
    schedule_id = new_schedule(client, headers, other, frequency="weekly", start=start, end=start + timedelta(days=10)).json()["id"]
    due = aware(schedule_row(schedule_id).next_run_at)

    run_at(due + timedelta(minutes=1))
    assert schedule_row(schedule_id).status == "active"
    run_at(due + timedelta(days=7, minutes=1))      # the next one would fall after the end date
    assert schedule_row(schedule_id).status == "completed"
    assert tx_count() == 2
    run_at(due + timedelta(days=30))
    assert tx_count() == 2


def test_pause_resume_and_cancel(client):
    _, other, headers = sender_with_pin(client)
    schedule_id = new_schedule(client, headers, other, frequency="daily").json()["id"]
    due = aware(schedule_row(schedule_id).next_run_at)

    assert client.post(f"/scheduled-transfers/{schedule_id}/pause", headers=headers).json()["status"] == "paused"
    run_at(due + timedelta(days=3))
    assert tx_count() == 0                                              # paused: nothing runs

    no_pin = client.post(f"/scheduled-transfers/{schedule_id}/resume", headers={k: v for k, v in headers.items() if k != "X-Transaction-Pin"})
    assert no_pin.status_code == 428                                    # resuming re-authorises
    resumed = client.post(f"/scheduled-transfers/{schedule_id}/resume", headers=headers)
    assert resumed.status_code == 200 and resumed.json()["status"] == "active"
    assert aware(schedule_row(schedule_id).next_run_at) > utc_now()    # the missed days were skipped, not replayed
    assert tx_count() == 0

    assert client.post(f"/scheduled-transfers/{schedule_id}/cancel", headers=headers).json()["status"] == "cancelled"
    run_at(utc_now() + timedelta(days=30))
    assert tx_count() == 0
    assert client.post(f"/scheduled-transfers/{schedule_id}/resume", headers=headers).status_code == 409


def test_nobody_can_manage_someone_elses_schedule(client):
    _, other, headers = sender_with_pin(client)
    schedule_id = new_schedule(client, headers, other).json()["id"]
    make_user(email="spy@example.com")
    spy = login(client, "spy@example.com")

    for action in ("pause", "resume", "cancel"):
        assert client.post(f"/scheduled-transfers/{schedule_id}/{action}", headers=spy).status_code in (404, 428)
    set_pin(client, spy)
    spy = with_pin(spy)
    for action in ("pause", "resume", "cancel"):
        assert client.post(f"/scheduled-transfers/{schedule_id}/{action}", headers=spy).status_code == 404
    assert client.get(f"/scheduled-transfers/{schedule_id}/runs", headers=spy).status_code == 404
    assert client.get("/scheduled-transfers", headers=spy).json() == []
    assert schedule_row(schedule_id).status == "active"


def test_monthly_dates_stay_on_the_right_day():
    jan31 = datetime(2027, 1, 31, 9, 0, tzinfo=timezone(timedelta(hours=1))).astimezone(timezone.utc)
    feb = sts.advance(jan31, "monthly", 31)
    mar = sts.advance(feb, "monthly", 31)
    dec = datetime(2027, 12, 15, 9, 0, tzinfo=timezone.utc)
    jan = sts.advance(dec, "monthly", 15)
    wat = timezone(timedelta(hours=1))
    assert feb.astimezone(wat).day == 28 and feb.astimezone(wat).month == 2
    assert mar.astimezone(wat).day == 31 and mar.astimezone(wat).month == 3     # back to the 31st, no drift
    assert (jan.year, jan.month, jan.day) == (2028, 1, 15)


def test_opening_the_app_runs_my_due_transfers(client):
    user_id, other, headers = sender_with_pin(client)
    schedule_id = new_schedule(client, headers, other, frequency="once").json()["id"]
    with SessionLocal() as db:   # time passes: it is now overdue
        db.query(ScheduledTransfer).filter(ScheduledTransfer.id == schedule_id).one().next_run_at = utc_now() - timedelta(minutes=5)
        db.commit()

    assert client.get("/account/profile", headers=headers).status_code == 200

    assert tx_count() == 1


def test_the_outside_timer_endpoint_is_locked_down(client, monkeypatch):
    monkeypatch.setattr(settings, "cron_token", "")
    assert client.post("/internal/run-schedules").status_code == 404           # off by default
    monkeypatch.setattr(settings, "cron_token", "a-long-secret-token-for-tests")
    assert client.post("/internal/run-schedules").status_code == 401
    assert client.post("/internal/run-schedules", headers={"X-Cron-Token": "wrong"}).status_code == 401
    ok = client.post("/internal/run-schedules", headers={"X-Cron-Token": "a-long-secret-token-for-tests"})
    assert ok.status_code == 200 and ok.json()["due"] == 0


def test_scheduled_transfer_still_needs_admin_approval_and_credits_once(client):
    user_id, other, headers = sender_with_pin(client, "500.00")
    receiver_id = 2
    make_user(email="admin@example.com", role="admin")
    schedule_id = new_schedule(client, headers, other, frequency="once", amount="40.00").json()["id"]
    run_at(aware(schedule_row(schedule_id).next_run_at) + timedelta(minutes=1))
    with SessionLocal() as db:
        tx_id = db.query(Transaction).one().id
    admin = login(client, "admin@example.com")

    assert client.post(f"/admin/transactions/{tx_id}/approve", headers=admin).status_code == 200
    assert client.post(f"/admin/transactions/{tx_id}/approve", headers=admin).status_code == 409

    assert balance(user_id) == Decimal("460.00") and balance(receiver_id) == Decimal("90.00")


# ================================================================== referrals

def register(client, email="new@example.com", code=None):
    body = {"full_name": "New Person", "email": email, "password": PASSWORD, "phone_number": "08031234567"}
    if code is not None:
        body["referral_code"] = code
    return client.post("/auth/register", json=body)


def admin_headers(client):
    make_user(email="admin@example.com", role="admin")
    return login(client, "admin@example.com")


def referrer_code(client, email="ada@example.com"):
    return client.get("/referrals/me", headers=login(client, email)).json()["code"]


def user_id_of(email):
    with SessionLocal() as db:
        return db.query(User).filter(User.email == email).one().id


def approve(client, admin, tx_id):
    response = client.post(f"/admin/transactions/{tx_id}/approve", headers=admin)
    assert response.status_code == 200, response.text


def pending_deposit(user_id, amount="6000.00"):
    return add_tx(TransactionType.DEPOSIT, amount, receiver=user_id, status="pending", description="deposit")


def reward_count():
    with SessionLocal() as db:
        return db.query(ReferralReward).count()


def test_everyone_gets_a_stable_referral_code(client):
    make_user()
    first = referrer_code(client)
    assert first.startswith("SB") and len(first) == 8
    assert referrer_code(client) == first


def test_signup_with_a_code(client):
    make_user()
    code = referrer_code(client)

    ok = register(client, code=code.lower())
    assert ok.status_code == 201, ok.text
    with SessionLocal() as db:
        assert db.query(User).filter(User.email == "new@example.com").one().referred_by_user_id == user_id_of("ada@example.com")

    bad = register(client, email="other@example.com", code="SBNOPE99")
    assert bad.status_code == 400
    with SessionLocal() as db:
        assert db.query(User).filter(User.email == "other@example.com").first() is None   # no half-made account
    assert register(client, email="plain@example.com").status_code == 201                  # a code is optional
    assert register(client, email="blank@example.com", code="  ").status_code == 201


def test_qualifying_first_deposit_creates_two_pending_bonuses_that_an_admin_approves(client):
    make_user()
    code = referrer_code(client)
    register(client, code=code)
    new_id, ref_id = user_id_of("new@example.com"), user_id_of("ada@example.com")
    admin = admin_headers(client)

    approve(client, admin, pending_deposit(new_id, "6000.00"))

    assert reward_count() == 1
    assert balance(new_id) == Decimal("6000.00")                    # the bonus is NOT credited automatically
    assert balance(ref_id) == Decimal("50.00")
    with SessionLocal() as db:
        bonuses = db.query(Transaction).filter(Transaction.description.like("%bonus%")).all()
        assert len(bonuses) == 2 and {b.status for b in bonuses} == {"pending"}
        assert {b.receiver_id for b in bonuses} == {new_id, ref_id}
        assert all(b.amount == Decimal("500") for b in bonuses)
        assert any("New Person" in b.description for b in bonuses)   # the admin can see who invited whom
        ids = [b.id for b in bonuses]
    for tx_id in ids:
        approve(client, admin, tx_id)

    assert balance(new_id) == Decimal("6500.00") and balance(ref_id) == Decimal("550.00")
    assert reward_count() == 1 and tx_count() == 3                  # bonuses never trigger more bonuses


def test_small_or_repeat_deposits_and_unreferred_users_earn_nothing(client):
    make_user()
    register(client, code=referrer_code(client))
    register(client, email="solo@example.com")                      # nobody referred this one
    new_id, solo_id = user_id_of("new@example.com"), user_id_of("solo@example.com")
    admin = admin_headers(client)

    approve(client, admin, pending_deposit(new_id, "4999.99"))      # just under the minimum
    approve(client, admin, pending_deposit(solo_id, "9000.00"))
    assert reward_count() == 0

    approve(client, admin, pending_deposit(new_id, "5000.00"))      # exactly the minimum qualifies
    approve(client, admin, pending_deposit(new_id, "8000.00"))      # a second one does not pay again
    assert reward_count() == 1
    with SessionLocal() as db:
        assert db.query(Transaction).filter(Transaction.description.like("%bonus%")).count() == 2


def test_rejected_deposit_earns_nothing(client):
    make_user()
    register(client, code=referrer_code(client))
    admin = admin_headers(client)
    tx_id = pending_deposit(user_id_of("new@example.com"))

    assert client.post(f"/admin/transactions/{tx_id}/reject", headers=admin).status_code == 200

    assert reward_count() == 0


def test_the_same_deposit_cannot_pay_twice(client):
    make_user()
    register(client, code=referrer_code(client))
    admin = admin_headers(client)
    tx_id = pending_deposit(user_id_of("new@example.com"))
    approve(client, admin, tx_id)

    with SessionLocal() as db:
        tx = db.query(Transaction).filter(Transaction.id == tx_id).one()
        assert referral_service.on_deposit_approved(db, tx) is None

    assert reward_count() == 1
    with SessionLocal() as db:
        assert db.query(Transaction).filter(Transaction.description.like("%bonus%")).count() == 2


def test_a_referrer_has_a_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "referral_max_rewards_per_user", 1)
    make_user()
    code = referrer_code(client)
    register(client, email="one@example.com", code=code)
    register(client, email="two@example.com", code=code)
    admin = admin_headers(client)

    approve(client, admin, pending_deposit(user_id_of("one@example.com")))
    approve(client, admin, pending_deposit(user_id_of("two@example.com")))

    assert reward_count() == 1


def test_a_failing_bonus_step_never_blocks_the_approval(client, monkeypatch):
    make_user()
    register(client, code=referrer_code(client))
    new_id = user_id_of("new@example.com")
    admin = admin_headers(client)

    def boom(db, tx):
        raise RuntimeError("bonus step exploded")

    monkeypatch.setattr(referral_service, "on_deposit_approved", boom)
    approve(client, admin, pending_deposit(new_id, "6000.00"))

    assert balance(new_id) == Decimal("6000.00")
    assert reward_count() == 0


def test_referral_page_data_shows_progress_with_hidden_names(client):
    make_user()
    code = referrer_code(client)
    register(client, code=code)
    admin = admin_headers(client)
    mine = login(client, "ada@example.com")

    before = client.get("/referrals/me", headers=mine).json()
    assert before["invited_count"] == 1 and before["items"][0]["state"] == "waiting"
    assert before["items"][0]["name"] == "New P***"
    assert Decimal(before["bonus_amount"]) == Decimal("500") and Decimal(before["earned"]) == 0

    approve(client, admin, pending_deposit(user_id_of("new@example.com")))
    assert client.get("/referrals/me", headers=mine).json()["items"][0]["state"] == "pending"

    with SessionLocal() as db:
        bonus_id = db.query(Transaction).filter(Transaction.receiver_id == user_id_of("ada@example.com"), Transaction.description.like("%bonus%")).one().id
    approve(client, admin, bonus_id)
    after = client.get("/referrals/me", headers=mine).json()
    assert after["items"][0]["state"] == "approved" and Decimal(after["earned"]) == Decimal("500")
    assert client.get("/referrals/me").status_code == 401

"""
Test setup. The tests run against a throw-away SQLite file and a fake StroWallet; they never
touch your real database or the real StroWallet.

SAFETY: the settings below are forced (not "set if missing") BEFORE the app is imported, so a
real backend/.env cannot point the tests at a real database. A check at the bottom stops the
whole run if the database is not SQLite.
"""
import os
import sys
import tempfile
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_DB_FILE = os.path.join(tempfile.mkdtemp(prefix="summit-tests-"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
os.environ["SECRET_KEY"] = "test-secret-key-used-only-by-the-tests"
os.environ["STROWALLET_WEBHOOK_SECRET"] = "test-webhook-secret-0123456789"
os.environ["STROWALLET_PUBLIC_KEY"] = "pk_test_PUBLICKEY_for_tests_only"
os.environ["STROWALLET_BASE_URL"] = "https://strowallet.test/api"
os.environ["STROWALLET_VERIFY_AMOUNT"] = "transaction"
os.environ["RESEND_API_KEY"] = ""

import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.strowallet_account import StroWalletAccount  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import email_service, strowallet_verification_service  # noqa: E402

if not settings.database_url.startswith("sqlite"):
    raise RuntimeError("Refusing to run tests: DATABASE_URL is not the throw-away SQLite file.")

NOT_RECEIVED = '{"message":"Transaction not received.","status":400}'
VERIFIED_OK = '{"message":"Transaction received.","status":200}'
WEBHOOK_TOKEN = settings.strowallet_webhook_secret
PASSWORD = "a-long-test-password-123"

_counter = {"n": 0}


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def no_real_email(monkeypatch):
    monkeypatch.setattr(email_service, "send_email", lambda *a, **k: None)


@pytest.fixture
def client():
    return TestClient(app)


class FakeStroWallet:
    """Stands in for StroWallet's verify endpoint. Default answer: 'Transaction not received'
    (what StroWallet really says for a session it has never seen)."""

    def __init__(self):
        self.calls = []
        self.reply = (400, NOT_RECEIVED)

    def says_verified(self, body=VERIFIED_OK):
        self.reply = (200, body)

    def says_not_received(self):
        self.reply = (400, NOT_RECEIVED)

    def is_down(self):
        self.reply = httpx.ConnectTimeout("simulated timeout")

    def __call__(self, url, params=None, headers=None, timeout=None, **kwargs):
        self.calls.append({"url": url, "params": dict(params or {})})
        if isinstance(self.reply, Exception):
            raise self.reply
        status, text = self.reply
        return httpx.Response(status, text=text)


@pytest.fixture
def stro(monkeypatch):
    fake = FakeStroWallet()
    monkeypatch.setattr(strowallet_verification_service.httpx, "get", fake)
    return fake


_hash_cache = {}


def _hashed(password):
    """Password hashing is deliberately slow; hash each test password only once per run."""
    if password not in _hash_cache:
        _hash_cache[password] = hash_password(password)
    return _hash_cache[password]


def make_user(email="ada@example.com", role="user", balance="50.00", password=PASSWORD):
    _counter["n"] += 1
    with SessionLocal() as db:
        user = User(
            full_name="Test User",
            email=email,
            hashed_password=_hashed(password),
            account_number=f"90{_counter['n']:08d}",
            balance=Decimal(balance),
            role=role,
        )
        db.add(user)
        db.commit()
        return user.id


def make_account(user_id, number="2426237910", mode="live", status="active"):
    with SessionLocal() as db:
        account = StroWalletAccount(
            user_id=user_id, nuban_account_number=number, mode=mode, status=status,
            bank_name="Test Bank", account_name="Test User", provider="sterling",
        )
        db.add(account)
        db.commit()
        return account.id

"""Login: the email is matched ignoring capital letters (phone keyboards capitalise the first letter; the website also trims spaces),
and the profile still loads if the opportunistic background steps fail."""
from tests.conftest import PASSWORD, make_user


def test_login_ignores_email_case_and_spaces(client):
    make_user(email="ada@example.com")
    for typed in ("Ada@Example.com", "ADA@EXAMPLE.COM"):
        response = client.post("/auth/login", json={"email": typed, "password": PASSWORD})
        assert response.status_code == 200, (typed, response.text)


def test_wrong_password_is_still_refused(client):
    make_user(email="ada@example.com")
    response = client.post("/auth/login", json={"email": "Ada@Example.com", "password": "wrong-password-1"})
    assert response.status_code == 401


def test_profile_loads_even_if_background_steps_fail(client, monkeypatch):
    from app.services import fixed_deposit_service, scheduled_transfer_service

    make_user(email="ada@example.com")
    token = client.post("/auth/login", json={"email": "ada@example.com", "password": PASSWORD}).json()["access_token"]

    def boom(*a, **k):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(fixed_deposit_service, "credit_matured_deposits", boom)
    monkeypatch.setattr(scheduled_transfer_service, "run_due", boom)
    response = client.get("/account/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

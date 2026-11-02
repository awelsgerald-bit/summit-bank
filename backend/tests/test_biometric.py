"""Fingerprint / Face ID sign-in (WebAuthn). A small fake "phone" makes a real key pair and signs
real challenges, so the server's checks run for real."""
import hashlib
import json
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.core.config import settings
from app.database import SessionLocal
from app.models.webauthn import WebAuthnCredential
from app.services import webauthn_service as ws

from tests.conftest import PASSWORD, make_user
from tests.test_round1_account_features import login

ORIGIN = settings.allowed_origins[0].rstrip("/")  # e.g. http://localhost:5173
HOST = ORIGIN.split("://", 1)[1].split(":")[0]


class FakePhone:
    def __init__(self, origin=ORIGIN):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = ws.b64u_encode(secrets.token_bytes(24))
        self.origin = origin
        self.counter = 0

    def public_key(self):
        der = self.key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        return ws.b64u_encode(der)

    def client_data(self, kind, challenge, origin=None):
        return json.dumps({"type": kind, "challenge": challenge, "origin": origin or self.origin}).encode()

    def register_body(self, challenge, password=PASSWORD, origin=None):
        return {
            "password": password, "credential_id": self.credential_id, "public_key": self.public_key(),
            "algorithm": -7, "label": "Test phone",
            "client_data_json": ws.b64u_encode(self.client_data("webauthn.create", challenge, origin)),
        }

    def assertion(self, challenge, flags=0x05, rp_host=HOST, kind="webauthn.get", origin=None, counter=None, sign_with=None):
        self.counter = self.counter + 1 if counter is None else counter
        auth_data = hashlib.sha256(rp_host.encode()).digest() + bytes([flags]) + self.counter.to_bytes(4, "big")
        client = self.client_data(kind, challenge, origin)
        signature = (sign_with or self.key).sign(auth_data + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
        return {
            "credential_id": self.credential_id,
            "client_data_json": ws.b64u_encode(client),
            "authenticator_data": ws.b64u_encode(auth_data),
            "signature": ws.b64u_encode(signature),
        }


def enable(client, headers, phone=None):
    phone = phone or FakePhone()
    challenge = client.post("/biometric/register/challenge", headers=headers).json()["challenge"]
    response = client.post("/biometric/register", headers=headers, json=phone.register_body(challenge))
    assert response.status_code == 201, response.text
    return phone


def login_challenge(client):
    return client.post("/biometric/login/challenge").json()["challenge"]


def test_register_then_sign_in_with_fingerprint(client):
    make_user()
    headers = login(client)
    phone = enable(client, headers)
    assert len(client.get("/biometric/credentials", headers=headers).json()) == 1

    response = client.post("/biometric/login", json=phone.assertion(login_challenge(client)))
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    profile = client.get("/account/profile", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200 and profile.json()["email"] == "ada@example.com"


def test_registering_needs_login_and_the_account_password(client):
    make_user()
    assert client.post("/biometric/register/challenge").status_code == 401
    headers = login(client)
    phone = FakePhone()
    challenge = client.post("/biometric/register/challenge", headers=headers).json()["challenge"]
    response = client.post("/biometric/register", headers=headers, json=phone.register_body(challenge, password="wrong-password"))
    assert response.status_code == 400
    assert client.get("/biometric/credentials", headers=headers).json() == []


def test_registering_with_a_bad_challenge_or_origin_is_refused(client):
    make_user()
    headers = login(client)
    phone = FakePhone()
    assert client.post("/biometric/register", headers=headers, json=phone.register_body("not-a-real-challenge")).status_code == 400
    login_style = login_challenge(client)  # a sign-in challenge cannot be used to register
    assert client.post("/biometric/register", headers=headers, json=phone.register_body(login_style)).status_code == 400
    challenge = client.post("/biometric/register/challenge", headers=headers).json()["challenge"]
    body = phone.register_body(challenge, origin="https://evil.example")
    assert client.post("/biometric/register", headers=headers, json=body).status_code == 403


def test_a_wrong_key_cannot_sign_in(client):
    make_user()
    phone = enable(client, login(client))
    attacker = ec.generate_private_key(ec.SECP256R1())
    response = client.post("/biometric/login", json=phone.assertion(login_challenge(client), sign_with=attacker))
    assert response.status_code == 401


def test_sign_in_needs_user_verification(client):
    make_user()
    phone = enable(client, login(client))
    # flags 0x01 = present but the fingerprint/face was not checked
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), flags=0x01)).status_code == 401
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), flags=0x04)).status_code == 401


def test_challenges_must_be_ours_fresh_and_for_sign_in(client, monkeypatch):
    make_user()
    headers = login(client)
    phone = enable(client, headers)
    assert client.post("/biometric/login", json=phone.assertion("made-up-challenge")).status_code == 401
    register_challenge = client.post("/biometric/register/challenge", headers=headers).json()["challenge"]
    assert client.post("/biometric/login", json=phone.assertion(register_challenge)).status_code == 401

    old = login_challenge(client)
    real_time = ws.time.time
    monkeypatch.setattr(ws.time, "time", lambda: real_time() + ws.CHALLENGE_TTL_SECONDS + 5)
    assert client.post("/biometric/login", json=phone.assertion(old)).status_code == 401


def test_a_foreign_website_or_wrong_type_is_refused(client):
    make_user()
    phone = enable(client, login(client))
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), origin="https://evil.example")).status_code == 401
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), kind="webauthn.create")).status_code == 401
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), rp_host="evil.example")).status_code == 401


def test_the_signature_counter_cannot_go_backwards(client):
    make_user()
    phone = enable(client, login(client))
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), counter=5)).status_code == 200
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), counter=5)).status_code == 401
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), counter=4)).status_code == 401
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client), counter=6)).status_code == 200


def test_an_unknown_device_is_refused(client):
    make_user()
    assert client.post("/biometric/login", json=FakePhone().assertion(login_challenge(client))).status_code == 401


def test_removing_a_device_stops_it_signing_in_and_you_cannot_remove_others(client):
    make_user()
    make_user(email="bola@example.com")
    ada = login(client)
    phone = enable(client, ada)
    cred_id = client.get("/biometric/credentials", headers=ada).json()[0]["id"]
    assert client.delete(f"/biometric/credentials/{cred_id}", headers=login(client, "bola@example.com")).status_code == 404
    assert client.delete(f"/biometric/credentials/{cred_id}", headers=ada).status_code == 200
    assert client.post("/biometric/login", json=phone.assertion(login_challenge(client))).status_code == 401


def test_the_same_device_cannot_be_registered_twice_and_there_is_a_limit(client):
    make_user()
    headers = login(client)
    phone = enable(client, headers)
    challenge = client.post("/biometric/register/challenge", headers=headers).json()["challenge"]
    assert client.post("/biometric/register", headers=headers, json=phone.register_body(challenge)).status_code == 409
    for _ in range(ws.MAX_CREDENTIALS_PER_USER - 1):
        enable(client, headers)
    challenge = client.post("/biometric/register/challenge", headers=headers).json()["challenge"]
    assert client.post("/biometric/register", headers=headers, json=FakePhone().register_body(challenge)).status_code == 400
    with SessionLocal() as db:
        assert db.query(WebAuthnCredential).count() == ws.MAX_CREDENTIALS_PER_USER

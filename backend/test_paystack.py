import requests

BASE_URL = "https://summit-bank-1.onrender.com"
EMAIL = "autotest@example.com"
PASSWORD = "strongpassword123"


def login():
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200
    return r.json()["access_token"]


def run():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initialize a payment
    r = requests.post(f"{BASE_URL}/payments/paystack/initialize", json={"amount": 5000}, headers=headers)
    print("Initialize:", r.status_code, r.json())
    assert r.status_code == 200
    data = r.json()
    assert "authorization_url" in data
    assert "reference" in data

    print("\nOpen this URL in a browser to complete a TEST payment:")
    print(data["authorization_url"])
    print("\nUse Paystack's test card: 4084 0840 8408 4081, any future expiry, CVV 408, any PIN/OTP if asked.")
    print(f"\nAfter paying, run: verify_after_payment('{data['reference']}')")


def verify_after_payment(reference):
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/payments/paystack/verify/{reference}", headers=headers)
    print("Verify:", r.status_code, r.json())


if __name__ == "__main__":
    run()
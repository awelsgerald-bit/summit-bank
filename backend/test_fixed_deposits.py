import requests
import time

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

    # 1. Check term options
    r = requests.get(f"{BASE_URL}/fixed-deposits/terms", headers=headers)
    print("Term options:", r.status_code, r.json())
    assert r.status_code == 200

    # 2. Try invalid term — expect 400
    r = requests.post(f"{BASE_URL}/fixed-deposits", json={"principal_amount": 100, "term_days": 7}, headers=headers)
    print("Invalid term (expect 400):", r.status_code, r.json())
    assert r.status_code == 400

    # 3. Check balance before
    r = requests.get(f"{BASE_URL}/account/balance", headers=headers)
    balance_before = float(r.json()["balance"])
    print("Balance before:", balance_before)

    # 4. Open a real fixed deposit
    r = requests.post(f"{BASE_URL}/fixed-deposits", json={"principal_amount": 200, "term_days": 30}, headers=headers)
    print("Open fixed deposit:", r.status_code, r.json())
    assert r.status_code == 201
    fd = r.json()
    assert fd["status"] == "active"
    assert float(fd["payout_amount"]) == 206.0  # 200 + 3%

    # 5. Confirm balance decreased by principal
    r = requests.get(f"{BASE_URL}/account/balance", headers=headers)
    balance_after_open = float(r.json()["balance"])
    print("Balance after opening FD:", balance_after_open)
    assert abs(balance_after_open - (balance_before - 200)) < 0.01

    # 6. List fixed deposits
    r = requests.get(f"{BASE_URL}/fixed-deposits", headers=headers)
    print("List FDs:", r.status_code, r.json())
    assert r.status_code == 200
    assert any(f["id"] == fd["id"] for f in r.json())

    # 7. Try opening one bigger than balance — expect 400
    r = requests.post(f"{BASE_URL}/fixed-deposits", json={"principal_amount": 999999, "term_days": 30}, headers=headers)
    print("Over-balance FD (expect 400):", r.status_code, r.json())
    assert r.status_code == 400

    print("\nAll fixed deposit checks passed ✅")
    print("\nNote: maturity auto-credit isn't tested here since it requires waiting for matures_at to pass.")
    print("To test that manually: open a Neon SQL editor and run:")
    print(f"  UPDATE fixed_deposits SET matures_at = now() - interval '1 minute' WHERE id = {fd['id']};")
    print("Then re-fetch /account/profile and confirm the balance jumped by the payout amount.")


if __name__ == "__main__":
    run()
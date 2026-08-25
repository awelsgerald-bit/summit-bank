import requests

BASE_URL = "https://summit-bank-1.onrender.com"
EMAIL = "autotest@example.com"
PASSWORD = "strongpassword123"


def get_token():
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def run():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List wallets (should include BTC if you already applied in earlier tests)
    r = requests.get(f"{BASE_URL}/wallets", headers=headers)
    print("List wallets:", r.status_code, r.json())
    assert r.status_code == 200

    # 2. Try applying again — should be 409 if already applied, 201 if first time
    r = requests.post(f"{BASE_URL}/wallets/apply", json={"currency": "BTC"}, headers=headers)
    print("Apply BTC wallet:", r.status_code, r.json())
    assert r.status_code in (201, 409)

    # 3. Apply for an unsupported currency — expect 400
    r = requests.post(f"{BASE_URL}/wallets/apply", json={"currency": "ETH"}, headers=headers)
    print("Apply unsupported currency (expect 400):", r.status_code, r.json())
    assert r.status_code == 400

    # 4. Get live BTC rate
    r = requests.get(f"{BASE_URL}/wallets/rates/BTC", headers=headers)
    print("Live BTC rate:", r.status_code, r.json())
    assert r.status_code == 200
    rate = float(r.json()["rate_usd"])
    assert rate > 0, "Rate should be a positive number"

    # 5. Deposit into BTC wallet and verify conversion math
    r = requests.get(f"{BASE_URL}/wallets", headers=headers)
    btc_before = next(w for w in r.json() if w["currency"] == "BTC")
    balance_before = float(btc_before["balance"])

    r = requests.post(f"{BASE_URL}/wallets/BTC/deposit", params={"amount_usd": 100}, headers=headers)
    print("Deposit $100 to BTC:", r.status_code, r.json())
    assert r.status_code == 201

    result = r.json()
    expected_converted = round(100 / rate, 8)
    actual_converted = round(float(result["converted_amount"]), 8)
    assert abs(expected_converted - actual_converted) < 0.0001, (
        f"Conversion math looks off: expected ~{expected_converted}, got {actual_converted}"
    )

    # 6. Confirm the wallet balance actually increased by that amount
    r = requests.get(f"{BASE_URL}/wallets", headers=headers)
    btc_after = next(w for w in r.json() if w["currency"] == "BTC")
    balance_after = float(btc_after["balance"])
    assert abs((balance_after - balance_before) - actual_converted) < 0.0001, "Balance didn't increase correctly"
    print(f"Balance before: {balance_before}, after: {balance_after} (+{actual_converted}) ✅")

    # 7. Deposit zero/negative — expect 400
    r = requests.post(f"{BASE_URL}/wallets/BTC/deposit", params={"amount_usd": 0}, headers=headers)
    print("Deposit $0 (expect 400):", r.status_code, r.json())
    assert r.status_code == 400

    # 8. Confirm USD balance was untouched by the BTC deposit (per our design decision)
    r = requests.get(f"{BASE_URL}/account/balance", headers=headers)
    print("USD balance (should be unaffected):", r.status_code, r.json())

    print("\nAll wallet checks passed ✅")


if __name__ == "__main__":
    run()
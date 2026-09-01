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

    # 1. Trigger velocity flag: submit 4 quick withdrawals
    tx_ids = []
    for i in range(4):
        r = requests.post(f"{BASE_URL}/transactions/withdraw", json={"amount": 1, "description": f"Fraud test {i}"}, headers=headers)
        print(f"Withdrawal {i+1}:", r.status_code, "flagged:", r.json().get("is_flagged"))
        tx_ids.append(r.json()["id"])

    last_tx = tx_ids[-1]

    # 2. Confirm the last one landed in the flagged queue, not the normal pending queue
    r = requests.get(f"{BASE_URL}/admin/transactions/flagged", headers=headers)
    print("Flagged queue:", r.status_code, [t["id"] for t in r.json()])
    assert r.status_code == 200
    flagged_ids = [t["id"] for t in r.json()]
    assert last_tx in flagged_ids, "Expected the 4th rapid withdrawal to be flagged"

    r = requests.get(f"{BASE_URL}/admin/transactions/pending", headers=headers)
    pending_ids = [t["id"] for t in r.json()]
    assert last_tx not in pending_ids, "Flagged transaction should NOT appear in the normal pending queue"

    # 3. Approve it from the flagged queue (uses the same approve endpoint)
    r = requests.post(f"{BASE_URL}/admin/transactions/{last_tx}/approve", headers=headers)
    print("Approve flagged tx:", r.status_code, r.json()["status"])
    assert r.status_code == 200

    # 4. Trigger large-amount flag (assuming account has little transaction history at a huge amount)
    r = requests.post(f"{BASE_URL}/transactions/deposit", json={"amount": 50000, "description": "Big deposit test"}, headers=headers)
    print("Large deposit:", r.status_code, "flagged:", r.json().get("is_flagged"), r.json().get("flag_reasons"))

    print("\nFraud detection checks passed ✅")
    print("Check the admin's inbox / Resend logs for fraud alert emails.")


if __name__ == "__main__":
    run()
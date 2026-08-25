import requests

BASE_URL = "https://summit-bank-1.onrender.com"
ADMIN_EMAIL = "autotest@example.com"
ADMIN_PASSWORD = "strongpassword123"


def login(email, password):
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def run():
    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Check balance before
    r = requests.get(f"{BASE_URL}/account/balance", headers=admin_headers)
    balance_before = float(r.json()["balance"])
    print("Balance before deposit:", balance_before)

    # 2. Submit a deposit
    r = requests.post(
        f"{BASE_URL}/transactions/deposit",
        json={"amount": 25, "description": "Approval flow test"},
        headers=admin_headers,
    )
    print("Submit deposit:", r.status_code, r.json())
    assert r.status_code == 201
    tx = r.json()
    assert tx["status"] == "pending", f"Expected pending, got {tx['status']}"
    tx_id = tx["id"]

    # 3. Confirm balance did NOT change yet
    r = requests.get(f"{BASE_URL}/account/balance", headers=admin_headers)
    balance_after_submit = float(r.json()["balance"])
    print("Balance right after submit (should be unchanged):", balance_after_submit)
    assert balance_after_submit == balance_before, "Balance changed before approval! This is the bug we're fixing."

    # 4. Confirm it shows up in the admin's pending queue
    r = requests.get(f"{BASE_URL}/admin/transactions/pending", headers=admin_headers)
    print("Pending queue:", r.status_code, r.json())
    assert r.status_code == 200
    pending_ids = [t["id"] for t in r.json()]
    assert tx_id in pending_ids, "Submitted transaction not found in pending queue"

    # 5. Approve it
    r = requests.post(f"{BASE_URL}/admin/transactions/{tx_id}/approve", headers=admin_headers)
    print("Approve:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    # 6. Confirm balance NOW updated
    r = requests.get(f"{BASE_URL}/account/balance", headers=admin_headers)
    balance_after_approval = float(r.json()["balance"])
    print("Balance after approval:", balance_after_approval)
    assert abs(balance_after_approval - (balance_before + 25)) < 0.01, "Balance didn't update correctly after approval"

    # 7. Try approving the same transaction again — expect 409
    r = requests.post(f"{BASE_URL}/admin/transactions/{tx_id}/approve", headers=admin_headers)
    print("Re-approve (expect 409):", r.status_code, r.json())
    assert r.status_code == 409

    # 8. Submit another deposit and reject it instead
    r = requests.post(
        f"{BASE_URL}/transactions/deposit",
        json={"amount": 15, "description": "Reject flow test"},
        headers=admin_headers,
    )
    tx_id_2 = r.json()["id"]

    r = requests.post(f"{BASE_URL}/admin/transactions/{tx_id_2}/reject", headers=admin_headers)
    print("Reject:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"

    # 9. Confirm balance unaffected by the rejected transaction
    r = requests.get(f"{BASE_URL}/account/balance", headers=admin_headers)
    balance_after_reject = float(r.json()["balance"])
    print("Balance after rejection (should match post-approval balance):", balance_after_reject)
    assert abs(balance_after_reject - balance_after_approval) < 0.01, "Rejected transaction affected balance!"

    print("\nAll approval-flow checks passed ✅")


if __name__ == "__main__":
    run()
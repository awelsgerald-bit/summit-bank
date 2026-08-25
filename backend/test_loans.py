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

    # 1. Apply for a loan
    r = requests.post(f"{BASE_URL}/loans/apply", json={"principal_amount": 1000, "term_months": 12, "purpose": "Test loan"}, headers=headers)
    print("Apply for loan:", r.status_code, r.json())
    assert r.status_code == 201
    loan = r.json()
    assert loan["status"] == "pending"
    loan_id = loan["id"]

    # 2. Balance should be unaffected while pending
    r = requests.get(f"{BASE_URL}/account/balance", headers=headers)
    balance_before = float(r.json()["balance"])
    print("Balance while pending:", balance_before)

    # 3. Try to repay a pending loan — expect 400
    r = requests.post(f"{BASE_URL}/loans/{loan_id}/repay", json={"amount": 100}, headers=headers)
    print("Repay pending loan (expect 400):", r.status_code, r.json())
    assert r.status_code == 400

    # 4. Show up in admin pending queue
    r = requests.get(f"{BASE_URL}/admin/loans/pending", headers=headers)
    print("Pending loans:", r.status_code, r.json())
    assert r.status_code == 200
    assert any(l["id"] == loan_id for l in r.json())

    # 5. Approve it
    r = requests.post(f"{BASE_URL}/admin/loans/{loan_id}/approve", headers=headers)
    print("Approve loan:", r.status_code, r.json())
    assert r.status_code == 200
    approved = r.json()
    assert approved["status"] == "approved"
    assert float(approved["total_repayable"]) == 1100.0  # 1000 + 10% interest

    # 6. Balance should now include the principal
    r = requests.get(f"{BASE_URL}/account/balance", headers=headers)
    balance_after_approval = float(r.json()["balance"])
    print("Balance after approval:", balance_after_approval)
    assert abs(balance_after_approval - (balance_before + 1000)) < 0.01

    # 7. Make a partial repayment
    r = requests.post(f"{BASE_URL}/loans/{loan_id}/repay", json={"amount": 500}, headers=headers)
    print("Partial repayment:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["status"] == "approved"  # not fully repaid yet
    assert float(r.json()["outstanding_balance"]) == 600.0  # 1100 - 500

    # 8. Repay the rest
    r = requests.post(f"{BASE_URL}/loans/{loan_id}/repay", json={"amount": 600}, headers=headers)
    print("Final repayment:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["status"] == "repaid"
    assert float(r.json()["outstanding_balance"]) == 0.0

    # 9. Try to repay an already-repaid loan — expect 400
    r = requests.post(f"{BASE_URL}/loans/{loan_id}/repay", json={"amount": 10}, headers=headers)
    print("Repay already-repaid loan (expect 400):", r.status_code, r.json())
    assert r.status_code == 400

    print("\nAll loan checks passed ✅")


if __name__ == "__main__":
    run()
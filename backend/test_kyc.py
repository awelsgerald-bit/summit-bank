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

    # 1. Submit KYC
    r = requests.post(f"{BASE_URL}/kyc/submit", json={
        "full_legal_name": "Awele Test",
        "date_of_birth": "1995-04-12",
        "id_type": "passport",
        "id_number": "X1234567",
        "address": "1 Test Street, Warri, Nigeria",
    }, headers=headers)
    print("Submit KYC:", r.status_code, r.json())
    assert r.status_code == 201
    submission_id = r.json()["id"]

    # 2. Duplicate pending submission — expect 409
    r = requests.post(f"{BASE_URL}/kyc/submit", json={
        "full_legal_name": "Awele Test", "date_of_birth": "1995-04-12",
        "id_type": "passport", "id_number": "X1234567", "address": "Somewhere",
    }, headers=headers)
    print("Duplicate pending (expect 409):", r.status_code, r.json())
    assert r.status_code == 409

    # 3. Confirm profile shows kyc_status = pending
    r = requests.get(f"{BASE_URL}/account/profile", headers=headers)
    print("Profile kyc_status:", r.json()["kyc_status"])
    assert r.json()["kyc_status"] == "pending"

    # 4. Show up in admin pending queue
    r = requests.get(f"{BASE_URL}/admin/kyc/pending", headers=headers)
    print("Pending KYC:", r.status_code, r.json())
    assert r.status_code == 200
    assert any(k["id"] == submission_id for k in r.json())

    # 5. Approve it (this should trigger a real email via Resend)
    r = requests.post(f"{BASE_URL}/admin/kyc/{submission_id}/approve", headers=headers)
    print("Approve KYC:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    # 6. Confirm profile now shows verified
    r = requests.get(f"{BASE_URL}/account/profile", headers=headers)
    print("Profile kyc_status after approval:", r.json()["kyc_status"])
    assert r.json()["kyc_status"] == "verified"

    print("\nAll KYC checks passed ✅")
    print("Check the inbox for autotest@example.com (or Resend's dashboard logs) to confirm the approval email sent.")


if __name__ == "__main__":
    run()
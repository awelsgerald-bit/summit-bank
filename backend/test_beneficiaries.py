import requests

BASE_URL = "https://summit-bank-1.onrender.com"
EMAIL = "autotest@example.com"
PASSWORD = "strongpassword123"
RECIPIENT_ACCOUNT = "6186960414"

def login():
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200
    return r.json()["access_token"]


def run():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(f"{BASE_URL}/account/profile", headers=headers)
    own_account = r.json()["account_number"]

    # 1. Empty list initially (or existing, either is fine)
    r = requests.get(f"{BASE_URL}/beneficiaries", headers=headers)
    print("List beneficiaries:", r.status_code, r.json())
    assert r.status_code == 200

    # 2. Add own account — expect 400
    r = requests.post(f"{BASE_URL}/beneficiaries", json={"nickname": "Me", "account_number": own_account}, headers=headers)
    print("Add own account (expect 400):", r.status_code, r.json())
    assert r.status_code == 400

    # 3. Add nonexistent account — expect 404
    r = requests.post(f"{BASE_URL}/beneficiaries", json={"nickname": "Ghost", "account_number": "0000000000"}, headers=headers)
    print("Add nonexistent account (expect 404):", r.status_code, r.json())
    assert r.status_code == 404

    # 4. Add a real beneficiary
    r = requests.post(f"{BASE_URL}/beneficiaries", json={"nickname": "Test Friend", "account_number": RECIPIENT_ACCOUNT}, headers=headers)
    print("Add real beneficiary:", r.status_code, r.json())
    assert r.status_code == 201
    beneficiary_id = r.json()["id"]

    # 5. Add same one again — expect 409
    r = requests.post(f"{BASE_URL}/beneficiaries", json={"nickname": "Dupe", "account_number": RECIPIENT_ACCOUNT}, headers=headers)
    print("Add duplicate (expect 409):", r.status_code, r.json())
    assert r.status_code == 409

    # 6. Delete it
    r = requests.delete(f"{BASE_URL}/beneficiaries/{beneficiary_id}", headers=headers)
    print("Delete beneficiary:", r.status_code)
    assert r.status_code == 204

    # 7. Delete again — expect 404
    r = requests.delete(f"{BASE_URL}/beneficiaries/{beneficiary_id}", headers=headers)
    print("Delete again (expect 404):", r.status_code, r.json())
    assert r.status_code == 404

    print("\nAll beneficiary checks passed ✅")


if __name__ == "__main__":
    run()
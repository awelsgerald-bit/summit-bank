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

    # 1. Apply for a card
    r = requests.post(f"{BASE_URL}/cards/apply", json={"card_type": "virtual"}, headers=headers)
    print("Apply for card:", r.status_code, r.json())
    assert r.status_code == 201
    card = r.json()
    assert card["status"] == "pending"
    assert card["card_number"] is None
    app_id = card["id"]

    # 2. Try applying again while one is pending — expect 409
    r = requests.post(f"{BASE_URL}/cards/apply", json={"card_type": "physical"}, headers=headers)
    print("Second application while pending (expect 409):", r.status_code, r.json())
    assert r.status_code == 409

    # 3. Invalid card type — expect 400 (need to clear the pending one first, so test this on a fresh check)
    # (skipped separately to avoid tripping the 409 above)

    # 4. Show up in admin pending queue
    r = requests.get(f"{BASE_URL}/admin/cards/pending", headers=headers)
    print("Pending cards:", r.status_code, r.json())
    assert r.status_code == 200
    assert any(c["id"] == app_id for c in r.json())

    # 5. Approve it
    r = requests.post(f"{BASE_URL}/admin/cards/{app_id}/approve", headers=headers)
    print("Approve card:", r.status_code, r.json())
    assert r.status_code == 200
    approved = r.json()
    assert approved["status"] == "approved"
    assert approved["card_number"] is not None
    assert approved["cvv"] is not None
    print(f"  Generated card: {approved['card_number']}, expires {approved['expiry_month']}/{approved['expiry_year']}")

    # 6. Re-approve — expect 409
    r = requests.post(f"{BASE_URL}/admin/cards/{app_id}/approve", headers=headers)
    print("Re-approve (expect 409):", r.status_code, r.json())
    assert r.status_code == 409

    # 7. List my cards, confirm it's there with full details
    r = requests.get(f"{BASE_URL}/cards", headers=headers)
    print("My cards:", r.status_code, r.json())
    assert r.status_code == 200
    assert any(c["id"] == app_id and c["card_number"] for c in r.json())

    # 8. Now that the first is approved (not pending), apply and reject a second one
    r = requests.post(f"{BASE_URL}/cards/apply", json={"card_type": "physical"}, headers=headers)
    assert r.status_code == 201
    app_id_2 = r.json()["id"]

    r = requests.post(f"{BASE_URL}/admin/cards/{app_id_2}/reject", headers=headers)
    print("Reject second application:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert r.json()["card_number"] is None

    print("\nAll card application checks passed ✅")


if __name__ == "__main__":
    run()
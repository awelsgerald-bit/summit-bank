import requests



BASE_URL = "http://127.0.0.1:8000"

def run():
    # 1. Register
    register_payload = {
        "full_name": "Awele Test",
        "email": "autotest@example.com",
        "password": "strongpassword123",
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
    print("Register:", r.status_code, r.json())

    # 2. Login
    login_payload = {"email": "autotest@example.com", "password": "strongpassword123"}
    r = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    print("Login:", r.status_code, r.json())
    token = r.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Profile
    r = requests.get(f"{BASE_URL}/account/profile", headers=headers)
    print("Profile:", r.status_code, r.json())

    # 4. Balance
    r = requests.get(f"{BASE_URL}/account/balance", headers=headers)
    print("Balance:", r.status_code, r.json())

    # 5. Unauthenticated check
    r = requests.get(f"{BASE_URL}/account/profile")
    print("No-auth profile (expect 401):", r.status_code)

    run()    

def run_transactions():
    # Log in as user 1
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": "autotest@example.com", "password": "strongpassword123"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Deposit
    r = requests.post(f"{BASE_URL}/transactions/deposit", json={"amount": 500, "description": "Test deposit"}, headers=headers)
    print("Deposit:", r.status_code, r.json())

    # Withdraw
    r = requests.post(f"{BASE_URL}/transactions/withdraw", json={"amount": 100}, headers=headers)
    print("Withdraw:", r.status_code, r.json())

    # Over-withdraw (expect 400)
    r = requests.post(f"{BASE_URL}/transactions/withdraw", json={"amount": 999999}, headers=headers)
    print("Over-withdraw (expect 400):", r.status_code, r.json())

    # Register a second user to transfer to
    requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Recipient User",
        "email": "recipient@example.com",
        "password": "strongpassword123",
    })
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": "recipient@example.com", "password": "strongpassword123"})
    recipient_token = r.json()["access_token"]
    r = requests.get(f"{BASE_URL}/account/profile", headers={"Authorization": f"Bearer {recipient_token}"})
    recipient_account = r.json()["account_number"]

    # Transfer
    r = requests.post(f"{BASE_URL}/transactions/transfer", json={
        "recipient_account_number": recipient_account,
        "amount": 50,
        "description": "Test transfer",
    }, headers=headers)
    print("Transfer:", r.status_code, r.json())

    # Transfer to self (expect 400)
    r = requests.get(f"{BASE_URL}/account/profile", headers=headers)
    own_account = r.json()["account_number"]
    r = requests.post(f"{BASE_URL}/transactions/transfer", json={
        "recipient_account_number": own_account,
        "amount": 10,
    }, headers=headers)
    print("Self-transfer (expect 400):", r.status_code, r.json())

    # Transfer to nonexistent account (expect 404)
    r = requests.post(f"{BASE_URL}/transactions/transfer", json={
        "recipient_account_number": "0000000000",
        "amount": 10,
    }, headers=headers)
    print("Nonexistent recipient (expect 404):", r.status_code, r.json())

    run()
    run_transactions()

def run_history():
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": "autotest@example.com", "password": "strongpassword123"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(f"{BASE_URL}/transactions/history", headers=headers)
    print("History:", r.status_code)
    for tx in r.json():
        print(" ", tx["transaction_type"], tx["amount"], tx["timestamp"])

if __name__ == "__main__":
    run()
    run_transactions()
    run_history()
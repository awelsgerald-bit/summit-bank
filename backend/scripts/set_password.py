"""
Set a new password for an existing user (for example the admin account).

Run it from the backend folder, with the same environment as the app (it reads DATABASE_URL
and the other settings from backend/.env):

    python scripts/set_password.py someone@example.com

The new password is typed at a hidden prompt. It is never printed, logged or stored anywhere
except as a bcrypt hash in the users table.
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models  # noqa: F401,E402  (registers every model so relationships resolve)
from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402

MIN_LENGTH = 12


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/set_password.py <email>")
        return 2
    email = sys.argv[1].strip()

    password = getpass.getpass(f"New password for {email} (min {MIN_LENGTH} characters): ")
    if len(password) < MIN_LENGTH:
        print(f"Too short: use at least {MIN_LENGTH} characters.")
        return 1
    if getpass.getpass("Type it again: ") != password:
        print("The two passwords do not match. Nothing was changed.")
        return 1

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            print(f"No user with email {email}. Nothing was changed.")
            return 1
        user.hashed_password = hash_password(password)
        db.commit()
        print(f"Password updated for {email}.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

"""Read-only health check of the live Summit Bank. It creates no accounts and moves no money.

    python scripts/smoke_check.py https://summit-bank-1.onrender.com https://summit-bank-fawn.vercel.app

The first request can take up to a minute while the free Render server wakes up.
"""
import sys

import httpx

BACKEND = (sys.argv[1] if len(sys.argv) > 1 else "https://summit-bank-1.onrender.com").rstrip("/")
FRONTEND = (sys.argv[2] if len(sys.argv) > 2 else "https://summit-bank-fawn.vercel.app").rstrip("/")

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"   ({detail})" if detail and not ok else ""))


def main():
    with httpx.Client(timeout=75, follow_redirects=False) as c:
        r = c.get(f"{BACKEND}/docs")
        check("backend is awake", r.status_code == 200, r.status_code)

        r = c.post(f"{BACKEND}/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
        check("wrong login is refused cleanly (not a server error)", r.status_code in (400, 401, 403, 422), r.status_code)

        for path in ("/account/profile", "/transactions/history", "/scheduled-transfers", "/referrals/me", "/savings/pots", "/statements"):
            r = c.get(f"{BACKEND}{path}")
            check(f"{path} needs a login", r.status_code in (401, 403, 404, 405), r.status_code)

        r = c.post(f"{BACKEND}/strowallet/webhook", params={"token": "definitely-wrong-token"}, content=b"{}")
        check("webhook with a wrong token is refused", r.status_code == 401, r.status_code)

        r = c.post(f"{BACKEND}/internal/run-schedules")
        check("scheduler endpoint is locked (404 off, 401 on)", r.status_code in (401, 404), r.status_code)

        r = c.options(
            f"{BACKEND}/auth/login",
            headers={"Origin": FRONTEND, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"},
        )
        check("the website is allowed to call the backend (CORS)", r.headers.get("access-control-allow-origin") in (FRONTEND, "*"), r.headers.get("access-control-allow-origin"))

        r = c.get(f"{FRONTEND}/")
        check("website home page loads", r.status_code == 200 and 'id="root"' in r.text, r.status_code)
        for path in ("/login", "/register", "/dashboard"):
            r = c.get(f"{FRONTEND}{path}")
            check(f"website {path} opens directly", r.status_code == 200, r.status_code)

    failed = results.count(False)
    print(f"\n{len(results) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

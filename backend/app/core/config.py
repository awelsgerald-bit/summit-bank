from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    environment: str = "development"
    allowed_origins: list[str] = ["http://localhost:5173"]
    resend_api_key: str = ""
    paystack_secret_key: str = "sk_test_19b0106046ceec9bdb0ec0ca569091d91b20fa4b"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    frontend_url: str = "http://localhost:5173"
    strowallet_public_key: str = ""
    strowallet_base_url: str = "https://strowallet.com/api"
    strowallet_webhook_secret: str = ""  # our own shared secret for compensating verification, not StroWallet's
    backend_base_url: str = "https://summit-bank-1.onrender.com"
    strowallet_mode: str = "sandbox"  # switch to "live" only after sandbox is fully proven
    strowallet_provider: str = "sterling"  # "sterling" (tested) or "fidelity" (untested) - never Nombank
    strowallet_live_enabled: bool = False  # second switch: must ALSO be true before STROWALLET_MODE=live does anything
    strowallet_verify_amount: str = "transaction"  # amount sent to StroWallet's verify call: "transaction" (gross) or "settled" (net). Not confirmed by StroWallet; change it here, not in code.
    strowallet_webhook_ips: str = ""  # comma-separated caller IPs allowed to post webhooks (StroWallet says: 209.74.72.48); empty = no IP check
    strowallet_webhook_ip_hops: int = 1  # which address from the right of X-Forwarded-For is the real caller (1 = last one)
    # Round 3B
    scheduler_enabled: bool = True  # run due scheduled transfers every minute while the server is awake
    cron_token: str = ""  # secret for POST /internal/run-schedules (an outside timer can wake the server); empty = endpoint off
    referral_bonus_amount: Decimal = Decimal("500")  # paid to EACH side (still needs admin approval)
    referral_min_first_deposit: Decimal = Decimal("5000")  # the new user's approved deposit must be at least this
    referral_max_rewards_per_user: int = 20
settings = Settings()
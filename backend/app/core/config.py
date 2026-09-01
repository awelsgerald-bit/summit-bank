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

settings = Settings()
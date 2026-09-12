from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./dpdp_audit.db"
    dodo_webhook_secret: str = ""
    dodo_payments_api_key: str = ""
    secret_key: str = "8a34b2c19d7e5f6a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f12"
    algorithm: str = "HS256"
    debug: bool = False
    allowed_origins: str = "https://consentlayers.in,http://localhost:8000,http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
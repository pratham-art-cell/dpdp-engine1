import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./dpdp_audit.db"
    dodo_webhook_secret: str = ""
    secret_key: str = secrets.token_urlsafe(32)  # Automatically secures the server
    algorithm: str = "HS256"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
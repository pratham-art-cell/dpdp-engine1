from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./dpdp_audit.db"
    dodo_webhook_secret: str = ""
    debug: bool = False  # <-- Add this line so database.py doesn't crash

    # This tells Pydantic to read from your .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Create a global settings object to use throughout your app
settings = Settings()
import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./youtube_tracker.db")
    poll_interval: int = int(os.getenv("POLL_INTERVAL", "600"))  # in seconds
    app_title: str = "YouTube Subscription Tracker"

    class Config:
        env_file = ".env"


settings = Settings()

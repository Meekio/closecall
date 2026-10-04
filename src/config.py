"""
Central configuration module.
Reads environment variables from .env and exposes typed settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level above src/)
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")


class Config:
    # API keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

    # Defaults
    DEFAULT_LOCATION: str = os.getenv("DEFAULT_LOCATION", "Mumbai")

    # Paths
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/closecall.db")
    IMAGE_STORAGE_PATH: Path = Path(os.getenv("IMAGE_STORAGE_PATH", "./data/images"))

    # Model names — configurable via GEMINI_MODEL env var
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    GEMINI_VISION_MODEL: str = os.getenv("GEMINI_VISION_MODEL", "gemini-3.5-flash")

    @classmethod
    def validate(cls) -> None:
        """Raise if required keys are missing."""
        missing = []
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Copy .env.example to .env and fill in your keys."
            )


config = Config()

import os
from dotenv import load_dotenv

load_dotenv()

class AgentConfig:
    # Google Gemini API key configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    
    # Model to use
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @classmethod
    def validate(cls):
        """Verifies Gemini credentials are set."""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY or GOOGLE_API_KEY is not configured in the environment. "
                "Please add it to your .env file."
            )

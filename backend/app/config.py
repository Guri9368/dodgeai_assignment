import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").strip()
    DATA_FILE_PATH: str = os.getenv("DATA_FILE_PATH", "../data/sap-o2c-data").strip()
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "business_data.db").strip()


settings = Settings()
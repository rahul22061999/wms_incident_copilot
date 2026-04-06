from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """All configs for wms_incident_copilot"""

    model_config = SettingsConfigDict(
        env_file= BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    ANTHROPIC_API_KEY: SecretStr = Field(
        description="Anthropic API key"
    )

    GROQ_API_KEY: SecretStr = Field(
        description="Groq API key"
    )

    GOOGLE_API_KEY: SecretStr = Field(
        description="Google API key"
    )

    OPENAI_API_KEY: SecretStr = Field(
        description="OpenAI API key"
    )

    DATABASE_URL: SecretStr = Field(
        description="Database connection string"
    )

    MEMORIES_DB_URL: SecretStr = Field(
        description="Memory database connection string"
    )

    LANGSMITH_API_KEY: SecretStr = Field(description="Langsmith API key")

    GOOGLE_AI_MODEL: str = "gemini-3.1-flash-lite-preview"
    OPEN_AI_MODEL: str = "gpt-5-nano"
    GROQ_MODEL: str ="llama-3.1-8b-instant"
    GOOGLE_TIMEOUT: int = 10


    #Database config
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_STATEMENT_TIMEOUT: int = 30_000
    DB_ECHO: bool = False
    DB_SCHEMA: str = "wms1"

    SQL_TABLES: list[str] = [
        "rcv_inventory",
        "pckwrk",
        "inventory"
    ]

    SUPERVISOR_MAX_LOOP: int = 3
    CHILD_MAX_LOOP: int = 3

    ##session store
    SESSION_STORE_DIR: str='src/data/sessions'



settings = Settings()
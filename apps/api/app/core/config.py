"""Pydantic Settings — environment-based configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interview_agent"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Interview settings
    DEFAULT_QUESTIONS_COUNT: int = 10
    MAX_FOLLOW_UPS: int = 2
    FOLLOW_UP_PROBABILITY: float = 0.3

    # ML model settings
    SPACY_MODEL: str = "en_core_web_sm"
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Speech-to-text
    WHISPER_MODEL: str = "base"

    # S3/MinIO
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_BUCKET: str = "interview-agent"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"

    # Email
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USER: str = ""
    EMAIL_SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@interviewagent.com"

    # Environment
    ENVIRONMENT: str = "development"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    APP_URL: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()

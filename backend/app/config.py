from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql://meduser:medpass@postgres:5432/meddb"

    # JWT
    SECRET_KEY: str = "changeme_use_random_32_bytes_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    PROJECT_NAME: str = "MedPlatform API"
    API_V1_STR: str = "/api/v1"

    # Storage — set STORAGE_BACKEND=s3 in prod .env
    STORAGE_BACKEND: str = "local"          # "local" | "s3"
    UPLOAD_DIR: str = "/api/uploads"        # used when STORAGE_BACKEND=local

    # S3 (only required when STORAGE_BACKEND=s3)
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Celery / Redis
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Preprocessing output (NumPy arrays saved here)
    PREPROCESSED_DIR: str = "/api/preprocessed"

    # PDF reports output
    REPORTS_DIR: str = "/api/reports"


settings = Settings()


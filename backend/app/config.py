from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Politia"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = ""
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Scoring
    scoring_formula_version: str = "v1"

    # Storage (Cloudflare R2 / S3-compatible)
    storage_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "politia-raw"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    model_config = {
        "env_file": ".env",
        "env_prefix": "POLITIA_",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()

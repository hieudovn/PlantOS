"""Application configuration loaded from environment variables.

CRITICAL: Never hardcode production credentials here.
All secrets must be set via environment variables or .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """PlantOS backend settings."""

    # Application
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "plantos"
    POSTGRES_USER: str = "plantos"
    POSTGRES_PASSWORD: str = ""  # Required — set via POSTGRES_PASSWORD env var

    # TDengine
    TDENGINE_HOST: str = "localhost"
    TDENGINE_PORT: int = 6041
    TDENGINE_DATABASE: str = "plantos_ts"
    TDENGINE_USER: str = "root"
    TDENGINE_PASSWORD: str = ""  # Required — set via TDENGINE_PASSWORD env var
    TDENGINE_TIMEOUT: int = 10  # connection timeout in seconds

    # EMQX
    EMQX_HOST: str = "localhost"
    EMQX_MQTT_PORT: int = 1883

    # Historian
    HISTORIAN_MODE: str = "tdengine"  # "tdengine" | "stub"

    # Authentication
    JWT_SECRET: str = ""  # Required — set via JWT_SECRET env var
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 1
    JWT_REFRESH_THRESHOLD_MINUTES: int = 30
    API_KEYS: str = ""  # Required — comma-separated from EDGE_API_KEY,FRONTEND_DEMO_KEY

    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL from settings."""
        if not self.POSTGRES_PASSWORD:
            raise RuntimeError(
                "POSTGRES_PASSWORD is not set. "
                "Create a deployment/.env file with POSTGRES_PASSWORD=<value>"
            )
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous URL for Alembic (migrations run sync)."""
        return self.DATABASE_URL

    def validate(self):
        """Validate required settings. Call at startup."""
        if not self.JWT_SECRET:
            raise RuntimeError(
                "JWT_SECRET is not set. "
                "Create a deployment/.env file with JWT_SECRET=<value>"
            )
        if not self.API_KEYS:
            raise RuntimeError(
                "API_KEYS is empty. At least one API key must be configured "
                "for internal service auth. Set EDGE_API_KEY and FRONTEND_DEMO_KEY in .env"
            )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()

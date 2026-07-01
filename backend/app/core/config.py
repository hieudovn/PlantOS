"""Application configuration loaded from environment variables."""

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
    POSTGRES_PASSWORD: str = "plantos"

    # TDengine
    TDENGINE_HOST: str = "localhost"
    TDENGINE_PORT: int = 6041
    TDENGINE_DATABASE: str = "plantos_ts"
    TDENGINE_USER: str = "root"
    TDENGINE_PASSWORD: str = "taosdata"
    TDENGINE_TIMEOUT: int = 10  # connection timeout in seconds

    # EMQX
    EMQX_HOST: str = "localhost"
    EMQX_MQTT_PORT: int = 1883

    # Historian
    HISTORIAN_MODE: str = "tdengine"  # "tdengine" | "stub"

    # Authentication
    JWT_SECRET: str = "plantos-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    API_KEYS: str = ""  # comma-separated: "key1,key2"

    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL from settings."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous URL for Alembic (migrations run sync)."""
        return self.DATABASE_URL

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict   # used for application configuration/settings management.

# Represents all application configuration.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App metadata ---
    APP_NAME: str = "Network Diagnostic API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development | staging | production


    HOST: str = "0.0.0.0"
    PORT: int = 8000


    LOG_LEVEL: str = "INFO"


    CORS_ORIGINS: str = "*"


    BLOCK_PRIVATE_TARGETS: bool = False

    MAX_PING_COUNT: int = 10
    MAX_TIMEOUT_SECONDS: float = 10.0

    # Convert the comma-separated CORS_ORIGINS string into list (e.g. CORS_ORIGINS=http://localhost:3000,https://example.com)
    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return  ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

# Creates and return the applications settings
@lru_cache
def get_settings() -> Settings:
    return Settings()
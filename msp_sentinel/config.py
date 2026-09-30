from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    refresh_seconds: int = 60
    http_timeout: float = 12.0
    nvd_api_key: str | None = None
    ollama_url: str = "http://localhost:11434"
    ollama_model: str | None = None

    model_config = SettingsConfigDict(env_prefix="MSP_SENTINEL_", env_file=".env", extra="ignore")


settings = Settings()

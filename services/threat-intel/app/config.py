from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server settings
    server_host: str = "0.0.0.0"
    server_port: int = 8082

    # Database
    database_url: str = "postgresql+asyncpg://siem:siem@postgres:5432/siem"

    # Redis
    redis_url: str = "redis://redis:6379"

    # Threat feeds
    otx_api_key: str = ""
    abuseipdb_api_key: str = ""
    virustotal_api_key: str = ""

    # Feed update interval (seconds)
    feed_update_interval: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

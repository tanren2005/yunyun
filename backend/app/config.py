from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "云云"
    secret_key: str = "yunyun-dev-secret-change-in-production-32chars"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    database_url: str = "postgresql+psycopg://yunyun:yunyun@localhost:5432/yunyun"
    redis_url: str = "redis://localhost:6379/0"

    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = ""

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_accounts_per_email: int = 2
    code_ttl_seconds: int = 600
    code_resend_interval_seconds: int = 60
    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 80
    max_files_per_item: int = 8
    # 启动时把该用户名设为管理员（本地方便）
    admin_username: str = "Tan"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

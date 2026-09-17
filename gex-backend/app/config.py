"""Uygulama konfigürasyonu — tüm gizli/ortam değerleri buradan okunur.

Build Spec Bölüm 15.2. Hiçbir gizli değer kod içine yazılmaz; hepsi ortam
değişkeninden (veya .env dosyasından) gelir.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Veritabanı ---
    database_url: str = "postgresql://gex_user:changeme@localhost:5432/gex_db"
    test_database_url: str = "postgresql://test_user:test_pass@localhost:5433/gex_test"

    # --- Kimlik Doğrulama ---
    jwt_secret_key: str = "CHANGE_THIS_TO_A_LONG_RANDOM_STRING"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_token_expire_days_remember_me: int = 30
    max_failed_login_attempts: int = 5
    lockout_minutes: int = 15

    # --- Veri Kaynağı ---
    market_data_provider: str = "yfinance"
    tradier_api_key: str | None = None
    polygon_api_key: str | None = None
    request_delay_seconds: float = 1.0
    max_fetch_retries: int = 3
    fetch_retry_backoff_seconds: int = 5

    # --- Hesaplama Parametreleri (Bölüm 3) ---
    risk_free_rate: float = 0.05
    contract_multiplier: int = 100
    gex_move_pct: float = 0.01
    neutral_band_pct: float = 0.002
    dealer_sign_convention: str = "standard"

    # --- Zamanlanmış İşler ---
    fetch_interval_minutes: int = 2
    alert_cooldown_minutes: int = 30
    cleanup_hour_et: int = 3

    # --- Veri Saklama (Bölüm 5.15) ---
    raw_data_retention_days: int = 90
    strike_gex_retention_days: int = 365
    price_snapshot_retention_days: int = 365
    read_notification_retention_days: int = 180

    # --- E-posta (Bölüm 12.5) ---
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_address: str = "noreply@gex-platform.example"

    # --- Genel ---
    environment: str = "development"
    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

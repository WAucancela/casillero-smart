# ══════════════════════════════════════════════════════════════
#  config/settings.py — Parche para agregar REFRESH_TOKEN_EXPIRE_DAYS
#
#  Agrega estas líneas al Settings existente en config/settings.py:
# ══════════════════════════════════════════════════════════════

# En la clase Settings, dentro del bloque JWT, añadir:
#
#   REFRESH_TOKEN_EXPIRE_DAYS: int = 30
#
# Ejemplo del bloque completo:
#
# class Settings(BaseSettings):
#     ...
#     # JWT
#     SECRET_KEY: str
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 480      # 8 horas
#     REFRESH_TOKEN_EXPIRE_DAYS: int = 30         # ← AGREGAR ESTO
#     ...

# ── Parche directo (si prefieres aplicarlo como archivo separado) ──
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480    # 8 horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30       # 30 días

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USER: str = "casilleros"
    MQTT_PASSWORD: str = ""

    # Biometría
    BIOMETRIC_CONFIDENCE_THRESHOLD: float = 0.75
    BIOMETRIC_ENCRYPTION_KEY: str = ""

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # App
    APP_NAME: str = "Casilleros Automatizados"
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    ALLOWED_ORIGINS: str = "http://localhost"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

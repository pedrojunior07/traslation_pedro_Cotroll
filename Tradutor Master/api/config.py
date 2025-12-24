import os
from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass
class Settings:
    db_host: str = os.getenv("DB_HOST", "102.211.186.44")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "Root@12345!")
    db_name: str = os.getenv("DB_NAME", "tradutor_db")

    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    access_token_exp_minutes: int = int(os.getenv("ACCESS_TOKEN_EXP_MIN", "720"))
    device_token_exp_minutes: int = int(os.getenv("DEVICE_TOKEN_EXP_MIN", "43200"))

    superadmin_user: str = os.getenv("SUPERADMIN_USER", "admin")
    superadmin_password: str = os.getenv("SUPERADMIN_PASSWORD", "1234")

    translate_base_url: str = "http://102.211.186.44/translate"
    translate_timeout: float = 15.0

    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_enabled: bool = os.getenv("OPENAI_ENABLED", "false").lower() == "true"


def build_db_url(settings: Settings) -> str:
    user = quote_plus(settings.db_user)
    password = quote_plus(settings.db_password)
    host = settings.db_host
    port = settings.db_port
    name = settings.db_name
    return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


from datetime import date, datetime
from math import ceil

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from api.database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superadmin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    type = Column(String(32), default="STANDARD")
    max_devices = Column(Integer, default=1)
    quota_type = Column(String(16), default="TRANSLATIONS")
    quota_limit = Column(Integer, default=500)
    quota_period = Column(String(16), default="DAILY")
    duration_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    @property
    def days_remaining(self) -> int | None:
        if not self.expires_at:
            return None
        remaining = ceil((self.expires_at - utcnow()).total_seconds() / 86400)
        return max(0, remaining)


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (UniqueConstraint("license_id", "device_id", name="uq_license_device"),)

    id = Column(Integer, primary_key=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    device_id = Column(String(128), nullable=False)
    device_name = Column(String(128), nullable=True)
    is_blocked = Column(Boolean, default=False)
    last_seen_at = Column(DateTime, nullable=True)
    usage_today = Column(Integer, default=0)
    usage_today_date = Column(Date, default=date.today)
    usage_month_count = Column(Integer, default=0)
    usage_month_month = Column(Integer, default=0)
    usage_month_year = Column(Integer, default=0)
    total_usage = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class TranslationLog(Base):
    __tablename__ = "translation_logs"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    source = Column(String(16), nullable=False)
    target = Column(String(16), nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    units = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)


class AIConfig(Base):
    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    provider = Column(String(32), default="openai")  # openai, gemini, grok
    base_url = Column(String(255), default="https://api.openai.com/v1")
    model = Column(String(128), default="gpt-4o-mini")
    api_key = Column(Text, default="")

    # Configurações específicas para Gemini
    gemini_api_key = Column(Text, default="")
    gemini_model = Column(String(128), default="gemini-1.5-flash")

    # Configurações específicas para Grok
    grok_api_key = Column(Text, default="")
    grok_model = Column(String(128), default="grok-2-latest")

    # Timeouts e limites
    timeout = Column(Float, default=30.0)
    max_retries = Column(Integer, default=3)

    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class TranslateConfig(Base):
    __tablename__ = "translate_config"

    id = Column(Integer, primary_key=True)
    # Provider: "libretranslate" ou "nllb"
    provider = Column(String(32), default="libretranslate")

    # LibreTranslate config
    base_url = Column(String(255), default="http://102.211.186.44/translate")

    # NLLB config
    nllb_base_url = Column(String(255), default="http://102.211.186.111:8000")

    timeout = Column(Float, default=15.0)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class TranslationToken(Base):
    """Armazena informações detalhadas de cada token traduzido."""
    __tablename__ = "translation_tokens"

    id = Column(Integer, primary_key=True)
    translation_log_id = Column(Integer, ForeignKey("translation_logs.id"), nullable=False, index=True)
    location = Column(String(255), nullable=False)  # Ex: "Paragrafo 1", "Tabela 1 L1C1"
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    original_length = Column(Integer, nullable=False)
    translated_length = Column(Integer, nullable=False)
    was_truncated = Column(Boolean, default=False)
    size_ratio = Column(Float, nullable=False)  # translated_length / original_length
    units = Column(Integer, default=1)
    warnings = Column(Text, nullable=True)  # JSON array de avisos
    created_at = Column(DateTime, default=utcnow)

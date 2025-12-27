from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserCreate(BaseModel):
    username: str
    password: str
    is_superadmin: bool = False


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    is_superadmin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LicenseCreate(BaseModel):
    type: str = "STANDARD"
    max_devices: int = 1
    quota_type: str = "TRANSLATIONS"
    quota_limit: int = 500
    quota_period: str = "DAILY"
    duration_days: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class LicenseUpdate(BaseModel):
    type: Optional[str] = None
    max_devices: Optional[int] = None
    quota_type: Optional[str] = None
    quota_limit: Optional[int] = None
    quota_period: Optional[str] = None
    duration_days: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class LicenseOut(BaseModel):
    id: int
    key: str
    type: str
    max_devices: int
    quota_type: str
    quota_limit: int
    quota_period: str
    duration_days: Optional[int]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    days_remaining: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceRegisterRequest(BaseModel):
    license_key: str
    device_id: str
    device_name: Optional[str] = None


class DeviceTokenResponse(BaseModel):
    device_token: str
    token_type: str = "bearer"


class DeviceUpdate(BaseModel):
    is_blocked: Optional[bool] = None


class DeviceOut(BaseModel):
    id: int
    license_id: int
    device_id: str
    device_name: Optional[str]
    is_blocked: bool
    last_seen_at: Optional[datetime]
    usage_today: int
    usage_today_date: date
    usage_month_count: int
    usage_month_month: int
    usage_month_year: int
    total_usage: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranslateRequest(BaseModel):
    text: str
    source: str
    target: str
    units: int = 1


class TranslateResponse(BaseModel):
    translatedText: str


class TranslateBatchRequest(BaseModel):
    texts: list[str]
    source: str
    target: str
    units: Optional[int] = None


class TranslateBatchResponse(BaseModel):
    translations: list[str]


class AITranslateRequest(BaseModel):
    text: str
    source: str
    target: str
    glossary: Optional[dict[str, str]] = None
    units: int = 1


class AIEvaluateRequest(BaseModel):
    texts: list[str]
    source: str
    target: str


class AIEvaluateItem(BaseModel):
    text: str
    translatable: bool
    reason: Optional[str] = None


class AIEvaluateResponse(BaseModel):
    items: list[AIEvaluateItem]


class AIGlossaryRequest(BaseModel):
    texts: list[str]
    source: str
    target: str


class AIGlossaryResponse(BaseModel):
    glossary: dict[str, str]


class ConsumeRequest(BaseModel):
    units: int = 1


class ConsumeResponse(BaseModel):
    status: str
    usage_today: int
    usage_month_count: int
    total_usage: int


class UsageResponse(BaseModel):
    device_id: int
    license_id: int
    usage_today: int
    usage_today_date: date
    usage_month_count: int
    usage_month_month: int
    usage_month_year: int
    total_usage: int
    quota_type: str
    quota_limit: int
    quota_period: str
    quota_remaining: Optional[int] = None
    license_active: bool
    license_expires_at: Optional[datetime]


class AIConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    provider: Optional[str] = None  # openai, gemini, grok
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    grok_api_key: Optional[str] = None
    grok_model: Optional[str] = None
    timeout: Optional[float] = None
    max_retries: Optional[int] = None


class AIConfigOut(BaseModel):
    enabled: bool
    provider: str
    base_url: str
    model: str
    api_key_present: bool
    gemini_api_key_present: bool
    gemini_model: str
    grok_api_key_present: bool
    grok_model: str
    timeout: float
    max_retries: int


class TranslateConfigUpdate(BaseModel):
    base_url: Optional[str] = None
    timeout: Optional[float] = None


class TranslateConfigOut(BaseModel):
    base_url: str
    timeout: float


class TranslationTokenOut(BaseModel):
    """Schema para retornar informações de um token traduzido."""
    id: int
    location: str
    original_text: str
    translated_text: str
    original_length: int
    translated_length: int
    was_truncated: bool
    size_ratio: float
    units: int
    warnings: Optional[list[str]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranslationLogWithTokens(BaseModel):
    """Schema para retornar log de tradução com todos os tokens."""
    id: int
    device_id: int
    source: str
    target: str
    original_text: str
    translated_text: str
    units: int
    created_at: datetime
    tokens: list[TranslationTokenOut]

    model_config = ConfigDict(from_attributes=True)

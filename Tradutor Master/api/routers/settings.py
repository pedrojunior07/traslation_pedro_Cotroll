from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.config import Settings
from api.database import get_db
from api.models import AIConfig, TranslateConfig, User
from api.schemas import AIConfigOut, AIConfigUpdate, TranslateConfigOut, TranslateConfigUpdate
from api.security import get_current_superadmin

router = APIRouter(prefix="/settings", tags=["settings"])
settings_cfg = Settings()


def _get_ai_config(db: Session) -> AIConfig:
    cfg = db.query(AIConfig).first()
    if cfg:
        return cfg
    cfg = AIConfig()
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


def _get_translate_config(db: Session) -> TranslateConfig:
    return TranslateConfig(base_url=settings_cfg.translate_base_url, timeout=settings_cfg.translate_timeout)


@router.get("/ai", response_model=AIConfigOut)
def get_ai_config(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> AIConfigOut:
    cfg = _get_ai_config(db)
    return AIConfigOut(
        enabled=cfg.enabled,
        base_url=cfg.base_url,
        model=cfg.model,
        api_key_present=bool(cfg.api_key),
    )


@router.put("/ai", response_model=AIConfigOut)
def update_ai_config(
    payload: AIConfigUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> AIConfigOut:
    cfg = _get_ai_config(db)
    if payload.enabled is not None:
        cfg.enabled = payload.enabled
    if payload.base_url is not None:
        cfg.base_url = payload.base_url
    if payload.model is not None:
        cfg.model = payload.model
    if payload.api_key is not None:
        cfg.api_key = payload.api_key
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return AIConfigOut(
        enabled=cfg.enabled,
        base_url=cfg.base_url,
        model=cfg.model,
        api_key_present=bool(cfg.api_key),
    )


@router.get("/translate", response_model=TranslateConfigOut)
def get_translate_config(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> TranslateConfigOut:
    cfg = _get_translate_config(db)
    return TranslateConfigOut(base_url=cfg.base_url, timeout=cfg.timeout)


@router.put("/translate", response_model=TranslateConfigOut)
def update_translate_config(
    payload: TranslateConfigUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> TranslateConfigOut:
    cfg = _get_translate_config(db)
    return TranslateConfigOut(base_url=cfg.base_url, timeout=cfg.timeout)


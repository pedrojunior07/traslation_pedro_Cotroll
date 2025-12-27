from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Device, License, TranslationLog, User
from api.schemas import (
    AIEvaluateRequest,
    AIEvaluateResponse,
    AIGlossaryRequest,
    AIGlossaryResponse,
    AITranslateRequest,
    ConsumeRequest,
    ConsumeResponse,
    TranslateBatchRequest,
    TranslateBatchResponse,
    TranslateRequest,
    TranslateResponse,
    UsageResponse,
)
from api.security import get_current_device, get_current_superadmin
from api.services import (
    request_ai_evaluate,
    request_ai_glossary,
    request_ai_translate,
    request_languages,
    request_translation,
    request_translation_batch,
)

router = APIRouter(tags=["translate"])


def _license_is_valid(license_obj: License) -> bool:
    if not license_obj.is_active:
        return False
    if license_obj.expires_at and license_obj.expires_at < datetime.utcnow():
        return False
    return True


def _reset_periods(device: Device) -> None:
    today = date.today()
    if device.usage_today_date != today:
        device.usage_today_date = today
        device.usage_today = 0
    if device.usage_month_year != today.year or device.usage_month_month != today.month:
        device.usage_month_year = today.year
        device.usage_month_month = today.month
        device.usage_month_count = 0


def _enforce_limits(device: Device, license_obj: License, units: int) -> None:
    if units <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Units must be positive")

    _reset_periods(device)

    period = (license_obj.quota_period or "").upper()
    limit = license_obj.quota_limit or 0
    if limit <= 0:
        return

    if period == "DAILY":
        if device.usage_today + units > limit:
            device.is_blocked = True
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Daily limit exceeded")
    elif period == "MONTHLY":
        if device.usage_month_count + units > limit:
            device.is_blocked = True
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Monthly limit exceeded")
    elif period == "TOTAL":
        if device.total_usage + units > limit:
            device.is_blocked = True
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Total limit exceeded")
    elif period == "NONE":
        return
    else:
        return


def _remaining_quota(device: Device, license_obj: License) -> int | None:
    limit = license_obj.quota_limit or 0
    if limit <= 0:
        return None
    period = (license_obj.quota_period or "").upper()
    if period == "DAILY":
        used = device.usage_today
    elif period == "MONTHLY":
        used = device.usage_month_count
    elif period == "TOTAL":
        used = device.total_usage
    elif period == "NONE":
        return None
    else:
        return None
    remaining = limit - used
    return remaining if remaining > 0 else 0


def _usage_payload(device: Device, license_obj: License) -> UsageResponse:
    return UsageResponse(
        device_id=device.id,
        license_id=license_obj.id,
        usage_today=device.usage_today,
        usage_today_date=device.usage_today_date,
        usage_month_count=device.usage_month_count,
        usage_month_month=device.usage_month_month,
        usage_month_year=device.usage_month_year,
        total_usage=device.total_usage,
        quota_type=license_obj.quota_type,
        quota_limit=license_obj.quota_limit,
        quota_period=license_obj.quota_period,
        quota_remaining=_remaining_quota(device, license_obj),
        license_active=license_obj.is_active,
        license_expires_at=license_obj.expires_at,
    )


@router.post("/translate", response_model=TranslateResponse)
def translate(
    payload: TranslateRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> TranslateResponse:
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")

    units = payload.units or 1
    _enforce_limits(device, license_obj, units)

    translated = request_translation(db, payload.text, payload.source, payload.target)

    device.usage_today += units
    device.usage_month_count += units
    device.total_usage += units
    device.last_seen_at = datetime.utcnow()

    log = TranslationLog(
        device_id=device.id,
        source=payload.source,
        target=payload.target,
        original_text=payload.text,
        translated_text=translated,
        units=units,
    )
    db.add(device)
    db.add(log)
    db.commit()

    return TranslateResponse(translatedText=translated)


@router.post("/translate-batch", response_model=TranslateBatchResponse)
def translate_batch(
    payload: TranslateBatchRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> TranslateBatchResponse:
    """
    Traduz múltiplos textos de uma vez usando LibreTranslate.
    Envia todos os textos em uma única requisição HTTP.
    """
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")

    # Calcula units: ou usa o especificado, ou conta número de textos
    units = payload.units if payload.units is not None else len(payload.texts)
    _enforce_limits(device, license_obj, units)

    # Traduz todos os textos de uma vez
    translations = request_translation_batch(db, payload.texts, payload.source, payload.target)

    # Atualiza usage
    device.usage_today += units
    device.usage_month_count += units
    device.total_usage += units
    device.last_seen_at = datetime.utcnow()

    # Log da tradução batch
    log = TranslationLog(
        device_id=device.id,
        source=payload.source,
        target=payload.target,
        original_text=f"[BATCH {len(payload.texts)} texts]",
        translated_text=f"[BATCH {len(translations)} translations]",
        units=units,
    )
    db.add(device)
    db.add(log)
    db.commit()

    return TranslateBatchResponse(translations=translations)


@router.post("/translate-nllb", response_model=TranslateResponse)
def translate_nllb(
    payload: TranslateRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> TranslateResponse:
    """
    Traduz usando NLLB-200.
    Códigos de língua: por_Latn, eng_Latn, fra_Latn, spa_Latn, etc.
    """
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")

    units = payload.units or 1
    _enforce_limits(device, license_obj, units)

    from api.services import request_nllb_translation
    translated = request_nllb_translation(db, payload.text, payload.source, payload.target)

    device.usage_today += units
    device.usage_month_count += units
    device.total_usage += units
    device.last_seen_at = datetime.utcnow()

    log = TranslationLog(
        device_id=device.id,
        source=payload.source,
        target=payload.target,
        original_text=payload.text,
        translated_text=translated,
        units=units,
    )
    db.add(device)
    db.add(log)
    db.commit()

    return TranslateResponse(translatedText=translated)


@router.post("/translate-nllb-batch", response_model=TranslateBatchResponse)
def translate_nllb_batch(
    payload: TranslateBatchRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> TranslateBatchResponse:
    """
    Traduz múltiplos textos usando NLLB-200 em paralelo.
    Códigos de língua: por_Latn, eng_Latn, fra_Latn, etc.
    """
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")

    units = payload.units if payload.units is not None else len(payload.texts)
    _enforce_limits(device, license_obj, units)

    from api.services import request_nllb_translation_batch
    translations = request_nllb_translation_batch(db, payload.texts, payload.source, payload.target)

    device.usage_today += units
    device.usage_month_count += units
    device.total_usage += units
    device.last_seen_at = datetime.utcnow()

    log = TranslationLog(
        device_id=device.id,
        source=payload.source,
        target=payload.target,
        original_text=f"[NLLB-BATCH {len(payload.texts)} texts]",
        translated_text=f"[NLLB-BATCH {len(translations)} translations]",
        units=units,
    )
    db.add(device)
    db.add(log)
    db.commit()

    return TranslateBatchResponse(translations=translations)


@router.post("/ai/translate", response_model=TranslateResponse)
def translate_ai(
    payload: AITranslateRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> TranslateResponse:
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")

    units = payload.units or 1
    _enforce_limits(device, license_obj, units)

    translated = request_ai_translate(
        db,
        payload.text,
        payload.source,
        payload.target,
        glossary=payload.glossary,
    )

    device.usage_today += units
    device.usage_month_count += units
    device.total_usage += units
    device.last_seen_at = datetime.utcnow()

    log = TranslationLog(
        device_id=device.id,
        source=payload.source,
        target=payload.target,
        original_text=payload.text,
        translated_text=translated,
        units=units,
    )
    db.add(device)
    db.add(log)
    db.commit()

    return TranslateResponse(translatedText=translated)


@router.post("/ai/evaluate", response_model=AIEvaluateResponse)
def evaluate_ai(
    payload: AIEvaluateRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> AIEvaluateResponse:
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")
    items = request_ai_evaluate(db, payload.texts, payload.source, payload.target)
    return AIEvaluateResponse(items=items)


@router.post("/ai/glossary", response_model=AIGlossaryResponse)
def glossary_ai(
    payload: AIGlossaryRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> AIGlossaryResponse:
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")
    glossary = request_ai_glossary(db, payload.texts, payload.source, payload.target)
    return AIGlossaryResponse(glossary=glossary)


@router.post("/quota/consume", response_model=ConsumeResponse)
def consume_quota(
    payload: ConsumeRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> ConsumeResponse:
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")

    units = payload.units or 1
    _enforce_limits(device, license_obj, units)

    device.usage_today += units
    device.usage_month_count += units
    device.total_usage += units
    device.last_seen_at = datetime.utcnow()

    db.add(device)
    db.commit()

    return ConsumeResponse(
        status="ok",
        usage_today=device.usage_today,
        usage_month_count=device.usage_month_count,
        total_usage=device.total_usage,
    )


@router.get("/usage", response_model=UsageResponse)
def usage(
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> UsageResponse:
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    _reset_periods(device)
    db.add(device)
    db.commit()
    return _usage_payload(device, license_obj)


@router.get("/usage/device/{device_id}", response_model=UsageResponse)
def usage_by_device(
    device_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> UsageResponse:
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    _reset_periods(device)
    db.add(device)
    db.commit()
    return _usage_payload(device, license_obj)


@router.get("/usage/license/{license_id}", response_model=list[UsageResponse])
def usage_by_license(
    license_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> list[UsageResponse]:
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    devices = db.query(Device).filter(Device.license_id == license_id).all()
    responses: list[UsageResponse] = []
    for device in devices:
        _reset_periods(device)
        db.add(device)
        responses.append(_usage_payload(device, license_obj))
    db.commit()
    return responses


@router.get("/languages")
def languages(db: Session = Depends(get_db), device: Device = Depends(get_current_device)):
    return request_languages(db)


@router.post("/ai/translate-batch")
def translate_batch_ai(
    payload: dict,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):
    """
    Traduz múltiplos tokens de uma vez usando IA.

    Body:
    {
        "tokens": [
            {"location": "Paragrafo 1", "text": "Hello"},
            {"location": "Paragrafo 2", "text": "World"}
        ],
        "source": "en",
        "target": "pt",
        "glossary": {"Hello": "Olá"}  # opcional
    }

    Response:
    {
        "translations": [
            {"location": "Paragrafo 1", "translation": "Olá"},
            {"location": "Paragrafo 2", "translation": "Mundo"}
        ]
    }
    """
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")
    if device.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")

    tokens = payload.get("tokens", [])
    source = payload.get("source")
    target = payload.get("target")
    glossary = payload.get("glossary")

    if not tokens or not source or not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields")

    # Calcula units baseado no número de tokens
    units = len(tokens)
    _enforce_limits(device, license_obj, units)

    # Traduz usando IA provider configurado
    from api.services import get_ai_provider

    try:
        provider = get_ai_provider(db)
        translations = provider.translate_batch(tokens, source, target, glossary)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Translation error: {str(e)}")

    # Atualiza usage
    device.usage_today += units
    device.usage_month_count += units
    device.total_usage += units
    device.last_seen_at = datetime.utcnow()

    # Log da tradução em lote (combina todos os textos)
    original_combined = "\n".join([t.get("text", "") for t in tokens])
    translated_combined = "\n".join([t.get("translation", "") for t in translations])

    log = TranslationLog(
        device_id=device.id,
        source=source,
        target=target,
        original_text=original_combined,
        translated_text=translated_combined,
        units=units,
    )

    db.add(device)
    db.add(log)
    db.commit()

    return {"translations": translations}

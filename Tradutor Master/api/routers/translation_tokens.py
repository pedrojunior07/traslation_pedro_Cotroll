"""
Endpoints para consultar informações detalhadas de tokens de tradução.
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from api.database import get_db
from api.models import Device, TranslationLog, TranslationToken, User
from api.schemas import TranslationTokenOut, TranslationLogWithTokens
from api.security import get_current_device, get_current_superadmin

router = APIRouter(tags=["translation_tokens"])


@router.get("/translation/{translation_log_id}/tokens", response_model=List[TranslationTokenOut])
def get_translation_tokens(
    translation_log_id: int,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> List[TranslationTokenOut]:
    """
    Retorna todos os tokens de uma tradução específica.

    O dispositivo só pode acessar suas próprias traduções.
    """
    # Verifica se o translation_log pertence ao dispositivo
    log = db.query(TranslationLog).filter(
        TranslationLog.id == translation_log_id,
        TranslationLog.device_id == device.id
    ).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation log not found or access denied"
        )

    # Busca todos os tokens
    tokens = db.query(TranslationToken).filter(
        TranslationToken.translation_log_id == translation_log_id
    ).order_by(TranslationToken.id).all()

    # Converte warnings de JSON para lista
    result = []
    for token in tokens:
        token_dict = {
            "id": token.id,
            "location": token.location,
            "original_text": token.original_text,
            "translated_text": token.translated_text,
            "original_length": token.original_length,
            "translated_length": token.translated_length,
            "was_truncated": token.was_truncated,
            "size_ratio": token.size_ratio,
            "units": token.units,
            "warnings": json.loads(token.warnings) if token.warnings else [],
            "created_at": token.created_at,
        }
        result.append(TranslationTokenOut(**token_dict))

    return result


@router.get("/translations/recent", response_model=List[TranslationLogWithTokens])
def get_recent_translations(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
) -> List[TranslationLogWithTokens]:
    """
    Retorna as traduções recentes do dispositivo com seus tokens.

    Args:
        limit: Número máximo de traduções a retornar (1-100)
    """
    # Busca logs recentes do dispositivo
    logs = db.query(TranslationLog).filter(
        TranslationLog.device_id == device.id
    ).order_by(TranslationLog.created_at.desc()).limit(limit).all()

    result = []
    for log in logs:
        # Busca tokens do log
        tokens = db.query(TranslationToken).filter(
            TranslationToken.translation_log_id == log.id
        ).order_by(TranslationToken.id).all()

        # Converte tokens
        token_list = []
        for token in tokens:
            token_dict = {
                "id": token.id,
                "location": token.location,
                "original_text": token.original_text,
                "translated_text": token.translated_text,
                "original_length": token.original_length,
                "translated_length": token.translated_length,
                "was_truncated": token.was_truncated,
                "size_ratio": token.size_ratio,
                "units": token.units,
                "warnings": json.loads(token.warnings) if token.warnings else [],
                "created_at": token.created_at,
            }
            token_list.append(TranslationTokenOut(**token_dict))

        log_with_tokens = TranslationLogWithTokens(
            id=log.id,
            device_id=log.device_id,
            source=log.source,
            target=log.target,
            original_text=log.original_text,
            translated_text=log.translated_text,
            units=log.units,
            created_at=log.created_at,
            tokens=token_list,
        )
        result.append(log_with_tokens)

    return result


@router.get("/admin/translation/{translation_log_id}/tokens", response_model=List[TranslationTokenOut])
def admin_get_translation_tokens(
    translation_log_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> List[TranslationTokenOut]:
    """
    Admin: Retorna todos os tokens de uma tradução específica.
    """
    # Verifica se o translation_log existe
    log = db.query(TranslationLog).filter(
        TranslationLog.id == translation_log_id
    ).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation log not found"
        )

    # Busca todos os tokens
    tokens = db.query(TranslationToken).filter(
        TranslationToken.translation_log_id == translation_log_id
    ).order_by(TranslationToken.id).all()

    # Converte warnings de JSON para lista
    result = []
    for token in tokens:
        token_dict = {
            "id": token.id,
            "location": token.location,
            "original_text": token.original_text,
            "translated_text": token.translated_text,
            "original_length": token.original_length,
            "translated_length": token.translated_length,
            "was_truncated": token.was_truncated,
            "size_ratio": token.size_ratio,
            "units": token.units,
            "warnings": json.loads(token.warnings) if token.warnings else [],
            "created_at": token.created_at,
        }
        result.append(TranslationTokenOut(**token_dict))

    return result


@router.get("/tokens/statistics")
def get_token_statistics(
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):
    """
    Retorna estatísticas sobre os tokens traduzidos pelo dispositivo.
    """
    # Busca todos os tokens do dispositivo através dos logs
    from sqlalchemy import func

    stats = db.query(
        func.count(TranslationToken.id).label("total_tokens"),
        func.sum(TranslationToken.original_length).label("total_original_chars"),
        func.sum(TranslationToken.translated_length).label("total_translated_chars"),
        func.avg(TranslationToken.size_ratio).label("avg_size_ratio"),
        func.sum(func.cast(TranslationToken.was_truncated, db.dialect.name == 'postgresql' and 'integer' or None)).label("truncated_count"),
    ).join(
        TranslationLog, TranslationToken.translation_log_id == TranslationLog.id
    ).filter(
        TranslationLog.device_id == device.id
    ).first()

    return {
        "total_tokens": stats.total_tokens or 0,
        "total_original_chars": stats.total_original_chars or 0,
        "total_translated_chars": stats.total_translated_chars or 0,
        "average_size_ratio": float(stats.avg_size_ratio) if stats.avg_size_ratio else 0.0,
        "truncated_count": stats.truncated_count or 0,
    }

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import License, User
from api.schemas import LicenseCreate, LicenseOut, LicenseUpdate
from api.security import get_current_superadmin

router = APIRouter(prefix="/licenses", tags=["licenses"])


def _generate_key() -> str:
    return f"LIC-{uuid.uuid4().hex.upper()}"


def _apply_duration(expires_at: datetime | None, duration_days: int | None) -> datetime | None:
    if expires_at is not None:
        return expires_at
    if duration_days is None:
        return None
    if duration_days <= 0:
        return None
    return datetime.utcnow() + timedelta(days=duration_days)


@router.post("", response_model=LicenseOut)
def create_license(
    payload: LicenseCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    license_obj = License(
        key=_generate_key(),
        type=payload.type,
        max_devices=1,
        quota_type=payload.quota_type,
        quota_limit=payload.quota_limit,
        quota_period=payload.quota_period,
        duration_days=payload.duration_days,
        is_active=payload.is_active,
        expires_at=_apply_duration(payload.expires_at, payload.duration_days),
    )
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return license_obj


@router.get("", response_model=list[LicenseOut])
def list_licenses(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    return db.query(License).order_by(License.id.asc()).all()


@router.get("/{license_id}", response_model=LicenseOut)
def get_license(
    license_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    return license_obj


@router.patch("/{license_id}", response_model=LicenseOut)
def update_license(
    license_id: int,
    payload: LicenseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    if payload.type is not None:
        license_obj.type = payload.type
    if payload.max_devices is not None:
        license_obj.max_devices = 1
    if payload.quota_type is not None:
        license_obj.quota_type = payload.quota_type
    if payload.quota_limit is not None:
        license_obj.quota_limit = payload.quota_limit
    if payload.quota_period is not None:
        license_obj.quota_period = payload.quota_period
    if payload.duration_days is not None:
        license_obj.duration_days = payload.duration_days
    if payload.expires_at is not None or payload.duration_days is not None:
        license_obj.expires_at = _apply_duration(payload.expires_at, payload.duration_days)
    if payload.is_active is not None:
        license_obj.is_active = payload.is_active
    license_obj.max_devices = 1
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return license_obj


@router.post("/{license_id}/revoke")
def revoke_license(
    license_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    license_obj.is_active = False
    db.add(license_obj)
    db.commit()
    return {"status": "revoked"}


@router.post("/{license_id}/rotate-key", response_model=LicenseOut)
def rotate_key(
    license_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    license_obj.key = _generate_key()
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return license_obj

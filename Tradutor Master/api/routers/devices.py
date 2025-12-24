from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.config import Settings
from api.database import get_db
from api.models import Device, License, User
from api.schemas import DeviceOut, DeviceRegisterRequest, DeviceTokenResponse, DeviceUpdate
from api.security import create_token, get_current_superadmin

router = APIRouter(prefix="/devices", tags=["devices"])
settings = Settings()


def _license_is_valid(license_obj: License) -> bool:
    if not license_obj.is_active:
        return False
    if license_obj.expires_at and license_obj.expires_at < datetime.utcnow():
        return False
    return True


@router.post("/register", response_model=DeviceTokenResponse)
def register_device(payload: DeviceRegisterRequest, db: Session = Depends(get_db)) -> DeviceTokenResponse:
    license_obj = db.query(License).filter(License.key == payload.license_key).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid license")

    if license_obj.max_devices == 1:
        other_device = (
            db.query(Device)
            .filter(Device.license_id == license_obj.id, Device.device_id != payload.device_id)
            .first()
        )
        if other_device:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device limit reached")

    existing = (
        db.query(Device)
        .filter(Device.license_id == license_obj.id, Device.device_id == payload.device_id)
        .first()
    )
    if existing and existing.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device blocked")

    if not existing:
        active_devices = (
            db.query(Device)
            .filter(Device.license_id == license_obj.id, Device.is_blocked == False)
            .count()
        )
        if license_obj.max_devices > 0 and active_devices >= license_obj.max_devices:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device limit reached")
        today = date.today()
        existing = Device(
            license_id=license_obj.id,
            device_id=payload.device_id,
            device_name=payload.device_name,
            last_seen_at=datetime.utcnow(),
            usage_today=0,
            usage_today_date=today,
            usage_month_count=0,
            usage_month_month=today.month,
            usage_month_year=today.year,
            total_usage=0,
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)
    else:
        existing.device_name = payload.device_name or existing.device_name
        existing.last_seen_at = datetime.utcnow()
        db.add(existing)
        db.commit()

    token = create_token(str(existing.id), "device", settings.device_token_exp_minutes)
    return DeviceTokenResponse(device_token=token)


@router.get("", response_model=list[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    return db.query(Device).order_by(Device.id.asc()).all()


@router.patch("/{device_id}", response_model=DeviceOut)
def update_device(
    device_id: int,
    payload: DeviceUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if payload.is_blocked is not None:
        device.is_blocked = payload.is_blocked
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.post("/{device_id}/reset-usage")
def reset_usage(
    device_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    today = date.today()
    device.usage_today = 0
    device.usage_today_date = today
    device.usage_month_count = 0
    device.usage_month_month = today.month
    device.usage_month_year = today.year
    db.add(device)
    db.commit()
    return {"status": "ok"}

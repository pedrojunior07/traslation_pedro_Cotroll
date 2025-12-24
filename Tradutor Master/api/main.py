from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from api.config import Settings
from api.database import Base, SessionLocal, engine
from api.models import AIConfig, TranslateConfig, User
from api.routers import auth, devices, licenses, settings, translate, users, web_admin
from api.security import hash_password

settings_cfg = Settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings_cfg.superadmin_user).first()
        if not admin:
            admin = User(
                username=settings_cfg.superadmin_user,
                password_hash=hash_password(settings_cfg.superadmin_password),
                is_superadmin=True,
                is_active=True,
            )
            db.add(admin)
        if not db.query(AIConfig).first():
            db.add(AIConfig())
        if not db.query(TranslateConfig).first():
            db.add(TranslateConfig())
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Tradutor Master API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(licenses.router)
app.include_router(devices.router)
app.include_router(settings.router)
app.include_router(translate.router)
app.include_router(web_admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}

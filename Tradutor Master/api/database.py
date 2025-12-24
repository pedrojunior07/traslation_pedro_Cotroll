from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from api.config import Settings, build_db_url

settings = Settings()
engine = create_engine(build_db_url(settings), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


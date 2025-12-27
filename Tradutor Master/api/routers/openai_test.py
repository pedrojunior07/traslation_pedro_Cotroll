from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import openai
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AIConfig, User
from .web_admin import get_admin

router = APIRouter(
    prefix="/admin/openai",
    tags=["admin-openai"],
)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

class APIKey(BaseModel):
    api_key: str | None = None

@router.get("/test-page", response_class=HTMLResponse)
async def get_test_page(
    request: Request,
    admin: User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    cfg = db.query(AIConfig).first()
    saved_key_tail = cfg.api_key[-4:] if cfg and cfg.api_key else ""
    return templates.TemplateResponse(
        "admin/openai_test.html",
        {"request": request, "admin": admin, "saved_key_tail": saved_key_tail},
    )

@router.post("/test")
async def test_openai_api(
    api_key_data: APIKey,
    admin: User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    try:
        api_key = api_key_data.api_key
        if not api_key:
            cfg = db.query(AIConfig).first()
            api_key = cfg.api_key if cfg else None
        if not api_key:
            raise HTTPException(status_code=400, detail="No API key provided or saved.")
        client = openai.OpenAI(api_key=api_key)
        response = client.models.list()
        return {"status": "success", "models": [model.id for model in response.data]}
    except openai.AuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"Invalid API Key: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

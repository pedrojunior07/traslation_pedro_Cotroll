import json

import requests
from sqlalchemy.orm import Session

from api.config import Settings
from api.models import AIConfig, TranslateConfig

settings = Settings()


def get_translate_config(db: Session) -> TranslateConfig:
    return TranslateConfig(base_url=settings.translate_base_url, timeout=settings.translate_timeout)


def get_ai_config(db: Session) -> AIConfig:
    cfg = db.query(AIConfig).first()
    if cfg:
        return cfg
    cfg = AIConfig()
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


def request_translation(db: Session, text: str, source: str, target: str) -> str:
    cfg = get_translate_config(db)
    base = cfg.base_url.rstrip("/")
    payload = {"q": text, "source": source, "target": target}
    url = base + "/translate"
    resp = requests.post(url, json=payload, timeout=cfg.timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Translate API error: {resp.status_code} {resp.text}")
    data = resp.json()
    translated = data.get("translatedText")
    if not isinstance(translated, str):
        raise RuntimeError("Translate API missing translatedText")
    return translated


def request_languages(db: Session):
    cfg = get_translate_config(db)
    base = cfg.base_url.rstrip("/")
    url = base + "/languages"
    resp = requests.get(url, timeout=cfg.timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Languages API error: {resp.status_code} {resp.text}")
    return resp.json()


def _openai_request(cfg: AIConfig, messages: list[dict], timeout: float) -> str:
    if not cfg.enabled or not cfg.api_key:
        raise RuntimeError("AI disabled or missing API key")
    url = f"{cfg.base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": cfg.model,
        "temperature": 0,
        "messages": messages,
    }
    headers = {"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"AI API error: {resp.status_code} {resp.text}")
    data = resp.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("AI API empty response")
    return content


def request_ai_translate(
    db: Session,
    text: str,
    source: str,
    target: str,
    glossary: dict[str, str] | None = None,
) -> str:
    cfg = get_ai_config(db)
    system = "Translate the input text. Return only the translated text."
    glossary_block = ""
    if glossary:
        glossary_lines = [f"{k} => {v}" for k, v in glossary.items()]
        glossary_block = "\nGlossary:\n" + "\n".join(glossary_lines)
    prompt = (
        f"Source language: {source}\nTarget language: {target}\n"
        f"{glossary_block}\n\nInput:\n{text}\n"
    )
    content = _openai_request(
        cfg,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        timeout=settings.translate_timeout,
    )
    return content.strip()


def request_ai_evaluate(
    db: Session,
    texts: list[str],
    source: str,
    target: str,
) -> list[dict]:
    cfg = get_ai_config(db)
    system = (
        "You are a translation reviewer. For each text, decide if it should be translated. "
        "Return JSON only."
    )
    payload = {
        "source": source,
        "target": target,
        "items": texts,
    }
    prompt = (
        "Return JSON with schema: {\"items\":[{\"text\":\"...\",\"translatable\":true,\"reason\":\"...\"}]}\n"
        f"Input:\n{payload}"
    )
    content = _openai_request(
        cfg,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        timeout=settings.translate_timeout,
    )
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("AI evaluate invalid JSON") from exc
    items = data.get("items")
    if not isinstance(items, list):
        raise RuntimeError("AI evaluate invalid response")
    results = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        text = entry.get("text")
        translatable = entry.get("translatable")
        if isinstance(text, str) and isinstance(translatable, bool):
            results.append(
                {"text": text, "translatable": translatable, "reason": entry.get("reason")}
            )
    return results


def request_ai_glossary(
    db: Session,
    texts: list[str],
    source: str,
    target: str,
) -> dict[str, str]:
    cfg = get_ai_config(db)
    system = "Build a glossary of important terms for translation. Return JSON only."
    payload = {
        "source": source,
        "target": target,
        "items": texts,
    }
    prompt = (
        "Return JSON with schema: {\"glossary\":{\"term\":\"translation\"}}. "
        "Only include terms that should be preserved consistently.\n"
        f"Input:\n{payload}"
    )
    content = _openai_request(
        cfg,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        timeout=settings.translate_timeout,
    )
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("AI glossary invalid JSON") from exc
    glossary = data.get("glossary")
    if not isinstance(glossary, dict):
        raise RuntimeError("AI glossary invalid response")
    cleaned: dict[str, str] = {}
    for key, value in glossary.items():
        if isinstance(key, str) and isinstance(value, str):
            cleaned[key] = value
    return cleaned

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
    """
    Traduz texto usando o provider configurado (LibreTranslate ou NLLB).
    """
    cfg = get_translate_config(db)

    # Detecta provider
    if cfg.provider == "nllb":
        return request_nllb_translation(db, text, source, target)

    # Default: LibreTranslate
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


def request_translation_batch(db: Session, texts: list[str], source: str, target: str) -> list[str]:
    """
    Traduz múltiplos textos de uma vez usando o provider configurado.
    LibreTranslate: usa batch nativo
    NLLB: usa requisições paralelas
    """
    cfg = get_translate_config(db)

    # Detecta provider
    if cfg.provider == "nllb":
        return request_nllb_translation_batch(db, texts, source, target)

    # Default: LibreTranslate com batch nativo
    base = cfg.base_url.rstrip("/")
    url = base + "/translate"

    # LibreTranslate aceita q como array de strings
    payload = {"q": texts, "source": source, "target": target}

    # Timeout maior para batch (proporcional ao número de textos)
    timeout = max(cfg.timeout, len(texts) * 2)

    resp = requests.post(url, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Translate API error: {resp.status_code} {resp.text}")

    data = resp.json()

    # Resposta é array de {"translatedText": "..."}
    if not isinstance(data, list):
        raise RuntimeError("Translate API batch response must be array")

    translations = []
    for item in data:
        if not isinstance(item, dict):
            raise RuntimeError("Translate API batch item must be dict")
        translated = item.get("translatedText")
        if not isinstance(translated, str):
            raise RuntimeError("Translate API batch item missing translatedText")
        translations.append(translated)

    return translations


def request_nllb_translation(db: Session, text: str, source: str, target: str) -> str:
    """
    Traduz usando NLLB-200 API.
    Códigos de língua NLLB: por_Latn, eng_Latn, fra_Latn, etc.
    """
    cfg = get_translate_config(db)
    base = cfg.nllb_base_url.rstrip("/")
    url = base + "/translate"

    payload = {
        "text": text,
        "source_lang": source,
        "target_lang": target,
        "max_new_tokens": 256
    }

    resp = requests.post(url, json=payload, timeout=cfg.timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"NLLB API error: {resp.status_code} {resp.text}")

    data = resp.json()
    translated = data.get("translated")
    if not isinstance(translated, str):
        raise RuntimeError("NLLB API missing 'translated' field")
    return translated


def request_nllb_translation_batch(db: Session, texts: list[str], source: str, target: str) -> list[str]:
    """
    Traduz múltiplos textos usando NLLB-200.
    Como NLLB não tem endpoint batch nativo, faz requisições em paralelo.
    """
    import concurrent.futures

    cfg = get_translate_config(db)
    base = cfg.nllb_base_url.rstrip("/")
    url = base + "/translate"

    def translate_single(text: str) -> str:
        payload = {
            "text": text,
            "source_lang": source,
            "target_lang": target,
            "max_new_tokens": 256
        }
        resp = requests.post(url, json=payload, timeout=cfg.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"NLLB API error: {resp.status_code} {resp.text}")
        data = resp.json()
        translated = data.get("translated")
        if not isinstance(translated, str):
            raise RuntimeError("NLLB API missing 'translated' field")
        return translated

    # Traduz em paralelo (max 10 threads simultâneas)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        translations = list(executor.map(translate_single, texts))

    return translations


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


# ============================================================================
# Multi-Provider AI Translation System
# ============================================================================


class AIProvider:
    """Classe base para provedores de IA."""

    def translate_batch(
        self,
        tokens: list[dict],
        source: str,
        target: str,
        glossary: dict[str, str] | None = None,
    ) -> list[dict]:
        """Traduz lote de tokens.

        Args:
            tokens: Lista de {"location": str, "text": str}
            source: Idioma origem (ex: "en")
            target: Idioma destino (ex: "pt")
            glossary: Glossário opcional {termo: tradução}

        Returns:
            Lista de {"location": str, "translation": str}
        """
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """Provedor OpenAI para tradução em lote."""

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float, max_retries: int):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def translate_batch(
        self,
        tokens: list[dict],
        source: str,
        target: str,
        glossary: dict[str, str] | None = None,
    ) -> list[dict]:
        """Traduz lote usando OpenAI API."""

        # Construir prompt com todos os tokens
        system = "You are a professional translator. Translate each text exactly as requested, maintaining the order."

        glossary_block = ""
        if glossary:
            glossary_lines = [f"{k} => {v}" for k, v in glossary.items()]
            glossary_block = "\nGlossary (use these translations):\n" + "\n".join(glossary_lines) + "\n"

        # Formato JSON para tokens
        tokens_json = json.dumps([{"location": t["location"], "text": t["text"]} for t in tokens], ensure_ascii=False)

        prompt = (
            f"Translate from {source} to {target}.\n"
            f"{glossary_block}\n"
            f"Input JSON:\n{tokens_json}\n\n"
            f"Return JSON with schema: {{\"translations\": [{{\"location\": \"...\", \"translation\": \"...\"}}]}}\n"
            f"Keep the same order and locations."
        )

        # Fazer request com retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                url = f"{self.base_url}/chat/completions"
                payload = {
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)

                if resp.status_code != 200:
                    raise RuntimeError(f"OpenAI API error: {resp.status_code} {resp.text}")

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content.strip():
                    raise RuntimeError("OpenAI API empty response")

                # Parse JSON response
                result = json.loads(content)
                translations = result.get("translations", [])

                if not isinstance(translations, list):
                    raise RuntimeError("Invalid response format from OpenAI")

                return translations

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue

        raise RuntimeError(f"OpenAI translation failed after {self.max_retries} attempts: {last_error}")


class GeminiProvider(AIProvider):
    """Provedor Google Gemini para tradução em lote."""

    def __init__(self, api_key: str, model: str, timeout: float, max_retries: int):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def translate_batch(
        self,
        tokens: list[dict],
        source: str,
        target: str,
        glossary: dict[str, str] | None = None,
    ) -> list[dict]:
        """Traduz lote usando Gemini API."""

        # Construir prompt
        glossary_block = ""
        if glossary:
            glossary_lines = [f"{k} => {v}" for k, v in glossary.items()]
            glossary_block = "\nGlossary (use these translations):\n" + "\n".join(glossary_lines) + "\n"

        tokens_json = json.dumps([{"location": t["location"], "text": t["text"]} for t in tokens], ensure_ascii=False)

        prompt = (
            f"You are a professional translator. Translate from {source} to {target}.\n"
            f"{glossary_block}\n"
            f"Input JSON:\n{tokens_json}\n\n"
            f"Return JSON with schema: {{\"translations\": [{{\"location\": \"...\", \"translation\": \"...\"}}]}}\n"
            f"Keep the same order and locations. Return only valid JSON, no markdown."
        )

        # Fazer request com retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0,
                    }
                }
                headers = {
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                }

                resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)

                if resp.status_code != 200:
                    raise RuntimeError(f"Gemini API error: {resp.status_code} {resp.text}")

                data = resp.json()

                # Extrair conteúdo da resposta
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError(f"Gemini API no candidates in response: {data}")

                content_data = candidates[0].get("content", {})
                parts = content_data.get("parts", [])
                if not parts:
                    raise RuntimeError(f"Gemini API no parts in response: {data}")

                content = parts[0].get("text", "")

                if not content.strip():
                    raise RuntimeError("Gemini API empty response")

                # Remove markdown code blocks se houver
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                # Parse JSON response
                try:
                    result = json.loads(content)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Gemini returned invalid JSON. Content: {content[:200]}...") from e

                translations = result.get("translations", [])

                if not isinstance(translations, list):
                    raise RuntimeError(f"Invalid response format from Gemini. Expected list, got: {type(translations)}")

                return translations

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue

        raise RuntimeError(f"Gemini translation failed after {self.max_retries} attempts: {last_error}")


class GrokProvider(AIProvider):
    """Provedor xAI Grok para tradução em lote."""

    def __init__(self, api_key: str, model: str, timeout: float, max_retries: int):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def translate_batch(
        self,
        tokens: list[dict],
        source: str,
        target: str,
        glossary: dict[str, str] | None = None,
    ) -> list[dict]:
        """Traduz lote usando Grok API."""

        # Construir prompt
        system = "You are a professional translator. Translate each text exactly as requested, maintaining the order."

        glossary_block = ""
        if glossary:
            glossary_lines = [f"{k} => {v}" for k, v in glossary.items()]
            glossary_block = "\nGlossary (use these translations):\n" + "\n".join(glossary_lines) + "\n"

        tokens_json = json.dumps([{"location": t["location"], "text": t["text"]} for t in tokens], ensure_ascii=False)

        prompt = (
            f"Translate from {source} to {target}.\n"
            f"{glossary_block}\n"
            f"Input JSON:\n{tokens_json}\n\n"
            f"Return JSON with schema: {{\"translations\": [{{\"location\": \"...\", \"translation\": \"...\"}}]}}\n"
            f"Keep the same order and locations."
        )

        # Fazer request com retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                url = "https://api.x.ai/v1/chat/completions"
                payload = {
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)

                if resp.status_code != 200:
                    raise RuntimeError(f"Grok API error: {resp.status_code} {resp.text}")

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content.strip():
                    raise RuntimeError("Grok API empty response")

                # Parse JSON response
                result = json.loads(content)
                translations = result.get("translations", [])

                if not isinstance(translations, list):
                    raise RuntimeError("Invalid response format from Grok")

                return translations

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue

        raise RuntimeError(f"Grok translation failed after {self.max_retries} attempts: {last_error}")


def get_ai_provider(db: Session) -> AIProvider:
    """Retorna o provedor de IA configurado."""
    from fastapi import HTTPException

    config = db.query(AIConfig).first()

    if not config or not config.enabled:
        raise HTTPException(status_code=400, detail="IA não configurada ou desabilitada")

    if config.provider == "openai":
        if not config.api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key não configurada")
        return OpenAIProvider(
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    elif config.provider == "gemini":
        if not config.gemini_api_key:
            raise HTTPException(status_code=400, detail="Gemini API key não configurada")
        return GeminiProvider(
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    elif config.provider == "grok":
        if not config.grok_api_key:
            raise HTTPException(status_code=400, detail="Grok API key não configurada")
        return GrokProvider(
            api_key=config.grok_api_key,
            model=config.grok_model,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    else:
        raise HTTPException(status_code=400, detail=f"Provedor desconhecido: {config.provider}")

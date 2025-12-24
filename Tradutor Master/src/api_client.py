import json
from typing import Any, Dict, List, Optional

import requests


class APIError(RuntimeError):
    pass


def _normalize_base_url(base_url: str) -> str:
    base = base_url.strip()
    if not base:
        raise ValueError("Base URL vazia.")
    return base.rstrip("/")


def register_device(
    base_url: str,
    license_key: str,
    device_id: str,
    device_name: Optional[str] = None,
    timeout: float = 10.0,
) -> str:
    base = _normalize_base_url(base_url)
    url = f"{base}/devices/register"
    payload = {"license_key": license_key, "device_id": device_id, "device_name": device_name}
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise APIError(f"Falha ao conectar no endpoint de registro: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao registrar dispositivo ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao registrar dispositivo.") from exc

    token = data.get("device_token")
    if not isinstance(token, str):
        raise APIError("Resposta da API sem device_token.")
    return token


def get_languages(base_url: str, device_token: str, timeout: float = 10.0) -> List[Dict[str, Any]]:
    base = _normalize_base_url(base_url)
    url = f"{base}/languages"
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {device_token}"}, timeout=timeout)
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise APIError(f"Falha ao conectar no endpoint de linguas: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao obter linguas ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao obter linguas.") from exc

    if not isinstance(data, list):
        raise APIError("Formato inesperado do endpoint /languages.")
    return data


def translate_text(
    base_url: str,
    device_token: str,
    text: str,
    source: str,
    target: str,
    units: Optional[int] = None,
    timeout: float = 15.0,
) -> str:
    base = _normalize_base_url(base_url)
    url = f"{base}/translate"
    payload: Dict[str, Any] = {"text": text, "source": source, "target": target}
    if units is not None:
        payload["units"] = units
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {device_token}"},
            timeout=timeout,
        )
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise APIError(f"Falha ao conectar no endpoint de traducao: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao traduzir ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao traduzir.") from exc

    translated = data.get("translatedText")
    if not isinstance(translated, str):
        raise APIError("Resposta da API sem translatedText.")
    return translated


def ai_translate_text(
    base_url: str,
    device_token: str,
    text: str,
    source: str,
    target: str,
    glossary: Optional[Dict[str, str]] = None,
    units: Optional[int] = None,
    timeout: float = 30.0,
) -> str:
    base = _normalize_base_url(base_url)
    url = f"{base}/ai/translate"
    payload: Dict[str, Any] = {"text": text, "source": source, "target": target}
    if glossary:
        payload["glossary"] = glossary
    if units is not None:
        payload["units"] = units
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {device_token}"},
            timeout=timeout,
        )
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise APIError(f"Falha ao conectar no endpoint AI: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao traduzir com IA ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao traduzir com IA.") from exc

    translated = data.get("translatedText")
    if not isinstance(translated, str):
        raise APIError("Resposta da API sem translatedText (IA).")
    return translated


def ai_evaluate_texts(
    base_url: str,
    device_token: str,
    texts: List[str],
    source: str,
    target: str,
    timeout: float = 30.0,
) -> List[Dict[str, Any]]:
    base = _normalize_base_url(base_url)
    url = f"{base}/ai/evaluate"
    payload = {"texts": texts, "source": source, "target": target}
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {device_token}"},
            timeout=timeout,
        )
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise APIError(f"Falha ao conectar no endpoint AI evaluate: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao avaliar com IA ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao avaliar com IA.") from exc

    items = data.get("items")
    if not isinstance(items, list):
        raise APIError("Resposta invalida ao avaliar com IA.")
    return items


def ai_build_glossary(
    base_url: str,
    device_token: str,
    texts: List[str],
    source: str,
    target: str,
    timeout: float = 30.0,
) -> Dict[str, str]:
    base = _normalize_base_url(base_url)
    url = f"{base}/ai/glossary"
    payload = {"texts": texts, "source": source, "target": target}
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {device_token}"},
            timeout=timeout,
        )
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise APIError(f"Falha ao conectar no endpoint AI glossary: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao criar glossario ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao criar glossario.") from exc

    glossary = data.get("glossary")
    if not isinstance(glossary, dict):
        raise APIError("Resposta invalida ao criar glossario.")
    return glossary


def get_usage(base_url: str, device_token: str, timeout: float = 10.0) -> Dict[str, Any]:
    base = _normalize_base_url(base_url)
    url = f"{base}/usage"
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {device_token}"}, timeout=timeout)
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise APIError(f"Falha ao conectar no endpoint de uso: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao obter uso ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao obter uso.") from exc

    if not isinstance(data, dict):
        raise APIError("Formato inesperado do endpoint /usage.")
    return data

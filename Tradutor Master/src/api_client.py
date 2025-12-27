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


def translate_batch(
    base_url: str,
    device_token: str,
    texts: List[str],
    source: str,
    target: str,
    units: Optional[int] = None,
    timeout: float = 60.0,
) -> List[str]:
    """
    Traduz múltiplos textos de uma vez.
    Muito mais rápido que chamar translate_text() múltiplas vezes.
    """
    base = _normalize_base_url(base_url)
    url = f"{base}/translate-batch"
    payload: Dict[str, Any] = {"texts": texts, "source": source, "target": target}
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
        raise APIError(f"Falha ao conectar no endpoint de traducao batch: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao traduzir batch ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao traduzir batch.") from exc

    translations = data.get("translations")
    if not isinstance(translations, list):
        raise APIError("Resposta da API sem translations.")
    return translations


def translate_nllb(
    base_url: str,
    device_token: str,
    text: str,
    source: str,
    target: str,
    units: Optional[int] = None,
    timeout: float = 15.0,
) -> str:
    """
    Traduz usando NLLB-200.
    Códigos de língua: por_Latn, eng_Latn, fra_Latn, spa_Latn, etc.
    """
    base = _normalize_base_url(base_url)
    url = f"{base}/translate-nllb"
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
        raise APIError(f"Falha ao conectar no endpoint NLLB: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao traduzir com NLLB ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao traduzir com NLLB.") from exc

    translated = data.get("translatedText")
    if not isinstance(translated, str):
        raise APIError("Resposta da API NLLB sem translatedText.")
    return translated


def translate_nllb_batch(
    base_url: str,
    device_token: str,
    texts: List[str],
    source: str,
    target: str,
    units: Optional[int] = None,
    timeout: float = 60.0,
) -> List[str]:
    """
    Traduz múltiplos textos usando NLLB-200 em paralelo.
    Códigos de língua: por_Latn, eng_Latn, fra_Latn, etc.
    """
    base = _normalize_base_url(base_url)
    url = f"{base}/translate-nllb-batch"
    payload: Dict[str, Any] = {"texts": texts, "source": source, "target": target}
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
        raise APIError(f"Falha ao conectar no endpoint NLLB batch: {exc}") from exc

    if resp.status_code != 200:
        raise APIError(f"Erro ao traduzir batch com NLLB ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise APIError("Resposta invalida ao traduzir batch com NLLB.") from exc

    translations = data.get("translations")
    if not isinstance(translations, list):
        raise APIError("Resposta da API NLLB sem translations.")
    return translations


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


class APIClient:
    """Cliente orientado a objetos para a API do Tradutor Master."""

    def __init__(self, base_url: str, device_token: str):
        """
        Inicializa o cliente da API.

        Args:
            base_url: URL base da API
            device_token: Token do dispositivo
        """
        self.base_url = _normalize_base_url(base_url)
        self.device_token = device_token
        self.headers = {"Authorization": f"Bearer {device_token}"}

    def get_recent_translations(self, limit: int = 10, timeout: float = 10.0) -> List[Dict[str, Any]]:
        """
        Busca traduções recentes do dispositivo.

        Args:
            limit: Número máximo de traduções
            timeout: Timeout da requisição

        Returns:
            Lista de traduções com seus tokens
        """
        url = f"{self.base_url}/translations/recent?limit={limit}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=timeout)
        except requests.RequestException as exc:
            raise APIError(f"Falha ao conectar: {exc}") from exc

        if resp.status_code != 200:
            raise APIError(f"Erro ao obter traduções ({resp.status_code}): {resp.text}")

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise APIError("Resposta inválida.") from exc

        if not isinstance(data, list):
            raise APIError("Formato inesperado.")
        return data

    def get_translation_tokens(self, translation_log_id: str, timeout: float = 10.0) -> List[Dict[str, Any]]:
        """
        Busca tokens de uma tradução específica.

        Args:
            translation_log_id: ID do log de tradução
            timeout: Timeout da requisição

        Returns:
            Lista de tokens
        """
        url = f"{self.base_url}/translation/{translation_log_id}/tokens"
        try:
            resp = requests.get(url, headers=self.headers, timeout=timeout)
        except requests.RequestException as exc:
            raise APIError(f"Falha ao conectar: {exc}") from exc

        if resp.status_code != 200:
            raise APIError(f"Erro ao obter tokens ({resp.status_code}): {resp.text}")

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise APIError("Resposta inválida.") from exc

        if not isinstance(data, list):
            raise APIError("Formato inesperado.")
        return data

    def get_token_statistics(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Busca estatísticas de tokens do dispositivo.

        Args:
            timeout: Timeout da requisição

        Returns:
            Dicionário com estatísticas
        """
        url = f"{self.base_url}/tokens/statistics"
        try:
            resp = requests.get(url, headers=self.headers, timeout=timeout)
        except requests.RequestException as exc:
            raise APIError(f"Falha ao conectar: {exc}") from exc

        if resp.status_code != 200:
            raise APIError(f"Erro ao obter estatísticas ({resp.status_code}): {resp.text}")

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise APIError("Resposta inválida.") from exc

        if not isinstance(data, dict):
            raise APIError("Formato inesperado.")
        return data

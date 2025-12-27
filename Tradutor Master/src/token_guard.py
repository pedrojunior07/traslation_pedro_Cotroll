from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import requests


Span = Tuple[int, int, str]


class GuardError(RuntimeError):
    pass


@dataclass
class OpenAIConfig:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    timeout: float = 12.0


@dataclass(frozen=True)
class TextSegment:
    text: str
    translatable: bool
    label: str = ""


class TokenGuard:
    def __init__(self, openai: Optional[OpenAIConfig] = None, enable_ai: bool = False) -> None:
        self._openai = openai
        self._enable_ai = enable_ai and openai is not None and bool(openai.api_key)

    def segment_text(self, text: str) -> List[TextSegment]:
        spans = self._collect_spans(text)
        if not spans:
            return [TextSegment(text, True)] if text else []
        spans = _dedupe_and_merge(spans)
        segments: List[TextSegment] = []
        cursor = 0
        for start, end, label in spans:
            if start > cursor:
                segments.append(TextSegment(text[cursor:start], True))
            segments.append(TextSegment(text[start:end], False, label))
            cursor = end
        if cursor < len(text):
            segments.append(TextSegment(text[cursor:], True))
        return segments

    def mask_text(self, text: str) -> tuple[str, Dict[str, str]]:
        spans = self._collect_spans(text)
        if not spans:
            return text, {}
        spans = _dedupe_and_merge(spans)
        masked = text
        placeholder_map: Dict[str, str] = {}
        replacements: List[Tuple[int, int, str]] = []
        for idx, (start, end, _) in enumerate(sorted(spans, key=lambda s: s[0])):
            placeholder = f"__NT_{idx:03d}__"
            placeholder_map[placeholder] = text[start:end]
            replacements.append((start, end, placeholder))
        for start, end, placeholder in sorted(replacements, key=lambda s: s[0], reverse=True):
            masked = masked[:start] + placeholder + masked[end:]
        return masked, placeholder_map

    def unmask_text(self, translated: str, placeholder_map: Dict[str, str]) -> str:
        if not placeholder_map:
            return translated
        placeholders = _sorted_placeholders(placeholder_map)
        positions = [_find_placeholder(translated, ph) for ph in placeholders]
        if any(pos < 0 for pos in positions):
            missing = [ph for ph, pos in zip(placeholders, positions) if pos < 0]
            raise GuardError(f"Token(s) nao preservado(s): {', '.join(missing)}")
        if positions != sorted(positions):
            raise GuardError("Tokens nao preservados na mesma ordem.")
        restored = translated
        for placeholder, original in placeholder_map.items():
            restored = restored.replace(placeholder, original)
        return restored

    def _collect_spans(self, text: str) -> List[Span]:
        spans = _heuristic_spans(text)
        if self._enable_ai:
            spans.extend(self._openai_spans(text))
        return spans

    def _openai_spans(self, text: str) -> List[Span]:
        assert self._openai is not None
        if not text.strip():
            return []
        prompt = (
            "Identify non-translatable tokens (names, locations, brands, ids, URLs, "
            "emails, codes) and return JSON with spans using start/end character indices "
            "for the exact substring in the input. Return only JSON.\n\n"
            f"Input:\n{text}\n\n"
            "JSON schema: {\"spans\":[{\"start\":0,\"end\":4,\"label\":\"NAME\"}]}"
        )
        url = f"{self._openai.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openai.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._openai.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "Return strictly valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self._openai.timeout)
        except requests.RequestException:
            return []
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except json.JSONDecodeError:
            return []
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return []
        spans = []
        for entry in parsed.get("spans", []):
            try:
                start = int(entry.get("start"))
                end = int(entry.get("end"))
            except (TypeError, ValueError):
                continue
            label = str(entry.get("label") or "AI")
            if 0 <= start < end <= len(text):
                spans.append((start, end, label))
        return spans


def _find_placeholder(text: str, placeholder: str) -> int:
    return text.find(placeholder)


def _sorted_placeholders(placeholder_map: Dict[str, str]) -> List[str]:
    def sort_key(value: str) -> Tuple[int, str]:
        match = re.search(r"__NT_(\d{3})__", value)
        if not match:
            return (10**9, value)
        return (int(match.group(1)), value)

    return sorted(placeholder_map.keys(), key=sort_key)


def _heuristic_spans(text: str) -> List[Span]:
    """Identifica spans não traduzíveis incluindo entidades moçambicanas."""
    patterns = [
        # URLs e Emails (primeiro para evitar conflitos)
        (r"\bhttps?://[^\s]+", "URL"),
        (r"\bwww\.[^\s]+", "URL"),
        (r"\b[\w.+-]+@[\w.-]+\.\w+\b", "EMAIL"),

        # === ENDEREÇOS E LOCALIZAÇÃO ===
        (r"(?:Av\.|Avenida|Rua|R\.|Travessa|Alameda|Praça|Estrada)\s+[A-ZÀ-Ú][a-zà-úA-ZÀ-Ú\s\d/,-]+?(?:,?\s*(?:n\.?º?|nº|número|No\.?|N\.?)?\s*\d+)?", "ADDRESS"),
        (r"(?:Bairro|B\.)\s+(?:d[aeo]\s+)?[A-ZÀ-Ú][a-zà-úA-ZÀ-Ú\s\d]+", "NEIGHBORHOOD"),
        (r"(?:C\.?P\.?|Caixa\s+Postal|P\.?O\.?\s*Box)\s*:?\s*\d+", "PO_BOX"),
        (r"(?:\+\d{1,3}\s*)?(?:\(\d{2,3}\)\s*)?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}", "PHONE"),
        (r"NUIT\s*:?\s*\d{9}", "NUIT"),
        (r"NIB\s*:?\s*\d{4}\s*\d{4}\s*\d{11}\s*\d{2}", "NIB"),
        (r"\b\d{1,2}\s+de\s+(?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\b", "HISTORIC_DATE"),
        (r"\b(?:Maputo|Matola|Beira|Nampula|Quelimane|Tete|Chimoio|Nacala|Pemba|Inhambane|Xai-Xai|Maxixe|Lichinga|Cuamba|Dondo|Angoche|Cidade de Maputo|Província de Maputo|Gaza|Sofala|Manica|Zambézia|Cabo Delgado|Niassa)\b", "LOCATION"),

        # === EMPRESAS PETROLÍFERAS E GÁS ===
        (r"\b(?:TotalEnergies|Total\s+E&P|Total\s+Mozambique|Total|ExxonMobil|Exxon|Mobil|Shell|Royal\s+Dutch\s+Shell|BP|British\s+Petroleum|Chevron|ConocoPhillips|Eni|ENI|Equinor|Statoil|Petrobras|Galp|Galp\s+Energia|Repsol|Sasol|Anadarko|Mitsui|PTTEP|ONGC|Vidya|Bharat|Pavilion\s+Energy|Mozambique\s+Rovuma\s+Venture|Coral\s+Sul\s+FLNG|Rovuma\s+LNG|Mozambique\s+LNG|Moz\s+LNG|Area\s+1|Area\s+4)\b", "OIL_GAS"),

        # === MULTINACIONAIS TECNOLOGIA ===
        (r"\b(?:Microsoft|Apple|Google|Alphabet|Amazon|Meta|Facebook|Instagram|WhatsApp|IBM|Oracle|SAP|Salesforce|Adobe|Cisco|Intel|AMD|NVIDIA|Qualcomm|Dell|HP|Hewlett[\s-]?Packard|Lenovo|Asus|Acer|Samsung|LG|Sony|Panasonic|Toshiba|Huawei|ZTE|Xiaomi|Oppo|Vivo|Realme)\b", "TECH_COMPANY"),

        # === AUTOMOTIVAS ===
        (r"\b(?:Toyota|Honda|Ford|Volkswagen|VW|Mercedes[\s-]?Benz|BMW|Audi|Nissan|Hyundai|Kia|Mazda|Mitsubishi|Suzuki|Isuzu|Volvo|Scania|MAN|DAF|Renault|Peugeot|Citroën|Fiat|Ferrari|Lamborghini|Porsche|Tesla|Land\s+Rover|Range\s+Rover|Jaguar|Jeep|Chevrolet|GMC|Subaru)\b", "AUTO_COMPANY"),

        # === FARMACÊUTICAS ===
        (r"\b(?:Pfizer|Moderna|AstraZeneca|Johnson\s*&\s*Johnson|J&J|Novartis|Roche|Sanofi|GlaxoSmithKline|GSK|Merck|Bayer|Abbott|Eli\s+Lilly|Bristol[\s-]?Myers\s+Squibb|Gilead|Amgen)\b", "PHARMA"),

        # === BANCOS INTERNACIONAIS ===
        (r"\b(?:Standard\s+Bank|Barclays|HSBC|Citibank|Citi|Santander|Deutsche\s+Bank|BNP\s+Paribas|Credit\s+Suisse|UBS|JP\s+Morgan|Goldman\s+Sachs|Morgan\s+Stanley|Wells\s+Fargo|Bank\s+of\s+America|Société\s+Générale)\b", "BANK"),

        # === CONSULTORIA ===
        (r"\b(?:Deloitte|PwC|PricewaterhouseCoopers|Ernst\s*&\s*Young|EY|KPMG|McKinsey|Boston\s+Consulting|BCG|Bain\s*&\s*Company|Accenture|Capgemini|Oliver\s+Wyman)\b", "CONSULTING"),

        # === AVIAÇÃO E LOGÍSTICA ===
        (r"\b(?:Emirates|Qatar\s+Airways|Ethiopian\s+Airlines|Kenya\s+Airways|South\s+African\s+Airways|SAA|British\s+Airways|Lufthansa|Air\s+France|KLM|TAP|DHL|FedEx|UPS|TNT|Maersk|MSC|CMA\s+CGM|Hapag[\s-]?Lloyd)\b", "AVIATION_LOGISTICS"),

        # === MINERAÇÃO ===
        (r"\b(?:Vale|Rio\s+Tinto|BHP|Glencore|Anglo\s+American|Kenmare\s+Resources|Syrah\s+Resources|Montepuez\s+Ruby\s+Mining|Gemfields|Twigg\s+Exploration|Beadell\s+Resources)\b", "MINING"),

        # === TELECOM INTERNACIONAL ===
        (r"\b(?:Verizon|AT&T|T[\s-]?Mobile|Orange|Telefonica|China\s+Mobile|China\s+Telecom|Bharti\s+Airtel|MTN|Liquid\s+Telecom|Vodafone)\b", "TELECOM_INTL"),

        # === CONSTRUÇÃO E ENGENHARIA ===
        (r"\b(?:China\s+Road\s+and\s+Bridge|CRBC|China\s+Communications|CCCC|Odebrecht|Mota[\s-]?Engil|Soares\s+da\s+Costa|Teixeira\s+Duarte|Costain|Bechtel|Fluor|Saipem|Technip|McDermott)\b", "CONSTRUCTION"),

        # === SIGLAS MOÇAMBICANAS ===
        (r"\b(?:UEM|UP|UCM|ISDB|ISCTEM|ISPU|MITESS|MISAU|MINEDH|MTC|MAE|MOPHRH|MIREME|MIREMPET|MIMAIP|MITUR|MINAG|EDM|TDM|FIPAG|CFM|LAM|AdM|HCM|HCB|BCI|BIM|Vodacom|Movitel|Tmcel|INE|INSS|BAU|INGC|SETSAN|IGEPE|CTA|CMCM|CMM|FUNAE|INAV|INAE|AR|PRM|ANAC|CIP|ENH|CMH|INAM|STAE)\b", "ACRONYM"),

        # Padrões genéricos
        (r"\b\d[\d\.,:/-]*\b", "NUMBER"),
        (r"\b[A-Z]{2,}\d+[A-Z0-9_-]*\b", "CODE"),
        (r"\b[A-Z0-9_-]*\d+[A-Z0-9_-]*\b", "CODE"),
        (r"\{[^}]+\}", "BRACE"),
        (r"\{\{[^}]+\}\}", "BRACE"),
        (r"\[[^\]]+\]", "BRACKET"),
        (r"<[^>]+>", "TAG"),
        (r"\b[A-Za-z]:\\[^\s]+", "PATH"),
        (r"\b/[^ \t\r\n]+", "PATH"),
    ]
    spans: List[Span] = []
    for pattern, label in patterns:
        for match in re.finditer(pattern, text):
            spans.append((match.start(), match.end(), label))
    return spans


def _dedupe_and_merge(spans: Iterable[Span]) -> List[Span]:
    ordered = sorted(spans, key=lambda s: (s[0], s[1]))
    merged: List[Span] = []
    for start, end, label in ordered:
        if not merged:
            merged.append((start, end, label))
            continue
        prev_start, prev_end, prev_label = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end), prev_label)
            continue
        merged.append((start, end, label))
    return merged

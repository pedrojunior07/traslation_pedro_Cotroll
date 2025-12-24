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
    patterns = [
        (r"\bhttps?://[^\s]+", "URL"),
        (r"\bwww\.[^\s]+", "URL"),
        (r"\b[\w.+-]+@[\w.-]+\.\w+\b", "EMAIL"),
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

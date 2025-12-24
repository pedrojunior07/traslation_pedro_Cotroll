from dataclasses import dataclass, field
from typing import List


@dataclass
class Token:
    source_file: str
    location: str
    text: str
    translation: str = field(default="")
    skip: bool = field(default=False)
    skip_reason: str = field(default="")
    units: int = field(default=1)
    source_original: str = field(default="")


def merge_tokens(existing: List[Token], new_tokens: List[Token]) -> List[Token]:
    """Append new tokens, avoiding duplicates by (source, location, text)."""
    seen = {(t.source_file, t.location, t.text) for t in existing}
    for token in new_tokens:
        key = (token.source_file, token.location, token.text)
        if key not in seen:
            existing.append(token)
            seen.add(key)
    return existing

from __future__ import annotations

import hashlib
import re


HEX_ADDRESS_RE = re.compile(r"0x[0-9a-fA-F]+")
LINE_NUMBER_RE = re.compile(r":\d+")
WHITESPACE_RE = re.compile(r"\s+")


def normalize_error(text: str) -> str:
    normalized = HEX_ADDRESS_RE.sub("0xADDR", text)
    normalized = LINE_NUMBER_RE.sub(":LINE", normalized)
    normalized = WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip().lower()


def fingerprint_error(text: str) -> str:
    return hashlib.sha256(normalize_error(text).encode("utf-8")).hexdigest()[:16]

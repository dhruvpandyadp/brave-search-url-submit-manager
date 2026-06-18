from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PREFIXES = ("utm_",)
TRACKING_KEYS = {
    "fbclid",
    "gclid",
    "gbraid",
    "wbraid",
    "mc_cid",
    "mc_eid",
}


@dataclass(frozen=True)
class UrlResult:
    original: str
    url: str
    domain: str
    is_valid: bool
    error: str = ""


def normalize_url(raw_url: str) -> UrlResult:
    original = (raw_url or "").strip()
    if not original:
        return UrlResult(original=original, url="", domain="", is_valid=False, error="Empty URL")

    candidate = original if "://" in original else f"https://{original}"
    parts = urlsplit(candidate)

    if parts.scheme not in {"http", "https"}:
        return UrlResult(original=original, url="", domain="", is_valid=False, error="Use http or https")

    if not parts.netloc or "." not in parts.netloc:
        return UrlResult(original=original, url="", domain="", is_valid=False, error="Missing valid domain")

    netloc = parts.netloc.lower()
    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    filtered_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key in TRACKING_KEYS or lower_key.startswith(TRACKING_PREFIXES):
            continue
        filtered_query.append((key, value))

    query = urlencode(filtered_query, doseq=True)
    normalized = urlunsplit((parts.scheme.lower(), netloc, path, query, ""))
    return UrlResult(original=original, url=normalized, domain=netloc, is_valid=True)


def parse_url_lines(text: str) -> list[str]:
    urls: list[str] = []
    for line in (text or "").splitlines():
        item = line.strip()
        if item:
            urls.append(item)
    return urls

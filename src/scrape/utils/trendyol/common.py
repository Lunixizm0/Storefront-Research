# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import json
from typing import Any

from bs4 import BeautifulSoup

from scrape.debug import debug, error, info

__all__ = [
    "_extract_first_string",
    "_format_price_value",
    "_is_placeholder_description_text",
    "_iter_json_ld_payloads",
    "_normalize_json_value",
    "_safe_api_call",
    "_str",
    "parse_html",
    "product_dataset_to_json",
]


def _is_placeholder_description_text(value):
    if value is None:
        return True

    cleaned = str(value).strip()
    if not cleaned:
        return True

    normalized = "".join(ch for ch in cleaned if ch.isalnum()).upper()
    if normalized in {
        "STD",
        "NAA",
        "NA",
        "NONE",
        "NULL",
        "UNKNOWN",
        "UNDEFINED",
        "N/A",
    }:
        return True

    return len(normalized) <= 3 and normalized.isalpha()


def parse_html(html_content):
    debug("html.parse", bytes=len(html_content or b""))
    soup = BeautifulSoup(html_content, "html.parser")
    debug("html.parsed", scripts=len(soup.select("script")))
    return soup


def _iter_json_ld_payloads(soup):
    for script in soup.select("script[type='application/ld+json']"):
        script_text = script.string or ""
        if not script_text.strip():
            continue
        try:
            payload = json.loads(script_text)
        except (TypeError, json.JSONDecodeError):
            continue

        yield payload


def _format_price_value(value):
    if value is None:
        return None
    try:
        return f"{float(value):.2f} TL"
    except (TypeError, ValueError):
        return None


def _normalize_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalize_json_value(item) for item in value]
    return str(value)


def _str(value: Any) -> str | None:
    normalized = _normalize_json_value(value)
    if normalized is None or isinstance(normalized, str):
        return normalized
    return str(normalized)


def _extract_first_string(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("name", "text", "value", "label"):
            candidate = _extract_first_string(value.get(key))
            if candidate:
                return candidate
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            candidate = _extract_first_string(item)
            if candidate:
                return candidate
    return str(value)


def _safe_api_call(fn, *args, **kwargs):
    api_name = getattr(fn, "__name__", str(fn))
    info("api.builder.start", builder=api_name)
    try:
        result = fn(*args, **kwargs)
        info("api.builder.complete", builder=api_name, available=result is not None)
        return result
    except Exception as e:
        error("api.builder.error", builder=api_name, error=f"{type(e).__name__}: {e}")
        return None


def product_dataset_to_json(dataset):
    if hasattr(dataset, "to_json"):
        return dataset.to_json()
    return json.dumps(dataset, ensure_ascii=False)

# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import json
import re
from typing import Any

from bs4 import BeautifulSoup

from scrape.debug import debug, warn

__all__ = [
    "_decode_mm_html",
    "_extract_apollo_state",
    "_extract_preloaded_state",
    "_feature_entities",
    "_get_entity",
    "_iter_breadcrumbs",
    "_product_id_from_url",
    "extract_product_data",
    "extract_product_id",
]

_PRELOADED_MARKER = "__PRELOADED_STATE__"
_APOLLO_KEY = "apolloState"


def _product_id_from_url(url):
    if not url:
        return None
    match = re.search(r"-(\d+)\.html\s*$", url)
    if match is None:
        match = re.search(r"(?:^|[^0-9])(\d{4,})\s*$", url)
    if match is None:
        return None
    return match.group(1)


def extract_product_id(url):
    return _product_id_from_url(url)


def _match_object(text, start):
    depth = 0
    in_str = False
    escaped = False
    index = start
    while index < len(text):
        char = text[index]
        if in_str:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_str = False
        else:
            if char == '"':
                in_str = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
        index += 1
    return None


def _extract_preloaded_state(soup):
    if not isinstance(soup, BeautifulSoup):
        return None

    for script in soup.select("script:not([src])"):
        text = script.string or ""
        if _PRELOADED_MARKER not in text:
            continue
        marker = text.index(_PRELOADED_MARKER)
        equals = text.index("=", marker)
        body = text[equals + 1 :].strip().rstrip().rstrip(";").strip()
        if not body or not body.startswith("{"):
            continue
        debug("preloaded_state.found", provider="mediamarkt")
        return body

    warn("preloaded_state.missing", provider="mediamarkt")
    return None


def _extract_apollo_state(soup_or_body):
    body = soup_or_body
    if isinstance(soup_or_body, BeautifulSoup):
        body = _extract_preloaded_state(soup_or_body)
    if not body:
        return None

    key_index = body.find(f'"{_APOLLO_KEY}"')
    if key_index == -1:
        warn("apollo_state.missing", provider="mediamarkt")
        return None

    brace_start = body.index("{", key_index)
    raw = _match_object(body, brace_start)
    if raw is None:
        warn("apollo_state.unmatched", provider="mediamarkt")
        return None

    try:
        state = json.loads(raw)
    except (TypeError, ValueError) as exc:
        warn("apollo_state.invalid", provider="mediamarkt", error=f"{exc}")
        return None

    debug("apollo_state.found", provider="mediamarkt", entities=len(state))
    return state


def _get_entity(state, key):
    if isinstance(state, dict):
        return state.get(key)
    return None


def _product_entity(state, product_id, locale="tr-TR"):
    return _get_entity(state, f"GraphqlProduct:Media:{locale}:{product_id}")


def _price_entities(state, product_id):
    prefix = "CofrPriceFeature:"
    for key, value in (state or {}).items():
        if key.startswith(prefix) and product_id in key:
            yield value


def _iter_breadcrumbs(entity):
    if not isinstance(entity, dict):
        return []
    breadcrumbs = entity.get("breadcrumbs")
    if not isinstance(breadcrumbs, list):
        return []
    names = []
    for crumb in breadcrumbs:
        if not isinstance(crumb, dict):
            continue
        name = crumb.get("name")
        if name:
            names.append(name)
    return names


def _decode_mm_html(value):
    # Decode MediaMarkt's angle-bracket escaped HTML (`<lt/>`/`<gt/>`)
    if not value:
        return None
    text = str(value)
    text = text.replace("<lt/>", "<").replace("<gt/>", ">")
    text = text.replace("<LT/>", "<").replace("<GT/>", ">")
    text = text.replace("&nbsp;", "\u00a0").replace("&amp;", "&")
    return text


def _feature_entities(state, product_id):
    # Yield (group_name, feature_name, feature_value) rows from feature groups.
    groups_key = f"GraphqlProductFeatureGroups:{product_id}"
    groups = _get_entity(state, groups_key)
    if not isinstance(groups, dict):
        return []

    rows = []
    for group in groups.get("featureGroups") or []:
        if not isinstance(group, dict):
            continue
        group_name = group.get("featureGroupName")
        for feature in group.get("features") or []:
            if not isinstance(feature, dict):
                continue
            ref = feature.get("__ref")
            entity = _get_entity(state, ref) if ref else None
            if not isinstance(entity, dict):
                continue
            name = entity.get("name") or ""
            value = entity.get("value")
            if name:
                rows.append((group_name, name, value))
    debug("features.rows", provider="mediamarkt", count=len(rows))
    return rows


def extract_product_data(soup, url=None):
    # Return the raw `apolloState` dict plus resolved client-side entities.
    # Returns ``(state, product_id)``. The product core data is embedded in the
    # SSR ``__PRELOADED_STATE__`` Apollo cache and never fetched via GraphQL on
    # initial load, so most of what the dataset needs lives here.
    state = _extract_apollo_state(soup)
    if state is None:
        return None, None

    if url is None:
        url = soup.get("url") if isinstance(soup, dict) else None
    product_id = extract_product_id(url)
    if not product_id:
        # Fall back to any GraphqlProduct entity present in the cache.
        for key in state:
            if key.startswith("GraphqlProduct:Media:tr-TR:"):
                product_id = key.rsplit(":", 1)[-1]
                break
    debug(
        "product_data.found",
        source="apollo_state",
        provider="mediamarkt",
        product_id=product_id,
    )
    return state, product_id

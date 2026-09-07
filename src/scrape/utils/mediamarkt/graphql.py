# In-tree package module. Do not use directly. import from scrape.utils.{pkg}
#
# Supplementary GraphQL path. MediaMarkt.com.tr is an Apollo Client (GraphQL)
# PWA. The core product aggregate is embedded in the SSR `__PRELOADED_STATE__`
# Apollo cache (see parsing.extract_product_data) and is NOT fetchable via
# GraphQL on initial load. GraphQL only supplies peripheral data such as media
# content (videos) and loyalty points, which we fetch here as persisted queries.
#
# The GraphQL endpoint is behind Cloudflare and only serves the PWA's own
# requests: queries must be sent as GETs carrying the persisted-query sha256
# hash plus the `pwa` extensions block, along with the apollo/x-mms request
# headers. A real browser TLS fingerprint (curl_cffi impersonation) and the
# cookies set by a plain page GET are required; without them Cloudflare answers
# 403 (missing headers), 429 (rate-limited / unknown fingerprint) or the API
# answers 500 (missing `pwa` extensions block).

import json
import os
import time
import uuid

from curl_cffi import requests as _cffi_requests

from scrape.debug import DebugRequests, debug, warn

from .http import _MM_UA, _graphql_headers

__all__ = [
    "_GRAPHQL_ENDPOINT",
    "_execute_persisted_query",
    "_graphql_enabled",
    "get_loyalty_points_from_graphql",
    "get_product_media_from_graphql",
]

_GRAPHQL_ENDPOINT = "https://www.mediamarkt.com.tr/api/v1/graphql"
_HOME_URL = "https://www.mediamarkt.com.tr/"

_EXTENSIONS_BASE = {
    "persistedQuery": {"version": 1, "sha256Hash": None},
    "pwa": {
        "captureChannel": "DESKTOP",
        "salesLine": "Media",
        "country": "TR",
        "language": "tr",
        "globalLoyaltyProgram": True,
        "isOneAccountProgramActive": True,
        "isCustomerReturnApiActive": True,
        "isUsingXccCustomerComponent": True,
        "isCheckoutAptNrActive": True,
        "isCheckoutAddressLevelActive": True,
        "isCheckoutAddressDistrictActive": True,
        "isCheckoutAddressQuarterActive": True,
        "isCheckoutPhoneCompareActive": True,
    },
}

# Persisted query hashes captured from the live PWA network traffic.
_PERSISTED_QUERIES = {
    "GetProductContentMediaContent": "6f8e832c9bf6301b23c12747b56c155f46b0fae05f5235b95e88422ffca504cc",
    "GetProductLoyaltyPoints": "6dc26319c65876368393797616f466dfb1e2c304eccec8e135f3fdc4f728fe49",
}


# GraphQL is gated behind an env flag so the live path can opt in while unit
# tests stay hermetic (no network). Unset/any value other than "0" enables it.
def _graphql_enabled():
    return os.environ.get("SCRAPE_MEDIAMARKT_GRAPHQL", "1") != "0"


_session = None
_warmed = False


def _set_warmed(value):
    global _warmed
    _warmed = value


def _graphql_session():
    global _session
    if _session is None:
        session = _cffi_requests.Session(impersonate="firefox133")
        session.headers.update({"User-Agent": _MM_UA})
        _session = DebugRequests(session)
    return _session


def _warm_cookies(product_url=None):
    # GET a page through the impersonated session so Cloudflare issues the `optid`/`__cf_bm` cookies the GraphQL endpoint expects
    warm_url = product_url or _HOME_URL
    session = _graphql_session()
    for attempt in range(3):
        try:
            response = session.get(
                warm_url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,*/*",
                    "Referer": _HOME_URL,
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US",
                },
                timeout=30,
            )
        except Exception as exc:
            warn(
                "graphql.cookie_warmup_error",
                provider="mediamarkt",
                attempt=attempt + 1,
                error=f"{type(exc).__name__}: {exc}",
            )
            time.sleep(1 + attempt)
            continue
        if response.status_code == 200:
            _set_warmed(True)
            return
        warn(
            "graphql.cookie_warmup_retry",
            provider="mediamarkt",
            status=response.status_code,
            attempt=attempt + 1,
        )
        time.sleep(1 + attempt)
    _set_warmed(True)  # give the query a chance even if warm-up wobbled


def _extensions_for(query_hash):
    extensions = dict(_EXTENSIONS_BASE)
    extensions["persistedQuery"] = {"version": 1, "sha256Hash": query_hash}
    return extensions


def _execute_persisted_query(
    operation_name, variables, product_url=None, hash_=None, retries=3
):
    if not _graphql_enabled():
        debug(
            "graphql.disabled",
            provider="mediamarkt",
            operation_name=operation_name,
        )
        return None

    query_hash = hash_ or _PERSISTED_QUERIES.get(operation_name)
    if not query_hash:
        warn(
            "graphql.unknown_query",
            provider="mediamarkt",
            operation_name=operation_name,
        )
        return None

    warm_url = product_url or _HOME_URL
    if not _warmed:
        _warm_cookies(warm_url)

    params = {
        "operationName": operation_name,
        "variables": json.dumps(variables),
        "extensions": json.dumps(_extensions_for(query_hash)),
    }

    last_status = None
    for attempt in range(retries):
        headers = _graphql_headers(
            product_url, operation_name=operation_name, flow_id=str(uuid.uuid4())
        )
        try:
            response = _graphql_session().get(
                _GRAPHQL_ENDPOINT,
                params=params,
                headers=headers,
                timeout=30,
            )
        except Exception as exc:
            last_status = None
            warn(
                "graphql.request_error",
                provider="mediamarkt",
                operation_name=operation_name,
                attempt=attempt + 1,
                error=f"{type(exc).__name__}: {exc}",
            )
        else:
            last_status = response.status_code
            if response.status_code == 200:
                return _parse_graphql_response(response, operation_name, variables)
            if response.status_code in (403, 429) and attempt + 1 < retries:
                # Cloudflare block / throttling: refresh cookies and back off.
                warn(
                    "graphql.retry",
                    provider="mediamarkt",
                    operation_name=operation_name,
                    status=response.status_code,
                    attempt=attempt + 1,
                )
                _set_warmed(False)
                _warm_cookies(warm_url)
                time.sleep(1.5 + attempt)
                continue
        if attempt + 1 < retries:
            time.sleep(0.5 + attempt)

    warn(
        "graphql.http_error",
        provider="mediamarkt",
        operation_name=operation_name,
        status=last_status,
    )
    return None


def _parse_graphql_response(response, operation_name, variables):
    try:
        data = response.json()
    except (TypeError, ValueError):
        warn(
            "graphql.invalid_json",
            provider="mediamarkt",
            operation_name=operation_name,
        )
        return None
    if not isinstance(data, dict):
        warn(
            "graphql.invalid_payload",
            provider="mediamarkt",
            operation_name=operation_name,
        )
        return None
    if data.get("errors"):
        warn(
            "graphql.errors",
            provider="mediamarkt",
            operation_name=operation_name,
            codes=",".join(
                str(e.get("extensions", {}).get("code", "?"))
                for e in data["errors"]
                if isinstance(e, dict)
            )
            or "unknown",
        )
        return None
    debug(
        "graphql.ok",
        provider="mediamarkt",
        operation_name=operation_name,
        variables=variables,
    )
    return data


def get_product_media_from_graphql(product_id, product_url=None):
    # Fetch media content (e.g. videos, 3D models) for a product
    data = _execute_persisted_query(
        "GetProductContentMediaContent",
        {"productId": str(product_id)},
        product_url=product_url,
    )
    if not isinstance(data, dict):
        return None
    result = data.get("data")
    if not isinstance(result, dict):
        return None
    content = result.get("productMediaContent")
    if not isinstance(content, dict):
        return None
    debug("graphql.media", provider="mediamarkt", product_id=product_id)
    return content


def get_loyalty_points_from_graphql(
    product_id, price, currency="TRY", product_url=None
):
    """Fetch loyalty points for a product at the given price."""
    data = _execute_persisted_query(
        "GetProductLoyaltyPoints",
        {
            "id": str(product_id),
            "price": price,
            "currency": currency,
        },
        product_url=product_url,
        hash_="6dc26319c65876368393797616f466dfb1e2c304eccec8e135f3fdc4f728fe49",
    )
    if not isinstance(data, dict):
        return None
    result = data.get("data")
    if not isinstance(result, dict):
        return None
    assessment = result.get("globalLoyItemAssessment")
    if not isinstance(assessment, dict):
        return None
    debug("graphql.loyalty", provider="mediamarkt", product_id=product_id)
    return assessment

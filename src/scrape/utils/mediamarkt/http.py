# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import requests as _requests

from scrape.debug import DebugRequests, request_get

__all__ = [
    "_MM_UA",
    "_graphql_headers",
    "_page_headers",
    "get_raw_html",
    "requests",
]


_MM_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
)


def get_raw_html(url):
    response = request_get(_requests, url, headers=_page_headers(), timeout=30)
    return response


def _page_headers():
    return {
        "User-Agent": _MM_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.mediamarkt.com.tr",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }


_GRAPHQL_CLIENT_NAME = "pwa-client-pqm"
_GRAPHQL_CLIENT_VERSION = "8.490.2"


def _graphql_headers(product_url=None, operation_name=None, flow_id=None):
    headers = {
        "User-Agent": _MM_UA,
        "Accept": "*/*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US",
        "Content-Type": "application/json",
        "Origin": "https://www.mediamarkt.com.tr",
        "Referer": product_url or "https://www.mediamarkt.com.tr/",
        "Host": "www.mediamarkt.com.tr",
        "Connection": "keep-alive",
        "apollographql-client-name": _GRAPHQL_CLIENT_NAME,
        "apollographql-client-version": _GRAPHQL_CLIENT_VERSION,
        "x-cacheable": "true",
        "x-mms-language": "tr",
        "x-mms-country": "TR",
        "x-mms-salesline": "Media",
    }
    if operation_name:
        headers["x-operation"] = operation_name
    if flow_id:
        headers["x-flow-id"] = flow_id
    return headers


requests = DebugRequests(_requests)

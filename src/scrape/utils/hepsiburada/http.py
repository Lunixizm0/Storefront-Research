# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import requests as _requests

from scrape.debug import DebugRequests, request_get

__all__ = [
    "_HEPB_UA",
    "_api_headers",
    "_goto_referer",
    "_to_int_list",
    "get_raw_html",
    "requests",
]


def get_raw_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:154.0) Gecko/20100101 Firefox/154.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.hepsiburada.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    response = request_get(_requests, url, headers=headers, timeout=30)
    return response


def _goto_referer(product_url):
    return product_url if product_url else "https://www.hepsiburada.com"


def _to_int_list(values):
    out = []
    for v in values or []:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            pass
    return out


def _api_headers(product_url=None, is_post=False):
    headers = {
        "User-Agent": _HEPB_UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": _goto_referer(product_url),
    }
    if is_post:
        headers["Content-Type"] = "application/json"
        headers["Origin"] = "https://www.hepsiburada.com"
    return headers


_HEPB_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
)

requests = DebugRequests(_requests)

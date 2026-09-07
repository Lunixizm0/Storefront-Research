# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import requests as _requests

from scrape.debug import DebugRequests, request_get

__all__ = ["get_common_api_headers", "get_raw_html", "requests"]


def get_raw_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:154.0) Gecko/20100101 Firefox/154.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Host": "www.trendyol.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    response = request_get(_requests, url, headers=headers, timeout=20)
    return response


def get_common_api_headers():
    return {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:154.0) Gecko/20100101 Firefox/154.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
        "x-agentname": "StorefrontProductGateway",
        "x-web-req-source": "StorefrontProductGateway",
        "Origin": "https://www.trendyol.com",
        "Cookie": "platform=web; AZ_SELECTED=false; storefrontId=1; countryCode=TR; language=tr",
    }


requests = DebugRequests(_requests)

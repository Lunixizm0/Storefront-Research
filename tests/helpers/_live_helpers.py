# Live URL fetchers for integration test parametrization
from __future__ import annotations

import re

import requests


def _normalize_trendyol_url(value):
    value = (value or "").strip()
    if not value:
        return None
    value = value.split("#", 1)[0].split("?", 1)[0].strip("\"'")
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("/"):
        return f"https://www.trendyol.com{value}"
    return f"https://www.trendyol.com/{value.lstrip('/')}"


def get_trendyol_product_urls(limit=5):
    try:
        page_url = "https://www.trendyol.com/cok-satanlar?type=bestSeller&webGenderId=1"
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:154.0) Gecko/20100101 Firefox/154.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.trendyol.com/",
        }
        session.get(page_url, headers=headers, timeout=30)

        api_url = "https://apigw.trendyol.com/discovery-sfint-browsing-service/api/top-rankings-v2/top-ranking-contents"
        params = {
            "rankingType": "bestSeller",
            "webGenderId": "1",
            "page": "1",
            "pageSize": str(limit),
            "categoryId": "27",
            "channelId": "1",
        }
        api_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:154.0) Gecko/20100101 Firefox/154.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "Referer": page_url,
            "Origin": "https://www.trendyol.com",
            "x-device-type": "desktop",
            "x-device-platform": "web",
        }
        resp = session.get(api_url, params=params, headers=api_headers, timeout=30)
        if resp.status_code != 200:
            return []

        products = resp.json().get("products") or []
        seen = set()
        urls = []
        for p in products:
            candidate = (p or {}).get("url")
            normalized = _normalize_trendyol_url(candidate)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
            if len(urls) >= limit:
                break
        return urls
    except Exception:
        return []


def _normalize_hepsiburada_url(value):
    value = (value or "").strip()
    if not value:
        return None
    value = value.split("#", 1)[0].split("?", 1)[0].strip("\"'")
    if value.startswith(("http://", "https://")):
        url = value
    elif value.startswith("/"):
        url = f"https://www.hepsiburada.com{value}"
    else:
        url = f"https://www.hepsiburada.com/{value.lstrip('/')}"
    url = url.replace("https://www.hepsiburada.com:443", "https://www.hepsiburada.com")
    return url.rstrip("/")


def _is_hb_product_url(url):
    return bool(re.search(r"[-/](?:p|pm)-[A-Za-z0-9]+$", url))


def get_hepsiburada_product_urls(limit=5):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:154.0) Gecko/20100101 Firefox/154.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        resp = requests.get("https://www.hepsiburada.com", headers=headers, timeout=30)
        if resp.status_code != 200:
            return []

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.text, "html.parser")
        seen = set()
        urls = []
        for a in soup.find_all("a", href=True):
            normalized = _normalize_hepsiburada_url(a["href"])
            if not normalized or not _is_hb_product_url(normalized):
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
            if len(urls) >= limit:
                break
        return urls
    except Exception:
        return []


def _normalize_mediamarkt_url(value):
    value = (value or "").strip()
    if not value:
        return None
    value = value.split("#", 1)[0].split("?", 1)[0].strip("\"'")
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("/"):
        return f"https://www.mediamarkt.com.tr{value}"
    return f"https://www.mediamarkt.com.tr/{value.lstrip('/')}"


def _is_mediamarkt_product_url(value):
    value = value or ""
    return bool(re.search(r"/tr/product/.+-(\d+)\.html$", value))


def _mediamarkt_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US",
        "Upgrade-Insecure-Requests": "1",
    }
    return requests.get(url, headers=headers, timeout=30)


def get_mediamarkt_product_urls(limit=5):
    # MediaMarkt server-renders actual product links on search pages category
    # and homepage only surface a cached SSRed product for anonymous access.
    queries = ["iphone", "samsung", "laptop", "televizyon", "kulakl%C4%B1k"]
    seen = set()
    urls = []
    try:
        for query in queries:
            page_url = f"https://www.mediamarkt.com.tr/tr/search.html?query={query}"
            resp = _mediamarkt_page(page_url)
            if resp.status_code != 200:
                continue
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                normalized = _normalize_mediamarkt_url(a["href"])
                if not normalized or not _is_mediamarkt_product_url(normalized):
                    continue
                if normalized in seen:
                    continue
                seen.add(normalized)
                urls.append(normalized)
                if len(urls) >= limit:
                    return urls
        return urls
    except Exception:
        return []

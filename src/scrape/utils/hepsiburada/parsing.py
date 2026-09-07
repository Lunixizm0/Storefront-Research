# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import json
import re

from bs4 import BeautifulSoup

from scrape.debug import debug, warn

from ..trendyol.common import (
    _extract_first_string,
    _format_price_value,
    _is_placeholder_description_text,
    _iter_json_ld_payloads,
)

__all__ = [
    "_META_FIELDS",
    "_build_description",
    "_clean_description_text",
    "_detect_category",
    "_extract_attribute_fallback_description",
    "_extract_availability",
    "_extract_custom_data",
    "_extract_description_from_dom",
    "_extract_image",
    "_extract_product_from_json_ld",
    "_extract_redux_product",
    "_extract_redux_store",
    "_is_generic_hepsiburada_description",
    "_strip_placeholder_tokens",
    "extract_price",
    "extract_product_data",
]


def _extract_product_from_json_ld(payload):
    if not isinstance(payload, dict):
        return None

    if payload.get("@type") == "Product":
        return payload

    graph = payload.get("@graph")
    if isinstance(graph, list):
        for item in graph:
            if isinstance(item, dict) and item.get("@type") == "Product":
                return item

    return None


def extract_product_data(soup) -> dict | None:
    if isinstance(soup, dict):
        return soup
    for payload in _iter_json_ld_payloads(soup):
        product = _extract_product_from_json_ld(payload)
        if product is not None:
            debug("product_data.found", source="json_ld", provider="hepsiburada")
            return product
    warn("product_data.missing", source="json_ld", provider="hepsiburada")
    return None


def extract_price(product_data_or_soup):
    if isinstance(product_data_or_soup, dict):
        product_data = product_data_or_soup
    else:
        product_data = extract_product_data(product_data_or_soup)

    if not isinstance(product_data, dict):
        return None

    offers = product_data.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price")
        if price is not None:
            return _format_price_value(price)

    price = product_data.get("price")
    if price is not None:
        return _format_price_value(price)

    return None


def _extract_redux_store(soup):
    if not isinstance(soup, BeautifulSoup):
        return None
    script = soup.select_one("script#reduxStore")
    if script is None:
        return None
    text = (script.string or "").strip()
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        store = json.loads(text[start : end + 1])
        debug("redux_store.found", provider="hepsiburada")
        return store
    except (TypeError, ValueError):
        warn("redux_store.invalid", provider="hepsiburada")
        return None


def _extract_description_from_dom(soup):
    if not isinstance(soup, BeautifulSoup):
        return None

    candidates = []

    product_desc = soup.select_one("div#ProductDescription")
    if product_desc is not None:
        candidates.append(product_desc)

    for element in soup.select("[class*='ProductDescription']"):
        if any(elem is element for elem in candidates):
            continue
        candidates.append(element)

    best = None
    for element in candidates:
        text = " ".join(element.get_text(" ", strip=True).split())
        if not text:
            continue
        if _is_placeholder_description_text(text):
            continue
        if _is_generic_hepsiburada_description(text):
            continue
        if best is None or len(text) > len(best):
            best = text

    return best


def _clean_description_text(value):
    if not value:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def _strip_placeholder_tokens(text):

    cleaned = " ".join(str(text).split())
    cleaned = re.sub(
        r"\s+(?:STD|N/?A|NONE|NA|NUL)\s*$", "", cleaned, flags=re.IGNORECASE
    )
    return cleaned.strip()


_META_FIELDS = {
    "name",
    "url",
    "image",
    "offers",
    "brand",
    "description",
    "category",
    "@id",
    "@type",
    "@context",
    "aggregateRating",
    "review",
    "hasMerchantReturnPolicy",
    "merchantReturnPolicy",
    "shippingDetails",
    "mainEntityOfPage",
    "potentialAction",
    "additionalType",
}


def _extract_attribute_fallback_description(product_data):
    if not isinstance(product_data, dict):
        return None

    name = _extract_first_string(product_data.get("name")) or ""
    name_lower = name.lower()

    snippets = []
    for key, value in product_data.items():
        normalized_key = str(key).lower()
        if normalized_key in _META_FIELDS or normalized_key.startswith("@"):
            continue
        if isinstance(value, (dict, list, tuple, bool)) or value is None:
            continue
        text = _extract_first_string(value)
        if not text or _is_placeholder_description_text(text):
            continue
        if text.lower() in name_lower:
            continue
        snippets.append(f"{key}: {text}")

    if snippets:
        heading = f"{name}." if name else ""
        return f"{heading} {'. '.join(snippets)}.".strip()
    return None


def _build_description(soup, product_data):
    parts = []
    dom_description = _extract_description_from_dom(soup)
    dom_description = (
        _strip_placeholder_tokens(dom_description) if dom_description else None
    )
    debug("desc.dom", has_dom=dom_description is not None)

    name = _extract_first_string(product_data.get("name")) or ""
    if dom_description:
        rest = dom_description
        if name and rest.lower().startswith(name.lower()):
            rest = rest[len(name) :].strip()
        if rest and len(rest) > 10:
            parts.append(dom_description)

    json_ld_description = _extract_first_string(product_data.get("description"))
    if json_ld_description and not _is_placeholder_description_text(
        json_ld_description
    ):
        if _is_generic_hepsiburada_description(json_ld_description):
            if not dom_description:
                parts.append(json_ld_description)
        else:
            parts.append(json_ld_description)
    debug("desc.json_ld", has_json_ld=json_ld_description is not None)

    if not parts:
        fallback = _extract_attribute_fallback_description(product_data)
        if fallback:
            debug("desc.fallback", source="attributes")
            return fallback
        debug("desc.none")
        return None
    debug(
        "desc.ok",
        source="dom" if len(parts) == 1 and parts[0] == dom_description else "combined",
    )
    return " ".join(parts)


def _is_generic_hepsiburada_description(value):
    if not value:
        return False
    normalized = "".join(ch for ch in str(value) if ch.isalnum()).lower()
    markers = (
        "eniyifiyatlahepsiburadadan",
        "satinalabilirsiniz",
        "ayağınızagelsin",
        "eniyifiyatlahepsiburada",
        "avantajlıfiyatlarla",
    )
    return any(marker in normalized for marker in markers)


def _extract_redux_product(redux):
    if not isinstance(redux, dict):
        return None
    product_state = redux.get("productState")
    if not isinstance(product_state, dict):
        return None
    product = product_state.get("product")
    if not isinstance(product, dict):
        return None
    return product


def _extract_image(product_data):
    image = product_data.get("image")
    if isinstance(image, list):
        image = image[0] if image else None
    if isinstance(image, dict):
        image = image.get("url")
    if isinstance(image, str):
        return image.replace("{size}", "375")
    return None


def _detect_category(product_data, redux_product):
    if isinstance(redux_product, dict):
        categories = redux_product.get("categories")
        if isinstance(categories, list) and categories:
            last = categories[-1]
            name = (
                _extract_first_string(last.get("categoryName"))
                if isinstance(last, dict)
                else None
            )
            if name:
                return name
    category = product_data.get("category")
    if category:
        return category
    return "unknown"


def _extract_availability(product_data, redux_product):
    offers = product_data.get("offers")
    if isinstance(offers, dict) and offers.get("availability"):
        return offers.get("availability")
    if isinstance(redux_product, dict):
        if redux_product.get("isInStock"):
            return "https://schema.org/InStock"
        return "https://schema.org/OutOfStock"
    return None


def _extract_custom_data(product_data, redux_product):
    custom = {}
    debug("custom_data.start")

    if isinstance(redux_product, dict):
        merchant = redux_product.get("merchantName")
        if merchant:
            custom["merchant"] = merchant
        product_id = redux_product.get("productId")
        if product_id:
            custom["product_id"] = product_id

        categories = redux_product.get("categories")
        if isinstance(categories, list) and categories:
            names = [
                c.get("categoryName")
                for c in categories
                if isinstance(c, dict) and c.get("categoryName")
            ]
            if names:
                custom["category_path"] = names

        listings = redux_product.get("listings")
        if isinstance(listings, list) and listings:
            listing_data = []
            for listing in listings[:3]:
                if not isinstance(listing, dict):
                    continue
                entry = {}
                if listing.get("merchantName"):
                    entry["merchant"] = listing["merchantName"]
                price = listing.get("price")
                if price is None:
                    prices = listing.get("prices")
                    if isinstance(prices, list) and prices:
                        first = prices[0]
                        if isinstance(first, dict):
                            price = first.get("value")
                if price is None:
                    price = listing.get("unitPrice")
                if price is not None:
                    entry["price"] = price
                original_price = listing.get("originalPrice")
                if original_price is None:
                    original_price = listing.get("minimumPrice")
                if original_price is not None:
                    entry["original_price"] = original_price
                if entry:
                    listing_data.append(entry)
            if listing_data:
                custom["listings"] = listing_data

        reviews = redux_product.get("reviews")
        if isinstance(reviews, dict):
            review_data = {}
            if reviews.get("customerReviewScore") is not None:
                review_data["score"] = reviews["customerReviewScore"]
            if reviews.get("customerReviewCount") is not None:
                review_data["count"] = reviews["customerReviewCount"]
            if review_data:
                custom["reviews"] = review_data

    debug("custom_data.done", keys=list(custom.keys()))
    return custom

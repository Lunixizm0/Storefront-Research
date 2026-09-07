# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import re

from scrape.debug import debug, warn

from .api import get_product_descriptions_from_api
from .common import _extract_first_string, _format_price_value, _iter_json_ld_payloads

__all__ = [
    "_BOILERPLATE_MARKERS",
    "_build_description",
    "_contains_boilerplate",
    "_detect_category_from_product_data",
    "_extract_attributes_dict",
    "_extract_description_clean",
    "_extract_image",
    "_strip_sentences_before_marker",
    "extract_price",
    "extract_price_from_product_data",
    "extract_product_data",
]


def extract_product_data(soup) -> dict | None:
    for payload in _iter_json_ld_payloads(soup):
        if not isinstance(payload, dict):
            continue

        if payload.get("@type") == "Product":
            debug("product_data.found", source="json_ld", match="@type")
            return payload

        offers = payload.get("offers")
        if isinstance(offers, dict) and payload.get("name"):
            debug("product_data.found", source="json_ld", match="offers_and_name")
            return payload

    warn("product_data.missing", source="json_ld")
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


def extract_price_from_product_data(product_data):
    return extract_price(product_data)


def _detect_category_from_product_data(product_data):
    if not isinstance(product_data, dict):
        return "unknown"

    for key in ("category", "categoryName", "itemCategory", "productCategory"):
        candidate = _extract_first_string(product_data.get(key))
        if candidate:
            return candidate

    for key in ("pattern", "type", "kind"):
        candidate = _extract_first_string(product_data.get(key))
        if candidate:
            return candidate

    return "unknown"


def _extract_attributes_dict(product_data):
    attributes = {}
    if not isinstance(product_data, dict):
        return attributes

    for field_name in ("additionalProperty", "attributes"):
        items = product_data.get(field_name)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and "key" in item and "value" in item:
                key = _extract_first_string(item.get("key"))
                value = _extract_first_string(item.get("value"))
            elif isinstance(item, dict):
                key = _extract_first_string(item.get("name"))
                value = _extract_first_string(
                    item.get("value")
                ) or _extract_first_string(item.get("unitText"))
            else:
                continue
            if key and value:
                attributes[key] = value
    return attributes


_BOILERPLATE_MARKERS = (
    "tarafından gönderilecektir",
    "kampanya fiyatından satılmak üzere",
    "satış fiyatını satıcı belirlemektedir",
    "birden fazla satıcı tarafından satılabilir",
    "adet sipariş verilebilir",
    "siparişinizi iptal etmek istemeniz durumunda",
    "ürünün satıcıları ürün için belirledikleri fiyata",
    "göre sıralanmaktadır",
    "ücretsiz iade",
    "incelemiş olduğunuz ürünün",
    "stok sunulmuştur",
    "limit kurumsal siparişlerde",
    "saklı tutar",
    "15 gün içinde",
    "bu üründen",
    "farklı limitler belirlenebilmektedir",
    "satıcı puanlarına",
    "teslimat statülerine",
    "kargonun bedava olup olmamasına",
    "hızlı teslimat ile teslim edilip edilememesine",
    "stok ve kategorileri bilgilerine",
    "gerçekleştirilen indirimler",
    "iade koşulları",
    "söz konusu ürün",
    "satın alındıktan sonra",
    "iptal etmek istemeniz durumunda",
    "adedin hepsi",
    "iptal edilecektir",
    "stoklarımıza",
    "siparişiniz onaylandıktan",
    "satılmak üzere",
)


def _contains_boilerplate(text: str) -> bool:
    lower = " ".join(text.split()).lower()
    for marker in _BOILERPLATE_MARKERS:
        if marker in lower:
            return True
    return bool(re.search(r"\[page", text))


def _strip_sentences_before_marker(text: str) -> str:
    if not text:
        return ""

    parts = re.split(r"(?<=[.!?])\s+", text)
    kept = []
    for part in parts:
        if not part.strip():
            continue
        if _contains_boilerplate(part):
            continue
        cleaned = re.sub(r"\[page(?:=\"[^\"]*\")?=[^\]]*\][^\[]*\[/page\]", "", part)
        cleaned = re.sub(r"\[page(?:=\"[^\"]*\")?=[^\]]*\]", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            kept.append(cleaned)

    return " ".join(kept).strip()


def _extract_description_clean(product_data):
    raw = product_data.get("description")
    if isinstance(raw, str):
        cleaned = _strip_sentences_before_marker(raw)
        return cleaned or None
    return None


def _build_description(product_data):
    if not isinstance(product_data, dict):
        debug("ty.desc.skip", reason="no_product_data")
        return None

    sku = product_data.get("sku")
    if sku:
        api_description = get_product_descriptions_from_api(str(sku))
        if api_description:
            cleaned_api = _strip_sentences_before_marker(api_description).strip()
            if cleaned_api and len(cleaned_api) > 10:
                debug("ty.desc.ok", source="api", sku=sku)
                return cleaned_api

    clean_description = _extract_description_clean(product_data)
    if clean_description and len(clean_description) > 10:
        debug("ty.desc.ok", source="clean", sku=sku)
        return clean_description

    attributes = _extract_attributes_dict(product_data)
    name = _extract_first_string(product_data.get("name"))

    if attributes:
        snippets = []
        for key, value in list(attributes.items())[:10]:
            snippets.append(f"{key}: {value}")
        base = ". ".join(snippets)
        if name:
            debug("ty.desc.ok", source="attributes_with_name", sku=sku)
            return f"{name}. Features: {base}."
        debug("ty.desc.ok", source="attributes_only", sku=sku)
        return base

    debug("ty.desc.ok", source="jsonld_fallback", sku=sku)
    return _extract_first_string(product_data.get("description"))


def _extract_image(product_data):
    image = product_data.get("image")
    if isinstance(image, list):
        image = image[0] if image else None
    if isinstance(image, dict):
        content_url = image.get("contentUrl")
        if isinstance(content_url, str):
            return content_url
        if isinstance(content_url, list) and content_url:
            return str(content_url[0])
        return None
    if isinstance(image, str):
        return image
    return None

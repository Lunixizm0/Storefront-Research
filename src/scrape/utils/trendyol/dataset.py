# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

from scrape.dataset import ProductDataset
from scrape.debug import debug, warn

from .builders import (
    _build_complete_the_look,
    _build_currencies,
    _build_delivery,
    _build_installments,
    _build_merchant_questions,
    _build_product_eligibility,
    _build_reviews,
    _build_seller_acceptance,
    _build_seller_follower,
    _build_seller_store,
    _build_slicing_attributes,
    _build_social_proof,
    _build_stamps,
    _build_stickers,
    _build_vas,
    _build_video,
)
from .common import _safe_api_call, _str
from .parsing import (
    _build_description,
    _detect_category_from_product_data,
    _extract_image,
    extract_price,
    extract_product_data,
)
from .shared_props import _detect_custom_data, _extract_shared_props

__all__ = ["build_product_dataset", "extract_product_dataset"]


def build_product_dataset(
    product_data, category="unknown", custom_data=None, soup=None
):
    if not isinstance(product_data, dict):
        warn("dataset.skipped", provider="trendyol", reason="product_data_missing")
        return None

    shared_props = _extract_shared_props(soup) if soup is not None else None
    debug(
        "dataset.build.start",
        provider="trendyol",
        shared_props_found=shared_props is not None,
    )

    offers_raw = product_data.get("offers")
    offers = offers_raw if isinstance(offers_raw, dict) else {}

    brand = product_data.get("brand")
    if isinstance(brand, dict):
        brand_name = brand.get("name")
    else:
        brand_name = product_data.get("manufacturer")

    detected_category = (
        category
        if category and category != "unknown"
        else _detect_category_from_product_data(product_data)
    )
    merged_custom_data = _detect_custom_data(product_data, shared_props=shared_props)
    if isinstance(custom_data, dict):
        merged_custom_data.update(custom_data)

    reviews = _build_reviews(product_data, shared_props)
    vas = _build_vas(product_data, shared_props)
    installments = _build_installments(product_data, shared_props)

    api_data = {}
    for name, builder in (
        ("delivery", _build_delivery),
        ("merchant_questions", _build_merchant_questions),
        ("seller_store", _build_seller_store),
        ("seller_follower", _build_seller_follower),
        ("seller_acceptance", _build_seller_acceptance),
        ("product_eligibility", _build_product_eligibility),
        ("slicing_attributes", _build_slicing_attributes),
        ("complete_the_look", _build_complete_the_look),
        ("social_proof", _build_social_proof),
        ("video", _build_video),
        ("stickers", _build_stickers),
        ("stamps", _build_stamps),
        ("currencies", _build_currencies),
    ):
        value = _safe_api_call(builder, product_data, shared_props)
        if value is not None:
            api_data[name] = value

    if api_data:
        merged_custom_data["api_data"] = api_data

    debug(
        "dataset.build.complete",
        provider="trendyol",
        api_sections=list(api_data),
        reviews=reviews is not None,
        vas=vas is not None,
        installments=installments is not None,
    )

    return ProductDataset(
        source="trendyol",
        category=str(detected_category),
        name=_str(product_data.get("name")),
        brand=_str(brand_name),
        price=_str(extract_price(product_data)),
        currency=_str(offers.get("priceCurrency")),
        url=_str(offers.get("url")),
        sku=_str(product_data.get("sku")),
        image=_extract_image(product_data),
        description=_build_description(product_data),
        availability=_str(offers.get("availability")),
        item_condition=_str(offers.get("itemCondition")),
        reviews=reviews,
        vas=vas,
        installments=installments,
        custom_data=merged_custom_data if isinstance(merged_custom_data, dict) else {},
    )


def extract_product_dataset(soup, category="unknown", custom_data=None):
    product_data = extract_product_data(soup)
    debug(
        "dataset.extract",
        provider="trendyol",
        product_data_found=product_data is not None,
    )
    return build_product_dataset(
        product_data, category=category, custom_data=custom_data, soup=soup
    )

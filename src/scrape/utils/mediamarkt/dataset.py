# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

from scrape.dataset import ProductDataset
from scrape.debug import debug, warn

from ..trendyol.common import _extract_first_string, _format_price_value, _safe_api_call
from .builders import (
    _build_availability,
    _build_category,
    _build_custom_data,
    _build_description,
    _build_features,
    _build_image,
    _build_installment,
    _build_name,
    _build_price,
    _build_reviews,
    _build_va_services,
)
from .graphql import (
    get_loyalty_points_from_graphql,
    get_product_media_from_graphql,
)
from .parsing import (
    _product_entity,
    extract_product_data,
    extract_product_id,
)

_BASE_URL = "https://www.mediamarkt.com.tr"

__all__ = ["build_product_dataset", "extract_product_dataset"]


def _absolute_url(value):
    if not value:
        return None
    if value.startswith(("http://", "https://")):
        return value
    return f"{_BASE_URL}{value}"


def _first_price_amount(state, product_id):
    amount, _currency = _build_price(state, product_id) or (None, None)
    return amount


def _supplementary_data(state, product_id, url):
    """Attempt the GraphQL path for data absent from the SSR cache."""
    extra = {}

    entity = _product_entity(state, product_id)
    loyalty = (
        entity.get("globalLoyItemAssessment") if isinstance(entity, dict) else None
    )
    if not isinstance(loyalty, dict) or loyalty.get("amount") is None:
        price = _first_price_amount(state, product_id)
        if price is not None:
            assessed = _safe_api_call(
                get_loyalty_points_from_graphql,
                product_id,
                price,
                "TRY",
                product_url=url,
            )
            if isinstance(assessed, dict) and assessed.get("amount") is not None:
                extra["loyalty_points"] = assessed["amount"]

    media = _safe_api_call(get_product_media_from_graphql, product_id, product_url=url)
    if isinstance(media, dict):
        videos = media.get("videos")
        if isinstance(videos, list) and videos:
            video_links = []
            for v in videos:
                if not isinstance(v, dict):
                    continue
                assets = {
                    a.get("name"): a.get("url")
                    for a in v.get("assets") or []
                    if isinstance(a, dict)
                }
                for candidate in (
                    assets.get("picture"),
                    assets.get("thumb"),
                    assets.get("icon"),
                ):
                    if candidate:
                        video_links.append(candidate)
                        break
            if video_links:
                extra["videos"] = video_links

    if extra:
        detail = ", ".join(
            f"{k}={'videos' if isinstance(v, list) else v}" for k, v in extra.items()
        )
        debug("supplementary.found", provider="mediamarkt", detail=detail)
    return extra


def build_product_dataset(state, url=None, product_id=None, category="unknown"):
    if not isinstance(state, dict):
        warn("dataset.skipped", provider="mediamarkt", reason="apollo_state_missing")
        return None

    if product_id is None:
        product_id = extract_product_id(url)
    if not product_id:
        for key in state:
            if key.startswith("GraphqlProduct:Media:tr-TR:"):
                product_id = key.rsplit(":", 1)[-1]
                break
    if not product_id:
        warn("dataset.skipped", provider="mediamarkt", reason="product_id_missing")
        return None

    entity = _product_entity(state, product_id)
    if not isinstance(entity, dict):
        warn("dataset.skipped", provider="mediamarkt", reason="product_entity_missing")
        return None

    debug(
        "dataset.build.start",
        provider="mediamarkt",
        product_id=product_id,
        product_found=True,
    )

    price, currency = _build_price(state, product_id) or (None, "TRY")
    reviews = _build_reviews(state, product_id)
    installments = _build_installment(state, product_id)
    vas = _build_va_services(state, product_id)

    custom_data = _build_custom_data(state, product_id, entity)
    if url:
        custom_data["product_id"] = product_id
        custom_data["url"] = (
            _absolute_url(_extract_first_string(entity.get("url"))) or url
        )

    supplementary = _supplementary_data(state, product_id, url)
    if supplementary:
        custom_data["graphql"] = supplementary

    category = (
        _build_category(state, product_id)
        if category in (None, "", "unknown")
        else category
    )

    dataset = ProductDataset(
        source="mediamarkt",
        category=category,
        name=_build_name(entity),
        brand=_extract_first_string(entity.get("manufacturer")),
        price=_format_price_value(price) if price is not None else None,
        currency=currency or "TRY",
        url=_absolute_url(_extract_first_string(entity.get("url"))) or url,
        sku=product_id,
        image=_build_image(state, product_id),
        description=_build_description(entity),
        availability=_build_availability(state, product_id),
        item_condition=None,
        reviews=reviews,
        installments=installments,
        vas=vas,
        custom_data=custom_data,
    )
    debug(
        "dataset.build.complete",
        provider="mediamarkt",
        populated_fields=sum(
            value is not None
            for value in (
                dataset.name,
                dataset.brand,
                dataset.price,
                dataset.sku,
                dataset.description,
                dataset.availability,
            )
        ),
    )
    return dataset


def extract_product_dataset(soup, url=None, category="unknown"):
    state, product_id = extract_product_data(soup, url)
    debug(
        "dataset.extract",
        provider="mediamarkt",
        state_found=state is not None,
        product_id=product_id,
    )
    return build_product_dataset(
        state, url=url, product_id=product_id, category=category
    )

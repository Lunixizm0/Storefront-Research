# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

from scrape.debug import debug

from .parsing import (
    _decode_mm_html,
    _feature_entities,
    _get_entity,
    _iter_breadcrumbs,
    _product_entity,
)

__all__ = [
    "_build_availability",
    "_build_category",
    "_build_custom_data",
    "_build_description",
    "_build_features",
    "_build_highlights",
    "_build_image",
    "_build_installment",
    "_build_name",
    "_build_price",
    "_build_reviews",
    "_build_status",
    "_build_va_services",
]


def _entity(state, product_id, feature_name, key=None):
    prefix = f"{feature_name}:Media:tr:{product_id}"
    for k, v in (state or {}).items():
        if k.startswith(prefix):
            return v
    return None


def _build_name(entity):
    if not isinstance(entity, dict):
        return None
    return entity.get("title")


def _build_price(state, product_id):
    for value in _price_values(state, product_id):
        promo = value.get("promoPrice")
        if isinstance(promo, dict) and promo.get("amount") is not None:
            amount = promo["amount"]
            currency = value.get("currency") or "TRY"
            return amount, currency
    return None


def _price_values(state, product_id):
    prefix = "CofrPriceFeature:"
    for key, value in (state or {}).items():
        if key.startswith(prefix) and product_id in key:
            yield value


def _build_installment(state, product_id):
    for value in _price_values(state, product_id):
        price = value.get("price")
        if not isinstance(price, dict):
            continue
        installment = price.get("installment")
        if not isinstance(installment, dict):
            continue
        if installment.get("duration") is None:
            continue
        out = {
            "duration": installment.get("duration"),
            "monthly_rate": installment.get("monthlyRate"),
            "total_amount": installment.get("totalAmount"),
        }
        debug(
            "installment.found",
            provider="mediamarkt",
            **{k: v for k, v in out.items() if v is not None},
        )
        return out
    return None


def _build_image(state, product_id):
    value = _entity(state, product_id, "CofrMediaAssetsFeature")
    if not isinstance(value, dict):
        return None
    main = value.get("productMainImage")
    if isinstance(main, dict) and main.get("link"):
        return main["link"]
    images = value.get("productImages")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict) and first.get("link"):
            return first["link"]
    return None


def _build_description(entity):
    if not isinstance(entity, dict):
        return None
    text = _decode_mm_html(entity.get("description"))
    if not text:
        return None
    soup_text = _html_to_text(text)
    return soup_text or None


def _html_to_text(html):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    return text.replace("\u00a0", " ")


def _build_category(state, product_id):
    entity = _product_entity(state, product_id)
    crumbs = _iter_breadcrumbs(entity)
    if crumbs:
        return crumbs[-1]
    return "unknown"


def _build_reviews(state, product_id):
    value = _entity(state, product_id, "CofrCoreFeature")
    if not isinstance(value, dict):
        return None
    stats = value.get("reviewStatistics")
    if not isinstance(stats, dict):
        return None
    out = {}
    if stats.get("averageOverallRating") is not None:
        out["average_rating"] = stats["averageOverallRating"]
    if stats.get("totalReviewCount") is not None:
        out["count"] = stats["totalReviewCount"]
    if stats.get("overallRatingRange") is not None:
        out["overall_rating_range"] = stats["overallRatingRange"]
    return out or None


def _build_status(state, product_id):
    delivery = _entity(state, product_id, "CofrDeliveryFeature")
    pickup = _entity(state, product_id, "CofrPickupFeature")
    online = _entity(state, product_id, "CofrOnlineStatusFeature")
    out = {}
    if isinstance(delivery, dict):
        inner = delivery.get("delivery")
        if isinstance(inner, dict):
            if inner.get("displayStatus"):
                out["delivery"] = inner["displayStatus"]
            if inner.get("deliveryStatus"):
                out["delivery_status"] = inner["deliveryStatus"]
    if isinstance(pickup, dict):
        if pickup.get("displayStatus"):
            out["pickup"] = pickup["displayStatus"]
        if pickup.get("pickupStatus"):
            out["pickup_status"] = pickup["pickupStatus"]
    if isinstance(online, dict):
        if online.get("onlineStatus"):
            out["online_status"] = online["onlineStatus"]
        for flag_key, label in (
            ("isAvailableForDelivery", "is_available_for_delivery"),
            ("isAvailableForPickup", "is_available_for_pickup"),
            ("isAvailableAndBuyable", "is_available_and_buyable"),
            ("isInAssortment", "is_in_assortment"),
        ):
            if online.get(flag_key) is not None:
                out[label] = online[flag_key]
    return out or None


def _availability_text(status):
    if not isinstance(status, dict):
        return None
    online = status.get("online_status")
    if online == "PERMANENTLY_NOT_AVAILABLE":
        return "OutOfStock"
    if online == "TEMPORARILY_NOT_AVAILABLE":
        return "OutOfStock"
    if status.get("is_available_and_buyable") is True:
        return "InStock"
    if status.get("delivery") == "AVAILABLE" or status.get("pickup") == "AVAILABLE":
        return "InStock"
    if online == "AVAILABLE":
        return "InStock"
    if status.get("is_in_assortment") is True:
        return "PreOrder"
    return "OutOfStock"


def _build_availability(state, product_id):
    return _availability_text(_build_status(state, product_id))


def _build_highlights(state, product_id):
    value = _entity(state, product_id, "CofrCoreFeature")
    if not isinstance(value, dict):
        return None
    highlights = value.get("highlightedFeatures")
    if not isinstance(highlights, list) or not highlights:
        return None
    rows = []
    for ref in highlights:
        if not isinstance(ref, dict):
            continue
        entity = _get_entity(state, ref.get("__ref"))
        if not isinstance(entity, dict):
            continue
        name = entity.get("name")
        values = entity.get("values")
        if name:
            rows.append({"name": name, "values": values})
    return rows or None


def _build_features(state, product_id):
    rows = _feature_entities(state, product_id)
    if not rows:
        return None
    grouped = {}
    for group_name, name, value in rows:
        grouped.setdefault(group_name, []).append({"name": name, "value": value})
    return grouped


def _build_va_services(state, product_id):
    prefix = "GraphqlServiceProductV2:"
    services = []
    for key, value in (state or {}).items():
        if not key.startswith(prefix):
            continue
        if not isinstance(value, dict):
            continue
        entry = {}
        if value.get("productId"):
            entry["product_id"] = value["productId"]
        if value.get("title"):
            entry["title"] = value["title"]
        if value.get("price") is not None:
            entry["price"] = value["price"]
        if entry:
            services.append(entry)
    return services or None


def _build_custom_data(state, product_id, entity):
    custom = {}
    debug("custom_data.start")

    for value in _price_values(state, product_id):
        price = value.get("price")
        if isinstance(price, dict):
            if price.get("amount") is not None:
                custom["price"] = price["amount"]
            if price.get("shippingCost") is not None:
                custom["shipping_cost"] = price["shippingCost"]
        if value.get("promoPrice") is not None and isinstance(
            value["promoPrice"], dict
        ):
            promo = value["promoPrice"]
            if promo.get("promoIds") is not None:
                custom["promo_ids"] = promo["promoIds"]
        if value.get("vatRate") is not None:
            custom["vat_rate"] = value["vatRate"]
        if value.get("strikePrice") is not None:
            custom["strike_price"] = value["strikePrice"]
        if value.get("productGroupId") is not None:
            custom["product_group_id"] = value["productGroupId"]

    if isinstance(entity, dict):
        for key, label in (
            ("productId", "product_id"),
            ("ean", "ean"),
            ("tax", "tax"),
            ("manufacturer", "manufacturer"),
            ("manufacturerId", "manufacturer_id"),
            ("featureName", "feature_name"),
            ("kindOfProduct", "kind_of_product"),
            ("rawTitle", "raw_title"),
            ("productGroupId", "product_group_id"),
        ):
            if entity.get(key) is not None:
                custom[label] = entity[key]

        breadcrumbs = _iter_breadcrumbs(entity)
        if breadcrumbs:
            custom["category_path"] = breadcrumbs

        loyalty = entity.get("globalLoyItemAssessment")
        if isinstance(loyalty, dict) and loyalty.get("amount") is not None:
            custom["loyalty_points"] = loyalty["amount"]

        groups = _get_entity(state, f"GraphqlProductFeatureGroups:{product_id}")
        if isinstance(groups, dict):
            group_names = [
                g.get("featureGroupName")
                for g in groups.get("featureGroups") or []
                if isinstance(g, dict) and g.get("featureGroupName")
            ]
            if group_names:
                custom["feature_groups"] = group_names

    status = _build_status(state, product_id)
    if status:
        custom["status"] = status

    highlights = _build_highlights(state, product_id)
    if highlights:
        custom["highlights"] = highlights

    features = _build_features(state, product_id)
    if features:
        custom["full_features"] = features

    services = _build_va_services(state, product_id)
    if services:
        custom["va_services"] = services

    debug("custom_data.done", keys=list(custom.keys()))
    return custom

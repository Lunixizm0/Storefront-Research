# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import json

from bs4 import BeautifulSoup

from scrape.debug import debug

from .common import _extract_first_string

__all__ = [
    "_detect_custom_data",
    "_extract_listing_entry",
    "_extract_listings_custom",
    "_extract_reviews_custom",
    "_extract_shared_props",
    "_find_category_path_in_shared_props",
    "_sp_category_id",
    "_sp_delivery",
    "_sp_group_tag_ids",
    "_sp_p_group_id",
    "_sp_product",
    "_sp_product_id",
    "_sp_seller_id",
    "_sp_selling_price",
    "_sp_sticker_ids",
    "_sp_tag_ids",
    "_sp_video_id",
]


def _extract_shared_props(soup) -> dict | None:
    if not isinstance(soup, BeautifulSoup):
        debug("shared_props.skip", reason="no_soup")
        return None

    for script in soup.select("script"):
        text = script.string or ""
        if "__envoy__SHARED_PROPS" not in text:
            continue

        marker = 'window["__envoy__SHARED_PROPS"]='
        start = text.find(marker)
        if start == -1:
            start = text.find("__envoy__SHARED_PROPS")
            start = text.find("=", start) + 1

        brace = text.find("{", start)
        if brace == -1:
            debug("shared_props.no_brace")
            continue

        depth = 0
        i = brace
        in_str = False
        while i < len(text):
            ch = text[i]
            if in_str:
                if ch == "\\":
                    i += 2
                    continue
                if ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
            i += 1

        try:
            payload = json.loads(text[brace : i + 1])
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            debug("shared_props.parse_failed", error=str(exc))
            continue
        if isinstance(payload, dict):
            debug("shared_props.ok", keys=list(payload.keys())[:5])
            return payload

    debug("shared_props.not_found")
    return None


def _extract_reviews_custom(product_data, shared_props):
    if isinstance(shared_props, dict):
        product = shared_props.get("product")
        if isinstance(product, dict):
            rating = product.get("ratingScore")
            if isinstance(rating, dict):
                review_data = {}
                if rating.get("averageRating") is not None:
                    review_data["score"] = rating["averageRating"]
                if rating.get("commentCount") is not None:
                    review_data["count"] = rating["commentCount"]
                if review_data:
                    return review_data

    aggregate_rating = product_data.get("aggregateRating")
    if isinstance(aggregate_rating, dict):
        review_data = {}
        if aggregate_rating.get("ratingValue") is not None:
            review_data["score"] = aggregate_rating["ratingValue"]
        count = aggregate_rating.get("reviewCount") or aggregate_rating.get(
            "ratingCount"
        )
        if count is not None:
            review_data["count"] = count
        if review_data:
            return review_data

    return None


def _extract_listing_entry(merchant_dict):
    if not isinstance(merchant_dict, dict):
        return None

    entry = {"merchant": merchant_dict.get("name")}

    variants = merchant_dict.get("variants")
    if isinstance(variants, list) and variants:
        variant = variants[0]
        if isinstance(variant, dict):
            price = variant.get("price")
            if isinstance(price, dict):
                discounted = price.get("discountedPrice") or price.get("sellingPrice")
                if isinstance(discounted, dict) and discounted.get("value") is not None:
                    entry["price"] = discounted["value"]
                original = price.get("originalPrice")
                if isinstance(original, dict) and original.get("value") is not None:
                    entry["original_price"] = original["value"]
    return entry


def _extract_listings_custom(shared_props):
    if not isinstance(shared_props, dict):
        return None

    product = shared_props.get("product")
    if not isinstance(product, dict):
        return None

    merchant_listing = product.get("merchantListing")
    if not isinstance(merchant_listing, dict):
        return None

    listings = []

    merchant = merchant_listing.get("merchant")
    if isinstance(merchant, dict) and merchant.get("name"):
        entry = _extract_listing_entry(
            {
                "name": merchant.get("name"),
                "variants": [merchant_listing.get("winnerVariant")]
                if merchant_listing.get("winnerVariant")
                else None,
            }
        )
        if entry:
            listings.append(entry)

    other_merchants = merchant_listing.get("otherMerchants")
    if isinstance(other_merchants, list):
        for other in other_merchants:
            entry = _extract_listing_entry(other)
            if entry:
                listings.append(entry)

    if not listings:
        return None
    return listings


def _find_category_path_in_shared_props(node, depth=0):
    if depth > 8 or node is None:
        return None
    if isinstance(node, dict):
        for key in ("categoryTree", "webCategoryTree"):
            cand = node.get(key)
            if isinstance(cand, list):
                path = [
                    c.get("name") for c in cand if isinstance(c, dict) and c.get("name")
                ]
                if path:
                    return path
        for value in node.values():
            found = _find_category_path_in_shared_props(value, depth + 1)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_category_path_in_shared_props(item, depth + 1)
            if found:
                return found
    return None


def _detect_custom_data(product_data, shared_props=None):
    custom = {}
    debug("ty.custom_data.start")

    if not isinstance(product_data, dict):
        debug("ty.custom_data.skip", reason="no_product_data")
        return custom

    pattern = _extract_first_string(product_data.get("pattern"))
    if pattern:
        custom["pattern"] = pattern

    additional_properties = product_data.get("additionalProperty")
    if isinstance(additional_properties, list):
        attributes = {}
        for entry in additional_properties:
            if not isinstance(entry, dict):
                continue
            name = _extract_first_string(entry.get("name"))
            value = _extract_first_string(entry.get("value")) or _extract_first_string(
                entry.get("unitText")
            )
            if not name or not value:
                continue
            lowered = name.lower()
            if "renk" in lowered or "brand" in lowered or "marka" in lowered:
                continue
            attributes[name] = value
        if attributes:
            custom["attributes"] = attributes

    reviews = _extract_reviews_custom(product_data, shared_props)
    if reviews:
        custom["reviews"] = reviews

    listings = _extract_listings_custom(shared_props)
    if listings:
        custom["listings"] = listings
        if not custom.get("merchant") and isinstance(listings[0], dict):
            merchant = listings[0].get("merchant")
            if merchant:
                custom["merchant"] = merchant

    if isinstance(shared_props, dict):
        path = _find_category_path_in_shared_props(shared_props)
        if not path:
            category = (
                shared_props.get("category")
                if isinstance(shared_props.get("category"), dict)
                else None
            )
            if category:
                hierarchy = category.get("hierarchy")
                if hierarchy:
                    path = [p.strip() for p in str(hierarchy).split("/") if p.strip()]
        if path:
            custom["category_path"] = path

    debug("ty.custom_data.done", keys=list(custom.keys()))
    return custom


def _sp_product(shared_props):
    if not isinstance(shared_props, dict):
        return None
    product = shared_props.get("product")
    return product if isinstance(product, dict) else None


def _sp_product_id(product_data, shared_props):
    pid = product_data.get("sku") if isinstance(product_data, dict) else None
    if pid is None:
        sp = _sp_product(shared_props)
        if sp:
            pid = sp.get("id")
    return pid


def _sp_seller_id(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return None
    listing = sp.get("merchantListing")
    if isinstance(listing, dict):
        merchant = listing.get("merchant")
        if isinstance(merchant, dict):
            return merchant.get("id")
    return None


def _sp_category_id(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return None
    category = sp.get("category")
    if isinstance(category, dict):
        return category.get("id")
    return None


def _sp_selling_price(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return None
    listing = sp.get("merchantListing")
    if not isinstance(listing, dict):
        return None
    winner = listing.get("winnerVariant")
    if not isinstance(winner, dict):
        return None
    price = winner.get("price")
    if not isinstance(price, dict):
        return None
    selling = price.get("sellingPrice")
    if isinstance(selling, dict) and selling.get("value") is not None:
        return selling["value"]
    discounted = price.get("discountedPrice")
    if isinstance(discounted, dict) and discounted.get("value") is not None:
        return discounted["value"]
    return None


def _sp_group_tag_ids(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return None
    for key in ("groupTagIds", "groupIdList", "groupTagId"):
        val = sp.get(key)
        if val:
            return val
    return None


def _sp_video_id(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return None
    for key in ("videoContentId", "videoId", "videoContents"):
        val = sp.get(key)
        if isinstance(val, dict):
            vid = val.get("id") or val.get("videoId")
            if vid:
                return vid
        elif val:
            return val
    return None


def _sp_p_group_id(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return None
    for key in ("pGroupId", "productGroupId", "group_id"):
        val = sp.get(key)
        if val:
            return val
    return None


def _sp_sticker_ids(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return None
    for key in ("stickerIds", "stickers"):
        val = sp.get(key)
        if val:
            return val
    return None


def _sp_tag_ids(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return None
    for key in ("tagIds", "tags", "filterableLabelIds"):
        val = sp.get(key)
        if val:
            return val
    return None


def _sp_delivery(shared_props):
    sp = _sp_product(shared_props)
    if not sp:
        return (None, None)
    listing = sp.get("merchantListing")
    if not isinstance(listing, dict):
        return (None, None)
    winner = listing.get("winnerVariant")
    item_number = None
    listing_id = None
    if isinstance(winner, dict):
        item_number = winner.get("itemNumber")
        if item_number is None:
            item_number = winner.get("item")
        listing_id = winner.get("listingId") or winner.get("id")
    if listing_id is None:
        listing_id = listing.get("listingId")
    return (item_number, listing_id)

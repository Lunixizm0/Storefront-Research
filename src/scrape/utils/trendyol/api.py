# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

from scrape.debug import error

from .common import _is_placeholder_description_text
from .http import get_common_api_headers, requests

__all__ = [
    "_flatten_vas_attributes",
    "get_complete_the_look_from_api",
    "get_currencies_from_api",
    "get_delivery_date_from_api",
    "get_installment_from_api",
    "get_merchant_questions_from_api",
    "get_product_descriptions_from_api",
    "get_product_eligibility_from_api",
    "get_reviews_from_api",
    "get_seller_acceptance_from_api",
    "get_seller_follower_from_api",
    "get_seller_store_from_api",
    "get_slicing_attributes_from_api",
    "get_social_proof_from_api",
    "get_stamps_from_api",
    "get_stickers_from_api",
    "get_vas_from_api",
    "get_video_content_from_api",
]


def get_product_descriptions_from_api(product_id):
    if not product_id:
        return None

    try:
        url = f"https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/component-read/component/{product_id}"
        headers = get_common_api_headers()
        params = {"channelId": "1"}

        response = requests.get(url, params=params, headers=headers, timeout=20)
        if response.status_code != 200:
            return None

        data = response.json()
        if not data.get("isSuccess") or not data.get("result"):
            return None

        descriptions = data.get("result", {}).get("descriptions", [])
        if not descriptions:
            return None

        valid_texts = []
        for desc in descriptions:
            text = desc.get("text") if isinstance(desc, dict) else None
            if not text or _is_placeholder_description_text(text):
                continue
            valid_texts.append(text)

        if valid_texts:
            return " ".join(valid_texts)

        return None
    except Exception as e:
        error("api.error", api="product_descriptions", error=f"{type(e).__name__}: {e}")
        return None


def get_reviews_from_api(product_id, page=0, page_size=5):
    # Fetch product reviews, AI summary, and rating stats via review-read API
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/review-read/product-reviews/detailed"
        params = {
            "contentId": product_id,
            "page": page,
            "pageSize": page_size,
            "channelId": "1",
        }
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="reviews", error=f"{type(e).__name__}: {e}")
        return None


def get_delivery_date_from_api(content_id, item_number, winner_listing_id):
    # Fetch delivery dates and shipping info via delivery-date-content API
    try:
        url = f"https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/delivery-date-content/delivery-date/{content_id}/itemNumber/{item_number}"
        params = {"winnerListingId": winner_listing_id, "channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="delivery_date", error=f"{type(e).__name__}: {e}")
        return None


def get_installment_from_api(amount, category_id, group_tag_ids, total_amount=None):
    # Fetch per-bank installment plans via installment API
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/installment/"
        params = {
            "amount": amount,
            "totalAmount": total_amount or amount,
            "categoryId": category_id,
            "categoryIds": str(category_id),
            "codEligible": "true",
            "clientPage": "PDP",
            "isUserTyPlusActive": "false",
            "groupTagIds": group_tag_ids,
            "channelId": "1",
        }
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="installment", error=str(e))
        return None


def get_merchant_questions_from_api(content_id, page=0, size=4, fulfilment_type="mp"):
    # Fetch answered Q&A via merchant-questions API.
    try:
        url = f"https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/merchant-questions/content/{content_id}/answered"
        params = {
            "fulfilmentType": fulfilment_type,
            "excludeTag": "false",
            "page": page,
            "size": size,
            "isMobile": "false",
            "channelId": "1",
        }
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="merchant_questions", error=str(e))
        return None


def get_seller_acceptance_from_api(seller_id):
    # Check seller question acceptance status via seller-acceptance API.
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/merchant-questions/seller-acceptance"
        params = {"sellerId": seller_id, "isMobile": "false", "channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="seller_acceptance", error=str(e))
        return None


def get_video_content_from_api(video_id):
    # Fetch video metadata (MP4 URL, thumbnail) via video-content API.
    try:
        url = f"https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/video-content/{video_id}"
        params = {"channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="video_content", error=str(e))
        return None


def get_currencies_from_api(culture="tr-TR", storefront_id=1):
    # Fetch TCMB exchange rates via currencies API.
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/currencies"
        params = {"storefrontId": storefront_id, "culture": culture, "channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="currencies", error=str(e))
        return None


def get_stickers_from_api(sticker_ids, platform="WEB"):
    # Fetch decorative/promotional stickers via stickers API
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/stickers/stickers"
        params = {"stickerIds": sticker_ids, "platform": platform, "channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="stickers", error=str(e))
        return None


def get_complete_the_look_from_api(content_id, culture="tr-TR"):
    # Fetch complete-the-look markers via complete-the-look API.
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/complete-the-look/markers"
        params = {
            "contentId": content_id,
            "intersactionAreaPadding": 5,
            "pointLabelGap": 30,
            "labelsGap": 4,
            "labelHeight": 28,
            "imageSize": "398x597",
            "labelPrefix": "+",
            "culture": culture,
            "channelId": "1",
        }
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="complete_the_look", error=str(e))
        return None


def get_slicing_attributes_from_api(group_id, content_id):
    # Fetch product variant options (colors, sizes) via slicing-attributes API.
    try:
        url = f"https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/slicing-attributes/product-group/{group_id}/slicing-attributes"
        params = {"contentId": content_id, "channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="slicing_attributes", error=str(e))
        return None


def get_social_proof_from_api(content_ids):
    # Fetch favorite count / social proof badges via social-proof API.
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/social-proof/"
        params = {"contentIds": content_ids, "channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="social_proof", error=str(e))
        return None


def get_seller_store_from_api(seller_id):
    # Fetch merchant store info (score, metrics, tenure) via seller-store API.
    try:
        url = f"https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/seller-store/{seller_id}/header-information"
        params = {"channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="seller_store", error=str(e))
        return None


def get_seller_follower_from_api(seller_id, culture="tr-TR"):
    # Fetch merchant store follower count via sellerstore-follow API.
    try:
        url = f"https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/sellerstore-follow/{seller_id}/follower-count"
        params = {"culture": culture, "channelId": "1", "checkCoupon": "true"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="seller_follower", error=str(e))
        return None


def get_stamps_from_api(tag_ids, platform="WEB"):
    # Fetch promotional stamps / badges via stamps API.
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/stamps/"
        params = {"tagIds": tag_ids, "platform": platform, "channelId": "1"}
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="stamps", error=str(e))
        return None


def get_product_eligibility_from_api(
    category_id, bank_category_id, price, culture="tr-TR", storefront_id=1
):
    # Fetch product eligibility status via product-eligibility API.
    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/product-eligibility/"
        params = {
            "categoryId": category_id,
            "bankCategoryId": bank_category_id,
            "price": price,
            "culture": culture,
            "storefrontId": storefront_id,
            "channelId": "1",
        }
        response = requests.get(
            url, params=params, headers=get_common_api_headers(), timeout=20
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="product_eligibility", error=str(e))
        return None


def get_vas_from_api(
    product_id=None, storefront_id=1, language="tr", shared_props=None
):
    sp = shared_props.get("product") if isinstance(shared_props, dict) else None
    if not isinstance(sp, dict):
        return None

    category_id = (sp.get("category") or {}).get("id")
    brand_id = (sp.get("brand") or {}).get("id")
    merchant_listing = sp.get("merchantListing") or {}
    seller_id = (merchant_listing.get("merchant") or {}).get("id")
    price_info = (merchant_listing.get("winnerVariant") or {}).get("price") or {}
    selling_price = (price_info.get("sellingPrice") or {}).get("value") or (
        price_info.get("discountedPrice") or {}
    ).get("value")
    attributes = _flatten_vas_attributes(sp.get("attributes"))
    pid = product_id or sp.get("id")

    if not all([pid, category_id, brand_id, seller_id, selling_price, attributes]):
        return None

    try:
        url = "https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/vas/"
        params = {"storefrontId": storefront_id, "language": language, "channelId": "1"}
        payload = {
            "categoryId": category_id,
            "brandId": brand_id,
            "sellerId": seller_id,
            "sellingPrice": selling_price,
            "attributes": attributes,
        }
        response = requests.post(
            url,
            params=params,
            json=payload,
            headers=get_common_api_headers(),
            timeout=20,
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        error("api.error", api="vas", error=f"{type(e).__name__}: {e}")
        return None


def _flatten_vas_attributes(attributes):
    if isinstance(attributes, dict):
        return [
            {
                "key": str(k),
                "value": str(v)
                if not isinstance(v, dict)
                else str(v.get("name") or v.get("name") or v),
            }
            for k, v in attributes.items()
        ]
    if isinstance(attributes, list):
        flat = []
        for attr in attributes:
            if not isinstance(attr, dict):
                continue
            key = attr.get("key")
            if isinstance(key, dict):
                key = key.get("name")
            value = attr.get("value")
            if isinstance(value, dict):
                value = value.get("name")
            if key or value:
                flat.append(
                    {
                        "key": str(key) if key else "",
                        "value": str(value) if value else "",
                    }
                )
        return flat
    return None

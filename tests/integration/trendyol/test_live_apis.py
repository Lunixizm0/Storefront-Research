from __future__ import annotations

import pytest

from scrape.utils.trendyol import (
    _extract_shared_props,
    get_complete_the_look_from_api,
    get_currencies_from_api,
    get_delivery_date_from_api,
    get_installment_from_api,
    get_merchant_questions_from_api,
    get_product_descriptions_from_api,
    get_product_eligibility_from_api,
    get_raw_html,
    get_reviews_from_api,
    get_seller_acceptance_from_api,
    get_seller_follower_from_api,
    get_seller_store_from_api,
    get_slicing_attributes_from_api,
    get_social_proof_from_api,
    get_stamps_from_api,
    get_stickers_from_api,
    get_vas_from_api,
    get_video_content_from_api,
    parse_html,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def live_ids():
    return {
        "product_id": "1081766367",
        "seller_id": "624588",
        "group_id": "821600500",
        "listing_id": "e6e8fd8c3d61815b470afae19defb73a",
        "item_number": "1494882815",
        "video_id": "6d1ee37d-be18-4bf1-a17f-464d7c2a3643",
    }


def test_real_review_read_api(live_ids):
    data = get_reviews_from_api(live_ids["product_id"])
    assert data is not None, "review-read API returned None"
    assert data.get("isSuccess") is True
    result = data.get("result", {})
    assert "summary" in result
    summary = result["summary"]
    assert "averageRating" in summary
    assert summary["averageRating"] > 0
    assert "totalRatingCount" in summary
    assert "ratingCounts" in summary
    assert isinstance(summary["ratingCounts"], list)
    assert "tags" in summary
    assert "reviews" in result
    assert isinstance(result["reviews"], list)
    if "aiSummary" in result:
        assert isinstance(result["aiSummary"], str)


def test_real_component_read_api(live_ids):
    text = get_product_descriptions_from_api(live_ids["product_id"])
    assert text is not None, "component-read API returned no text"
    assert len(text) > 10
    assert isinstance(text, str)


def test_real_delivery_date_api(live_ids):
    data = get_delivery_date_from_api(
        live_ids["product_id"],
        live_ids["item_number"],
        live_ids["listing_id"],
    )
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", {})
    assert "deliveryDates" in result
    assert isinstance(result["deliveryDates"], list)
    assert len(result["deliveryDates"]) > 0
    first = result["deliveryDates"][0]
    assert "deliveryStartDate" in first
    assert "deliveryEndDate" in first


def test_real_installment_api():
    data = get_installment_from_api(4199, 1058, "eac211e6-2e86-42fa-a755-87479743934a")
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", {})
    assert "summary" in result
    assert "installmentOffers" in result
    offers = result["installmentOffers"]
    assert isinstance(offers, list)
    assert len(offers) > 0
    first_bank = offers[0]
    assert "installements" in first_bank
    assert len(first_bank["installements"]) > 0


def test_real_merchant_questions_api(live_ids):
    data = get_merchant_questions_from_api(live_ids["product_id"])
    assert data is not None
    assert data.get("isSuccess") is True
    questions = data.get("questions", {})
    assert "content" in questions
    assert "totalElements" in questions


def test_real_seller_acceptance_api(live_ids):
    data = get_seller_acceptance_from_api(live_ids["seller_id"])
    assert data is not None
    assert "isSellerAcceptQuestions" in data
    assert isinstance(data["isSellerAcceptQuestions"], bool)


def test_real_video_content_api(live_ids):
    data = get_video_content_from_api(live_ids["video_id"])
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", {})
    assert "url" in result
    assert result["url"].endswith(".mp4")
    assert "thumbnail" in result


def test_real_currencies_api():
    data = get_currencies_from_api()
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", [])
    assert isinstance(result, list)
    assert len(result) > 0
    currency_names = {c["currencyName"] for c in result}
    assert "USD" in currency_names
    assert "EUR" in currency_names
    assert "TRY" in currency_names


def test_real_stickers_api():
    data = get_stickers_from_api("1044")
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", [])
    assert isinstance(result, list)


def test_real_complete_the_look_api(live_ids):
    data = get_complete_the_look_from_api(live_ids["product_id"])
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", {})
    assert "markers" in result
    assert isinstance(result["markers"], list)


def test_real_slicing_attributes_api(live_ids):
    data = get_slicing_attributes_from_api(live_ids["group_id"], live_ids["product_id"])
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", [])
    assert isinstance(result, list)
    assert len(result) > 0
    first_group = result[0]
    assert "type" in first_group
    assert "values" in first_group
    assert isinstance(first_group["values"], list)


def test_real_social_proof_api(live_ids):
    data = get_social_proof_from_api(live_ids["product_id"])
    assert data is not None
    assert live_ids["product_id"] in data
    proof = data[live_ids["product_id"]]
    assert "socialProofs" in proof
    assert isinstance(proof["socialProofs"], list)


def test_real_seller_store_api(live_ids):
    data = get_seller_store_from_api(live_ids["seller_id"])
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", {})
    assert "name" in result
    assert "score" in result
    assert "sellerMetrics" in result
    assert isinstance(result["sellerMetrics"], list)


def test_real_seller_follower_api(live_ids):
    data = get_seller_follower_from_api(live_ids["seller_id"])
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", {})
    assert "count" in result
    assert isinstance(result["count"], int)
    assert result["count"] > 0


def test_real_stamps_api():
    data = get_stamps_from_api("4905,8581,9637")
    assert data is not None
    assert data.get("isSuccess") is True
    result = data.get("result", {})
    assert isinstance(result, dict)
    assert len(result) > 0
    for stamp_data in result.values():
        assert "name" in stamp_data
        assert "stamps" in stamp_data


def test_real_product_eligibility_api():
    data = get_product_eligibility_from_api(1058, 13, 4199)
    assert data is not None
    assert data.get("isSuccess") is True


def test_real_vas_api_post_returns_data():
    response = get_raw_html(
        "https://www.trendyol.com/oci/xiaomi-14t-pro-256-g-p-1081766367"
    )
    assert response.status_code == 200
    soup = parse_html(response.content)
    assert soup is not None

    shared_props = _extract_shared_props(soup)
    assert shared_props is not None, "Could not extract __envoy__SHARED_PROPS from page"

    data = get_vas_from_api(shared_props=shared_props)
    if data is not None:
        assert isinstance(data, dict)
    else:
        product = shared_props.get("product") or {}
        attrs = product.get("attributes")
        merchant = (product.get("merchantListing") or {}).get("merchant") or {}
        price_info = (
            (product.get("merchantListing") or {}).get("winnerVariant") or {}
        ).get("price") or {}
        has_price = (
            (price_info.get("sellingPrice") or {}).get("value")
        ) is not None or (
            (price_info.get("discountedPrice") or {}).get("value")
        ) is not None
        pytest.skip(
            f"VAS API returned None - missing fields: "
            f"category={product.get('category') is not None}, "
            f"brand={product.get('brand') is not None}, "
            f"seller={merchant.get('id') is not None}, "
            f"price={has_price}, "
            f"attributes={isinstance(attrs, list) and len(attrs) > 0}"
        )

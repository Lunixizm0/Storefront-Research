from __future__ import annotations

import json
import re

import pytest

from scrape.utils.trendyol import (
    extract_price,
    extract_price_from_product_data,
    extract_product_data,
    extract_product_dataset,
    get_raw_html,
    parse_html,
    product_dataset_to_json,
)

pytestmark = pytest.mark.integration


def test_extracts_price_from_live_trendyol_product(trendyol_url):
    response = get_raw_html(trendyol_url)
    assert response.status_code == 200, (
        f"Request failed for {trendyol_url}: {response.status_code}"
    )

    soup = parse_html(response.content)
    product_data = extract_product_data(soup)
    assert product_data is not None, f"No product JSON found on {trendyol_url}"

    price = extract_price_from_product_data(product_data)
    assert price is not None, f"No price found on {trendyol_url}"
    assert re.search(r"\d[\d.,]*\s*TL", price), (
        f"Unexpected price format for {trendyol_url}: {price}"
    )

    assert extract_price(soup) == price, (
        f"DOM and JSON price mismatch for {trendyol_url}"
    )

    dataset = extract_product_dataset(soup)
    assert dataset is not None
    assert dataset.source == "trendyol"
    assert dataset.category is not None
    assert dataset.price is not None
    assert "brand" not in dataset.custom_data
    assert "color" not in dataset.custom_data
    assert dataset.description is not None and len(dataset.description) > 10, (
        f"Description too short: {dataset.description}"
    )
    json.loads(product_dataset_to_json(dataset))


def test_live_trendyol_product_has_reviews_and_listings(trendyol_url):
    response = get_raw_html(trendyol_url)
    assert response.status_code == 200, (
        f"Request failed for {trendyol_url}: {response.status_code}"
    )

    soup = parse_html(response.content)
    dataset = extract_product_dataset(soup)
    assert dataset is not None

    reviews = dataset.custom_data.get("reviews")
    assert reviews is not None, f"No reviews found on {trendyol_url}"
    assert isinstance(reviews, dict), (
        f"Unexpected reviews type on {trendyol_url}: {reviews}"
    )
    assert "score" in reviews or "count" in reviews

    listings = dataset.custom_data.get("listings")
    assert listings is not None, f"No listings found on {trendyol_url}"
    assert isinstance(listings, list) and len(listings) > 0, (
        f"Empty listings on {trendyol_url}"
    )
    assert all("merchant" in listing for listing in listings), (
        f"Listing missing merchant on {trendyol_url}"
    )

    json.loads(product_dataset_to_json(dataset))

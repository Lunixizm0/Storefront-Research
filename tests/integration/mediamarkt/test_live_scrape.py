from __future__ import annotations

import json
import re

import pytest

from scrape.utils.mediamarkt import (
    extract_product_data,
    extract_product_dataset,
    get_raw_html,
    parse_html,
    product_dataset_to_json,
)

pytestmark = pytest.mark.integration


def test_extracts_product_from_live_mediamarkt_product(mediamarkt_url):
    response = get_raw_html(mediamarkt_url)
    assert response.status_code == 200, (
        f"Request failed for {mediamarkt_url}: {response.status_code}"
    )

    soup = parse_html(response.content)
    state, _product_id = extract_product_data(soup, url=mediamarkt_url)
    assert state is not None, f"No apolloState on {mediamarkt_url}"

    dataset = extract_product_dataset(soup, url=mediamarkt_url)
    assert dataset is not None, f"No dataset built for {mediamarkt_url}"
    assert dataset is not None

    assert dataset.source == "mediamarkt"
    assert dataset.name is not None and len(dataset.name) > 0, (
        f"No name on {mediamarkt_url}"
    )
    assert dataset.brand is not None, f"No brand on {mediamarkt_url}"
    assert dataset.sku is not None, f"No sku on {mediamarkt_url}"
    assert dataset.price is not None, f"No price on {mediamarkt_url}"
    assert re.search(r"\d[\d.,]*\s*TL", dataset.price), (
        f"Unexpected price format on {mediamarkt_url}: {dataset.price}"
    )
    assert dataset.currency == "TRY", (
        f"Unexpected currency on {mediamarkt_url}: {dataset.currency}"
    )
    assert dataset.category not in (None, "unknown"), f"No category on {mediamarkt_url}"
    assert dataset.availability is not None, f"No availability on {mediamarkt_url}"

    assert dataset.description is not None and len(dataset.description) > 10, (
        f"Description too short on {mediamarkt_url}"
    )
    assert dataset.image is not None, f"No image on {mediamarkt_url}"
    assert dataset.url is not None and dataset.url.startswith(
        "https://www.mediamarkt.com.tr/tr/product/"
    ), f"Unexpected url on {mediamarkt_url}: {dataset.url}"

    json.loads(product_dataset_to_json(dataset))


def test_live_mediamarkt_product_has_reviews_and_features(mediamarkt_url):
    response = get_raw_html(mediamarkt_url)
    assert response.status_code == 200, (
        f"Request failed for {mediamarkt_url}: {response.status_code}"
    )

    soup = parse_html(response.content)
    dataset = extract_product_dataset(soup, url=mediamarkt_url)
    assert dataset is not None, f"No dataset built for {mediamarkt_url}"

    assert dataset.reviews is not None, f"No reviews on {mediamarkt_url}"
    assert isinstance(dataset.reviews, dict), (
        f"Unexpected reviews type on {mediamarkt_url}: {dataset.reviews}"
    )
    assert "average_rating" in dataset.reviews or "count" in dataset.reviews, (
        f"Unexpected reviews keys on {mediamarkt_url}: {dataset.reviews}"
    )

    features = dataset.custom_data.get("full_features")
    assert features is None or isinstance(features, dict), (
        f"Unexpected features on {mediamarkt_url}: {features}"
    )

    json.loads(product_dataset_to_json(dataset))

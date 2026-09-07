from __future__ import annotations

import json
import re

import pytest

from scrape.utils.hepsiburada import (
    extract_product_data,
    extract_product_dataset,
    get_raw_html,
    parse_html,
    product_dataset_to_json,
)

pytestmark = pytest.mark.integration


def test_extracts_product_from_live_hepsiburada_product(hepsiburada_url):
    response = get_raw_html(hepsiburada_url)
    assert response.status_code == 200, (
        f"Request failed for {hepsiburada_url}: {response.status_code}"
    )

    soup = parse_html(response.content)
    product_data = extract_product_data(soup)
    assert product_data is not None, f"No product JSON-LD found on {hepsiburada_url}"

    dataset = extract_product_dataset(soup)
    assert dataset is not None

    assert dataset.source == "hepsiburada"
    assert dataset.name is not None and len(dataset.name) > 0, (
        f"No name on {hepsiburada_url}"
    )
    assert dataset.brand is not None, f"No brand on {hepsiburada_url}"
    assert dataset.sku is not None, f"No sku on {hepsiburada_url}"
    assert dataset.price is not None, f"No price on {hepsiburada_url}"
    assert re.search(r"\d[\d.,]*\s*TL", dataset.price), (
        f"Unexpected price format on {hepsiburada_url}: {dataset.price}"
    )
    assert dataset.currency == "TRY", (
        f"Unexpected currency on {hepsiburada_url}: {dataset.currency}"
    )
    assert dataset.category not in (None, "unknown"), (
        f"No category on {hepsiburada_url}"
    )
    assert dataset.availability is not None, f"No availability on {hepsiburada_url}"

    assert dataset.description is not None and len(dataset.description) > 10, (
        f"Description too short on {hepsiburada_url}"
    )

    assert "merchant" in dataset.custom_data, (
        f"No merchant in custom_data on {hepsiburada_url}"
    )

    json.loads(product_dataset_to_json(dataset))


def test_live_hepsiburada_product_has_reviews_and_listings(hepsiburada_url):
    response = get_raw_html(hepsiburada_url)
    assert response.status_code == 200, (
        f"Request failed for {hepsiburada_url}: {response.status_code}"
    )

    soup = parse_html(response.content)
    dataset = extract_product_dataset(soup)

    assert dataset.custom_data.get("reviews") is not None, (
        f"No reviews on {hepsiburada_url}"
    )

    listings = dataset.custom_data.get("listings")
    assert listings is None or (isinstance(listings, list) and len(listings) > 0), (
        f"Unexpected listings on {hepsiburada_url}: {listings}"
    )


def test_live_hepsiburada_product_has_vas():
    response = get_raw_html(
        "https://www.hepsiburada.com/razer-blackshark-v2-pro-2023-kablosuz-gaming-kulaklik-beyaz-rz04-04530200-r3m1-p-HBCV00004MW5Q6"
    )
    assert response.status_code == 200
    soup = parse_html(response.content)
    dataset = extract_product_dataset(soup)
    assert dataset is not None
    vas = dataset.vas
    assert isinstance(vas, list) and len(vas) > 0, "No vas suggestions"
    first = vas[0]
    assert first.get("title") or first.get("suggested_sku"), (
        f"Unexpected vas entry: {first}"
    )

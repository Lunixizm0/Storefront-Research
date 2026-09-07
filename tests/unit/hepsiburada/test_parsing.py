# unit tests for Hepsiburada HTML/JSON parsing - zero network
from __future__ import annotations

import json

from tests.helpers.hepsiburada_fixtures import (
    load_expected,
    load_product_html,
    load_soup,
)


class TestExtractProductData:
    def test_returns_dict(self):
        from scrape.utils.hepsiburada import extract_product_data

        product_data = extract_product_data(load_soup())
        assert isinstance(product_data, dict)

    def test_has_product_type(self):
        from scrape.utils.hepsiburada import extract_product_data

        product_data = extract_product_data(load_soup())
        assert product_data.get("@type") == "Product"

    def test_has_name(self):
        from scrape.utils.hepsiburada import extract_product_data

        product_data = extract_product_data(load_soup())
        assert product_data.get("name") is not None

    def test_has_sku(self):
        from scrape.utils.hepsiburada import extract_product_data

        product_data = extract_product_data(load_soup())
        assert product_data.get("sku") is not None

    def test_has_offers(self):
        from scrape.utils.hepsiburada import extract_product_data

        product_data = extract_product_data(load_soup())
        offers = product_data.get("offers")
        assert offers is not None

    def test_matches_expected(self):
        from scrape.utils.hepsiburada import extract_product_data

        product_data = extract_product_data(load_soup())
        expected = load_expected("product_data.json")
        assert product_data["name"] == expected["name"]
        assert product_data["sku"] == expected["sku"]


class TestExtractPrice:
    def test_returns_price_string(self):
        from scrape.utils.hepsiburada import extract_price, extract_product_data

        product_data = extract_product_data(load_soup())
        price = extract_price(product_data)
        assert price is not None
        assert "TL" in price

    def test_matches_expected(self):
        from scrape.utils.hepsiburada import extract_price, extract_product_data

        product_data = extract_product_data(load_soup())
        price = extract_price(product_data)
        expected_price = load_expected("price.txt")
        assert price == expected_price

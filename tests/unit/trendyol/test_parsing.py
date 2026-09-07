from __future__ import annotations

import json

from tests.helpers.trendyol_fixtures import (
    load_expected,
    load_product_bytes,
    load_product_html,
    load_soup,
)


class TestParseHtml:
    def test_returns_beautifulsoup(self):
        from bs4 import BeautifulSoup

        soup = load_soup()
        assert isinstance(soup, BeautifulSoup)

    def test_html_is_parseable(self):
        html = load_product_html()
        assert len(html) > 1000
        assert "<html" in html.lower() or "<!doctype" in html.lower()


class TestExtractProductData:
    def test_returns_dict(self):
        from scrape.utils.trendyol import extract_product_data

        product_data = extract_product_data(load_soup())
        assert isinstance(product_data, dict)

    def test_has_product_type(self):
        from scrape.utils.trendyol import extract_product_data

        product_data = extract_product_data(load_soup())
        assert product_data is not None
        assert product_data.get("@type") in ("Product", "ProductGroup")

    def test_has_name(self):
        from scrape.utils.trendyol import extract_product_data

        product_data = extract_product_data(load_soup())
        assert product_data is not None
        assert product_data.get("name") is not None

    def test_has_offers_with_price(self):
        from scrape.utils.trendyol import extract_product_data

        product_data = extract_product_data(load_soup())
        assert product_data is not None
        offers = product_data.get("offers")
        assert offers is not None
        assert offers.get("price") is not None

    def test_matches_expected(self):
        from scrape.utils.trendyol import extract_product_data

        product_data = extract_product_data(load_soup())
        assert product_data is not None
        expected = load_expected("product_data.json")
        assert product_data["name"] == expected["name"]
        assert product_data["sku"] == expected["sku"]


class TestExtractPrice:
    def test_from_dict(self):
        from scrape.utils.trendyol import extract_price

        product_data = load_expected("product_data.json")
        price = extract_price(product_data)
        assert price is not None
        assert "TL" in price

    def test_from_soup(self):
        from scrape.utils.trendyol import extract_price

        price = extract_price(load_soup())
        assert price is not None
        assert "TL" in price

    def test_matches_expected(self):
        from scrape.utils.trendyol import extract_price

        product_data = load_expected("product_data.json")
        price = extract_price(product_data)
        expected_price = load_expected("price.txt")
        assert price == expected_price

    def test_format_is_correct(self):
        from scrape.utils.trendyol import extract_price

        product_data = load_expected("product_data.json")
        price = extract_price(product_data)
        assert price is not None
        # Should match pattern like "1234.56 TL"
        import re

        assert re.match(r"\d[\d.,]*\s*TL$", price), f"Unexpected format: {price}"

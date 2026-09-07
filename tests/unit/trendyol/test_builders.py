from __future__ import annotations

from tests.helpers.trendyol_fixtures import load_expected, load_product_bytes, load_soup


class TestFlattenVasAttributes:
    def test_dict_input(self):
        from scrape.utils.trendyol import _flatten_vas_attributes

        attrs = {"Renk": "Siyah", "Beden": "M"}
        result = _flatten_vas_attributes(attrs)
        assert isinstance(result, list)
        assert len(result) == 2
        keys = {r["key"] for r in result}
        assert "Renk" in keys
        assert "Beden" in keys

    def test_list_input(self):
        from scrape.utils.trendyol import _flatten_vas_attributes

        attrs = [
            {"key": "Renk", "value": "Siyah"},
            {"key": "Beden", "value": {"name": "M"}},
        ]
        result = _flatten_vas_attributes(attrs)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["key"] == "Renk"
        assert result[0]["value"] == "Siyah"
        assert result[1]["key"] == "Beden"
        assert result[1]["value"] == "M"

    def test_none_input(self):
        from scrape.utils.trendyol import _flatten_vas_attributes

        assert _flatten_vas_attributes(None) is None

    def test_unsupported_type(self):
        from scrape.utils.trendyol import _flatten_vas_attributes

        assert _flatten_vas_attributes("invalid") is None

    def test_matches_expected(self):
        from scrape.utils.trendyol import _extract_shared_props, _flatten_vas_attributes

        shared_props = _extract_shared_props(load_soup())
        assert shared_props is not None
        product = shared_props["product"]
        result = _flatten_vas_attributes(product.get("attributes"))
        expected = load_expected("vas_attributes.json")
        assert result == expected


class TestExtractReviewsCustom:
    def test_returns_dict_with_score_and_count(self):
        from scrape.utils.trendyol import _extract_reviews_custom

        product_data = {"aggregateRating": {"ratingValue": "4.5", "reviewCount": "100"}}
        reviews = _extract_reviews_custom(product_data, None)
        assert isinstance(reviews, dict)
        assert "score" in reviews
        assert "count" in reviews
        # Score can be string or float
        assert float(reviews["score"]) == 4.5
        assert int(reviews["count"]) == 100

    def test_returns_none_when_no_data(self):
        from scrape.utils.trendyol import _extract_reviews_custom

        assert _extract_reviews_custom({}, None) is None

    def test_matches_expected(self):
        from scrape.utils.trendyol import (
            _extract_reviews_custom,
            _extract_shared_props,
            extract_product_data,
        )

        shared_props = _extract_shared_props(load_soup())
        product_data = extract_product_data(load_soup())
        reviews = _extract_reviews_custom(product_data, shared_props)
        expected = load_expected("reviews_custom.json")
        assert reviews == expected


class TestExtractListingEntry:
    def test_basic_merchant(self):
        from scrape.utils.trendyol import _extract_listing_entry

        merchant = {
            "name": "Test Seller",
            "variants": [
                {
                    "price": {
                        "discountedPrice": {"value": 99.99},
                        "sellingPrice": {"value": 99.99},
                        "originalPrice": {"value": 149.99},
                    }
                }
            ],
        }
        entry = _extract_listing_entry(merchant)
        assert entry is not None
        assert entry["merchant"] == "Test Seller"
        assert entry["price"] == 99.99
        assert entry["original_price"] == 149.99

    def test_none_input(self):
        from scrape.utils.trendyol import _extract_listing_entry

        assert _extract_listing_entry(None) is None

    def test_matches_expected(self):
        from scrape.utils.trendyol import _extract_listing_entry, _extract_shared_props

        shared_props = _extract_shared_props(load_soup())
        assert shared_props is not None
        product = shared_props["product"]
        merchant_raw = product.get("merchantListing", {}).get("merchant")
        if isinstance(merchant_raw, dict):
            entry = _extract_listing_entry(merchant_raw)
            expected = load_expected("listing_entry.json")
            assert entry == expected

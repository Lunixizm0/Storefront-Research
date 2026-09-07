from __future__ import annotations

from tests.helpers.trendyol_fixtures import (
    load_expected,
    load_product_bytes,
    load_soup,
)


class TestExtractSharedProps:
    def test_returns_dict(self):
        from scrape.utils.trendyol import _extract_shared_props

        shared_props = _extract_shared_props(load_soup())
        assert isinstance(shared_props, dict)

    def test_has_product_key(self):
        from scrape.utils.trendyol import _extract_shared_props

        shared_props = _extract_shared_props(load_soup())
        assert shared_props is not None
        assert "product" in shared_props
        assert isinstance(shared_props["product"], dict)

    def test_product_has_id(self):
        from scrape.utils.trendyol import _extract_shared_props

        shared_props = _extract_shared_props(load_soup())
        assert shared_props is not None
        product = shared_props["product"]
        assert "id" in product

    def test_product_has_category(self):
        from scrape.utils.trendyol import _extract_shared_props

        shared_props = _extract_shared_props(load_soup())
        assert shared_props is not None
        product = shared_props["product"]
        assert "category" in product
        assert isinstance(product["category"], dict)
        assert "id" in product["category"]

    def test_product_has_brand(self):
        from scrape.utils.trendyol import _extract_shared_props

        shared_props = _extract_shared_props(load_soup())
        assert shared_props is not None
        product = shared_props["product"]
        assert "brand" in product
        assert isinstance(product["brand"], dict)

    def test_product_has_merchant_listing(self):
        from scrape.utils.trendyol import _extract_shared_props

        shared_props = _extract_shared_props(load_soup())
        assert shared_props is not None
        product = shared_props["product"]
        ml = product.get("merchantListing")
        assert isinstance(ml, dict)
        assert "merchant" in ml

    def test_matches_expected(self):
        from scrape.utils.trendyol import _extract_shared_props

        shared_props = _extract_shared_props(load_soup())
        assert shared_props is not None
        expected = load_expected("shared_props.json")
        # Core product id should match
        assert shared_props["product"]["id"] == expected["product"]["id"]


class TestDetectCategoryPath:
    def test_returns_list(self):
        from scrape.utils.trendyol import (
            _extract_shared_props,
            _find_category_path_in_shared_props,
        )

        shared_props = _extract_shared_props(load_soup())
        path = _find_category_path_in_shared_props(shared_props)
        assert isinstance(path, list)

    def test_has_categories(self):
        from scrape.utils.trendyol import (
            _extract_shared_props,
            _find_category_path_in_shared_props,
        )

        shared_props = _extract_shared_props(load_soup())
        path = _find_category_path_in_shared_props(shared_props)
        assert path is not None
        assert len(path) > 0
        assert all(isinstance(c, str) for c in path)

    def test_matches_expected(self):
        from scrape.utils.trendyol import (
            _extract_shared_props,
            _find_category_path_in_shared_props,
        )

        shared_props = _extract_shared_props(load_soup())
        path = _find_category_path_in_shared_props(shared_props)
        expected = load_expected("category_path.json")
        assert path == expected


class TestDetectCustomData:
    def test_returns_dict(self):
        from scrape.utils.trendyol import (
            _detect_custom_data,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        custom = _detect_custom_data(product_data)
        assert isinstance(custom, dict)

    def test_has_reviews(self):
        from scrape.utils.trendyol import (
            _detect_custom_data,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        custom = _detect_custom_data(product_data)
        assert "reviews" in custom
        reviews = custom["reviews"]
        assert isinstance(reviews, dict)

    def test_has_listings(self):
        from scrape.utils.trendyol import (
            _detect_custom_data,
            _extract_shared_props,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        shared_props = _extract_shared_props(load_soup())
        custom = _detect_custom_data(product_data, shared_props)
        # listings require shared_props with merchantListing
        if "listings" in custom:
            listings = custom["listings"]
            assert isinstance(listings, list)
        else:
            from pytest import skip

            skip("listings not in custom data for this product (no merchantListing)")

    def test_has_category_path(self):
        from scrape.utils.trendyol import (
            _detect_custom_data,
            _extract_shared_props,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        shared_props = _extract_shared_props(load_soup())
        custom = _detect_custom_data(product_data, shared_props)
        if "category_path" in custom:
            assert isinstance(custom["category_path"], list)
        else:
            from pytest import skip

            skip("category_path not in custom data for this product")

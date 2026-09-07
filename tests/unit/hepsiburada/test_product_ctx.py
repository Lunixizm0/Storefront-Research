from __future__ import annotations

from tests.helpers.hepsiburada_fixtures import (
    load_expected,
    load_redux_store,
    load_soup,
)


class TestExtractProductCtx:
    def test_returns_dict(self):
        from scrape.utils.hepsiburada import (
            _extract_product_ctx,
            extract_product_data,
        )

        soup = load_soup()
        product_data = extract_product_data(soup)
        ctx = _extract_product_ctx(soup, product_data)
        assert isinstance(ctx, dict)

    def test_has_sku(self):
        from scrape.utils.hepsiburada import (
            _extract_product_ctx,
            extract_product_data,
        )

        soup = load_soup()
        product_data = extract_product_data(soup)
        ctx = _extract_product_ctx(soup, product_data)
        assert "sku" in ctx

    def test_has_url(self):
        from scrape.utils.hepsiburada import (
            _extract_product_ctx,
            extract_product_data,
        )

        soup = load_soup()
        product_data = extract_product_data(soup)
        ctx = _extract_product_ctx(soup, product_data)
        assert "url" in ctx
        assert ctx["url"].startswith("http")

    def test_matches_expected(self):
        from scrape.utils.hepsiburada import (
            _extract_product_ctx,
            extract_product_data,
        )

        soup = load_soup()
        product_data = extract_product_data(soup)
        ctx = _extract_product_ctx(soup, product_data)
        assert ctx is not None
        expected = load_expected("product_ctx.json")
        assert ctx["sku"] == expected["sku"]


class TestDetectCategory:
    def test_returns_string(self):
        from scrape.utils.hepsiburada import (
            _detect_category,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        redux = load_redux_store()
        redux_product = None
        if redux and "productState" in redux:
            redux_product = redux["productState"].get("product")
        category = _detect_category(product_data, redux_product)
        assert isinstance(category, str)

    def test_not_unknown(self):
        from scrape.utils.hepsiburada import (
            _detect_category,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        redux = load_redux_store()
        redux_product = None
        if redux and "productState" in redux:
            redux_product = redux["productState"].get("product")
        category = _detect_category(product_data, redux_product)
        assert category != "unknown"

    def test_matches_expected(self):
        from scrape.utils.hepsiburada import (
            _detect_category,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        redux = load_redux_store()
        redux_product = None
        if redux and "productState" in redux:
            redux_product = redux["productState"].get("product")
        category = _detect_category(product_data, redux_product)
        expected = load_expected("category.txt")
        assert category == expected


class TestExtractAvailability:
    def test_returns_string_or_none(self):
        from scrape.utils.hepsiburada import (
            _extract_availability,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        redux = load_redux_store()
        redux_product = None
        if redux and "productState" in redux:
            redux_product = redux["productState"].get("product")
        availability = _extract_availability(product_data, redux_product)
        assert availability is None or isinstance(availability, str)


class TestExtractImage:
    def test_returns_url(self):
        from scrape.utils.hepsiburada import (
            _extract_image,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        image = _extract_image(product_data)
        assert image is None or image.startswith("http")

    def test_matches_expected(self):
        from scrape.utils.hepsiburada import (
            _extract_image,
            extract_product_data,
        )

        product_data = extract_product_data(load_soup())
        image = _extract_image(product_data)
        expected = load_expected("image.txt")
        if expected:
            assert image == expected

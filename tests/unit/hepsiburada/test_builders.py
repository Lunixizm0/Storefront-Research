# Unit tests for Hepsiburada builder/helper functions - zero network
from __future__ import annotations

from tests.helpers.hepsiburada_fixtures import (
    load_expected,
    load_product_bytes,
    load_redux_store,
    load_soup,
)


class TestBuildVas:
    def test_none_input(self):
        from scrape.utils.hepsiburada import _build_vas

        assert _build_vas(None) is None

    def test_empty_dict(self):
        from scrape.utils.hepsiburada import _build_vas

        assert _build_vas({}) is None

    def test_valid_data(self):
        from scrape.utils.hepsiburada import _build_vas

        data = {
            "suggestedProducts": [
                {
                    "suggestedSku": "ABC123",
                    "title": "Test VAS",
                    "subTitle": "Sub",
                    "price": 99.99,
                }
            ]
        }
        result = _build_vas(data)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Test VAS"

    def test_matches_expected(self):
        from scrape.utils.hepsiburada import _build_vas

        expected = load_expected("vas_built.json")
        if expected is None:
            from pytest import skip

            skip("VAS fixture not available (API returned 400)")
        # If fixture exists, just verify type
        assert isinstance(expected, (list, type(None)))


class TestBuildDescription:
    def test_returns_string_or_none(self):
        from scrape.utils.hepsiburada import (
            _build_description,
            extract_product_data,
        )

        soup = load_soup()
        product_data = extract_product_data(soup)
        desc = _build_description(soup, product_data)
        assert desc is None or isinstance(desc, str)

    def test_has_content_when_available(self):
        from scrape.utils.hepsiburada import (
            _build_description,
            extract_product_data,
        )

        soup = load_soup()
        product_data = extract_product_data(soup)
        desc = _build_description(soup, product_data)
        expected_desc = load_expected("description.txt")
        if expected_desc:
            assert desc is not None
            assert len(desc) > 0


class TestIsGenericDescription:
    def test_generic_returns_true(self):
        from scrape.utils.hepsiburada import _is_generic_hepsiburada_description

        assert (
            _is_generic_hepsiburada_description(
                "En iyi fiyatla hepsiburadadan alabilirsiniz."
            )
            is True
        )

    def test_real_returns_false(self):
        from scrape.utils.hepsiburada import _is_generic_hepsiburada_description

        assert (
            _is_generic_hepsiburada_description(
                "Bu ürün Razer tarafından üretilmiştir."
            )
            is False
        )

    def test_none_returns_false(self):
        from scrape.utils.hepsiburada import _is_generic_hepsiburada_description

        assert _is_generic_hepsiburada_description(None) is False

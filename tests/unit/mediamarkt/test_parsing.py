from __future__ import annotations

from scrape.utils import mediamarkt
from scrape.utils.mediamarkt.parsing import _product_id_from_url
from tests.helpers.mediamarkt_fixtures import load_apollo_state, load_soup


class TestProductIdFromUrl:
    def test_extracts_trailing_id(self):
        assert (
            _product_id_from_url(
                "https://www.mediamarkt.com.tr/tr/product/_slug-prod-1232522.html"
            )
            == "1232522"
        )

    def test_returns_none_for_unmatched(self):
        assert (
            _product_id_from_url("https://www.mediamarkt.com.tr/tr/category/x.html")
            is None
        )

    def test_returns_none_for_empty(self):
        assert _product_id_from_url("") is None
        assert _product_id_from_url(None) is None


class TestExtractProductData:
    def test_returns_state_and_id(self):
        soup = load_soup()
        state, product_id = mediamarkt.extract_product_data(
            soup, url="...-1232522.html"
        )
        assert isinstance(state, dict)
        assert product_id == "1232522"

    def test_state_contains_product_entity(self):
        state, product_id = mediamarkt.extract_product_data(
            load_soup(), url="x-1232522.html"
        )
        assert state is not None
        assert product_id is not None
        key = f"GraphqlProduct:Media:tr-TR:{product_id}"
        assert key in state
        entity = state[key]
        assert isinstance(entity, dict)
        assert entity.get("ean") == "5025155081754"

    def test_state_contains_price_entity(self):
        state, _ = mediamarkt.extract_product_data(load_soup(), url="x-1232522.html")
        assert state is not None
        price = mediamarkt._build_price(state, "1232522")
        assert price is not None
        amount, currency = price
        assert isinstance(amount, (int, float))
        assert currency == "TRY"

    def test_id_fallback_without_url(self):
        soup = load_soup()
        _, product_id = mediamarkt.extract_product_data(soup)
        assert product_id is not None
        assert product_id.isdigit()


class TestDecodeMmHtml:
    def test_replaces_markers(self):
        assert (
            mediamarkt._decode_mm_html("<lt/>a<gt/>b&nbsp;c&amp;d") == "<a>b\u00a0c&d"
        )


class TestFeatureEntities:
    def test_rows(self):
        state = load_apollo_state()
        rows = list(mediamarkt._feature_entities(state, "1232522"))
        assert rows
        group, name, value = rows[0]
        assert group
        assert name
        assert value is not None

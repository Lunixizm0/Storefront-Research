from __future__ import annotations

import json

from scrape.dataset import ProductDataset
from scrape.utils import mediamarkt
from tests.helpers.mediamarkt_fixtures import (
    load_apollo_state,
    load_expected_dataset,
    load_soup,
)

URL = "https://www.mediamarkt.com.tr/tr/product/_dyson-v15-detect-kablosuz-sarjli-dikey-supurge-sari-nikel-1232522.html"


class TestBuildProductDataset:
    def test_returns_product_dataset(self):
        state = load_apollo_state()
        dataset = mediamarkt.build_product_dataset(state, url=URL, product_id="1232522")
        assert isinstance(dataset, ProductDataset)

    def test_core_fields(self):
        state = load_apollo_state()
        d = mediamarkt.build_product_dataset(state, url=URL, product_id="1232522")
        assert isinstance(d, ProductDataset)
        assert d.source == "mediamarkt"
        assert d.name == "DYSON V15 Detect Absolute Şarjlı Dikey Süpürge"
        assert d.brand == "DYSON"
        assert d.price == "34897.00 TL"
        assert d.currency == "TRY"
        assert d.sku == "1232522"
        assert d.category == "Şarjlı Dikey Süpürge"

    def test_url_is_absolute(self):
        state = load_apollo_state()
        d = mediamarkt.build_product_dataset(state, url=URL, product_id="1232522")
        assert isinstance(d, ProductDataset)
        assert d.url is not None and d.url.startswith(
            "https://www.mediamarkt.com.tr/tr/product/"
        )

    def test_matches_expected(self):
        state = load_apollo_state()
        d = mediamarkt.build_product_dataset(state, url=URL, product_id="1232522")
        assert isinstance(d, ProductDataset)
        expected = load_expected_dataset()
        got = d.to_dict()
        assert got["name"] == expected["name"]
        assert got["price"] == expected["price"]
        assert got["availability"] == expected["availability"]
        assert got["sku"] == expected["sku"]

    def test_null_price_is_safe(self):
        state = load_apollo_state()
        # 137220224 is a sibling entity in the fixture with a null price.
        d = mediamarkt.build_product_dataset(state, url=URL, product_id="137220224")
        assert isinstance(d, ProductDataset)
        assert d.price is None


class TestExtractProductDataset:
    def test_from_soup(self):
        d = mediamarkt.extract_product_dataset(load_soup(), url=URL)
        assert isinstance(d, ProductDataset)
        assert d.sku == "1232522"
        assert d.name is not None

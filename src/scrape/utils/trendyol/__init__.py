# scrape.utils.trendyol package facade that keeps the module-level API

from . import api, builders, common, dataset, http, parsing, shared_props
from .common import (
    _extract_first_string,
    _format_price_value,
    _is_placeholder_description_text,
    _iter_json_ld_payloads,
    _normalize_json_value,
    _safe_api_call,
    _str,
    parse_html,
    product_dataset_to_json,
)

__all__: list[str] = (
    [
        "_extract_first_string",
        "_format_price_value",
        "_is_placeholder_description_text",
        "_iter_json_ld_payloads",
        "_normalize_json_value",
        "_safe_api_call",
        "_str",
        "parse_html",
        "product_dataset_to_json",
    ]
    + api.__all__
    + builders.__all__
    + common.__all__
    + dataset.__all__
    + http.__all__
    + parsing.__all__
    + shared_props.__all__
)

for _module in (api, builders, common, dataset, http, parsing, shared_props):
    for _name in _module.__all__:
        globals()[_name] = getattr(_module, _name)
del _module, _name

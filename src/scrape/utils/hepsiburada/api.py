# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

import json
import re
import uuid

from bs4 import BeautifulSoup

from scrape.debug import debug

from .http import _api_headers, _to_int_list, requests

__all__ = [
    "_HepbAPIContext",
    "_extract_product_ctx",
    "_merge_product_meta",
    "get_ask_to_seller_from_api",
    "get_installment_from_api",
    "get_listings_from_api",
    "get_other_merchants_from_api",
    "get_payment_options_from_api",
    "get_shipping_due_date_from_api",
    "get_vas_from_api",
    "get_without_affordability_from_api",
]


def _extract_product_ctx(soup, product_data):
    ctx = {}
    debug("ctx.extract.start", sku=(product_data or {}).get("sku"))

    if isinstance(product_data, dict):
        ctx["sku"] = product_data.get("sku")
        offers = product_data.get("offers")
        if isinstance(offers, dict):
            ctx["url"] = offers.get("url")
    debug("ctx.extract.from_product_data", sku=ctx.get("sku"), url=ctx.get("url"))

    if isinstance(soup, BeautifulSoup):
        script = soup.select_one("script#reduxStore")
        text = (script.string or "").strip() if script is not None else ""
        if text:
            try:
                store = json.loads(text[text.find("{") : text.rfind("}") + 1])
            except (TypeError, ValueError, json.JSONDecodeError):
                debug("ctx.extract.redux_parse_failed")
                store = None
            if isinstance(store, dict):
                product_state = store.get("productState")
                if isinstance(product_state, dict):
                    product = product_state.get("product")
                    if isinstance(product, dict):
                        if ctx.get("sku") is None:
                            ctx["sku"] = product.get("sku")
                        if ctx.get("url") is None:
                            ctx["url"] = product.get("url")
                        if ctx.get("url") is None and product.get("slugName"):
                            _sku = ctx.get("sku") or product.get("sku")
                            if _sku:
                                ctx["url"] = (
                                    "https://www.hepsiburada.com/"
                                    f"{product.get('slugName')}-p-{_sku}"
                                )
                        if ctx.get("product_id") is None:
                            ctx["product_id"] = product.get("productId")
                        if ctx.get("definition_id") is None:
                            ctx["definition_id"] = product.get("definitionId")
                        if ctx.get("definition_name") is None:
                            ctx["definition_name"] = product.get("definitionName")
                        if ctx.get("tax_vat_rate") is None:
                            ctx["tax_vat_rate"] = product.get("taxVatRate")
                        listings = product.get("listings")
                        if isinstance(listings, list) and listings:
                            first = listings[0]
                            if isinstance(first, dict):
                                if ctx.get("merchant_id") is None:
                                    ctx["merchant_id"] = first.get("merchantId")
                                if ctx.get("listing_id") is None:
                                    ctx["listing_id"] = first.get("listingId")
                                if ctx.get("merchant_name") is None:
                                    ctx["merchant_name"] = first.get("merchantName")
                                if ctx.get("warehouse_id") is None:
                                    ctx["warehouse_id"] = first.get("warehouseId")
                                if ctx.get("shipment_day") is None:
                                    ctx["shipment_day"] = first.get("shipmentDay")
                                if ctx.get("shipping_profile_id") is None:
                                    ctx["shipping_profile_id"] = first.get(
                                        "shippingProfileId"
                                    )
                                if ctx.get("merchant_city") is None:
                                    ctx["merchant_city"] = first.get("merchantCity")
                                if ctx.get("merchant_country") is None:
                                    ctx["merchant_country"] = first.get(
                                        "merchantCountry"
                                    )
                        # categories from redux product
                        if not ctx.get("root_category_list"):
                            categories = product.get("categories")
                            if isinstance(categories, list) and categories:
                                ids = [
                                    c.get("categoryId")
                                    for c in categories
                                    if isinstance(c, dict) and c.get("categoryId")
                                ]
                                if ids:
                                    ctx["root_category_list"] = ids
                                    ctx["root_buying_category_list"] = [ids[-1]]
                        debug(
                            "ctx.extract.redux_ok",
                            sku=ctx.get("sku"),
                            definition_id=ctx.get("definition_id"),
                            merchant_id=ctx.get("merchant_id"),
                        )

        # backfill from raw HTML regardless of redux presence
        html = str(soup)
        try:
            import re

            if ctx.get("definition_id") is None:
                md = re.search(r'"definitionId":(\d+)', html)
                if md:
                    ctx["definition_id"] = int(md.group(1))
            if ctx.get("definition_name") is None:
                mn = re.search(r'"definitionName":"([^"]+)"', html)
                if mn:
                    ctx["definition_name"] = mn.group(1)
            if ctx.get("tax_vat_rate") is None:
                mt = re.search(r'"taxVatRate":(\d+)', html)
                if mt:
                    ctx["tax_vat_rate"] = int(mt.group(1))
            if ctx.get("product_id") is None:
                mp = re.search(r'"productId":"([^"]+)"', html)
                if mp:
                    ctx["product_id"] = mp.group(1)
            if not ctx.get("root_category_list"):
                mr = re.search(r'"rootCategoryList":(\[.*?\])', html)
                if mr:
                    ids = [
                        int(x)
                        for x in re.findall(r'categoryId":"(\d+)"', mr.group(1))
                        if int(x) != 0
                    ]
                    if ids:
                        ctx["root_category_list"] = ids
                        ctx["root_buying_category_list"] = [ids[-1]]
        except Exception as exc:
            debug("ctx.extract.html_backfill_failed", error=str(exc))

    if ctx.get("sku") is None and isinstance(product_data, dict):
        ctx["sku"] = product_data.get("sku")

    debug(
        "ctx.extract.done",
        sku=ctx.get("sku"),
        definition_id=ctx.get("definition_id"),
        merchant_id=ctx.get("merchant_id"),
        url=ctx.get("url"),
    )
    return ctx


class _HepbAPIContext:
    def __init__(
        self, soup=None, product_data=None, anonymous_id=None, product_url=None
    ):
        self.ctx = _extract_product_ctx(soup, product_data)
        self.soup = soup
        self.product_data = product_data or {}
        self.anonymous_id = anonymous_id or str(uuid.uuid4())
        self.product_url = (
            product_url
            or self.ctx.get("url")
            or (
                f"https://www.hepsiburada.com/-p-{self.ctx['sku']}"
                if self.ctx.get("sku")
                else "https://www.hepsiburada.com"
            )
        )
        if not self.ctx.get("sku") and isinstance(product_data, dict):
            self.ctx["sku"] = product_data.get("sku")


def get_listings_from_api(sku, product_url=None):
    debug("api.listings.start", sku=sku)
    ctx = _HepbAPIContext(product_data={"sku": sku}, product_url=product_url)
    url = f"https://www.hepsiburada.com/api/v1/product/listings/{sku}"
    resp = requests.get(url, headers=_api_headers(ctx.product_url), timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("data") if isinstance(payload, dict) else None
    listings = data.get("listings") if isinstance(data, dict) else None
    if isinstance(listings, list):
        filtered = []
        for listing in listings:
            if not isinstance(listing, dict):
                filtered.append(listing)
                continue
            item = dict(listing)
            item.pop("pbs", None)
            filtered.append(item)
        listings = filtered
    debug(
        "api.listings.ok",
        sku=sku,
        count=len(listings) if isinstance(listings, list) else 0,
    )
    return listings


def get_installment_from_api(
    sku,
    amount=None,
    definition_id=None,
    tax_ratio=None,
    merchant_id=None,
    is_fashion="false",
    product_url=None,
):
    debug("api.installment.start", sku=sku)
    params = {
        "maxInstallment": 12,
        "amount": str(amount or 0),
        "definitionId": str(definition_id or ""),
        "isFashion": str(is_fashion or "false"),
        "consumerFinanceTag": "",
        "paymentTag": "",
        "sku": sku,
        "merchantId": str(merchant_id or ""),
        "taxRatio": str(tax_ratio or ""),
    }
    resp = requests.get(
        "https://www.hepsiburada.com/api/v1/product/installment",
        params=params,
        headers=_api_headers(product_url),
        timeout=30,
    )
    resp.raise_for_status()
    debug("api.installment.ok", sku=sku)
    return resp.json()


def _merge_product_meta(ctx, product_tags=None, **overrides):
    root_category_list = ctx.ctx.get("root_category_list") or []
    root_buying_category_list = ctx.ctx.get("root_buying_category_list") or []

    body = {
        "userId": ctx.anonymous_id,
        "product": {
            "productTags": product_tags if product_tags is not None else [],
            "sku": ctx.ctx.get("sku"),
            "productId": ctx.ctx.get("product_id"),
            "brand": ctx.ctx.get("merchant_name"),
            "merchantId": ctx.ctx.get("merchant_id"),
            "listingId": ctx.ctx.get("listing_id"),
            "rootCategoryList": _to_int_list(root_category_list),
            "rootBuyingCategoryList": _to_int_list(root_buying_category_list),
            "definitionName": ctx.ctx.get("definition_name"),
            "definitionId": str(ctx.ctx.get("definition_id") or ""),
            "taxVatRate": ctx.ctx.get("tax_vat_rate"),
            "campaignIds": [],
        },
    }
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                body["product"][key] = value
    return body


def get_without_affordability_from_api(
    sku,
    product_tags,
    product_url=None,
    anonymous_id=None,
    product_data=None,
    soup=None,
    ctx_dict=None,
    **overrides,
):
    debug("api.without_affordability.start", sku=sku)
    ctx = _HepbAPIContext(
        soup=soup,
        product_data={"sku": sku},
        product_url=product_url,
        anonymous_id=anonymous_id,
    )
    if isinstance(ctx_dict, dict):
        ctx.ctx.update(ctx_dict)
    body = _merge_product_meta(ctx, product_tags=product_tags, **overrides)
    body["affordabilityRequest"] = {
        "product": None,
        "additionalData": None,
        "definitionId": str(ctx.ctx.get("definition_id") or ""),
    }
    headers = _api_headers(ctx.product_url, is_post=True)
    headers.update(
        {
            "x-gotham_is_include_premium_clubs": "true",
            "x-gotham_is_include_payment_campaigns": "true",
            "x-gotham_is_enabled_next_eligible_campaign": "true",
            "x-gotham_is_enabled_evaluate_coupon": "true",
            "x-gotham_app-key": "All",
        }
    )
    resp = requests.post(
        "https://www.hepsiburada.com/api/v1/withoutAffordability",
        headers=headers,
        data=json.dumps(body),
        timeout=30,
    )
    resp.raise_for_status()
    debug("api.without_affordability.ok", sku=sku)
    return resp.json()


def get_vas_from_api(
    sku,
    product_url=None,
    product_data=None,
    soup=None,
    ctx_dict=None,
    **overrides,
):
    debug("api.vas.start", sku=sku)
    ctx = _HepbAPIContext(
        soup=soup,
        product_data={"sku": sku},
        product_url=product_url,
    )
    if isinstance(ctx_dict, dict):
        ctx.ctx.update(ctx_dict)
    definition_name = (
        ctx.ctx.get("definition_name")
        or ctx.ctx.get("name")
        or (product_data.get("name") if isinstance(product_data, dict) else None)
    )
    root_categories = _to_int_list(ctx.ctx.get("root_category_list"))
    price = ctx.ctx.get("price")
    if price is None and isinstance(product_data, dict):
        offers = product_data.get("offers")
        if isinstance(offers, dict):
            price = offers.get("price")
    body = {
        "definationName": definition_name or "",
        "merchantName": ctx.ctx.get("merchant_name") or "",
        "price": price,
        "rootCategories": root_categories,
        "sku": sku,
    }
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                body[key] = value
    resp = requests.post(
        "https://customer-voltran-gw.hepsiburada.com/api/vas/evaluate",
        headers=_api_headers(ctx.product_url, is_post=True),
        data=json.dumps(body),
        timeout=30,
    )
    resp.raise_for_status()
    debug("api.vas.ok", sku=sku)
    return resp.json()


def get_payment_options_from_api(
    sku,
    product_url=None,
    anonymous_id=None,
    definition_id=None,
    **overrides,
):
    debug("api.payment_options.start", sku=sku)
    if anonymous_id is None:
        anonymous_id = str(uuid.uuid4())
    body = {
        "userId": anonymous_id,
        "affordabilityRequest": {
            "product": None,
            "additionalData": None,
            "definitionId": str(definition_id or ""),
        },
    }
    if overrides:
        body["userId"] = anonymous_id
        for key, value in overrides.items():
            if value is not None:
                body[key] = value
    headers = _api_headers(product_url, is_post=True)
    headers.update(
        {
            "x-gotham_is_include_premium_clubs": "true",
            "x-gotham_is_include_payment_campaigns": "true",
            "x-gotham_is_enabled_next_eligible_campaign": "true",
            "x-gotham_is_enabled_evaluate_coupon": "true",
            "x-gotham_app-key": "All",
        }
    )
    resp = requests.post(
        "https://www.hepsiburada.com/api/v1/paymentOptions",
        headers=headers,
        data=json.dumps(body),
        timeout=30,
    )
    resp.raise_for_status()
    debug("api.payment_options.ok", sku=sku)
    return resp.json()


def get_other_merchants_from_api(
    sku,
    product_tags,
    product_url=None,
    anonymous_id=None,
    merchant_id=None,
    merchant_name=None,
    listing_id=None,
    final_price_on_sale=None,
    minimum_price=None,
    product_data=None,
    soup=None,
    ctx_dict=None,
    **overrides,
):
    debug("api.other_merchants.start", sku=sku)
    ctx = _HepbAPIContext(
        soup=soup,
        product_data={"sku": sku},
        product_url=product_url,
        anonymous_id=anonymous_id,
    )
    if isinstance(ctx_dict, dict):
        ctx.ctx.update(ctx_dict)
    body = _merge_product_meta(ctx, product_tags=product_tags)
    body["product"]["otherMerchants"] = [
        {
            "productTags": product_tags if product_tags is not None else [],
            "campaignIds": [],
            "finalPriceOnSale": final_price_on_sale or 0,
            "minimumPriceForNLastDays": minimum_price or 0,
            "merchantId": merchant_id or ctx.ctx.get("merchant_id"),
            "merchantName": merchant_name or ctx.ctx.get("merchant_name"),
            "listingId": listing_id or ctx.ctx.get("listing_id"),
        }
    ]
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                body[key] = value
    resp = requests.post(
        "https://www.hepsiburada.com/api/v1/otherMerchants",
        headers=_api_headers(ctx.product_url, is_post=True),
        data=json.dumps(body),
        timeout=30,
    )
    resp.raise_for_status()
    debug("api.other_merchants.ok", sku=sku)
    return resp.json()


def get_shipping_due_date_from_api(
    ctx,
    product_url=None,
    anonymous_id=None,
):
    if anonymous_id is None:
        anonymous_id = str(uuid.uuid4())
    sku = ctx.ctx.get("sku")
    debug("api.shipping_due_date.start", sku=sku)
    listing = ctx.ctx.get("_listing") or {}
    query_model = {
        "sku": sku,
        "listingId": listing.get("listingId") or ctx.ctx.get("listing_id"),
        "definitionName": ctx.ctx.get("definition_name"),
        "warehouseId": listing.get("warehouseId") or ctx.ctx.get("warehouse_id"),
        "shipmentDay": listing.get("shipmentDay") or ctx.ctx.get("shipment_day"),
        "shippingProfileId": listing.get("shippingProfileId")
        or ctx.ctx.get("shipping_profile_id"),
        "deci": 1,
        "inStockDate": "",
        "tags": ctx.ctx.get("product_tags") or [],
        "isBuyBoxWinner": True,
        "quantity": 1,
        "merchantId": listing.get("merchantId") or ctx.ctx.get("merchant_id"),
        "merchantCity": listing.get("merchantCity") or ctx.ctx.get("merchant_city"),
        "merchantCountry": listing.get("merchantCountry")
        or ctx.ctx.get("merchant_country"),
        "shipmentDaysPredictedByHb": 2,
        "customerId": anonymous_id,
        "availableWarehouses": [],
    }
    body = {
        "queryModels": [query_model],
        "customerId": anonymous_id,
        "customerLocation": "",
        "customerCity": "",
        "customerTown": "",
        "customerTownCode": "",
        "customerDistrict": "",
        "customerDistrictCode": "",
        "anonymousId": anonymous_id,
        "locationDeliveryUnavailableDays": [],
        "merchantSortingEnabled": True,
    }
    resp = requests.post(
        "https://shipping-external.hepsiburada.com/duedateapi/querymodel/withtext/v2",
        headers=_api_headers(product_url or ctx.product_url, is_post=True),
        data=json.dumps(body),
        timeout=30,
    )
    resp.raise_for_status()
    debug("api.shipping_due_date.ok", sku=sku)
    return resp.json()


def get_ask_to_seller_from_api(sku, product_url=None):
    debug("api.ask_to_seller.start", sku=sku)
    ctx = _HepbAPIContext(product_data={"sku": sku}, product_url=product_url)
    resp = requests.get(
        f"https://api-asktoseller.hepsiburada.com/api/v2.0/products/{sku}/merchants/accept-questions",
        headers=_api_headers(ctx.product_url),
        timeout=30,
    )
    resp.raise_for_status()
    debug("api.ask_to_seller.ok", sku=sku)
    return resp.json()

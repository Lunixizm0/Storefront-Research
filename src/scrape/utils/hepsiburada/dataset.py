# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

from scrape.dataset import ProductDataset
from scrape.debug import debug, warn

from ..trendyol.common import _extract_first_string, _safe_api_call
from .api import (
    _HepbAPIContext,
    get_ask_to_seller_from_api,
    get_installment_from_api,
    get_listings_from_api,
    get_other_merchants_from_api,
    get_payment_options_from_api,
    get_shipping_due_date_from_api,
    get_vas_from_api,
    get_without_affordability_from_api,
)
from .builders import (
    _build_ask_to_seller,
    _build_installment_offer,
    _build_other_merchants,
    _build_payment_options,
    _build_shipping,
    _build_vas,
    _build_without_affordability,
    _kurus_amount,
    _listing_price_value,
)
from .parsing import (
    _build_description,
    _detect_category,
    _extract_availability,
    _extract_custom_data,
    _extract_image,
    _extract_redux_product,
    _extract_redux_store,
    extract_price,
    extract_product_data,
)

__all__ = ["build_product_dataset", "extract_product_dataset"]


def build_product_dataset(
    product_data, category="unknown", custom_data=None, soup=None
):
    if not isinstance(product_data, dict):
        warn("dataset.skipped", provider="hepsiburada", reason="product_data_missing")
        return None

    redux = _extract_redux_store(soup) if soup is not None else None
    redux_product = _extract_redux_product(redux)
    debug(
        "dataset.build.start",
        provider="hepsiburada",
        redux_product_found=redux_product is not None,
    )

    offers = product_data.get("offers")
    if not isinstance(offers, dict):
        offers = {}

    brand = product_data.get("brand")
    if isinstance(brand, dict):
        brand_name = brand.get("name")
    else:
        brand_name = brand

    custom_data = _extract_custom_data(product_data, redux_product)

    sku = product_data.get("sku")
    merchant_id = None
    listing_id = None
    product_tags = []
    merchant_name = None
    listing = {}
    if isinstance(redux_product, dict):
        listings = redux_product.get("listings")
        if isinstance(listings, list) and listings:
            listing = listings[0] if isinstance(listings[0], dict) else {}
        if not listing and isinstance(redux_product.get("listings"), list):
            listing = {}
        merchant_id = listing.get("merchantId")
        listing_id = listing.get("listingId")
        merchant_name = listing.get("merchantName")
        _product_id = listing.get("productId") or redux_product.get("productId")
        payment_tag = listing.get("paymentTag")
        if isinstance(payment_tag, str) and payment_tag:
            product_tags = [t.strip() for t in payment_tag.split(",") if t.strip()]
        if not product_tags:
            tag_list = listing.get("tagList")
            if isinstance(tag_list, list):
                product_tags = [
                    t.get("tagId")
                    for t in tag_list
                    if isinstance(t, dict) and t.get("tagId")
                ]

    if sku is None:
        sku = (redux_product or {}).get("sku")

    api_data = {}

    if sku:
        listings = _safe_api_call(get_listings_from_api, sku)
        if isinstance(listings, list) and listings:
            first_listing = listings[0]
            listing = first_listing if isinstance(first_listing, dict) else {}
            if isinstance(first_listing, dict):
                if merchant_id is None:
                    merchant_id = first_listing.get("merchantId")
                if listing_id is None:
                    listing_id = first_listing.get("listingId")
                if merchant_name is None:
                    merchant_name = first_listing.get("merchantName")
                if not product_tags:
                    payment_tag = first_listing.get("paymentTag")
                    if isinstance(payment_tag, str) and payment_tag:
                        product_tags = [
                            t.strip() for t in payment_tag.split(",") if t.strip()
                        ]
                    if not product_tags:
                        tag_list = first_listing.get("tagList")
                        if isinstance(tag_list, list):
                            product_tags = [
                                t.get("tagId")
                                for t in tag_list
                                if isinstance(t, dict) and t.get("tagId")
                            ]
            api_data["listings"] = listings

    api_ctx = _HepbAPIContext(soup=soup, product_data=product_data)
    api_ctx.ctx["merchant_id"] = api_ctx.ctx.get("merchant_id") or merchant_id
    api_ctx.ctx["listing_id"] = api_ctx.ctx.get("listing_id") or listing_id
    api_ctx.ctx["merchant_name"] = api_ctx.ctx.get("merchant_name") or merchant_name
    api_ctx.ctx["product_tags"] = product_tags
    api_ctx.ctx["_listing"] = listing

    definition_id = api_ctx.ctx.get("definition_id")
    tax_ratio = api_ctx.ctx.get("tax_vat_rate")
    product_url = api_ctx.product_url

    installment = _safe_api_call(
        get_installment_from_api,
        sku,
        amount=_kurus_amount(_listing_price_value(listing, "price")),
        definition_id=definition_id,
        tax_ratio=tax_ratio,
        merchant_id=merchant_id,
        product_url=product_url,
    )
    built_installment = _build_installment_offer(installment)
    if built_installment:
        api_data["installment"] = built_installment

    ask_to_seller = _safe_api_call(
        get_ask_to_seller_from_api, sku, product_url=product_url
    )
    built_ask = _build_ask_to_seller(ask_to_seller)
    if built_ask:
        api_data["ask_to_seller"] = built_ask

    if product_tags:
        without_aff = _safe_api_call(
            get_without_affordability_from_api,
            sku,
            product_tags,
            finalPrice=_listing_price_value(listing, "price"),
            finalPriceOnSale=_listing_price_value(listing, "price"),
            taxVatRate=tax_ratio,
            product_url=product_url,
            product_data=product_data,
            soup=soup,
            ctx_dict=api_ctx.ctx,
        )
        built_without_aff = _build_without_affordability(without_aff)
        if built_without_aff:
            api_data["affordability"] = built_without_aff

        other_merchants = _safe_api_call(
            get_other_merchants_from_api,
            sku,
            product_tags,
            merchant_id=merchant_id,
            merchant_name=merchant_name,
            listing_id=listing_id,
            final_price_on_sale=_listing_price_value(listing, "price"),
            minimum_price=_listing_price_value(listing, "minimumPrice"),
            product_url=product_url,
            product_data=product_data,
            soup=soup,
            ctx_dict=api_ctx.ctx,
        )
        built_other = _build_other_merchants(other_merchants)
        if built_other:
            api_data["other_merchants"] = built_other

    shipping = _safe_api_call(get_shipping_due_date_from_api, api_ctx)
    built_shipping = _build_shipping(shipping)
    if built_shipping:
        api_data["shipping"] = built_shipping

    payment_options = _safe_api_call(
        get_payment_options_from_api,
        sku,
        definition_id=definition_id,
        product_url=product_url,
    )
    built_payment = _build_payment_options(payment_options)
    if built_payment:
        api_data["payment_options"] = built_payment

    vas = _safe_api_call(
        get_vas_from_api,
        sku,
        price=_listing_price_value(listing, "price"),
        product_url=product_url,
        product_data=product_data,
        soup=soup,
        ctx_dict=api_ctx.ctx,
    )
    built_vas = _build_vas(vas)
    if built_vas:
        api_data["vas"] = built_vas

    if api_data:
        custom_data["api_data"] = api_data

    dataset = ProductDataset(
        source="hepsiburada",
        category=_detect_category(product_data, redux_product)
        if category in (None, "", "unknown")
        else category,
        name=_extract_first_string(product_data.get("name")),
        brand=_extract_first_string(brand_name),
        price=extract_price(product_data),
        currency=offers.get("priceCurrency"),
        url=offers.get("url"),
        sku=sku,
        image=_extract_image(product_data),
        description=_build_description(soup, product_data)
        if soup is not None
        else _extract_first_string(product_data.get("description")),
        availability=_extract_availability(product_data, redux_product),
        item_condition=offers.get("itemCondition"),
        reviews=custom_data.get("reviews"),
        installments=api_data.get("installment"),
        vas=api_data.get("vas"),
        custom_data=custom_data,
    )
    debug(
        "dataset.build.complete",
        provider="hepsiburada",
        api_sections=list(api_data),
        populated_fields=sum(
            value is not None
            for value in (
                dataset.name,
                dataset.brand,
                dataset.price,
                dataset.sku,
                dataset.description,
                dataset.availability,
            )
        ),
    )
    return dataset


def extract_product_dataset(soup, category="unknown", custom_data=None):
    product_data = extract_product_data(soup)
    debug(
        "dataset.extract",
        provider="hepsiburada",
        product_data_found=product_data is not None,
    )
    return build_product_dataset(
        product_data, category=category, custom_data=custom_data, soup=soup
    )

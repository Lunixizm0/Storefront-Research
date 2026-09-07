# In-tree package module. Do not use directly. import from scrape.utils.{pkg}


__all__ = [
    "_build_ask_to_seller",
    "_build_discount_rate",
    "_build_installment_offer",
    "_build_other_merchants",
    "_build_payment_options",
    "_build_pricing",
    "_build_shipping",
    "_build_vas",
    "_build_without_affordability",
    "_is_hepb_response_dict",
    "_kurus_amount",
    "_listing_price_value",
]


def _is_hepb_response_dict(data):
    return isinstance(data, dict) and data.get("statusCode") == 200


def _listing_price_value(listing, key):
    if isinstance(listing, dict):
        v = listing.get(key)
        if isinstance(v, dict):
            return v.get("value")
        return v
    return None


def _kurus_amount(value):
    try:
        return round(float(value) * 100)
    except (TypeError, ValueError):
        return 0


def _build_pricing(pricing_data, promo_data):
    if not isinstance(pricing_data, dict):
        return None
    out = {}
    if pricing_data.get("rawPrice") is not None:
        out["original_price"] = pricing_data["rawPrice"]
    if pricing_data.get("discountedPrice") is not None:
        out["price"] = pricing_data["discountedPrice"]
    if pricing_data.get("priceText"):
        out["price_text"] = pricing_data["priceText"]
    if not out and pricing_data.get("price") is not None:
        out["price"] = pricing_data["price"]
    if isinstance(promo_data, dict) and promo_data.get("price"):
        promo = promo_data["price"]
        if isinstance(promo, dict):
            if promo.get("price") is not None:
                out["price"] = promo["price"]
            if promo.get("discountedPrice") is not None:
                out["price"] = promo["discountedPrice"]
    return out if out else None


def _build_discount_rate(discount_data):
    if not isinstance(discount_data, dict):
        return None
    out = {}
    if discount_data.get("discountRate") is not None:
        out["rate"] = discount_data["discountRate"]
    if discount_data.get("text"):
        out["text"] = discount_data["text"]
    if discount_data.get("type"):
        out["type"] = discount_data["type"]
    return out if out else None


def _build_installment_offer(data):
    if not _is_hepb_response_dict(data):
        return None
    detail = (
        data.get("data", {}).get("instalmentDetail")
        if isinstance(data.get("data"), dict)
        else None
    )
    if not isinstance(detail, dict):
        return None
    out = {}
    for key, label in (
        ("cardAmount", "card_amount"),
        ("cardInstallment", "card_installment"),
        ("loanAmount", "loan_amount"),
        ("loanInstallment", "loan_installment"),
    ):
        if detail.get(key) is not None:
            out[label] = detail[key]
    return out if out else None


def _build_ask_to_seller(data):
    if not isinstance(data, dict):
        return None
    out = {}
    if data.get("questionCount") is not None:
        out["question_count"] = data["questionCount"]
    merchants = data.get("merchants")
    if isinstance(merchants, list) and merchants:
        entries = []
        for m in merchants:
            if not isinstance(m, dict):
                continue
            entry = {}
            if m.get("name"):
                entry["merchant"] = m["name"]
            if m.get("rating") is not None:
                entry["rating"] = m["rating"]
            if entry:
                entries.append(entry)
        if entries:
            out["merchants"] = entries
    return out if out else None


def _build_shipping(data):
    if not isinstance(data, list) or not data:
        return None
    first = data[0]
    if not isinstance(first, dict):
        return None
    out = {}
    for key, label in (
        ("dueDateFormatted", "due_date"),
        ("dueText", "due_text"),
        ("checkoutDueText", "checkout_due_text"),
        ("shipmentTimeText", "shipment_time_text"),
        ("cargoFirmId", "cargo_firm_id"),
        ("cutOffTime", "cut_off_time"),
    ):
        if first.get(key) is not None:
            out[label] = first[key]
    delivery_options = first.get("deliveryOptions")
    if isinstance(delivery_options, list) and delivery_options:
        opts = []
        for d in delivery_options:
            if not isinstance(d, dict):
                continue
            entry = {}
            if d.get("optionName"):
                entry["name"] = d["optionName"]
            if d.get("text"):
                entry["text"] = d["text"]
            if d.get("type"):
                entry["type"] = d["type"]
            if d.get("cargoFirmId") is not None:
                entry["cargo_firm_id"] = d["cargoFirmId"]
            if d.get("imageUrl"):
                entry["image_url"] = d["imageUrl"]
            if entry:
                opts.append(entry)
        if opts:
            out["delivery_options"] = opts
    return out if out else None


def _build_without_affordability(data):
    if not _is_hepb_response_dict(data):
        return None
    result = (
        data.get("data", {}).get("result")
        if isinstance(data.get("data"), dict)
        else None
    )
    product = result.get("product") if isinstance(result, dict) else None
    if not isinstance(product, dict):
        return None
    out = {}
    price = _build_pricing(product.get("priceData"), product.get("promoData"))
    if price:
        out["price"] = price
    rate = _build_discount_rate(product.get("discountRateData"))
    if rate:
        out["discount_rate"] = rate
    promo_data = product.get("promoData")
    if isinstance(promo_data, dict) and isinstance(promo_data.get("data"), dict):
        campaign_data = promo_data["data"]
        campaigns = campaign_data.get("campaigns")
        if isinstance(campaigns, dict):
            tab = campaigns.get("campaignTabDetailList")
            if isinstance(tab, dict):
                for section_name, label in (
                    ("freeShippingCampaignList", "free_shipping_campaigns"),
                    ("specialCampaignList", "special_campaigns"),
                    ("couponCampaignList", "coupon_campaigns"),
                ):
                    section = tab.get(section_name)
                    if isinstance(section, list) and section:
                        entries = []
                        for item in section:
                            if not isinstance(item, dict):
                                continue
                            entry = {}
                            if item.get("name"):
                                entry["name"] = item["name"]
                            if item.get("conditionAmount") is not None:
                                entry["condition_amount"] = item["conditionAmount"]
                            if item.get("endDateTime"):
                                entry["end_date"] = item["endDateTime"]
                            if entry:
                                entries.append(entry)
                        if entries:
                            out.setdefault("campaigns", {})[label] = entries
    return out if out else None


def _build_payment_options(data):
    if not _is_hepb_response_dict(data):
        return None
    result = (
        data.get("data", {}).get("result")
        if isinstance(data.get("data"), dict)
        else None
    )
    product = result.get("product") if isinstance(result, dict) else None
    if not isinstance(product, dict):
        return None
    options = product.get("paymentOptions")
    if not isinstance(options, list) or not options:
        return None
    entries = []
    for opt in options:
        if not isinstance(opt, dict):
            continue
        entry = {}
        if opt.get("title"):
            entry["title"] = opt["title"]
        if opt.get("text"):
            entry["text"] = opt["text"]
        if opt.get("paymentType") is not None:
            entry["payment_type"] = opt["paymentType"]
        if opt.get("isCashPrice") is not None:
            entry["is_cash_price"] = opt["isCashPrice"]
        if opt.get("iconUrl"):
            entry["icon_url"] = opt["iconUrl"]
        if entry:
            entries.append(entry)
    return entries if entries else None


def _build_other_merchants(data):
    if not _is_hepb_response_dict(data):
        return None
    result = (
        data.get("data", {}).get("result")
        if isinstance(data.get("data"), dict)
        else None
    )
    products = result.get("products") if isinstance(result, dict) else None
    merchants = products.get("otherMerchants") if isinstance(products, dict) else None
    if not isinstance(merchants, list) or not merchants:
        return None
    entries = []
    for m in merchants:
        if not isinstance(m, dict):
            continue
        entry = {}
        if m.get("merchantName"):
            entry["merchant"] = m["merchantName"]
        if m.get("merchantId"):
            entry["merchant_id"] = m["merchantId"]
        price = _build_pricing(m.get("priceData"), m.get("promoData"))
        if price:
            entry["price"] = price
        if m.get("couponCount") is not None:
            entry["coupon_count"] = m["couponCount"]
        campaigns = m.get("campaigns")
        if isinstance(campaigns, list) and campaigns:
            texts = [
                c.get("text")
                for c in campaigns
                if isinstance(c, dict) and c.get("text")
            ]
            if texts:
                entry["campaigns"] = texts
        if entry:
            entries.append(entry)
    return entries if entries else None


def _build_vas(data):
    if not isinstance(data, dict):
        return None
    suggested = data.get("suggestedProducts")
    if not isinstance(suggested, list) or not suggested:
        return None
    entries = []
    for s in suggested:
        if not isinstance(s, dict):
            continue
        entry = {}
        if s.get("suggestedSku"):
            entry["suggested_sku"] = s["suggestedSku"]
        if s.get("title"):
            entry["title"] = s["title"]
        if s.get("subTitle"):
            entry["sub_title"] = s["subTitle"]
        if s.get("description"):
            entry["description"] = s["description"]
        if s.get("name_mobile"):
            entry["name_mobile"] = s["name_mobile"]
        if s.get("price") is not None:
            entry["price"] = s["price"]
        if s.get("brand"):
            entry["brand"] = s["brand"]
        if s.get("listingId"):
            entry["listing_id"] = s["listingId"]
        if s.get("logo"):
            entry["logo"] = s["logo"]
        if s.get("detailLink"):
            entry["detail_link"] = s["detailLink"]
        if s.get("staticPage"):
            entry["static_page"] = s["staticPage"]
        items = s.get("items_mobile")
        if isinstance(items, list) and items:
            item_entries = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                ie = {}
                if item.get("title"):
                    ie["title"] = item["title"]
                if item.get("description"):
                    ie["description"] = item["description"]
                if item.get("image"):
                    ie["image"] = item["image"]
                if ie:
                    item_entries.append(ie)
            if item_entries:
                entry["items"] = item_entries
        if entry:
            entries.append(entry)
    return entries if entries else None

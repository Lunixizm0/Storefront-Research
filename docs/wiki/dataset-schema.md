# Product Dataset Schema

All providers reduce their enriched product data to a single plain-JSON record: the `ProductDataset` dataclass (`src/scrape/dataset.py`).

## Definition (for now)

``` python
@dataclass
class ProductDataset:
    source: str                       # "trendyol" | "hepsiburada" | "mediamarkt"
    category: str = "unknown"         # detected category (leaf name), never null
    name: str | None = None
    brand: str | None = None
    price: str | None = None          # formatted, e.g. "3839.00 TL"
    currency: str | None = None       # e.g. "TRY"
    url: str | None = None            # canonical product URL
    sku: str | None = None
    image: str | None = None          # single primary image URL
    description: str | None = None
    availability: str | None = None   # schema.org availability URL (trendyol/hepsiburada) or plain status string (mediamarkt: "InStock"/"OutOfStock"/"PreOrder")
    item_condition: str | None = None # schema.org itemCondition URL (null for mediamarkt)
    reviews: dict | None = None
    vas: list | None = None           # value-added services / attributes
    installments: dict | None = None
    custom_data: dict = field(default_factory=dict)
```

`to_dict()` (`dataset.py`) mirrors every field name verbatim; `to_json()` serializes it with `ensure_ascii=False`, i.e. Turkish characters stay literal.

## Field mapping per provider

| Field | Trendyol | Hepsiburada | MediaMarkt |
| --- | --- | --- | --- |
| `category` | `_find_category_path_in_shared_props` (leaf of `categoryTree`/`webCategoryTree`), overridable | `_detect_category` (leaf of `productState.product` category list / breadcrumbs), overridable | `_build_category` (leaf breadcrumb of `GraphqlProduct.breadcrumbs`), overridable |
| `name` / `brand` | JSON-LD `name`, `brand.name` | JSON-LD `name`, `brand.name` | `GraphqlProduct.title` / `manufacturer` |
| `price` / `currency` | `extract_price` (buy-box from `merchantListing.winnerVariant`), JSON-LD `offers.priceCurrency` | `extract_price` (JSON-LD `offers.price`, mirrors redux `prices[1]`), JSON-LD `offers.priceCurrency` | `_build_price` (`CofrPriceFeature.promoPrice.amount`, fallback `price.amount`), `currency` |
| `url` | JSON-LD `@id` | JSON-LD `offers.url` (+ redux/slug fallback) | `GraphqlProduct.url` absolutised against `https://www.mediamarkt.com.tr` |
| `sku` | JSON-LD `sku` | redux `productState.product.sku` (or JSON-LD) | product id from URL / `GraphqlProduct.id` |
| `image` | ImageObject `contentUrl` | `_extract_image` (JSON-LD `image` to `data-*` picture) | `CofrMediaAssetsFeature` `productMainImage.link` (fallback `productImages[0].link`) |
| `description` | **API** (`component-read`) + sentence-marker strip | **DOM** (`div#ProductDescription` / `[class*=ProductDescription]`), JSON-LD only as fallback | **Embedded state** `GraphqlProduct.description`, decoded (`<lt/>`/`<gt/>`) + textified |
| `availability` / `item_condition` | JSON-LD `offers.availability` / `itemCondition` | `_extract_availability` (offers/stock) / `offers.itemCondition` | `_build_availability` from `CofrOnlineStatusFeature`/`CofrDeliveryFeature`/`CofrPickupFeature` to plain `"InStock"`/`"OutOfStock"`/`"PreOrder"` / always `null` |
| `reviews` | `_extract_reviews_custom` from `product.ratingScore` | `productState.product.reviews` to `{score, count}` | `CofrCoreFeature.reviewStatistics` to `{average_rating, count, overall_rating_range}` |
| `vas` | `_build_vas` (11 entries from attributes/anc) | `_build_vas` (`get_vas_from_api`) | `GraphqlServiceProductV2` entities to `{product_id[, title, price]}` |
| `installments` | `_build_installments` from `__envoy__SHARED_PROPS` | `api_data.installment` | `CofrPriceFeature.price.installment` to `{duration, monthly_rate, total_amount}` |
| `custom_data` | `_detect_custom_data` + merged caller data + `api_data` | merged + `api_data` | `_build_custom_data` + `graphql` supplementary + merged caller data |

## On-page vs API enrichment

The 16 dataset fields come from four sources per provider:

1. **JSON-LD** - identity fields (`name`, `brand`, `sku`, `url`, `image`, `offers`). Used only by Trendyol/Hepsiburada; **MediaMarkt exposes no JSON-LD on the PDP**.
2. **Embedded state** - Trendyol `window["__envoy__SHARED_PROPS"]=`, Hepsiburada `script#reduxStore`, MediaMarkt `window.__PRELOADED_STATE__` to `apolloState` (Apollo cache, see [mediamarkt-preloaded_state](mediamarkt-preloaded_state)). Fills what JSON-LD lacks: category tree, buybox merchant/price, all listings, review score, merchant context - and on MediaMarkt it is the **only** source: the state already carries name, price, image, description, features, category, availability, installment, reviews and VA services.
3. **Live APIs** - Trendyol component-read (description) + the `api_data` sections (delivery, merchant questions, seller store, slicing attributes, video, currencies, VAS, installments, ...); Hepsiburada VAS/installment/payment APIs; MediaMarkt GraphQL persisted queries (media content + loyalty points only, see [mediamarkt-graphql](mediamarkt-graphql)).
4. **DOM** - description block (Hepsiburada), `__PRELOADED_STATE__` script extraction (MediaMarkt), and regex backfill for ids when state is missing.

## Captured examples

### Trendyol (`product_data.json` query dataset)

``` json
{
  "source": "trendyol",
  "category": "Kulak İçi Bluetooth Kulaklık",
  "name": "Xiaomi Redmi Buds 8 Pro Siyah ..., Xiaomi Türkiye Garantili",
  "brand": "Xiaomi",
  "price": "3839.00 TL",
  "currency": "TRY",
  "sku": "1081766367",
  "availability": "https://schema.org/InStock",
  "item_condition": "https://schema.org/NewCondition",
  "reviews": { "score": 4.349056603773585, "count": 56 },
  "vas": [ { "key": "Garanti Tipi", "value": "Resmi Distribütör Garantili" }, "... 10 more" ]
}
```

`custom_data`: `{ pattern, attributes, reviews, listings[], merchant, category_path[], api_data{} }`. `category_path` here = `["Elektronik", "Giyilebilir Teknoloji", "Kulaklıklar", "Kulak içi TWS Bluetooth Kulaklık"]`; `listings` (winning merchant first) as `{ merchant, price, original_price }` - Trendyol/3839, Xiaomi Resmi Mağazası/4499, VATAN BİLGİSAYAR/4499, ARVONX GLOBAL/5930.45, EnSonu/6199.

### Hepsiburada (`expected/*`)

``` json
{
  "source": "hepsiburada",
  "category": "Kulak Üstü Kulaklık",
  "name": "Razer BlackShark V2 Pro 2023 Kablosuz Gaming Kulaklık, Beyaz RZ04-04530200-R3M1",
  "brand": "Razer",
  "price": "7890.00 TL",
  "currency": "TRY",
  "sku": "HBCV00004MW5Q6",
  "url": "https://www.hepsiburada.com/razer-blackshark-v2-pro-2023-kablosuz-gaming-kulaklik-beyaz-rz04-04530200-r3m1-p-HBCV00004MW5Q6",
  "image": "https://productimages.hepsiburada.net/s/435/375/110000467783749.jpg/format:webp",
  "description": "Razer BlackShark V2 Pro 2023 Kablosuz Gaming Kulaklık, Beyaz RZ04-04530200-R3M1",
  "availability": "https://schema.org/InStock",
  "reviews": { "score": 4.6, "count": 82 }
}
```

`custom_data`: `{ merchant: "Nethouse", product_id, category_path, listings[], reviews, api_data{} }`; `product_ctx.json` holds the extended raw context (definition_id 297, merchant_id, listing_id, root_category_list, root_buying_category_list, ...).

### MediaMarkt (`expected_dataset.json`)

``` json
{
  "source": "mediamarkt",
  "category": "Şarjlı Dikey Süpürge",
  "name": "DYSON V15 Detect Absolute Şarjlı Dikey Süpürge",
  "brand": "DYSON",
  "price": "34897.00 TL",
  "currency": "TRY",
  "sku": "1232522",
  "url": "https://www.mediamarkt.com.tr/tr/product/_dyson-v15-detect-kablosuz-sarjli-dikey-supurge-sari-nikel-1232522.html",
  "image": "https://assets.mmsrg.com/isr/166325/c1/-/ASSET_MMS_130158814",
  "availability": "OutOfStock",
  "reviews": { "average_rating": 4.5909, "count": 44, "overall_rating_range": 5 },
  "installments": { "duration": 4, "monthly_rate": 8724.25, "total_amount": 34897 }
}
```

`custom_data`: `{ price, shipping_cost, promo_ids[], vat_rate, product_group_id, ean, tax, manufacturer, manufacturer_id, feature_name, kind_of_product, raw_title, category_path[], loyalty_points, feature_groups[], status{}, highlights[], full_features{}, va_services[], product_id, url, graphql{ loyalty, videos[] } }`. `category_path` = `["Ev Aletleri & Yaşam", "Süpürgeler", "Dikey Süpürge", "Şarjlı Dikey Süpürge"]`; `full_features` groups the feature rows by `featureGroupName`.

## Notes

- `category` has no `None` fallback in the dataclass signature but each parser substitutes the leaf name or `"unknown"` - so it always exists in the exported JSON.
- `price` is stored as a **formatted string** (`"3839.00 TL"`), not a number; the numeric value (3839) lives in `custom_data.listings[].price` (Trendyol), `custom_data.price` (MediaMarkt).
- `description` on Trendyol reflects the post-strip text (see [trendyol-description](trendyol-description)); on Hepsiburada the DOM title line (see [hepsiburada-description](hepsiburada-description)).
- `availability` is a schema.org URL on Trendyol/Hepsiburada, but a plain status string on MediaMarkt (`"InStock"` / `"OutOfStock"` / `"PreOrder"` derived from the online/delivery/pickup statuses); `item_condition` is always `null` for MediaMarkt.
- MediaMarkt's GraphQL `graphql` supplementary block appears in `custom_data` only when the live call succeeded or loyalty came from the embedded state; scraping never fails when GraphQL is unavailable.
- New `api_data` sections are additive and only appear in the output when the corresponding live call succeeded.
# JSON-LD Structured Data (Product Page)

Trendyol's product detail page (PDP) exposes two JSON-LD blocks inside `script[type="application/ld+json"]` tags:

1. **ProductGroup** - the product and its variant family.
2. **WebPage** - page-level metadata (name, description, primary image, related links).

Both blocks were captured live from the following test product:
`https://www.trendyol.com/xiaomi/redmi-buds-8-pro-siyah-bluetooth-kulakici-kulaklik-tws-anc-bt-5-4-xiaomi-tr-garantili-p-1081766367` (product id: `1081766367`, "Xiaomi Redmi Buds 8 Pro Siyah Bluetooth Kulakiçi Kulaklık TWS - ANC BT 5.4 (Xiaomi TR Garantili)").

Fixture: `product_data.json` (the `ProductGroup` block).

## Block 1: ProductGroup

Unlike Hepsiburada (whose block is `@type: Product`), the Trendyol block is a `ProductGroup`: a grouping of color/size variants of the same product family. Its fields:

| Field | Type | Example Value |
| --- | --- | --- |
| `@type` | string | `ProductGroup` |
| `productGroupID` | string | `821600500` |
| `@id` | string | Canonical product URL (`https://www.trendyol.com/xiaomi/redmi-buds-8-pro-siyah-...-p-1081766367`) |
| `name` | string | `Xiaomi Redmi Buds 8 Pro Siyah Bluetooth Kulakiçi Kulaklık TWS - ANC BT 5.4 (Xiaomi TR Garantili)` |
| `manufacturer` | object | `{ "@type": "Brand", "name": "Xiaomi" }` |
| `brand` | object | `{ "@type": "Brand", "name": "Xiaomi" }` |
| `sku` | string | `1081766367` |
| `color` | string | e.g. `siyah` |
| `audience` | object | e.g. `{ "@type": "PeopleAudience", "suggestedGender": "unisex" }` |
| `description` | string | `Xiaomi Redmi Buds 8 Pro Siyah Bluetooth Kulakiçi Kulaklık TWS - ANC BT 5.4 (Xiaomi TR Garantili) yorumlarını inceleyin, Trendyol'a özel indirimli fiyata satın alın.` |
| `image` | object | `ImageObject` with `contentUrl[]` (11 URLs, `cdn.dsmcdn.com/.../1_org_zoom.jpg`) plus `embeddedTextCaption` |
| `offers` | object | of type `Offer` (see below) |
| `isRelatedTo` | array | 8 related product URLs (e.g. mavi `p-1081766366`, beyaz `p-1081766368`, qcy/melobuds `p-1053918274`) |
| `additionalProperty` | array | `PropertyValue[]` - key product features (see below) |
| `variesBy` | array | `["https://schema.org/size", "https://schema.org/color"]` |
| `hasVariant` | array | `Product[]` - sibling variants (see below) |
| `aggregateRating` | object | `{ "@type": "AggregateRating", "ratingValue": 4.4, "ratingCount": 107, "reviewCount": 55 }` |
| `review` | array | `Review[]` - individual review objects (see below) |

### `additionalProperty` (PropertyValue)

Each entry is a single `{ "@type": "PropertyValue", "name", "unitText" }` pair (unitText carries the value):

| name | unitText |
| --- | --- |
| `Aktif Gürültü Önleme (ANC)` | `Var` |
| `Dokunmatik Kontrol` | `Var` |
| `Garanti Tipi` | `Resmi Distribütör Garantili` |
| `Renk` | `Siyah` |

### `hasVariant` (Product)

Each variant is a `Product` with its own `sku` (id), name, description, image, `offers`, and an `isVariantOf` link back to the group's `@id`:

| Field | Type | Example Value |
| --- | --- | --- |
| `sku` | string | `1081766366` (mavi), `1081766368` (beyaz) |
| `color` | string | `mavi-c` |
| `isVariantOf` | object | `{ "@id": "<group canonical URL>" }` |
| `offers` | object | `Offer` for the sibling variant |

### `review` (Review)

| Field | Type | Example Value |
| --- | --- | --- |
| `author` | object | `{ "@type": "Person", "name": "N** N**" }` (masked) |
| `datePublished` | string | `2026-04-18` |
| `reviewBody` | string | `Harika bir kulaklık, hiç pişman etmedi. Trendyol ekibine çook teşekkürler 🖤🖤` |
| `reviewRating` | object | `{ "@type": "Rating", "bestRating": 5, "ratingValue": 5, "worstRating": 1 }` |

### `offers` (Offer) sub-structure

| Field | Type | Example Value |
| --- | --- | --- |
| `@type` | string | `Offer` |
| `url` | string | Canonical product URL |
| `price` | string | `3839.00` |
| `priceCurrency` | string | `TRY` |
| `itemCondition` | string | `https://schema.org/NewCondition` |
| `availability` | string | `https://schema.org/InStock` |
| `hasMerchantReturnPolicy` | object | `{ applicableCountry: "TR", merchantReturnDays: 15, returnFees: "https://schema.org/FreeReturn", returnMethod: [...] }` |
| `shippingDetails` | object | `OfferShippingDetails` (shippingRate `49.99` TRY, shippingDestination TR, deliveryTime with handlingTime `0–1 days`, transitTime, cutoffTime `16:30-08:30`) |

## Block 2: WebPage

| Field | Type | Example Value |
| --- | --- | --- |
| `name` | string | Product name |
| `description` | string | Meta description |
| `url` | string | Canonical product URL |
| `inLanguage` | string | `tr` |
| `primaryImageOfPage` | object | `ImageObject` |
| `isRelatedTo` | array | Related product links |

## Notes

- The block is discovered and parsed by `_iter_json_ld_payloads` (`src/scrape/utils/trendyol.py:384`) and `extract_product_data` (`:397`). `extract_product_data` returns a payload when `@type == "Product"`, or when it has both `offers` (dict) and `name` - which is how the `ProductGroup` block is matched.
- There are exactly **2** `ld+json` scripts on the TY PDP (ProductGroup + WebPage). The Hepsiburada page instead carries a `WebPage + Product` block and a separate review-list array.
- `aggregateRating` here uses `ratingCount` (107) plus a separate `reviewCount` (55). The richer rating data (average `4.349056603773585`, comment count `56`) lives in `__envoy__SHARED_PROPS` to `product.ratingScore`, not here.
- The `price` value (`3839.00`) is the selling price shown in the JSON-LD; merchant/buy-box pricing and campaigns come from `__envoy__SHARED_PROPS` to `product.merchantListing.winnerVariant.price`.
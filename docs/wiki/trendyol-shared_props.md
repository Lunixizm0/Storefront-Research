# Shared Props (`__envoy__SHARED_PROPS`)

The Trendyol PDP embeds the server-side state of the React app in a script assignment:

``` js
window["__envoy__SHARED_PROPS"]={ ... }
```

Captured from the same live product as
`tests/fixtures/trendyol/expected/shared_props.json`:
`https://www.trendyol.com/xiaomi/redmi-buds-8-pro-siyah-bluetooth-kulakici-kulaklik-tws-anc-bt-5-4-xiaomi-tr-garantili-p-1081766367` (product id `1081766367`).

## Extraction

`_extract_shared_props(soup)` (`src/scrape/utils/trendyol.py:503`) scans `script` tags for the `__envoy__SHARED_PROPS` marker, finds the first `{`, then bracket-matches to the closing `}` while honoring string literals and escaped quotes, and `json.loads` the slice. Unlike `script#reduxStore` on Hepsiburada, the value assignment is not a standalone JSON document, so it cannot be parsed with a naive first-`{`/last-`}` slice (trailing JS may contain braces).

## Top-level structure

Root keys (as captured):

``` json
["product", "storefront", "culture", "language", "isAzSelected", "isMobile",
 "isMilla", "isInternational", "platform", "user", "isArtwork"]
```

- `product` - the main product payload (37 keys, see below).
- `storefront` / `culture` / `language` / `platform` / `user` - app-level context.
- `isMobile`, `isAzSelected`, etc. - view/state flags.

## `product` (main payload)

Keys (37): `id`, `name`, `productCode`, `productGroupId`, `businessUnitData`, `tax`, `maxInstallment`, `ratingScore`, `inStock`, `brand`, `category`, `categoryTree`, `gender`, `hasHtmlContent`, `webBrand`, `webCategory`, `images`, `isArtwork`, `hasAzDelivery`, `slicingAttributes`, `merchantListing`, `isSellerQuestionEnabled`, `favoriteCount`, `attributes`, `isStarredAttributesVisible`, `uxLayout`, `sizeExpectationAvailable`, `categoryTopRankings`, `filterableLabelIds`, `moreConvenientMerchantAvailable`, `variants`, `webCategoryTree`, `englishTranslation`, `energyClass`, `isRefundable`, `isGlobalBrand`, `sgrPrice`.

Key sample values (live fixture):

| Field | Type | Example Value |
| --- | --- | --- |
| `id` | number | `1081766367` |
| `productCode` | string | `buds8pro` |
| `productGroupId` | number | `821600500` |
| `ratingScore` | object | `{ "averageRating": 4.349056603773585, "commentCount": 56, "totalCount": 106 }` |
| `inStock` | bool | `true` |
| `brand` | object | `{ "id": 11079, "name": "Xiaomi" }` |
| `category` | object | `{ "id": 1058, "name": "Kulak içi TWS Bluetooth Kulaklık", "hierarchy": "Elektronik/Giyilebilir Teknoloji/Kulaklıklar/Kulak içi TWS Bluetooth Kulaklık", "isVASEnabled": true, "isCreditSuitable": true, "bankType": {...} }` |
| `webCategory` | object | `{ "id": 165994, "name": "Kulak İçi Bluetooth Kulaklık" }` |
| `categoryTree` | array | 4 levels: Elektronik(1071) to Giyilebilir Teknoloji(1215) to Kulaklıklar(775) to Kulak içi TWS Bluetooth Kulaklık(1058); each `{ id, name, parent? }` |
| `webCategoryTree` | array | 4 levels (leaf-first): `{ {"name": "Kulak İçi Bluetooth Kulaklık", "id": 165994, "level": 4}, ... {Elektronik, level: 1} }` |
| `images` | array | `https://cdn.dsmcdn.com/ty1000319/.../1_org_zoom.jpg` (includes a `product-placeholder-v2.jpeg` fallback) |
| `attributes` | array | VAS/product attributes (see below) |
| `variants` | array | Buy-box variants; first element = selected winner (see below) |
| `merchantListing` | object | Buyer/seller context (see below) |
| `sgrPrice` | string | `""` (empty unless a special price rule applies) |

### `attributes` (each entry)

| Field | Type | Example Value |
| --- | --- | --- |
| `key` | object | `{ "id": 290, "name": "Garanti Tipi" }` |
| `value` | object | `{ "id": 4183, "name": "Resmi Distribütör Garantili" }` |
| `searchable` | bool | `true` |
| `type` | string | `Warranty Type` |
| `typeId` | number | `284` |
| `isStarred` | bool | `true` |
| `description` | string | `""` |
| `mediaUrls` | array | `[]` |

Other captured entries: `Aktif Gürültü Önleme (ANC)` (key id `647`), `Dokunmatik Kontrol` (key id `667`), `Garanti Süresi`, `Renk`, `Menşei`, `Bluetooth Versiyon` (5.4), etc. These feed the VAS API payload and the `vas` dataset field.

### `variants` / `merchantListing`

- `variants[0]` is the selected (winner) variant: `{ itemNumber: 1494882815, barcode: "6932554458171", isSelected: true, inStock: true, price: { value: 3839, text: "3.839 TL" }, tagDetails: [{ tagId: 4897, tag: "sari_kampanya_urunu", displayName: "Avantajlı Ürün", ... }], ... }`.
- `merchantListing` holds the selling/tracking data not present in the JSON-LD:
    - `merchant` - `{ id, name: "Trendyol", officialName: "DSM GRUP ...", taxNumber, cityName: "İstanbul", sellerScore, videoContentId: "6d1ee37d-be18-4bf1-a17f-464d7c2a3643", ... }`.
    - `otherMerchants[]` - competitor offers.
    - `campaign` - `{ id, name: "1P All Elektronik", startDate, endDate, ... }`.
    - `winnerVariant` - `{ itemNumber, listingId: "0732f56e2ce43d44b1e8e279400f588e", price: {discountedPrice}/{sellingPrice}/{originalPrice}, fulfilmentType: "st", rushDeliveryDuration: 24, freeCargo: false, inStock: true, stockStatus: 1, maxSaleLimit: 1, quantity: 64, barcode, groupTagIds, ... }`.

## Usage in the pipeline

`_sp_*` helpers in `src/scrape/utils/trendyol.py` read the payload:

| Helper | Line | Reads |
| --- | --- | --- |
| `_sp_product` | 868 | the `product` object |
| `_sp_product_id` | 875 | `product.id` (fallback from JSON-LD) |
| `_sp_seller_id` | 884 | `merchantListing.merchant.id` |
| `_sp_category_id` | 896 | `product.category.id` |
| `_sp_selling_price` | 906 | `merchantListing.winnerVariant.price.sellingPrice` / `discountedPrice` |
| `_sp_group_tag_ids` | 928 | `winnerVariant.groupTagIds` |
| `_sp_video_id` | 939 | `merchant.videoContentId` |
| `_sp_p_group_id` | 954 | `productGroupId` |
| `_sp_sticker_ids` | 965 | `winnerVariant.stickerIds` |
| `_sp_tag_ids` | 976 | `winnerVariant.tagDetails[].tagId` |
| `_sp_delivery` | 987 | delivery/shipping flags |

Derived helpers that consume it: `_extract_reviews_custom` (`:559`, from `product.ratingScore`), `_find_category_path_in_shared_props` (`:649`, first of `categoryTree`/`webCategoryTree`), `_extract_listings_custom` (`:610`, winner + `otherMerchants`), and `get_vas_from_api` (`:340`, builds the `/api/vas/` payload from `category`, `brand`, `merchantListing`, and flattened `attributes`).

## Notes

- `product.ratingScore` is the authoritative review summary; `aggregateRating` in the JSON-LD is a secondary/rounded copy.
- The buy-box **price** lives in `merchantListing.winnerVariant.price`, not the JSON-LD `offers.price`.
- `category.hierarchy` is a `/`-joined string; the tree arrays (`categoryTree`, `webCategoryTree`) give the structured path used for the `category` dataset field.
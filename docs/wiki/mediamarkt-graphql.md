# GraphQL (Supplementary Data)

MediaMarkt's storefront frontend is an Apollo Client GraphQL client. On initial load the product data is served from the SSR `__PRELOADED_STATE__` Apollo cache (see [preloaded-state](mediamarkt-preloaded_state)); the GraphQL endpoint only supplies supplementary data that is **not** in that cache:

- `GetProductContentMediaContent` - product media content (e.g. video / 3D assets).
- `GetProductLoyaltyPoints` - loyalty points earned on purchase at a given price.

Example captured from a live product (`1232522`):
`https://www.mediamarkt.com.tr/tr/product/_dyson-v15-detect-kablosuz-sarjli-dikey-supurge-sari-nikel-1232522.html`

## Endpoint

```
GET https://www.mediamarkt.com.tr/api/v1/graphql
```

Despite the default GraphQL convention (POST + JSON body) the PWA sends every query as a **GET** with the query text replaced by a persisted-query hash.

## Query parameters

| Parameter | Value |
| --- | --- |
| `operationName` | e.g. `GetProductContentMediaContent` |
| `variables` | JSON string, e.g. `{"productId": "1232522"}` |
| `extensions` | JSON string (see below) |

### `extensions`

``` json
{
  "persistedQuery": {
    "version": 1,
    "sha256Hash": "<query hash>"
  },
  "pwa": {
    "captureChannel": "DESKTOP",
    "salesLine": "Media",
    "country": "TR",
    "language": "tr",
    "globalLoyaltyProgram": true,
    "isOneAccountProgramActive": true,
    "isCustomerReturnApiActive": true,
    "isUsingXccCustomerComponent": true,
    "isCheckoutAptNrActive": true,
    "isCheckoutAddressLevelActive": true,
    "isCheckoutAddressDistrictActive": true,
    "isCheckoutAddressQuarterActive": true,
    "isCheckoutPhoneCompareActive": true
  }
}
```

The `pwa` extensions block is mandatory - omitting it returns HTTP `500` from the API. `captureChannel`, `salesLine`, `country`, `language` identify the PWA context; the remaining booleans mirror the app's runtime feature flags.

## Request headers

| Header | Value |
| --- | --- |
| `User-Agent` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0` |
| `Origin` | `https://www.mediamarkt.com.tr` |
| `Referer` | the product URL (or `https://www.mediamarkt.com.tr/`) |
| `apollographql-client-name` | `pwa-client-pqm` |
| `apollographql-client-version` | `8.490.2` |
| `x-cacheable` | `true` |
| `x-mms-language` | `tr` |
| `x-mms-country` | `TR` |
| `x-mms-salesline` | `Media` |
| `x-operation` | operation name (extra, used by our client) |
| `x-flow-id` | random UUID (extra, used by our client) |

## Accessibility

The endpoint sits behind a Cloudflare-fronted gateway, but the queries are served to plain HTTP clients (the project verifies this with plain `requests`):

- `403` - missing the apollo / `x-mms-*` request headers or the `x-cacheable` / `x-operation` / `x-flow-id` gateway headers.
- `400` - `Content-Type: application/json` and/or `Origin` missing → blocked as a potential Cross-Site Request Forgery (CSRF).
- `500` - missing the `pwa` extensions block.

With the full header set from [http.py](mediamarkt-README) (`apollographql-client-*`, `x-mms-*`, `x-cacheable`, `x-operation`, `x-flow-id`, `Content-Type: application/json`, `Origin`) a GET carrying the persisted query + `pwa` extensions block succeeds with plain `requests` - **no** `curl_cffi` TLS impersonation or browser `optid`/`__cf_bm` cookies required. The client still performs a best-effort page GET ("cookie warm-up") and on `403`/`429` re-warms the cookies, backs off, and retries (3 attempts) as a fallback for stricter networks. GraphQL is enabled by default; it can be disabled with `SCRAPE_MEDIAMARKT_GRAPHQL=0` (unit tests set this so the suite stays hermetic).

## Operations

### `GetProductContentMediaContent`

Fetches media (videos / 3D models) for a product.

| | |
| --- | --- |
| `operationName` | `GetProductContentMediaContent` |
| `sha256Hash` | `6f8e832c9bf6301b23c12747b56c155f46b0fae05f5235b95e88422ffca504cc` |
| `variables` | `{"productId": "1232522"}` |

Response shape (`data.productMediaContent`):

``` json
{
  "content": [
    {
      "id": "4290634",
      "language": "en",
      "title": "Dyson - V15 Detect |{movieID20022079}",
      "type": "VIDEO",
      "assets": [
        {
          "id": "1290439",
          "name": "thumb",
          "link": "https://mycliplister.com/thumb/189971/6890c9b791ad52b5f7ca01ed0f769ca541dca6955e6f7e9da8f59841c91a5ef8dae148186913bdbfc17d1bc5eeeE76dbf"
        },
        {
          "id": "1290436",
          "name": "icon",
          "link": "https://mycliplister.com/icon/189971/6890c9b791ad52b5f7ca01ed0f769ca541dca6955e6f7e9da8f59841c91a5ef8dae148186913bdbfc17d1bc5eeeE76dbf"
        },
        {
          "id": "1290435",
          "name": "picture",
          "link": "https://mycliplister.com/picture/189971/112d19c499c87414d6f8056bcf5f6ce04048f0a69fe55b31cfd8df11f85aa48e43cbaa7546eda8a658fbab275cd519725"
        }
      ]
    }
  ],
  "__typename": "GraphqlProductMediaContent"
}
```

The dataset stores the media entries in `custom_data["graphql"]["videos"]`, preferring the `picture` asset link, then `thumb`, then `icon`.

### `GetProductLoyaltyPoints`

Fetches the loyalty points a member earns on buying the product at the current price.

| | |
| --- | --- |
| `operationName` | `GetProductLoyaltyPoints` |
| `sha256Hash` | `6dc26319c65876368393797616f466dfb1e2c304eccec8e135f3fdc4f728fe49` |
| `variables` | `{"id": "1232522", "price": 34897, "currency": "TRY"}` |

Response shape (`data.globalLoyItemAssessment`):

``` json
{
  "amount": 3490,
  "baseAmount": 3490,
  "promotionAmount": 0,
  "__typename": "GraphqlGlobalLoyPoint"
}
```

The dataset stores it in `custom_data["graphql"]["loyalty"]` and reflects the amount in `custom_data["loyalty_points"]`.

## Usage in the pipeline

`src/scrape/utils/mediamarkt/dataset.py` (`_supplementary_data`) checks the Apollo product entity first for `globalLoyItemAssessment`; only when loyalty is absent does it call `get_loyalty_points_from_graphql`. Media content is always fetched via `get_product_media_from_graphql`. Both functions live in `src/scrape/utils/mediamarkt/graphql.py` and gate on `_graphql_enabled()`. Failures return `None` and are logged as `graphql.*` warnings - they never fail the scrape (the dataset is built from the embedded state regardless).
# MediaMarkt API Documentation (Storefront)

This directory documents the data sources that feed MediaMarkt Türkiye's product detail page (PDP) and how the `mediamarkt` provider turns them into a `ProductDataset`. Each topic page covers the source, its structure, and real JSON captured from a live page.

The base URL for the storefront is:

```
https://www.mediamarkt.com.tr
```

## Data Source Groups

MediaMarkt.com.tr is an **Apollo Client (GraphQL) PWA**. The product data comes from two groups:

1. **Embedded state (`__PRELOADED_STATE__` to `apolloState`)** - the server-side rendered Apollo cache embedded in the product HTML. This holds the core product aggregate (name, price, images, description, features, category, availability, reviews, VA services) and is **not** fetchable via GraphQL on initial load. See [preloaded-state](mediamarkt-preloaded_state).
2. **GraphQL persisted queries (`/api/v1/graphql`)** - supplementary data missing from the SSR cache: product media content (videos) and loyalty points. See [graphql](mediamarkt-graphql).

## Common Request Headers

### Product page (plain `requests`)

Fetching the HTML itself works with a plain `requests` GET using full browser-navigation headers (`_page_headers()` in `src/scrape/utils/mediamarkt/http.py`):

| Header | Value |
| --- | --- |
| `User-Agent` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0` |
| `Accept` | `text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*` |
| `Accept-Language` | `tr-TR,tr;q=0.9,en-US` |
| `Host` | `www.mediamarkt.com.tr` |
| `Sec-Fetch-Dest` / `-Mode` / `-Site` / `-User` | `document` / `navigate` / `none` / `?1` |

### GraphQL endpoint (plain `requests`)

The GraphQL calls need the Apollo Client request headers (`_graphql_headers()` in `http.py`), the `x-cacheable`/`x-operation`/`x-flow-id` gateway headers, and `Content-Type: application/json` + `Origin` (Apollo CSRF check) - served to plain `requests`, no TLS impersonation or browser cookies - see [graphql](mediamarkt-graphql).

## Accessibility

- The **HTML page** is retrievable with plain `requests`.
- The **GraphQL endpoint** sits behind a Cloudflare-fronted gateway but serves plain HTTP clients. It requires:
  - a GET carrying the persisted-query `sha256Hash` and the `pwa` extensions block;
  - all apollo / `x-mms-*` request headers plus `x-cacheable`/`x-operation`/`x-flow-id` (see [graphql](mediamarkt-graphql));
  - `Content-Type: application/json` and `Origin` to pass the Apollo CSRF check.

Missing headers answer `403` (gateway WAF), `400` (missing `Content-Type`/`Origin` → CSRF block) or `500` (missing `pwa` extensions block). A plain `requests` GET with the full header set returns `200`; as a best-effort fallback the client GETs the page first so Cloudflare issues `optid`/`__cf_bm` cookies and re-warms on `403`/`429`.

## Endpoint List

| # | Source | Method | Purpose | Links |
| --- | --- | --- | --- | --- |
| 1 | `__PRELOADED_STATE__` SSR Apollo cache (embedded in HTML) | - | Core product aggregate (name, price, images, description, features, category, availability, installment, reviews, VA services) | [`preloaded-state`](mediamarkt-preloaded_state) |
| 2 | `/api/v1/graphql` - `GetProductContentMediaContent` | GET | Product media content (videos) | [`graphql`](mediamarkt-graphql) |
| 3 | `/api/v1/graphql` - `GetProductLoyaltyPoints` | GET | Loyalty points for the given price | [`graphql`](mediamarkt-graphql) |

## Accessibility notes vs. other providers

Unlike Trendyol (pure REST gateway) and Hepsiburada (REST + `_abck` Akamai), MediaMarkt exposes almost no REST API: the PWA renders from the embedded Apollo cache and only the media/loyalty bits are fetched via GraphQL persisted queries.

## Test Product

All examples were captured from the following product:
`https://www.mediamarkt.com.tr/tr/product/_dyson-v15-detect-kablosuz-sarjli-dikey-supurge-sari-nikel-1232522.html`

- **SKU / product id:** `1232522`
- **Entity key:** `GraphqlProduct:Media:tr-TR:1232522`
- **Brand / manufacturer:** DYSON
- **Price:** `34897.00 TL` (TRY)
- **Main image:** `https://assets.mmsrg.com/isr/166325/c1/-/ASSET_MMS_130158814`
- **Category (leaf):** `Şarjlı Dikey Süpürge` (path: `Ev Aletleri & Yaşam > Süpürgeler > Dikey Süpürge > Şarjlı Dikey Süpürge`)

The exported dataset lives in `tests/fixtures/mediamarkt/expected_dataset.json` and `docs/mediamarkt-example.json`.